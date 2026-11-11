from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import RegistroSansanoForm
from .models import PerfilSansano
from . import planes_base


class ModeloTests(TestCase):
    def test_imc_property(self):
        u = User.objects.create_user('a', 'a@usm.cl', 'x')
        p = PerfilSansano.objects.create(usuario=u, peso=70, altura=1.75)
        self.assertEqual(p.imc, 22.86)

    def test_imc_altura_cero(self):
        u = User.objects.create_user('a', 'a@usm.cl', 'x')
        p = PerfilSansano.objects.create(usuario=u, peso=70, altura=0)
        self.assertIsNone(p.imc)


class PlanesBaseTests(TestCase):
    def test_clasificacion(self):
        for imc, cat in [(17, 'bajo'), (18.5, 'normal'), (24.99, 'normal'),
                         (25, 'sobrepeso'), (30, 'obesidad')]:
            self.assertEqual(planes_base.clasificar_imc(imc), cat)

    def test_dietas_completas(self):
        self.assertEqual(set(planes_base.PLAN_ALIMENTACION), {'bajo', 'normal', 'sobrepeso', 'obesidad'})
        for d in planes_base.PLAN_ALIMENTACION.values():
            self.assertEqual(len(d), 7)
            for comidas in d.values():
                self.assertEqual(set(comidas), {'desayuno', 'almuerzo', 'once'})

    def test_alerta(self):
        self.assertIsNotNone(planes_base.alerta_profesional(15.5))
        self.assertIsNotNone(planes_base.alerta_profesional(36))
        self.assertIsNone(planes_base.alerta_profesional(22))

    def test_ejercicios_varios_bloques(self):
        e = planes_base.ejercicios_base('normal', {'lunes': ['8:15-9:25', '14:40-15:50'], 'martes': []})
        self.assertIn('Bloques 8:15-9:25 y 14:40-15:50', e['Lunes'])
        self.assertEqual(e['Martes'], planes_base.SIN_TIEMPO)


class EncuestaTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user('a', 'a@usm.cl', 'x')
        self.client.login(username='a', password='x')

    def test_guarda_varios_bloques_y_transporte(self):
        r = self.client.post(reverse('encuesta_datos'), {
            'peso': '70,5', 'altura': '175', 'tiempo_transporte_min': '40',
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
            r = self.client.post(reverse('encuesta_datos'), {'peso': peso, 'altura': altura})
            self.assertEqual(r.status_code, 200, (peso, altura))
        self.assertFalse(PerfilSansano.objects.exists())

    def test_editar_recalcula_imc(self):
        self.client.post(reverse('encuesta_datos'), {'peso': '70', 'altura': '1.75'})
        self.client.post(reverse('editar_perfil'), {'peso': '90', 'altura': '1.75'})
        self.assertEqual(PerfilSansano.objects.get().imc, 29.39)

    def test_requiere_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('portal')).status_code, 302)

    def test_portal(self):
        PerfilSansano.objects.create(usuario=self.u, peso=70, altura=1.75,
                                     bloques_libres={'lunes': ['8:15-9:25']})
        r = self.client.get(reverse('portal'))
        self.assertEqual(r.context['tipo_imc'], "Peso normal (Dieta equilibrada)")
        self.assertIn('Miércoles', r.context['rutina'])
        self.assertIn('Lunes', r.context['ejercicios'])

    def test_formulario_prefill(self):
        PerfilSansano.objects.create(usuario=self.u, peso=70, altura=1.75, tiempo_transporte_min=30,
                                     bloques_libres={'lunes': ['8:15-9:25']})
        r = self.client.get(reverse('encuesta_datos'))
        lunes = r.context['dias_ui'][0]
        self.assertEqual(lunes['etiqueta'], 'Lunes')
        self.assertTrue(lunes['bloques'][0]['marcado'])
        self.assertFalse(lunes['bloques'][1]['marcado'])
        self.assertEqual(r.context['transporte_val'], 30)

    def test_portal_sin_perfil(self):
        r = self.client.get(reverse('portal'))
        self.assertEqual(r.context['tipo_imc'], "Sin datos")


class RegistroTests(TestCase):
    def datos(self, email):
        return {'username': 'nuevo', 'email': email,
                'password1': 'Clave-segura-9271', 'password2': 'Clave-segura-9271'}

    def test_dominio_y_mayusculas(self):
        self.assertTrue(RegistroSansanoForm(self.datos('Ana@USM.cl')).is_valid())
        self.assertFalse(RegistroSansanoForm(self.datos('ana@gmail.com')).is_valid())

    def test_correo_duplicado_activo(self):
        User.objects.create_user('otro', 'ana@usm.cl', 'x')
        self.assertFalse(RegistroSansanoForm(self.datos('ANA@usm.cl')).is_valid())

    def test_sansano_subdominio_no_permitido(self):
        self.assertFalse(RegistroSansanoForm(self.datos('ana@sansano.usm.cl')).is_valid())
        self.assertFalse(RegistroSansanoForm(self.datos('@usm.cl')).is_valid())

    def test_cuenta_sin_activar_no_bloquea_al_dueno(self):
        squat = User.objects.create_user('squatter', 'pperezn@usm.cl', 'x')
        squat.is_active = False
        squat.save()
        datos = self.datos('pperezn@usm.cl')
        r = self.client.post(reverse('registro'), datos)
        self.assertContains(r, 'Cuenta creada')
        self.assertFalse(User.objects.filter(username='squatter').exists())
        self.assertEqual(User.objects.filter(email='pperezn@usm.cl').count(), 1)
        self.assertFalse(User.objects.get(username='nuevo').is_active)
