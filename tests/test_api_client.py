from unittest.mock import Mock

from app import create_app
from app.services.api_client import api_get


# Este archivo se ejecuta únicamente al iniciar pytest o al usar "Run Test".
# Abrir la aplicación en Google Chrome mediante el servidor Flask no importa
# estos tests, no activa monkeypatch y utiliza las llamadas HTTP reales.


class TestConfig:
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test"
    API_BASE_URL = "http://api.test"


def test_api_get_construye_la_url_del_backend(monkeypatch):
    # monkeypatch reemplaza requests.request solamente durante este test.
    # No modifica api_client ni evita que la aplicación real consulte el
    # backend: permite comprobar la URL construida sin realizar tráfico HTTP.
    request = Mock()
    monkeypatch.setattr(
        "app.services.api_client.requests.request",
        request,
    )
    app = create_app(TestConfig)

    with app.app_context():
        api_get("/funciones/7/butacas")

    request.assert_called_once_with(
        "GET",
        "http://api.test/funciones/7/butacas",
        timeout=10,
    )
