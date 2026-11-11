"""Plan base (por reglas) usado como respaldo cuando no hay plan de IA.

Las comidas se copiaron tal cual desde la vista original.
"""

AVISO_SALUD = (
    "Esta propuesta es orientativa y no reemplaza la opinión de un médico o "
    "nutricionista. Si tienes alguna condición de salud, consúltalo antes de cambiar tu alimentación o rutina."
)

PLAN_ALIMENTACION = {
    'bajo': {
        'Lunes': {'desayuno': 'Avena con leche entera, plátano y mantequilla de maní', 'almuerzo': 'Arroz, pechuga de pollo a la plancha, palta y ensalada', 'once': 'Pan con huevo revuelto y un vaso de leche'},
        'Martes': {'desayuno': 'Pan con palta y un huevo duro, vaso de leche', 'almuerzo': 'Puré de papas con carne vacuna y ensalada mixta', 'once': 'Yogurt con granola y frutos secos'},
        'Miércoles': {'desayuno': 'Pancakes de avena y plátano con miel', 'almuerzo': 'Fideos con salsa boloñesa y queso rallado', 'once': 'Té con pan y queso mantecoso'},
        'Jueves': {'desayuno': 'Batido de plátano, avena, leche y mantequilla de maní', 'almuerzo': 'Arroz con atún, huevo duro y ensalada', 'once': 'Galletas de avena con leche'},
        'Viernes': {'desayuno': 'Tostadas con mantequilla de maní y rodajas de plátano', 'almuerzo': 'Lentejas con arroz y trozos de zapallo', 'once': 'Pan con palta y un vaso de leche'},
        'Sábado': {'desayuno': 'Revuelto de huevos con jamón y pan tostado', 'almuerzo': 'Carne al horno con papas doradas y ensalada', 'once': 'Queque casero con té o leche'},
        'Domingo': {'desayuno': 'Pudín de chía con leche y frutas', 'almuerzo': 'Pescado al horno con puré y ensalada', 'once': 'Pan con queso y un vaso de jugo natural'},
    },
    'normal': {
        'Lunes': {'desayuno': 'Yogurt descremado con avena y fruta fresca', 'almuerzo': 'Pechuga de pollo con quinoa y ensalada verde', 'once': 'Infusión con tostadas integrales y quesillo'},
        'Martes': {'desayuno': 'Tostada integral con palta y huevo pochado', 'almuerzo': 'Pescado al horno con papas cocidas y brócoli', 'once': 'Fruta y un puñado de almendras'},
        'Miércoles': {'desayuno': 'Batido verde (espinaca, manzana, plátano y agua)', 'almuerzo': 'Lentejas guisadas con verduras y un huevo duro', 'once': 'Yogurt con semillas de chía'},
        'Jueves': {'desayuno': 'Pan integral con jamón de pavo y queso fresco', 'almuerzo': 'Arroz integral con carne magra y ensalada mixta', 'once': 'Té con panqueques de avena'},
        'Viernes': {'desayuno': 'Omelette de claras con espinaca y tomate', 'almuerzo': 'Fideos integrales con salsa de tomate natural y pavo', 'once': 'Infusión con galletas de arroz y palta'},
        'Sábado': {'desayuno': 'Pancakes saludables de avena y plátano', 'almuerzo': 'Carne magra a la plancha con puré de zapallo y ensalada', 'once': 'Leche con pan integral y quesillo'},
        'Domingo': {'desayuno': 'Fruta picada con yogurt natural y nueces', 'almuerzo': 'Garbanzos salteados con verduras y pollo desmenuzado', 'once': 'Infusión con tostadas y mermelada sin azúcar'},
    },
    'sobrepeso': {
        'Lunes': {'desayuno': 'Infusión sin azúcar con tostada integral y quesillo light', 'almuerzo': 'Pechuga de pollo a la plancha con ensalada abundante de lechuga y tomate', 'once': 'Yogurt descremado con infusión'},
        'Martes': {'desayuno': 'Leche descremada con frutillas', 'almuerzo': 'Merluza al horno con puré de zapallo italiano y ensalada verde', 'once': 'Infusión con pan integral y palta (porción moderada)'},
        'Miércoles': {'desayuno': 'Yogurt descremado con avena', 'almuerzo': 'Sopa de verduras y porción pequeña de carne magra con ensalada', 'once': 'Infusión con galletas de arroz y quesillo'},
        'Jueves': {'desayuno': 'Omelette de claras con champiñones', 'almuerzo': 'Ensalada grande de atún al agua con huevo duro y verduras', 'once': 'Té con tostada integral y huevo'},
        'Viernes': {'desayuno': 'Infusión con pan integral y quesillo light', 'almuerzo': 'Pollo desmenuzado con mix de verduras salteadas y quinoa', 'once': 'Yogurt descremado'},
        'Sábado': {'desayuno': 'Pudín de chía con leche descremada y frutos rojos', 'almuerzo': 'Carne magra al horno con ensalada de brócoli y coliflor', 'once': 'Infusión con tostadas integrales'},
        'Domingo': {'desayuno': 'Huevos revueltos con tomate y té', 'almuerzo': 'Pescado al vapor con espárragos y ensalada mixta', 'once': 'Infusión con pan integral y quesillo'},
    },
    'obesidad': {
        'Lunes': {'desayuno': 'Infusión sin azúcar con una tostada integral y un huevo revuelto', 'almuerzo': 'Pechuga de pollo a la plancha con gran cantidad de ensalada verde', 'once': 'Yogurt descremado sin azúcar'},
        'Martes': {'desayuno': 'Leche descremada con avena y una fruta pequeña', 'almuerzo': 'Pescado blanco al horno con zapallo italiano y brócoli al vapor', 'once': 'Infusión con pan integral y quesillo descremado'},
        'Miércoles': {'desayuno': 'Infusión con dos huevos duros', 'almuerzo': 'Ensalada verde abundante con atún al agua y media porción de legumbres', 'once': 'Yogurt descremado con semillas'},
        'Jueves': {'desayuno': 'Batido de frutos rojos con leche descremada', 'almuerzo': 'Carne magra desgrasada con ensalada mixta de pepino y lechuga', 'once': 'Infusión con galletas de arroz'},
        'Viernes': {'desayuno': 'Infusión sin azúcar con tostada integral y poca palta', 'almuerzo': 'Pechuga de pavo al horno con verduras al vapor (sin aceite)', 'once': 'Infusión con un huevo duro'},
        'Sábado': {'desayuno': 'Omelette de claras con espinaca y tomate', 'almuerzo': 'Sopa clara de verduras y filete de pescado con espárragos', 'once': 'Yogurt descremado'},
        'Domingo': {'desayuno': 'Infusión con pan integral y quesillo', 'almuerzo': 'Ensalada grande con pollo grillado y verduras cocidas', 'once': 'Infusión con tostadas integrales'},
    },
}

