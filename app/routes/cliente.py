from collections import defaultdict
from datetime import datetime

import requests
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.services.api_client import api_get, api_patch, api_post

cliente_bp = Blueprint("cliente", __name__) 

def _mensaje_error_api(respuesta, mensaje_predeterminado):
    """Extrae la descripción pública del formato de errores del backend."""
    try:
        cuerpo = respuesta.json()
        detalles = cuerpo.get("detalles", [])
        if detalles:
            return detalles[0].get("mensaje", mensaje_predeterminado)

        # Compatibilidad temporal con respuestas anteriores del backend.
        errores = cuerpo.get("errors", [])
        if errores:
            return errores[0].get("description", mensaje_predeterminado)
    except (AttributeError, TypeError, ValueError):
        pass
    return mensaje_predeterminado


def _cargar_contexto_funcion(funcion_id):
    """Consulta función y película para no repetir datos temporales en vistas."""
    respuesta_funcion = api_get(f"/funciones/{funcion_id}")
    respuesta_funcion.raise_for_status()
    funcion_api = respuesta_funcion.json()

    respuesta_pelicula = api_get(
        f"/peliculas/{funcion_api['pelicula_id']}"
    )
    respuesta_pelicula.raise_for_status()
    pelicula = respuesta_pelicula.json()

    fecha_hora = datetime.fromisoformat(funcion_api["fecha_hora"])
    funcion_publicada = next(
        (
            item
            for item in pelicula.get("funciones_disponibles", [])
            if item["id"] == funcion_id
        ),
        {},
    )

    return {
        "id": funcion_id,
        "pelicula_id": funcion_api["pelicula_id"],
        "pelicula": pelicula["titulo"],
        "clasificacion": pelicula.get("clasificacion", ""),
        "poster_url": pelicula.get("poster_url"),
        "fecha": fecha_hora.strftime("%d/%m/%Y"),
        "hora": fecha_hora.strftime("%H:%M"),
        "sucursal": funcion_publicada.get("local_nombre", "Cine Paradiso"),
        "sala": funcion_publicada.get(
            "sala_nombre", f"Sala {funcion_api['sala_id']}"
        ),
        "precio": int(funcion_api["precio"]),
    }


def _agrupar_butacas_por_fila(butacas):
    """Ordena la respuesta plana de la API para renderizar una fila por vez."""
    filas = defaultdict(list)

    for butaca in butacas:
        estado = butaca["estado"]
        filas[butaca["fila"]].append(
            {
                "id": butaca["id"],
                "fila": butaca["fila"],
                "numero": butaca["numero"],
                "estado": estado,
                "disponible": estado == "disponible",
            }
        )

    return [
        sorted(filas[fila], key=lambda butaca: butaca["numero"])
        for fila in sorted(filas)
    ]


def obtener_filtros():
    # Conserva los filtros elegidos al navegar entre la cartelera y las
    # pantallas de preferencias. Más adelante Flask enviará estos valores al
    # backend mediante api_client; el navegador no consultará la API con fetch.
    nombres_filtros = (
        "local_id",
        "fecha",
        "genero",
        "idioma",
        "formato",
        "categoria",
    )
    return {
        nombre: request.args.get(nombre, "")
        for nombre in nombres_filtros
    }

def obtener_headers():
    token = session.get("access_token", "")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


@cliente_bp.app_context_processor
def contexto_filtros():
    def url_con_filtros(endpoint, **cambios):
        filtros = obtener_filtros()
        filtros.update(cambios)
        parametros = {
            clave: valor
            for clave, valor in filtros.items()
            if valor
        }
        return url_for(endpoint, **parametros)

    return {"url_con_filtros": url_con_filtros}


@cliente_bp.get("/")
def cartelera():
    peliculas = []
    error = None

    local_id = request.args.get("local_id", "").strip()
    fecha = request.args.get("fecha", "").strip()

    locales = [
        {"id": 1, "nombre": "Cine Paradiso Centro"},
        {"id": 2, "nombre": "Cine Paradiso Norte"},
        {"id": 3, "nombre": "Cine Paradiso Puerto"}
    ]
    parametros = {}

    if local_id:
        parametros["local_id"] = local_id

    if fecha:
        parametros["fecha"] = fecha

    try:
        respuesta = api_get("/cartelera", params=parametros)
        respuesta.raise_for_status()

        datos = respuesta.json()
        peliculas = datos.get("peliculas", [])

    except requests.exceptions.RequestException:
        current_app.logger.exception(
            "Error al consultar la cartelera"
        )
        error = "No se pudo cargar la cartelera."

    generos = []

    for pelicula in peliculas:
        for genero in pelicula.get("generos", []):
            if genero not in generos:
                generos.append(genero)

    return render_template(
        "cliente/cartelera.html",
        peliculas=peliculas,
        estrenos=[],
        generos=generos,
        error=error,
        local_id=local_id,
        fecha=fecha,
        locales=locales,
    )


