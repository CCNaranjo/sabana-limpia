"""
Forms for the reportes app.

Keeping form validation logic in forms.py (not views.py) follows the
Django fat-models/thin-views pattern and makes each layer independently testable.
"""

from django import forms

from .models import Reporte


class NuevoReporteForm(forms.ModelForm):
    """
    Form for creating a new citizen report.

    The fields `usuario`, `municipio`, `estado`, `operador` and `nota_operador`
    are excluded because they are set programmatically in the view — never by
    the citizen.

    Coordinate fields are rendered as hidden inputs populated by JS
    (navigator.geolocation). We keep them in the form so Django validates
    their presence and type, avoiding any server-side trust in the raw POST data.
    """

    latitud = forms.FloatField(
        widget=forms.HiddenInput(),
        error_messages={
            "required": "Activa la ubicación y presiona 'Usar mi ubicación' antes de enviar.",
            "invalid": "Las coordenadas de latitud no son válidas.",
        },
    )

    longitud = forms.FloatField(
        widget=forms.HiddenInput(),
        error_messages={
            "required": "Activa la ubicación y presiona 'Usar mi ubicación' antes de enviar.",
            "invalid": "Las coordenadas de longitud no son válidas.",
        },
    )

    class Meta:
        model = Reporte
        fields = ["titulo", "descripcion", "categoria", "latitud", "longitud", "foto"]
        widgets = {
            "titulo": forms.TextInput(
                attrs={
                    "placeholder": "Ej: Basura acumulada en parque central",
                    "maxlength": 120,
                    "autocomplete": "off",
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "placeholder": "Describe la situación: cantidad aproximada, tiempo que lleva ahí, riesgo visible…",
                    "rows": 4,
                }
            ),
            "categoria": forms.Select(),
            "foto": forms.FileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
        }
        error_messages = {
            "titulo": {"required": "El título es obligatorio."},
            "descripcion": {"required": "La descripción es obligatoria."},
            "categoria": {"required": "Selecciona una categoría."},
            "foto": {"required": "La foto es obligatoria para verificar el reporte."},
        }

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto:
            # 5 MB hard limit server-side (client-side compression targets < 2 MB)
            max_size_bytes = 5 * 1024 * 1024
            if foto.size > max_size_bytes:
                raise forms.ValidationError(
                    "La imagen supera el límite de 5 MB. "
                    "Intenta con una foto de menor resolución."
                )
            allowed_types = {"image/jpeg", "image/png", "image/webp"}
            if foto.content_type not in allowed_types:
                raise forms.ValidationError(
                    "Solo se aceptan imágenes en formato JPG, PNG o WebP."
                )
        return foto

    def clean(self):
        cleaned = super().clean()
        lat = cleaned.get("latitud")
        lon = cleaned.get("longitud")

        # Basic geographic bounds check for Sabana Centro, Cundinamarca
        # Approximate bounding box: lat [4.5, 5.2] lon [-74.4, -73.8]
        if lat is not None and not (4.5 <= lat <= 5.2):
            self.add_error(
                "latitud",
                "Las coordenadas no corresponden a Sabana Centro. "
                "Asegúrate de estar en uno de los municipios cubiertos.",
            )
        if lon is not None and not (-74.4 <= lon <= -73.8):
            self.add_error(
                "longitud",
                "Las coordenadas no corresponden a Sabana Centro.",
            )
        return cleaned