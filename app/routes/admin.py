from flask import Blueprint, render_template, request
import requests

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

Backend_url = "http://127.0.0.1:5000"

@admin_bp.get("/peliculas")
def peliculas():
    return render_template("administrador/peliculas.html")


@admin_bp.get("/funciones")
def funciones():
    return render_template("administrador/funciones.html")


@admin_bp.route("/salas", methods=["GET", "POST"])
def salas():

    if request.method == "POST":
            datos = {
                "local_id": request.form.get("local", type=int),
                "nombre": request.form.get("nombre", "").strip(),
                "filas": request.form.get("filas", type=int),
                "butacas_por_fila": request.form.get("butacas_por_fila", type=int),
            }
            try:
                respuesta = requests.post(
                    f"{Backend_url}/salas",
                    json=datos,
                    timeout=5,
                )
                respuesta.raise_for_status()
                print("Sala creada correctamente")
            except requests.RequestException:
                print(datos)
        

    salas = []
    try:
        respuesta = requests.get(f"{Backend_url}/salas", timeout=5)
        
        salas = respuesta.json()["salas"]
        error_salas = False
    except requests.RequestException:
        error_salas = True
    return render_template("administrador/salas.html", salas = salas, error_salas = error_salas)


@admin_bp.get("/servicios")
def servicios():
    return render_template("administrador/servicios.html")


@admin_bp.get("/estadisticas")
def estadisticas():
    return render_template("administrador/estadisticas.html")


@admin_bp.get("/entradas/validar")
def validar_entrada():
    return render_template("administrador/validar_entrada.html")

