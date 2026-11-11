from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class PerfilSansano(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    peso = models.FloatField(
        help_text="Peso en kg",
        validators=[MinValueValidator(30), MaxValueValidator(300)],
    )
    altura = models.FloatField(
        help_text="Altura en metros",
        validators=[MinValueValidator(1.0), MaxValueValidator(2.5)],
    )
    # {'lunes': ['8:15-9:25', '14:40-15:50'], 'martes': [], ...}
    bloques_libres = models.JSONField(
        default=dict, blank=True,
        help_text="Bloques libres por día: {'lunes': ['8:15-9:25'], ...}",
    )
    tiempo_transporte_min = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MaxValueValidator(240)],
        help_text="Minutos de transporte por trayecto (casa-universidad)",
    )

    @property
    def imc(self):
        if not self.altura or self.altura <= 0:
            return None
        return round(self.peso / (self.altura ** 2), 2)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"
