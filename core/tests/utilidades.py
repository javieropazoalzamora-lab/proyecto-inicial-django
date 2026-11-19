"""Datos y ayudas compartidas por las pruebas."""
import json
import os
from unittest import mock

from ..constantes import DIAS


BASE = {
    'mayor_de_edad': 'on', 'actividad_fisica': 'moderada', 'objetivo': 'mantener', 'tipo_dieta': 'omnivora', 'alergias': '',
    'presupuesto': 'medio', 'tiempo_cocina': 'normal', 'lugar_entrenamiento': 'casa',
}


class SinClaveMixin:
    """Los tests nunca llaman a la API real."""
    def setUp(self):
        super().setUp()
        p = mock.patch.dict(os.environ, {}, clear=False)
        p.start()
        os.environ.pop('GEMINI_API_KEY', None)
        self.addCleanup(p.stop)


def plan_json(**cambios):
    dias = [{'dia': d, 'desayuno': 'Avena con fruta', 'almuerzo': 'Lentejas con arroz',
             'once': 'Pan con palta', 'colacion': 'Fruta', 'actividad': 'Trote suave 30 min'} for d in DIAS]
    obj = {'resumen': 'Plan equilibrado', 'dias': dias, 'consejos': ['Toma agua']}
    obj.update(cambios)
    return json.dumps(obj)


DATOS = {
    'imc': 22.0, 'categoria_imc': 'normal',
    'bloques_libres': {d: (['8:15-9:25'] if d in ('lunes', 'jueves') else []) for d in DIAS},
    'tiempo_transporte_min': 30, 'actividad_fisica': 'moderada', 'objetivo': 'mantener', 'tipo_dieta': 'omnivora', 'alergias': '',
    'presupuesto': 'medio', 'tiempo_cocina': 'normal', 'lugar_entrenamiento': 'casa', 'tiene_lesion': False,
}


def datos_con_ventanas(**cambios):
    d = dict(DATOS)
    d['ventanas_libres'] = {dia: ([{'inicio': '8:15', 'fin': '9:25', 'minutos': 70}] if dia in ('lunes', 'jueves') else [])
                            for dia in DIAS}
    d.update(cambios)
    return d


RUTINA_IA = {'titulo': 'Circuito casero', 'duracion_min': 40, 'intensidad': 'alta',
             'ejercicios': [{'nombre': 'Sentadillas', 'detalle': '3 x 12'}, {'nombre': 'Plancha', 'detalle': '30 s'}]}
