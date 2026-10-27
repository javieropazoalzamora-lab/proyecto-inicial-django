from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import PerfilSansano

class RegistroSansanoForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo Institucional")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@usm.cl'):
            raise forms.ValidationError("Solo se permiten correos @usm.cl")
        return email