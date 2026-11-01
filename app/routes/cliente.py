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
    return render_template(
        "cliente/detalle_pelicula.html", pelicula_id=pelicula_id
    )


@cliente_bp.get("/funciones/<int:funcion_id>/butacas")
def seleccionar_butacas(funcion_id):
    return render_template(
        "cliente/seleccionar_butacas.html", funcion_id=funcion_id
    )


@cliente_bp.get("/compras/servicios")
def seleccionar_servicios():
    return render_template("cliente/seleccionar_servicios.html")


@cliente_bp.get("/compras/resumen")
def resumen_compra():
    return render_template("cliente/resumen_compra.html")


@cliente_bp.get("/mis-compras")
def mis_compras():
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
