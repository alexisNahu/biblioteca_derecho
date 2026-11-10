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
]
