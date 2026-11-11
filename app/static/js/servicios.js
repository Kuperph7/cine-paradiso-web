document.addEventListener("DOMContentLoaded", () => {
    const dialog = document.getElementById("servicio-dialog");

    if (!dialog) {
        return;
    }

    const idInput = document.getElementById("edit-servicio-id");
    const nombreInput = document.getElementById("edit-servicio-nombre");
    const descripcionInput = document.getElementById(
        "edit-servicio-descripcion"
    );
    const precioInput = document.getElementById("edit-servicio-precio");

    document.querySelectorAll("[data-edit-service]").forEach((button) => {
        button.addEventListener("click", () => {
            idInput.value = button.dataset.id || "";
            nombreInput.value = button.dataset.nombre || "";
            descripcionInput.value = button.dataset.descripcion || "";
            precioInput.value = button.dataset.precio || "";

            dialog.showModal();
        });
    });

    dialog.querySelectorAll("[data-close-dialog]").forEach((button) => {
        button.addEventListener("click", () => dialog.close());
    });

    const deleteButton = dialog.querySelector("[data-delete-service]");

    deleteButton.addEventListener("click", (event) => {
        const nombre = nombreInput.value || "este servicio";

        if (!window.confirm(`¿Querés borrar "${nombre}"?`)) {
            event.preventDefault();
        }
    });
});