// App principal de El Zoco Market
const elZocoApp = (function() {
    // Variables privadas
    let carrito = [];
    let totalAcumulado = 0;
    let sonidoPop = null;

    // Inicialización
    function init() {
        // Cargar carrito desde localStorage
        cargarCarritoStorage();
        
        // Inicializar audio
        try {
            sonidoPop = new Audio('https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3');
            sonidoPop.volume = 0.5;
        } catch (e) {
            console.log('Audio no disponible');
        }

        // Renderizar productos - COMENTADO TEMPORALMENTE
        // if (typeof renderizarProductos === 'function') {
        //     renderizarProductos();
        // }

        // Event listeners
        document.getElementById('btnAbrirCarrito').addEventListener('click', function() {
            renderizarCarrito();
            abrirModal('modalCarrito');
        });

        document.getElementById('searchInput').addEventListener('keyup', filtrarProductos);

        // Cerrar modales con Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                cerrarModales();
            }
        });

        // Actualizar contador del carrito
        actualizarContadorCarrito();
    }

    // ========== FUNCIONES DEL CARRITO ==========

    function agregarAlCarrito(nombre, precio, event, codigo = "0000000000000") {
        // Reproducir sonido
        if (sonidoPop) {
            sonidoPop.currentTime = 0;
            sonidoPop.play().catch(e => console.log('Audio requiere interacción'));
        }

        // Agregar al carrito
        carrito.push({ nombre, precio, codigo });
        
        // Guardar en localStorage
        guardarCarritoStorage();
        
        // Actualizar contador
        actualizarContadorCarrito();

        // Animación del carrito
        const cartIcon = document.querySelector('.cart-icon');
        cartIcon.classList.add('cart-shake');
        setTimeout(() => cartIcon.classList.remove('cart-shake'), 400);

        // Notificación flotante
        if (event) {
            crearNotificacionFlotante(event);
        }
    }

    function eliminarUno(nombreProducto) {
        const indice = carrito.map(item => item.nombre).lastIndexOf(nombreProducto);
        
        if (indice !== -1) {
            carrito.splice(indice, 1);
        }
        
        guardarCarritoStorage();
        actualizarContadorCarrito();
        renderizarCarrito();
    }

    function eliminarGrupo(nombreProducto) {
        carrito = carrito.filter(item => item.nombre !== nombreProducto);
        guardarCarritoStorage();
        actualizarContadorCarrito();
        renderizarCarrito();
    }

    function vaciarCarrito() {
        if (carrito.length === 0) return;
        
        if (confirm("¿Estás seguro de que quieres vaciar todo el carrito?")) {
            carrito = [];
            guardarCarritoStorage();
            actualizarContadorCarrito();
            renderizarCarrito();
        }
    }

    function renderizarCarrito() {
        const contenedor = document.getElementById('listaItems');
        if (!contenedor) return;
        
        contenedor.innerHTML = '';
        totalAcumulado = 0;

        if (carrito.length === 0) {
            contenedor.innerHTML = '<p style="text-align:center; padding:20px;">Tu carrito está vacío</p>';
            document.getElementById('textoTotal').innerText = "Total: $0.00";
            return;
        }

        // Agrupar productos
        let agrupados = {};
        carrito.forEach(item => {
            if (!agrupados[item.nombre]) {
                agrupados[item.nombre] = { cantidad: 0, precio: item.precio, codigo: item.codigo };
            }
            agrupados[item.nombre].cantidad++;
            totalAcumulado += item.precio;
        });

        // Renderizar items agrupados
        for (let nombre in agrupados) {
            const prod = agrupados[nombre];
            const itemDiv = document.createElement('div');
            itemDiv.className = 'cart-item';
            itemDiv.innerHTML = `
                <span><b>${prod.cantidad}x</b> ${nombre}</span>
                <div>
                    <span>$${(prod.cantidad * prod.precio).toFixed(2)}</span>
                    <button onclick="elZocoApp.eliminarUno('${nombre}')" class="btn-del" aria-label="Eliminar uno">
                        <i class="fas fa-minus-circle"></i>
                    </button>
                </div>
            `;
            contenedor.appendChild(itemDiv);
        }
        
        document.getElementById('textoTotal').innerText = "Total: $" + totalAcumulado.toFixed(2);
    }

    // ========== FUNCIONES DE ALMACENAMIENTO ==========

    function guardarCarritoStorage() {
        try {
            localStorage.setItem('elZocoCarrito', JSON.stringify(carrito));
        } catch (e) {
            console.log('Error al guardar en localStorage');
        }
    }

    function cargarCarritoStorage() {
        try {
            const guardado = localStorage.getItem('elZocoCarrito');
            if (guardado) {
                carrito = JSON.parse(guardado);
                actualizarContadorCarrito();
            }
        } catch (e) {
            console.log('Error al cargar desde localStorage');
        }
    }

    function actualizarContadorCarrito() {
        const contador = document.querySelector('.cart-count');
        if (contador) {
            contador.innerText = carrito.length;
        }
    }

    // ========== FUNCIONES DE MODALES ==========

    function abrirModal(idModal) {
        cerrarModales();
        const modal = document.getElementById(idModal);
        if (modal) {
            modal.classList.add('open');
            document.body.style.overflow = 'hidden';
        }
    }

    function cerrarModales() {
        const modales = document.querySelectorAll('.modal');
        modales.forEach(modal => modal.classList.remove('open'));
        document.body.style.overflow = '';
    }

    function abrirEnvio() {
        if (carrito.length === 0) {
            alert("El carrito está vacío");
            return;
        }
        abrirModal('modalEnvio');
    }

    function pasarAPago() {
        const nom = document.getElementById('inputNombreEnvio').value.trim();
        const dir = document.getElementById('inputDireccion').value.trim();
        const tel = document.getElementById('inputTel').value.trim();
        
        if (!nom || !dir || !tel) {
            alert("Por favor, completa todos los datos para el envío");
            return;
        }
        
        if (tel.length !== 10 || !/^\d+$/.test(tel)) {
            alert("Por favor, ingresa un teléfono válido de 10 dígitos");
            return;
        }
        
        abrirModal('modalPago');
    }

    // ========== FUNCIÓN DE ENVÍO A WHATSAPP ==========

    function enviarPedido() {
        const numero = "525580867149";
        const nombre = document.getElementById('inputNombreEnvio').value.trim();
        const direccion = document.getElementById('inputDireccion').value.trim();
        const telefono = document.getElementById('inputTel').value.trim();

        if (!nombre || !direccion || !telefono) {
            alert("Por favor, completa todos los datos de envío.");
            return;
        }

        // Agrupar productos para el mensaje
        let agrupados = {};
        carrito.forEach(item => {
            if (!agrupados[item.nombre]) {
                agrupados[item.nombre] = { cantidad: 0, codigo: item.codigo };
            }
            agrupados[item.nombre].cantidad++;
        });

        // Construir mensaje
        let texto = `*NUEVA COTIZACION O VENTA*\n`;
        texto += `Confirmo mi pago con el comprobante anexo\n`;
        texto += `--------------------------\n`;
        texto += `👤 CLIENTE: ${nombre}\n`;
        texto += `📞 TEL: ${telefono}\n`;
        texto += `📍 DIR: ${direccion}\n`;
        texto += `--------------------------\n`;
        
        for (let n in agrupados) {
            texto += `*${agrupados[n].cantidad} -> ${n.toUpperCase()} :PZA : ${agrupados[n].codigo}\n`;
        }

        // Cerrar el modal de pago ANTES de lanzar el confeti
        cerrarModales();
        
        // Pequeña pausa para asegurar que el modal se cerró
        setTimeout(() => {
            // Lanzar confeti con efecto mejorado
            if (typeof confetti === 'function') {
                // Primera oleada - confeti principal
                confetti({
                    particleCount: 2500,
                    spread: 70,
                    origin: { y: 0.6 },
                    zIndex: 3000,
                    colors: ['#ca870b', '#2c3e50', '#ffffff', '#ffd700', '#e74c3c', '#3498db']
                });
                
                // Segunda oleada - confeti desde la izquierda
                setTimeout(() => {
                    confetti({
                        particleCount: 2000,
                        spread: 100,
                        origin: { y: 0.5, x: 0.2 },
                        zIndex: 3000,
                        colors: ['#ca870b', '#2c3e50', '#ffd700']
                    });
                }, 150);
                
                // Tercera oleada - confeti desde la derecha
                setTimeout(() => {
                    confetti({
                        particleCount: 2000,
                        spread: 100,
                        origin: { y: 0.5, x: 0.8 },
                        zIndex: 3000,
                        colors: ['#ca870b', '#2c3e50', '#ffd700']
                    });
                }, 300);
                
                // Cuarta oleada - confeti de celebración
                setTimeout(() => {
                    confetti({
                        particleCount: 2200,
                        spread: 120,
                        origin: { y: 0.7 },
                        zIndex: 3000,
                        colors: ['#e74c3c', '#3498db', '#ca870b']
                    });
                }, 450);
            }

            // Enviar WhatsApp después de 2 segundos (para disfrutar el confeti)
            setTimeout(() => {
                const enlace = `https://wa.me/${numero}?text=${encodeURIComponent(texto)}`;
                window.open(enlace, '_blank');

                // Limpiar carrito
                carrito = [];
                guardarCarritoStorage();
                actualizarContadorCarrito();

                // Limpiar formulario
                document.getElementById('inputNombreEnvio').value = '';
                document.getElementById('inputDireccion').value = '';
                document.getElementById('inputTel').value = '';

                renderizarCarrito();
            }, 2000);
        }, 100);
    }

    // ========== FUNCIONES DE UTILIDAD ==========

    function crearNotificacionFlotante(event) {
        const bubble = document.createElement('div');
        bubble.className = 'floating-notify';
        bubble.innerText = '+1';
        bubble.style.left = event.clientX + 'px';
        bubble.style.top = event.clientY + 'px';
        document.body.appendChild(bubble);
        setTimeout(() => bubble.remove(), 1500);
    }

    function verDetalles(nombre, precio, desc, img, codigo) {
        cerrarModales();
        
        document.getElementById('detallesNombre').innerText = nombre;
        document.getElementById('detallesPrecio').innerText = `$${precio.toFixed(2)}`;
        document.getElementById('detallesDesc').innerText = desc;
        document.getElementById('detallesImg').src = img;
        document.getElementById('detallesImg').alt = nombre;
        
        const btn = document.getElementById('btnAgregarDesdeDetalle');
        btn.onclick = function(event) {
            agregarAlCarrito(nombre, precio, event, codigo);
            cerrarModales();
        };

        abrirModal('modalDetalles');
    }

    function filtrarProductos() {
        const input = document.getElementById('searchInput');
        if (!input) return;
        
        const filter = input.value.toLowerCase().trim();
        const tarjetas = document.querySelectorAll('.product-card');

        let visibleCount = 0;
        
        tarjetas.forEach(tarjeta => {
            // Buscar en el nombre del producto
            const nombre = tarjeta.querySelector('h3').innerText.toLowerCase();
            
            // Buscar en la etiqueta (badge)
            let etiqueta = '';
            const badgeElement = tarjeta.querySelector('[class^="badge-"]');
            if (badgeElement) {
                etiqueta = badgeElement.innerText.toLowerCase();
            }
            
            // Buscar en el precio
            const precioElement = tarjeta.querySelector('.precio-card');
            const precio = precioElement ? precioElement.innerText.toLowerCase() : '';
            
            // Si el filtro está vacío, mostrar todos
            if (filter === '') {
                tarjeta.style.display = "block";
                visibleCount++;
            } 
            // Buscar coincidencias en nombre O etiqueta
            else if (nombre.includes(filter) || etiqueta.includes(filter) || precio.includes(filter)) {
                tarjeta.style.display = "block";
                visibleCount++;
            } else {
                tarjeta.style.display = "none";
            }
        });

        // Manejar mensaje de "no resultados"
        const grids = document.querySelectorAll('.products-grid');
        grids.forEach(grid => {
            // Eliminar mensajes anteriores
            const oldNoResults = grid.querySelector('.no-results');
            if (oldNoResults) oldNoResults.remove();
            
            // Si no hay productos visibles en este grid y hay filtro
            const tarjetasVisibles = Array.from(grid.querySelectorAll('.product-card')).filter(card => card.style.display !== "none");
            
            if (tarjetasVisibles.length === 0 && filter !== '') {
                const msg = document.createElement('p');
                msg.className = 'no-results';
                msg.innerText = 'No se encontraron productos en esta categoría';
                msg.style.gridColumn = '1/-1';
                msg.style.textAlign = 'center';
                msg.style.padding = '40px';
                grid.appendChild(msg);
            }
        });
    }

    function compartirPagina() {
        const shareData = {
            title: 'El Zoco Market',
            text: '¡Mira estos tesoros y soluciones extraordinarias que encontré en El Zoco!',
            url: window.location.href
        };

        if (navigator.share) {
            navigator.share(shareData)
                .catch(err => console.log('Error al compartir:', err));
        } else {
            navigator.clipboard.writeText(window.location.href)
                .then(() => alert("¡Enlace copiado al portapapeles! Compártelo con tus amigos. 🚀"))
                .catch(() => alert("No se pudo copiar el enlace"));
        }
    }

    function contactarSoporte() {
        const numero = "525580867149";
        const texto = encodeURIComponent("Hola El Zoco Market, me gustaría recibir atención personalizada sobre un producto.");
        window.open(`https://wa.me/${numero}?text=${texto}`, '_blank');
    }

    // Función para cambiar entre opciones de pago
    function mostrarPago(tipo) {
        // Ocultar todas las secciones
        document.querySelectorAll('.pago-seccion').forEach(sec => sec.classList.remove('active'));
        
        // Desactivar todos los botones
        document.querySelectorAll('.pago-opcion').forEach(btn => btn.classList.remove('activa'));
        
        // Mostrar la sección seleccionada
        document.getElementById(`pago-${tipo}`).classList.add('active');
        
        // Activar el botón correspondiente
        event.target.classList.add('activa');
    }

    // API pública
    return {
        init,
        agregarAlCarrito,
        eliminarUno,
        eliminarGrupo,
        vaciarCarrito,
        abrirEnvio,
        pasarAPago,
        enviarPedido,
        verDetalles,
        abrirModal,
        cerrarModales,
        compartirPagina,
        contactarSoporte,
        filtrarProductos,
        mostrarPago  // ← Agregada correctamente
    };
})();

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    elZocoApp.init();
    
    // Exponer funciones globalmente para onclick
    window.elZocoApp = elZocoApp;
});