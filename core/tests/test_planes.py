"""Plan base por reglas (perfiles P1-P9) y rutinas de ejercicio."""
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .. import ia
from .. import planes_base
from ..constantes import DIAS
from .utilidades import BASE, SinClaveMixin, datos_con_ventanas, RUTINA_IA


class PlanesBaseTests(TestCase):
    def test_clasificacion(self):
        for imc, cat in [(17, 'bajo'), (18.5, 'normal'), (24.99, 'normal'),
                         (25, 'sobrepeso'), (30, 'obesidad')]:
            self.assertEqual(planes_base.clasificar_imc(imc), cat)

    def test_nueve_perfiles_completos(self):
        self.assertEqual(set(planes_base.PERFILES), {f'P{i}' for i in range(1, 10)})
        combos = set()
        for pf in planes_base.PERFILES.values():
            combos.add((pf['meta'], pf['actividad']))
            self.assertEqual(len(pf['dias']), 7)
            for comidas in pf['dias'].values():
                self.assertEqual(set(comidas), {'desayuno', 'almuerzo', 'once', 'colacion'})
                self.assertTrue(all(comidas.values()))
        self.assertEqual(len(combos), 9)

    def test_perfil_segun_imc_y_actividad(self):
        casos = [(17, 'leve', 'P1'), (18.49, 'alta', 'P3'), (18.5, 'leve', 'P4'),
                 (24.95, 'moderada', 'P5'), (25, 'moderada', 'P8'), (31, 'alta', 'P9'),
                 (22, 'rara', 'P5')]
        for imc, act, cod in casos:
            self.assertEqual(planes_base.perfil_alimentacion(imc, act)[0], cod, (imc, act))

    def test_alerta(self):
        self.assertIsNotNone(planes_base.alerta_profesional(15.5))
        self.assertIsNotNone(planes_base.alerta_profesional(36))
        self.assertIsNone(planes_base.alerta_profesional(22))

    def test_ejercicios_varios_bloques(self):
        e = planes_base.ejercicios_base('normal', {'lunes': ['8:15-9:25', '14:40-15:50'], 'martes': []})
        self.assertIn('Bloques 8:15-9:25 y 14:40-15:50', e['Lunes'])
        self.assertEqual(e['Martes'], planes_base.SIN_TIEMPO)


