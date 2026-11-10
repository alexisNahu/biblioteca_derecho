from django.conf import settings
from django.db import models
from django.utils import timezone

from catalogo.models import Ejemplar


class Prestamo(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        DEVUELTO = "devuelto", "Devuelto"

    ejemplar = models.ForeignKey(Ejemplar, on_delete=models.PROTECT, related_name="prestamos")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="prestamos",
    )
    # Bibliotecario que entregó el ejemplar
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="prestamos_registrados",
        null=True,
        blank=True,
    )
    fecha_prestamo = models.DateTimeField(default=timezone.now)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = "prestamo"
        ordering = ["-fecha_prestamo"]
        constraints = [
            # Un ejemplar no puede estar en dos préstamos activos a la vez
            models.UniqueConstraint(
                fields=["ejemplar"],
                condition=models.Q(estado="activo"),
                name="prestamo_activo_unico_por_ejemplar",
            ),
        ]

    def __str__(self):
        return f"{self.ejemplar} -> {self.usuario}"

    @property
    def vencido(self):
        return self.estado == self.Estado.ACTIVO and timezone.localdate() > self.fecha_vencimiento


class Devolucion(models.Model):
    prestamo = models.OneToOneField(Prestamo, on_delete=models.PROTECT, related_name="devolucion")
    # Bibliotecario que recibió el ejemplar
    recibido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="devoluciones_recibidas",
        null=True,
        blank=True,
    )
    fecha_devolucion = models.DateTimeField(default=timezone.now)
    estado_ejemplar = models.CharField(
        max_length=20,
        choices=Ejemplar.Estado.choices,
        default=Ejemplar.Estado.DISPONIBLE,
        help_text="Estado en que queda el ejemplar después de la devolución",
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = "devolucion"
        verbose_name_plural = "devoluciones"
        ordering = ["-fecha_devolucion"]

    def __str__(self):
        return f"Devolución de {self.prestamo}"

    @property
    def con_atraso(self):
        return timezone.localdate(self.fecha_devolucion) > self.prestamo.fecha_vencimiento
