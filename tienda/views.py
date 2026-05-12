from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Producto
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from .models import Producto, Categoria, Venta, Deuda, Abono

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

def generar_ticket(request, tipo, id):
    items = []
    total = 0
    folio = id
    
    if tipo == 'venta':
        obj = get_object_or_404(Venta, id=id)
        tipo_comprobante = "COMPROBANTE DE VENTA"
        total = obj.total
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

def ticket_abono(request, abono_id):
    from django.db.models import Sum
    abono_actual = get_object_or_404(Abono, id=abono_id)
    deuda = abono_actual.deuda
    
    # Historial para calcular la posición
    historial_abonos = deuda.abonos.all().order_by('fecha')
    lista_abonos = list(historial_abonos)
    
    try:
        numero_pago_actual = lista_abonos.index(abono_actual) + 1
    except ValueError:
        numero_pago_actual = 1

    total_pagado = historial_abonos.filter(pagado=True).aggregate(total=Sum('monto'))['total'] or 0

    context = {
        'tipo_comprobante': 'ESTADO DE CUENTA',
        'folio': abono_actual.id,
        'fecha': abono_actual.fecha,
        'proveedor': deuda.persona,
        'historial': historial_abonos.filter(pagado=True),
        'monto_total_origin': deuda.monto_total,
        'total_pagado': total_pagado,
        'saldo_restante': deuda.saldo_pendiente,
        'usuario_atendio': request.user.get_full_name() or request.user.username,
        
        # Estas variables deben coincidir exactamente con el HTML
        'total_pagos': deuda.cantidad_pagos,      
        'periodicidad': deuda.periodicidad_dias,  
        'numero_pago': numero_pago_actual,        
    }
    return render(request, 'tienda/ticket_abono.html', context)

def buscar_producto_codigo(request, codigo):
    producto = get_object_or_404(Producto, codigo=codigo)
    return JsonResponse({
        'id': producto.id,
        'nombre': producto.nombre,
        'precio': float(producto.precio),
        'stock': producto.stock
    })

def pos_view(request):
    # Esta vista carga tu nuevo template estilo App
    return render(request, 'tienda/pos.html')

def buscar_producto(request, codigo):
    # Busca por el campo 'codigo' que tienes en tu ProductoAdmin
    producto = get_object_or_404(Producto, codigo=codigo, disponible=True)
    data = {
        'id': producto.id,
        'nombre': producto.nombre,
        'precio': float(producto.precio),
        'codigo': producto.codigo,
        'imagen': producto.imagen.url if producto.imagen else '/static/img/default.png'
    }
    return JsonResponse(data)

@csrf_exempt # Solo para pruebas locales, en producción usa el token CSRF
def guardar_venta(request):
    if request.method == 'POST':
        datos = json.loads(request.body)
        # 1. Crear la Venta
        nueva_venta = Venta.objects.create(
            total=datos['total'],
            metodo_pago=datos['metodo_pago']
        )
        # 2. Crear los detalles y descontar stock
        for item in datos['productos']:
            prod = Producto.objects.get(id=item['id'])
            VentaDetalle.objects.create(
                venta=nueva_venta,
                producto=prod,
                cantidad=item['cantidad'],
                precio_unitario=item['precio']
            )
            prod.stock -= item['cantidad']
            prod.save()
            
        return JsonResponse({'status': 'ok', 'venta_id': nueva_venta.id})   