(() => {
    const panel = document.querySelector("[data-payment-poll]");
    if (!panel) return;
    const countdown = panel.querySelector("[data-payment-countdown]");
    const message = panel.querySelector("[data-payment-message]");
    const expiresAt = Date.parse(panel.dataset.paymentExpiry);

    panel.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", () => {
            panel.querySelectorAll("button").forEach((button) => {
                button.disabled = true;
            });
            message.textContent = "Procesando tu decisión…";
        });
    });

    const tick = () => {
        const remaining = Math.max(0, expiresAt - Date.now());
        const seconds = Math.ceil(remaining / 1000);
        countdown.textContent = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
        panel.querySelector(".payment-hold")?.classList.toggle("is-urgent", remaining <= 60000);
        if (remaining === 0) {
            countdown.textContent = "Vencido";
            message.textContent = "El tiempo para completar la compra venció. Las butacas volverán a estar disponibles.";
        }
    };

    const poll = async () => {
        try {
            const response = await fetch(panel.dataset.paymentPoll, {
                headers: { Accept: "application/json" },
                cache: "no-store",
            });
            const data = await response.json();
            if (data.estado === "vendida" && data.compra_id) {
                window.location.replace(`/compras/${data.compra_id}/confirmacion`);
                return;
            }
            if (response.status === 410 || data.estado === "pago_rechazado") {
                message.textContent = "El pago no se confirmó a tiempo y no se emitieron entradas.";
            }
        } catch (_error) {
            message.textContent = "No pudimos actualizar el estado. Podés intentar pagar o cancelar nuevamente.";
        }
    };

    tick();
    window.setInterval(tick, 1000);
    window.setInterval(poll, 5000);
})();
