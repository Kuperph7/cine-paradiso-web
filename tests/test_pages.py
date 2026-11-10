from app import create_app
from unittest.mock import Mock
from flask import render_template

class TestConfig:
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test"
    API_BASE_URL = "http://api.test"


def test_initial_pages_render():
    app = create_app(TestConfig)
    client = app.test_client()
    paths = [
        "/",
        "/login",
        "/registro",
        "/perfil",
        "/peliculas/1",
        "/funciones/1/butacas",
        "/compras/servicios",
        "/compras/resumen",
        "/mis-compras",
        "/mis-entradas",
        "/entradas/1",
        "/admin/peliculas",
        "/admin/funciones",
        "/admin/salas",
        "/admin/servicios",
        "/admin/estadisticas",
        "/admin/entradas/validar",
    ]

    for path in paths:
        assert client.get(path).status_code == 200

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

    app = create_app(TestConfig)
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
    app = create_app(TestConfig)

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

    app = create_app(TestConfig)
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

    app = create_app(TestConfig)
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

    app = create_app(TestConfig)
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
