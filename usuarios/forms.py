from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password

from core.forms import BootstrapFormMixin

from .models import Rol, Usuario


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class CambiarPasswordForm(BootstrapFormMixin, PasswordChangeForm):
    pass


class AsignarPasswordForm(BootstrapFormMixin, SetPasswordForm):
    pass


class UsuarioForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["nombre", "apellido", "email", "activo", "roles"]
        widgets = {"roles": forms.CheckboxSelectMultiple}
        help_texts = {"activo": "Un usuario inactivo no puede iniciar sesión ni recibir préstamos."}


class UsuarioCrearForm(UsuarioForm):
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(label="Repetir contraseña", widget=forms.PasswordInput, strip=False)

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        elif p1:
            try:
                validate_password(p1, self.instance)
            except forms.ValidationError as e:
                self.add_error("password1", e)
        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
            self.save_m2m()
        return usuario


class RolForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Rol
        fields = ["nombre", "descripcion", "permisos"]
        labels = {"descripcion": "Descripción"}
        widgets = {"permisos": forms.CheckboxSelectMultiple}
