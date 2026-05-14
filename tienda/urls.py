from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('contacto/', views.contacto, name='contacto'),
    path('tienda/ticket/abono/<int:abono_id>/', views.ticket_abono, name='ticket_abono'),
    path('pos/', views.pos_view, name='pos'),
    path('procesar-pago/', views.procesar_pago, name='procesar_pago'),
    path('tienda/ticket/venta/<int:id>/', views.generar_ticket, {'tipo': 'venta'}, name='ticket_venta'),
]
