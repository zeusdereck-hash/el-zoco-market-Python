from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.db import transaction
from .models import Producto, Categoria, Venta, DetalleVenta, Deuda, Abono

def index(request):
    context = {
        'productos_telefonia': Producto.objects.filter(categoria__nombre='Telefonia', disponible=True),
        'productos_moto': Producto.objects.filter(categoria__nombre='Moto Gadgets', disponible=True),
        'productos_hogar': Producto.objects.filter(categoria__nombre='Mascotas y Hogar', disponible=True),
        'productos_salud': Producto.objects.filter(categoria__nombre='Deporte y Salud', disponible=True),
    }
    return render(request, 'tienda/index.html', context)

def contacto(request):
    return render(request, 'tienda/contacto.html')

def pos_view(request):
    productos = Producto.objects.filter(stock__gt=0)
    categorias = Categoria.objects.all()
    ultimo = Venta.objects.last()
    prox_id = (ultimo.id + 1) if ultimo else 1
    context = {
        'productos': productos,
        'categorias': categorias,
        'folio': f"TK-{prox_id:04d}"
    }
    return render(request, 'tienda/pos.html', context)

# --- LÓGICA DE TICKETS Y COMPROBANTES (Formato Unificado) ---

def generar_ticket(request, id, tipo='venta'):
    
    if tipo == 'venta':
        venta = get_object_or_404(Venta, id=id)
        return render(request, 'tienda/ticket_pos.html', {'venta': venta})

        items = []
        for det in obj.productos.all():
            items.append({
                'cantidad': int(det.cantidad),
                'descripcion': det.descripcion,
                'precio': int(det.precio_unitario),
                'subtotal': int(det.subtotal)
            })
            
        context = {
            'venta': obj,  # Enviamos el objeto completo para {{ venta.fecha }}, etc.
            'tipo_comprobante': "TICKET DE VENTA",
            'folio': obj.folio,
            'fecha': obj.fecha,
            'cliente': obj.cliente,
            'items': items,
            'total': int(obj.total),
            'forma_pago': obj.forma_pago,
        }
        return render(request, 'tienda/ticket_pos.html', context)
    
    return redirect('admin:index')


def ticket_abono(request, abono_id):
    """
    Maneja la visualización del ticket de abono/estado de cuenta.
    Inyecta exactamente las variables que el HTML en blanco está buscando.
    """
    abono_actual = get_object_or_404(Abono, id=abono_id)
    deuda = abono_actual.deuda
    historial_abonos = Abono.objects.filter(deuda=deuda).order_by('fecha')
    
    try:
        lista_ids = list(historial_abonos.values_list('id', flat=True))
        numero_pago_actual = lista_ids.index(abono_actual.id) + 1
    except ValueError:
        numero_pago_actual = 1

    total_pagado = historial_abonos.filter(pagado=True).aggregate(total=Sum('monto'))['total'] or 0

    # Mapeo de campo seguro según el modelo Deuda (usa .persona)
    proveedor_nombre = "No asignado"
    if deuda:
        if hasattr(deuda, 'persona'):
            proveedor_nombre = deuda.persona
        elif hasattr(deuda, 'proveedor'):
            proveedor_nombre = deuda.proveedor

    context = {
        'abono': abono_actual,
        'tipo_comprobante': 'COMPROBANTE DE ABONO',
        
        # Variables que el HTML espera
        'folio': f"ABO-{abono_actual.id:05d}",
        'fecha': abono_actual.fecha,
        'proveedor': proveedor_nombre, 
        
        # Datos cuantitativos de la Deuda
        'monto_total_origin': deuda.monto_total if deuda else 0,
        'total_pagado': total_pagado,
        'saldo_restante': deuda.saldo_pendiente if deuda else 0,
        
        # Datos complementarios de impresión
        'usuario_atendio': request.user.get_full_name() or request.user.username or "SISTEMA",
        'total_pagos': deuda.cantidad_pagos if deuda else 1,      
        'periodicidad': deuda.periodicidad_dias if deuda else 0,  
        'numero_pago': numero_pago_actual,        
    }
    return render(request, 'tienda/ticket_abono.html', context)

@csrf_exempt
def procesar_pago(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            carrito = data.get('carrito', [])
            total = data.get('total', 0)
            forma_pago = data.get('forma_pago', 'EFECTIVO')
            cliente = data.get('cliente', 'Venta Mostrador')

            with transaction.atomic():
                nueva_venta = Venta.objects.create(
                    total=total,
                    forma_pago=forma_pago,
                    cliente=cliente,
                    vendedor=request.user if request.user.is_authenticated else None
                )

                for item in carrito:
                    producto = Producto.objects.get(id=item['id'])
                    
                    # CORRECCIÓN: Extraer dinámicamente la cantidad agrupada del frontend (con valor por defecto 1)
                    cantidad_comprada = int(item.get('cantidad', 1))
                    
                    if producto.stock < cantidad_comprada:
                        raise Exception(f"Stock insuficiente para: {producto.nombre}. Disponible: {producto.stock}")

                    # Calcular el subtotal real multiplicando precio unitario por cantidad agrupada
                    precio_unitario = float(item['precio'])
                    subtotal_renglon = precio_unitario * cantidad_comprada

                    DetalleVenta.objects.create(
                        venta=nueva_venta,
                        producto=producto,
                        descripcion=producto.nombre,
                        cantidad=cantidad_comprada,       # <-- CORREGIDO: Guarda la cantidad real
                        precio_unitario=precio_unitario,
                        subtotal=subtotal_renglon         # <-- CORREGIDO: Guarda el subtotal real
                    )

                    # Descontar el total de piezas vendidas del inventario
                    producto.stock -= cantidad_comprada
                    producto.save()

                return JsonResponse({
                    'status': 'ok',
                    'venta_id': nueva_venta.id,
                    'folio': nueva_venta.folio
                })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)