from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.db.models import Sum
from django.utils import timezone 
from .models import Categoria, Producto, MovimientoCaja, Deuda, Abono, Venta 
from django.utils.html import format_html
from .models import Deuda
from django.urls import path
from django.shortcuts import redirect

# --- CONFIGURACIÓN DEL SITIO ADMINISTRATIVO PERSONALIZADO ---

# admin.py

class ElZocoAdminSite(admin.AdminSite):
    site_header = "El Zoco Market - Panel de Control"
    index_title = "Administración del Sistema"
    index_template = 'admin/dashboard_zoco.html'

    def index(self, request, extra_context=None):
        from .models import MovimientoCaja, Deuda, Abono
        from django.db.models import Sum
        
        # --- CÁLCULOS DE CAJA ---
        ingresos_totales = MovimientoCaja.objects.filter(tipo='INGRESO').aggregate(total=Sum('monto'))['total'] or 0
        egresos_totales = MovimientoCaja.objects.filter(tipo='GASTO').aggregate(total=Sum('monto'))['total'] or 0
        
        # --- CÁLCULOS DE DEUDAS (Tarjetas nuevas) ---
        deudas_qs = Deuda.objects.all()
        # Monto total de lo que se ha pactado con proveedores
        total_deuda_original = deudas_qs.aggregate(total=Sum('monto_total'))['total'] or 0
        
        # Saldo pendiente real (suma de lo que falta en cada deuda)
        pendiente_proveedores = sum(d.saldo_pendiente for d in deudas_qs)
        
        # Total ya pagado (Abonos realizados)
        total_pagado_deudas = Abono.objects.filter(pagado=True).aggregate(total=Sum('monto'))['total'] or 0

        extra_context = extra_context or {}
        extra_context.update({
            'balance': ingresos_totales - egresos_totales,
            'ingresos_totales': ingresos_totales,
            'egresos_totales': egresos_totales,
            'pendiente_proveedores': pendiente_proveedores,
            'total_deuda_original': total_deuda_original,
            'total_pagado_deudas': total_pagado_deudas,
        })
        
        return super().index(request, extra_context)

    def get_app_list(self, request, app_label=None):
        app_dict = self._build_app_dict(request, app_label)
        
        # 1. Extraer las piezas
        auth_app = app_dict.get('auth')
        tienda_app = app_dict.get('tienda')
        
        final_list = []

        # 2. INSERTAR AUTENTICACIÓN PRIMERO
        if auth_app:
            # Forzamos que sea el primer elemento
            final_list.append(auth_app)

        # 3. CONSTRUIR GRUPO TIENDA
        if tienda_app:
            modelos = tienda_app['models']
            
            # Separar modelos
            modelos_tienda = [m for m in modelos if m['object_name'] in ['Venta', 'Producto', 'Categoria']]
            modelos_finanzas = [m for m in modelos if m['object_name'] in ['Deuda', 'MovimientoCaja']]

            # Agregar Bloque Tienda
            if modelos_tienda:
                # Copiamos la estructura original para mantener iconos y estilos
                tienda_group = tienda_app.copy()
                tienda_group['name'] = 'Tienda'
                tienda_group['models'] = modelos_tienda
                final_list.append(tienda_group)
            
            # Agregar Bloque Finanzas
            if modelos_finanzas:
                finanzas_group = tienda_app.copy() # Copiamos de 'tienda' para heredar el contexto de la app
                finanzas_group['name'] = 'Finanzas'
                finanzas_group['app_label'] = 'finanzas'
                finanzas_group['models'] = modelos_finanzas
                final_list.append(finanzas_group)

        # 4. Agregar cualquier otra cosa que no sea auth o tienda
        for app in app_dict.values():
            if app['app_label'] not in ['auth', 'tienda']:
                final_list.append(app)

        return final_list

# Instancia del sitio personalizado
admin_site = ElZocoAdminSite(name='elzoco_admin')

# --- ACCIONES ---

@admin.action(description="💰 Exportar Deudas (Formato El Zoco)")
def exportar_deudas_excel_custom(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Reporte_Deudas_Zoco.xlsx"'
    wb = Workbook()
    ws = wb.active
    ws.title = "Deudas"
    header_fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
    red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    white_font = Font(color="FFFFFF", bold=True)
    header_font = Font(bold=True, size=12)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    center_align = Alignment(horizontal="center", vertical="center")
    headers = ['Proveedor', 'Deuda', 'Abonado', 'Fechas de Abonos', 'Resto deuda', '% avance']
    ws.append(headers)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border
    for deuda in queryset:
        abonos = deuda.abonos.all()
        total_abonado = sum(a.monto for a in abonos)
        resto = deuda.monto_total - total_abonado
        avance = (total_abonado / deuda.monto_total) if deuda.monto_total > 0 else 0
        fechas_texto = ", ".join([a.fecha.strftime('%d/%m/%Y') for a in abonos])
        ws.append([deuda.persona, deuda.monto_total, total_abonado, fechas_texto if fechas_texto else "Sin abonos", resto, avance])
        for cell in ws[ws.max_row]:
            cell.border = border
            if cell.column in [2, 3, 5]: cell.number_format = '"$"#,##0'
            if cell.column == 6:
                cell.number_format = '0%'
                cell.alignment = center_align
                if avance >= 1:
                    cell.fill = red_fill
                    cell.font = white_font
    wb.save(response)
    return response

# --- REGISTRO DE MODELOS ---

@admin.register(Categoria, site=admin_site)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}

