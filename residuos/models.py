"""
residuos/models.py
==================
Modelo de datos para el registro doméstico de residuos.

Decisiones de diseño:
- `semana` siempre es el lunes de esa semana (calculado en la vista, nunca en el modelo).
- `municipio` se desnormaliza desde el usuario al guardar — permite agrupar en
  estadísticas (T-29) sin JOIN a la tabla de usuarios.
- `unique_together = ('usuario', 'semana')` garantiza un único registro por semana
  a nivel de base de datos, no solo a nivel de aplicación.
- `updated_at` es necesario para la lógica de edición: solo se permite editar si
  la semana es la actual O si el registro fue creado ayer (ventana de corrección).
"""

from django.db import models
from django.conf import settings


class RegistroResiduo(models.Model):

    class Municipio(models.TextChoices):
        CHIA       = 'Chia',       'Chía'
        CAJICA     = 'Cajica',     'Cajicá'
        ZIPAQUIRA  = 'Zipaquira',  'Zipaquirá'
        COGUA      = 'Cogua',      'Cogua'
        TAUSA      = 'Tausa',      'Tausa'
        SOPO       = 'Sopo',       'Sopó'
        TOCANCIPA  = 'Tocancipa',  'Tocancipá'
        GACHANCIPA = 'Gachancipa', 'Gachancipá'
        NEMOCON    = 'Nemocon',    'Nemocón'
        SUPATA     = 'Supata',     'Supatá'
        TABIO      = 'Tabio',      'Tabio'

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

    # Tipos de residuo en kg
    organico_kg      = models.FloatField(default=0, verbose_name='Orgánico (kg)')
    reciclable_kg    = models.FloatField(default=0, verbose_name='Reciclable (kg)')
    no_reciclable_kg = models.FloatField(default=0, verbose_name='No reciclable (kg)')
    especial_kg      = models.FloatField(default=0, verbose_name='Especial (kg)')
    peligroso_kg     = models.FloatField(default=0, verbose_name='Peligroso (kg)')

    observaciones = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observaciones',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    # updated_at permite determinar si el registro está dentro de la ventana
    # de edición (semana actual o día anterior al registro).
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------------------------------------------------
    # Métodos de negocio
    # ------------------------------------------------------------------

    def total_kg(self) -> float:
        """
        Suma de todos los tipos de residuo en kg.

        Centraliza el cálculo para que templates, admin y futuras APIs
        no repitan la misma aritmética.
        """
        return (
            self.organico_kg
            + self.reciclable_kg
            + self.no_reciclable_kg
            + self.especial_kg
            + self.peligroso_kg
        )

    # ------------------------------------------------------------------
    # Representación
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return f"{self.usuario.email} — Semana {self.semana} ({self.municipio})"

    # ------------------------------------------------------------------
    # Meta
    # ------------------------------------------------------------------

    class Meta:
        verbose_name        = 'Registro de Residuos'
        verbose_name_plural = 'Registros de Residuos'
        ordering            = ['-semana']
        unique_together     = ('usuario', 'semana')