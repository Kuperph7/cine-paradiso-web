from datetime import date, datetime, time, timedelta
from functools import wraps
from zoneinfo import ZoneInfo

import requests
from flask import Blueprint, redirect, render_template, session, url_for, request, flash
from requests.exceptions import RequestException

from app.services.api_client import api_delete, api_get, api_patch, api_post

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(funcion):
    @wraps(funcion)
    def funcion_protegida(*args, **kwargs):
        if not session.get("access_token"):
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


def cargar_categorias_pelicula():
    try:
        respuesta = api_get("/categorias")
        if respuesta.status_code != 200:
            return [], obtener_errores_api(respuesta)

        datos = respuesta.json()
        categorias = datos.get("categorias") if isinstance(datos, dict) else None

        if not isinstance(categorias, list):
            return [], ["La API devolvió un listado de categorías inválido."]

        for categoria in categorias:
            if (
                not isinstance(categoria, dict)
                or type(categoria.get("id")) is not int
                or categoria["id"] <= 0
                or not isinstance(categoria.get("nombre"), str)
            ):
                return [], ["La API devolvió una categoría inválida."]

        return categorias, []
    except requests.RequestException:
        return [], ["No se pudieron cargar las categorías. Intentá nuevamente."]
    except ValueError:
        return [], ["La API devolvió una respuesta de categorías inválida."]


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

    if formulario.get("categorias_cargadas") == "1":
        datos["categoria_ids"] = []
        for valor in formulario.get("categoria_ids", []):
            if not valor.isdecimal() or int(valor) <= 0:
                errores.append("Las categorías seleccionadas no son válidas.")
                break
            categoria_id = int(valor)
            if categoria_id not in datos["categoria_ids"]:
                datos["categoria_ids"].append(categoria_id)
    return datos, errores


@admin_bp.get("/peliculas")
@admin_required
def peliculas():
    return renderizar_peliculas()


def renderizar_peliculas(formulario=None, errores_formulario=None, abrir_formulario=False):
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

    categorias, errores_categorias = cargar_categorias_pelicula()

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
        categorias=categorias,
        errores_categorias=errores_categorias,
        abrir_formulario=abrir_formulario,
    )


@admin_bp.get("/peliculas/externas/<int:id_externo>")
@admin_required
def seleccionar_pelicula_externa(id_externo):
    credencial_acceso = session["access_token"]
    formulario = {"id_externo": str(id_externo)}
    errores = []
    estado = 200

    try:
        respuesta = api_get(
            f"/admin/peliculas/externas/{id_externo}",
            headers={"Authorization": f"Bearer {credencial_acceso}"},
        )

        if respuesta.status_code == 200:
            datos = respuesta.json()
            pelicula = datos.get("pelicula") if isinstance(datos, dict) else None

            if isinstance(pelicula, dict):
                for campo in (
                    "titulo", "sinopsis", "poster_url",
                    "duracion_minutos", "clasificacion", "genero",
                ):
                    valor = pelicula.get(campo)
                    formulario[campo] = "" if valor is None else str(valor)

                formulario["categoria_ids"] = [
                    str(categoria_id)
                    for categoria_id in pelicula.get("categoria_ids", [])
                ]
            else:
                errores = ["La API devolvió un detalle de película inválido."]
                estado = 502
        else:
            errores = obtener_errores_api(respuesta)
            estado = respuesta.status_code

    except requests.RequestException:
        errores = ["No se pudo conectar con la API para consultar la película."]
        estado = 502
    except ValueError:
        errores = ["La API devolvió una respuesta inválida."]
        estado = 502

    return renderizar_peliculas(
        formulario=formulario,
        errores_formulario=errores,
        abrir_formulario=True,
    ), estado


