import math
import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .horarios import modulos_desde_post, ventanas_desde_modulos
from .constantes import (ACTIVIDADES, DIAS, DIETAS, LUGARES, OBJETIVOS,
                         PRESUPUESTOS, TIEMPOS_COCINA)
from .models import PerfilSansano

DOMINIO_PERMITIDO = '@usm.cl'

# Rangos aceptados (los mismos validadores que tiene el modelo PerfilSansano)
PESO_MIN, PESO_MAX = 30, 300          # kg
ALTURA_MIN, ALTURA_MAX = 1.0, 2.5     # m
IMC_PLAUSIBLE_MIN, IMC_PLAUSIBLE_MAX = 10, 80


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


class EncuestaPerfilForm(forms.ModelForm):
    """Encuesta de perfil ligada al modelo PerfilSansano.

    El usuario NO es un campo del formulario: la vista lo asigna con
    form.save(commit=False) + perfil.usuario = request.user, así nadie puede
    escribir en el perfil de otra persona manipulando el POST."""

    # Peso y altura se reciben como texto para aceptar coma decimal ("70,5") y altura en cm ("175").
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

    class Meta:
        model = PerfilSansano
        fields = ['peso', 'altura', 'tiempo_transporte_min', 'mayor_de_edad', 'actividad_fisica', 'objetivo',
                  'tipo_dieta', 'alergias', 'presupuesto', 'tiempo_cocina', 'lugar_entrenamiento', 'tiene_lesion']

    def clean_alergias(self):
        # Texto corto que irá a la IA: solo letras, números y puntuación simple (reduce inyección de instrucciones)
        texto = re.sub(r'[^\w\s,.\-áéíóúñÁÉÍÓÚÑ]', ' ', self.cleaned_data.get('alergias') or '')
        return re.sub(r'\s+', ' ', texto).strip()[:100]

    def clean_peso(self):
        peso = _a_numero(self.cleaned_data['peso'], 'el peso')
        if not PESO_MIN <= peso <= PESO_MAX:
            raise forms.ValidationError(f"El peso debe estar entre {PESO_MIN} y {PESO_MAX} kg.")
        return peso

    def clean_altura(self):
        altura = _a_numero(self.cleaned_data['altura'], 'la altura')
        if altura > 3:  # ingresada en cm
            altura = altura / 100
        if not ALTURA_MIN <= altura <= ALTURA_MAX:
            raise forms.ValidationError("La altura debe estar entre 1,00 y 2,50 m (o 100 y 250 cm).")
        return round(altura, 3)

    def clean(self):
        cleaned = super().clean()

        # Validación cruzada: cada dato puede estar en rango y aun así la combinación ser imposible
        # (típico error de unidades, p. ej. 30 kg con 2,40 m). Solo se revisa si ambos campos son válidos.
        peso, altura = cleaned.get('peso'), cleaned.get('altura')
        if peso is not None and altura is not None:
            imc = peso / (altura ** 2)
            if not IMC_PLAUSIBLE_MIN <= imc <= IMC_PLAUSIBLE_MAX:
                raise forms.ValidationError(
                    f"La combinación de peso y altura da un IMC de {imc:.1f}, que no es posible. "
                    "Revisa que el peso esté en kg y la altura en metros o centímetros.")

        # Grilla de horario: no son campos del formulario (son casillas libre_<dia>/clase_<dia>)
        bloques, clases = {}, {}
        for dia in DIAS:
            libres, cl = modulos_desde_post(self.data, dia)
            bloques[dia] = ventanas_desde_modulos(libres)   # ventanas libres, p. ej. ['9:40-13:40']
            clases[dia] = sorted(cl)
        cleaned['bloques'] = bloques
        cleaned['clases'] = clases
        return cleaned

    def save(self, commit=True):
        perfil = super().save(commit=False)
        perfil.bloques_libres = self.cleaned_data['bloques']
        perfil.clases = self.cleaned_data['clases']
        if commit:
            perfil.save()
        return perfil
