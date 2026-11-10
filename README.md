# Biblioteca Jonas

Sistema web de gestión de biblioteca: catálogo de libros y ejemplares, préstamos, devoluciones y administración de usuarios con roles y permisos.

**Stack:** Python 3.14 · Django 5.2 · PostgreSQL (psycopg 3) · Bootstrap 5.3 (CDN) · python-dotenv

---

## Puesta en marcha

### Requisitos
- Python 3.14
- PostgreSQL corriendo y una base creada (por defecto `biblioteca`)

### Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # completar los valores (ver abajo)
python manage.py migrate     # crea tablas, permisos y roles iniciales
python manage.py createsuperuser   # pide email, nombre, apellido y contraseña
python manage.py runserver
```

La aplicación queda en http://127.0.0.1:8000/ y se ingresa con **email** y contraseña.

### Variables de entorno (`.env`)

| Variable | Default | Descripción |
|---|---|---|
| `DJANGO_SECRET_KEY` | `django-insecure-...` | Clave secreta de Django. Cambiar en producción. |
| `DJANGO_DEBUG` | `True` | `True` / `False` |
| `DB_NAME` | `biblioteca` | Nombre de la base PostgreSQL |
| `DB_USER` | `postgres` | Usuario de la base |
| `DB_PASSWORD` | *(vacío)* | Contraseña de la base |
| `DB_HOST` | `localhost` | Host de la base |
| `DB_PORT` | `5432` | Puerto de la base |
| `PRESTAMO_DIAS` | `14` | Duración por defecto de un préstamo (días) |
| `PRESTAMO_MAXIMO_POR_USUARIO` | `3` | Préstamos activos simultáneos permitidos por usuario |

### Comandos útiles

```bash
python manage.py test                                   # corre los tests
python manage.py changepassword <email>                 # cambia la contraseña de un usuario
python manage.py makemigrations && python manage.py migrate
```

---

## Estructura del proyecto

```
config/        Configuración de Django (settings, urls raíz, wsgi/asgi)
core/          Página de inicio (dashboard) y vistas/plantillas genéricas reutilizables
usuarios/      Modelo de usuario propio, roles, permisos, login y gestión de cuentas
catalogo/      Libros, autores, categorías y ejemplares
prestamos/     Préstamos y devoluciones (lógica de negocio en services.py)
templates/     Plantillas globales: base.html, 403.html, registration/ (login)
diagrama.txt   Diagrama entidad-relación (formato Mermaid)
```

### Apps en detalle

- **core**
  - `views.inicio`: dashboard. Todos ven sus préstamos activos. Quien tiene permiso de préstamos ve además totales de libros, ejemplares disponibles, préstamos activos y vencidos.
  - `FormularioMixin` y `BorrarView`: bases compartidas para los formularios de alta/edición y las confirmaciones de borrado (plantillas `core/form.html` y `core/confirmar_borrado.html`).
- **usuarios**
  - `models.py`: `Usuario` (hereda de `AbstractBaseUser`, login por email), `Rol` y `Permiso`.
  - `mixins.PermisoRequeridoMixin`: exige login y, si la vista define `permiso`, que el usuario lo tenga. Si no lo tiene, responde 403.
  - `context_processors.permisos`: expone `permisos` en las plantillas para mostrar u ocultar opciones.
  - `permisos.py`: constantes con los códigos de permiso.
- **catalogo**: CRUD de libros, autores, categorías y ejemplares.
- **prestamos**
  - `services.prestar()` y `services.devolver()`: concentran las reglas de negocio (ver más abajo).
  - Las vistas solo validan el formulario y llaman a los servicios.

---

## Modelo de datos

Las tablas usan nombres explícitos (`db_table`) que coinciden con `diagrama.txt`.

| Tabla | Campos principales | Notas |
|---|---|---|
| `usuario` | nombre, apellido, email (único), password_hash, activo | Login por email. Sin `last_login` ni `is_superuser`. |
| `rol` | nombre (único), descripcion | M:N con permiso (`rol_permiso`) |
| `permiso` | codigo (único), descripcion | |
| `usuario_rol` | usuario_id, rol_id | M:N usuario–rol |
| `libro` | titulo, isbn, anio_publicacion, editorial, codigo_dewey | M:N con autor (`libro_autor`) y categoría (`libro_categoria`) |
| `autor` | nombre, apellido | |
| `categoria` | nombre, descripcion | |
| `ejemplar` | libro_id, codigo_barras (único), estado, ubicacion | Estados: `disponible`, `prestado`, `en_reparacion`, `baja` |
| `prestamo` | ejemplar_id, usuario_id, registrado_por_id, fecha_prestamo, fecha_vencimiento, estado, observaciones | Estados: `activo`, `devuelto`. Restricción: un solo préstamo activo por ejemplar. |
| `devolucion` | prestamo_id (único), recibido_por_id, fecha_devolucion, estado_ejemplar, observaciones | Cierra un préstamo (1:1) |

Las claves foráneas usan `on_delete=PROTECT`. Por ejemplo, no se puede borrar un libro que tiene ejemplares, ni un ejemplar con préstamos.

---

## Roles y permisos

La migración `usuarios/0002_roles_permisos_iniciales` crea estos permisos y roles:

| Permiso | Habilita |
|---|---|
| `catalogo.gestionar` | Alta, edición y baja de libros, autores, categorías y ejemplares |
| `prestamos.gestionar` | Registrar préstamos y devoluciones, ver todos los préstamos |
| `usuarios.gestionar` | Administrar usuarios y roles |

| Rol | Permisos |
|---|---|
| **Administrador** | los tres |
| **Bibliotecario** | `catalogo.gestionar`, `prestamos.gestionar` |
| **Socio** | ninguno: consulta el catálogo y sus propios préstamos |

`createsuperuser` asigna automáticamente el rol Administrador con todos los permisos existentes. Los roles se pueden editar desde la aplicación (`/usuarios/roles/`).

---

## Reglas de préstamo

Implementadas en `prestamos/services.py`. Cada operación corre en una transacción con `select_for_update` para evitar que dos bibliotecarios presten el mismo ejemplar a la vez.

**Prestar** (`prestar`). Se rechaza si:
- el ejemplar no está `disponible`;
- el usuario está inactivo;
- la fecha de vencimiento es anterior a hoy;
- el usuario ya tiene `PRESTAMO_MAXIMO_POR_USUARIO` préstamos activos;
- el usuario tiene préstamos vencidos sin devolver.

Al prestar, el ejemplar pasa a `prestado` y se registra quién hizo el préstamo (`registrado_por`).

**Devolver** (`devolver`):
- No se puede devolver dos veces el mismo préstamo.
- El ejemplar queda en el estado indicado (`disponible`, `en_reparacion` o `baja`), nunca en `prestado`.
- El préstamo pasa a `devuelto` y se registra quién recibió el ejemplar (`recibido_por`).
- `Devolucion.con_atraso` indica si se devolvió después del vencimiento, y `Prestamo.vencido` si un préstamo activo ya venció.

---

## Rutas

| Ruta | Descripción | Permiso |
|---|---|---|
| `/` | Inicio / dashboard | login |
| `/cuentas/login/`, `/cuentas/logout/` | Ingreso y salida | — |
| `/cuentas/password/` | Cambiar la propia contraseña | login |
| `/catalogo/libros/` | Listado y detalle de libros | login |
| `/catalogo/libros/nuevo/`, `.../<id>/editar/`, `.../<id>/borrar/` | ABM de libros | `catalogo.gestionar` |
| `/catalogo/libros/<id>/ejemplares/nuevo/`, `/catalogo/ejemplares/<id>/editar\|borrar/` | ABM de ejemplares | `catalogo.gestionar` |
| `/catalogo/autores/`, `/catalogo/categorias/` | Listado de autores y categorías | login |
| `.../nuevo\|nueva/`, `.../<id>/editar/`, `.../<id>/borrar/` | ABM de autores y categorías | `catalogo.gestionar` |
| `/prestamos/` | Listado de préstamos (filtro por estado y búsqueda) | `prestamos.gestionar` |
| `/prestamos/nuevo/` | Registrar préstamo | `prestamos.gestionar` |
| `/prestamos/devolucion/` | Buscar ejemplar por código de barras para devolverlo | `prestamos.gestionar` |
| `/prestamos/<id>/devolver/` | Registrar devolución | `prestamos.gestionar` |
| `/prestamos/<id>/` | Detalle (sin permiso, solo los propios) | login |
| `/prestamos/mis-prestamos/` | Historial de préstamos del usuario | login |
| `/usuarios/` | ABM de usuarios y asignación de contraseña | `usuarios.gestionar` |
| `/usuarios/roles/` | ABM de roles | `usuarios.gestionar` |

---

## Tests

Los tests están en `prestamos/tests.py` y cubren:
- el flujo de préstamo y devolución, tanto desde los servicios como desde las páginas;
- las reglas de rechazo: ejemplar no disponible, usuario inactivo, máximo de préstamos, préstamos vencidos y devolución doble;
- los permisos: un socio no puede gestionar préstamos y solo ve los suyos;
- que todas las páginas cargan y que borrar un libro con ejemplares muestra un aviso.

```bash
python manage.py test
```

Necesitan que el usuario de PostgreSQL pueda crear la base de test (`test_biblioteca`).

---

## Configuración regional

- Idioma: `es-ar`
- Zona horaria: `America/Argentina/Buenos_Aires`
- Los mensajes de error usan la clase `danger` de Bootstrap (`MESSAGE_TAGS`).