ETIQUETAS = {
    'bajo': "Bajo peso (Dieta hipercalórica saludable)",
    'normal': "Peso normal (Dieta equilibrada)",
    'sobrepeso': "Sobrepeso (Dieta de control calórico)",
    'obesidad': "Obesidad (Dieta hipocalórica supervisada)",
}

EJERCICIO_POR_CATEGORIA = {
    'bajo': "Rutina de fuerza moderada (ganancia muscular) + descanso intermedio.",
    'normal': "Combinado: 30 min de cardio + ejercicios de tonificación.",
    'sobrepeso': "Quema grasa: Cardio sostenido (trote suave / caminata rápida) en el bloque libre.",
    'obesidad': "Bajo impacto: Caminata activa o elíptica durante el bloque disponible.",
}

SIN_TIEMPO = "Día libre / Descanso (Sin bloques disponibles)"


def clasificar_imc(imc):
    """Devuelve la categoría ('bajo', 'normal', 'sobrepeso', 'obesidad')."""
    if imc < 18.5:
        return 'bajo'
    if imc < 25:
        return 'normal'
    if imc < 30:
        return 'sobrepeso'
    return 'obesidad'


def alerta_profesional(imc):
    """Mensaje si el IMC es extremo; None en caso contrario."""
    if imc is None:
        return None
    if imc < 16 or imc >= 35:
        return ("Tu IMC está en un rango en que conviene consultar a un profesional de la salud "
                "antes de seguir cualquier plan de alimentación o ejercicio.")
    return None


def ejercicios_base(categoria, bloques):
    """bloques: dict dia -> lista de bloques. Devuelve dict 'Dia' -> texto."""
    from .constantes import DIAS
    resultado = {}
    for dia in DIAS:
        lista = bloques.get(dia) or []
        if not lista:
            resultado[dia.capitalize()] = SIN_TIEMPO
            continue
        etiqueta = "Bloque" if len(lista) == 1 else "Bloques"
        resultado[dia.capitalize()] = f"{etiqueta} {' y '.join(lista)}: {EJERCICIO_POR_CATEGORIA[categoria]}"
    return resultado
