from app import create_app
from unittest.mock import Mock

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
    def api_get_simulado(ruta):
        assert ruta == "/funciones"
        return respuesta_api

    monkeypatch.setattr(
        "app.routes.admin.api_get",
        api_get_simulado
    )

    app = create_app(TestConfig)
    client = app.test_client()

    respuesta = client.get("/admin/funciones")
    html = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 200
    assert "Función 12" in html
    assert "Pelicula 5" in html
    assert "programada" in html
    assert "1 funciones listadas" in html