class RutinasTests(SinClaveMixin, TestCase):
    def plan(self, datos, rutina):
        dias = [{'dia': d, 'desayuno': 'a', 'almuerzo': 'b', 'once': 'c', 'colacion': 'd', 'actividad': 'Algo',
                 **({'rutina': rutina} if rutina is not None else {})} for d in DIAS]
        return ia.validar_plan(json.dumps({'resumen': 'r', 'dias': dias, 'consejos': []}), datos)

    def test_minutos_disponibles_restan_margen_y_topan(self):
        from .. import rutinas
        d = datos_con_ventanas()
        self.assertEqual(rutinas.minutos_disponibles(d, 'lunes'), 60)
        self.assertEqual(rutinas.minutos_disponibles(d, 'martes'), 0)
        d['ventanas_libres']['lunes'] = [{'inicio': '9:00', 'fin': '16:00', 'minutos': 420}]
        self.assertEqual(rutinas.minutos_disponibles(d, 'lunes'), 90)

    def test_rutina_base_respeta_el_tiempo(self):
        from .. import rutinas
        d = datos_con_ventanas()
        r = rutinas.rutina_base(d, 'lunes', 0)
        self.assertLessEqual(r['duracion_min'], 60)
        self.assertIsNone(rutinas.rutina_base(d, 'martes', 0))
        d['ventanas_libres']['lunes'] = [{'inicio': '8:15', 'fin': '8:35', 'minutos': 20}]  # 10 útiles
        corta = rutinas.rutina_base(d, 'lunes', 0)
        self.assertEqual(corta['duracion_min'], 10)
        self.assertNotIn('Calentamiento', [e['nombre'] for e in corta['ejercicios']])

    def test_rutina_base_conservadora_con_lesion_o_imc_extremo(self):
        from .. import rutinas
        for extra in ({'tiene_lesion': True}, {'imc': 36.0, 'categoria_imc': 'obesidad'}, {'imc': 15.0, 'categoria_imc': 'bajo'}):
            for i in range(4):
                r = rutinas.rutina_base(datos_con_ventanas(**extra), 'lunes', i)
                self.assertEqual(r['intensidad'], 'baja', extra)
                self.assertIn(r['titulo'], ('Bajo impacto', 'Movilidad y estiramiento'))

    def test_ia_rutina_se_valida_y_se_acota(self):
        r = self.plan(datos_con_ventanas(), RUTINA_IA)['dias']
        self.assertEqual(r['lunes']['rutina']['titulo'], 'Circuito casero')
        self.assertEqual(r['lunes']['rutina']['intensidad'], 'alta')
        self.assertEqual(r['lunes']['actividad'], 'Algo')  # se conserva el texto de la IA
        largo = dict(RUTINA_IA, duracion_min=200)
        self.assertEqual(self.plan(datos_con_ventanas(), largo)['dias']['lunes']['rutina']['duracion_min'], 60)

    def test_ia_intensidad_alta_se_baja_con_lesion(self):
        r = self.plan(datos_con_ventanas(tiene_lesion=True), RUTINA_IA)['dias']
        self.assertEqual(r['lunes']['rutina']['intensidad'], 'baja')

    def test_ia_rutina_invalida_usa_la_base_y_sin_hueco_no_hay_rutina(self):
        for mala in (None, 'texto', {'titulo': '', 'duracion_min': 30, 'ejercicios': []},
                     dict(RUTINA_IA, ejercicios=[]), dict(RUTINA_IA, duracion_min='mucho')):
            r = self.plan(datos_con_ventanas(), mala)['dias']
            self.assertIsNotNone(r['lunes']['rutina'], mala)
            self.assertIn('min · intensidad', r['lunes']['actividad'])
        r = self.plan(datos_con_ventanas(), RUTINA_IA)['dias']
        self.assertIsNone(r['martes']['rutina'])  # sin hueco: descanso, aunque la IA mande rutina
        self.assertIn('Descanso', r['martes']['actividad'])

    def test_ia_rutina_sanea_textos(self):
        sucia = dict(RUTINA_IA, titulo='  Hola\n\n  mundo  ' + 'x' * 100,
                     ejercicios=[{'nombre': 'a' * 200, 'detalle': 'b'}] * 12 + ['basura', {'nombre': ''}])
        r = self.plan(datos_con_ventanas(), sucia)['dias']['lunes']['rutina']
        self.assertTrue(r['titulo'].startswith('Hola mundo'))
        self.assertLessEqual(len(r['titulo']), 60)
        self.assertEqual(len(r['ejercicios']), 8)
        self.assertEqual(len(r['ejercicios'][0]['nombre']), 60)

    def test_respaldo_incluye_rutinas_variadas(self):
        d = datos_con_ventanas()
        d['ventanas_libres'] = {dia: [{'inicio': '8:15', 'fin': '9:25', 'minutos': 70}] for dia in DIAS}
        d['bloques_libres'] = {dia: ['8:15-9:25'] for dia in DIAS}
        plan = planes_base.plan_respaldo(d)
        titulos = {x['rutina']['titulo'] for x in plan['dias'].values()}
        self.assertGreaterEqual(len(titulos), 2)
        self.assertIn('8:15-9:25', plan['dias']['lunes']['actividad'])

    def test_portal_muestra_la_rutina(self):
        User.objects.create_user('r', 'r@usm.cl', 'x')
        self.client.login(username='r', password='x')
        self.client.post(reverse('encuesta_datos'), {
            **BASE, 'peso': '70', 'altura': '1.75', 'libre_lunes': ['1', '2'], 'lugar_entrenamiento': 'gimnasio'})
        self.client.post(reverse('plan_generar'))  # sin clave: respaldo
        r = self.client.get(reverse('portal'))
        rut = r.context['semana'][0]['rutina']
        self.assertEqual(rut['ejercicios'][0]['nombre'], 'Calentamiento' if rut['duracion_min'] >= 20 else rut['ejercicios'][0]['nombre'])
        self.assertContains(r, rut['titulo'])
        self.assertIsNone(r.context['semana'][1]['rutina'])
