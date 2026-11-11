from unittest.mock import Mock

from app import create_app
from app.services.api_client import api_get

TEST_CONFIG = {
    "TESTING": True,
    "DEBUG": False,
    "SECRET_KEY": "test",
    "API_BASE_URL": "http://api.test",
}

def test_api_get_construye_la_url_del_backend(monkeypatch):
    request = Mock()

    monkeypatch.setattr(
        "app.services.api_client.requests.request",
        request,
    )

    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.app_context():
        api_get("/funciones/7/butacas")

    request.assert_called_once_with(
        "GET",
        "http://api.test/funciones/7/butacas",
        timeout=10,
    )