@cliente_bp.get("/peliculas/<int:pelicula_id>")
def detalle_pelicula(pelicula_id):
    pelicula = None
    funciones = []
    error = None

    try:
        respuesta = api_get(f"/cartelera/{pelicula_id}")
        respuesta.raise_for_status()

        pelicula = respuesta.json()
        funciones = pelicula.get("funciones_disponibles", [])

        for funcion in funciones:
            fecha_hora = funcion["fecha_hora"]
            funcion["fecha"] = fecha_hora[0:10]
            funcion["hora"] = fecha_hora[11:16]

    except requests.exceptions.HTTPError as error_api:
        current_app.logger.exception(
            "Error al consultar el detalle de la película"
        )

        if error_api.response.status_code == 404:
            error = "No se encontró la película solicitada."
        else:
            error = "No se pudo cargar el detalle de la película."

    except requests.exceptions.RequestException:
        current_app.logger.exception(
            "Error al conectar con la API"
        )
        error = "No se pudo conectar con el servidor."

    return render_template(
        "cliente/detalle_pelicula.html",
        pelicula=pelicula,
        funciones=funciones,
        error=error,
    )


@cliente_bp.get("/funciones/<int:funcion_id>/butacas")
def seleccionar_butacas(funcion_id):
    # Flask obtiene la función, la película y la disponibilidad desde la API.
    # El navegador solo recibe el HTML ya renderizado; no utiliza fetch.
    funcion = {"id": funcion_id, "pelicula_id": 1}
    butacas = []
    total_butacas = 0
    butacas_libres = 0
    error = None

    try:
        funcion = _cargar_contexto_funcion(funcion_id)
        respuesta = api_get(f"/funciones/{funcion_id}/butacas")

        if respuesta.status_code == 404:
            error = "No se encontró la función seleccionada."
        else:
            respuesta.raise_for_status()
            datos = respuesta.json()
            butacas_api = datos.get("butacas", [])
            butacas = _agrupar_butacas_por_fila(butacas_api)
            total_butacas = datos.get("total_butacas", len(butacas_api))
            butacas_libres = datos.get(
                "butacas_libres",
                sum(
                    butaca["estado"] == "disponible"
                    for butaca in butacas_api
                ),
            )
    except requests.exceptions.HTTPError as error_http:
        if error_http.response is not None and error_http.response.status_code == 404:
            error = "No se encontró la función seleccionada."
        else:
            error = "No se pudo cargar la información de la función."
    except requests.exceptions.RequestException:
        current_app.logger.exception(
            "No fue posible consultar las butacas de la función %s",
            funcion_id,
        )
        error = "No se pudo conectar con el servidor para cargar las butacas."
    except (KeyError, StopIteration, TypeError, ValueError):
        current_app.logger.exception(
            "La API devolvió datos de butacas con un formato inválido"
        )
        error = "No se pudo interpretar la disponibilidad de las butacas."

    return render_template(
        "cliente/seleccionar_butacas.html",
        funcion=funcion,
        butacas=butacas,
        total_butacas=total_butacas,
        butacas_libres=butacas_libres,
        error=error,
    )


