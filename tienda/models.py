from django.db import models
from django.utils.text import slugify
from django.db.models import Sum
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

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

# --- SISTEMA DE DEUDAS Y ABONOS ---

class Deuda(models.Model):
    persona = models.CharField(max_length=200, verbose_name="Proveedor")
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField(default=timezone.now, verbose_name="Fecha de Inicio")
    yo_debo = models.BooleanField(default=True, verbose_name="¿Es deuda mía?")
    
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

    @property
    def saldo_pendiente(self):
        total_abonado = self.abonos.filter(pagado=True).aggregate(total=Sum('monto'))['total'] or 0
        return self.monto_total - total_abonado

    def __str__(self):
        return f"{self.persona} (${self.saldo_pendiente})"

    def actualizar_cuota(self):
        """Recalcula el monto por pago basado en el saldo pendiente actual"""
        saldo = self.saldo_pendiente
        if self.cantidad_pagos > 0:
            nuevo_monto = saldo / self.cantidad_pagos
            # Usamos update para evitar disparar señales recursivas
            Deuda.objects.filter(pk=self.pk).update(monto_por_pago=nuevo_monto)

    def save(self, *args, **kwargs):
        # Al guardar manualmente, calculamos según el saldo o monto total
        if self.pk:
            saldo = self.saldo_pendiente
        else:
            saldo = self.monto_total

        if self.cantidad_pagos > 0:
            self.monto_por_pago = saldo / self.cantidad_pagos
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Generación automática de abonos (solo para deudas nuevas)
        if is_new and self.cantidad_pagos > 1 and self.periodicidad_dias > 0:
            for i in range(self.cantidad_pagos):
                fecha_pago = self.fecha_inicio + timezone.timedelta(days=i * self.periodicidad_dias)
                Abono.objects.create(
                    deuda=self,
                    monto=self.monto_por_pago,
                    fecha=fecha_pago,
                    pagado=False
                )

    class Meta:
        verbose_name = "Deuda"
        verbose_name_plural = "Administración De Deudas"

class Abono(models.Model):
    deuda = models.ForeignKey(Deuda, on_delete=models.CASCADE, related_name='abonos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Pago/Programada")
    pagado = models.BooleanField(default=True, verbose_name="¿Pagado?")

    def __str__(self):
        return f"Abono de ${self.monto} - {self.deuda.persona}"

    class Meta:
        verbose_name = "Abono"
        verbose_name_plural = "Abonos"
        ordering = ['fecha']

# --- SISTEMA DE VENTAS ---

class Venta(models.Model):
    METODO_PAGO = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia/Tarjeta'),
    ]
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO, default='EFECTIVO')
    notas = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha.strftime('%d/%m/%Y')}"

class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)

# --- SEÑALES (Signals) ---
# Esto automatiza el recálculo al crear o eliminar abonos

@receiver(post_save, sender=Abono)
@receiver(post_delete, sender=Abono)
def actualizar_deuda_al_abonar(sender, instance, **kwargs):
    """Llamamos al método de recálculo de la deuda cada vez que hay cambios en sus abonos"""
    instance.deuda.actualizar_cuota()