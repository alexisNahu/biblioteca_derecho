from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("libros/", views.LibroListView.as_view(), name="libro_lista"),
    path("libros/nuevo/", views.LibroCreateView.as_view(), name="libro_nuevo"),
    path("libros/<int:pk>/", views.LibroDetailView.as_view(), name="libro_detalle"),
    path("libros/<int:pk>/editar/", views.LibroUpdateView.as_view(), name="libro_editar"),
    path("libros/<int:pk>/borrar/", views.LibroDeleteView.as_view(), name="libro_borrar"),
    path("libros/<int:libro_pk>/ejemplares/nuevo/", views.EjemplarCreateView.as_view(), name="ejemplar_nuevo"),
    path("ejemplares/<int:pk>/editar/", views.EjemplarUpdateView.as_view(), name="ejemplar_editar"),
    path("ejemplares/<int:pk>/borrar/", views.EjemplarDeleteView.as_view(), name="ejemplar_borrar"),
    path("autores/", views.AutorListView.as_view(), name="autor_lista"),
    path("autores/nuevo/", views.AutorCreateView.as_view(), name="autor_nuevo"),
    path("autores/<int:pk>/editar/", views.AutorUpdateView.as_view(), name="autor_editar"),
    path("autores/<int:pk>/borrar/", views.AutorDeleteView.as_view(), name="autor_borrar"),
    path("categorias/", views.CategoriaListView.as_view(), name="categoria_lista"),
    path("categorias/nueva/", views.CategoriaCreateView.as_view(), name="categoria_nueva"),
    path("categorias/<int:pk>/editar/", views.CategoriaUpdateView.as_view(), name="categoria_editar"),
    path("categorias/<int:pk>/borrar/", views.CategoriaDeleteView.as_view(), name="categoria_borrar"),
]