@admin_bp.post("/peliculas/crear")
def crear_pelicula():
    credencial_acceso = session.get("access_token")
    if not credencial_acceso:
        return redirect(url_for("auth.login"))

    formulario = request.form.to_dict()
    formulario["categoria_ids"] = request.form.getlist("categoria_ids")
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
    formulario["categoria_ids"] = request.form.getlist("categoria_ids")
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
@admin_required
def funciones():
    funciones = []
    peliculas = []
    salas = []
    mensaje_error = None
    mensaje_salas = None
    mensaje_accion = None

    token = session.get("access_token")

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

                for campo in ("formato", "idioma"):
                    valor = request.form.get(campo, "").strip()
                    if valor:
                        datos_funcion[campo] = valor

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
                    mensaje_accion = " ".join(
                        obtener_errores_api(respuesta_creacion)
                    )

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

                    for campo in ("formato", "idioma"):
                        valor = request.form.get(campo, "").strip()
                        if valor:
                            datos_actualizacion[campo] = valor

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
                    mensaje_accion = " ".join(
                        obtener_errores_api(respuesta_actualizacion)
                    )

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
        respuesta_peliculas = api_get(
            "/admin/peliculas",
            headers={"Authorization": f"Bearer {token}"},
)

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
        mensaje_accion=mensaje_accion,
        formatos_funcion=("2D", "3D", "4D", "Confort"),
        idiomas_funcion=("Castellano", "Subtitulada"),
    )


@admin_bp.route("/salas", methods=["GET", "POST"])
@admin_required
def salas():

    token = session.get("access_token")

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
                    headers={"Authorization": f"Bearer {token}"}
                )
                respuesta.raise_for_status()
                
            except requests.RequestException:
                print(datos)
        

    salas = []
    try:
        respuesta = api_get(
            "/salas",
            headers={"Authorization": f"Bearer {token}"}
            )
        
        salas = respuesta.json()["salas"]
        error_salas = False
    except requests.RequestException:
        error_salas = True
    return render_template("administrador/salas.html", salas = salas, error_salas = error_salas)


