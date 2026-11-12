from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constantes import ACTIVIDADES, DIETAS, LUGARES, OBJETIVOS, PRESUPUESTOS, TIEMPOS_COCINA


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
    mayor_de_edad = models.BooleanField(default=False, help_text="Confirma tener 18 años o más")
    actividad_fisica = models.CharField(
        max_length=10, choices=ACTIVIDADES, default='moderada', help_text="Nivel de actividad física actual")
    objetivo = models.CharField(max_length=20, choices=OBJETIVOS, default='mantener')
    tipo_dieta = models.CharField(max_length=20, choices=DIETAS, default='omnivora')
    alergias = models.CharField(max_length=100, blank=True, help_text="Alergias o intolerancias (texto corto)")
    presupuesto = models.CharField(max_length=10, choices=PRESUPUESTOS, default='medio')
    tiempo_cocina = models.CharField(max_length=10, choices=TIEMPOS_COCINA, default='normal')
    lugar_entrenamiento = models.CharField(max_length=12, choices=LUGARES, default='casa')
    tiene_lesion = models.BooleanField(default=False, help_text="Molestia o lesión que limita ejercicios")

    @property
    def imc(self):
        if not self.altura or self.altura <= 0:
            return None
        return round(self.peso / (self.altura ** 2), 2)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


class PlanSemanal(models.Model):
    """Plan generado una vez al enviar la encuesta; el portal solo lo lee."""
    ORIGENES = [('ia', 'Generado por IA'), ('respaldo', 'Plan base por reglas')]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='plan')
    contenido = models.JSONField(default=dict)
    origen = models.CharField(max_length=10, choices=ORIGENES)
    huella = models.CharField(max_length=64, help_text="Hash de los datos usados para generarlo")
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Plan de {self.usuario.username} ({self.origen})"
