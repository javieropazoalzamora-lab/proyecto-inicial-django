import math

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .constantes import BLOQUES_VALIDOS, DIAS

DOMINIO_PERMITIDO = '@usm.cl'


class RegistroSansanoForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo Institucional")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email.endswith(DOMINIO_PERMITIDO) or len(email) == len(DOMINIO_PERMITIDO):
            raise forms.ValidationError("Solo se permiten correos @usm.cl")
        # Solo bloquea si ya hay una cuenta VERIFICADA con ese correo. Una cuenta sin
        # activar no prueba que su creador sea el dueño del correo, así que no debe
        # impedir que el dueño real se registre (la vista la reemplaza).
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email


def _a_numero(valor, nombre):
    try:
        numero = float(str(valor).strip().replace(',', '.'))
    except (TypeError, ValueError):
        raise forms.ValidationError(f"Ingresa un número válido para {nombre}.")
    if not math.isfinite(numero):
        raise forms.ValidationError(f"Ingresa un número válido para {nombre}.")
    return numero


class EncuestaPerfilForm(forms.Form):
    peso = forms.CharField()
    altura = forms.CharField()
    tiempo_transporte_min = forms.IntegerField(required=False, min_value=0, max_value=240)

    def clean_peso(self):
        peso = _a_numero(self.cleaned_data['peso'], 'el peso')
        if not 30 <= peso <= 300:
            raise forms.ValidationError("El peso debe estar entre 30 y 300 kg.")
        return peso

    def clean_altura(self):
        altura = _a_numero(self.cleaned_data['altura'], 'la altura')
        if altura > 3:  # ingresada en cm
            altura = altura / 100
        if not 1.0 <= altura <= 2.5:
            raise forms.ValidationError("La altura debe estar entre 1,00 y 2,50 m (o 100 y 250 cm).")
        return round(altura, 3)

    def clean(self):
        cleaned = super().clean()
        data = self.data
        bloques = {}
        for dia in DIAS:
            if hasattr(data, 'getlist'):
                elegidos = data.getlist(dia)
            else:
                v = data.get(dia, [])
                elegidos = v if isinstance(v, (list, tuple)) else [v]
            bloques[dia] = [b for b in BLOQUES_VALIDOS if b in elegidos]  # orden canónico, sin duplicados
        cleaned['bloques'] = bloques
        return cleaned
