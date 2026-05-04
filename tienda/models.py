from django.db import models
from django.utils.text import slugify
from django.db.models import Sum

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

# --- SISTEMA DE DEUDAS Y ABONOS ---

class Deuda(models.Model):
    persona = models.CharField(max_length=200, verbose_name="Cliente o Proveedor")
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    yo_debo = models.BooleanField(default=False, verbose_name="¿Es una deuda mía?")
    fecha_limite = models.DateField(verbose_name="Fecha de Pago")

    @property
    def saldo_pendiente(self):
        # Calcula el saldo restando los abonos del monto total
        total_abonado = self.abonos.aggregate(total=Sum('monto'))['total'] or 0
        return self.monto_total - total_abonado

    def __str__(self):
        tipo = "Debo" if self.yo_debo else "Me deben"
        return f"{tipo} - {self.persona} (${self.saldo_pendiente})"

    class Meta:
        verbose_name = "Deuda"
        verbose_name_plural = "Deudas"

class Abono(models.Model):
    deuda = models.ForeignKey(Deuda, on_delete=models.CASCADE, related_name='abonos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Abono de ${self.monto} - {self.deuda.persona}"

    class Meta:
        verbose_name = "Abono"
        verbose_name_plural = "Abonos"