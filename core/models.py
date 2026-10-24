from django.db import models
from django.contrib.auth.models import User

class PerfilSansano(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    peso = models.FloatField(help_text="Peso en kg")
    altura = models.FloatField(help_text="Altura en metros")
    bloques_libres = models.TextField(help_text="Ej: Lunes 08:15, Martes 14:40")

    def __str__(self):
        return f"Perfil de {self.usuario.username}"