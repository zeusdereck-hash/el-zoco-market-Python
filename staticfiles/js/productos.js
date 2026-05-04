
// Base de datos de productos
const productosData = {
    telefonia: [
        {
            id: 'cargador-65w',
            nombre: 'CARGADOR 65W GAN FAST',
            precio: 380,
            codigo: 'GAN-65W-FAST',
            imagen: '/static/img/productos/cargador_65w.jpg',
            badge: 'Nuevo',
            descripcion: '⚡ Tecnología GaN: Más potencia en menor tamaño\n🚀 Carga Ultra Rápida de 65W para Laptop y Celular\n🔌 Puertos Duales: USB-C (PD) + USB-A\n🛡️ Protección inteligente contra sobrecalentamiento\n📱 Compatible con iPhone, Samsung y Xiaomi.'
        },
        {
            id: 'cargador-essager',
            nombre: 'CARGADOR ESSAGER 100W GAN',
            precio: 650,
            codigo: 'ESG-100W-GAN',
            imagen: '/static/img/productos/cargadorPD.jpg',
            badge: 'Premium',
            descripcion: '⚡ Potencia Extrema de 100W GaN\n💻 Carga Laptops, Macbooks y Celulares\n🚀 Soporta PD 4.0, QC 3.0\n🔌 2 Puertos tipo C y 2 tipo A\n🛡️ Tecnología de disipación de calor avanzada.'
        },
        {
            id: 'soporte-aluminio',
            nombre: 'SOPORTE DE ALUMINIO 360°',
            precio: 350,
            codigo: 'SUP-ALUM-360',
            imagen: '/static/img/productos/soporte_aluminio.jpg',
            badge: 'Nuevo',
            descripcion: '🔄 Base giratoria de 360° para ángulos perfectos\n🏗️ Construcción robusta en aleación de aluminio\n📏 Altura y ángulo totalmente ajustables\n🛡️ Almohadillas de silicona antideslizantes\n💻 Ideal para Celulares, Tablets y iPad.'
        }
    ],
    moto: [
        {
            id: 'bepocam',
            nombre: 'Navegación Moto BEPOCAM',
            precio: 2100,
            codigo: 'BEPO-GPS-2026',
            imagen: '/static/img/productos/bepocam1.jpg',
            badge: 'Mas Vendido',
            descripcion: '🚀 Navegación profesional para Uber y Didi\n📱 Pantalla táctil HD 6.25 pulgadas\n🎥 Cámara DVR para grabar tus viajes\n📍 GPS con mapas actualizados y alertas\n🔊 Conexión Bluetooth para manos libres\n⚡ Batería de larga duración (8+ horas)'
        },
        {
            id: 'q58-max',
            nombre: 'Intercomunicador Q58 Max',
            precio: 810,
            codigo: 'Q58MAX2026',
            imagen: '/static/img/productos/intercomunicador_q58.jpg',
            badge: null,
            descripcion: 'Pantalla LCD, Radio FM y alcance de 500m.'
        },
        {
            id: 'bolsa-tanque',
            nombre: 'Bolsa de Tanque Táctica',
            precio: 550,
            codigo: 'MH-TANK-2026',
            imagen: '/static/img/productos/bolsa_tanque.jpg',
            badge: 'Nuevo',
            descripcion: '📱 Ventana Táctil para control de dispositivos\n🌧️ 100% impermeable\n🎒 Convertible a bolsa de hombro\n🛡️ Material táctico de alta resistencia.'
        },
        {
            id: 'candado-alarma',
            nombre: 'CANDADO ALARMA SEGURIDAD',
            precio: 380,
            codigo: 'ALRM-DISC-380',
            imagen: '/static/img/productos/candado_alarma.jpg',
            badge: 'Nuevo',
            descripcion: '🔊 Alarma potente de 110dB\n🛡️ Aleación de aluminio ultra resistente\n🌊 100% Impermeable y resistente al clima\n🔋 Incluye baterías y llaves de seguridad\n🚲 Ideal para motosicletas.'
        }
    ],
    hogar: [
        {
            id: 'funda-asientos',
            nombre: 'Funda Protectora de Asientos',
            precio: 550,
            codigo: '852147963',
            imagen: '/static/img/productos/funda_asientos.jpg',
            badge: null,
            descripcion: 'Impermeable y resistente para mascotas.'
        },
        {
            id: 'control-seg',
            nombre: 'Control SEG',
            precio: 280,
            codigo: '7501098612074',
            imagen: '/static/img/productos/ControlSEG.jpg',
            badge: null,
            descripcion: 'Original SEG 433MHz para portones.'
        }
    ]
};

// Función para renderizar productos en el grid
function renderizarProductos() {
    console.log("Renderizando productos...");
    
    // Renderizar telefonía
    const gridTelefonia = document.getElementById('productos-telefonia');
    if (gridTelefonia) {
        gridTelefonia.innerHTML = productosData.telefonia.map(producto => crearTarjetaProducto(producto)).join('');
    }

    // Renderizar moto
    const gridMoto = document.getElementById('productos-moto');
    if (gridMoto) {
        gridMoto.innerHTML = productosData.moto.map(producto => crearTarjetaProducto(producto)).join('');
    }

    // Renderizar hogar
    const gridHogar = document.getElementById('productos-hogar');
    if (gridHogar) {
        gridHogar.innerHTML = productosData.hogar.map(producto => crearTarjetaProducto(producto)).join('');
    }
    
    console.log("✅ Productos renderizados");
}

// Función para crear una tarjeta de producto
function crearTarjetaProducto(producto) {
    // Mapear los badges a las clases CSS correctas
    let badgeClass = '';
    if (producto.badge) {
        if (producto.badge.toLowerCase() === 'nuevo') {
            badgeClass = 'badge-top';
        } else if (producto.badge.toLowerCase() === 'premium') {
            badgeClass = 'badge-premium';
        } else if (producto.badge.toLowerCase() === 'mas vendido') {
            badgeClass = 'badge-mas-vendido';
        } else {
            badgeClass = 'badge-top';
        }
    }
    
    const badgeHTML = producto.badge ? 
        `<span class="${badgeClass}">${producto.badge}</span>` : '';
    
    // Escapar la descripción para que no rompa el HTML
    const descripcionEscapada = producto.descripcion.replace(/'/g, "\\'").replace(/\n/g, '\\n');
    
    return `
        <article class="product-card" data-nombre="${producto.nombre.toLowerCase()}" data-etiquetas="${producto.badge ? producto.badge.toLowerCase() : ''}">
            ${badgeHTML}
            <img src="${producto.imagen}" alt="${producto.nombre}" 
                 onclick="elZocoApp.verDetalles('${producto.nombre}', ${producto.precio}, '${descripcionEscapada}', '${producto.imagen}', '${producto.codigo}')" 
                 loading="lazy">
            <h3>${producto.nombre}</h3>
            <p class="precio-card">$${producto.precio.toFixed(2)}</p>
            <button class="btn-add" onclick="elZocoApp.agregarAlCarrito('${producto.nombre}', ${producto.precio}, event, '${producto.codigo}')">
                Añadir al Carrito
            </button>
        </article>
    `;
}

// Hacer disponible para otros archivos
window.productosData = productosData;
window.renderizarProductos = renderizarProductos;
window.crearTarjetaProducto = crearTarjetaProducto;

console.log("✅ productos.js cargado con rutas /static/");