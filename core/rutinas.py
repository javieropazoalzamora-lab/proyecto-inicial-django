"""Rutinas de ejercicio estructuradas (banco conservador + validación de lo que propone la IA).

Una rutina es: {'titulo', 'duracion_min', 'intensidad', 'ejercicios': [{'nombre', 'detalle'}]}.
El banco es deliberadamente simple y de bajo riesgo: ejercicios básicos con peso corporal, caminata
y movilidad. No reemplaza a un profesional.
"""
import re

INTENSIDADES = ('baja', 'media', 'alta')
MAX_EJERCICIOS = 8
DURACION_MAX = 90
DURACION_MIN = 10
MARGEN_MIN = 10  # tiempo para cambiarse / trasladarse dentro del hueco

CALENTAMIENTO = {'nombre': 'Calentamiento', 'detalle': '5 min de movilidad articular y caminata suave'}
ENFRIAMIENTO = {'nombre': 'Vuelta a la calma', 'detalle': '5 min de estiramiento suave'}

# Bloques principales por tipo de sesión y lugar: (nombre, detalle)
FUERZA = {
    'casa': [('Sentadillas', '3 x 12'), ('Flexiones (en rodillas si cuesta)', '3 x 8-10'),
             ('Remo con mochila cargada', '3 x 12'), ('Puente de glúteos', '3 x 15'), ('Plancha', '3 x 20-30 s')],
    'gimnasio': [('Prensa de piernas', '3 x 12'), ('Press de pecho en máquina', '3 x 10'),
                 ('Remo en polea', '3 x 12'), ('Peso muerto rumano liviano', '3 x 10'), ('Plancha', '3 x 30 s')],
    'aire_libre': [('Sentadillas', '3 x 12'), ('Flexiones en banca o muro', '3 x 10'),
                   ('Zancadas', '3 x 10 por pierna'), ('Remo invertido o con mochila', '3 x 10'), ('Plancha', '3 x 30 s')],
}
CARDIO = {
    'casa': [('Marcha en el lugar o saltos suaves', '3 x 3 min'), ('Subir y bajar un escalón', '3 x 2 min'),
             ('Boxeo de sombra', '3 x 2 min')],
    'gimnasio': [('Trote suave o cinta inclinada', '20 min a ritmo en que puedas conversar'),
                 ('Bicicleta o elíptica', '10 min suaves')],
    'aire_libre': [('Trote suave alternado con caminata', '20 min (1 min trote / 1 min caminata)'),
                   ('Caminata rápida', '10 min')],
}
BAJO_IMPACTO = {
    'casa': [('Caminata activa en el lugar o por el barrio', '20 min'), ('Sentadilla a una silla', '2 x 10'),
             ('Elevaciones de talón', '2 x 15'), ('Flexiones en muro', '2 x 10')],
    'gimnasio': [('Elíptica o bicicleta', '20 min suaves'), ('Prensa de piernas liviana', '2 x 12'),
                 ('Remo en polea liviano', '2 x 12')],
    'aire_libre': [('Caminata activa', '25 min'), ('Sentadilla a una banca', '2 x 10'),
                   ('Flexiones en muro', '2 x 10')],
}
MOVILIDAD = [('Movilidad de cadera y hombros', '5 min'), ('Estiramiento de isquios y pecho', '2 x 30 s por lado'),
             ('Caminata suave', '5-10 min')]

# Rotación semanal según la categoría de IMC
ROTACION = {
    'bajo': ['fuerza', 'fuerza', 'movilidad'],
    'normal': ['fuerza', 'cardio', 'fuerza', 'cardio'],
    'sobrepeso': ['cardio', 'fuerza', 'cardio', 'movilidad'],
    'obesidad': ['bajo_impacto', 'bajo_impacto', 'movilidad'],
}
TITULOS = {'fuerza': 'Fuerza con peso corporal', 'cardio': 'Cardio moderado',
           'bajo_impacto': 'Bajo impacto', 'movilidad': 'Movilidad y estiramiento'}
INTENSIDAD_TIPO = {'fuerza': 'media', 'cardio': 'media', 'bajo_impacto': 'baja', 'movilidad': 'baja'}


def _lugar(lugar_entrenamiento):
    return lugar_entrenamiento if lugar_entrenamiento in ('casa', 'gimnasio', 'aire_libre') else 'casa'