@cliente_bp.get("/compras/servicios")
def seleccionar_servicios():
    funcion_id = request.args.get("funcion_id", type=int)
    butaca_ids = request.args.getlist("butaca_ids", type=int)
    servicio_ids = request.args.getlist("servicio_ids", type=int)
    cantidades = {
        servicio_id: max(
            1,
            request.args.get(f"cantidad_{servicio_id}", 1, type=int),
        )
        for servicio_id in servicio_ids
    }
    productos = []
    error = None
    estilos = (
        "candy-combo",
        "candy-duo",
        "candy-popcorn",
        "candy-drink",
        "candy-nachos",
        "candy-chocolate",
        "candy-coffee",
        "candy-icecream",
    )

    # El navegador no consulta el backend. Flask frontend usa requests en
    # api_get(), recibe el JSON y recién entonces renderiza el HTML con Jinja.
    try:
        respuesta = api_get("/servicios")
        respuesta.raise_for_status()
        servicios = respuesta.json().get("servicios", [])
        productos = [
            {
                **servicio,
                "categoria": "Candy",
                "marca": "".join(
                    palabra[0] for palabra in servicio["nombre"].split()
                )[:4].upper(),
                "estilo": estilos[indice % len(estilos)],
            }
            for indice, servicio in enumerate(servicios)
        ]
    except requests.exceptions.RequestException:
        current_app.logger.exception("No fue posible cargar el catálogo de Candy")
        error = "No se pudo conectar con el servidor para cargar Candy."
    except (AttributeError, KeyError, TypeError, ValueError):
        current_app.logger.exception("La API devolvió servicios inválidos")
        error = "No se pudo interpretar el catálogo de Candy."

    resumen_url = url_for(
        "cliente.resumen_compra",
        funcion_id=funcion_id,
        butaca_ids=butaca_ids,
    )

    return render_template(
        "cliente/seleccionar_servicios.html",
        categorias=["Todos los productos"],
        productos=productos,
        resumen_url=resumen_url,
        funcion_id=funcion_id,
        butaca_ids=butaca_ids,
        servicio_ids=servicio_ids,
        cantidades=cantidades,
        error=error,
    )


@cliente_bp.get("/compras/resumen")
def resumen_compra():
    # Los identificadores llegan desde el formulario de butacas, pero Flask los
    # vuelve a contrastar con la disponibilidad actual informada por la API.
    funcion_id = request.args.get("funcion_id", type=int)
    butaca_ids = request.args.getlist("butaca_ids", type=int)
    servicio_ids = request.args.getlist("servicio_ids", type=int)

    if funcion_id is None or not butaca_ids:
        flash("Seleccioná al menos una butaca para continuar.", "error")
        if funcion_id is not None:
            return redirect(
                url_for("cliente.seleccionar_butacas", funcion_id=funcion_id)
            )
        return redirect(url_for("cliente.cartelera"))

    try:
        funcion = _cargar_contexto_funcion(funcion_id)
        respuesta_butacas = api_get(f"/funciones/{funcion_id}/butacas")
        respuesta_butacas.raise_for_status()
        butacas_api = respuesta_butacas.json().get("butacas", [])
        respuesta_servicios = api_get("/servicios")
        respuesta_servicios.raise_for_status()
        servicios_api = respuesta_servicios.json().get("servicios", [])
    except requests.exceptions.RequestException:
        flash("No se pudo validar la selección con el servidor.", "error")
        return redirect(
            url_for("cliente.seleccionar_butacas", funcion_id=funcion_id)
        )
    except (KeyError, TypeError, ValueError):
        flash("La información de la función no tiene el formato esperado.", "error")
        return redirect(
            url_for("cliente.seleccionar_butacas", funcion_id=funcion_id)
        )

    disponibles = {
        int(butaca["id"]): butaca
        for butaca in butacas_api
        if butaca.get("estado") == "disponible"
    }
    if any(butaca_id not in disponibles for butaca_id in butaca_ids):
        flash(
            "Una de las butacas elegidas ya no está disponible.",
            "error",
        )
        return redirect(
            url_for("cliente.seleccionar_butacas", funcion_id=funcion_id)
        )

    butacas_seleccionadas = [
        {
            "id": butaca_id,
            "codigo": (
                f"{disponibles[butaca_id]['fila']}"
                f"{disponibles[butaca_id]['numero']}"
            ),
            "precio": funcion["precio"],
        }
        for butaca_id in butaca_ids
    ]
    servicios_disponibles = {
        int(servicio["id"]): servicio for servicio in servicios_api
    }
    if any(servicio_id not in servicios_disponibles for servicio_id in servicio_ids):
        flash("Uno de los productos elegidos ya no está disponible.", "error")
        return redirect(
            url_for(
                "cliente.seleccionar_servicios",
                funcion_id=funcion_id,
                butaca_ids=butaca_ids,
            )
        )

    servicios_seleccionados = []
    for servicio_id in servicio_ids:
        cantidad = request.args.get(f"cantidad_{servicio_id}", 1, type=int)
        if cantidad is None or cantidad < 1:
            flash("La cantidad de cada producto debe ser mayor a cero.", "error")
            return redirect(
                url_for(
                    "cliente.seleccionar_servicios",
                    funcion_id=funcion_id,
                    butaca_ids=butaca_ids,
                )
            )
        servicio = servicios_disponibles[servicio_id]
        servicios_seleccionados.append(
            {
                "servicio_id": servicio_id,
                "nombre": servicio["nombre"],
                "cantidad": cantidad,
                "precio_unitario": int(servicio["precio"]),
            }
        )

    compra = {
        "pelicula": funcion["pelicula"],
        "clasificacion": funcion["clasificacion"],
        "poster_url": funcion["poster_url"],
        "funcion": funcion,
        "butacas": butacas_seleccionadas,
        "servicios": servicios_seleccionados,
    }

    candy_url = url_for(
        "cliente.seleccionar_servicios",
        funcion_id=funcion_id,
        butaca_ids=butaca_ids,
        servicio_ids=servicio_ids,
        **{
            f"cantidad_{servicio['servicio_id']}": servicio["cantidad"]
            for servicio in servicios_seleccionados
        },
    )

    total_entradas = sum(
        butaca["precio"] for butaca in compra["butacas"]
    )
    total_servicios = sum(
        servicio["cantidad"] * servicio["precio_unitario"]
        for servicio in compra["servicios"]
    )

    return render_template(
        "cliente/resumen_compra.html",
        compra=compra,
        total_entradas=total_entradas,
        total_servicios=total_servicios,
        total=total_entradas + total_servicios,
        candy_url=candy_url,
    )


