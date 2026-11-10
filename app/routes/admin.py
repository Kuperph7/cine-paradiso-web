from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, render_template, session, request
from requests.exceptions import RequestException

from app.services.api_client import api_get,api_post

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/peliculas")
def peliculas():
    return render_template("administrador/peliculas.html")


@admin_bp.route("/funciones", methods=["GET", "POST"])
def funciones():
    funciones = []
    peliculas = []
    salas = []
    mensaje_error = None
    mensaje_salas = None
    mensaje_accion = None

    token = session.get("token")

    if request.method == "POST":
        if not token:
            mensaje_accion = "Tenés que iniciar sesión como administrador."
        else:
            try:
                pelicula_id = int(request.form.get("pelicula_id", ""))
                sala_id = int(request.form.get("sala_id", ""))
                precio = int(request.form.get("precio", ""))

                fecha = request.form.get("fecha", "")
                horario = request.form.get("horario", "")

                fecha_hora = datetime.fromisoformat(
                    f"{fecha}T{horario}"
                ).replace(
                    tzinfo=ZoneInfo("America/Argentina/Buenos_Aires")
                )

                if pelicula_id <= 0 or sala_id <= 0 or precio < 0:
                    raise ValueError("Datos inválidos")

                datos_funcion = {
                    "pelicula_id": pelicula_id,
                    "sala_id": sala_id,
                    "fecha_hora": fecha_hora.isoformat(timespec="seconds"),
                    "precio": precio
                }

                respuesta_creacion = api_post(
                    "/funciones",
                    json=datos_funcion,
                    headers={"Authorization": f"Bearer {token}"}
                )

                if respuesta_creacion.status_code == 201:
                    mensaje_accion = "Función creada correctamente."
                elif respuesta_creacion.status_code in (401, 403):
                    mensaje_accion = "No tenés permisos para crear funciones."
                else:
                    mensaje_accion = "No se pudo crear la función."

            except ValueError:
                mensaje_accion = "Revisá los datos ingresados."

            except RequestException:
                mensaje_accion = "No fue posible conectar con la API."


    try:
        respuesta = api_get("/funciones")

        if respuesta.status_code == 200:
            datos = respuesta.json()
            funciones = datos.get("funciones", [])
        else:
            mensaje_error = "No pudieron cargar las funciones"

    except (RequestException, ValueError):
        mensaje_error = "No fue posible conectar con la API"

    try:
        respuesta_peliculas = api_get("/admin/peliculas")

        if respuesta_peliculas.status_code == 200:
            datos_peliculas = respuesta_peliculas.json()
            peliculas = datos_peliculas.get("peliculas", [])

    except (RequestException, ValueError):
        peliculas = []

    if token:
        try:
            respuesta_salas = api_get(
                "/salas",
                headers={"Authorization": f"Bearer {token}"}
            )

            if respuesta_salas.status_code == 200:
                datos_salas = respuesta_salas.json()
                salas = datos_salas.get("salas", [])
            else:
                mensaje_salas = "No se pudieron cargar las salas."

        except (RequestException, ValueError):
            mensaje_salas = "No fue posible conectar con la API de salas."
    else:
        mensaje_salas = "Iniciá sesión como administrador para cargar las salas."



    return render_template(
        "administrador/funciones.html",
        funciones=funciones,
        peliculas=peliculas,
        salas=salas,
        mensaje_salas=mensaje_salas,
        mensaje_error=mensaje_error,
        mensaje_accion=mensaje_accion
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

