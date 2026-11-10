import requests
from flask import Blueprint, redirect, render_template, session, url_for, request

from app.services.api_client import api_get


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


@admin_bp.get("/peliculas")
def peliculas():
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

