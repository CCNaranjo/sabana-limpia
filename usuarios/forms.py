from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import CustomUser


class RegistroForm(forms.ModelForm):
    """
    Formulario de registro para ciudadanos.
    - Email único validado a nivel de formulario y de BD.
    - Contraseña con confirmación y validadores de Django.
    - Municipio obligatorio con choices del modelo.
    """

    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Mínimo 8 caracteres',
            'autocomplete': 'new-password',
        }),
        help_text='Mínimo 8 caracteres. No puede ser solo números.',
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Repite tu contraseña',
            'autocomplete': 'new-password',
        }),
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'municipio']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'tu@correo.com',
                'autocomplete': 'email',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Tu nombre',
                'autocomplete': 'given-name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Tu apellido',
                'autocomplete': 'family-name',
            }),
            'municipio': forms.Select(attrs={
                'class': 'form-input',
            }),
        }
        labels = {
            'email': 'Correo electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'municipio': 'Municipio',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Ya existe una cuenta con este correo electrónico.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        # Usa los validadores configurados en AUTH_PASSWORD_VALIDATORS del settings
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Las contraseñas no coinciden.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        # rol queda como 'ciudadano' (default del modelo)
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """
    Formulario de login por email y contraseña.
    La autenticación real se hace en la vista con authenticate().
    """

    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'tu@correo.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Tu contraseña',
            'autocomplete': 'current-password',
        }),
    )
    recordarme = forms.BooleanField(
        label='Recordarme',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
    )

    def clean_email(self):
        return self.cleaned_data.get('email', '').lower().strip()