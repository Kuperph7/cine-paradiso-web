from unittest.mock import Mock

from app import create_app


TEST_CONFIG = {
    "TESTING": True,
    "DEBUG": False,
    "SECRET_KEY": "test",
    "API_BASE_URL": "http://api.test",
}


def _respuesta(datos, estado=200):
    respuesta = Mock(status_code=estado)
    respuesta.json.return_value = datos
    return respuesta


def _api_get(path, **kwargs):
    if path == "/servicios":
        return _respuesta(
            {
                "servicios": [
                    {
                        "id": 1,
                        "nombre": "Combo Paradiso",
                        "descripcion": "Pochoclos y gaseosas",
                        "precio": 14800,
                        "activo": True,
                    }
                ]
            }
        )
    if path == "/funciones/1":
        return _respuesta(
            {
                "id": 1,
                "pelicula_id": 1,
                "sala_id": 1,
                "fecha_hora": "2026-12-10T18:30:00-03:00",
                "precio": 6500,
                "estado": "programada",
            }
        )
    if path == "/peliculas/1":
        return _respuesta(
            {
                "id": 1,
                "titulo": "Horizonte final",
                "clasificacion": "+13",
                "poster_url": None,
                "funciones_disponibles": [
                    {
                        "id": 1,
                        "sala_nombre": "Sala 1",
                        "local_nombre": "Cine Paradiso Centro",
                    }
                ],
            }
        )
    if path == "/funciones/1/butacas":
        return _respuesta(
            {
                "funcion_id": 1,
                "butacas": [
                    {
                        "id": 1,
                        "fila": "A",
                        "numero": 1,
                        "estado": "disponible",
                    }
                ],
            }
        )
    raise AssertionError(f"Consulta inesperada: {path}")


def test_candy_renderiza_catalogo_obtenido_del_backend(monkeypatch):
    api_get = Mock(side_effect=_api_get)
    monkeypatch.setattr("app.routes.cliente.api_get", api_get)
    app = create_app()
    app.config.update(TEST_CONFIG)

    respuesta = app.test_client().get(
        "/compras/servicios?funcion_id=1&butaca_ids=1"
    )

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "Combo Paradiso" in html
    assert 'name="servicio_ids"' in html
    api_get.assert_called_once_with("/servicios")


def test_resumen_conserva_candy_y_calcula_total(monkeypatch):
    monkeypatch.setattr("app.routes.cliente.api_get", Mock(side_effect=_api_get))
    app = create_app()
    app.config.update(TEST_CONFIG)

    respuesta = app.test_client().get(
        "/compras/resumen?funcion_id=1&butaca_ids=1"
        "&servicio_ids=1&cantidad_1=2"
    )

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "2 × Combo Paradiso" in html
    assert "$29.600" in html
    assert 'name="cantidad_1" value="2"' in html
