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


def _mensaje_error_api(respuesta):
    """Obtiene el mensaje más útil del contrato uniforme de errores de la API."""
    try:
        datos = respuesta.json()
    except (requests.exceptions.JSONDecodeError, ValueError):
        return None

    if not isinstance(datos, dict):
        return None

    detalles = datos.get("detalles")
    if isinstance(detalles, list):
        for detalle in detalles:
            if not isinstance(detalle, dict):
                continue
            mensaje = detalle.get("mensaje")
            if isinstance(mensaje, str) and mensaje.strip():
                return mensaje.strip()

    mensaje = datos.get("mensaje")
    if isinstance(mensaje, str) and mensaje.strip():
        return mensaje.strip()

    return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    error_titulo = None
    destino = request.values.get("next", "")
    email = request.form.get("email", "") if request.method == "POST" else ""

    if request.method == "POST":
        try:
            respuesta = api_post(
                "/auth/login",
                json={
                    "email": email,
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

            mensaje_api = _mensaje_error_api(respuesta)
            if respuesta.status_code >= 500:
                error_titulo = "El servidor tuvo un problema"
                error = mensaje_api or (
                    "No fue posible procesar el inicio de sesión. "
                    "Intentá nuevamente en unos minutos."
                )
            else:
                error_titulo = "No pudimos iniciar sesión"
                error = mensaje_api or (
                    "Revisá tus datos e intentá nuevamente."
                )
        except requests.exceptions.RequestException:
            error_titulo = "No pudimos conectar"
            error = (
                "El servidor de autenticación no está disponible. "
                "Intentá nuevamente en unos minutos."
            )
        except (KeyError, ValueError):
            error_titulo = "Respuesta inesperada"
            error = (
                "El servidor devolvió una respuesta inválida. "
                "Intentá nuevamente."
            )

    return render_template(
        "auth/login.html",
        error=error,
        error_titulo=error_titulo,
        next=destino,
        email=email,
    )


@auth_bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("cliente.cartelera"))


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        return render_template("auth/registro.html")
    
    datos = {
        "nombre": request.form.get("nombre", ""),
        "email": request.form.get("email", ""),
        "password": request.form.get("password", "")
    }
    
    respuesta = api_post("/auth/register", json=datos)
    
    if respuesta.ok:
        return render_template("auth/login.html", mensaje="Registro exitoso. Por favor, inicia sesión.")
    try:
        error = respuesta.json()
        mensaje = error.get("mensaje", "No se pudo registrar el usuario")
    
    except ValueError:
        mensaje = "No se pudo registrar el usuario"

    return render_template("auth/registro.html", error=mensaje), respuesta.status_code

@auth_bp.get("/perfil")
def perfil():
    token = session.get("token")
    
    if not token:
        return redirect(url_for("cliente.cartelera"))
    
    respuesta= api_get("/auth/perfil", headers={"Authorization": f"Bearer {token}"})
    
    if respuesta.ok:
        usuario = respuesta.json()
        session["usuario"] = usuario
        
        return render_template( "auth/perfil.html",usuario=usuario)
    
    session.clear()
    
    return render_template(
        "auth/perfil_sin_sesion.html",
        error="La sesión expiró. Iniciá sesión nuevamente."
    )

@auth_bp.get("/logout")
def logout_get():
    session.clear()
    return redirect(url_for("cliente.cartelera"))

@auth_bp.get("/perfil/configuracion")
def configuracion_perfil():
    return render_template("auth/configuracion_perfil.html")
