document.addEventListener("DOMContentLoaded", () => {
    const toast = document.querySelector("[data-toast]");

    if (!toast) {
        return;
    }

    const closeButton = toast.querySelector("[data-toast-close]");
    let timeoutId;

    const dismiss = () => {
        window.clearTimeout(timeoutId);
        toast.classList.add("is-leaving");
        window.setTimeout(() => toast.remove(), 240);
    };

    closeButton?.addEventListener("click", dismiss);
    timeoutId = window.setTimeout(dismiss, 8000);
});
