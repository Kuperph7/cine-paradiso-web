from app import create_app


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

