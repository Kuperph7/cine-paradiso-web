from flask import Blueprint, render_template


cliente_bp = Blueprint("cliente", __name__) 


@cliente_bp.get("/")
def cartelera():
    # Películas temporales utilizadas únicamente para visualizar el mockup.
    # Más adelante estos datos serán reemplazados por la respuesta de la API.
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
    # Esta pantalla recibe el ID de la función elegida en el detalle de la
    # película. En la integración, Flask consultará mediante api_client
    # GET /cartelera/funciones/{funcion_id}/butacas para obtener la sala y
    # distinguir las butacas disponibles de las ocupadas.
    return render_template(
        "cliente/seleccionar_butacas.html", funcion_id=funcion_id
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

    return render_template(
        "cliente/seleccionar_servicios.html",
        categorias=categorias,
        productos=productos,
    )


@cliente_bp.get("/compras/resumen")
def resumen_compra():
    # Compra temporal utilizada únicamente para desarrollar el template.
    # En la integración, la selección llegará desde los pasos anteriores:
    # detalle de película -> función -> butacas -> productos de Candy.
    # Flask deberá conservar estos datos en la sesión o recuperarlos del
    # backend antes de renderizar este resumen.
    compra = {
        "pelicula": "Horizonte final",
        "clasificacion": "+13",
        "estilo": "poster-space",
        "funcion": {
            "id": 101,
            "fecha": "Sábado 14 de noviembre",
            "hora": "18:30",
            "sucursal": "Cine Paradiso Centro",
            "sala": "Sala 3",
            "formato": "2D",
            "idioma": "Castellano",
        },
        "butacas": [
            {"id": 12, "codigo": "F6", "precio": 6500},
            {"id": 13, "codigo": "F7", "precio": 6500},
        ],
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
    return render_template("cliente/mis_compras.html")


@cliente_bp.get("/mis-entradas")
def mis_entradas():
    return render_template("cliente/mis_entradas.html")


@cliente_bp.get("/entradas/<int:entrada_id>")
def detalle_entrada(entrada_id):
    return render_template(
        "cliente/detalle_entrada.html", entrada_id=entrada_id
    )

