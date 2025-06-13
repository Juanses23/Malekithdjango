function habilitarCampo(campoId) {
    const input = document.getElementById(campoId);
    const guardarBtn = input.nextElementSibling.nextElementSibling;

    input.removeAttribute('readonly');
    input.focus();
    guardarBtn.style.display = 'inline';
}
