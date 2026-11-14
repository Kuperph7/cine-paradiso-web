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

## Flujo de reservas

Al continuar desde el mapa de butacas, el frontend solicita una retención de
cinco minutos y conserva únicamente su identificador. Candy y el resumen
consultan siempre esa reserva en la API, muestran el vencimiento calculado por
el backend y redirigen si recibe `410 Gone`.

La pantalla final inicia un pago pendiente y lo resuelve mediante una pasarela
ficticia: pagar confirma la compra y emite las entradas; cancelar libera las
butacas. Si el usuario vuelve a la cartelera antes de decidir, la API informa
la reserva activa y el inicio muestra “Continuar con la compra”. El mapa
actualiza la disponibilidad cada ocho segundos y maneja los conflictos `409`
sin asumir que el estado visual sea la fuente de verdad.
