import re
from datetime import datetime, timedelta
from unittest.mock import Mock

import requests
from flask import render_template

from app import create_app

TEST_CONFIG = {
    "TESTING": True,
    "DEBUG": False,
    "SECRET_KEY": "test",
    "API_BASE_URL": "http://api.test",
}



def _respuesta_butacas():
    respuesta = Mock()
    respuesta.status_code = 200
    respuesta.json.return_value = {
        "funcion_id": 1,
        "total_butacas": 4,
        "butacas_libres": 1,
        "butacas": [
            {"id": 2, "fila": "A", "numero": 2, "estado": "reservada"},
            {"id": 1, "fila": "A", "numero": 1, "estado": "disponible"},
            {"id": 4, "fila": "B", "numero": 2, "estado": "inactiva"},
            {"id": 3, "fila": "B", "numero": 1, "estado": "ocupada"},
        ],
    }
    return respuesta


def _respuesta_funcion(funcion_id=1):
    respuesta = Mock()
    respuesta.status_code = 200
    respuesta.json.return_value = {
        "id": funcion_id,
        "pelicula_id": 1,
        "sala_id": 1,
        "fecha_hora": "2026-12-10T18:30:00-03:00",
        "precio": 6500,
        "estado": "programada",
    }
    return respuesta


def _respuesta_pelicula():
    respuesta = Mock()
    respuesta.status_code = 200
    respuesta.json.return_value = {
        "id": 1,
        "titulo": "Horizonte final",
        "clasificacion": "+13",
        "poster_url": "https://example.test/poster.jpg",
        "funciones_disponibles": [
            {
                "id": 1,
                "local_id": 1,
                "sala_nombre": "Sala 1",
                "local_nombre": "Cine Paradiso Centro",
                "fecha_hora": "2026-12-10T18:30:00-03:00",
                "precio": 6500,
            },
            {
                "id": 7,
                "local_id": 1,
                "sala_nombre": "Sala 1",
                "local_nombre": "Cine Paradiso Centro",
                "fecha_hora": "2026-12-10T20:30:00-03:00",
                "precio": 6500,
            },
        ],
    }
    return respuesta


def _api_get_correcto(path, **kwargs):
    if path == "/cartelera":
        respuesta = Mock(status_code=200)
        respuesta.json.return_value = {"peliculas": []}
        return respuesta
    if path.startswith("/cartelera/"):
        return _respuesta_pelicula()
    if path.startswith("/funciones/") and path.endswith("/butacas"):
        return _respuesta_butacas()
    if path.startswith("/funciones/"):
        return _respuesta_funcion(int(path.rsplit("/", 1)[1]))
    if path.startswith("/peliculas/"):
        return _respuesta_pelicula()
    raise AssertionError(f"Consulta inesperada: {path}")


def _input_butaca(html, butaca_id):
    return re.search(
        rf'<input[^>]*id="butaca-{butaca_id}"[^>]*>',
        html,
        re.DOTALL,
    ).group()


def test_initial_pages_render(monkeypatch):
    monkeypatch.setattr(
        "app.routes.cliente.api_get",
        Mock(side_effect=_api_get_correcto),
    )
    app = create_app()
    app.config.update(TEST_CONFIG)

    client = app.test_client()
    paths = [
        "/",
        "/login",
        "/registro",
        "/peliculas/1",
        "/funciones/1/butacas",
        "/mis-entradas",
        "/admin/funciones",
        "/admin/salas",
        "/admin/servicios",
    ]

    for path in paths:
        assert client.get(path).status_code == 200

    respuesta = client.get("/admin/peliculas")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"] == "/login"
    assert client.get("/mis-compras").status_code == 302
    assert client.get("/entradas/1").status_code == 302

