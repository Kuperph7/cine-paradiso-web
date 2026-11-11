from flask import Blueprint, render_template , session , redirect , url_for
from functools import wraps


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

@admin_bp.get("/peliculas")
@admin_required
def peliculas():
    return render_template("administrador/peliculas.html")


@admin_bp.get("/funciones")
@admin_required
def funciones():
    return render_template("administrador/funciones.html")


@admin_bp.get("/salas")
@admin_required
def salas():
    return render_template("administrador/salas.html")


@admin_bp.get("/servicios")
@admin_required
def servicios():
    return render_template("administrador/servicios.html")


@admin_bp.get("/estadisticas")
@admin_required
def estadisticas():
    return render_template("administrador/estadisticas.html")


@admin_bp.get("/entradas/validar")
@admin_required
def validar_entrada():
    return render_template("administrador/validar_entrada.html")

