import datetime
from django.db import models
from django.utils.text import slugify
from django.db.models import Sum
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.html import format_html
from django.contrib.auth.models import User

# --- MODELOS DE LA TIENDA ---

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    BADGE_CHOICES = [
        ('Nuevo', 'Nuevo'),
        ('Premium', 'Premium'),
        ('Mas Vendido', 'Mas Vendido'),
    ]

    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo de Compra")
    stock = models.IntegerField(default=0, verbose_name="Cantidad en Existencia")
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='productos/')
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, blank=True, null=True)
    disponible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class MovimientoCaja(models.Model):
    TIPO_CHOICES = [('INGRESO', 'Ingreso (+)'), ('GASTO', 'Gasto (-)')]
    tipo = models.CharField(max_length=7, choices=TIPO_CHOICES)
    descripcion = models.TextField(verbose_name="Concepto (Ej. Renta, Pago Proveedor)")
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Caja"
        verbose_name_plural = "Movimientos de Caja"
        ordering = ['-monto']


# --- CLASE BASE PARA FINANZAS (Estructura Compartida Abstracta) ---

class BaseCredito(models.Model):
    persona = models.CharField(max_length=200)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField(default=timezone.now, verbose_name="Fecha de Inicio")
    
    # Slots de programación
    cantidad_pagos = models.PositiveIntegerField(default=1, verbose_name="Cantidad de Plazos")
    periodicidad_dias = models.PositiveIntegerField(default=0, verbose_name="Cada cuántos días")
    monto_por_pago = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        editable=False, 
        default=0, 
        verbose_name="Monto x c/pago"
    )

    class Meta:
        abstract = True

    @property
    def saldo_pendiente(self):
        total_abonado = self.abonos.filter(pagado=True).aggregate(total=Sum('monto'))['total'] or 0
        return self.monto_total - total_abonado

    def actualizar_cuota(self):
        """Recalcula el monto por pago basado en el saldo pendiente actual de forma segura"""
        saldo = self.saldo_pendiente
        if self.cantidad_pagos > 0:
            nuevo_monto = saldo / self.cantidad_pagos
            self.__class__.objects.filter(pk=self.pk).update(monto_por_pago=nuevo_monto)


# --- SECCIÓN FINANZAS: 1. CUENTAS POR PAGAR (PROVEEDORES) ---

class Deuda(BaseCredito):
    class Meta:
        verbose_name = "Cuenta por Pagar)"
        verbose_name_plural = "Cuentas por Pagar"

    def __str__(self):
        return f"{self.persona} (${self.saldo_pendiente})"

    def save(self, *args, **kwargs):
        if self.pk:
            saldo = self.saldo_pendiente
        else:
            saldo = self.monto_total

        if self.cantidad_pagos > 0:
            self.monto_por_pago = saldo / self.cantidad_pagos
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Generación automática de plazos programados para Proveedores
        if is_new and self.cantidad_pagos > 1 and self.periodicidad_dias > 0:
            for i in range(self.cantidad_pagos):
                fecha_pago = self.fecha_inicio + timezone.timedelta(days=i * self.periodicidad_dias)
                Abono.objects.create(
                    deuda=self,
                    monto=self.monto_por_pago,
                    fecha=fecha_pago,
                    pagado=False
                )


# --- SECCIÓN FINANZAS: 2. VENTAS A CRÉDITO (CLIENTES) ---

class VentaCredito(BaseCredito):
    # Vinculación opcional a la venta del POS para auditoría de qué productos se llevaron a crédito
    venta = models.OneToOneField('Venta', on_delete=models.SET_NULL, null=True, blank=True, related_name='credito_asignado')

    class Meta:
        verbose_name = "Venta a Crédito"
        verbose_name_plural = "Ventas a Crédito"

    def __str__(self):
        return f"Cliente: {self.persona} (${self.saldo_pendiente})"

    def save(self, *args, **kwargs):
        if self.pk:
            saldo = self.saldo_pendiente
        else:
            saldo = self.monto_total

        if self.cantidad_pagos > 0:
            self.monto_por_pago = saldo / self.cantidad_pagos
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Generación automática de plazos programados para Clientes
        if is_new and self.cantidad_pagos > 1 and self.periodicidad_dias > 0:
            for i in range(self.cantidad_pagos):
                fecha_pago = self.fecha_inicio + timezone.timedelta(days=i * self.periodicidad_dias)
                Abono.objects.create(
                    venta_credito=self,
                    monto=self.monto_por_pago,
                    fecha=fecha_pago,
                    pagado=False
                )


# --- TABLA UNIFICADA DE HISTORIAL DE ABONOS ---

