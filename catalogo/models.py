from django.db import models


class Autor(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)

    class Meta:
        db_table = "autor"
        verbose_name_plural = "autores"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "categoria"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Libro(models.Model):
    titulo = models.CharField(max_length=255)
    isbn = models.CharField(max_length=17, blank=True)
    anio_publicacion = models.PositiveSmallIntegerField(null=True, blank=True)
    editorial = models.CharField(max_length=150, blank=True)
    codigo_dewey = models.CharField(max_length=20, blank=True)
    autores = models.ManyToManyField(
        Autor,
        related_name="libros",
        blank=True,
        db_table="libro_autor",
    )
    categorias = models.ManyToManyField(
        Categoria,
        related_name="libros",
        blank=True,
        db_table="libro_categoria",
    )

    class Meta:
        db_table = "libro"
        ordering = ["titulo"]

    def __str__(self):
        return self.titulo


class Ejemplar(models.Model):
    class Estado(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        PRESTADO = "prestado", "Prestado"
        EN_REPARACION = "en_reparacion", "En reparación"
        BAJA = "baja", "De baja"

    libro = models.ForeignKey(Libro, on_delete=models.PROTECT, related_name="ejemplares")
    codigo_barras = models.CharField(max_length=50, unique=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.DISPONIBLE)
    ubicacion = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "ejemplar"
        verbose_name_plural = "ejemplares"

    def __str__(self):
        return f"{self.libro} [{self.codigo_barras}]"
