from flask import Blueprint, render_template


cliente_bp = Blueprint("cliente", __name__)


@cliente_bp.get("/")
def cartelera():
    return render_template("cliente/cartelera.html")


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

