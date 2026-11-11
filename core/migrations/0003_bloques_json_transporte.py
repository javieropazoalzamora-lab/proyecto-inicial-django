import ast

import django.core.validators
from django.db import migrations, models

DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']


def convertir_bloques(apps, schema_editor):
    Perfil = apps.get_model('core', 'PerfilSansano')
    for p in Perfil.objects.all():
        try:
            viejo = ast.literal_eval(p.bloques_libres_old) if p.bloques_libres_old else {}
        except (ValueError, SyntaxError):
            viejo = {}
        nuevo = {}
        for dia in DIAS:
            valor = viejo.get(dia) if isinstance(viejo, dict) else None
            if isinstance(valor, str) and valor and valor != 'Sin tiempo libre':
                nuevo[dia] = [valor]
            else:
                nuevo[dia] = []
        p.bloques_libres = nuevo
        # Alturas guardadas en cm (ej. 175) se pasan a metros
        if p.altura and p.altura > 3:
            p.altura = p.altura / 100
        p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_perfilsansano_imc'),
    ]

    operations = [
        migrations.RenameField('perfilsansano', 'bloques_libres', 'bloques_libres_old'),
        migrations.AddField(
            'perfilsansano', 'bloques_libres',
            models.JSONField(blank=True, default=dict,
                             help_text="Bloques libres por día: {'lunes': ['8:15-9:25'], ...}"),
        ),
        migrations.RunPython(convertir_bloques, migrations.RunPython.noop),
        migrations.RemoveField('perfilsansano', 'bloques_libres_old'),
        migrations.RemoveField('perfilsansano', 'imc'),
        migrations.AddField(
            'perfilsansano', 'tiempo_transporte_min',
            models.PositiveSmallIntegerField(
                blank=True, null=True,
                validators=[django.core.validators.MaxValueValidator(240)],
                help_text="Minutos de transporte por trayecto (casa-universidad)"),
        ),
        migrations.AlterField(
            'perfilsansano', 'peso',
            models.FloatField(help_text="Peso en kg", validators=[
                django.core.validators.MinValueValidator(30),
                django.core.validators.MaxValueValidator(300)]),
        ),
        migrations.AlterField(
            'perfilsansano', 'altura',
            models.FloatField(help_text="Altura en metros", validators=[
                django.core.validators.MinValueValidator(1.0),
                django.core.validators.MaxValueValidator(2.5)]),
        ),
    ]
