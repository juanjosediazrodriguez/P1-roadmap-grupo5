// Manejar selección visual de checkboxes
document.querySelectorAll('.option-card').forEach(card => {
    const input = card.querySelector('input');
    
    if (input.checked) {
        card.classList.add('selected');
    }
    
    card.addEventListener('click', function(e) {
        if (input.type === 'checkbox') {
            setTimeout(() => {
                if (input.checked) {
                    this.classList.add('selected');
                } else {
                    this.classList.remove('selected');
                }
            }, 10);
        }
    });
});


document.querySelectorAll('.radio-option').forEach(option => {
    const radio = option.querySelector('input');
    
    // Estado inicial
    if (radio.checked) {
        option.classList.add('selected');
    }
    
    option.addEventListener('click', function() {
        // Solo aplica si el radio no estaba ya seleccionado
        if (!radio.checked) {

            // Deseleccionar todos los radios del mismo grupo
            document.querySelectorAll(`input[name="${radio.name}"]`).forEach(r => {
                r.checked = false;
                r.closest('.radio-option').classList.remove('selected');
            });

            // Seleccionar este
            radio.checked = true;
            this.classList.add('selected');
        } 
    });
});