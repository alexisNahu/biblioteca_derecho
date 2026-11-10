from django.db import migrations

PERMISOS = [
    ("catalogo.gestionar", "Alta, edición y baja de libros, autores, categorías y ejemplares"),
    ("prestamos.gestionar", "Registrar préstamos y devoluciones"),
    ("usuarios.gestionar", "Administrar usuarios y roles"),
]

ROLES = {
    "Administrador": ("Acceso total al sistema", ["catalogo.gestionar", "prestamos.gestionar", "usuarios.gestionar"]),
    "Bibliotecario": ("Gestiona el catálogo, préstamos y devoluciones", ["catalogo.gestionar", "prestamos.gestionar"]),
    "Socio": ("Consulta el catálogo y sus propios préstamos", []),
}


def crear(apps, schema_editor):
    Permiso = apps.get_model("usuarios", "Permiso")
    Rol = apps.get_model("usuarios", "Rol")
    for codigo, descripcion in PERMISOS:
        Permiso.objects.get_or_create(codigo=codigo, defaults={"descripcion": descripcion})
    for nombre, (descripcion, codigos) in ROLES.items():
        rol, _ = Rol.objects.get_or_create(nombre=nombre, defaults={"descripcion": descripcion})
        rol.permisos.set(Permiso.objects.filter(codigo__in=codigos))


def borrar(apps, schema_editor):
    apps.get_model("usuarios", "Rol").objects.filter(nombre__in=ROLES).delete()
    apps.get_model("usuarios", "Permiso").objects.filter(codigo__in=[c for c, _ in PERMISOS]).delete()


class Migration(migrations.Migration):
    dependencies = [("usuarios", "0001_initial")]

    operations = [migrations.RunPython(crear, borrar)]
