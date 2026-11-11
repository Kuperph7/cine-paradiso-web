from flask import Blueprint, render_template , request , session , redirect , url_for
from app.services.api_client import api_post , api_get


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method =="GET": 
       return render_template("auth/login.html")
    
    datos = {
        "email": request.form.get("email", ""),
        "password": request.form.get("password", "")
    }
    
    respuesta = api_post("/auth/login", json = datos)
    
    if respuesta.ok:
        resultado = respuesta.json()
        session["token"] = resultado.get("token")
        session["usuario"] = resultado.get("usuario")
        
        return redirect(url_for("auth.perfil"))
        
    try:
        error = respuesta.json()
        
        
        mensaje = error.get("mensaje", "Email o contraseña incorrectos")
    
    except ValueError:
        mensaje = "No se pudo iniciar sesión"
    
    return render_template("auth/login.html", error = mensaje ), respuesta.status_code


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
def logout():
    session.clear()
    return redirect(url_for("cliente.cartelera"))

@auth_bp.get("/perfil/configuracion")
def configuracion_perfil():
    return render_template("auth/configuracion_perfil.html")