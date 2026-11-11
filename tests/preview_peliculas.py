from unittest.mock import Mock, patch
from flask import session
from app import create_app

app = create_app()
app.config.update(
    SECRET_KEY="solo-para-vista-previa-local",
    SESSION_COOKIE_NAME="vista_previa_peliculas",
    SESSION_COOKIE_SECURE=False,
    DEBUG=False,
)

peliculas = [{
    "id": 1,
    "id_externo": 101,
    "titulo": "Película local de prueba",
    "sinopsis": "Esta película existe solamente en la vista previa.",
    "poster_url": "https://example.com/poster.jpg",
    "duracion_minutos": 120,
    "clasificacion": "ATP",
    "genero": "Drama",
    "activa": True,
}]

catalogo = [{
    "id_externo": 202,
    "titulo": "Avatar de prueba",
    "sinopsis": "Resultado simulado del catálogo externo.",
    "poster_url": "https://example.com/avatar.jpg",
}]


@app.before_request
def sesion_de_prueba():
    session["access_token"] = "credencial-simulada"


def respuesta_simulada(estado, datos):
    respuesta = Mock(status_code=estado)
    respuesta.json.return_value = datos
    return respuesta


def api_simulada(method, path, **kwargs):
    parametros = kwargs.get("params", {})
    titulo = parametros.get("titulo", "").strip().casefold()

    if method == "GET" and path in (
        "/admin/peliculas",
        "/admin/peliculas/externas",
    ):
        if titulo == "error":
            return respuesta_simulada(503, {
                "mensaje": "Error simulado: catálogo no disponible."
            })

        origen = catalogo if path.endswith("/externas") else peliculas
        resultados = [
            pelicula.copy() for pelicula in origen
            if titulo in pelicula["titulo"].casefold()
        ]
        return respuesta_simulada(200, {"peliculas": resultados})

    if method == "POST" and path == "/admin/peliculas":
        datos = kwargs.get("json", {}).copy()

        if datos.get("titulo", "").casefold() == "error":
            return respuesta_simulada(400, {
                "mensaje": "Error simulado: revisá el título."
            })

        if datos.get("id_externo") is not None and any(
            pelicula.get("id_externo") == datos["id_externo"]
            for pelicula in peliculas
        ):
            return respuesta_simulada(409, {
                "mensaje": "La película ya existe."
            })

        datos["id"] = max((p["id"] for p in peliculas), default=0) + 1
        datos["activa"] = True
        peliculas.append(datos)
        return respuesta_simulada(201, datos.copy())

    if method == "PATCH" and path.startswith("/admin/peliculas/"):
        identificador = path.rsplit("/", 1)[-1]
        pelicula = next(
            (p for p in peliculas if str(p["id"]) == identificador),
            None,
        )

        if pelicula is None:
            return respuesta_simulada(404, {
                "mensaje": "La película no existe."
            })

        datos = kwargs.get("json", {})

        if datos.get("titulo", "").casefold() == "error":
            return respuesta_simulada(400, {
                "mensaje": "Error simulado: revisá el título."
            })

        pelicula.update(datos)
        return respuesta_simulada(200, pelicula.copy())

    return respuesta_simulada(404, {
        "mensaje": "Operación no simulada."
    })


if __name__ == "__main__":
    with patch("app.services.api_client.api_request", side_effect=api_simulada):
        app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)