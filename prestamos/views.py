from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView

from usuarios.mixins import PermisoRequeridoMixin
from usuarios.permisos import GESTIONAR_PRESTAMOS

from . import services
from .forms import BuscarDevolucionForm, DevolucionForm, PrestamoForm
from .models import Prestamo


class PrestamoListView(PermisoRequeridoMixin, ListView):
    permiso = GESTIONAR_PRESTAMOS
    model = Prestamo
    paginate_by = 25

    FILTROS = [("activos", "Activos"), ("vencidos", "Vencidos"), ("devueltos", "Devueltos"), ("todos", "Todos")]

    def get_filtro(self):
        filtro = self.request.GET.get("estado", "activos")
        return filtro if filtro in dict(self.FILTROS) else "activos"

    def get_queryset(self):
        qs = Prestamo.objects.select_related("ejemplar__libro", "usuario", "devolucion")
        filtro = self.get_filtro()
        hoy = timezone.localdate()
        if filtro == "activos":
            qs = qs.filter(estado=Prestamo.Estado.ACTIVO)
        elif filtro == "vencidos":
            qs = qs.filter(estado=Prestamo.Estado.ACTIVO, fecha_vencimiento__lt=hoy)
        elif filtro == "devueltos":
            qs = qs.filter(estado=Prestamo.Estado.DEVUELTO)

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(usuario__nombre__icontains=q)
                | Q(usuario__apellido__icontains=q)
                | Q(usuario__email__icontains=q)
                | Q(ejemplar__codigo_barras__icontains=q)
                | Q(ejemplar__libro__titulo__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filtros"] = self.FILTROS
        context["filtro"] = self.get_filtro()
        return context


class MisPrestamosView(PermisoRequeridoMixin, ListView):
    template_name = "prestamos/mis_prestamos.html"
    paginate_by = 25

    def get_queryset(self):
        return Prestamo.objects.filter(usuario=self.request.user).select_related("ejemplar__libro", "devolucion")


class PrestamoDetailView(PermisoRequeridoMixin, DetailView):
    model = Prestamo

    def get_queryset(self):
        qs = Prestamo.objects.select_related(
            "ejemplar__libro", "usuario", "registrado_por", "devolucion__recibido_por"
        )
        # Sin permiso de gestión, cada usuario solo ve sus propios préstamos
        if not self.request.user.tiene_permiso(GESTIONAR_PRESTAMOS):
            qs = qs.filter(usuario=self.request.user)
        return qs


class PrestamoCreateView(PermisoRequeridoMixin, FormView):
    permiso = GESTIONAR_PRESTAMOS
    form_class = PrestamoForm
    template_name = "prestamos/prestamo_form.html"

    def get_initial(self):
        return {
            "ejemplar": self.request.GET.get("ejemplar", ""),
            "fecha_vencimiento": timezone.localdate() + timedelta(days=settings.PRESTAMO_DIAS),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dias"] = settings.PRESTAMO_DIAS
        context["maximo"] = settings.PRESTAMO_MAXIMO_POR_USUARIO
        return context

    def form_valid(self, form):
        try:
            self.prestamo = services.prestar(registrado_por=self.request.user, **form.cleaned_data)
        except ValidationError as e:
            for mensaje in e.messages:
                form.add_error(None, mensaje)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Préstamo registrado: «{self.prestamo.ejemplar.libro}» a {self.prestamo.usuario.nombre_completo}, "
            f"vence el {self.prestamo.fecha_vencimiento:%d/%m/%Y}.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("prestamos:detalle", args=[self.prestamo.pk])


class BuscarDevolucionView(PermisoRequeridoMixin, FormView):
    """Paso previo a la devolución: se escanea el ejemplar y se busca su préstamo activo."""

    permiso = GESTIONAR_PRESTAMOS
    form_class = BuscarDevolucionForm
    template_name = "prestamos/buscar_devolucion.html"

    def form_valid(self, form):
        ejemplar = form.cleaned_data["ejemplar"]
        prestamo = ejemplar.prestamos.filter(estado=Prestamo.Estado.ACTIVO).first()
        if prestamo is None:
            form.add_error("ejemplar", f"El ejemplar {ejemplar.codigo_barras} no tiene un préstamo activo.")
            return self.form_invalid(form)
        return redirect("prestamos:devolver", pk=prestamo.pk)


class DevolucionCreateView(PermisoRequeridoMixin, FormView):
    permiso = GESTIONAR_PRESTAMOS
    form_class = DevolucionForm
    template_name = "prestamos/devolucion_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.prestamo = get_object_or_404(
            Prestamo.objects.select_related("ejemplar__libro", "usuario"), pk=kwargs["pk"]
        )
        if request.user.is_authenticated and self.prestamo.estado != Prestamo.Estado.ACTIVO:
            messages.warning(request, "Este préstamo ya fue devuelto.")
            return redirect("prestamos:detalle", pk=self.prestamo.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["prestamo"] = self.prestamo
        context["hoy"] = timezone.localdate()
        return context

    def form_valid(self, form):
        try:
            services.devolver(self.prestamo, recibido_por=self.request.user, **form.cleaned_data)
        except ValidationError as e:
            for mensaje in e.messages:
                form.add_error(None, mensaje)
            return self.form_invalid(form)
        mensaje = f"Devolución registrada: «{self.prestamo.ejemplar.libro}»."
        if self.prestamo.vencido:
            dias = (timezone.localdate() - self.prestamo.fecha_vencimiento).days
            messages.warning(self.request, f"{mensaje} Se devolvió con {dias} día(s) de atraso.")
        else:
            messages.success(self.request, mensaje)
        return redirect("prestamos:detalle", pk=self.prestamo.pk)
