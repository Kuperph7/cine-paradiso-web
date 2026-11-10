import requests
from flask import Blueprint, redirect, render_template, session, url_for, request, flash

from app.services.api_client import api_get, api_post, api_patch


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def obtener_errores_api(respuesta):
    try:
        datos = respuesta.json()
    except ValueError:
        return ["El servidor devolvió una respuesta inválida."]

    if not isinstance(datos, dict):
        return ["El servidor devolvió una respuesta inválida."]

    errores = []
    detalles = datos.get("detalles", [])

    if isinstance(detalles, list):
        for detalle in detalles:
            if isinstance(detalle, dict):
                mensaje = detalle.get("mensaje")
                if isinstance(mensaje, str) and mensaje:
                    errores.append(mensaje)

    if errores:
        return errores

    mensaje = datos.get("mensaje")
    if isinstance(mensaje, str) and mensaje:
        return [mensaje]

    return ["No fue posible completar la operación."]


def preparar_datos_pelicula(formulario):
    datos = {}
    errores = []
    campos_texto = ("titulo", "sinopsis", "poster_url", "clasificacion", "genero")

    for campo in campos_texto:
        datos[campo] = formulario.get(campo, "").strip()

    duracion = formulario.get("duracion_minutos", "").strip()
    try:
        datos["duracion_minutos"] = int(duracion)
    except ValueError:
        errores.append("La duración debe ser un número entero positivo.")
    else:
        if datos["duracion_minutos"] <= 0:
            errores.append("La duración debe ser un número entero positivo.")

    id_externo = formulario.get("id_externo", "").strip()
    if id_externo:
        try:
            datos["id_externo"] = int(id_externo)
        except ValueError:
            errores.append("El identificador externo debe ser un número entero.")

    return datos, errores


@admin_bp.get("/peliculas")
def peliculas():
    return renderizar_peliculas()


def renderizar_peliculas(formulario=None, errores_formulario=None):
    credencial_acceso = session.get("credencial_acceso")
    if not credencial_acceso:
        return redirect(url_for("auth.login"))

    titulo = request.args.get("titulo", "").strip()
    titulo_externo = request.args.get("titulo_externo", "").strip()
    peliculas_sistema = []
    peliculas_externas = []
    errores = []
    errores_externos = []

    try:
        respuesta = api_get(
            "/admin/peliculas",
            headers={"Authorization": f"Bearer {credencial_acceso}"},
            params={"incluir_inactivas": "true", "titulo": titulo},
        )
        if respuesta.status_code == 200:
            datos = respuesta.json()
            if not isinstance(datos, dict):
                raise ValueError("Respuesta inválida")
            peliculas_sistema = datos["peliculas"]
            if not isinstance(peliculas_sistema, list):
                raise ValueError("Listado inválido")
        else:
            errores = obtener_errores_api(respuesta)
    except requests.exceptions.JSONDecodeError:
        errores = ["La API devolvió una respuesta inválida."]
    except requests.RequestException:
        errores = ["No fue posible conectar con la API. Intentá nuevamente."]
    except (ValueError, KeyError, TypeError):
        peliculas_sistema = []
        errores = ["La API devolvió un listado de películas inválido."]

    if titulo_externo:
        try:
            respuesta_externa = api_get(
                "/admin/peliculas/externas",
                headers={"Authorization": f"Bearer {credencial_acceso}"},
                params={"titulo": titulo_externo},
            )
            if respuesta_externa.status_code == 200:
                datos_externos = respuesta_externa.json()
                if not isinstance(datos_externos, dict):
                    raise ValueError("Respuesta inválida")
                peliculas_externas = datos_externos["peliculas"]
                if not isinstance(peliculas_externas, list):
                    raise ValueError("Listado inválido")
            else:
                errores_externos = obtener_errores_api(respuesta_externa)
        except requests.exceptions.JSONDecodeError:
            errores_externos = ["El catálogo externo devolvió una respuesta inválida."]
        except requests.RequestException:
            errores_externos = ["No fue posible conectar con la API. Intentá nuevamente."]
        except (ValueError, KeyError, TypeError):
            peliculas_externas = []
            errores_externos = ["El catálogo externo devolvió un listado inválido."]

    return render_template(
        "administrador/peliculas.html",
        peliculas=peliculas_sistema,
        peliculas_api=peliculas_externas,
        errores=errores,
        errores_externos=errores_externos,
        titulo=titulo,
        titulo_externo=titulo_externo,
        formulario=formulario or {},
        errores_formulario=errores_formulario or [],
    )


