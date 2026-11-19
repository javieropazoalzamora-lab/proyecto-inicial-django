"""Vista de la encuesta (crear/editar perfil) y portal."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ..models import PerfilSansano
from .utilidades import BASE, SinClaveMixin


class EncuestaTests(SinClaveMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.u = User.objects.create_user('a', 'a@usm.cl', 'x')
        self.client.login(username='a', password='x')

    def test_guarda_varios_bloques_y_transporte(self):
        r = self.client.post(reverse('encuesta_datos'), {
            **BASE, 'peso': '70,5', 'altura': '175', 'tiempo_transporte_min': '40',
            'lunes': ['14:40-15:50', '8:15-9:25', 'inventado'],
        })
        self.assertRedirects(r, reverse('portal'))
        p = PerfilSansano.objects.get(usuario=self.u)
        self.assertEqual(p.altura, 1.75)
        self.assertEqual(p.peso, 70.5)
        self.assertEqual(p.bloques_libres['lunes'], ['8:15-9:25', '14:40-15:50'])
        self.assertEqual(p.bloques_libres['martes'], [])
        self.assertEqual(p.tiempo_transporte_min, 40)

    def test_datos_invalidos_no_guardan(self):
        for peso, altura in [('abc', '175'), ('70', ''), ('nan', '1.7'), ('inf', '1.7'),
                             ('0', '0'), ('500', '1.7'), ('70', '50')]:
            r = self.client.post(reverse('encuesta_datos'), {**BASE, 'peso': peso, 'altura': altura})
            self.assertEqual(r.status_code, 200, (peso, altura))
        self.assertFalse(PerfilSansano.objects.exists())

    def test_editar_recalcula_imc(self):
        self.client.post(reverse('encuesta_datos'), {**BASE, 'peso': '70', 'altura': '1.75'})
        self.client.post(reverse('editar_perfil'), {**BASE, 'peso': '90', 'altura': '1.75'})
        self.assertEqual(PerfilSansano.objects.get().imc, 29.39)

    def test_requiere_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('portal')).status_code, 302)

    def test_portal(self):
        PerfilSansano.objects.create(usuario=self.u, peso=70, altura=1.75,
                                     bloques_libres={'lunes': ['8:15-9:25']})
        r = self.client.get(reverse('portal'))
        self.assertEqual(r.context['tipo_imc'], "P5: Mantener peso (Actividad media)")
        self.assertIn('Miércoles', r.context['rutina'])
        self.assertIn('Lunes', r.context['ejercicios'])

    def test_formulario_prefill(self):
        PerfilSansano.objects.create(usuario=self.u, peso=70, altura=1.75, tiempo_transporte_min=30,
                                     bloques_libres={'lunes': ['8:15-9:25']})
        r = self.client.get(reverse('encuesta_datos'))
        g = r.context['grilla']
        self.assertEqual([g[0]['celdas'][0]['estado'], g[1]['celdas'][0]['estado'], g[2]['celdas'][0]['estado']],
                         ['libre', 'libre', ''])
        self.assertEqual(len(g), 14)
        self.assertEqual(r.context['transporte_val'], 30)

    def test_actividad_se_guarda_y_login_redirige(self):
        datos = {'peso': '70', 'altura': '1.75', 'actividad_fisica': 'alta', 'mayor_de_edad': 'on',
                 'objetivo': 'mantener', 'tipo_dieta': 'omnivora', 'presupuesto': 'medio',
                 'tiempo_cocina': 'normal', 'lugar_entrenamiento': 'casa'}
        self.client.post(reverse('encuesta_datos'), datos)
        self.assertEqual(PerfilSansano.objects.get().actividad_fisica, 'alta')
        self.client.logout()
        r = self.client.post(reverse('login'), {'username': 'a', 'password': 'x'})
        self.assertRedirects(r, reverse('portal'))

    def test_cocina_familia_se_guarda_y_portal_tiene_pestanas(self):
        datos = {'peso': '70', 'altura': '1.75', 'actividad_fisica': 'moderada', 'mayor_de_edad': 'on',
                 'objetivo': 'mantener', 'tipo_dieta': 'omnivora', 'presupuesto': 'medio',
                 'tiempo_cocina': 'familia', 'lugar_entrenamiento': 'casa'}
        self.client.post(reverse('encuesta_datos'), datos)
        self.assertEqual(PerfilSansano.objects.get().tiempo_cocina, 'familia')
        self.client.post(reverse('plan_generar'))
        html = self.client.get(reverse('portal')).content.decode()
        for t in ('p-resumen', 'p-actividad', 'p-nutricion'):
            self.assertIn(f'id="{t}"', html)

    def test_login_sin_perfil_va_a_encuesta(self):
        self.client.logout()
        r = self.client.post(reverse('login'), {'username': 'a', 'password': 'x'})
        self.assertRedirects(r, reverse('encuesta_datos'))

    def test_portal_sin_perfil(self):
        r = self.client.get(reverse('portal'))
        self.assertEqual(r.context['tipo_imc'], "Sin datos")
