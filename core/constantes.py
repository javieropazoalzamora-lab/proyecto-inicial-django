"""Constantes compartidas por modelos, formularios y vistas."""

BLOQUES_VALIDOS = [
    '8:15-9:25',
    '9:40-10:50',
    '11:05-12:15',
    '12:30-13:40',
    '14:40-15:50',
    '16:05-17:15',
    '17:30-18:40',
]

DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']

ETIQUETAS_DIA = {
    'lunes': 'Lunes', 'martes': 'Martes', 'miercoles': 'Miércoles', 'jueves': 'Jueves',
    'viernes': 'Viernes', 'sabado': 'Sábado', 'domingo': 'Domingo',
}

OBJETIVOS = [
    ('bajar_grasa', 'Perder grasa / bajar de peso'),
    ('ganar_musculo', 'Ganar masa muscular'),
    ('mantener', 'Mantener mi peso'),
    ('energia', 'Mejorar energía y resistencia'),
]
DIETAS = [
    ('omnivora', 'Omnívora'),
    ('vegetariana', 'Vegetariana'),
    ('vegana', 'Vegana'),
]
PRESUPUESTOS = [
    ('bajo', 'Bajo (comida económica)'),
    ('medio', 'Medio'),
    ('alto', 'Alto'),
]
TIEMPOS_COCINA = [
    ('15min', 'Hasta 15 minutos por comida'),
    ('normal', 'Puedo cocinar con calma'),
    ('meal_prep', 'Prefiero preparar para varios días'),
]
LUGARES = [
    ('casa', 'En casa (sin equipo)'),
    ('gimnasio', 'Gimnasio'),
    ('aire_libre', 'Al aire libre'),
]

ACTIVIDADES = [
    ('leve', 'Leve (poco o ningún ejercicio frecuente)'),
    ('moderada', 'Moderada (ejercicio ligero, 2 a 3 veces por semana)'),
    ('alta', 'Alta (ejercicio intenso, 4 o más veces por semana)'),
]
