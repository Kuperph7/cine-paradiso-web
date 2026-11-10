from flask import Blueprint, render_template
from requests.exceptions import RequestException
from app.services.api_client import api_get

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/peliculas")
def peliculas():
    return render_template("administrador/peliculas.html")


@admin_bp.get("/funciones")
def funciones():
    funciones = []
    mensaje_error = None

    try:
        respuesta = api_get("/funciones")

        if respuesta.status_code == 200:
            datos = respuesta.json()
            funciones = datos.get("funciones", [])
        else:
            mensaje_error = "No pudieron cargar las funciones"

    except (RequestException, ValueError):
        mensaje_error = "No fue posible conectar con la API"

    return render_template(
        "administrador/funciones.html",
        funciones=funciones,
        mensaje_error=mensaje_error
    )


@admin_bp.get("/salas")
def salas():
    return render_template("administrador/salas.html")


@admin_bp.get("/servicios")
def servicios():
    return render_template("administrador/servicios.html")


@admin_bp.get("/estadisticas")
def estadisticas():
    return render_template("administrador/estadisticas.html")


@admin_bp.get("/entradas/validar")
def validar_entrada():
    return render_template("administrador/validar_entrada.html")

