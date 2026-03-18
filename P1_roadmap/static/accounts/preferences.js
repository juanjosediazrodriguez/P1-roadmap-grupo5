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

// Manejar selección visual de radios
document.querySelectorAll('.radio-option').forEach(option => {
    const radio = option.querySelector('input');
    
    if (radio.checked) {
        option.classList.add('selected');
    }
    
    option.addEventListener('click', function() {
        document.querySelectorAll(`input[name="${radio.name}"]`).forEach(r => {
            r.closest('.radio-option').classList.remove('selected');
        });
        
        radio.checked = true;
        this.classList.add('selected');
    });
});