def test_admin_funciones_muestra_datos_api(monkeypatch):
    respuesta_api = Mock()
    respuesta_api.status_code = 200
    respuesta_api.json.return_value = {
        "funciones": [
            {
                "id": 12,
                "pelicula_id": 5,
                "sala_id": 2,
                "fecha_hora": "2026-11-20T20:00:00-03:00",
                "estado": "programada"
            }
        ]
    }
    respuesta_peliculas_api = Mock()
    respuesta_peliculas_api.status_code = 200
    respuesta_peliculas_api.json.return_value = {
        "peliculas": [
            {
                "id": 8,
                "titulo": "Titanic"
            }
        ]
    }
    respuesta_salas_api = Mock()
    respuesta_salas_api.status_code = 200
    respuesta_salas_api.json.return_value = {
        "salas": [{"id": 3, "nombre": "Sala Premium"}]
    }

    def api_get_simulado(ruta, **kwargs):
        if ruta == "/funciones":
            return respuesta_api

        if ruta == "/admin/peliculas":
            return respuesta_peliculas_api

        if ruta == "/salas":
            assert kwargs["headers"]["Authorization"] == "Bearer token-prueba"
            return respuesta_salas_api

        raise AssertionError(f"Ruta inesperada: {ruta}")


    monkeypatch.setattr(
        "app.routes.admin.api_get",
        api_get_simulado
    )

    app = create_app()
    app.config.update(TEST_CONFIG)

    client = app.test_client()

    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"

    respuesta = client.get("/admin/funciones")
    html = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 200
    assert "Función 12" in html
    assert "Pelicula 5" in html
    assert "programada" in html
    assert "1 funciones listadas" in html
    assert "Titanic" in html
    assert "Sala Premium" in html

def test_selector_salas_muestra_opciones():
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_request_context("/admin/funciones"):
        html = render_template(
            "administrador/funciones.html",
            funciones=[],
            peliculas=[],
            salas=[
                {"id": 3, "nombre": "Sala Premium"}
            ],
            mensaje_error=None
        )

    assert 'value="3"' in html
    assert "Sala Premium" in html

def test_crear_funcion_correctamente(monkeypatch):
    def api_get_simulado(ruta, **kwargs):
        respuesta = Mock()
        respuesta.status_code = 200

        if ruta == "/funciones":
            respuesta.json.return_value = {"funciones": []}
        elif ruta == "/admin/peliculas":
            respuesta.json.return_value = {"peliculas": []}
        elif ruta == "/salas":
            respuesta.json.return_value = {"salas": []}
        else:
            raise AssertionError(f"Ruta inesperada: {ruta}")

        return respuesta

    def api_post_simulado(ruta, **kwargs):
        assert ruta == "/funciones"
        assert kwargs["headers"]["Authorization"] == "Bearer token-prueba"

        datos = kwargs["json"]
        assert datos["pelicula_id"] == 5
        assert datos["sala_id"] == 2
        assert datos["precio"] == 3000
        assert datos["fecha_hora"] == "2026-11-20T20:00:00-03:00"

        respuesta = Mock()
        respuesta.status_code = 201
        return respuesta

    monkeypatch.setattr("app.routes.admin.api_get", api_get_simulado)
    monkeypatch.setattr("app.routes.admin.api_post", api_post_simulado)

    app = create_app()
    app.config.update(TEST_CONFIG)

    client = app.test_client()

    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"

    respuesta = client.post(
        "/admin/funciones",
        data={
            "pelicula_id": "5",
            "sala_id": "2",
            "fecha": "2026-11-20",
            "horario": "20:00",
            "precio": "3000"
        }
    )

    html = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 200
    assert "Función creada correctamente." in html


