from django.core.management.base import BaseCommand

from catalogo.models import Ejemplar, Libro
from usuarios.models import Rol, Usuario

LIBROS = [
    ("Rayuela", ["RAY-001", "RAY-002"]),
    ("Cien años de soledad", ["CAS-001", "CAS-002"]),
    ("Ficciones", ["FIC-001"]),
    ("El túnel", ["TUN-001"]),
]

USUARIOS = [
    ("bibliotecario@demo.com", "Juan", "Gómez", "Bibliotecario"),
    ("socio@demo.com", "Ana", "Pérez", "Socio"),
]

PASSWORD = "demo1234"


class Command(BaseCommand):
    help = "Carga libros, ejemplares y usuarios de prueba para probar préstamos y devoluciones."

    def handle(self, *args, **options):
        for titulo, codigos in LIBROS:
            libro, _ = Libro.objects.get_or_create(titulo=titulo)
            for codigo in codigos:
                Ejemplar.objects.get_or_create(codigo_barras=codigo, defaults={"libro": libro})

        for email, nombre, apellido, rol in USUARIOS:
            if not Usuario.objects.filter(email=email).exists():
                usuario = Usuario.objects.create_user(email, PASSWORD, nombre=nombre, apellido=apellido)
                usuario.roles.add(Rol.objects.get(nombre=rol))

        self.stdout.write(self.style.SUCCESS(
            f"Datos cargados. Usuarios: {', '.join(u[0] for u in USUARIOS)} (contraseña: {PASSWORD})"
        ))
