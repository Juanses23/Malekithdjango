document.addEventListener('DOMContentLoaded', function() {
            const productoSelect = document.getElementById('id_id_producto');
            const cantidadInput = document.getElementById('id_cantidad_producto');
            const costoCalculadoInput = document.getElementById('id_costo_entrada_calculado');
    
            function calcularCosto() {
                const productoId = productoSelect.value;
                const cantidad = cantidadInput.value;
    
                // --- AÑADIR ESTA VALIDACIÓN ---
                if (!productoId) { // Check if a product is selected
                    costoCalculadoInput.value = 'Seleccione producto';
                    return;
                }
                if (!cantidad || isNaN(cantidad) || parseFloat(cantidad) <= 0) { // Check if quantity is valid
                    costoCalculadoInput.value = 'Ingrese cantidad válida';
                    return;
                }
                // --- FIN DE LA VALIDACIÓN A AÑADIR ---
    
                fetch(`{% url 'calcular_costo_entrada_ajax' %}?producto_id=${productoId}&cantidad=${cantidad}`)
                    .then(response => {
                        if (!response.ok) { // Check if the HTTP response was successful
                            if (response.status === 400) {
                                return response.json().then(err => { throw new Error(err.error || 'Bad Request'); });
                            }
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.costo_total) {
                            costoCalculadoInput.value = parseFloat(data.costo_total).toFixed(2);
                        } else if (data.error) {
                            costoCalculadoInput.value = 'Error';
                            console.error('Error al calcular costo:', data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error en la llamada AJAX:', error);
                        costoCalculadoInput.value = 'Error de conexión/dato';
                    });
            }
    
            if (productoSelect) {
                productoSelect.addEventListener('change', calcularCosto);
            }
    
            if (cantidadInput) {
                cantidadInput.addEventListener('input', calcularCosto);
            }
    
            // Llamar al cálculo al cargar la página si ya hay valores (en caso de edición)
            calcularCosto();
        });