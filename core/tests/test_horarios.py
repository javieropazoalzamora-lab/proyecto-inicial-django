"""Bloques horarios, grilla de módulos y viajes."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .. import planes_base
from .. import servicios
from ..models import PerfilSansano


class HorariosTests(TestCase):
    def test_une_bloques_seguidos_y_recreos(self):
        from ..horarios import ventanas_texto, ventanas_con_minutos
        self.assertEqual(ventanas_texto(['9:40-10:50', '11:05-12:15', '12:30-13:40']), ['9:40-13:40'])
        # el almuerzo (1 hora) NO se une
        self.assertEqual(ventanas_texto(['12:30-13:40', '14:40-15:50']), ['12:30-13:40', '14:40-15:50'])
        # desordenados y duplicados
        self.assertEqual(ventanas_texto(['11:05-12:15', '9:40-10:50', '9:40-10:50']), ['9:40-12:15'])
        self.assertEqual(ventanas_texto([]), [])
        self.assertEqual(ventanas_con_minutos(['9:40-10:50', '11:05-12:15']),
                         [{'inicio': '9:40', 'fin': '12:15', 'minutos': 155}])

    def test_ejercicios_usan_ventana_unida(self):
        e = planes_base.ejercicios_base('normal', {'lunes': ['9:40-10:50', '11:05-12:15']})
        self.assertIn('Bloque 9:40-12:15:', e['Lunes'])


class GrillaTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user('g', 'g@usm.cl', 'x')
        self.client.login(username='g', password='x')

    def post(self, extra):
        datos = {'peso': '70', 'altura': '1.75', 'actividad_fisica': 'moderada', 'mayor_de_edad': 'on',
                 'objetivo': 'mantener', 'tipo_dieta': 'omnivora', 'presupuesto': 'medio',
                 'tiempo_cocina': 'normal', 'lugar_entrenamiento': 'casa', **extra}
        return self.client.post(reverse('encuesta_datos'), datos)

    def test_guarda_libres_y_clases_por_modulo(self):
        self.post({'libre_lunes': ['3', '4', '12'], 'clase_lunes': ['1', '2'], 'tiempo_transporte_min': '40'})
        p = PerfilSansano.objects.get()
        self.assertEqual(p.clases['lunes'], [1, 2])
        self.assertEqual(p.bloques_libres['lunes'], ['9:40-10:50', '16:40-17:15'])

    def test_clase_gana_sobre_libre_y_se_ignoran_modulos_invalidos(self):
        self.post({'libre_martes': ['1', '2', '99', 'x'], 'clase_martes': ['1']})
        p = PerfilSansano.objects.get()
        self.assertEqual(p.clases['martes'], [1])
        self.assertEqual(p.bloques_libres['martes'], ['8:50-9:25'])

    def test_ida_y_vuelta_de_la_grilla(self):
        self.post({'libre_jueves': ['5', '6'], 'clase_jueves': ['9']})
        g = self.client.get(reverse('encuesta_datos')).context['grilla']
        estados = {f['n']: f['celdas'][3]['estado'] for f in g}  # columna jueves
        self.assertEqual((estados[5], estados[6], estados[9], estados[1]), ('libre', 'libre', 'clase', ''))

    def test_viaje_y_lugar_de_ventanas(self):
        from ..horarios import viaje_del_dia, ventanas_con_minutos
        self.assertEqual(viaje_del_dia([1, 2, 11, 12], 40),
                         {'primera_clase': '8:15', 'ultima_clase': '17:15', 'sale_de_casa': '7:35', 'llega_a_casa': '17:55'})
        self.assertEqual(viaje_del_dia([1, 2], None), {'primera_clase': '8:15', 'ultima_clase': '9:25'})
        self.assertIsNone(viaje_del_dia([], 40))
        v = ventanas_con_minutos(['9:40-10:15', '12:30-13:05'], [1, 2, 3, 4, 5])  # clases hasta 11:40
        self.assertEqual([x['lugar'] for x in v], ['universidad', 'casa'])
        self.assertNotIn('lugar', ventanas_con_minutos(['9:40-10:15'], [])[0])  # sin clases: no se sabe

    def test_datos_para_la_ia_incluyen_clases_y_transporte(self):
        self.post({'clase_lunes': ['1', '2', '3', '4'], 'libre_lunes': ['9'], 'tiempo_transporte_min': '30'})
        d = servicios.construir_datos(PerfilSansano.objects.get())
        self.assertEqual(d['dias_con_clases']['lunes']['sale_de_casa'], '7:45')
        self.assertEqual(d['ventanas_libres']['lunes'][0]['lugar'], 'casa')  # 14:40 es después de la última clase
        self.assertNotIn('martes', d['dias_con_clases'])

    def test_portal_muestra_viaje(self):
        self.post({'clase_lunes': ['1', '2'], 'tiempo_transporte_min': '40'})
        self.client.post(reverse('plan_generar'))
        r = self.client.get(reverse('portal'))
        self.assertTrue(r.context['hay_clases'])
        self.assertEqual(r.context['semana'][0]['viaje']['sale_de_casa'], '7:35')
        self.assertContains(r, 'Sales 7:35')
