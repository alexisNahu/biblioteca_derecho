from django import forms
from django.utils import timezone

from core.forms import BootstrapFormMixin

from .models import Autor, Categoria, Ejemplar, Libro


class LibroForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Libro
        fields = ["titulo", "isbn", "anio_publicacion", "editorial", "codigo_dewey", "autores", "categorias"]
        labels = {
            "titulo": "Título",
            "isbn": "ISBN",
            "anio_publicacion": "Año de publicación",
            "codigo_dewey": "Código Dewey",
        }
        widgets = {
            "autores": forms.SelectMultiple(attrs={"size": 6}),
            "categorias": forms.SelectMultiple(attrs={"size": 6}),
        }
        help_texts = {
            "autores": "Mantené Ctrl (o Cmd) para elegir varios.",
            "categorias": "Mantené Ctrl (o Cmd) para elegir varias.",
        }

    def clean_anio_publicacion(self):
        anio = self.cleaned_data["anio_publicacion"]
        if anio and anio > timezone.localdate().year:
            raise forms.ValidationError("El año de publicación no puede ser futuro.")
        return anio


class AutorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Autor
        fields = ["nombre", "apellido"]


class CategoriaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion"]
        labels = {"descripcion": "Descripción"}


class EjemplarForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ejemplar
        fields = ["codigo_barras", "estado", "ubicacion"]
        labels = {"codigo_barras": "Código de barras", "ubicacion": "Ubicación"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estado = self.fields["estado"]
        if self.instance.estado == Ejemplar.Estado.PRESTADO:
            # Solo una devolución puede sacar al ejemplar de "prestado"
            estado.disabled = True
            estado.help_text = "El ejemplar está prestado; su estado cambia al registrar la devolución."
        else:
            # "Prestado" lo asigna el proceso de préstamo, no se elige a mano
            estado.choices = [c for c in Ejemplar.Estado.choices if c[0] != Ejemplar.Estado.PRESTADO]
