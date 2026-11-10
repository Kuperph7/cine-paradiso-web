const Formulario_registro = document.getElementById("Formulario-registro");

Formulario_registro.addEventListener("submit", function(event) {

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const nombre = document.getElementById("nombre").value;
    console.log(email);
    console.log(password);
    console.log(nombre);
});