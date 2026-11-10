from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from core.forms import BootstrapFormMixin


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class CambiarPasswordForm(BootstrapFormMixin, PasswordChangeForm):
    pass
