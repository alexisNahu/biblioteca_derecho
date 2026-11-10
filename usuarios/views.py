from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

from .forms import CambiarPasswordForm


class MiPasswordView(PasswordChangeView):
    form_class = CambiarPasswordForm
    template_name = "core/form.html"
    success_url = reverse_lazy("inicio")
    extra_context = {"titulo": "Cambiar mi contraseña", "cancelar_url": reverse_lazy("inicio")}

    def form_valid(self, form):
        messages.success(self.request, "Tu contraseña fue actualizada.")
        return super().form_valid(form)