def test_crear_funcion_con_errores(monkeypatch):
    respuesta_api = Mock()
    respuesta_api.status_code = 200
    respuesta_api.json.return_value = {
        "funciones": [],
        "peliculas": [],
        "salas": []
    }

    monkeypatch.setattr(
        "app.routes.admin.api_get",
        lambda ruta, **kwargs: respuesta_api
    )

    api_post_simulado = Mock()
    monkeypatch.setattr(
        "app.routes.admin.api_post",
        api_post_simulado
    )

    app = create_app()
    app.config.update(TEST_CONFIG)

    client = app.test_client()

    # Caso 1: usuario sin iniciar sesión
    respuesta = client.post(
        "/admin/funciones",
        data={
            "pelicula_id": "5",
            "sala_id": "2",
            "fecha": "2026-11-20",
            "horario": "20:00",
            "precio": "3000"
        }
    )

    assert respuesta.status_code == 200
    assert "Tenés que iniciar sesión" in respuesta.get_data(as_text=True)
    api_post_simulado.assert_not_called()

    # Caso 2: administrador con precio inválido
    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"

    respuesta = client.post(
        "/admin/funciones",
        data={
            "pelicula_id": "5",
            "sala_id": "2",
            "fecha": "2026-11-20",
            "horario": "20:00",
            "precio": "abc"
        }
    )

    assert respuesta.status_code == 200
    assert "Revisá los datos ingresados" in respuesta.get_data(as_text=True)
    api_post_simulado.assert_not_called()


def test_admin_funciones_patch(monkeypatch):
    respuesta_get = Mock()
    respuesta_get.status_code = 200
    respuesta_get.json.return_value = {
        "funciones": [],
        "peliculas": [],
        "salas": []
    }

    respuesta_patch = Mock()
    respuesta_patch.status_code = 200

    patch_simulado = Mock(return_value=respuesta_patch)

    monkeypatch.setattr(
        "app.routes.admin.api_get",
        lambda ruta, **kwargs: respuesta_get
    )
    monkeypatch.setattr(
        "app.routes.admin.api_patch",
        patch_simulado
    )

    app = create_app()
    app.config.update(TEST_CONFIG)

    client = app.test_client()

    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"

    casos = [
        (
            "cancelar",
            {},
            {"estado": "cancelada"}
        ),
        (
            "publicar",
            {},
            {"estado": "programada"}
        ),
        (
            "editar",
            {
                "pelicula_id": "5",
                "sala_id": "2",
                "fecha": "2026-11-20",
                "horario": "20:00",
                "precio": "3000"
            },
            {
                "pelicula_id": 5,
                "sala_id": 2,
                "fecha_hora": "2026-11-20T20:00:00-03:00",
                "precio": 3000
            }
        )
    ]

    for accion, datos, json_esperado in casos:
        respuesta = client.post(
            "/admin/funciones",
            data={
                "accion": accion,
                "funcion_id": "12",
                **datos
            }
        )

        assert respuesta.status_code == 200
        assert "Función actualizada correctamente." in respuesta.get_data(
            as_text=True
        )

        patch_simulado.assert_called_with(
            "/funciones/12",
            json=json_esperado,
            headers={"Authorization": "Bearer token-prueba"}
        )

    # Sin autenticación no debe enviarse PATCH
    patch_simulado.reset_mock()

    cliente_sin_token = app.test_client()
    respuesta = cliente_sin_token.post(
        "/admin/funciones",
        data={
            "accion": "cancelar",
            "funcion_id": "12"
        }
    )

    assert "Tenés que iniciar sesión" in respuesta.get_data(as_text=True)
    patch_simulado.assert_not_called()
def test_butacas_se_consultan_y_solo_las_disponibles_se_habilitan(
    monkeypatch,
):
    api_get = Mock(side_effect=_api_get_correcto)
    monkeypatch.setattr("app.routes.cliente.api_get", api_get)
    app = create_app()
    app.config.update(TEST_CONFIG)

    respuesta = app.test_client().get("/funciones/7/butacas")
    html = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 200
    assert api_get.call_args_list[-1].args == ("/funciones/7/butacas",)
    assert api_get.call_count == 3
    assert "disabled" not in _input_butaca(html, 1)
    assert "disabled" in _input_butaca(html, 2)
    assert "disabled" in _input_butaca(html, 3)
    assert "disabled" in _input_butaca(html, 4)
    assert html.index("Butaca A1") < html.index("Butaca A2")
    assert "1 de 4" in html


