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
    return render_template("cliente/mis_compras.html")


@cliente_bp.get("/mis-entradas")
def mis_entradas():
    return render_template("cliente/mis_entradas.html")


@cliente_bp.get("/entradas/<int:entrada_id>")
def detalle_entrada(entrada_id):
    return render_template(
        "cliente/detalle_entrada.html", entrada_id=entrada_id
    )

