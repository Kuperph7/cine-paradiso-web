(() => {
    const form = document.querySelector("[data-seat-map]");
    if (!form) return;

    const status = form.querySelector("[data-seat-status]");
    const stateClasses = [
        "state-disponible",
        "state-retenida",
        "state-pago_en_proceso",
        "state-vendida",
        "occupied",
    ];

    const refresh = async () => {
        try {
            const response = await fetch(form.dataset.availabilityUrl, {
                headers: { Accept: "application/json" },
                cache: "no-store",
            });
            if (!response.ok) throw new Error("availability");
            const data = await response.json();
            data.butacas.forEach((seat) => {
                const input = form.querySelector(`[data-seat-id="${seat.id}"]`);
                const label = form.querySelector(`[data-seat-label="${seat.id}"]`);
                if (!input || !label || input.checked) return;
                const available = seat.estado === "disponible";
                input.disabled = !available;
                stateClasses.forEach((name) => label.classList.remove(name));
                label.classList.add(`state-${seat.estado}`);
                label.classList.toggle("occupied", !available);
                label.title = `Butaca ${seat.fila}${seat.numero}: ${seat.estado}`;
            });
            if (status) {
                status.textContent = `${data.butacas_libres} lugares disponibles · actualizado ahora`;
            }
        } catch (_error) {
            if (status) status.textContent = "No pudimos actualizar. Validaremos al continuar.";
        }
    };

    window.setInterval(refresh, 8000);
})();
