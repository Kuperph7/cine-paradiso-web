(() => {
    const hold = document.querySelector("[data-hold-expiry]");
    if (!hold) return;
    const output = hold.querySelector("[data-hold-countdown]");
    const expiresAt = Date.parse(hold.dataset.holdExpiry);

    const tick = () => {
        const remaining = Math.max(0, expiresAt - Date.now());
        const totalSeconds = Math.ceil(remaining / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        output.textContent = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
        hold.classList.toggle("is-urgent", remaining <= 60000);
        if (remaining === 0) {
            output.textContent = "Vencida";
            window.location.replace(hold.dataset.expiredUrl);
        }
    };

    tick();
    window.setInterval(tick, 1000);
})();
