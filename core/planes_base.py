"""Plan base (por reglas) usado como respaldo cuando no hay plan de IA.

Las comidas se copiaron tal cual desde la vista original.
"""

from .horarios import ventanas_texto

AVISO_SALUD = (
    "Esta propuesta es orientativa y no reemplaza la opinión de un médico o "
    "nutricionista. Si tienes alguna condición de salud, consúltalo antes de cambiar tu alimentación o rutina."
)

# Perfiles P1-P9 (meta según IMC x nivel de actividad) con porciones y colación.
# Contenido aportado por Felipe (rama feature/backend-recomendador), según la pauta del grupo.
PERFILES = {
    'P1': {
        'meta': 'ganar', 'actividad': 'leve',
        'etiqueta': 'P1: Ganar peso (Actividad baja)',
        'dias': {
            'lunes': {'desayuno': 'Pan con palta y huevo (2 rebanadas pan integral, palta, 1 huevo revuelto y 1 vaso de leche)', 'almuerzo': 'Pollo con arroz y ensalada (1 presa al horno, 1 taza de arroz y ensalada con aceite de oliva)', 'once': 'Sándwich de queso y jamón (2 panes con queso, jamón y palta. Té o leche)', 'colacion': 'Frutos secos con pasas (1 puñado de nueces/almendras con pasas)'},
            'martes': {'desayuno': 'Avena con leche y plátano (1 taza de avena en leche entera, 1 plátano y nueces)', 'almuerzo': 'Lentejas con arroz y huevo (1 plato de lentejas, 1/2 taza de arroz y 1 huevo cocido)', 'once': 'Yogur con fruta y frutos secos (1 yogur entero, fruta picada y frutos secos)', 'colacion': 'Batido de plátano (1 plátano licuado con leche entera y mantequilla de maní)'},
            'miercoles': {'desayuno': 'Tostadas con queso y fruta (2 tostadas con queso, 1 fruta y 1 vaso de leche)', 'almuerzo': 'Carne con puré (1 trozo de carne guisada, 1 taza de puré y ensalada de tomate)', 'once': 'Pan con palta y huevo (2 panes con palta y huevo cocido, 1 vaso de leche)', 'colacion': 'Yogur con avena (1 yogur entero con 1 cda. de avena)'},
            'jueves': {'desayuno': 'Yogur con granola y fruta (1 yogur entero con granola y plátano)', 'almuerzo': 'Fideos con salsa de carne (1 plato de fideos con carne molida y verduras. Postre: 1 fruta)', 'once': 'Sándwich de pollo (2 panes con pollo desmenuzado, palta y tomate)', 'colacion': 'Pan con mantequilla de maní (1 pan con mantequilla de maní)'},
            'viernes': {'desayuno': 'Panqueques de avena (2 panqueques de avena, huevo y plátano con miel y leche)', 'almuerzo': 'Pescado con papas (1 filete de pescado al horno, 2 papas cocidas y ensalada)', 'once': 'Tostadas con queso y mermelada (2 tostadas con queso fresco y mermelada + leche)', 'colacion': 'Fruta con queso (1 fruta de temporada y 1 lámina de queso)'},
            'sabado': {'desayuno': 'Huevos con pan y jugo (2 huevos revueltos, 2 panes, palta y jugo natural)', 'almuerzo': 'Cazuela de pollo (1 plato con pollo, papa, choclo, zapallo y 1/2 taza de arroz)', 'once': 'Panqueques con plátano (2 panqueques con plátano y miel + leche)', 'colacion': 'Galletas de avena (2 galletas de avena y 1 vaso de leche)'},
            'domingo': {'desayuno': 'Pan con mantequilla de maní (2 rebanadas con mantequilla de maní, plátano y leche)', 'almuerzo': 'Porotos con fideos (1 plato de porotos con fideos y zapallo, ensalada y fruta)', 'once': 'Pan con queso y huevo (2 panes con queso derretido y huevo revuelto + leche)', 'colacion': 'Plátano con yogur (1 plátano con yogur entero y miel)'},
        },
    },
    'P2': {
        'meta': 'ganar', 'actividad': 'moderada',
        'etiqueta': 'P2: Ganar peso (Actividad media)',
        'dias': {
            'lunes': {'desayuno': 'Pan con palta y huevo (3 rebanadas pan integral, palta, 2 huevos revueltos y leche)', 'almuerzo': 'Pollo con arroz y ensalada (1 presa de pollo, 1.5 tazas de arroz y ensalada)', 'once': 'Sándwich de queso y jamón (2 panes con queso, jamón y palta + leche)', 'colacion': 'Frutos secos con pasas (1 puñado de nueces o almendras con pasas)'},
            'martes': {'desayuno': 'Avena con leche y plátano (1.5 tazas de avena en leche entera, plátano y nueces)', 'almuerzo': 'Lentejas con arroz y huevo (1 plato grande de lentejas, 1/2 taza de arroz y huevo)', 'once': 'Yogur con fruta y frutos secos (1 yogur entero, fruta picada y frutos secos)', 'colacion': 'Batido de plátano (1 plátano licuado con leche y mantequilla de maní)'},
            'miercoles': {'desayuno': 'Tostadas con queso y fruta (3 tostadas con queso, 1 fruta y 1 vaso de leche)', 'almuerzo': 'Carne con puré (1 trozo de carne, 1.5 tazas de puré y ensalada de tomate)', 'once': 'Pan con palta y huevo (2 panes con palta y huevo cocido + leche)', 'colacion': 'Yogur con avena (1 yogur entero con 2 cdas. de avena)'},
            'jueves': {'desayuno': 'Yogur con granola y fruta (1 yogur entero con 4 cdas. de granola y plátano)', 'almuerzo': 'Fideos con salsa de carne (1.5 platos de fideos con carne molida y verduras + fruta)', 'once': 'Sándwich de pollo (2 panes con pollo desmenuzado, palta y tomate)', 'colacion': 'Pan con mantequilla de maní (1 pan con mantequilla de maní)'},
            'viernes': {'desayuno': 'Panqueques de avena (3 panqueques de avena, huevo y plátano con miel + leche)', 'almuerzo': 'Pescado con papas (1 filete de pescado al horno, 3 papas cocidas y ensalada)', 'once': 'Tostadas con queso y mermelada (3 tostadas con queso fresco y mermelada + leche)', 'colacion': 'Fruta con queso (1 fruta y 2 láminas de queso)'},
            'sabado': {'desayuno': 'Huevos con pan y jugo (2 huevos revueltos, 3 panes, palta y jugo natural)', 'almuerzo': 'Cazuela de pollo (1 plato grande con pollo, papa, choclo, zapallo y 1 taza de arroz)', 'once': 'Panqueques con plátano (3 panqueques con plátano y miel + leche)', 'colacion': 'Galletas de avena (3 galletas de avena y 1 vaso de leche)'},
            'domingo': {'desayuno': 'Pan con mantequilla de maní (3 rebanadas con mantequilla de maní y plátano + leche)', 'almuerzo': 'Porotos con fideos (1 plato grande de porotos con fideos, zapallo, ensalada y fruta)', 'once': 'Pan con queso y huevo (2 panes con queso derretido y huevo revuelto + leche)', 'colacion': 'Plátano con yogur (1 plátano con yogur entero y miel)'},
        },
    },
    'P3': {
        'meta': 'ganar', 'actividad': 'alta',
        'etiqueta': 'P3: Ganar peso (Actividad alta)',
        'dias': {
            'lunes': {'desayuno': 'Pan con palta y huevo (3 rebanadas pan integral, palta, 2 huevos revueltos y leche)', 'almuerzo': 'Pollo con arroz y ensalada (1 presa de pollo, 2 tazas de arroz y ensalada)', 'once': 'Sándwich de queso y jamón (3 panes con queso, jamón y palta + leche)', 'colacion': 'Frutos secos con pasas (2 puñados de nueces o almendras con pasas)'},
            'martes': {'desayuno': 'Avena con leche y plátano (2 tazas de avena en leche entera, plátano y nueces)', 'almuerzo': 'Lentejas con arroz y huevo (1 plato grande de lentejas, 1 taza de arroz y huevo)', 'once': 'Yogur con fruta y frutos secos (1 yogur entero, fruta y 2 puñados de frutos secos)', 'colacion': 'Batido de plátano (1 plátano con leche entera y mantequilla de maní)'},
            'miercoles': {'desayuno': 'Tostadas con queso y fruta (4 tostadas con queso, 1 fruta y 1 vaso de leche)', 'almuerzo': 'Carne con puré (1 trozo de carne, 2 tazas de puré y ensalada de tomate)', 'once': 'Pan con palta y huevo (3 panes con palta y huevo cocido + leche)', 'colacion': 'Yogur con avena (1 yogur entero con 3 cdas. de avena)'},
            'jueves': {'desayuno': 'Yogur con granola y fruta (1 yogur entero con 6 cdas. de granola y plátano)', 'almuerzo': 'Fideos con salsa de carne (2 platos de fideos con carne molida, verduras + fruta)', 'once': 'Sándwich de pollo (3 panes con pollo desmenuzado, palta y tomate)', 'colacion': 'Pan con mantequilla de maní (2 panes con mantequilla de maní)'},
            'viernes': {'desayuno': 'Panqueques de avena (4 panqueques de avena, huevo y plátano con miel + leche)', 'almuerzo': 'Pescado con papas (1 filete de pescado al horno, 4 papas cocidas y ensalada)', 'once': 'Tostadas con queso y mermelada (4 tostadas con queso fresco y mermelada + leche)', 'colacion': 'Fruta con queso (1 fruta de temporada y 2 láminas de queso)'},
            'sabado': {'desayuno': 'Huevos con pan y jugo (3 huevos revueltos, 3 panes, palta y jugo natural)', 'almuerzo': 'Cazuela de pollo (1 plato grande con pollo, papa, choclo, zapallo y 1 taza de arroz)', 'once': 'Panqueques con plátano (3 panqueques con plátano y miel + leche)', 'colacion': 'Galletas de avena (4 galletas de avena y 1 vaso de leche)'},
            'domingo': {'desayuno': 'Pan con mantequilla de maní (3 rebanadas con mantequilla de maní y plátano + leche)', 'almuerzo': 'Porotos con fideos (1 plato grande de porotos con fideos, zapallo, ensalada y fruta)', 'once': 'Pan con queso y huevo (3 panes con queso derretido y huevo revuelto + leche)', 'colacion': 'Plátano con yogur (1 plátano con yogur entero y miel)'},
        },
    },
    'P4': {
        'meta': 'mantener', 'actividad': 'leve',
        'etiqueta': 'P4: Mantener peso (Actividad baja)',
        'dias': {
            'lunes': {'desayuno': 'Pan integral con palta (1 rebanada con palta y 1 huevo, té o café)', 'almuerzo': 'Pollo con arroz y ensalada (1 presa de pollo sin piel, 1/2 taza de arroz y ensalada)', 'once': 'Sándwich de pavo y palta (1 pan con pavo, palta y tomate)', 'colacion': 'Fruta de temporada (1 manzana, pera o naranja)'},
            'martes': {'desayuno': 'Yogur con fruta y avena (1 yogur natural, fruta y 2 cdas. de avena)', 'almuerzo': 'Lentejas con verduras (1 plato de lentejas con zanahoria y zapallo + ensalada)', 'once': 'Yogur con granola (1 yogur natural con 1 cda. de granola)', 'colacion': 'Yogur natural (1 yogur natural sin azúcar con fruta)'},
            'miercoles': {'desayuno': 'Pan con queso fresco (1 pan con queso fresco y tomate + té)', 'almuerzo': 'Pescado al horno con ensalada (1 filete de pescado, ensalada y 1 papa cocida)', 'once': 'Pan con queso fresco (1 pan con queso fresco y tomate)', 'colacion': 'Zanahoria con hummus (Palitos de zanahoria con 1 cda. de hummus)'},
            'jueves': {'desayuno': 'Avena con leche (1 taza de avena en leche semidescremada, fruta y canela)', 'almuerzo': 'Fideos con atún y verduras (1/2 plato de fideos con atún, tomate y verduras)', 'once': 'Fruta con almendras (1 fruta y 5 almendras)', 'colacion': 'Frutos secos (1 puñado de nueces o almendras)'},
            'viernes': {'desayuno': 'Tostadas con huevo y fruta (2 rebanadas pan integral, 1 huevo y fruta)', 'almuerzo': 'Carne magra con arroz (1 trozo de carne, 1/2 taza de arroz y verduras salteadas)', 'once': 'Huevos revueltos con verduras (1 huevo revuelto con tomate, cebolla y pan)', 'colacion': 'Plátano (1 plátano solo)'},
            'sabado': {'desayuno': 'Pan con queso fresco y tomate (1 pan con queso fresco y tomate + fruta)', 'almuerzo': 'Cazuela de vacuno (1 plato mediano con carne, papa, choclo y zapallo)', 'once': 'Sándwich de atún (1 pan con atún, tomate y lechuga)', 'colacion': 'Galletas de avena (1 galleta de avena casera y té)'},
            'domingo': {'desayuno': 'Panqueques de avena (1 panqueque de avena y plátano con yogur natural)', 'almuerzo': 'Garbanzos con arroz (1 plato de garbanzos, 1/2 taza de arroz y ensalada)', 'once': 'Pan con huevo (1 pan con huevo revuelto y tomate + té)', 'colacion': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)'},
        },
    },
    'P5': {
        'meta': 'mantener', 'actividad': 'moderada',
        'etiqueta': 'P5: Mantener peso (Actividad media)',
        'dias': {
            'lunes': {'desayuno': 'Pan integral con palta (2 rebanadas pan integral con palta y 1 huevo)', 'almuerzo': 'Pollo con arroz y ensalada (1 presa de pollo sin piel, 3/4 taza de arroz y ensalada)', 'once': 'Sándwich de pavo y palta (1 pan con pechuga de pavo, palta y tomate)', 'colacion': 'Fruta de temporada (1 manzana, pera o naranja)'},
            'martes': {'desayuno': 'Yogur con fruta y avena (1 yogur natural, fruta y 3 cdas. de avena)', 'almuerzo': 'Lentejas con verduras (1 plato de lentejas con verduras y ensalada)', 'once': 'Yogur con granola (1 yogur natural con 2 cdas. de granola)', 'colacion': 'Yogur natural (1 yogur natural con fruta)'},
            'miercoles': {'desayuno': 'Tostadas con huevo y fruta (2 rebanadas pan integral, 1 huevo y fruta)', 'almuerzo': 'Pescado al horno con ensalada (1 filete, ensalada y 1 papa cocida)', 'once': 'Pan con queso fresco (1 pan con queso fresco y tomate)', 'colacion': 'Zanahoria con hummus (Palitos de zanahoria con 2 cdas. de hummus)'},
            'jueves': {'desayuno': 'Avena con leche (1 taza de avena en leche semidescremada, fruta y canela)', 'almuerzo': 'Fideos con atún y verduras (1 plato de fideos con atún y verduras)', 'once': 'Fruta con almendras (1 fruta y 8 almendras)', 'colacion': 'Frutos secos (1 puñado de nueces o almendras)'},
            'viernes': {'desayuno': 'Pan con queso fresco y tomate (2 panes con queso fresco, tomate y fruta)', 'almuerzo': 'Carne magra con arroz (1 trozo de carne, 3/4 taza de arroz y verduras)', 'once': 'Tostadas con palta (2 tostadas con palta y 1 huevo cocido)', 'colacion': 'Plátano (1 plátano solo)'},
            'sabado': {'desayuno': 'Huevos revueltos con verduras (2 huevos revueltos con tomate, cebolla y 2 panes)', 'almuerzo': 'Cazuela de vacuno (1 plato mediano con carne, papa, choclo y zapallo)', 'once': 'Sándwich de atún (1 pan con atún, tomate y lechuga)', 'colacion': 'Galletas de avena (2 galletas de avena caseras y té)'},
            'domingo': {'desayuno': 'Panqueques de avena (2 panqueques de avena y plátano con yogur natural)', 'almuerzo': 'Garbanzos con arroz (1 plato de garbanzos, 1/2 taza de arroz y ensalada)', 'once': 'Pan con huevo (1 pan con huevo revuelto y tomate)', 'colacion': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)'},
        },
    },
    'P6': {
        'meta': 'mantener', 'actividad': 'alta',
        'etiqueta': 'P6: Mantener peso (Actividad alta)',
        'dias': {
            'lunes': {'desayuno': 'Pan integral con palta (2 rebanadas pan integral con palta y 2 huevos)', 'almuerzo': 'Pollo con arroz y ensalada (1 presa de pollo sin piel, 1 taza de arroz y ensalada)', 'once': 'Sándwich de pavo y palta (2 panes con pavo, palta y tomate)', 'colacion': 'Fruta de temporada (1 manzana, pera o naranja)'},
            'martes': {'desayuno': 'Yogur con fruta y avena (1 yogur natural, fruta y 4 cdas. de avena)', 'almuerzo': 'Lentejas con verduras (1 plato grande de lentejas con verduras y ensalada)', 'once': 'Yogur con granola (1 yogur natural con 3 cdas. de granola)', 'colacion': 'Yogur natural (1 yogur natural con fruta y 1 cda. de avena)'},
            'miercoles': {'desayuno': 'Tostadas con huevo y fruta (3 rebanadas pan integral, 1 huevo y fruta)', 'almuerzo': 'Pescado al horno con ensalada (1 filete, ensalada y 2 papas cocidas)', 'once': 'Pan con queso fresco (2 panes con queso fresco y tomate)', 'colacion': 'Zanahoria con hummus (Palitos de zanahoria con 3 cdas. de hummus)'},
            'jueves': {'desayuno': 'Avena con leche (1.5 tazas de avena en leche semidescremada, fruta y canela)', 'almuerzo': 'Fideos con atún y verduras (1.5 platos de fideos con atún y verduras)', 'once': 'Fruta con almendras (1 fruta y 10 almendras)', 'colacion': 'Frutos secos (1 puñado de nueces o almendras)'},
            'viernes': {'desayuno': 'Pan con queso fresco y tomate (2 panes con queso fresco, tomate y fruta)', 'almuerzo': 'Carne magra con arroz (1 trozo de carne, 1 taza de arroz y verduras)', 'once': 'Tostadas con palta (2 tostadas con palta y 1 huevo cocido)', 'colacion': 'Plátano con mantequilla de maní (1 plátano con 1 cda. de mantequilla de maní)'},
            'sabado': {'desayuno': 'Huevos revueltos con verduras (3 huevos revueltos con tomate, cebolla y 2 panes)', 'almuerzo': 'Cazuela de vacuno (1 plato grande con carne, papa, choclo y zapallo)', 'once': 'Sándwich de atún (2 panes con atún, tomate y lechuga)', 'colacion': 'Galletas de avena (3 galletas de avena caseras y té)'},
            'domingo': {'desayuno': 'Panqueques de avena (3 panqueques de avena y plátano con yogur natural)', 'almuerzo': 'Garbanzos con arroz (1 plato grande de garbanzos, 1 taza de arroz y ensalada)', 'once': 'Pan con huevo (2 panes con huevo revuelto y tomate)', 'colacion': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)'},
        },
    },
    'P7': {
        'meta': 'reducir', 'actividad': 'leve',
        'etiqueta': 'P7: Reducir grasa corporal (Actividad baja)',
        'dias': {
            'lunes': {'desayuno': 'Pan integral con queso fresco (1 rebanada con queso fresco, tomate, 1 huevo cocido)', 'almuerzo': 'Pollo a la plancha con ensalada (1 presa sin piel, ensalada y 1/2 taza de arroz)', 'once': 'Pan integral con palta (1 rebanada con 2 cdas. de palta)', 'colacion': 'Fruta entera (1 manzana, pera o naranja)'},
            'martes': {'desayuno': 'Yogur natural con fruta (1 yogur sin azúcar, 1/2 taza de fruta y avena)', 'almuerzo': 'Lentejas con verduras (1 plato mediano de lentejas con zapallo, zanahoria y ensalada)', 'once': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)', 'colacion': 'Verduras crudas (Zanahoria, pepino o apio en palitos con limón)'},
            'miercoles': {'desayuno': 'Tostada con huevo revuelto (1 pan integral con 1 huevo revuelto y tomate)', 'almuerzo': 'Pescado al horno con verduras (1 filete, 1 taza de verduras al vapor y 1/2 taza de quinoa)', 'once': 'Pan integral con pavo (1 pan integral con pechuga de pavo y tomate)', 'colacion': 'Yogur natural (1 yogur natural sin azúcar)'},
            'jueves': {'desayuno': 'Avena con fruta (1/2 taza de avena en agua o leche descremada con manzana)', 'almuerzo': 'Ensalada con pollo (Lechuga, tomate, pollo desmenuzado, 1/2 taza de garbanzos y limón)', 'once': 'Yogur con fruta (1 yogur natural sin azúcar con fruta picada)', 'colacion': 'Zanahoria con hummus (Palitos de zanahoria con 1 cda. de hummus)'},
            'viernes': {'desayuno': 'Pan con palta (1 rebanada pan integral con 2 cdas. de palta y fruta)', 'almuerzo': 'Atún con legumbres y ensalada (1/2 lata de atún, 1/2 taza de porotos/garbanzos y ensalada)', 'once': 'Pan con queso fresco (1 rebanada con queso fresco y pepino)', 'colacion': 'Fruta con almendras (1 fruta y 3 almendras)'},
            'sabado': {'desayuno': 'Huevos con verduras (1 huevo revuelto con espinaca o tomate y pan integral)', 'almuerzo': 'Carne magra con verduras (1 trozo pequeño de carne, verduras y 1 papa cocida)', 'once': 'Tostada con atún (1 tostada integral con atún y tomate)', 'colacion': 'Huevo cocido (1 huevo cocido con tomate)'},
            'domingo': {'desayuno': 'Yogur con avena y plátano (1 yogur natural con avena y 1/2 plátano)', 'almuerzo': 'Sopa de verduras con pollo (1 plato de sopa con pollo, zapallo, zanahoria y choclo + ensalada)', 'once': 'Fruta con almendras (1 fruta y 3 almendras)', 'colacion': 'Fruta picada con canela (1 taza de fruta picada con canela)'},
        },
    },
    'P8': {
        'meta': 'reducir', 'actividad': 'moderada',
        'etiqueta': 'P8: Reducir grasa corporal (Actividad media)',
        'dias': {
            'lunes': {'desayuno': 'Pan integral con queso fresco (1 rebanada con queso fresco, tomate, 1 huevo cocido)', 'almuerzo': 'Pollo a la plancha con ensalada (1 presa sin piel, ensalada y 1/2 taza de arroz)', 'once': 'Pan integral con palta (1 rebanada con 2 cdas. de palta)', 'colacion': 'Fruta entera (1 manzana, pera o naranja)'},
            'martes': {'desayuno': 'Yogur natural con fruta (1 yogur sin azúcar, fruta y 2 cdas. de avena)', 'almuerzo': 'Lentejas con verduras (1 plato mediano de lentejas con zapallo y ensalada)', 'once': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)', 'colacion': 'Verduras crudas (Zanahoria, pepino o apio en palitos con limón)'},
            'miercoles': {'desayuno': 'Tostada con huevo revuelto (2 rebanadas pan integral con 1 huevo revuelto y tomate)', 'almuerzo': 'Pescado al horno con verduras (1 filete, 1.5 tazas de verduras al vapor y 1/2 taza de quinoa)', 'once': 'Pan integral con pavo (1 pan integral con pechuga de pavo y tomate)', 'colacion': 'Yogur natural (1 yogur natural sin azúcar)'},
            'jueves': {'desayuno': 'Avena con fruta (1/2 taza de avena en agua o leche descremada con manzana)', 'almuerzo': 'Ensalada con pollo (Lechuga, tomate, pollo desmenuzado, 1/2 taza de garbanzos y limón)', 'once': 'Yogur con fruta (1 yogur natural sin azúcar con fruta picada)', 'colacion': 'Zanahoria con hummus (Palitos de zanahoria con 2 cdas. de hummus)'},
            'viernes': {'desayuno': 'Pan con palta (1 rebanada pan integral con 2 cdas. de palta y fruta)', 'almuerzo': 'Atún con legumbres y ensalada (1 lata de atún, 1/2 taza de porotos/garbanzos y ensalada)', 'once': 'Pan con queso fresco (1 rebanada con queso fresco y pepino)', 'colacion': 'Fruta con almendras (1 fruta y 5 almendras)'},
            'sabado': {'desayuno': 'Huevos con verduras (2 huevos revueltos con espinaca o tomate y pan integral)', 'almuerzo': 'Carne magra con verduras (1 trozo pequeño de carne, verduras y 1 papa cocida)', 'once': 'Tostada con atún (1 tostada integral con atún y tomate)', 'colacion': 'Huevo cocido (1 huevo cocido con tomate)'},
            'domingo': {'desayuno': 'Yogur con avena y plátano (1 yogur natural con 3 cdas. de avena y 1/2 plátano)', 'almuerzo': 'Sopa de verduras con pollo (1 plato de sopa con pollo, zapallo, zanahoria y choclo + ensalada)', 'once': 'Fruta con almendras (1 fruta y 5 almendras)', 'colacion': 'Fruta picada con canela (1 taza de fruta picada con canela)'},
        },
    },
    'P9': {
        'meta': 'reducir', 'actividad': 'alta',
        'etiqueta': 'P9: Reducir grasa corporal (Actividad alta)',
        'dias': {
            'lunes': {'desayuno': 'Pan integral con queso fresco (2 rebanadas con queso fresco, tomate, 1 huevo cocido)', 'almuerzo': 'Pollo a la plancha con ensalada (1 presa sin piel, ensalada y 3/4 taza de arroz)', 'once': 'Pan integral con palta (2 rebanadas con 2 cdas. de palta)', 'colacion': 'Fruta entera (1 manzana, pera o naranja)'},
            'martes': {'desayuno': 'Yogur natural con fruta (1 yogur sin azúcar, fruta y 3 cdas. de avena)', 'almuerzo': 'Lentejas con verduras (1 plato de lentejas con zapallo, zanahoria y ensalada)', 'once': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)', 'colacion': 'Verduras crudas (Zanahoria, pepino o apio en palitos con limón)'},
            'miercoles': {'desayuno': 'Tostada con huevo revuelto (2 rebanadas pan integral con 2 huevos revueltos y tomate)', 'almuerzo': 'Pescado al horno con verduras (1 filete, 2 tazas de verduras al vapor y 1/2 taza de quinoa)', 'once': 'Pan integral con pavo (2 panes integrales con pechuga de pavo y tomate)', 'colacion': 'Yogur natural / Zanahoria con hummus (1 yogur natural sin azúcar / Palitos con hummus)'},
            'jueves': {'desayuno': 'Avena con fruta (1 taza de avena en agua o leche descremada con manzana)', 'almuerzo': 'Ensalada con pollo (Lechuga, tomate, pollo desmenuzado, 1/2 taza de garbanzos y limón)', 'once': 'Yogur con fruta (1 yogur natural sin azúcar con fruta picada)', 'colacion': 'Zanahoria con hummus (Palitos de zanahoria con 2 cdas. de hummus)'},
            'viernes': {'desayuno': 'Pan con palta (2 rebanadas pan integral con 2 cdas. de palta y fruta)', 'almuerzo': 'Atún con legumbres y ensalada (1 lata de atún, 1 taza de porotos/garbanzos y ensalada)', 'once': 'Pan con queso fresco (2 rebanadas con queso fresco y pepino)', 'colacion': 'Fruta con almendras (1 fruta y 5 almendras)'},
            'sabado': {'desayuno': 'Huevos con verduras (2 huevos revueltos con espinaca o tomate y 2 panes integrales)', 'almuerzo': 'Carne magra con verduras (1 trozo de carne, verduras y 2 papas cocidas)', 'once': 'Tostada con atún (2 tostadas integrales con atún y tomate)', 'colacion': 'Huevo cocido (1 huevo cocido con tomate)'},
            'domingo': {'desayuno': 'Yogur con avena y plátano (1 yogur natural con 4 cdas. de avena y 1/2 plátano)', 'almuerzo': 'Sopa de verduras con pollo (1 plato grande de sopa con pollo, verduras y choclo + ensalada)', 'once': 'Fruta con almendras (1 fruta y 8 almendras)', 'colacion': 'Fruta picada con canela (1.5 tazas de fruta picada con canela)'},
        },
    },
}


