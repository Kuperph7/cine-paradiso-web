import requests

from flask import Blueprint, current_app, render_template, request, url_for

from app.services.api_client import api_get


cliente_bp = Blueprint("cliente", __name__) 


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
    # Esta pantalla recibe el ID de la función elegida en el detalle de la
    # película. En la integración, Flask consultará mediante api_client
    # GET /cartelera/funciones/{funcion_id}/butacas para obtener la sala y
    # distinguir las butacas disponibles de las ocupadas.
    # Datos temporales para completar el template mientras el frontend todavía
    # no está conectado al backend. La forma de cada butaca respeta la respuesta
    # pública definida en Swagger: id, fila, columna y ocupada.
    funcion = {
        "id": funcion_id,
        "pelicula_id": 1,
        "pelicula": "Horizonte final",
        "fecha": "Sábado 14 de noviembre",
        "hora": "18:30",
        "sucursal": "Cine Paradiso Centro",
        "sala": "Sala 3",
        "formato": "2D",
        "idioma": "Castellano",
        "precio": 6500,
    }

    # Estos IDs simulan las butacas que el backend devolverá con ocupada=True.
    # Se usan únicamente para distinguir los estados dentro del mockup.
    butacas_ocupadas = {3, 4, 11, 18, 29, 30, 38, 45}
    butacas = []

    # Construye una sala temporal de seis filas y ocho butacas por fila. Jinja
    # recibe esta estructura y genera un checkbox HTML por cada butaca.
    for numero_fila, fila in enumerate("ABCDEF"):
        butacas.append(
            [
                {
                    "id": numero_fila * 8 + columna,
                    "fila": fila,
                    "columna": columna,
                    "ocupada": numero_fila * 8 + columna in butacas_ocupadas,
                }
                for columna in range(1, 9)
            ]
        )

    total_butacas = sum(len(fila) for fila in butacas)
    butacas_libres = sum(
        not butaca["ocupada"]
        for fila in butacas
        for butaca in fila
    )

    return render_template(
        "cliente/seleccionar_butacas.html",
        funcion=funcion,
        butacas=butacas,
        total_butacas=total_butacas,
        butacas_libres=butacas_libres,
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
    # Compra temporal utilizada únicamente para desarrollar el template.
    # En la integración, la selección llegará desde los pasos anteriores:
    # detalle de película -> función -> butacas -> productos de Candy.
    # Flask deberá conservar estos datos en la sesión o recuperarlos del
    # backend antes de renderizar este resumen.
    # Durante el mockup, el formulario de butacas envía estos valores mediante
    # query params. En la integración deberán conservarse en la sesión de Flask
    # o en el mecanismo acordado, y nunca confiarse sin validar con el backend.
    funcion_id = request.args.get("funcion_id", default=101, type=int)
    butaca_ids = request.args.getlist("butaca_ids", type=int)

    if not butaca_ids:
        butaca_ids = [46, 47]

    butacas_seleccionadas = []

    # Traduce temporalmente cada ID a un código visible (por ejemplo, 1 -> A1).
    # Los datos definitivos de fila y columna deberán provenir de la API.
    for butaca_id in butaca_ids:
        numero_fila = (butaca_id - 1) // 8
        numero_columna = (butaca_id - 1) % 8 + 1
        codigo = f"{chr(65 + numero_fila)}{numero_columna}"
        butacas_seleccionadas.append(
            {"id": butaca_id, "codigo": codigo, "precio": 6500}
        )

    compra = {
        "pelicula": "Horizonte final",
        "clasificacion": "+13",
        "estilo": "poster-space",
        "funcion": {
            "id": funcion_id,
            "fecha": "Sábado 14 de noviembre",
            "hora": "18:30",
            "sucursal": "Cine Paradiso Centro",
            "sala": "Sala 3",
            "formato": "2D",
            "idioma": "Castellano",
        },
        "butacas": butacas_seleccionadas,
        "servicios": [
            {
                "nombre": "Combo Paradiso",
                "cantidad": 1,
                "precio_unitario": 14800,
            },
        ],
    }

    total_entradas = sum(
        butaca["precio"] for butaca in compra["butacas"]
    )
    total_servicios = sum(
        servicio["cantidad"] * servicio["precio_unitario"]
        for servicio in compra["servicios"]
    )

    # Este GET solamente muestra el resumen. Más adelante se agregará una ruta
    # POST del frontend para recibir la confirmación, llamar mediante api_client
    # a POST /compras y procesar la respuesta 201 del backend. Esa respuesta
    # contendrá las entradas y sus QR; luego Flask deberá redirigir al template
    # de confirmación/QR, nunca generar el QR desde este resumen.
    return render_template(
        "cliente/resumen_compra.html",
        compra=compra,
        total_entradas=total_entradas,
        total_servicios=total_servicios,
        total=total_entradas + total_servicios,
    )


@cliente_bp.get("/mis-compras")
def mis_compras():
    # Datos temporales del historial. En la integración, Flask consultará
    # GET /mis-compras mediante api_client y entregará la respuesta al template
    # usando la variable "compras".
    compras_usuario = [
        {
            "id": 10293,
            "pelicula": "Zootopia 3D",
            "fecha": "22/05/2026",
            "monto": "12.500",
            "estado": "Confirmada",
            "cancelable": True
        },
        {
            "id": 10182,
            "pelicula": "Horizonte Final",
            "fecha": "10/04/2026",
            "monto": "8.000",
            "estado": "Finalizada",
            "cancelable": False
        }
    ]
    return render_template("cliente/mis_compras.html")


@cliente_bp.get("/mis-entradas")
def mis_entradas():
    return render_template("cliente/mis_entradas.html")


@cliente_bp.get("/entradas/<int:entrada_id>")
def detalle_entrada(entrada_id):
    # Confirmación temporal posterior a la compra. Luego de POST /compras, el
    # backend devuelve la compra confirmada, sus entradas y los QR. Flask deberá
    # utilizar esa respuesta —o consultar GET /compras/{compra_id}— y recién
    # entonces renderizar esta pantalla; el frontend no debe generar los QR.
    compra_data = {
        "fecha": "22/5/26",
        "detalle_entradas": "Entrada Zootopia 3D Inglés VIP x2",
        "detalle_combos": "Combo palomitas con bebidas x1",
        "monto_total": "12.500",
        "qr_url": "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=CINEPARADISO-COMPRA-10293",
        "cancelable": True,
        "fecha_limite_cancelacion": "20/05/2026"
    }
    return render_template(
        "cliente/detalle_entrada.html", entrada_id=entrada_id, compra=compra_data
    )


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
