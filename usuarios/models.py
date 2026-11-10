from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class Permiso(models.Model):
    codigo = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "permiso"
        ordering = ["codigo"]

    def __str__(self):
        return self.codigo


class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    permisos = models.ManyToManyField(
        Permiso,
        related_name="roles",
        blank=True,
        db_table="rol_permiso",
    )

    class Meta:
        db_table = "rol"
        verbose_name_plural = "roles"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        usuario = self.model(email=self.normalize_email(email), **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        usuario = self.create_user(email, password, **extra_fields)
        rol, _ = Rol.objects.get_or_create(nombre="Administrador")
        rol.permisos.set(Permiso.objects.all())
        usuario.roles.add(rol)
        return usuario


class Usuario(AbstractBaseUser):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    # AbstractBaseUser define "password"; se guarda en la columna password_hash
    password = models.CharField(max_length=128, db_column="password_hash")
    activo = models.BooleanField(default=True)
    roles = models.ManyToManyField(
        Rol,
        related_name="usuarios",
        blank=True,
        db_table="usuario_rol",
    )

    # AbstractBaseUser incluye last_login; el diagrama no lo tiene
    last_login = None

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nombre", "apellido"]

    class Meta:
        db_table = "usuario"

    def __str__(self):
        return f"{self.nombre} {self.apellido} <{self.email}>"

    @property
    def is_active(self):
        return self.activo

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def codigos_permisos(self):
        # Se cachea en la instancia: se consulta varias veces por request
        if not hasattr(self, "_codigos_permisos"):
            self._codigos_permisos = set(
                Permiso.objects.filter(roles__usuarios=self).values_list("codigo", flat=True)
            )
        return self._codigos_permisos

    def tiene_permiso(self, codigo):
        return codigo in self.codigos_permisos()