def test_butacas_muestra_error_si_el_backend_no_responde(monkeypatch):
    monkeypatch.setattr(
        "app.routes.cliente.api_get",
        Mock(side_effect=requests.exceptions.ConnectionError),
    )
    app = create_app()
    app.config.update(TEST_CONFIG)

    respuesta = app.test_client().get("/funciones/7/butacas")

    assert respuesta.status_code == 200
    assert "No se pudo conectar con el servidor" in respuesta.get_data(
        as_text=True
    )


def test_butacas_muestra_error_si_la_funcion_no_existe(monkeypatch):
    respuesta_api = Mock()
    respuesta_api.status_code = 404
    respuesta_api.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=respuesta_api
    )
    monkeypatch.setattr(
        "app.routes.cliente.api_get",
        Mock(return_value=respuesta_api),
    )
    app = create_app()
    app.config.update(TEST_CONFIG)

    respuesta = app.test_client().get("/funciones/999/butacas")

    assert respuesta.status_code == 200
    assert "No se encontró la función seleccionada" in respuesta.get_data(
        as_text=True
    )


def test_login_guarda_token_y_usuario_en_la_sesion(monkeypatch):
    respuesta_api = Mock()
    respuesta_api.status_code = 200
    respuesta_api.json.return_value = {
        "token": "jwt-de-prueba",
        "usuario": {"id": 1, "nombre": "Cliente Demo", "rol": "cliente"},
    }
    api_post = Mock(return_value=respuesta_api)
    monkeypatch.setattr("app.routes.auth.api_post", api_post)
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        respuesta = client.post(
            "/login",
            data={
                "email": "cliente@cineparadiso.local",
                "password": "Cliente123!",
                "next": "/",
            },
        )
        with client.session_transaction() as sesion:
            assert sesion["access_token"] == "jwt-de-prueba"
            assert sesion["usuario"]["id"] == 1

    assert respuesta.status_code == 302
    api_post.assert_called_once()


def test_login_muestra_toast_con_error_de_credenciales(monkeypatch):
    respuesta_api = Mock()
    respuesta_api.status_code = 401
    respuesta_api.json.return_value = {
        "codigo": "CREDENCIALES_INVALIDAS",
        "mensaje": "Error de autenticación",
        "detalles": [
            {
                "campo": "general",
                "mensaje": "Email o contraseña incorrectos.",
            }
        ],
    }
    monkeypatch.setattr(
        "app.routes.auth.api_post",
        Mock(return_value=respuesta_api),
    )
    app = create_app()
    app.config.update(TEST_CONFIG)

    respuesta = app.test_client().post(
        "/login",
        data={
            "email": "cliente@cineparadiso.local",
            "password": "incorrecta",
        },
    )

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert 'class="login-toast"' in html
    assert 'role="alert"' in html
    assert "No pudimos iniciar sesión" in html
    assert "Email o contraseña incorrectos." in html
    assert 'value="cliente@cineparadiso.local"' in html


def test_login_muestra_toast_con_mensaje_del_servidor(monkeypatch):
    respuesta_api = Mock()
    respuesta_api.status_code = 500
    respuesta_api.json.return_value = {
        "codigo": "ERROR_INTERNO",
        "mensaje": "Error interno del servidor",
        "detalles": [
            {
                "campo": "general",
                "mensaje": "No fue posible procesar la solicitud.",
            }
        ],
    }
    monkeypatch.setattr(
        "app.routes.auth.api_post",
        Mock(return_value=respuesta_api),
    )
    app = create_app()
    app.config.update(TEST_CONFIG)

    respuesta = app.test_client().post(
        "/login",
        data={"email": "cliente@example.com", "password": "secreto"},
    )

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "El servidor tuvo un problema" in html
    assert "No fue posible procesar la solicitud." in html


