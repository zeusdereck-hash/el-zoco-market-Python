from django.contrib import admin
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.db.models import Sum # Importamos para cálculos más rápidos
from .models import Categoria, Producto, MovimientoCaja, Deuda, Abono

# --- REPORTE PERSONALIZADO EL ZOCO (NARANJA / ROJO) ---

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

    headers = ['PROVEEDORES', 'Deuda', 'Abonado', 'Fechas de Abonos', 'Resto deuda', '% avance']
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

        ws.append([
            deuda.persona,
            deuda.monto_total,
            total_abonado,
            fechas_texto if fechas_texto else "Sin abonos",
            resto,
            avance
        ])

        for cell in ws[ws.max_row]:
            cell.border = border
            if cell.column in [2, 3, 5]:
                cell.number_format = '"$"#,##0'
            if cell.column == 6:
                cell.number_format = '0%'
                cell.alignment = center_align
                if avance >= 1:
                    cell.fill = red_fill
                    cell.font = white_font

    column_widths = [25, 15, 15, 35, 15, 12]
    for i, width in enumerate(column_widths):
        ws.column_dimensions[ws.cell(row=1, column=i+1).column_letter].width = width

    wb.save(response)
    return response

# --- CONFIGURACIÓN DEL PANEL ---

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'categoria', 'disponible')
    search_fields = ('nombre',)
    list_filter = ('categoria',)

class AbonoInline(admin.TabularInline):
    model = Abono
    extra = 1
    readonly_fields = ('fecha',)

@admin.register(Deuda)
class DeudaAdmin(admin.ModelAdmin):
    list_display = ('persona', 'monto_total', 'saldo_pendiente', 'yo_debo', 'fecha_limite')
    list_filter = ('yo_debo', 'fecha_limite')
    inlines = [AbonoInline]
    actions = [exportar_deudas_excel_custom]

    # IMPORTANTE: Indica la ruta de la plantilla personalizada
    change_list_template = "admin/tienda/deuda/change_list.html"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            # Obtenemos el queryset actual (considerando filtros y búsquedas)
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        # Cálculo de totales eficiente usando agregación de base de datos
        total_deuda = qs.aggregate(total=Sum('monto_total'))['total'] or 0

        # Sumamos todos los abonos relacionados al queryset actual
        total_abonado = Abono.objects.filter(deuda__in=qs).aggregate(total=Sum('monto'))['total'] or 0

        total_pendiente = total_deuda - total_abonado

        # Enviamos los datos al template
        extra_context = extra_context or {}
        extra_context['resumen_zoco'] = {
            'total': total_deuda,
            'abonado': total_abonado,
            'pendiente': total_pendiente,
        }

        response.context_data.update(extra_context)
        return response

@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'descripcion', 'monto', 'fecha')