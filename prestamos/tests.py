from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Ejemplar, Libro
from usuarios.models import Rol, Usuario

from . import services
from .models import Prestamo


class Datos(TestCase):
    def setUp(self):
        self.libro = Libro.objects.create(titulo="Rayuela")
        self.ejemplar = Ejemplar.objects.create(libro=self.libro, codigo_barras="0001")
        self.socio = Usuario.objects.create_user("socio@test.com", "clave-segura-123", nombre="Ana", apellido="Pérez")
        self.socio.roles.add(Rol.objects.get(nombre="Socio"))
        self.biblio = Usuario.objects.create_user("biblio@test.com", "clave-segura-123", nombre="Juan", apellido="Gómez")
        self.biblio.roles.add(Rol.objects.get(nombre="Bibliotecario"))
        self.vence = timezone.localdate() + timedelta(days=14)


class ServiciosTests(Datos):
    def test_prestar_y_devolver(self):
        prestamo = services.prestar(self.ejemplar, self.socio, self.vence, registrado_por=self.biblio)
        self.ejemplar.refresh_from_db()
        self.assertEqual(self.ejemplar.estado, Ejemplar.Estado.PRESTADO)

        services.devolver(prestamo, recibido_por=self.biblio, estado_ejemplar=Ejemplar.Estado.EN_REPARACION)
        prestamo.refresh_from_db()
        self.ejemplar.refresh_from_db()
        self.assertEqual(prestamo.estado, Prestamo.Estado.DEVUELTO)
        self.assertEqual(self.ejemplar.estado, Ejemplar.Estado.EN_REPARACION)
        self.assertFalse(prestamo.devolucion.con_atraso)

    def test_no_presta_ejemplar_no_disponible(self):
        services.prestar(self.ejemplar, self.socio, self.vence)
        with self.assertRaises(ValidationError):
            services.prestar(self.ejemplar, self.biblio, self.vence)

    def test_no_devuelve_dos_veces(self):
        prestamo = services.prestar(self.ejemplar, self.socio, self.vence)
        services.devolver(prestamo)
        with self.assertRaises(ValidationError):
            services.devolver(prestamo)

    def test_no_presta_a_usuario_inactivo(self):
        self.socio.activo = False
        self.socio.save()
        with self.assertRaises(ValidationError):
            services.prestar(self.ejemplar, self.socio, self.vence)

    @override_settings(PRESTAMO_MAXIMO_POR_USUARIO=1)
    def test_maximo_de_prestamos(self):
        otro = Ejemplar.objects.create(libro=self.libro, codigo_barras="0002")
        services.prestar(self.ejemplar, self.socio, self.vence)
        with self.assertRaises(ValidationError):
            services.prestar(otro, self.socio, self.vence)

    def test_no_presta_con_vencidos(self):
        otro = Ejemplar.objects.create(libro=self.libro, codigo_barras="0002")
        prestamo = services.prestar(self.ejemplar, self.socio, self.vence)
        Prestamo.objects.filter(pk=prestamo.pk).update(fecha_vencimiento=timezone.localdate() - timedelta(days=1))
        with self.assertRaises(ValidationError):
            services.prestar(otro, self.socio, self.vence)


class VistasTests(Datos):
    def test_flujo_completo_desde_las_paginas(self):
        self.client.force_login(self.biblio)
        r = self.client.post(reverse("prestamos:nuevo"), {
            "ejemplar": "0001", "usuario": self.socio.pk, "fecha_vencimiento": self.vence.isoformat(),
        })
        prestamo = Prestamo.objects.get()
        self.assertRedirects(r, reverse("prestamos:detalle", args=[prestamo.pk]))

        r = self.client.post(reverse("prestamos:buscar_devolucion"), {"ejemplar": "0001"})
        self.assertRedirects(r, reverse("prestamos:devolver", args=[prestamo.pk]))

        r = self.client.post(reverse("prestamos:devolver", args=[prestamo.pk]), {"estado_ejemplar": "disponible"})
        self.assertRedirects(r, reverse("prestamos:detalle", args=[prestamo.pk]))
        prestamo.refresh_from_db()
        self.assertEqual(prestamo.estado, Prestamo.Estado.DEVUELTO)

    def test_prestar_ejemplar_ocupado_muestra_error(self):
        services.prestar(self.ejemplar, self.socio, self.vence)
        self.client.force_login(self.biblio)
        r = self.client.post(reverse("prestamos:nuevo"), {
            "ejemplar": "0001", "usuario": self.biblio.pk, "fecha_vencimiento": self.vence.isoformat(),
        })
        self.assertContains(r, "no está disponible")

    def test_socio_no_puede_gestionar_prestamos(self):
        self.client.force_login(self.socio)
        self.assertEqual(self.client.get(reverse("prestamos:nuevo")).status_code, 403)
        self.assertEqual(self.client.get(reverse("prestamos:lista")).status_code, 403)
        self.assertEqual(self.client.get(reverse("prestamos:mis_prestamos")).status_code, 200)

    def test_socio_solo_ve_sus_prestamos(self):
        ajeno = services.prestar(self.ejemplar, self.biblio, self.vence)
        self.client.force_login(self.socio)
        self.assertEqual(self.client.get(reverse("prestamos:detalle", args=[ajeno.pk])).status_code, 404)

    def test_paginas_cargan(self):
        prestamo = services.prestar(self.ejemplar, self.socio, self.vence)
        admin = Usuario.objects.create_superuser("admin@test.com", "clave-segura-123", nombre="Ad", apellido="Min")
        self.client.force_login(admin)
        urls = [
            reverse("inicio"),
            reverse("catalogo:libro_lista") + "?q=ray",
            reverse("catalogo:libro_detalle", args=[self.libro.pk]),
            reverse("catalogo:libro_nuevo"),
            reverse("catalogo:libro_editar", args=[self.libro.pk]),
            reverse("catalogo:ejemplar_nuevo", args=[self.libro.pk]),
            reverse("catalogo:ejemplar_editar", args=[self.ejemplar.pk]),
            reverse("catalogo:autor_lista"),
            reverse("catalogo:autor_nuevo"),
            reverse("catalogo:categoria_lista"),
            reverse("catalogo:categoria_nueva"),
            reverse("prestamos:lista") + "?estado=todos",
            reverse("prestamos:detalle", args=[prestamo.pk]),
            reverse("prestamos:devolver", args=[prestamo.pk]),
            reverse("prestamos:mis_prestamos"),
            reverse("usuarios:lista"),
            reverse("usuarios:nuevo"),
            reverse("usuarios:editar", args=[self.socio.pk]),
            reverse("usuarios:password", args=[self.socio.pk]),
            reverse("usuarios:rol_lista"),
            reverse("usuarios:rol_nuevo"),
            reverse("password_change"),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_borrar_libro_con_ejemplares_avisa(self):
        self.client.force_login(self.biblio)
        r = self.client.post(reverse("catalogo:libro_borrar", args=[self.libro.pk]), follow=True)
        self.assertContains(r, "tiene registros asociados")
        self.assertTrue(Libro.objects.filter(pk=self.libro.pk).exists())