def meta_por_imc(imc):
    """'ganar' (<18,5), 'mantener' (18,5 a <25) o 'reducir' (>=25)."""
    if imc < 18.5:
        return 'ganar'
    if imc < 25:
        return 'mantener'
    return 'reducir'


def perfil_alimentacion(imc, actividad):
    """Devuelve (codigo, perfil) del P1-P9 que corresponde al IMC y al nivel de actividad."""
    meta = meta_por_imc(imc)
    if actividad not in ('leve', 'moderada', 'alta'):
        actividad = 'moderada'
    for cod, pf in PERFILES.items():
        if pf['meta'] == meta and pf['actividad'] == actividad:
            return cod, pf
    raise KeyError((meta, actividad))


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
        lista = ventanas_texto(bloques.get(dia))
        if not lista:
            resultado[dia.capitalize()] = SIN_TIEMPO
            continue
        etiqueta = "Bloque" if len(lista) == 1 else "Bloques"
        resultado[dia.capitalize()] = f"{etiqueta} {' y '.join(lista)}: {EJERCICIO_POR_CATEGORIA[categoria]}"
    return resultado


def plan_respaldo(datos):
    """Plan por reglas con el mismo formato que el de la IA. `datos` viene de servicios.construir_datos."""
    from .constantes import DIAS
    categoria = clasificar_imc(datos['imc'])
    _cod, perfil_pdf = perfil_alimentacion(datos['imc'], datos.get('actividad_fisica', 'moderada'))
    cat_ejercicio = 'obesidad' if datos.get('tiene_lesion') else categoria  # bajo impacto si hay lesión
    ejercicios = ejercicios_base(cat_ejercicio, datos.get('bloques_libres', {}))
    dias = {}
    for dia in DIAS:
        c = perfil_pdf['dias'][dia]
        dias[dia] = {
            'desayuno': c['desayuno'], 'almuerzo': c['almuerzo'], 'once': c['once'],
            'colacion': c['colacion'],
            'actividad': ejercicios[dia.capitalize()],
        }
    avisos = []
    if datos.get('tipo_dieta') != 'omnivora' or datos.get('alergias'):
        avisos.append("Este menú es genérico y NO se adaptó a tu tipo de dieta ni a tus alergias; "
                      "revísalo antes de seguirlo.")
    if datos.get('tiene_lesion'):
        avisos.append("Indicaste una molestia o lesión: se usó ejercicio de bajo impacto. "
                      "Consulta a un profesional antes de entrenar.")
    return {
        'resumen': perfil_pdf['etiqueta'],
        'dias': dias,
        'consejos': [],
        'advertencia': ' '.join(avisos) or None,
    }
