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

# Módulos de 35 minutos (cada bloque de 70 min son dos módulos seguidos).
# Los módulos 13 y 14 (tarde) se deducen del patrón; confirmar con el horario real de SIGA.
MODULOS = [
    (1, '8:15', '8:50'), (2, '8:50', '9:25'),
    (3, '9:40', '10:15'), (4, '10:15', '10:50'),
    (5, '11:05', '11:40'), (6, '11:40', '12:15'),
    (7, '12:30', '13:05'), (8, '13:05', '13:40'),
    (9, '14:40', '15:15'), (10, '15:15', '15:50'),
    (11, '16:05', '16:40'), (12, '16:40', '17:15'),
    (13, '17:30', '18:05'), (14, '18:05', '18:40'),
]
MODULO_TEXTO = {n: f"{i}-{f}" for n, i, f in MODULOS}
DIAS_CORTOS = {'lunes': 'Lun', 'martes': 'Mar', 'miercoles': 'Mié', 'jueves': 'Jue',
               'viernes': 'Vie', 'sabado': 'Sáb', 'domingo': 'Dom'}

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
    ('familia', 'Cocina otra persona (familia, residencia, casino)'),
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
