# Cine Paradiso Web

Frontend del sistema Cine Paradiso, desarrollado con Flask y templates Jinja.
La comunicación con el backend se realiza desde Python mediante `requests`.

## Preparación local

1. Crear y activar un entorno virtual de Python.
2. Instalar las dependencias con `pip install -r requirements.txt`.
3. Copiar `.env.example` como `.env` y completar la configuración local.
4. Iniciar primero la API backend.
5. Ejecutar el frontend con `python run.py`.

Por defecto, el frontend se abre en `http://127.0.0.1:5001` y espera encontrar
la API en `http://127.0.0.1:5000`.

## Organización

- `app/routes`: navegación y renderizado de páginas.
- `app/services/api_client.py`: comunicación con el backend usando `requests`.
- `app/templates/auth`: registro, inicio de sesión y perfil.
- `app/templates/cliente`: cartelera, compras y entradas.
- `app/templates/administrador`: backoffice del administrador.
- `app/static`: estilos e imágenes.
- `tests`: pruebas automatizadas de las páginas.
- `docs`: mockups y documentación del frontend.
