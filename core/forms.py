import math
import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .horarios import modulos_desde_post, ventanas_desde_modulos
from .constantes import (ACTIVIDADES, BLOQUES_VALIDOS, DIAS, DIETAS, LUGARES, OBJETIVOS,
                         PRESUPUESTOS, TIEMPOS_COCINA)

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
    mayor_de_edad = forms.BooleanField(
        required=True, error_messages={'required': "Debes confirmar que tienes 18 años o más."})
    actividad_fisica = forms.ChoiceField(choices=ACTIVIDADES)
    objetivo = forms.ChoiceField(choices=OBJETIVOS)
    tipo_dieta = forms.ChoiceField(choices=DIETAS)
    alergias = forms.CharField(required=False, max_length=100)
    presupuesto = forms.ChoiceField(choices=PRESUPUESTOS)
    tiempo_cocina = forms.ChoiceField(choices=TIEMPOS_COCINA)
    lugar_entrenamiento = forms.ChoiceField(choices=LUGARES)
    tiene_lesion = forms.BooleanField(required=False)

    def clean_alergias(self):
        # Texto corto que irá a la IA: solo letras, números y puntuación simple (reduce inyección de instrucciones)
        texto = re.sub(r'[^\w\s,.\-áéíóúñÁÉÍÓÚÑ]', ' ', self.cleaned_data.get('alergias') or '')
        return re.sub(r'\s+', ' ', texto).strip()[:100]

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
        bloques, clases = {}, {}
        for dia in DIAS:
            libres, cl = modulos_desde_post(self.data, dia)
            bloques[dia] = ventanas_desde_modulos(libres)   # ventanas libres, p. ej. ['9:40-13:40']
            clases[dia] = sorted(cl)
        cleaned['bloques'] = bloques
        cleaned['clases'] = clases
        return cleaned
