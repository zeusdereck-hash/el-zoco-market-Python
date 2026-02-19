#!/usr/bin/env python
# Script para migrar todos los productos de productos.js a la base de datos
# Ejecutar con: python migrar_todos_productos.py

import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elzoco.settings')
django.setup()

from tienda.models import Categoria, Producto
from django.utils.text import slugify

def generar_slug_unico(nombre):
    """Genera un slug único agregando un sufijo numérico si es necesario"""
    slug_base = slugify(nombre)
    slug = slug_base
    contador = 1
    
    # Verificar si el slug ya existe
    while Producto.objects.filter(slug=slug).exists():
        slug = f"{slug_base}-{contador}"
        contador += 1
    
    return slug

def limpiar_descripcion(texto):
    """Limpia y formatea la descripción"""
    if not texto:
        return "Sin descripción disponible"
    # Reemplazar caracteres especiales
    texto = texto.replace('\\n', '\n').replace('\\"', '"')
    return texto

def crear_categorias():
    """Crear las categorías si no existen"""
    categorias_data = [
        {'nombre': 'Telefonía', 'slug': 'telefonia'},
        {'nombre': 'Moto Gadgets', 'slug': 'moto-gadgets'},
        {'nombre': 'Mascotas y Hogar', 'slug': 'mascotas-y-hogar'}
    ]
    
    categorias = {}
    for cat_data in categorias_data:
        # Intentar obtener por slug primero
        try:
            cat = Categoria.objects.get(slug=cat_data['slug'])
            created = False
            print(f"📦 Categoría existente: {cat_data['nombre']}")
        except Categoria.DoesNotExist:
            # Si no existe por slug, crear nueva
            cat = Categoria.objects.create(
                nombre=cat_data['nombre'],
                slug=cat_data['slug']
            )
            created = True
            print(f"✅ Creada categoría: {cat_data['nombre']}")
        
        # Guardar en diccionario por nombre simplificado
        if 'Telefonía' in cat_data['nombre']:
            categorias['telefonia'] = cat
        elif 'Moto' in cat_data['nombre']:
            categorias['moto'] = cat
        else:
            categorias['hogar'] = cat
    
    return categorias

