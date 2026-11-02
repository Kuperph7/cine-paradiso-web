document.addEventListener("DOMContentLoaded", () => {
    const dialog = document.getElementById("pelicula-dialog");
    const form = document.getElementById("pelicula-form");

    if (!dialog || !form) {
        return;
    }

    const idInput = document.getElementById("pelicula-id");
    const sinopsisInput = document.getElementById("pelicula-sinopsis");
    const disponibilidadInput = document.getElementById(
        "pelicula-disponibilidad"
    );
    const dialogTitle = document.getElementById("pelicula-dialog-title");

    document.querySelectorAll("[data-pelicula-open]").forEach((button) => {
        button.addEventListener("click", () => {
            const editar = button.dataset.peliculaOpen === "editar";

            form.reset();

            idInput.value = editar ? button.dataset.id || "" : "";
            sinopsisInput.value = editar ? button.dataset.sinopsis || "" : "";
            disponibilidadInput.value = editar
                ? button.dataset.disponibilidad || ""
                : "";

            dialogTitle.textContent = editar
                ? "Editar película"
                : "Añadir película";

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