
document.addEventListener("DOMContentLoaded", () => {

    const dialog = document.getElementById("funcion-dialog");

    if (!dialog) {
        return;
    }

    const funcionId = document.getElementById("funcion-id-edicion");
    const pelicula = document.getElementById("pelicula-edicion");
    const sala = document.getElementById("sala-edicion");
    const fecha = document.getElementById("fecha-edicion");
    const horario = document.getElementById("horario-edicion");
    const precio = document.getElementById("precio-edicion");
    const formato = document.getElementById("formato-edicion");
    const idioma = document.getElementById("idioma-edicion");

    document.querySelectorAll("[data-editar-funcion]").forEach((boton) => {

        boton.addEventListener("click", () => {

            funcionId.value = boton.dataset.funcionId;
            pelicula.value = boton.dataset.peliculaId;
            sala.value = boton.dataset.salaId;
            fecha.value = boton.dataset.fecha;
            horario.value = boton.dataset.horario;
            precio.value = boton.dataset.precio;
            formato.value = boton.dataset.formato;
            idioma.value = boton.dataset.idioma;

            dialog.showModal();

        });
    });

    dialog.querySelectorAll("[data-cerrar-dialog]").forEach((boton) => {

        boton.addEventListener("click", () => {
            dialog.close();
        });

    });

});
