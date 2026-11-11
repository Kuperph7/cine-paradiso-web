from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from flask import Blueprint, redirect, render_template, session, url_for, request, flash
from requests.exceptions import RequestException

from app.services.api_client import api_delete, api_get, api_patch, api_post

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(funcion):
    @wraps(funcion)
    def funcion_protegida(*args, **kwargs):
        if not session.get("token"):
            return redirect(url_for("auth.login"))
        
        usuario = session.get("usuario", {})
        
        if usuario.get("rol") != "administrador":
            return redirect(url_for("cliente.cartelera"))
        
        return funcion(*args, **kwargs)
    return funcion_protegida

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
@admin_required
def peliculas():
    return renderizar_peliculas()


def renderizar_peliculas(formulario=None, errores_formulario=None):
    credencial_acceso = session.get("access_token")
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
    credencial_acceso = session.get("access_token")
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
    credencial_acceso = session.get("access_token")
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
    credencial_acceso = session.get("access_token")
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


@admin_bp.route("/funciones", methods=["GET", "POST"])
def funciones():
    funciones = []
    peliculas = []
    salas = []
    mensaje_error = None
    mensaje_salas = None
    mensaje_accion = None

    token = session.get("token")

    if request.method == "POST" and not request.form.get("accion"):
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


    if request.method == "POST" and request.form.get("accion"):
        accion = request.form.get("accion")

        if not token:
            mensaje_accion = "Tenés que iniciar sesión como administrador."

        elif accion not in ("cancelar", "publicar", "editar"):
            mensaje_accion = "Acción no válida."

        else:
            try:
                funcion_id = int(request.form.get("funcion_id", ""))

                if funcion_id <= 0:
                    raise ValueError("ID inválido")


                if accion == "editar":
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

                    datos_actualizacion = {
                        "pelicula_id": pelicula_id,
                        "sala_id": sala_id,
                        "fecha_hora": fecha_hora.isoformat(timespec="seconds"),
                        "precio": precio
                    }

                else:
                    if accion == "cancelar":
                        nuevo_estado = "cancelada"
                    else:
                        nuevo_estado = "programada"

                    datos_actualizacion = {"estado": nuevo_estado}

                respuesta_actualizacion = api_patch(
                    f"/funciones/{funcion_id}",
                    json=datos_actualizacion,
                    headers={"Authorization": f"Bearer {token}"}
                )

                if respuesta_actualizacion.status_code == 200:
                    mensaje_accion = "Función actualizada correctamente."

                elif respuesta_actualizacion.status_code in (401, 403):
                    mensaje_accion = "No tenés permisos para modificar funciones."

                else:
                    mensaje_accion = "No se pudo actualizar la función."

            except ValueError:
                mensaje_accion = "El identificador de la función no es válido."

            except RequestException:
                mensaje_accion = "No fue posible conectar con la API."


    try:
        respuesta = api_get(
            "/funciones",
            headers={"Authorization": f"Bearer {token}"} if token else {}
        )

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


@admin_bp.route("/salas", methods=["GET", "POST"])
def salas():

    if request.method == "POST":
            datos = {
                "local_id": request.form.get("local", type=int),
                "nombre": request.form.get("nombre", "").strip(),
                "filas": request.form.get("filas", type=int),
                "butacas_por_fila": request.form.get("butacas_por_fila", type=int),
            }
            try:
                respuesta = api_post(
                    "/salas",
                    json=datos,
                )
                respuesta.raise_for_status()
                
            except requests.RequestException:
                print(datos)
        

    salas = []
    try:
        respuesta = api_get("/salas")
        
        salas = respuesta.json()["salas"]
        error_salas = False
    except requests.RequestException:
        error_salas = True
    return render_template("administrador/salas.html", salas = salas, error_salas = error_salas)


@admin_bp.route("/servicios", methods=["GET", "POST"])
def servicios():
    error_servicios = False

    if request.method == "POST":
        accion = request.form.get("accion", "crear")
        
        try:
            
            #Cambio de estado
            if accion == "cambiar_estado":
                servicio_id = int(request.form.get("servicio_id"))
                activo = request.form.get("activo") == "1"

                respuesta = api_patch(
                    f"/servicios/{servicio_id}",
                    json={"activo": activo},
                )

            #Edicion del servicio
            elif accion == "editar":
                servicio_id = int(request.form.get("servicio_id"))

                datos = {
                    "nombre": request.form.get("nombre", "").strip(),
                    "descripcion": request.form.get("descripcion", "").strip(),
                    "precio": request.form.get("precio", type=float),
                }

                respuesta = api_patch(
                    f"/servicios/{servicio_id}",
                    json=datos,
                )

            #Eliminacion del servicio
            elif accion == "borrar":
                servicio_id = int(request.form.get("servicio_id"))

                respuesta = api_delete(
                    f"/servicios/{servicio_id}",
                )
                respuesta.raise_for_status()
                return redirect(url_for("admin.servicios"))
            
            #Creacion del servicio
            elif accion == "crear":
                datos = {
                    "nombre": request.form.get("nombre", "").strip(),
                    "descripcion": request.form.get("descripcion", "").strip(),
                    "precio": request.form.get("precio", type=float),
                }

                respuesta = api_post(
                    "/servicios",
                    json=datos,
                    )

            respuesta.raise_for_status()
            return redirect(url_for("admin.servicios"))

        except (requests.RequestException, TypeError, ValueError):
            error_servicios = True


    # Renderizado de los servicios
    servicios = []

    try:
        respuesta = api_get("/servicios")
        respuesta.raise_for_status()

        datos_respuesta = respuesta.json()

        if isinstance(datos_respuesta, dict):
            servicios = datos_respuesta.get("servicios", [])
        else:
            servicios = datos_respuesta

    except (requests.RequestException, ValueError):
        error_servicios = True

    return render_template(
        "administrador/servicios.html",
        servicios=servicios,
        error_servicios=error_servicios,
    )


@admin_bp.get("/estadisticas")
@admin_required
def estadisticas():
    return render_template("administrador/estadisticas.html")


@admin_bp.get("/entradas/validar")
@admin_required
def validar_entrada():
    return render_template("administrador/validar_entrada.html")