def test_login_muestra_toast_si_no_hay_conexion(monkeypatch):
    monkeypatch.setattr(
        "app.routes.auth.api_post",
        Mock(side_effect=requests.exceptions.ConnectionError),
    )
    app = create_app()
    app.config.update(TEST_CONFIG)

    respuesta = app.test_client().post(
        "/login",
        data={"email": "cliente@example.com", "password": "secreto"},
    )

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "No pudimos conectar" in html
    assert "El servidor de autenticación no está disponible." in html


def test_navbar_distingue_ingreso_y_usuario_autenticado():
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        login_html = client.get("/login").get_data(as_text=True)
        assert "profile-link-login active" in login_html
        assert "Ingresar" in login_html

        with client.session_transaction() as sesion:
            sesion["access_token"] = "jwt-de-prueba"
            sesion["usuario"] = {"id": 1, "nombre": "Cliente Demo"}

        usuario_html = client.get("/login").get_data(as_text=True)
        assert "profile-link-user" in usuario_html
        assert 'class="profile-link-avatar"' in usuario_html
        assert ">C</span>" in usuario_html
        assert "Cliente Demo" in usuario_html


def test_perfil_muestra_boton_para_cerrar_sesion(monkeypatch):
    respuesta_api = Mock(status_code=200, ok=True)
    respuesta_api.json.return_value = {
        "id": 1,
        "nombre": "Cliente Demo",
        "email": "cliente@cineparadiso.local",
    }
    monkeypatch.setattr("app.routes.auth.api_get", Mock(return_value=respuesta_api))
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["access_token"] = "jwt-de-prueba"
            sesion["usuario"] = {
                "id": 1,
                "nombre": "Cliente Demo",
                "email": "cliente@cineparadiso.local",
            }

        respuesta = client.get("/perfil")

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert 'action="/logout"' in html
    assert 'method="post"' in html
    assert "Cerrar sesión" in html


def test_perfil_administrador_enlaza_panel_en_lugar_de_peliculas_vistas(
    monkeypatch,
):
    respuesta_api = Mock(status_code=200, ok=True)
    respuesta_api.json.return_value = {
        "id": 2,
        "nombre": "Administrador Demo",
        "email": "admin@cineparadiso.local",
        "rol": "administrador",
    }
    monkeypatch.setattr("app.routes.auth.api_get", Mock(return_value=respuesta_api))
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["access_token"] = "jwt-de-prueba"
            sesion["usuario"] = respuesta_api.json.return_value

        respuesta = client.get("/perfil")

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert 'href="/admin/peliculas"' in html
    assert "Panel de administración" in html
    assert "Películas vistas" not in html


def test_perfil_cliente_conserva_acceso_a_peliculas_vistas(monkeypatch):
    respuesta_api = Mock(status_code=200, ok=True)
    respuesta_api.json.return_value = {
        "id": 1,
        "nombre": "Cliente Demo",
        "email": "cliente@cineparadiso.local",
        "rol": "cliente",
    }
    monkeypatch.setattr("app.routes.auth.api_get", Mock(return_value=respuesta_api))
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["access_token"] = "jwt-de-prueba"
            sesion["usuario"] = respuesta_api.json.return_value

        respuesta = client.get("/perfil")

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert 'href="/peliculas-vistas"' in html
    assert "Películas vistas" in html
    assert "Panel de administración" not in html


def test_logout_limpia_la_sesion_y_redirige_a_cartelera():
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["access_token"] = "jwt-de-prueba"
            sesion["usuario"] = {"id": 1, "nombre": "Cliente Demo"}

        respuesta = client.post("/logout")

        with client.session_transaction() as sesion:
            assert "access_token" not in sesion
            assert "usuario" not in sesion

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"] == "/"


