from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.UsuarioListView.as_view(), name="lista"),
    path("nuevo/", views.UsuarioCreateView.as_view(), name="nuevo"),
    path("<int:pk>/editar/", views.UsuarioUpdateView.as_view(), name="editar"),
    path("<int:pk>/password/", views.UsuarioPasswordView.as_view(), name="password"),
    path("roles/", views.RolListView.as_view(), name="rol_lista"),
    path("roles/nuevo/", views.RolCreateView.as_view(), name="rol_nuevo"),
    path("roles/<int:pk>/editar/", views.RolUpdateView.as_view(), name="rol_editar"),
    path("roles/<int:pk>/borrar/", views.RolDeleteView.as_view(), name="rol_borrar"),
]
