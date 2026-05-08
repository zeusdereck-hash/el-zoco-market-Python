from django.shortcuts import render
from .models import Producto, Categoria
from django.shortcuts import render, get_object_or_404
from .models import Venta, Deuda, Abono

def index(request):
    # Obtener productos de la base de datos filtrados por categoría
    context = {
        'productos_telefonia': Producto.objects.filter(categoria__nombre='Telefonia', disponible=True),
        'productos_moto': Producto.objects.filter(categoria__nombre='Moto Gadgets', disponible=True),
        'productos_hogar': Producto.objects.filter(categoria__nombre='Mascotas y Hogar', disponible=True),
        'productos_salud': Producto.objects.filter(categoria__nombre='Deporte y Salud', disponible=True),
    }
    # Este return DEBE estar dentro de index (alineado con 'context')
    return render(request, 'tienda/index.html', context)

def contacto(request):
    # Este return DEBE estar dentro de contacto
    return render(request, 'tienda/contacto.html')

def generar_ticket(request, tipo, id):
    items = []
    total = 0
    folio = id
    
    if tipo == 'venta':
        obj = get_object_or_404(Venta, id=id)
        tipo_comprobante = "COMPROBANTE DE VENTA"
        total = obj.total
        # Suponiendo que tienes un modelo DetalleVenta relacionado
        for det in obj.detalles.all():
            items.append({
                'cantidad': det.cantidad,
                'descripcion': det.producto.nombre,
                'subtotal': det.subtotal
            })
            
    elif tipo == 'abono':
        obj = get_object_or_404(Abono, id=id)
        tipo_comprobante = "RECIBO DE ABONO"
        total = obj.monto
        items.append({
            'cantidad': 1,
            'descripcion': f"Abono a cuenta de {obj.deuda.persona}",
            'subtotal': obj.monto
        })

    context = {
        'tipo_comprobante': tipo_comprobante,
        'fecha': obj.fecha,
        'folio': folio,
        'items': items,
        'total': total,
    }
    return render(request, 'tienda/ticket_58mm.html', context)

from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from .models import Abono

def ticket_abono(request, abono_id):
    # Obtenemos el abono que disparó la impresión
    abono_actual = get_object_or_404(Abono, id=abono_id)
    deuda = abono_actual.deuda
    
    # Obtenemos todos los abonos de esta deuda, del más antiguo al más reciente
    historial_abonos = deuda.abonos.all().order_by('fecha')
    
    # Calculamos el total pagado hasta la fecha
    total_pagado = historial_abonos.aggregate(total=Sum('monto'))['total'] or 0

    context = {
        'tipo_comprobante': 'ESTADO DE CUENTA',
        'folio': abono_actual.id,
        'fecha': abono_actual.fecha,
        'proveedor': deuda.persona,
        'monto_actual': abono_actual.monto,
        'historial': historial_abonos,
        'monto_total_origin': deuda.monto_total,
        'total_pagado': total_pagado,
        'saldo_restante': deuda.saldo_pendiente,
        'usuario_atendio': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'tienda/ticket_abono.html', context)