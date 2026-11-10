def permisos(request):
    """Expone los códigos de permiso del usuario para mostrar u ocultar opciones en las plantillas."""
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return {"permisos": user.codigos_permisos()}
    return {"permisos": set()}
