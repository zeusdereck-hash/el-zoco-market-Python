from django.contrib import admin
from django.http import HttpResponse
from openpyxl import Workbook
from .models import Categoria, Producto

# --- ACCIÓN PARA EXPORTAR A EXCEL ---
@admin.action(description="📦 Descargar Inventario El Zoco (Excel)")
def exportar_a_excel(modeladmin, request, queryset):
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="Inventario_El_Zoco_Market.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Productos"

    # Definimos los encabezados basándonos en tus campos de list_display
    headers = ['Nombre', 'Categoría', 'Precio', 'Código/SKU', 'Estado', 'Fecha de Creación']
    ws.append(headers)

    # Llenamos las filas con los datos del queryset
    for producto in queryset:
        ws.append([
            producto.nombre,
            str(producto.categoria),
            producto.precio,
            getattr(producto, 'codigo', 'N/A'), # Usamos getattr por si el campo varía
            "Disponible" if producto.disponible else "No disponible",
            producto.created_at.strftime('%d/%m/%Y') if producto.created_at else ''
        ])

    wb.save(response)
    return response

# --- CONFIGURACIÓN DEL ADMIN ---

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'badge', 'disponible', 'created_at')
    list_filter = ('categoria', 'badge', 'disponible')
    search_fields = ('nombre', 'codigo', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}
    list_editable = ('precio', 'disponible')
    list_per_page = 20
    
    # AGREGAMOS LA ACCIÓN AQUÍ
    actions = [exportar_a_excel]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('categoria', 'nombre', 'slug', 'codigo')
        }),
        ('Precio y Descripción', {
            'fields': ('precio', 'descripcion', 'imagen')
        }),
        ('Etiquetas y Estado', {
            'fields': ('badge', 'disponible')
        }),
    )