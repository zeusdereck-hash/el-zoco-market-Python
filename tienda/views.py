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

# --- LÓGICA DE TICKETS Y COMPROBANTES (Formato Imagen WhatsApp) ---

def generar_ticket(request, tipo, id):
    items = []
    if tipo == 'venta':
        obj = get_object_or_404(Venta, id=id)
        # Extraemos los productos asociados a la venta
        detalles = obj.productos.all() 
        for det in detalles:
            items.append({
                'cantidad': int(det.cantidad),
                'descripcion': det.descripcion,
                'precio': int(det.precio_unitario),
                'subtotal': int(det.subtotal)
            })
            
        context = {
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
    abono_actual = get_object_or_404(Abono, id=abono_id)
    deuda = abono_actual.deuda
    historial_abonos = Abono.objects.filter(deuda=deuda).order_by('fecha')
    
    try:
        lista_ids = list(historial_abonos.values_list('id', flat=True))
        numero_pago_actual = lista_ids.index(abono_actual.id) + 1
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
        'total_pagos': deuda.cantidad_pagos,      
        'periodicidad': deuda.periodicidad_dias,  
        'numero_pago': numero_pago_actual,        
    }
    return render(request, 'tienda/ticket_abono.html', context)

# --- SISTEMA POS (POINT OF SALE) ---

def pos_view(request):
    productos = Producto.objects.filter(stock__gt=0)
    categorias = Categoria.objects.all()
    
    ultimo_ticket = Venta.objects.last()
    if ultimo_ticket:
        try:
            numero_folio = int(ultimo_ticket.folio.split('-')[-1]) + 1
            proximo_folio = f"TK-{numero_folio:04d}"
        except:
            proximo_folio = "TK-0001"
    else:
        proximo_folio = "TK-0001"

    context = {
        'productos': productos,
        'categorias': categorias,
        'folio': proximo_folio,
    }
    return render(request, 'tienda/pos.html', context)

def buscar_producto_codigo(request, codigo):
    producto = get_object_or_404(Producto, codigo=codigo)
    return JsonResponse({
        'id': producto.id,
        'nombre': producto.nombre,
        'precio': float(producto.precio),
        'stock': producto.stock
    })

@csrf_exempt
def procesar_pago(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            carrito = data.get('carrito', [])
            total = data.get('total', 0)
            forma_pago = data.get('forma_pago', 'EFECTIVO')
            cliente = data.get('cliente', 'Venta Mostrador')

            if not carrito:
                return JsonResponse({'status': 'error', 'message': 'El carrito está vacío'}, status=400)

            with transaction.atomic():
                # 1. Crear la Venta
                nueva_venta = Venta.objects.create(
                    total=total,
                    forma_pago=forma_pago,
                    cliente=cliente,
                    vendedor=request.user if request.user.is_authenticated else None
                )

                # 2. Registrar detalles y descontar stock
                for item in carrito:
                    producto = Producto.objects.get(id=item['id'])
                    
                    if producto.stock < 1:
                        raise Exception(f"Stock insuficiente para: {producto.nombre}")

                    DetalleVenta.objects.create(
                        venta=nueva_venta,
                        producto=producto,
                        descripcion=producto.nombre,
                        cantidad=1,
                        precio_unitario=item['precio'],
                        subtotal=item['precio']
                    )

                    # Descuento de inventario
                    producto.stock -= 1
                    producto.save()

                return JsonResponse({
                    'status': 'ok',
                    'venta_id': nueva_venta.id,
                    'folio': nueva_venta.folio
                })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)