def migrar_productos():
    """Función principal de migración"""
    print("=" * 50)
    print("🚀 INICIANDO MIGRACIÓN DE PRODUCTOS")
    print("=" * 50)
    
    # Crear categorías
    categorias = crear_categorias()
    
    # Datos de productos (basados en productos.js)
    productos_data = {
        'telefonia': [
            {
                'nombre': 'REDMI NOTE 13',
                'precio': 3000.00,
                'codigo': '711000257145',
                'badge': 'Premium',
                'descripcion': '''📱 REDMI NOTE 13 - Pantalla AMOLED y Carga Rápida

El REDMI NOTE 13 redefine tu experiencia móvil con su impresionante pantalla AMOLED FHD+ de 120Hz.

🎯 Características:
• Pantalla AMOLED FHD+ 6.67" 120Hz
• Carga Rápida 33W
• Procesador Snapdragon
• Triple cámara 108MP
• Batería 5000 mAh
• Protección IP54

📦 Incluye:
- 1 REDMI NOTE 13
- 1 Cargador 33W
- 1 Cable USB-C
- 1 Funda protectora
- 1 Protector de pantalla
- Herramienta SIM
- Manual de usuario

✅ Producto 100% original'''
            },
            {
                'nombre': 'CARGADOR 65W GAN FAST',
                'precio': 380.00,
                'codigo': 'GAN-65W-FAST',
                'badge': 'Nuevo',
                'descripcion': '''⚡ Cargador 65W GAN Fast

Tecnología GaN: Más potencia en menor tamaño
Carga Ultra Rápida de 65W para Laptop y Celular
Puertos Duales: USB-C (PD) + USB-A
Protección inteligente contra sobrecalentamiento
Compatible con iPhone, Samsung y Xiaomi

✅ Cargador original de alta calidad'''
            },
            {
                'nombre': 'CARGADOR ESSAGER 100W GAN',
                'precio': 650.00,
                'codigo': 'ESG-100W-GAN',
                'badge': 'Premium',
                'descripcion': '''⚡ Cargador ESSAGER 100W GaN

Potencia Extrema de 100W GaN
Carga Laptops, Macbooks y Celulares
Soporta PD 4.0, QC 3.0
2 Puertos tipo C y 2 tipo A
Tecnología de disipación de calor avanzada

✅ Cargador profesional para múltiples dispositivos'''
            },
            {
                'nombre': 'SOPORTE DE ALUMINIO 360°',
                'precio': 350.00,
                'codigo': 'SUP-ALUM-360',
                'badge': 'Nuevo',
                'descripcion': '''🔄 Soporte de Aluminio 360°

Base giratoria de 360° para ángulos perfectos
Construcción robusta en aleación de aluminio
Altura y ángulo totalmente ajustables
Almohadillas de silicona antideslizantes
Ideal para Celulares, Tablets y iPad

✅ Soporte premium para tu escritorio'''
            }
        ],
        'moto': [
            {
                'nombre': 'Navegación Moto BEPOCAM',
                'precio': 2100.00,
                'codigo': 'BEPO-GPS-2026',
                'badge': 'Mas Vendido',
                'descripcion': '''🚀 Navegación Profesional BEPOCAM

Navegación profesional para Uber y Didi
Pantalla táctil HD 6.25 pulgadas
Cámara DVR para grabar tus viajes
GPS con mapas actualizados y alertas
Conexión Bluetooth para manos libres
Batería de larga duración (8+ horas)

✅ El favorito de los conductores'''
            },
            {
                'nombre': 'Intercomunicador Q58 Max',
                'precio': 810.00,
                'codigo': 'Q58MAX2026',
                'badge': '',
                'descripcion': '''🔊 Intercomunicador Q58 Max

Pantalla LCD
Radio FM
Alcance de 500m
Comunicación clara y nítida
Batería de larga duración

✅ Ideal para rutas en grupo'''
            },
            {
                'nombre': 'Bolsa de Tanque Táctica',
                'precio': 550.00,
                'codigo': 'MH-TANK-2026',
                'badge': 'Nuevo',
                'descripcion': '''🎒 Bolsa de Tanque Táctica

Ventana Táctil para control de dispositivos
100% impermeable
Convertible a bolsa de hombro
Material táctico de alta resistencia
Múltiples compartimentos

✅ La compañera perfecta para tu viaje'''
            },
            {
                'nombre': 'CANDADO ALARMA SEGURIDAD',
                'precio': 380.00,
                'codigo': 'ALRM-DISC-380',
                'badge': 'Nuevo',
                'descripcion': '''🔒 Candado Alarma de Seguridad

Alarma potente de 110dB
Aleación de aluminio ultra resistente
100% Impermeable
Incluye baterías y llaves de seguridad
Ideal para motocicletas

✅ Tu moto siempre protegida'''
            }
        ],
        'hogar': [
            {
                'nombre': 'Funda Protectora de Asientos',
                'precio': 550.00,
                'codigo': '852147963',
                'badge': '',
                'descripcion': '''🐕 Funda Protectora de Asientos

Impermeable y resistente para mascotas
Fácil de instalar y limpiar
Protege tus asientos de uñas y pelos
Material antideslizante
Compatible con la mayoría de vehículos

✅ Viaja cómodo con tu mascota'''
            },
            {
                'nombre': 'Control SEG',
                'precio': 280.00,
                'codigo': '7501098612074',
                'badge': '',
                'descripcion': '''🏠 Control SEG Original

Original SEG 433MHz para portones
Alta compatibilidad
Fácil programación
Diseño ergonómico
Largo alcance

✅ Control original de alta calidad'''
            }
        ]
    }
    
    # Estadísticas
    total_creados = 0
    total_existentes = 0
    
    # Migrar productos por categoría
    for cat_key, productos in productos_data.items():
        categoria = categorias[cat_key]
        print(f"\n📁 Procesando categoría: {categoria.nombre}")
        print("-" * 30)
        
        for prod_data in productos:
            # Verificar si el producto ya existe por código
            producto_existente = Producto.objects.filter(codigo=prod_data['codigo']).first()
            
            if producto_existente:
                print(f"  ⚠️ Ya existe: {prod_data['nombre']}")
                total_existentes += 1
                continue
            
            # Crear nuevo producto con slug único
            try:
                producto = Producto.objects.create(
                    categoria=categoria,
                    nombre=prod_data['nombre'],
                    slug=generar_slug_unico(prod_data['nombre']),
                    precio=prod_data['precio'],
                    codigo=prod_data['codigo'],
                    descripcion=limpiar_descripcion(prod_data['descripcion']),
                    badge=prod_data['badge'] if prod_data['badge'] else None,
                    disponible=True,
                )
                print(f"  ✅ Creado: {prod_data['nombre']} (${prod_data['precio']})")
                total_creados += 1
                
            except Exception as e:
                print(f"  ❌ Error al crear {prod_data['nombre']}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE MIGRACIÓN")
    print("=" * 50)
    print(f"✅ Productos creados: {total_creados}")
    print(f"📦 Productos existentes: {total_existentes}")
    print(f"🎯 Total procesados: {total_creados + total_existentes}")
    print("=" * 50)

if __name__ == '__main__':
    migrar_productos()