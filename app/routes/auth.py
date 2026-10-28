from flask import Blueprint, render_template


auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login():
    return render_template("auth/login.html")


@auth_bp.get("/registro")
def registro():
    return render_template("auth/registro.html")


@auth_bp.get("/perfil")
def perfil():
    return render_template("auth/perfil.html")

