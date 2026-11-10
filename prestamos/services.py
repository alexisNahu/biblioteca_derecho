"""Procesos de préstamo y devolución.

Cada operación corre en una transacción y bloquea las filas que modifica,
para que dos bibliotecarios no presten el mismo ejemplar al mismo tiempo.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from catalogo.models import Ejemplar

from .models import Devolucion, Prestamo


@transaction.atomic
def prestar(ejemplar, usuario, fecha_vencimiento, registrado_por=None, observaciones=""):
    ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar.pk)

    if ejemplar.estado != Ejemplar.Estado.DISPONIBLE:
        raise ValidationError(f"El ejemplar {ejemplar.codigo_barras} no está disponible ({ejemplar.get_estado_display().lower()}).")
    if not usuario.activo:
        raise ValidationError(f"El usuario {usuario.nombre_completo} está inactivo.")
    if fecha_vencimiento < timezone.localdate():
        raise ValidationError("La fecha de vencimiento no puede ser anterior a hoy.")

    activos = Prestamo.objects.filter(usuario=usuario, estado=Prestamo.Estado.ACTIVO)
    if activos.count() >= settings.PRESTAMO_MAXIMO_POR_USUARIO:
        raise ValidationError(
            f"{usuario.nombre_completo} ya tiene {settings.PRESTAMO_MAXIMO_POR_USUARIO} préstamos activos, el máximo permitido."
        )
    if activos.filter(fecha_vencimiento__lt=timezone.localdate()).exists():
        raise ValidationError(f"{usuario.nombre_completo} tiene préstamos vencidos sin devolver.")

    prestamo = Prestamo.objects.create(
        ejemplar=ejemplar,
        usuario=usuario,
        registrado_por=registrado_por,
        fecha_vencimiento=fecha_vencimiento,
        observaciones=observaciones,
    )
    ejemplar.estado = Ejemplar.Estado.PRESTADO
    ejemplar.save(update_fields=["estado"])
    return prestamo
