import re
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
                "sala_nombre": "Sala 1",
                "local_nombre": "Cine Paradiso Centro",
            },
            {
                "id": 7,
                "sala_nombre": "Sala 1",
                "local_nombre": "Cine Paradiso Centro",
            },
        ],
    }
    return respuesta


def _api_get_correcto(path, **kwargs):
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
        "/perfil",
        "/peliculas/1",
        "/funciones/1/butacas",
        "/compras/servicios",
        "/compras/resumen?funcion_id=1&butaca_ids=1",
        "/mis-entradas",
        "/admin/funciones",
        "/admin/salas",
        "/admin/servicios",
        "/admin/estadisticas",
        "/admin/entradas/validar",
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
        sesion["token"] = "token-prueba"

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
        sesion["token"] = "token-prueba"

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
        sesion["token"] = "token-prueba"

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
        sesion["token"] = "token-prueba"

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
    app = create_app(TestConfig)

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
    app = create_app(TestConfig)

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
    app = create_app(TestConfig)

    respuesta = app.test_client().post(
        "/login",
        data={"email": "cliente@example.com", "password": "secreto"},
    )

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "No pudimos conectar" in html
    assert "El servidor de autenticación no está disponible." in html


def test_navbar_distingue_ingreso_y_usuario_autenticado():
    app = create_app(TestConfig)

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


def test_perfil_muestra_boton_para_cerrar_sesion():
    app = create_app(TestConfig)

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


def test_logout_limpia_la_sesion_y_redirige_a_cartelera():
    app = create_app(TestConfig)

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
    respuesta_api.status_code = 201
    respuesta_api.json.return_value = {"id": 55}
    api_post = Mock(return_value=respuesta_api)
    monkeypatch.setattr("app.routes.cliente.api_post", api_post)
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["access_token"] = "jwt-de-prueba"

        respuesta = client.post(
            "/compras/confirmar",
            data={
                "funcion_id": "101",
                "butaca_ids": ["16", "17"],
                "medio_pago": "tarjeta",
            },
        )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith(
        "/compras/55/confirmacion"
    )
    api_post.assert_called_once_with(
        "/compras",
        json={
            "funcion_id": 101,
            "butaca_ids": [16, 17],
            "servicios": [],
            "medio_pago": "tarjeta",
        },
        headers={"Authorization": "Bearer jwt-de-prueba"},
    )
