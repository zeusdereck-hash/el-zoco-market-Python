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

# --- VISTAS DE TICKETS CORREGIDAS ---

def generar_ticket(request, tipo, id):
    """Maneja la visualización del ticket de venta"""
    if tipo == 'venta':
        venta = get_object_or_404(Venta, id=id)
        context = {
            'venta': venta,
            'tipo_comprobante': 'TICKET DE VENTA',
        }
        return render(request, 'tienda/ticket_pos.html', context)
    return redirect('pos')

def ticket_abono(request, abono_id):
    """Maneja la visualización del ticket de abono (Evita el AttributeError)"""
    abono = get_object_or_404(Abono, id=abono_id)
    return render(request, 'tienda/ticket_abono.html', {'abono': abono})

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