@admin.register(Producto, site=admin_site)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'categoria', 'disponible')
    search_fields = ('nombre',)
    list_filter = ('categoria',)

class AbonoInline(admin.TabularInline):
    model = Abono
    extra = 1
    fields = ('monto', 'fecha')

@admin.register(Deuda, site=admin_site)
class DeudaAdmin(admin.ModelAdmin):
    actions = [exportar_deudas_excel_custom]
    readonly_fields = ('monto_por_pago',)
    fieldsets = (
        ('Información General', {'fields': ('persona', 'monto_total', 'fecha_inicio')}),
        ('Programación de Pagos', {'fields': ('cantidad_pagos', 'periodicidad_dias','monto_por_pago')}),
    )
    list_display = ('persona', 'monto_total', 'saldo_pendiente', 'pago_actual', 'monto_por_pago', 'avance_pago', 'imprimir_ticket_boton')
    search_fields = ('persona', 'monto_total')
    list_filter = ('persona', 'monto_total')
    inlines = [AbonoInline]

    def changelist_view(self, request, extra_context=None):
        # 1. Cálculos de Deudas sin decimales
        deudas_qs = Deuda.objects.all()
        
        # Usamos int() para forzar que no haya decimales
        total_original = int(deudas_qs.aggregate(total=Sum('monto_total'))['total'] or 0)
        total_pagado = int(Abono.objects.filter(pagado=True).aggregate(total=Sum('monto'))['total'] or 0)
        total_pendiente = int(sum(d.saldo_pendiente for d in deudas_qs))

        extra_context = extra_context or {}
        extra_context.update({
            'total_deuda_original': total_original,
            'total_pagado_deudas': total_pagado,
            'pendiente_proveedores': total_pendiente,
        })
        
        return super().changelist_view(request, extra_context=extra_context)
    
    def pago_actual(self, obj):
        pagados = obj.abonos.filter(pagado=True).count()
        total = obj.cantidad_pagos
        if total > 1:
            if pagados >= total: return format_html('<span style="color: #15ff00; font-weight: bold;">Completado</span>')
            return format_html("Pago <b>{}</b> de <b>{}</b>", pagados, total)
        return "Pago Único"
    pago_actual.short_description = "Esquema"

    def imprimir_ticket_boton(self, obj):
        ultimo_abono = obj.abonos.first() 
        if ultimo_abono:
            return format_html('<a class="button" href="/tienda/ticket/abono/{}/" target="_blank">🎟️ Ticket</a>', ultimo_abono.id)
        return "Sin abonos"
    imprimir_ticket_boton.short_description = "Ticket"

    def avance_pago(self, obj):
        total = float(obj.monto_total)
        pendiente = float(obj.saldo_pendiente)
        pagado = total - pendiente
        porcentaje = int((pagado / total) * 100) if total > 0 else 0
        color = "#ff4d4d" if porcentaje < 30 else "#f57e06" if porcentaje < 70 else "#19850f"
        return format_html('<div style="background-color: {}; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">{}%</div>', color, porcentaje)

@admin.register(MovimientoCaja, site=admin_site)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'descripcion', 'monto', 'fecha', 'imprimir_ticket')
    def imprimir_ticket(self, obj):
        return format_html('<a class="button" href="/tienda/ticket/venta/{}/" target="_blank">🎟️ Ticket</a>', obj.id)

@admin.register(Venta, site=admin_site)
class VentaAdmin(admin.ModelAdmin):
    # Desactivamos edición para que sea solo "Sección de Información"
    list_display = ('ticket_preview', 'total_destacado', 'fecha_formateada')
    readonly_fields = ('folio', 'fecha', 'total', 'forma_pago', 'cliente')
    
    def ticket_preview(self, obj):
        # Genera una mini-tarjeta visual en el listado
        return format_html(
            '<div style="background: #fff; border: 1px solid #ddd; padding: 10px; border-left: 5px solid #000; width: 250px;">'
            '<span style="font-size: 10px; color: #888;">FOLIO: {}</span><br>'
            '<strong style="font-size: 14px;">{}</strong><br>'
            '<small>Pago: {}</small>'
            '</div>',
            obj.folio, obj.cliente.upper(), obj.forma_pago
        )
    ticket_preview.short_description = "Información del Ticket"

    def total_destacado(self, obj):
        return format_html('<span style="font-size: 18px; font-weight: bold;">${:,.0f}</span>', obj.total)
    total_destacado.short_description = "Total"

    def fecha_formateada(self, obj):
        return obj.fecha.strftime("%d/%m/%Y %H:%M")
# Registrar Autenticación al final del archivo pero aparecerán primero por la lógica de get_app_list
admin_site.register(User)
admin_site.register(Group)
admin_site.site_header = "El Zoco"