from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class PermisoRequeridoMixin(LoginRequiredMixin):
    """Exige login y, si se define `permiso`, que alguno de los roles del usuario lo tenga."""

    permiso = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.permiso and not request.user.tiene_permiso(self.permiso):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
