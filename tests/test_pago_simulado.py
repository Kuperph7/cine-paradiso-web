from unittest.mock import Mock

from app import create_app


TEST_CONFIG = {
    "TESTING": True,
    "DEBUG": False,
    "SECRET_KEY": "test",
    "API_BASE_URL": "http://api.test",
}


def _respuesta(datos, estado=200):
    respuesta = Mock(status_code=estado, ok=200 <= estado < 400)
    respuesta.json.return_value = datos
    return respuesta


def test_cartelera_permite_continuar_un_pago_activo(monkeypatch):
    def api_get_simulado(ruta, **_kwargs):
        if ruta == "/cartelera":
            return _respuesta({"peliculas": []})
        if ruta == "/reservas/activa":
            return _respuesta(
                {
                    "reserva": {
                        "id": "reserva-1",
                        "funcion_id": 1,
                        "estado": "pago_en_proceso",
                        "expira_en": "2026-12-10T21:00:00Z",
                        "butacas": [
                            {"id": 1, "fila": "A", "numero": 1},
                            {"id": 2, "fila": "A", "numero": 2},
                        ],
                    }
                }
            )
        raise AssertionError(f"Consulta inesperada: {ruta}")

    monkeypatch.setattr("app.routes.cliente.api_get", api_get_simulado)
    app = create_app()
    app.config.update(TEST_CONFIG)
    client = app.test_client()
    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"

    respuesta = client.get("/")
    html = respuesta.get_data(as_text=True)
    texto = " ".join(html.split())

    assert respuesta.status_code == 200
    assert "Continuar con la compra" in html
    assert "A1 · A2" in texto
    assert '/reservas/reserva-1/pago-pendiente' in html


def test_pantalla_de_pago_ofrece_confirmar_o_cancelar(monkeypatch):
    monkeypatch.setattr(
        "app.routes.cliente.api_get",
        Mock(
            return_value=_respuesta(
                {
                    "id": "reserva-1",
                    "funcion_id": 1,
                    "estado": "pago_en_proceso",
                    "expira_en": "2026-12-10T21:00:00Z",
                    "butacas": [{"id": 1, "fila": "A", "numero": 1}],
                }
            )
        ),
    )
    app = create_app()
    app.config.update(TEST_CONFIG)
    client = app.test_client()
    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"

    respuesta = client.get("/reservas/reserva-1/pago-pendiente")
    html = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 200
    assert "Pagar y confirmar compra" in html
    assert "Cancelar compra" in html
    assert "Volver a cartelera y continuar más tarde" in html
    assert "La confirmación debe llegar desde el proveedor" not in html


def test_pago_simulado_aprobado_redirige_a_confirmacion(monkeypatch):
    compra = {
        "id": 41,
        "funcion_id": 7,
        "estado": "confirmada",
        "entradas": [{"butaca": {"id": 3}}],
    }
    api_post = Mock(return_value=_respuesta(compra))
    monkeypatch.setattr("app.routes.cliente.api_post", api_post)
    app = create_app()
    app.config.update(TEST_CONFIG)
    client = app.test_client()
    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"
        sesion["reserva_activa"] = {"id": "reserva-1"}
        sesion["ultimo_pago"] = {"reserva_id": "reserva-1"}

    respuesta = client.post(
        "/reservas/reserva-1/pago-simulado",
        data={"resultado": "aprobado"},
    )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"] == "/compras/41/confirmacion"
    api_post.assert_called_once_with(
        "/reservas/reserva-1/pagos/simular",
        json={"resultado": "aprobado"},
        headers={"Authorization": "Bearer token-prueba"},
    )
    with client.session_transaction() as sesion:
        assert "reserva_activa" not in sesion
        assert "ultimo_pago" not in sesion
        assert sesion["ultima_compra"]["compra_id"] == 41


def test_cancelar_pago_simulado_vuelve_a_cartelera(monkeypatch):
    api_post = Mock(
        return_value=_respuesta(
            {"id": "reserva-1", "estado": "pago_rechazado"}
        )
    )
    monkeypatch.setattr("app.routes.cliente.api_post", api_post)
    app = create_app()
    app.config.update(TEST_CONFIG)
    client = app.test_client()
    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"
        sesion["reserva_activa"] = {"id": "reserva-1"}

    respuesta = client.post(
        "/reservas/reserva-1/pago-simulado",
        data={"resultado": "cancelado"},
    )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"] == "/"
    api_post.assert_called_once_with(
        "/reservas/reserva-1/pagos/simular",
        json={"resultado": "cancelado"},
        headers={"Authorization": "Bearer token-prueba"},
    )
