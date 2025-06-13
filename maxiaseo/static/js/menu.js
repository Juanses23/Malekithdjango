document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("userMenuToggle");
    const menu = document.getElementById("userMenu");

    toggle.addEventListener("click", function (e) {
        e.preventDefault();
        menu.style.display = menu.style.display === "block" ? "none" : "block";
    });

    // Ocultar el menú si se hace clic fuera
    document.addEventListener("click", function (e) {
        if (!toggle.contains(e.target) && !menu.contains(e.target)) {
            menu.style.display = "none";
        }
    });
});