@admin_bp.post("/peliculas/crear")
def crear_pelicula():
    credencial_acceso = session.get("credencial_acceso")
    if not credencial_acceso:
        return redirect(url_for("auth.login"))

    formulario = request.form.to_dict()
    datos, errores_formulario = preparar_datos_pelicula(formulario)

    if errores_formulario:
        return renderizar_peliculas(formulario, errores_formulario), 400

    try:
        respuesta = api_post(
            "/admin/peliculas",
            headers={"Authorization": f"Bearer {credencial_acceso}"},
            json=datos,
        )
    except requests.RequestException:
        errores_formulario = [
            "No se pudo confirmar la creación. Revisá el listado antes de volver a intentar."
        ]
        return renderizar_peliculas(formulario, errores_formulario), 502

    if respuesta.status_code == 201:
        return redirect(
            url_for(
                "admin.peliculas",
                titulo=request.args.get("titulo", ""),
                titulo_externo=request.args.get("titulo_externo", ""),
            ),
            code=303,
        )

    errores_formulario = obtener_errores_api(respuesta)
    return renderizar_peliculas(formulario, errores_formulario), respuesta.status_code


@admin_bp.post("/peliculas/<int:pelicula_id>/modificar")
def modificar_pelicula(pelicula_id):
    credencial_acceso = session.get("credencial_acceso")
    if not credencial_acceso:
        return redirect(url_for("auth.login"))

    formulario = request.form.to_dict()
    formulario["pelicula_id"] = str(pelicula_id)
    formulario.pop("id_externo", None)
    datos, errores_formulario = preparar_datos_pelicula(formulario)

    if errores_formulario:
        return renderizar_peliculas(formulario, errores_formulario), 400

    try:
        respuesta = api_patch(
            f"/admin/peliculas/{pelicula_id}",
            headers={"Authorization": f"Bearer {credencial_acceso}"},
            json=datos,
        )
    except requests.RequestException:
        errores_formulario = [
            "No se pudo confirmar la modificación. Revisá el listado antes de volver a intentar."
        ]
        return renderizar_peliculas(formulario, errores_formulario), 502

    if respuesta.status_code == 200:
        return redirect(
            url_for(
                "admin.peliculas",
                titulo=request.args.get("titulo", ""),
                titulo_externo=request.args.get("titulo_externo", ""),
            ),
            code=303,
        )

    errores_formulario = obtener_errores_api(respuesta)
    return renderizar_peliculas(formulario, errores_formulario), respuesta.status_code


@admin_bp.post("/peliculas/<int:pelicula_id>/desactivar")
def desactivar_pelicula(pelicula_id):
    credencial_acceso = session.get("credencial_acceso")
    if not credencial_acceso:
        return redirect(url_for("auth.login"))

    try:
        respuesta = api_patch(
            f"/admin/peliculas/{pelicula_id}",
            headers={"Authorization": f"Bearer {credencial_acceso}"},
            json={"activa": False},
        )
    except requests.RequestException:
        flash(
            "No se pudo confirmar la desactivación. Revisá el listado antes de volver a intentar.",
            "error",
        )
    else:
        if respuesta.status_code == 200:
            flash("Película desactivada correctamente.", "exito")
        else:
            for error in obtener_errores_api(respuesta):
                flash(error, "error")

    return redirect(
        url_for(
            "admin.peliculas",
            titulo=request.args.get("titulo", ""),
            titulo_externo=request.args.get("titulo_externo", ""),
        ),
        code=303,
    )


@admin_bp.get("/funciones")
def funciones():
    return render_template("administrador/funciones.html")


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

