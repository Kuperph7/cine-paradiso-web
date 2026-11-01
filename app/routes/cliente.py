from flask import Blueprint, render_template, request, url_for


cliente_bp = Blueprint("cliente", __name__)

def obtener_filtros():
    return {
        "idioma": request.args.get("idioma", ""),
        "formato": request.args.get("formato", ""),
        "categoria": request.args.get("categoria", ""),
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