def _conservador(datos):
    """True si hay que limitar a intensidad baja (lesión o IMC en rango de consulta profesional)."""
    imc = datos.get('imc')
    return bool(datos.get('tiene_lesion')) or (imc is not None and (imc < 16 or imc >= 35))


def minutos_disponibles(datos, dia):
    """Minutos útiles de ejercicio del día: el hueco más largo menos un margen. 0 si no hay hueco."""
    ventanas = (datos.get('ventanas_libres') or {}).get(dia) or []
    mayor = max((v['minutos'] for v in ventanas), default=0)
    return max(0, min(DURACION_MAX, mayor - MARGEN_MIN))


def rutina_base(datos, dia, indice_sesion):
    """Rutina por reglas para `dia`, o None si no hay tiempo suficiente."""
    minutos = minutos_disponibles(datos, dia)
    if minutos < DURACION_MIN:
        return None
    lugar = _lugar(datos.get('lugar_entrenamiento'))
    categoria = 'obesidad' if _conservador(datos) else datos.get('categoria_imc', 'normal')
    rotacion = ROTACION.get(categoria, ROTACION['normal'])
    tipo = rotacion[indice_sesion % len(rotacion)]
    bloque = MOVILIDAD if tipo == 'movilidad' else {'fuerza': FUERZA, 'cardio': CARDIO,
                                                     'bajo_impacto': BAJO_IMPACTO}[tipo][lugar]
    objetivo_min = min(minutos, 20 if tipo == 'movilidad' else 45)
    con_marco = objetivo_min >= 20
    cabe = max(1, (objetivo_min - (10 if con_marco else 0)) // 6)  # ~6 min por ejercicio
    ejercicios = [{'nombre': n, 'detalle': d} for n, d in bloque[:cabe]]
    if con_marco:
        ejercicios = [dict(CALENTAMIENTO)] + ejercicios + [dict(ENFRIAMIENTO)]
    return {
        'titulo': TITULOS[tipo],
        'duracion_min': objetivo_min,
        'intensidad': INTENSIDAD_TIPO[tipo],
        'ejercicios': ejercicios[:MAX_EJERCICIOS],
    }


def texto_resumen(rutina, ventanas_txt):
    """Texto corto de la actividad (compatible con el campo `actividad` ya existente)."""
    base = f"{rutina['titulo']} · {rutina['duracion_min']} min · intensidad {rutina['intensidad']}"
    return f"{ventanas_txt}: {base}" if ventanas_txt else base


def _limpiar(valor, largo):
    if not isinstance(valor, str):
        return ''
    return re.sub(r'\s+', ' ', valor).strip()[:largo]


def validar_rutina(bruto, datos, dia):
    """Normaliza la rutina propuesta por la IA. Devuelve un dict válido o None si no sirve
    (quien llama usa entonces la rutina base)."""
    if not isinstance(bruto, dict):
        return None
    maximo = minutos_disponibles(datos, dia)
    if maximo < DURACION_MIN:
        return None
    titulo = _limpiar(bruto.get('titulo'), 60)
    duracion = bruto.get('duracion_min')
    if not titulo or isinstance(duracion, bool) or not isinstance(duracion, (int, float)):
        return None
    duracion = int(duracion)
    if duracion < DURACION_MIN:
        return None
    duracion = min(duracion, maximo)  # regla dura: nunca más que el hueco disponible
    intensidad = bruto.get('intensidad')
    if intensidad not in INTENSIDADES:
        intensidad = 'baja'
    if _conservador(datos):
        intensidad = 'baja'  # regla dura: lesión o IMC extremo → solo intensidad baja
    ejercicios = []
    lista = bruto.get('ejercicios')
    for e in lista if isinstance(lista, list) else []:
        if not isinstance(e, dict):
            continue
        nombre, detalle = _limpiar(e.get('nombre'), 60), _limpiar(e.get('detalle'), 90)
        if nombre:
            ejercicios.append({'nombre': nombre, 'detalle': detalle})
    if not ejercicios:
        return None
    return {'titulo': titulo, 'duracion_min': duracion, 'intensidad': intensidad,
            'ejercicios': ejercicios[:MAX_EJERCICIOS]}
