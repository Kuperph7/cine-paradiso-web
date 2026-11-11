import requests
from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.services.api_client import api_post


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    destino = request.values.get("next", "")

    if request.method == "POST":
        try:
            respuesta = api_post(
                "/auth/login",
                json={
                    "email": request.form.get("email", ""),
                    "password": request.form.get("password", ""),
                },
            )
            if respuesta.status_code == 200:
                datos = respuesta.json()
                session["access_token"] = datos["token"]
                session["usuario"] = datos["usuario"]

                if destino.startswith("/") and not destino.startswith("//"):
                    return redirect(destino)
                return redirect(url_for("cliente.cartelera"))

            if respuesta.status_code == 401:
                error = "El email o la contraseña son incorrectos."
            else:
                error = "No fue posible iniciar sesión. Intentá nuevamente."
        except (requests.exceptions.RequestException, KeyError, ValueError):
            error = "No se pudo conectar con el servidor de autenticación."

    return render_template("auth/login.html", error=error, next=destino)


@auth_bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("cliente.cartelera"))


@auth_bp.get("/registro")
def registro():
    return render_template("auth/registro.html")


@auth_bp.get("/perfil")
def perfil():
    return render_template("auth/perfil.html")

@auth_bp.get("/perfil/configuracion")
def configuracion_perfil():
    return render_template("auth/configuracion_perfil.html")