def test_confirmar_compra_envia_jwt_y_datos_a_la_api(monkeypatch):
    respuesta_api = Mock()
    respuesta_api.status_code = 202
    respuesta_api.json.return_value = {
        "id": "reserva-1",
        "estado": "pago_en_proceso",
        "compra_id": 55,
    }
    api_post = Mock(return_value=respuesta_api)
    monkeypatch.setattr("app.routes.cliente.api_post", api_post)
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["access_token"] = "jwt-de-prueba"
            sesion["checkout_id"] = "checkout-1"

        respuesta = client.post(
            "/compras/confirmar",
            data={
                "checkout_id": "checkout-1",
                    "reserva_id": "reserva-1",
                "medio_pago": "tarjeta",
            },
        )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith(
        "/reservas/reserva-1/pago-pendiente"
    )
    api_post.assert_called_once_with(
        "/reservas/reserva-1/pagos",
        json={
            "servicios": [],
            "medio_pago": "tarjeta",
        },
        headers={
            "Authorization": "Bearer jwt-de-prueba",
            "Idempotency-Key": "checkout-1",
        },
    )


def _api_get_resumen(path, **kwargs):
    if path == "/reservas/reserva-1":
        respuesta = Mock(status_code=200)
        respuesta.json.return_value = {
            "id": "reserva-1",
            "funcion_id": 1,
            "estado": "retenida",
            "expira_en": "2026-12-10T21:00:00Z",
            "butacas": [{"id": 1, "fila": "A", "numero": 1}],
        }
        return respuesta
    if path == "/servicios":
        respuesta = Mock()
        respuesta.status_code = 200
        respuesta.json.return_value = {"servicios": []}
        return respuesta
    return _api_get_correcto(path, **kwargs)


def test_resumen_no_se_cachea_y_habilita_una_confirmacion(monkeypatch):
    monkeypatch.setattr(
        "app.routes.cliente.api_get",
        Mock(side_effect=_api_get_resumen),
    )
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["access_token"] = "token-prueba"
        respuesta = client.get("/compras/resumen?reserva_id=reserva-1")

        with client.session_transaction() as sesion:
            checkout_id = sesion["checkout_id"]

    assert respuesta.status_code == 200
    assert respuesta.headers["Cache-Control"] == "no-store"
    assert (
        f'name="checkout_id" value="{checkout_id}"'
        in respuesta.get_data(as_text=True)
    )


def test_reenviar_el_formulario_no_crea_otra_compra(monkeypatch):
    # Issue #96: comprar, volver atrás y confirmar de nuevo el mismo carrito.
    respuesta_api = Mock()
    respuesta_api.status_code = 202
    respuesta_api.json.return_value = {
        "id": "reserva-1",
        "estado": "pago_en_proceso",
        "compra_id": 55,
    }
    api_post = Mock(return_value=respuesta_api)
    monkeypatch.setattr("app.routes.cliente.api_post", api_post)
    app = create_app()
    app.config.update(TEST_CONFIG)
    formulario = {
        "checkout_id": "checkout-1",
        "reserva_id": "reserva-1",
        "medio_pago": "tarjeta",
    }

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["access_token"] = "jwt-de-prueba"
            sesion["checkout_id"] = "checkout-1"

        primera = client.post("/compras/confirmar", data=formulario)
        segunda = client.post("/compras/confirmar", data=formulario)

    assert primera.headers["Location"].endswith(
        "/reservas/reserva-1/pago-pendiente"
    )
    assert segunda.headers["Location"].endswith(
        "/reservas/reserva-1/pago-pendiente"
    )
    api_post.assert_called_once()


def test_confirmar_con_un_resumen_vencido_no_llama_a_la_api(monkeypatch):
    api_post = Mock()
    monkeypatch.setattr("app.routes.cliente.api_post", api_post)
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["access_token"] = "jwt-de-prueba"
            sesion["checkout_id"] = "checkout-nuevo"

        respuesta = client.post(
            "/compras/confirmar",
            data={
                "checkout_id": "checkout-viejo",
                "reserva_id": "reserva-1",
            },
        )

    assert respuesta.status_code == 302
    assert "/compras/resumen" in respuesta.headers["Location"]
    api_post.assert_not_called()


