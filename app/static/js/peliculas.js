document.addEventListener("DOMContentLoaded", () => {
    const dialog = document.getElementById("pelicula-dialog");
    const form = document.getElementById("pelicula-form");

    if (!dialog || !form) {
        return;
    }

    const idInput = document.getElementById("pelicula-id");
    const idExternoInput = document.getElementById("pelicula-id-externo");
    const tituloInput = document.getElementById("pelicula-titulo");
    const sinopsisInput = document.getElementById("pelicula-sinopsis");
    const posterInput = document.getElementById("pelicula-poster-url");
    const duracionInput = document.getElementById("pelicula-duracion");
    const clasificacionInput = document.getElementById("pelicula-clasificacion");
    const generoInput = document.getElementById("pelicula-genero");
    const dialogTitle = document.getElementById("pelicula-dialog-title");
    const erroresPanel = document.getElementById("pelicula-errores");

    if (dialog.dataset.conErrores === "true") {
        dialog.showModal();
    }

    document.querySelectorAll("[data-pelicula-open]").forEach((button) => {
        button.addEventListener("click", () => {
            const editar = button.dataset.peliculaOpen === "editar";

            form.reset();
            form.querySelectorAll("input, textarea").forEach((campo) => {
                campo.value = "";
            });
            if (erroresPanel) {
                erroresPanel.hidden = true;
            }

            form.action = editar ? button.dataset.action : form.dataset.crearUrl;
            idInput.value = editar ? button.dataset.id || "" : "";
            idExternoInput.value = editar ? "" : button.dataset.idExterno || "";
            tituloInput.value = button.dataset.titulo || "";
            sinopsisInput.value = button.dataset.sinopsis || "";
            posterInput.value = button.dataset.posterUrl || "";
            duracionInput.value = editar ? button.dataset.duracion || "" : "";
            clasificacionInput.value = editar ? button.dataset.clasificacion || "" : "";
            generoInput.value = editar ? button.dataset.genero || "" : "";
            dialogTitle.textContent = editar ? "Editar película" : "Añadir película";

            dialog.showModal();
        });
    });

    dialog.querySelector(".dialog-close").addEventListener("click", () => {
        dialog.close();
    });

    dialog.querySelector(".dialog-cancel").addEventListener("click", () => {
        dialog.close();
    });
});