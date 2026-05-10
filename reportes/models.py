from django.db import models
from django.conf import settings


class Reporte(models.Model):

    class Categoria(models.TextChoices):
        RESIDUOS_SOLIDOS   = 'residuos_solidos',   'Residuos Sólidos'
        ESCOMBROS          = 'escombros',           'Escombros'
        RESIDUOS_PELIGROSOS = 'residuos_peligrosos', 'Residuos Peligrosos'
        RAEE               = 'raee',                'RAEE (Electrónicos)'
        ORGANICOS          = 'organicos',           'Orgánicos'
        OTRO               = 'otro',                'Otro'

    class Estado(models.TextChoices):
        PENDIENTE   = 'pendiente',   'Pendiente'
        EN_GESTION  = 'en_gestion',  'En Gestión'
        RESUELTO    = 'resuelto',    'Resuelto'
        RECHAZADO   = 'rechazado',   'Rechazado'

    class Municipio(models.TextChoices):
        CHIA        = 'Chia',        'Chía'
        CAJICA      = 'Cajica',      'Cajicá'
        ZIPAQUIRA   = 'Zipaquira',   'Zipaquirá'
        COGUA       = 'Cogua',       'Cogua'
        TAUSA       = 'Tausa',       'Tausa'
        SOPO        = 'Sopo',        'Sopó'
        TOCANCIPA   = 'Tocancipa',   'Tocancipá'
        GACHANCIPA  = 'Gachancipa',  'Gachancipá'
        NEMOCON     = 'Nemocon',     'Nemocón'
        SUPATA      = 'Supata',      'Supatá'
        TABIO       = 'Tabio',       'Tabio'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reportes',
        verbose_name='Ciudadano',
    )
    titulo = models.CharField(max_length=120, verbose_name='Título')
    descripcion = models.TextField(verbose_name='Descripción')
    categoria = models.CharField(
        max_length=30,
        choices=Categoria.choices,
        verbose_name='Categoría',
        db_index=True,
    )
    latitud  = models.FloatField(verbose_name='Latitud')
    longitud = models.FloatField(verbose_name='Longitud')
    foto = models.ImageField(
        upload_to='reportes/',
        verbose_name='Foto',
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name='Estado',
        db_index=True,
    )
    municipio = models.CharField(
        max_length=50,
        choices=Municipio.choices,
        verbose_name='Municipio',
        db_index=True,
    )
    nota_operador = models.TextField(
        null=True,
        blank=True,
        verbose_name='Nota del operador',
    )
    operador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reportes_gestionados',
        verbose_name='Operador asignado',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.id}] {self.titulo} — {self.get_estado_display()} ({self.municipio})"

    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-created_at']