from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import DeleteView

from catalogo.models import Ejemplar, Libro
from prestamos.models import Prestamo
from usuarios.permisos import GESTIONAR_PRESTAMOS


class FormularioMixin(SuccessMessageMixin):
    """Vistas de alta/edición que usan la plantilla genérica core/form.html."""

    template_name = "core/form.html"
    titulo = ""
    cancelar_url = None

    def get_titulo(self):
        return self.titulo

    def get_cancelar_url(self):
        return self.cancelar_url or self.success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = self.get_titulo()
        context["cancelar_url"] = self.get_cancelar_url()
        return context


class BorrarView(DeleteView):
    """Confirmación de borrado que avisa en lugar de fallar si hay registros asociados (PROTECT)."""

    template_name = "core/confirmar_borrado.html"

    def get_cancelar_url(self):
        return self.get_success_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancelar_url"] = self.get_cancelar_url()
        return context

    def form_valid(self, form):
        nombre = str(self.object)
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, f"No se puede borrar «{nombre}» porque tiene registros asociados.")
            return redirect(self.get_cancelar_url())
        messages.success(self.request, f"«{nombre}» fue borrado.")
        return response


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
