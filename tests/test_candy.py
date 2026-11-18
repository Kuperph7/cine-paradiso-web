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
    if path == "/reservas/reserva-1":
        return _respuesta(
            {
                "id": "reserva-1",
                "funcion_id": 1,
                "estado": "retenida",
                "expira_en": "2026-12-10T21:00:00Z",
                "butacas": [{"id": 1, "fila": "A", "numero": 1}],
            }
        )
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
                    },
                    {
                        "id": 9,
                        "nombre": "Estacionamiento",
                        "descripcion": "Lugar de estacionamiento por 3 horas.",
                        "precio": 5000,
                        "activo": True,
                        "disponibles": 18,
                        "capacidad_maxima": 20,
                    },
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

    client = app.test_client()
    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"
    respuesta = client.get("/compras/servicios?reserva_id=reserva-1")

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "Combo Paradiso" in html
    assert "Progreso de la compra" in html
    assert "1. Función" in html
    assert "3. Candy" in html
    assert 'name="servicio_ids"' in html
    assert 'href="/compras/servicios?reserva_id=reserva-1"' in html
    assert [llamada.args[0] for llamada in api_get.call_args_list] == [
        "/reservas/reserva-1",
        "/servicios",
    ]


def test_candy_desde_navbar_muestra_catalogo_sin_flujo_de_compra(monkeypatch):
    api_get = Mock(side_effect=_api_get)
    monkeypatch.setattr("app.routes.cliente.api_get", api_get)
    app = create_app()
    app.config.update(TEST_CONFIG)

    client = app.test_client()
    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"
        sesion["reserva_activa"] = {"id": "reserva-1"}

    respuesta = client.get("/compras/servicios?vista=catalogo")

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "Combo Paradiso" in html
    assert "Progreso de la compra" not in html
    assert 'name="servicio_ids"' not in html
    assert "Continuar sin productos" not in html
    assert "Revisar compra" not in html
    assert "Ver cartelera" in html
    assert [llamada.args[0] for llamada in api_get.call_args_list] == [
        "/servicios",
    ]


def test_enlaces_generales_abren_candy_como_catalogo(monkeypatch):
    monkeypatch.setattr("app.routes.cliente.api_get", Mock(side_effect=_api_get))
    app = create_app()
    app.config.update(TEST_CONFIG)

    respuesta = app.test_client().get("/compras/servicios?vista=catalogo")

    html = respuesta.get_data(as_text=True)
    assert 'href="/compras/servicios?vista=catalogo"' in html


def test_butacas_continua_a_candy_y_candy_permite_omitir(monkeypatch):
    monkeypatch.setattr("app.routes.cliente.api_get", Mock(side_effect=_api_get))
    app = create_app()
    app.config.update(TEST_CONFIG)
    client = app.test_client()

    respuesta_butacas = client.get("/funciones/1/butacas")
    html_butacas = respuesta_butacas.get_data(as_text=True)

    assert respuesta_butacas.status_code == 200
    assert 'action="/funciones/1/reservas"' in html_butacas
    assert ">Continuar<" in html_butacas
    assert "Agregar productos de Candy" not in html_butacas

    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"
    respuesta_candy = client.get("/compras/servicios?reserva_id=reserva-1")
    html_candy = respuesta_candy.get_data(as_text=True)

    assert respuesta_candy.status_code == 200
    assert "Continuar sin productos" in html_candy
    assert "/compras/resumen?reserva_id=reserva-1" in html_candy


def test_resumen_conserva_candy_y_calcula_total(monkeypatch):
    monkeypatch.setattr("app.routes.cliente.api_get", Mock(side_effect=_api_get))
    app = create_app()
    app.config.update(TEST_CONFIG)

    client = app.test_client()
    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"
    respuesta = client.get(
        "/compras/resumen?reserva_id=reserva-1"
        "&servicio_ids=1&cantidad_1=2"
    )

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "2 × Combo Paradiso" in html
    assert "$29.600" in html
    assert 'name="cantidad_1" value="2"' in html


def test_estacionamiento_se_separa_de_candy_y_se_suma_en_resumen(monkeypatch):
    monkeypatch.setattr("app.routes.cliente.api_get", Mock(side_effect=_api_get))
    app = create_app()
    app.config.update(TEST_CONFIG)

    client = app.test_client()
    with client.session_transaction() as sesion:
        sesion["access_token"] = "token-prueba"

    respuesta_servicios = client.get("/compras/servicios?reserva_id=reserva-1")
    html_servicios = respuesta_servicios.get_data(as_text=True)
    assert respuesta_servicios.status_code == 200
    assert "Estacionamiento" not in html_servicios
    assert "1 opciones disponibles" in html_servicios

    respuesta_resumen_sin_est = client.get("/compras/resumen?reserva_id=reserva-1")
    html_resumen_sin_est = respuesta_resumen_sin_est.get_data(as_text=True)
    assert respuesta_resumen_sin_est.status_code == 200
    assert "18 de 20 lugares disponibles" in html_resumen_sin_est

    respuesta_resumen = client.get(
        "/compras/resumen?reserva_id=reserva-1"
        "&servicio_ids=9&cantidad_9=2"
    )
    html_resumen = respuesta_resumen.get_data(as_text=True)
    assert respuesta_resumen.status_code == 200
    assert "Reservaste 2 plazas de estacionamiento" in html_resumen
    assert "$10.000" in html_resumen
    assert 'name="cantidad_9" value="2"' in html_resumen


def test_continuar_retiene_butacas_antes_de_ir_a_candy(monkeypatch):
    respuesta_api = _respuesta(
        {
            "id": "reserva-1",
            "funcion_id": 1,
            "estado": "retenida",
        },
        estado=201,
    )
    api_post = Mock(return_value=respuesta_api)
    monkeypatch.setattr("app.routes.cliente.api_post", api_post)
    app = create_app()
    app.config.update(TEST_CONFIG)

    with app.test_client() as client:
        with client.session_transaction() as sesion:
            sesion["access_token"] = "token-prueba"
        respuesta = client.post(
            "/funciones/1/reservas",
            data={"butaca_ids": ["1", "2"]},
        )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith(
        "/compras/servicios?reserva_id=reserva-1"
    )
    api_post.assert_called_once_with(
        "/funciones/1/reservas",
        json={"butaca_ids": [1, 2]},
        headers={"Authorization": "Bearer token-prueba"},
    )
