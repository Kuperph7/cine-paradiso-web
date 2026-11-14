from unittest.mock import Mock, patch

import pytest

from app import create_app


@pytest.fixture
def cliente():
    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY="solo-para-pruebas")
    cliente = app.test_client()

    with cliente.session_transaction() as sesion:
        sesion["access_token"] = "credencial-simulada"
        sesion["usuario"] = {
            "nombre": "Administrador de prueba",
            "rol": "administrador",
        }

    with patch(
        "app.services.api_client.api_request",
        side_effect=AssertionError("La prueba no debe llamar a la API real."),
    ):
        yield cliente

@pytest.fixture
def formulario():
    return {
        "titulo": "Película de prueba",
        "sinopsis": "Sinopsis de prueba",
        "poster_url": "https://example.com/poster.jpg",
        "duracion_minutos": "120",
        "clasificacion": "ATP",
        "genero": "Drama",
        "id_externo": "123",
    }


def test_crear_pelicula_correctamente(cliente, formulario):
    respuesta_api = Mock(status_code=201)

    with patch("app.routes.admin.api_post", return_value=respuesta_api) as crear:
        respuesta = cliente.post("/admin/peliculas/crear", data=formulario)

    assert respuesta.status_code == 303
    assert "/admin/peliculas" in respuesta.headers["Location"]
    assert crear.call_count == 1
    assert crear.call_args.args == ("/admin/peliculas",)
    assert crear.call_args.kwargs["headers"] == {
        "Authorization": "Bearer credencial-simulada"
    }
    assert crear.call_args.kwargs["json"] == {
        **formulario,
        "duracion_minutos": 120,
        "id_externo": 123,
    }


def test_crear_con_duracion_invalida(cliente, formulario):
    formulario["duracion_minutos"] = "0"
    listado = Mock(status_code=200)
    listado.json.return_value = {"peliculas": []}

    with patch("app.routes.admin.api_post") as crear:
        with patch("app.routes.admin.api_get", return_value=listado):
            respuesta = cliente.post("/admin/peliculas/crear", data=formulario)

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 400
    crear.assert_not_called()
    assert "La duración debe ser un número entero positivo." in html
    assert 'value="Película de prueba"' in html
    assert 'value="0"' in html
    assert 'data-con-errores="true"' in html


def test_crear_muestra_error_del_backend(cliente, formulario):
    respuesta_api = Mock(status_code=409)
    respuesta_api.json.return_value = {
        "mensaje": "La película ya existe.",
        "detalles": [],
    }
    listado = Mock(status_code=200)
    listado.json.return_value = {"peliculas": []}

    with patch("app.routes.admin.api_post", return_value=respuesta_api):
        with patch("app.routes.admin.api_get", return_value=listado):
            respuesta = cliente.post("/admin/peliculas/crear", data=formulario)

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 409
    assert "La película ya existe." in html
    assert 'value="Película de prueba"' in html
    assert "Sinopsis de prueba" in html
    assert 'value="123"' in html
    assert 'data-con-errores="true"' in html

def test_modificar_pelicula_correctamente(cliente, formulario):
    respuesta_api = Mock(status_code=200)

    with patch("app.routes.admin.api_patch", return_value=respuesta_api) as modificar:
        respuesta = cliente.post("/admin/peliculas/12/modificar", data=formulario)

    assert respuesta.status_code == 303
    assert modificar.call_count == 1
    assert modificar.call_args.args == ("/admin/peliculas/12",)
    datos = modificar.call_args.kwargs["json"]
    assert datos["titulo"] == formulario["titulo"]
    assert datos["duracion_minutos"] == 120
    assert "id_externo" not in datos
    assert "pelicula_id" not in datos

def test_modificar_conserva_formulario_si_falla(cliente, formulario):
    respuesta_api = Mock(status_code=400)
    respuesta_api.json.return_value = {
        "mensaje": "La clasificación no es válida.",
        "detalles": [],
    }
    listado = Mock(status_code=200)
    listado.json.return_value = {"peliculas": []}

    with patch("app.routes.admin.api_patch", return_value=respuesta_api):
        with patch("app.routes.admin.api_get", return_value=listado):
            respuesta = cliente.post("/admin/peliculas/12/modificar", data=formulario)

    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 400
    assert "La clasificación no es válida." in html
    assert 'value="Película de prueba"' in html
    assert 'name="pelicula_id" id="pelicula-id" value="12"' in html
    assert 'action="/admin/peliculas/12/modificar?' in html
    assert 'data-con-errores="true"' in html

def test_desactivar_pelicula_correctamente(cliente):
    respuesta_api = Mock(status_code=200)
    listado = Mock(status_code=200)
    listado.json.return_value = {"peliculas": []}

    with patch("app.routes.admin.api_patch", return_value=respuesta_api) as desactivar:
        respuesta = cliente.post("/admin/peliculas/12/desactivar?titulo=Avatar")

    assert respuesta.status_code == 303
    assert "titulo=Avatar" in respuesta.headers["Location"]
    assert desactivar.call_args.args == ("/admin/peliculas/12",)
    assert desactivar.call_args.kwargs["json"] == {"activa": False}

    with patch("app.routes.admin.api_get", return_value=listado):
        pagina = cliente.get(respuesta.headers["Location"])

    assert "Película desactivada correctamente." in pagina.get_data(as_text=True)

def test_desactivar_muestra_error_del_backend(cliente):
    respuesta_api = Mock(status_code=403)
    respuesta_api.json.return_value = {
        "mensaje": "Permiso denegado.",
        "detalles": [],
    }
    listado = Mock(status_code=200)
    listado.json.return_value = {"peliculas": []}

    with patch("app.routes.admin.api_patch", return_value=respuesta_api):
        respuesta = cliente.post("/admin/peliculas/12/desactivar")

    assert respuesta.status_code == 303

    with patch("app.routes.admin.api_get", return_value=listado):
        pagina = cliente.get(respuesta.headers["Location"])

    html = pagina.get_data(as_text=True)
    assert "Permiso denegado." in html
    assert "Película desactivada correctamente." not in html