from django import forms

from catalogo.models import Ejemplar
from core.forms import BootstrapFormMixin
from usuarios.models import Usuario

from .models import Devolucion


class CodigoBarrasField(forms.CharField):
    """Recibe un código de barras y devuelve el Ejemplar correspondiente."""

    def clean(self, value):
        codigo = super().clean(value).strip()
        try:
            return Ejemplar.objects.select_related("libro").get(codigo_barras=codigo)
        except Ejemplar.DoesNotExist:
            raise forms.ValidationError(f"No existe un ejemplar con el código «{codigo}».")


class PrestamoForm(BootstrapFormMixin, forms.Form):
    ejemplar = CodigoBarrasField(
        label="Código de barras del ejemplar",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "off"}),
    )
    usuario = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(activo=True).order_by("apellido", "nombre"),
        label="Usuario",
    )
    fecha_vencimiento = forms.DateField(label="Fecha de vencimiento", widget=forms.DateInput(attrs={"type": "date"}))
    observaciones = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)


class BuscarDevolucionForm(BootstrapFormMixin, forms.Form):
    ejemplar = CodigoBarrasField(
        label="Código de barras del ejemplar",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "off"}),
    )


class DevolucionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Devolucion
        fields = ["estado_ejemplar", "observaciones"]
        labels = {"estado_ejemplar": "Estado del ejemplar"}
        widgets = {"observaciones": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estado_ejemplar"].choices = [
            c for c in Ejemplar.Estado.choices if c[0] != Ejemplar.Estado.PRESTADO
        ]
