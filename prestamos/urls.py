from django.urls import path

from . import views

app_name = "prestamos"

urlpatterns = [
    path("", views.PrestamoListView.as_view(), name="lista"),
    path("mis-prestamos/", views.MisPrestamosView.as_view(), name="mis_prestamos"),
    path("nuevo/", views.PrestamoCreateView.as_view(), name="nuevo"),
    path("<int:pk>/", views.PrestamoDetailView.as_view(), name="detalle"),
]
