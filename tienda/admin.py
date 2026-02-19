from django.contrib import admin
from .models import Categoria, Producto

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