@cliente_bp.post("/compras/confirmar")
def confirmar_compra():
    """Envía la compra a la API usando el JWT guardado por Flask."""
    funcion_id = request.form.get("funcion_id", type=int)
    butaca_ids = request.form.getlist("butaca_ids", type=int)
    servicio_ids = request.form.getlist("servicio_ids", type=int)
    servicios = [
        {
            "servicio_id": servicio_id,
            "cantidad": request.form.get(
                f"cantidad_{servicio_id}", 1, type=int
            ),
        }
        for servicio_id in servicio_ids
    ]
    resumen_url = url_for(
        "cliente.resumen_compra",
        funcion_id=funcion_id,
        butaca_ids=butaca_ids,
        servicio_ids=servicio_ids,
        **{
            f"cantidad_{servicio['servicio_id']}": servicio["cantidad"]
            for servicio in servicios
        },
    )

    token = session.get("access_token")
    if not token:
        return redirect(url_for("auth.login", next=resumen_url))

    try:
        respuesta = api_post(
            "/compras",
            json={
                "funcion_id": funcion_id,
                "butaca_ids": butaca_ids,
                "servicios": servicios,
                "medio_pago": request.form.get("medio_pago", "tarjeta"),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    except requests.exceptions.RequestException:
        flash("No se pudo conectar con el servidor para confirmar la compra.", "error")
        return redirect(resumen_url)

    if respuesta.status_code == 201:
        compra = respuesta.json()
        return redirect(
            url_for("cliente.confirmacion_compra", compra_id=compra["id"])
        )

    if respuesta.status_code == 401:
        session.clear()
        flash("Tu sesión venció. Iniciá sesión nuevamente.", "error")
        return redirect(url_for("auth.login", next=resumen_url))

    flash(
        _mensaje_error_api(
            respuesta,
            "No fue posible confirmar la compra.",
        ),
        "error",
    )
    return redirect(resumen_url)


@cliente_bp.get("/compras/<int:compra_id>/confirmacion")
def confirmacion_compra(compra_id):
    """Recupera del backend la compra persistida y muestra sus entradas."""
    token = session.get("access_token")
    if not token:
        return redirect(
            url_for("auth.login", next=request.path)
        )

    try:
        respuesta = api_get(
            f"/compras/{compra_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if respuesta.status_code == 401:
            session.clear()
            return redirect(url_for("auth.login", next=request.path))
        respuesta.raise_for_status()
        compra = respuesta.json()
    except requests.exceptions.RequestException:
        flash("No se pudo recuperar la compra confirmada.", "error")
        return redirect(url_for("cliente.cartelera"))

    return render_template(
        "cliente/confirmacion_compra.html",
        compra=compra,
    )


@cliente_bp.get("/mis-compras")
def mis_compras():
    # Flask consulta el historial protegido y adapta la respuesta al template.
    headers = obtener_headers()
    compras_data = []

    if not session.get("access_token"):
        return redirect(url_for("auth.login", next=request.path))

    try:
        response = api_get("/compras", headers=headers)

        if response.status_code == 401:
            session.clear()
            return redirect(url_for("auth.login", next=request.path))

        if response.status_code == 200:
            for compra in response.json().get("compras", []):
                funcion = _cargar_contexto_funcion(compra["funcion_id"])
                fecha = datetime.fromisoformat(compra["fecha_hora"])
                compras_data.append(
                    {
                        "id": compra["id"],
                        "pelicula": funcion["pelicula"],
                        "fecha": fecha.strftime("%d/%m/%Y"),
                        "monto": f"{int(compra['total']):,}".replace(",", "."),
                        "estado": compra["estado"].capitalize(),
                    }
                )
        else:
            flash("No se pudo obtener el historial de compras.", "error")
    except (requests.exceptions.RequestException, KeyError, TypeError, ValueError):
        current_app.logger.exception("No fue posible cargar el historial")
        flash("No se pudo conectar con el servidor de compras.", "error")

    return render_template("cliente/mis_compras.html", compras=compras_data)


@cliente_bp.get("/mis-entradas")
def mis_entradas():
    return render_template("cliente/mis_entradas.html")


@cliente_bp.get("/entradas/<int:entrada_id>")
def detalle_entrada(entrada_id):
    headers = obtener_headers()

    if not session.get("access_token"):
        return redirect(url_for("auth.login", next=request.path))

    try:
        response = api_get(f"/entradas/{entrada_id}", headers=headers)

        if response.status_code == 401:
            session.clear()
            return redirect(url_for("auth.login", next=request.path))

        if response.status_code == 200:
            entrada = response.json()
            return redirect(
                url_for(
                    "cliente.confirmacion_compra",
                    compra_id=entrada["compra_id"],
                )
            )
        flash("No se encontró la entrada solicitada.", "error")
    except (requests.exceptions.RequestException, KeyError, TypeError, ValueError):
        current_app.logger.exception("No fue posible consultar la entrada")
        flash("No se pudo conectar con el servidor de entradas.", "error")

    return redirect(url_for("cliente.mis_compras"))

@cliente_bp.post("/compras/<int:compra_id>/cancelar")
def cancelar_compra(compra_id):
    headers = obtener_headers()

    if not session.get("access_token"):
        return redirect(url_for("auth.login", next=url_for("cliente.mis_compras")))

    payload = {
        "estado": "cancelada",
        "motivo": "Cancelación solicitada por el usuario desde el panel web"
    }

    try:
        response = api_patch(
            f"/compras/{compra_id}",
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            flash(f"La compra #{compra_id} fue cancelada.", "success")
        else:
            flash(
                _mensaje_error_api(response, "No se pudo cancelar la compra."),
                "error",
            )
    except requests.exceptions.RequestException:
        current_app.logger.exception("No fue posible cancelar la compra")
        flash("No se pudo conectar con el servidor de compras.", "error")

    return redirect(url_for("cliente.mis_compras"))


@cliente_bp.get("/sucursales")
def sucursales():
    # Datos temporales utilizados para maquetar la vista de sucursales.
    # El contrato actual no define un endpoint público de sucursales; antes de
    # integrar esta pantalla, el equipo deberá confirmar su origen sin inventar
    # una ruta que no exista en Swagger.
    lista_sucursales = [
        {
            "nombre": "Sede Central",
            "direccion": "Av. Corrientes 1234, CABA",
            "descripcion": "Salas 3D/4D, estacionamiento propio y acceso accesible.",
            "imagen": "sucursal_central.jpg",
            "mapa_url": "https://maps.google.com"
        },
        {
            "nombre": "Sede Belgrano",
            "direccion": "Av. Cabildo 2345, CABA",
            "descripcion": "Sonido Dolby Atmos, candy bar extendido y zona VIP.",
            "imagen": "sucursal_belgrano.jpg",
            "mapa_url": "https://maps.google.com"
        },
        {
            "nombre": "Sede Palermo",
            "direccion": "Av. Santa Fe 3456, CABA",
            "descripcion": "Proyección IMAX, patio gastronómico y estacionamiento.",
            "imagen": "sucursal_palermo.jpg",
            "mapa_url": "https://maps.google.com"
        }
    ]
    return render_template("cliente/sucursales.html", sucursales=lista_sucursales)


@cliente_bp.get("/preguntas-frecuentes")
def preguntas_frecuentes():
    return render_template("cliente/preguntas_frecuentes.html")


@cliente_bp.get("/peliculas-vistas")
def peliculas_vistas():
    return render_template("cliente/peliculas_vistas.html")


@cliente_bp.get("/configuracion/idioma")
def configurar_idioma():
    return render_template("cliente/idioma.html")


@cliente_bp.get("/configuracion/formato")
def configurar_formato():
    return render_template("cliente/formato.html")


@cliente_bp.get("/configuracion/categoria")
def configurar_categoria():
    return render_template("cliente/categoria.html")
