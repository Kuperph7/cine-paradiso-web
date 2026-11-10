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


@admin_bp.route("/servicios", methods=["GET", "POST", "DELETE"])
def servicios():
    error_servicios = False

    if request.method == "POST":
        accion = request.form.get("accion", "crear")
        
        try:
            
            #Cambio de estado
            if accion == "cambiar_estado":
                servicio_id = int(request.form.get("servicio_id"))
                activo = request.form.get("activo") == "1"

                respuesta = requests.patch(
                    f"{Backend_url}/servicios/{servicio_id}",
                    json={"activo": activo},
                    timeout=5,
                )

            #Edicion del servicios
            elif accion == "editar":
                servicio_id = int(request.form.get("servicio_id"))

                datos = {
                    "nombre": request.form.get("nombre", "").strip(),
                    "descripcion": request.form.get("descripcion", "").strip(),
                    "precio": request.form.get("precio", type=float),
                }

                respuesta = requests.patch(
                    f"{Backend_url}/servicios/{servicio_id}",
                    json=datos,
                    timeout=5,
                )

            #Eliminacion del servicio
            elif accion == "borrar":
                servicio_id = int(request.form.get("servicio_id"))

                respuesta = requests.delete(
                    f"{Backend_url}/servicios/{servicio_id}",
                    timeout=5,
                )

            
            #Creacion del servicio
            datos = {
                "nombre": request.form.get("nombre", "").strip(),
                "descripcion": request.form.get("descripcion", "").strip(),
                "precio": request.form.get("precio", type=float),
            }

            respuesta = requests.post(
                f"{Backend_url}/servicios",
                json=datos,
                timeout=5,
                )

            respuesta.raise_for_status()


        except (requests.RequestException, TypeError, ValueError):
            error_servicios = True


    # Renderizado de los servicios
    servicios = []

    try:
        respuesta = requests.get(f"{Backend_url}/servicios", timeout=5)
        respuesta.raise_for_status()

        datos_respuesta = respuesta.json()

        if isinstance(datos_respuesta, dict):
            servicios = datos_respuesta.get("servicios", [])
        else:
            servicios = datos_respuesta

    except (requests.RequestException, ValueError):
        error_servicios = True

    return render_template(
        "administrador/servicios.html",
        servicios=servicios,
        error_servicios=error_servicios,
    )


@admin_bp.get("/estadisticas")
def estadisticas():
    return render_template("administrador/estadisticas.html")


@admin_bp.get("/entradas/validar")
def validar_entrada():
    return render_template("administrador/validar_entrada.html")

