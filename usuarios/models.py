from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'admin')
        return self.create_user(email, password, **extra_fields)
    
class CustomUser(AbstractUser):
    """
    Usuario personalizado de SabanaLimpia.
    - Autenticación por email (no username).
    - El username se autogenera desde el email para compatibilidad con el admin de Django.
    - Rol y municipio como choices para garantizar integridad.
    """

    class Rol(models.TextChoices):
        CIUDADANO = 'ciudadano', 'Ciudadano'
        OPERADOR = 'operador', 'Operador Municipal'
        ADMIN = 'admin', 'Administrador'

    class Municipio(models.TextChoices):
        CHIA = 'Chia', 'Chía'
        CAJICA = 'Cajica', 'Cajicá'
        ZIPAQUIRA = 'Zipaquira', 'Zipaquirá'
        COGUA = 'Cogua', 'Cogua'
        TAUSA = 'Tausa', 'Tausa'
        SOPO = 'Sopo', 'Sopó'
        TOCANCIPA = 'Tocancipa', 'Tocancipá'
        GACHANCIPA = 'Gachancipa', 'Gachancipá'
        NEMOCON = 'Nemocon', 'Nemocón'
        SUPATA = 'Supata', 'Supatá'
        TABIO = 'Tabio', 'Tabio'

    objects = CustomUserManager()
    
    # --- Campos de autenticación ---
    email = models.EmailField(
        unique=True,
        verbose_name='Correo electrónico',
    )

    # --- Campos de negocio ---
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CIUDADANO,
        verbose_name='Rol',
        db_index=True,  # Se filtra por rol frecuentemente (panel operador)
    )
    municipio = models.CharField(
        max_length=50,  # Holgura suficiente para nombres con tildes o futuros municipios
        choices=Municipio.choices,
        default=Municipio.CHIA,
        verbose_name='Municipio',
        db_index=True,  # Se filtra por municipio frecuentemente
    )

    # --- Configuración de autenticación ---
    USERNAME_FIELD = 'email'
    # username se autogenera en save(); no se le pide al usuario en el registro
    REQUIRED_FIELDS = []  # Sin campos extra obligatorios en createsuperuser

    # --- Propiedades de conveniencia (alineadas con el plan de desarrollo) ---
    @property
    def fecha_registro(self):
        """Alias legible de date_joined (ya provisto por AbstractUser)."""
        return self.date_joined

    @property
    def activo(self):
        """Alias legible de is_active (ya provisto por AbstractUser)."""
        return self.is_active

    # --- Helpers de rol (evitan comparar strings en las vistas) ---
    def es_ciudadano(self):
        return self.rol == self.Rol.CIUDADANO

    def es_operador(self):
        return self.rol == self.Rol.OPERADOR

    def es_admin(self):
        return self.rol == self.Rol.ADMIN

    # --- Ciclo de vida ---
    def save(self, *args, **kwargs):
        """
        Autogenera el username a partir del email para no pedírselo al usuario.
        El username sigue siendo obligatorio internamente en Django, pero el
        ciudadano jamás lo ve ni lo escribe.
        """
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.email} — {self.get_rol_display()} ({self.municipio})"

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']  # Más recientes primero en el admin

class Insignia(models.Model):
    """
    Catálogo completo de insignias disponibles en el sistema.
    Las condiciones se almacenan como JSON para flexibilidad.
    """

    NIVEL_CHOICES = [
        (0, 'Especial'),   # Pionero y Primera vez (sin jerarquía de nivel)
        (1, 'Bronce'),
        (2, 'Plata'),
        (3, 'Oro'),
    ]

    slug        = models.SlugField(max_length=80, unique=True)
    nombre      = models.CharField(max_length=150)   # Nombre épico en la app
    descripcion = models.TextField()                  # Texto del logro
    emoji       = models.CharField(max_length=10)
    nivel       = models.IntegerField(choices=NIVEL_CHOICES, default=1)
    condicion   = models.JSONField()
    # Estructura de condicion:
    # {
    #   "tipo": "total_reportes" | "reportes_resueltos" |
    #           "semanas_consecutivas" | "municipios_distintos" |
    #           "categorias_distintas" | "primer_reporte_municipio_virgen",
    #   "umbral": <int>   (no requerido para tipo "primer_reporte_municipio_virgen")
    # }
    orden       = models.PositiveIntegerField(default=0)
    visible     = models.BooleanField(default=True)
    # Si False, no aparece en la galería hasta que el usuario la obtiene

    class Meta:
        ordering = ['-nivel', 'orden']

    def __str__(self):
        return f'{self.nombre} (Nivel {self.nivel})'


class LogroUsuario(models.Model):
    """Registro de qué insignia obtuvo qué usuario y cuándo."""

    usuario          = models.ForeignKey(
        'CustomUser', on_delete=models.CASCADE, related_name='logros'
    )
    insignia         = models.ForeignKey(
        Insignia, on_delete=models.CASCADE, related_name='logros'
    )
    fecha_obtencion  = models.DateTimeField(auto_now_add=True)
    notificado       = models.BooleanField(default=False)
    # True cuando el toast ya fue mostrado al usuario

    class Meta:
        unique_together = ('usuario', 'insignia')
        ordering        = ['-fecha_obtencion']

    def __str__(self):
        return f'{self.usuario.email} — {self.insignia.nombre}'