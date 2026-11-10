from django.urls import include, path

urlpatterns = [
    path('', include('core.urls')),
    path('cuentas/', include('usuarios.urls_cuentas')),
    path('prestamos/', include('prestamos.urls')),
    path('usuarios/', include('usuarios.urls')),
]