def test_volver_al_resumen_de_una_compra_hecha_lleva_a_la_confirmacion(
    monkeypatch,
):
    respuesta = Mock(status_code=200)
    respuesta.json.return_value = {
        "id": "reserva-vendida",
        "funcion_id": 101,
        "estado": "vendida",
        "compra_id": 55,
        "butacas": [{"id": 16, "fila": "A", "numero": 1}],
    }
    api_get = Mock(return_value=respuesta)
    monkeypatch.setattr("app.routes.cliente.api_get", api_get)
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["access_token"] = "token-prueba"

        respuesta = client.get(
            "/compras/resumen?reserva_id=reserva-vendida"
        )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/compras/55/confirmacion")
    api_get.assert_called_once()


def test_volver_a_butacas_de_compra_finalizada_redirige_a_confirmacion(monkeypatch):
    api_get = Mock()
    monkeypatch.setattr("app.routes.cliente.api_get", api_get)

    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["ultima_compra"] = {
                "funcion_id": 7,
                "compra_id": 55,
                "checkout_id": "prueba-123",
            }

        respuesta = client.get("/funciones/7/butacas")

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith(
        "/compras/55/confirmacion"
    )
    api_get.assert_not_called()


def test_nueva_compra_permite_elegir_butacas(monkeypatch):
    respuesta_api = Mock()
    respuesta_api.status_code = 200
    respuesta_api.json.return_value = {
        "butacas": [],
        "total_butacas": 0,
        "butacas_libres": 0,
    }
    api_get = Mock(return_value=respuesta_api)

    monkeypatch.setattr("app.routes.cliente.api_get", api_get)
    monkeypatch.setattr(
        "app.routes.cliente._cargar_contexto_funcion",
        lambda funcion_id: {
            "id": funcion_id,
            "pelicula_id": 1,
            "pelicula": "Horizonte final",
            "fecha": "14/11/2026",
            "hora": "20:00",
            "sala": "Sala 1",
            "sucursal": "Centro",
            "precio": 6500,
        },
    )

    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["ultima_compra"] = {
                "funcion_id": 7,
                "compra_id": 55,
                "checkout_id": "prueba-123",
            }

        respuesta = client.get("/funciones/7/butacas?nueva_compra=1")

        with client.session_transaction() as sesion:
            assert "ultima_compra" not in sesion

    assert respuesta.status_code == 200
    assert "Seleccioná tus butacas" in respuesta.get_data(as_text=True)
    api_get.assert_called_once_with("/funciones/7/butacas")


def test_elegir_funcion_desde_cartelera_inicia_compra_nueva(monkeypatch):
    fecha_funcion = (datetime.now().date() + timedelta(days=1)).isoformat()
    respuesta_api = Mock()
    respuesta_api.status_code = 200
    respuesta_api.json.return_value = {
        "id": 1,
        "titulo": "Horizonte final",
        "poster_url": None,
        "clasificacion": "+13",
        "generos": ["Ciencia ficción"],
        "duracion_minutos": 120,
        "sinopsis": "Película de prueba",
        "funciones_disponibles": [
            {
                "id": 7,
                    "local_id": 1,
                "fecha_hora": f"{fecha_funcion}T20:00:00-03:00",
                "local_nombre": "Centro",
                "sala_nombre": "Sala 1",
                "precio": 6500,
            }
        ],
    }

    monkeypatch.setattr(
        "app.routes.cliente.api_get",
        Mock(return_value=respuesta_api),
    )

    app = create_app()
    app.config.update(TEST_CONFIG)

    respuesta = app.test_client().get("/peliculas/1?local_id=1")

    assert respuesta.status_code == 200
    assert (
        'href="/funciones/7/butacas?nueva_compra=1"'
        in respuesta.get_data(as_text=True)
    )
