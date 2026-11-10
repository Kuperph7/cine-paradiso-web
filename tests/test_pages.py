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
