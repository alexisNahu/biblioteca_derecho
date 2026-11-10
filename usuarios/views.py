from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, ListView, UpdateView

from core.views import BorrarView, FormularioMixin

from .forms import AsignarPasswordForm, CambiarPasswordForm, RolForm, UsuarioCrearForm, UsuarioForm
from .mixins import PermisoRequeridoMixin
from .models import Rol, Usuario
from .permisos import GESTIONAR_USUARIOS


class UsuarioListView(PermisoRequeridoMixin, ListView):
    permiso = GESTIONAR_USUARIOS
    model = Usuario
    paginate_by = 25

    def get_queryset(self):
        qs = Usuario.objects.prefetch_related("roles").order_by("apellido", "nombre")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(email__icontains=q))
        return qs


class UsuarioCreateView(PermisoRequeridoMixin, FormularioMixin, CreateView):
    permiso = GESTIONAR_USUARIOS
    model = Usuario
    form_class = UsuarioCrearForm
    titulo = "Nuevo usuario"
    success_url = reverse_lazy("usuarios:lista")
    success_message = "Usuario %(email)s creado."

    def get_initial(self):
        # Por defecto los usuarios nuevos son socios
        return {"roles": Rol.objects.filter(nombre="Socio")}


class UsuarioUpdateView(PermisoRequeridoMixin, FormularioMixin, UpdateView):
    permiso = GESTIONAR_USUARIOS
    model = Usuario
    form_class = UsuarioForm
    success_url = reverse_lazy("usuarios:lista")
    success_message = "Usuario %(email)s actualizado."

    def get_titulo(self):
        return f"Editar usuario {self.object.nombre_completo}"

    def form_valid(self, form):
        # Evita que un administrador se bloquee a sí mismo
        if self.object.pk == self.request.user.pk:
            if not form.cleaned_data["activo"]:
                form.add_error("activo", "No podés desactivar tu propio usuario.")
                return self.form_invalid(form)
            roles = form.cleaned_data["roles"]
            if not roles.filter(permisos__codigo=GESTIONAR_USUARIOS).exists():
                form.add_error("roles", "No podés quitarte el permiso de administrar usuarios.")
                return self.form_invalid(form)
        return super().form_valid(form)


class UsuarioPasswordView(PermisoRequeridoMixin, FormView):
    permiso = GESTIONAR_USUARIOS
    form_class = AsignarPasswordForm
    template_name = "core/form.html"

    def dispatch(self, request, *args, **kwargs):
        self.usuario = get_object_or_404(Usuario, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.usuario
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = f"Cambiar contraseña de {self.usuario.nombre_completo}"
        context["cancelar_url"] = reverse_lazy("usuarios:lista")
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f"Contraseña de {self.usuario.email} actualizada.")
        return redirect("usuarios:lista")


class RolListView(PermisoRequeridoMixin, ListView):
    permiso = GESTIONAR_USUARIOS
    model = Rol

    def get_queryset(self):
        return Rol.objects.prefetch_related("permisos").annotate(total_usuarios=Count("usuarios")).order_by("nombre")


class RolCreateView(PermisoRequeridoMixin, FormularioMixin, CreateView):
    permiso = GESTIONAR_USUARIOS
    model = Rol
    form_class = RolForm
    titulo = "Nuevo rol"
    success_url = reverse_lazy("usuarios:rol_lista")
    success_message = "Rol «%(nombre)s» creado."


class RolUpdateView(PermisoRequeridoMixin, FormularioMixin, UpdateView):
    permiso = GESTIONAR_USUARIOS
    model = Rol
    form_class = RolForm
    titulo = "Editar rol"
    success_url = reverse_lazy("usuarios:rol_lista")
    success_message = "Rol «%(nombre)s» actualizado."


class RolDeleteView(PermisoRequeridoMixin, BorrarView):
    permiso = GESTIONAR_USUARIOS
    model = Rol
    success_url = reverse_lazy("usuarios:rol_lista")

    def form_valid(self, form):
        if self.object.usuarios.exists():
            messages.error(self.request, f"No se puede borrar «{self.object}» porque tiene usuarios asignados.")
            return redirect(self.success_url)
        return super().form_valid(form)


class MiPasswordView(PasswordChangeView):
    form_class = CambiarPasswordForm
    template_name = "core/form.html"
    success_url = reverse_lazy("inicio")
    extra_context = {"titulo": "Cambiar mi contraseña", "cancelar_url": reverse_lazy("inicio")}

    def form_valid(self, form):
        messages.success(self.request, "Tu contraseña fue actualizada.")
        return super().form_valid(form)
