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


@transaction.atomic
def devolver(prestamo, recibido_por=None, estado_ejemplar=Ejemplar.Estado.DISPONIBLE, observaciones=""):
    prestamo = Prestamo.objects.select_for_update().select_related("ejemplar").get(pk=prestamo.pk)

    if prestamo.estado != Prestamo.Estado.ACTIVO:
        raise ValidationError("Este préstamo ya fue devuelto.")
    if estado_ejemplar == Ejemplar.Estado.PRESTADO:
        raise ValidationError("El ejemplar devuelto no puede quedar en estado «prestado».")

    devolucion = Devolucion.objects.create(
        prestamo=prestamo,
        recibido_por=recibido_por,
        estado_ejemplar=estado_ejemplar,
        observaciones=observaciones,
    )
    prestamo.estado = Prestamo.Estado.DEVUELTO
    prestamo.save(update_fields=["estado"])

    ejemplar = prestamo.ejemplar
    ejemplar.estado = estado_ejemplar
    ejemplar.save(update_fields=["estado"])
    return devolucion
