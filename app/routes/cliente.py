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
        errores = respuesta.json().get("errors", [])
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
        "sucursal",
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
    # Películas temporales utilizadas únicamente para visualizar el mockup.
    # Más adelante estos datos serán reemplazados por la respuesta de la API.
    # Flask deberá leer los filtros enviados por query params y consultar
    # GET /cartelera mediante api_client antes de renderizar el template.
    peliculas = [
        {"id": 1, "titulo": "Horizonte final", "genero": "Ciencia ficción", "duracion": "2 h 08 min", "clasificacion": "+13", "formatos": ["2D", "Subt."], "sucursales": ["Centro", "Norte"], "fechas": ["Hoy", "Fin de semana"], "estilo": "poster-space"},
        {"id": 2, "titulo": "La última función", "genero": "Drama", "duracion": "1 h 52 min", "clasificacion": "ATP", "formatos": ["2D"], "sucursales": ["Centro", "Puerto"], "fechas": ["Hoy", "Mañana"], "estilo": "poster-stage"},
        {"id": 3, "titulo": "Código nocturno", "genero": "Suspenso", "duracion": "1 h 46 min", "clasificacion": "+16", "formatos": ["3D", "Subt."], "sucursales": ["Puerto", "Norte"], "fechas": ["Mañana", "Fin de semana"], "estilo": "poster-night"},
        {"id": 4, "titulo": "Un verano contigo", "genero": "Romance", "duracion": "1 h 39 min", "clasificacion": "ATP", "formatos": ["2D"], "sucursales": ["Centro"], "fechas": ["Hoy"], "estilo": "poster-summer"},
        {"id": 5, "titulo": "Planeta salvaje", "genero": "Aventura", "duracion": "2 h 14 min", "clasificacion": "+13", "formatos": ["3D"], "sucursales": ["Puerto", "Norte"], "fechas": ["Hoy", "Fin de semana"], "estilo": "poster-jungle"},
        {"id": 6, "titulo": "Risas en familia", "genero": "Comedia", "duracion": "1 h 31 min", "clasificacion": "ATP", "formatos": ["2D", "Subt."], "sucursales": ["Centro", "Norte"], "fechas": ["Mañana"], "estilo": "poster-comedy"},
        {"id": 7, "titulo": "El guardián del tiempo", "genero": "Fantasía", "duracion": "2 h 02 min", "clasificacion": "+13", "formatos": ["3D"], "sucursales": ["Centro", "Puerto"], "fechas": ["Fin de semana"], "estilo": "poster-time"},
        {"id": 8, "titulo": "Velocidad límite", "genero": "Acción", "duracion": "1 h 58 min", "clasificacion": "+16", "formatos": ["2D", "Subt."], "sucursales": ["Norte"], "fechas": ["Hoy", "Mañana"], "estilo": "poster-speed"},
    ]

    return render_template(
        "cliente/cartelera.html",
        peliculas=peliculas,
        estrenos=peliculas[2:6],
        generos=sorted({pelicula["genero"] for pelicula in peliculas}),
    )


