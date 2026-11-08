from django.db import models
from django.contrib.auth.models import User

class PerfilSansano(models.Model):
    OPCIONES_ACTIVIDAD = [
        ('leve', 'Leve'),
        ('moderada', 'Moderada'),
        ('alta', 'Alta'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    peso = models.FloatField(help_text="Peso en kg")
    altura = models.FloatField(help_text="Altura en metros")
    imc = models.FloatField(null=True, blank=True)
    
    # Nuevo campo añadido para la actividad física
    actividad_fisica = models.CharField(
        max_length=20, 
        choices=OPCIONES_ACTIVIDAD, 
        default='moderada',
        help_text="Nivel de actividad física"
    )
    
    bloques_libres = models.TextField(help_text="Ej: Lunes 08:15, Martes 14:40")

    def __str__(self):
        return f"Perfil de {self.usuario.username}"