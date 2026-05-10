from django.db import models
from django.conf import settings


class RegistroResiduo(models.Model):

    class Municipio(models.TextChoices):
        CHIA        = 'Chia',       'Chía'
        CAJICA      = 'Cajica',     'Cajicá'
        ZIPAQUIRA   = 'Zipaquira',  'Zipaquirá'
        COGUA       = 'Cogua',      'Cogua'
        TAUSA       = 'Tausa',      'Tausa'
        SOPO        = 'Sopo',       'Sopó'
        TOCANCIPA   = 'Tocancipa',  'Tocancipá'
        GACHANCIPA  = 'Gachancipa', 'Gachancipá'
        NEMOCON     = 'Nemocon',    'Nemocón'
        SUPATA      = 'Supata',     'Supatá'
        TABIO       = 'Tabio',      'Tabio'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_residuos',
        verbose_name='Ciudadano',
    )
    semana = models.DateField(
        verbose_name='Semana (lunes)',
        help_text='Fecha del lunes de la semana registrada',
    )
    municipio = models.CharField(
        max_length=50,
        choices=Municipio.choices,
        verbose_name='Municipio',
        db_index=True,
    )
    organico_kg = models.FloatField(default=0, verbose_name='Orgánico (kg)')
    reciclable_kg = models.FloatField(default=0, verbose_name='Reciclable (kg)')
    no_reciclable_kg = models.FloatField(default=0, verbose_name='No reciclable (kg)')
    especial_kg = models.FloatField(default=0, verbose_name='Especial (kg)')
    peligroso_kg = models.FloatField(default=0, verbose_name='Peligroso (kg)')
    observaciones = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observaciones',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.email} — Semana {self.semana} ({self.municipio})"

    class Meta:
        verbose_name = 'Registro de Residuos'
        verbose_name_plural = 'Registros de Residuos'
        ordering = ['-semana']
        unique_together = ('usuario', 'semana')