@cliente_bp.get("/peliculas/<int:pelicula_id>")
def detalle_pelicula(pelicula_id):
    # Datos temporales utilizados para maquetar el detalle de cada película.
    # En la integración, esta información llegará desde la API backend mediante
    # api_client, usando el identificador recibido en la URL.
    peliculas_temporales = {
        1: {
            "id": 1,
            "titulo": "Horizonte final",
            "genero": "Ciencia ficción",
            "duracion": "2 h 08 min",
            "clasificacion": "+13",
            "formatos": ["2D", "Subtitulada"],
            "estreno": "14 de noviembre de 2026",
            "estilo": "poster-space",
            "sinopsis": (
                "Una tripulación emprende el último viaje hacia una estación "
                "perdida. Al cruzar el límite conocido, deberá decidir cuánto "
                "está dispuesta a arriesgar para regresar a casa."
            ),
        },
        2: {
            "id": 2,
            "titulo": "La última función",
            "genero": "Drama",
            "duracion": "1 h 52 min",
            "clasificacion": "ATP",
            "formatos": ["2D"],
            "estreno": "7 de noviembre de 2026",
            "estilo": "poster-stage",
            "sinopsis": (
                "El cierre de un antiguo cine reúne a sus trabajadores y "
                "espectadores para una despedida capaz de cambiar sus historias."
            ),
        },
        3: {
            "id": 3,
            "titulo": "Código nocturno",
            "genero": "Suspenso",
            "duracion": "1 h 46 min",
            "clasificacion": "+16",
            "formatos": ["3D", "Subtitulada"],
            "estreno": "20 de noviembre de 2026",
            "estilo": "poster-night",
            "sinopsis": (
                "Una analista descubre un mensaje oculto que conecta una serie "
                "de desapariciones y la obliga a recorrer la ciudad antes del amanecer."
            ),
        },
        4: {
            "id": 4,
            "titulo": "Un verano contigo",
            "genero": "Romance",
            "duracion": "1 h 39 min",
            "clasificacion": "ATP",
            "formatos": ["2D"],
            "estreno": "12 de noviembre de 2026",
            "estilo": "poster-summer",
            "sinopsis": (
                "Dos amigos vuelven al pueblo donde crecieron y descubren que "
                "algunas promesas pueden esperar, pero no para siempre."
            ),
        },
        5: {
            "id": 5,
            "titulo": "Planeta salvaje",
            "genero": "Aventura",
            "duracion": "2 h 14 min",
            "clasificacion": "+13",
            "formatos": ["3D"],
            "estreno": "28 de noviembre de 2026",
            "estilo": "poster-jungle",
            "sinopsis": (
                "Una expedición científica queda aislada en un mundo desconocido "
                "donde cada forma de vida protege un secreto extraordinario."
            ),
        },
        6: {
            "id": 6,
            "titulo": "Risas en familia",
            "genero": "Comedia",
            "duracion": "1 h 31 min",
            "clasificacion": "ATP",
            "formatos": ["2D", "Subtitulada"],
            "estreno": "5 de noviembre de 2026",
            "estilo": "poster-comedy",
            "sinopsis": (
                "Un festejo familiar perfectamente organizado se convierte en "
                "una sucesión de enredos que nadie olvidará."
            ),
        },
        7: {
            "id": 7,
            "titulo": "El guardián del tiempo",
            "genero": "Fantasía",
            "duracion": "2 h 02 min",
            "clasificacion": "+13",
            "formatos": ["3D"],
            "estreno": "26 de noviembre de 2026",
            "estilo": "poster-time",
            "sinopsis": (
                "Un aprendiz recibe la misión de custodiar el reloj que mantiene "
                "en equilibrio el pasado y el futuro."
            ),
        },
        8: {
            "id": 8,
            "titulo": "Velocidad límite",
            "genero": "Acción",
            "duracion": "1 h 58 min",
            "clasificacion": "+16",
            "formatos": ["2D", "Subtitulada"],
            "estreno": "19 de noviembre de 2026",
            "estilo": "poster-speed",
            "sinopsis": (
                "Una piloto retirada vuelve a competir para descubrir quién está "
                "detrás de una peligrosa red de carreras clandestinas."
            ),
        },
    }

    pelicula = peliculas_temporales.get(
        pelicula_id, peliculas_temporales[1]
    )

    # Funciones temporales para visualizar la selección de disponibilidad.
    # Luego serán reemplazadas por las funciones disponibles devueltas por la API.
    funciones_por_sucursal = [
        {
            "nombre": "Cine Paradiso Centro",
            "direccion": "Av. Corrientes 1234, CABA",
            "funciones": [
                {
                    "id": 101,
                    "fecha": "Hoy",
                    "hora": "18:30",
                    "formato": "2D",
                    "idioma": "Castellano",
                },
                {
                    "id": 102,
                    "fecha": "Hoy",
                    "hora": "21:15",
                    "formato": "3D",
                    "idioma": "Subtitulada",
                },
            ],
        },
        {
            "nombre": "Cine Paradiso Norte",
            "direccion": "Av. Cabildo 2345, CABA",
            "funciones": [
                {
                    "id": 103,
                    "fecha": "Mañana",
                    "hora": "17:45",
                    "formato": "2D",
                    "idioma": "Castellano",
                },
                {
                    "id": 104,
                    "fecha": "Mañana",
                    "hora": "20:30",
                    "formato": "2D",
                    "idioma": "Subtitulada",
                },
            ],
        },
    ]

    return render_template(
        "cliente/detalle_pelicula.html",
        pelicula=pelicula,
        funciones_por_sucursal=funciones_por_sucursal,
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
    # Contenido temporal utilizado únicamente para desarrollar el template.
    # En el hito de integración, los productos llegarán desde la API backend.
    # El contrato actual solo expone la gestión administrativa de servicios;
    # antes de integrar esta vista, el equipo deberá confirmar de qué endpoint
    # cliente se obtendrán los productos sin inventar una ruta nueva.
    categorias = [
        "Combos",
        "Pochoclos",
        "Bebidas",
        "Snacks",
        "Golosinas",
        "Café y helados",
    ]
    productos = [
        {
            "nombre": "Combo Paradiso",
            "descripcion": "Pochoclos grandes y dos gaseosas medianas",
            "precio": 14800,
            "categoria": "Combos",
            "marca": "CP",
            "estilo": "candy-combo",
        },
        {
            "nombre": "Combo Dúo",
            "descripcion": "Pochoclos medianos y dos gaseosas chicas",
            "precio": 11200,
            "categoria": "Combos",
            "marca": "2×",
            "estilo": "candy-duo",
        },
        {
            "nombre": "Pochoclos clásicos",
            "descripcion": "Pochoclos acaramelados tamaño grande",
            "precio": 6800,
            "categoria": "Pochoclos",
            "marca": "POP",
            "estilo": "candy-popcorn",
        },
        {
            "nombre": "Gaseosa mediana",
            "descripcion": "Vaso de 500 ml, sabor a elección",
            "precio": 4200,
            "categoria": "Bebidas",
            "marca": "500",
            "estilo": "candy-drink",
        },
        {
            "nombre": "Nachos con cheddar",
            "descripcion": "Nachos crocantes con salsa de cheddar",
            "precio": 5900,
            "categoria": "Snacks",
            "marca": "N",
            "estilo": "candy-nachos",
        },
        {
            "nombre": "Chocolate",
            "descripcion": "Chocolate con leche de 100 gramos",
            "precio": 3500,
            "categoria": "Golosinas",
            "marca": "CH",
            "estilo": "candy-chocolate",
        },
        {
            "nombre": "Café con leche",
            "descripcion": "Café suave con leche espumada",
            "precio": 3900,
            "categoria": "Café y helados",
            "marca": "CAFÉ",
            "estilo": "candy-coffee",
        },
        {
            "nombre": "Helado individual",
            "descripcion": "Pote individual, sabor a elección",
            "precio": 4700,
            "categoria": "Café y helados",
            "marca": "ICE",
            "estilo": "candy-icecream",
        },
    ]

    funcion_id = request.args.get("funcion_id", type=int)
    butaca_ids = request.args.getlist("butaca_ids", type=int)
    resumen_url = url_for(
        "cliente.resumen_compra",
        funcion_id=funcion_id,
        butaca_ids=butaca_ids,
    )

    return render_template(
        "cliente/seleccionar_servicios.html",
        categorias=categorias,
        productos=productos,
        resumen_url=resumen_url,
    )


@cliente_bp.get("/compras/resumen")
def resumen_compra():
    # Los identificadores llegan desde el formulario de butacas, pero Flask los
    # vuelve a contrastar con la disponibilidad actual informada por la API.
    funcion_id = request.args.get("funcion_id", type=int)
    butaca_ids = request.args.getlist("butaca_ids", type=int)

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
    compra = {
        "pelicula": funcion["pelicula"],
        "clasificacion": funcion["clasificacion"],
        "poster_url": funcion["poster_url"],
        "funcion": funcion,
        "butacas": butacas_seleccionadas,
        # Candy todavía no forma parte de este flujo mínimo de prueba.
        "servicios": [],
    }

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
    )


@cliente_bp.post("/compras/confirmar")
def confirmar_compra():
    """Envía la compra a la API usando el JWT guardado por Flask."""
    funcion_id = request.form.get("funcion_id", type=int)
    butaca_ids = request.form.getlist("butaca_ids", type=int)
    resumen_url = url_for(
        "cliente.resumen_compra",
        funcion_id=funcion_id,
        butaca_ids=butaca_ids,
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
                "servicios": [],
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
