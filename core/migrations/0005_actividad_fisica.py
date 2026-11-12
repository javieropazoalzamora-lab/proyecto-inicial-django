from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_encuesta_ampliada_y_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilsansano',
            name='actividad_fisica',
            field=models.CharField(
                choices=[('leve', 'Leve (poco o ningún ejercicio frecuente)'),
                         ('moderada', 'Moderada (ejercicio ligero, 2 a 3 veces por semana)'),
                         ('alta', 'Alta (ejercicio intenso, 4 o más veces por semana)')],
                default='moderada', help_text='Nivel de actividad física actual', max_length=10),
        ),
    ]
