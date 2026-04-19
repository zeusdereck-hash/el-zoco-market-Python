from django.shortcuts import render
from .models import Producto, Categoria

def index(request):
    # Obtener productos de la base de datos filtrados por categoría
    context = {
        'productos_telefonia': Producto.objects.filter(categoria__nombre='Telefonia', disponible=True),
        'productos_moto': Producto.objects.filter(categoria__nombre='Moto Gadgets', disponible=True),
        'productos_hogar': Producto.objects.filter(categoria__nombre='Mascotas y Hogar', disponible=True),
    }
    return render(request, 'tienda/index.html', context)