@admin_bp.route("/servicios", methods=["GET", "POST"])
@admin_required
def servicios():
    error_servicios = False
    token = session.get("access_token")

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
                    headers={"Authorization": f"Bearer {token}"}
                )

            #Edicion del servicio
            elif accion == "editar":
                servicio_id = int(request.form.get("servicio_id"))

                datos = {
                    "nombre": request.form.get("nombre", "").strip(),
                    "descripcion": request.form.get("descripcion", "").strip(),
                    "precio": request.form.get("precio", type=int),
                }

                respuesta = api_patch(
                    f"/servicios/{servicio_id}",
                    json=datos,
                    headers={"Authorization": f"Bearer {token}"}
                )

            #Eliminacion del servicio
            elif accion == "borrar":
                servicio_id = int(request.form.get("servicio_id"))

                respuesta = api_delete(
                    f"/servicios/{servicio_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                respuesta.raise_for_status()
                return redirect(url_for("admin.servicios"))
            
            #Creacion del servicio
            elif accion == "crear":
                datos = {
                    "nombre": request.form.get("nombre", "").strip(),
                    "descripcion": request.form.get("descripcion", "").strip(),
                    "precio": request.form.get("precio", type=int),
                }

                respuesta = api_post(
                    "/servicios",
                    json=datos,
                    headers={"Authorization": f"Bearer {token}"}
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

ZONA_ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")
POR_PAGINA_ESTADISTICAS = 10
PARAMETROS_ESTADISTICAS = (
    "desde", "hasta", "buscar_genero", "buscar_pelicula", "buscar_funcion",
)
PARAMETROS_PAGINA = ("pagina_peliculas", "pagina_funciones", "pagina_cancelaciones")


def _leer_fecha(texto):
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def _formatear_fecha(texto_iso):
    try:
        return datetime.fromisoformat(texto_iso).strftime("%d/%m %H:%M")
    except (TypeError, ValueError):
        return texto_iso or "-"


def _normalizar_estadisticas(datos):
    if not isinstance(datos, dict):
        raise ValueError("Respuesta inválida")

    resultado = {}
    for clave in (
        "ocupacion_por_funcion", "ocupacion_por_pelicula",
        "ventas_por_genero", "franjas_horarias", "funciones_canceladas",
        "compras_canceladas",
    ):
        valor = datos.get(clave, [])
        if not isinstance(valor, list):
            raise ValueError(f"{clave} inválido")
        resultado[clave] = valor

    for funcion in resultado["ocupacion_por_funcion"] + resultado["funciones_canceladas"]:
        funcion["fecha_texto"] = _formatear_fecha(funcion.get("fecha_hora"))

    for compra in resultado["compras_canceladas"]:
        compra["funcion_fecha_texto"] = _formatear_fecha(compra.get("funcion_fecha_hora"))
        compra["cancelacion_texto"] = _formatear_fecha(compra.get("fecha_cancelacion"))

    resumen = datos.get("resumen")
    resultado["resumen"] = resumen if isinstance(resumen, dict) else {}
    resultado["resumen"].setdefault("compras_canceladas", datos.get("cancelaciones", 0))
    return resultado


def _filtrar(lista, texto, campos):
    texto = texto.strip().lower()
    if not texto:
        return lista

    resultado = []
    for item in lista:
        valores = " ".join(str(item.get(campo) or "") for campo in campos).lower()
        if texto in valores:
            resultado.append(item)
    return resultado


def _paginar(lista, nombre_parametro, parametros):
    total_paginas = max(1, (len(lista) + POR_PAGINA_ESTADISTICAS - 1) // POR_PAGINA_ESTADISTICAS)

    try:
        pagina = int(request.args.get(nombre_parametro, 1))
    except ValueError:
        pagina = 1
    pagina = min(max(pagina, 1), total_paginas)

    # Se conservan los filtros y la página de las otras tablas.
    base = dict(parametros)
    for clave in PARAMETROS_PAGINA:
        if clave != nombre_parametro and request.args.get(clave):
            base[clave] = request.args.get(clave)

    anterior = None
    siguiente = None
    if pagina > 1:
        base[nombre_parametro] = pagina - 1
        anterior = url_for("admin.estadisticas", **base)
    if pagina < total_paginas:
        base[nombre_parametro] = pagina + 1
        siguiente = url_for("admin.estadisticas", **base)

    inicio = (pagina - 1) * POR_PAGINA_ESTADISTICAS
    paginacion = {
        "pagina": pagina,
        "total_paginas": total_paginas,
        "anterior": anterior,
        "siguiente": siguiente,
    }
    return lista[inicio:inicio + POR_PAGINA_ESTADISTICAS], paginacion


@admin_bp.get("/estadisticas")
@admin_required
def estadisticas():

    token = session["access_token"]
    hoy = date.today()
    errores = []

    desde = _leer_fecha(request.args.get("desde", "").strip())
    hasta = _leer_fecha(request.args.get("hasta", "").strip())

    # La API exige desde y hasta juntos: si falta uno, se completa.
    if desde and not hasta:
        hasta = hoy
    if hasta and not desde:
        desde = date(2000, 1, 1)
    if desde and hasta and desde > hasta:
        errores.append("La fecha 'desde' no puede ser posterior a 'hasta'.")
        desde = None
        hasta = None

    datos = {
        "resumen": {},
        "ocupacion_por_funcion": [],
        "ocupacion_por_pelicula": [],
        "ventas_por_genero": [],
        "franjas_horarias": [],
        "funciones_canceladas": [],
        "compras_canceladas": [],
    }

    try:

        if not token:
            return redirect(url_for("auth.login"))

        
        params = {}
        if desde and hasta:
            params["desde"] = datetime.combine(
                desde, time.min, tzinfo=ZONA_ARGENTINA
            ).isoformat()
            params["hasta"] = datetime.combine(
                hasta, time(23, 59, 59), tzinfo=ZONA_ARGENTINA
            ).isoformat()
    
        respuesta = api_get(
            "/admin/estadisticas",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            )

        if respuesta.status_code == 401:
            # Token vencido o inválido: hay que volver a iniciar sesión.
            return redirect(url_for("auth.login"))
        if respuesta.status_code == 200:
            datos.update(_normalizar_estadisticas(respuesta.json()))
        else:
            errores.extend(obtener_errores_api(respuesta))


        respuesta.raise_for_status()

    except requests.RequestException:
        errores.append("No fue posible conectar con la API. Intentá nuevamente.")
    except (ValueError, KeyError, TypeError):
        errores.append("La API devolvió estadísticas con un formato inválido.")

        parametros = {}
    for clave in PARAMETROS_ESTADISTICAS:
        valor = request.args.get(clave, "").strip()
        if valor:
            parametros[clave] = valor
    if desde and hasta:
        parametros["desde"] = desde.isoformat()
        parametros["hasta"] = hasta.isoformat()
    else:
        parametros.pop("desde", None)
        parametros.pop("hasta", None)

    busquedas = {
        "genero": parametros.get("buscar_genero", ""),
        "pelicula": parametros.get("buscar_pelicula", ""),
        "funcion": parametros.get("buscar_funcion", ""),
    }

    generos = _filtrar(datos["ventas_por_genero"], busquedas["genero"], ("genero",))
    peliculas = _filtrar(
        datos["ocupacion_por_pelicula"], busquedas["pelicula"], ("titulo", "genero"),
    )
    funciones = _filtrar(
        datos["ocupacion_por_funcion"], busquedas["funcion"],
        ("funcion_id", "pelicula_titulo", "sala_nombre", "fecha_texto"),
    )

    peliculas_pagina, paginacion_peliculas = _paginar(peliculas, "pagina_peliculas", parametros)
    funciones_pagina, paginacion_funciones = _paginar(funciones, "pagina_funciones", parametros)
    cancelaciones_pagina, paginacion_cancelaciones = _paginar(
        datos["compras_canceladas"], "pagina_cancelaciones", parametros,
    )

    # Atajos de rango de fechas.
    rangos = [
        ("Últimos 7 días", hoy - timedelta(days=6), hoy),
        ("Últimos 30 días", hoy - timedelta(days=29), hoy),
        ("Este mes", hoy.replace(day=1), hoy),
    ]
    atajos = []
    for etiqueta, inicio, fin in rangos:
        atajos.append({
            "etiqueta": etiqueta,
            "url": url_for(
                "admin.estadisticas", desde=inicio.isoformat(), hasta=fin.isoformat()
            ),
            "activo": desde == inicio and hasta == fin,
        })
    atajos.append({
        "etiqueta": "Todo",
        "url": url_for("admin.estadisticas"),
        "activo": desde is None,
    })

    if desde and hasta:
        periodo = f"{desde:%d/%m/%Y} al {hasta:%d/%m/%Y}"
    else:
        periodo = "Todo el historial"
    
    return render_template(
        "administrador/estadisticas.html",
        resumen=datos["resumen"],
        ventas_por_genero=generos,
        ocupacion_por_pelicula=peliculas_pagina,
        ocupacion_por_funcion=funciones_pagina,
        franjas_horarias=datos["franjas_horarias"],
        compras_canceladas=cancelaciones_pagina,
        totales={
            "generos": len(datos["ventas_por_genero"]),
            "peliculas": len(datos["ocupacion_por_pelicula"]),
            "funciones": len(datos["ocupacion_por_funcion"]),
            "cancelaciones": len(datos["compras_canceladas"]),
        },
        encontrados={
            "generos": len(generos),
            "peliculas": len(peliculas),
            "funciones": len(funciones),
        },
        paginacion_peliculas=paginacion_peliculas,
        paginacion_funciones=paginacion_funciones,
        paginacion_cancelaciones=paginacion_cancelaciones,
        busquedas=busquedas,
        parametros=parametros,
        desde=desde.isoformat() if desde else "",
        hasta=hasta.isoformat() if hasta else "",
        periodo=periodo,
        atajos=atajos,
        errores=errores,
        )



@admin_bp.route("/entradas/validar", methods=["GET", "POST"])
@admin_required
def validar_entrada():
    resultado = None
    error = None
    codigo_qr = ""
    funcion_id = ""

    if request.method == "POST":
        codigo_qr = request.form.get("codigo_qr", "").strip()
        funcion_id = request.form.get("funcion_id", "").strip()

        if not codigo_qr or not funcion_id.isdigit() or int(funcion_id) <= 0:
            error = "Ingresá un código QR y un ID de función válido."
        else:
            try:
                respuesta = api_post(
                    "/admin/entradas/validar",
                    json={
                        "codigo_qr": codigo_qr,
                        "funcion_id": int(funcion_id),
                    },
                    headers={
                        "Authorization": f"Bearer {session['access_token']}"
                    },
                )

                if respuesta.status_code == 200:
                    resultado = respuesta.json()
                else:
                    error = " ".join(obtener_errores_api(respuesta))

            except (requests.exceptions.RequestException, ValueError):
                error = "No fue posible validar la entrada con la API."

    return render_template(
        "administrador/validar_entrada.html",
        resultado=resultado,
        error=error,
        codigo_qr=codigo_qr,
        funcion_id=funcion_id,
    )
