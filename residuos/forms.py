"""
residuos/forms.py
=================
Formulario para crear y editar registros de residuos domésticos.

Decisiones de diseño:
- `NuevoRegistroForm` extiende ModelForm para aprovechar la validación
  automática de tipos y los mensajes de error del modelo.
- Los campos `usuario`, `semana` y `municipio` quedan FUERA del formulario
  porque los asigna la vista (principio de menor privilegio).
- Las validaciones custom están en `clean_<campo>` y `clean()` para seguir
  el patrón Django estándar, separando validación por campo de validación
  cruzada.
- Los widgets usan `step="0.1"` y `min="0"` como primera barrera client-side,
  pero la validación server-side en `clean_*` es la fuente de verdad.
"""

from django import forms

from .models import RegistroResiduo

# Campos que el ciudadano puede editar directamente
CAMPOS_KG = [
    'organico_kg',
    'reciclable_kg',
    'no_reciclable_kg',
    'especial_kg',
    'peligroso_kg',
]


class NuevoRegistroForm(forms.ModelForm):
    """
    Formulario para crear o editar un RegistroResiduo semanal.

    Campos editables por el ciudadano:
        - organico_kg, reciclable_kg, no_reciclable_kg, especial_kg, peligroso_kg
        - observaciones (opcional)

    Campos asignados por la vista (no aparecen en el formulario):
        - usuario   ← request.user
        - semana    ← calculado: lunes de la semana actual
        - municipio ← request.user.municipio
    """

    class Meta:
        model  = RegistroResiduo
        fields = CAMPOS_KG + ['observaciones']
        widgets = {
            'organico_kg': forms.NumberInput(attrs={
                'step': '0.1',
                'min':  '0',
                'placeholder': '0.0',
            }),
            'reciclable_kg': forms.NumberInput(attrs={
                'step': '0.1',
                'min':  '0',
                'placeholder': '0.0',
            }),
            'no_reciclable_kg': forms.NumberInput(attrs={
                'step': '0.1',
                'min':  '0',
                'placeholder': '0.0',
            }),
            'especial_kg': forms.NumberInput(attrs={
                'step': '0.1',
                'min':  '0',
                'placeholder': '0.0',
            }),
            'peligroso_kg': forms.NumberInput(attrs={
                'step': '0.1',
                'min':  '0',
                'placeholder': '0.0',
            }),
            'observaciones': forms.Textarea(attrs={
                'rows':        3,
                'placeholder': 'Ej: Incluye residuos de la reforma que hicimos esta semana.',
                'maxlength':   500,
            }),
        }
        error_messages = {
            'organico_kg':      {'invalid': 'Ingresa un número válido (ej: 1.5).'},
            'reciclable_kg':    {'invalid': 'Ingresa un número válido (ej: 0.8).'},
            'no_reciclable_kg': {'invalid': 'Ingresa un número válido (ej: 2.0).'},
            'especial_kg':      {'invalid': 'Ingresa un número válido (ej: 0.3).'},
            'peligroso_kg':     {'invalid': 'Ingresa un número válido (ej: 0.1).'},
        }

    # ------------------------------------------------------------------
    # Validaciones por campo — no se permiten valores negativos
    # ------------------------------------------------------------------

    def _validate_kg_field(self, field_name: str) -> float:
        """Helper interno para validar cualquier campo de kg."""
        value = self.cleaned_data.get(field_name, 0) or 0
        if value < 0:
            raise forms.ValidationError(
                'El valor no puede ser negativo.'
            )
        return value

    def clean_organico_kg(self):
        return self._validate_kg_field('organico_kg')

    def clean_reciclable_kg(self):
        return self._validate_kg_field('reciclable_kg')

    def clean_no_reciclable_kg(self):
        return self._validate_kg_field('no_reciclable_kg')

    def clean_especial_kg(self):
        return self._validate_kg_field('especial_kg')

    def clean_peligroso_kg(self):
        return self._validate_kg_field('peligroso_kg')

    # ------------------------------------------------------------------
    # Validación cruzada — al menos un tipo debe ser > 0
    # ------------------------------------------------------------------

    def clean(self):
        cleaned = super().clean()

        total = sum(
            cleaned.get(campo, 0) or 0
            for campo in CAMPOS_KG
        )

        if total <= 0:
            raise forms.ValidationError(
                'Ingresa al menos un tipo de residuo con cantidad mayor a 0 kg. '
                'Si no generaste residuos esta semana, no es necesario crear un registro.'
            )

        return cleaned