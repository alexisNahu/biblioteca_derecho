from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.views import BorrarView, FormularioMixin
from prestamos.models import Prestamo
from usuarios.mixins import PermisoRequeridoMixin
from usuarios.permisos import GESTIONAR_CATALOGO

from .forms import AutorForm, CategoriaForm, EjemplarForm, LibroForm
from .models import Autor, Categoria, Ejemplar, Libro


# Libros

class LibroListView(PermisoRequeridoMixin, ListView):
    model = Libro
    paginate_by = 20

    def get_queryset(self):
        qs = Libro.objects.prefetch_related("autores", "categorias").annotate(
            total_ejemplares=Count("ejemplares", distinct=True),
            disponibles=Count(
                "ejemplares",
                filter=Q(ejemplares__estado=Ejemplar.Estado.DISPONIBLE),
                distinct=True,
            ),
        ).order_by("titulo")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(titulo__icontains=q)
                | Q(isbn__icontains=q)
                | Q(editorial__icontains=q)
                | Q(autores__nombre__icontains=q)
                | Q(autores__apellido__icontains=q)
            ).distinct()
        categoria = self.request.GET.get("categoria")
        if categoria:
            qs = qs.filter(categorias__id=categoria)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorias"] = Categoria.objects.all()
        return context


class LibroDetailView(PermisoRequeridoMixin, DetailView):
    model = Libro

    def get_queryset(self):
        prestamos_activos = Prestamo.objects.filter(estado=Prestamo.Estado.ACTIVO).select_related("usuario")
        ejemplares = Ejemplar.objects.order_by("codigo_barras").prefetch_related(
            Prefetch("prestamos", queryset=prestamos_activos, to_attr="prestamos_activos")
        )
        return Libro.objects.prefetch_related(
            "autores", "categorias", Prefetch("ejemplares", queryset=ejemplares)
        )


class LibroCreateView(PermisoRequeridoMixin, FormularioMixin, CreateView):
    permiso = GESTIONAR_CATALOGO
    model = Libro
    form_class = LibroForm
    titulo = "Nuevo libro"
    cancelar_url = reverse_lazy("catalogo:libro_lista")
    success_message = "Libro «%(titulo)s» creado. Ahora podés agregarle ejemplares."

    def get_success_url(self):
        return reverse("catalogo:libro_detalle", args=[self.object.pk])


class LibroUpdateView(PermisoRequeridoMixin, FormularioMixin, UpdateView):
    permiso = GESTIONAR_CATALOGO
    model = Libro
    form_class = LibroForm
    success_message = "Libro «%(titulo)s» actualizado."

    def get_titulo(self):
        return f"Editar «{self.object}»"

    def get_success_url(self):
        return reverse("catalogo:libro_detalle", args=[self.object.pk])

    def get_cancelar_url(self):
        return self.get_success_url()


class LibroDeleteView(PermisoRequeridoMixin, BorrarView):
    permiso = GESTIONAR_CATALOGO
    model = Libro
    success_url = reverse_lazy("catalogo:libro_lista")

    def get_cancelar_url(self):
        return reverse("catalogo:libro_detalle", args=[self.object.pk])


# Autores

class AutorListView(PermisoRequeridoMixin, ListView):
    model = Autor
    paginate_by = 30

    def get_queryset(self):
        qs = Autor.objects.annotate(total_libros=Count("libros")).order_by("apellido", "nombre")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q))
        return qs


class AutorCreateView(PermisoRequeridoMixin, FormularioMixin, CreateView):
    permiso = GESTIONAR_CATALOGO
    model = Autor
    form_class = AutorForm
    titulo = "Nuevo autor"
    success_url = reverse_lazy("catalogo:autor_lista")
    success_message = "Autor «%(nombre)s %(apellido)s» creado."


class AutorUpdateView(PermisoRequeridoMixin, FormularioMixin, UpdateView):
    permiso = GESTIONAR_CATALOGO
    model = Autor
    form_class = AutorForm
    titulo = "Editar autor"
    success_url = reverse_lazy("catalogo:autor_lista")
    success_message = "Autor «%(nombre)s %(apellido)s» actualizado."


class AutorDeleteView(PermisoRequeridoMixin, BorrarView):
    permiso = GESTIONAR_CATALOGO
    model = Autor
    success_url = reverse_lazy("catalogo:autor_lista")


# Categorías

class CategoriaListView(PermisoRequeridoMixin, ListView):
    model = Categoria
    paginate_by = 30

    def get_queryset(self):
        qs = Categoria.objects.annotate(total_libros=Count("libros")).order_by("nombre")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(nombre__icontains=q)
        return qs


class CategoriaCreateView(PermisoRequeridoMixin, FormularioMixin, CreateView):
    permiso = GESTIONAR_CATALOGO
    model = Categoria
    form_class = CategoriaForm
    titulo = "Nueva categoría"
    success_url = reverse_lazy("catalogo:categoria_lista")
    success_message = "Categoría «%(nombre)s» creada."


class CategoriaUpdateView(PermisoRequeridoMixin, FormularioMixin, UpdateView):
    permiso = GESTIONAR_CATALOGO
    model = Categoria
    form_class = CategoriaForm
    titulo = "Editar categoría"
    success_url = reverse_lazy("catalogo:categoria_lista")
    success_message = "Categoría «%(nombre)s» actualizada."


class CategoriaDeleteView(PermisoRequeridoMixin, BorrarView):
    permiso = GESTIONAR_CATALOGO
    model = Categoria
    success_url = reverse_lazy("catalogo:categoria_lista")


# Ejemplares

class EjemplarCreateView(PermisoRequeridoMixin, FormularioMixin, CreateView):
    permiso = GESTIONAR_CATALOGO
    model = Ejemplar
    form_class = EjemplarForm
    success_message = "Ejemplar %(codigo_barras)s agregado."

    def dispatch(self, request, *args, **kwargs):
        self.libro = get_object_or_404(Libro, pk=kwargs["libro_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_titulo(self):
        return f"Nuevo ejemplar de «{self.libro}»"

    def form_valid(self, form):
        form.instance.libro = self.libro
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("catalogo:libro_detalle", args=[self.libro.pk])

    def get_cancelar_url(self):
        return self.get_success_url()


class EjemplarUpdateView(PermisoRequeridoMixin, FormularioMixin, UpdateView):
    permiso = GESTIONAR_CATALOGO
    model = Ejemplar
    form_class = EjemplarForm
    success_message = "Ejemplar %(codigo_barras)s actualizado."

    def get_titulo(self):
        return f"Editar ejemplar {self.object.codigo_barras}"

    def get_success_url(self):
        return reverse("catalogo:libro_detalle", args=[self.object.libro_id])

    def get_cancelar_url(self):
        return self.get_success_url()


class EjemplarDeleteView(PermisoRequeridoMixin, BorrarView):
    permiso = GESTIONAR_CATALOGO
    model = Ejemplar

    def get_success_url(self):
        return reverse("catalogo:libro_detalle", args=[self.object.libro_id])
