from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from catalogo.models import Ejemplar, Libro
from prestamos.models import Prestamo
from usuarios.permisos import GESTIONAR_PRESTAMOS


@login_required
def inicio(request):
    hoy = timezone.localdate()
    context = {
        "mis_prestamos": Prestamo.objects.filter(usuario=request.user, estado=Prestamo.Estado.ACTIVO)
        .select_related("ejemplar__libro")
        .order_by("fecha_vencimiento"),
        "hoy": hoy,
    }
    if request.user.tiene_permiso(GESTIONAR_PRESTAMOS):
        activos = Prestamo.objects.filter(estado=Prestamo.Estado.ACTIVO)
        context.update(
            total_libros=Libro.objects.count(),
            ejemplares_disponibles=Ejemplar.objects.filter(estado=Ejemplar.Estado.DISPONIBLE).count(),
            prestamos_activos=activos.count(),
            vencidos=activos.filter(fecha_vencimiento__lt=hoy)
            .select_related("ejemplar__libro", "usuario")
            .order_by("fecha_vencimiento")[:10],
            total_vencidos=activos.filter(fecha_vencimiento__lt=hoy).count(),
        )
    return render(request, "core/inicio.html", context)