class Abono(models.Model):
    # Un abono pertenece dinámicamente a una Deuda de Proveedor O a una Venta a Crédito de Cliente
    deuda = models.ForeignKey(Deuda, on_delete=models.CASCADE, related_name='abonos', null=True, blank=True)
    venta_credito = models.ForeignKey(VentaCredito, on_delete=models.CASCADE, related_name='abonos', null=True, blank=True)
    
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Pago/Programada")
    pagado = models.BooleanField(default=True, verbose_name="¿Pagado?")

    def __str__(self):
        if self.deuda:
            return f"Abono de ${self.monto} -> Prov: {self.deuda.persona}"
        return f"Abono de ${self.monto} <- Cliente: {self.venta_credito.persona}"

    class Meta:
        verbose_name = "Abono"
        verbose_name_plural = "Historial General de Abonos"
        ordering = ['fecha', '-id']


# --- HISTORIAL DE VENTAS (POS) ---

def generar_folio():
    from .models import Venta 
    ultimo_ticket = Venta.objects.all().order_by('id').last()
    fecha_hoy = datetime.datetime.now().strftime("%Y%m%d")
    
    if not ultimo_ticket:
        return f"ZOCO-{fecha_hoy}-00001"
    
    nuevo_id = ultimo_ticket.id + 1
    return f"ZOCO-{fecha_hoy}-{nuevo_id:05d}"


class Venta(models.Model):
    folio = models.CharField(
        max_length=30, 
        unique=True, 
        default=generar_folio,
        verbose_name="Folio Ticket",
        editable=False
    )
    
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha/Hora")
    cliente = models.CharField(max_length=100, default="Venta Mostrador")
    
    FORMA_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('MERCADO PAGO', 'Mercado Pago'),
        ('PAYPAL', 'PayPal'),
        ('TARJETA', 'Tarjeta'),
        ('CREDITO', 'Crédito'), # Nueva opción integrada
    ]
    
    forma_pago = models.CharField(
        max_length=50, 
        choices=FORMA_PAGO_CHOICES, 
        default="EFECTIVO"
    )
    
    total = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    vendedor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    qr_data = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Ticket de Venta"
        verbose_name_plural = "Historial de Tickets (Cajas)"

    def __str__(self):
        return f"Ticket {self.folio} - {self.cliente}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='productos', on_delete=models.CASCADE)
    producto = models.ForeignKey('Producto', on_delete=models.SET_NULL, null=True)
    descripcion = models.CharField(max_length=255)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=0)

    def __str__(self):
        return f"{self.cantidad} x {self.descripcion}"


# --- RECEPTORES DE SEÑALES (Signals) ---

# --- RECEPTORES DE SEÑALES (Signals) ---

@receiver(post_save, sender=Abono)
@receiver(post_delete, sender=Abono)
def actualizar_finanzas_al_abonar(sender, instance, **kwargs):
    """Dispara de forma inteligente el recálculo en el módulo financiero que corresponda"""
    if instance.deuda:
        instance.deuda.actualizar_cuota()
    if instance.venta_credito:
        instance.venta_credito.actualizar_cuota()


@receiver(post_save, sender=Venta)
def crear_venta_a_credito_desde_pos(sender, instance, created, **kwargs):
    """
    Automatización: Si el POS genera un ticket marcado como 'CREDITO',
    se abre automáticamente un expediente en Ventas a Crédito (Clientes).
    """
    if created and instance.forma_pago == 'CREDITO':
        if not VentaCredito.objects.filter(venta=instance).exists():
            VentaCredito.objects.create(
                venta=instance,
                persona=instance.cliente,
                monto_total=instance.total,
                fecha_inicio=instance.fecha.date(),
                cantidad_pagos=1,
                periodicidad_dias=0
            )


@receiver(post_save, sender=Venta)
def registrar_ingreso_caja_desde_pos(sender, instance, created, **kwargs):
    """
    Automatización: Si el POS genera una venta con pago inmediato (Efectivo, Transferencia, MP),
    registra automáticamente el ingreso en el módulo de Movimientos de Caja.
    """
    if created and instance.forma_pago in ['EFECTIVO', 'TRANSFERENCIA', 'MERCADO_PAGO']:
        descripcion_movimiento = f"Venta POS - Folio #{instance.folio}"
        
        if not MovimientoCaja.objects.filter(descripcion=descripcion_movimiento).exists():
            MovimientoCaja.objects.create(
                tipo='INGRESO',
                monto=instance.total,
                descripcion=descripcion_movimiento,
                fecha=instance.fecha
            )