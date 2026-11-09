from flask import Blueprint, render_template
import requests

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

Backend_url = ""

@admin_bp.get("/peliculas")
def peliculas():
    return render_template("administrador/peliculas.html")


@admin_bp.get("/funciones")
def funciones():
    return render_template("administrador/funciones.html")


@admin_bp.get("/salas")
def salas():
    respuesta = requests.get(f"{Backend_url}/salas", timeout=5)
    #No estoy seguro si la url del backend es admin/salas o /salas a secas
    salas = respuesta.json()["salas"]
    return render_template("administrador/salas.html", salas = salas)


@admin_bp.get("/servicios")
def servicios():
    return render_template("administrador/servicios.html")


@admin_bp.get("/estadisticas")
def estadisticas():
    return render_template("administrador/estadisticas.html")


@admin_bp.get("/entradas/validar")
def validar_entrada():
    return render_template("administrador/validar_entrada.html")

