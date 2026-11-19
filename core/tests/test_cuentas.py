"""Registro, activación por correo, login/logout, seguridad y mensajes."""
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .. import servicios
from ..forms import RegistroSansanoForm
from ..models import PerfilSansano


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
        r = self.client.post(reverse('registro'), datos, follow=True)
        self.assertContains(r, 'Cuenta creada')   # ahora llega como mensaje en la página de login
        self.assertFalse(User.objects.filter(username='squatter').exists())
        self.assertEqual(User.objects.filter(email='pperezn@usm.cl').count(), 1)
        self.assertFalse(User.objects.get(username='nuevo').is_active)


class AuditoriaSeguridadTests(TestCase):
    """Pruebas agregadas en la auditoría de entrega."""

    def setUp(self):
        self.u = User.objects.create_user('aud', 'aud@usm.cl', 'ClaveSegura123')

    # --- IMC robusto ---
    def test_imc_con_peso_nulo_o_negativo_devuelve_none(self):
        self.assertIsNone(PerfilSansano(peso=None, altura=1.70).imc)
        self.assertIsNone(PerfilSansano(peso=70, altura=None).imc)
        self.assertIsNone(PerfilSansano(peso=-5, altura=1.70).imc)
        self.assertIsNone(PerfilSansano(peso=float('nan'), altura=1.70).imc)

    def test_generar_plan_sin_imc_lanza_error_controlado(self):
        perfil = PerfilSansano(usuario=self.u, peso=70, altura=0)
        with self.assertRaises(ValueError):
            servicios.generar_y_guardar_plan(perfil, usar_ia=False)

    # --- @login_required redirige a la vista de login real (no a /accounts/login/) ---
    def test_vistas_protegidas_redirigen_al_login_propio(self):
        for nombre in ('portal', 'encuesta_datos', 'editar_perfil', 'cambiar_clave'):
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302, nombre)
            self.assertTrue(r['Location'].startswith(reverse('login')), (nombre, r['Location']))

    def test_login_respeta_next_interno_y_descarta_externo(self):
        r = self.client.post(reverse('login') + '?next=/formulario/',
                             {'username': 'aud', 'password': 'ClaveSegura123'})
        self.assertRedirects(r, '/formulario/', fetch_redirect_response=False)
        self.client.post(reverse('logout'))
        r = self.client.post(reverse('login') + '?next=https://malicioso.com/',
                             {'username': 'aud', 'password': 'ClaveSegura123'})
        self.assertEqual(r['Location'], reverse('encuesta_datos'))

    # --- Logout solo por POST ---
    def test_logout_por_get_no_cierra_sesion(self):
        self.client.force_login(self.u)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertEqual(self.client.get(reverse('encuesta_datos')).status_code, 200)
        self.client.post(reverse('logout'))
        self.assertEqual(self.client.get(reverse('encuesta_datos')).status_code, 302)

    # --- Cada usuario solo ve/edita SU perfil ---
    def test_encuesta_no_permite_escribir_perfil_ajeno(self):
        otro = User.objects.create_user('otro', 'otro@usm.cl', 'x')
        PerfilSansano.objects.create(usuario=otro, peso=80, altura=1.80)
        self.client.force_login(self.u)
        self.client.post(reverse('encuesta_datos'), {
            'usuario': otro.pk, 'peso': '60', 'altura': '1.60', 'mayor_de_edad': 'on',
            'actividad_fisica': 'moderada', 'objetivo': 'mantener', 'tipo_dieta': 'omnivora',
            'presupuesto': 'medio', 'tiempo_cocina': 'normal', 'lugar_entrenamiento': 'casa',
        })
        self.assertEqual(PerfilSansano.objects.get(usuario=otro).peso, 80)
        self.assertEqual(PerfilSansano.objects.get(usuario=self.u).peso, 60)

    # --- Enlace de activación generado con reverse() ---
    def test_enlace_de_activacion_usa_la_ruta_real(self):
        from django.core import mail
        self.client.post(reverse('registro'), {
            'username': 'nuevo', 'email': 'nuevo@usm.cl',
            'password1': 'OtraClave!2026', 'password2': 'OtraClave!2026',
        })
        self.assertEqual(len(mail.outbox), 1)
        enlace = [l for l in mail.outbox[0].body.split() if '/activar/' in l][0]
        r = self.client.get(enlace.replace('http://testserver', ''))
        self.assertRedirects(r, reverse('encuesta_datos'), fetch_redirect_response=False)
        self.assertTrue(User.objects.get(username='nuevo').is_active)


class FlujoCompletoTests(TestCase):
    """Registro → correo HTML → activación → encuesta (ModelForm) → portal, con mensajes."""

    DATOS_ENCUESTA = {
        'peso': '70,5', 'altura': '175', 'tiempo_transporte_min': '30', 'mayor_de_edad': 'on',
        'actividad_fisica': 'moderada', 'objetivo': 'mantener', 'tipo_dieta': 'omnivora',
        'presupuesto': 'medio', 'tiempo_cocina': 'normal', 'lugar_entrenamiento': 'casa',
        'libre_lunes': ['1', '2'], 'clase_martes': ['3'],
    }

    def _registrar(self, usuario='ana', email='ana.perez@usm.cl'):
        return self.client.post(reverse('registro'), {
            'username': usuario, 'email': email,
            'password1': 'ClaveMuySegura!26', 'password2': 'ClaveMuySegura!26',
        }, follow=True)

    def _enlace(self, correo):
        return next(p for p in correo.body.split() if '/activar/' in p).replace('http://testserver', '')

    def test_registro_envia_correo_html_y_texto(self):
        from django.core import mail
        r = self._registrar()
        self.assertRedirects(r, reverse('login'))
        self.assertContains(r, 'Cuenta creada')                        # mensaje de éxito visible
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ['ana.perez@usm.cl'])
        self.assertEqual(correo.subject, 'Activa tu cuenta de VitaSansano')
        self.assertIn('VitaSansano', correo.from_email)
        html, tipo = correo.alternatives[0]
        self.assertEqual(tipo, 'text/html')
        self.assertIn('Activar mi cuenta', html)
        self.assertIn(self._enlace(correo), html)                       # mismo enlace en ambas versiones
        self.assertFalse(User.objects.get(username='ana').is_active)

    def test_activacion_inicia_sesion_y_enlace_es_de_un_solo_uso(self):
        from django.core import mail
        self._registrar()
        enlace = self._enlace(mail.outbox[0])
        r = self.client.get(enlace, follow=True)
        self.assertRedirects(r, reverse('encuesta_datos'))
        self.assertContains(r, 'Correo verificado')
        self.assertTrue(User.objects.get(username='ana').is_active)
        self.client.post(reverse('logout'))
        r = self.client.get(enlace, follow=True)                       # segundo uso: inválido
        self.assertRedirects(r, reverse('login'))
        self.assertContains(r, 'no es válido o ya venció')

    def test_si_falla_el_envio_no_queda_cuenta_creada(self):
        with mock.patch('core.views.EmailMultiAlternatives.send', side_effect=OSError('SMTP caído')):
            r = self._registrar()
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'No pudimos enviar el correo')
        self.assertFalse(User.objects.filter(username='ana').exists())

    def test_login_con_cuenta_sin_activar_reenvia_el_correo(self):
        from django.core import mail
        self._registrar()
        mail.outbox.clear()
        r = self.client.post(reverse('login'), {'username': 'ana', 'password': 'ClaveMuySegura!26'})
        self.assertContains(r, 'aún no está activada')
        self.assertNotContains(r, 'no coinciden')
        self.assertEqual(len(mail.outbox), 1)
        # Con clave incorrecta no se reenvía nada ni se revela el estado de la cuenta
        mail.outbox.clear()
        r = self.client.post(reverse('login'), {'username': 'ana', 'password': 'otra'})
        self.assertNotContains(r, 'aún no está activada')
        self.assertEqual(len(mail.outbox), 0)

    def test_login_exitoso_muestra_bienvenida(self):
        User.objects.create_user('beto', 'beto@usm.cl', 'ClaveMuySegura!26')
        r = self.client.post(reverse('login'), {'username': 'beto', 'password': 'ClaveMuySegura!26'}, follow=True)
        self.assertContains(r, 'Hola de nuevo, beto')

    def test_encuesta_modelform_asigna_usuario_y_calcula_imc(self):
        u = User.objects.create_user('caro', 'caro@usm.cl', 'x')
        self.client.force_login(u)
        r = self.client.post(reverse('encuesta_datos'), self.DATOS_ENCUESTA)
        self.assertRedirects(r, reverse('portal'), fetch_redirect_response=False)
        perfil = PerfilSansano.objects.get(usuario=u)
        self.assertEqual((perfil.peso, perfil.altura), (70.5, 1.75))     # coma decimal y cm convertidos
        self.assertEqual(perfil.imc, round(70.5 / 1.75 ** 2, 2))
        self.assertEqual(perfil.bloques_libres['lunes'], ['8:15-9:25'])
        self.assertEqual(perfil.clases['martes'], [3])

    def test_encuesta_edicion_actualiza_el_mismo_perfil(self):
        u = User.objects.create_user('caro', 'caro@usm.cl', 'x')
        self.client.force_login(u)
        self.client.post(reverse('encuesta_datos'), self.DATOS_ENCUESTA)
        r = self.client.post(reverse('encuesta_datos'), {**self.DATOS_ENCUESTA, 'peso': '80'}, follow=True)
        self.assertEqual(PerfilSansano.objects.filter(usuario=u).count(), 1)
        self.assertEqual(PerfilSansano.objects.get(usuario=u).peso, 80)
        self.assertContains(r, 'Tus datos se actualizaron')

    def test_encuesta_rechaza_combinacion_imposible_sin_guardar(self):
        u = User.objects.create_user('caro', 'caro@usm.cl', 'x')
        self.client.force_login(u)
        r = self.client.post(reverse('encuesta_datos'), {**self.DATOS_ENCUESTA, 'peso': '30', 'altura': '2.4'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'no es posible')
        self.assertFalse(PerfilSansano.objects.filter(usuario=u).exists())

    def test_encuesta_invalida_no_altera_el_perfil_guardado(self):
        u = User.objects.create_user('caro', 'caro@usm.cl', 'x')
        PerfilSansano.objects.create(usuario=u, peso=70, altura=1.75, mayor_de_edad=True)
        self.client.force_login(u)
        self.client.post(reverse('encuesta_datos'), {**self.DATOS_ENCUESTA, 'peso': 'abc'})
        self.assertEqual(PerfilSansano.objects.get(usuario=u).peso, 70)

    def test_logout_muestra_mensaje(self):
        u = User.objects.create_user('dani', 'dani@usm.cl', 'x')
        self.client.force_login(u)
        r = self.client.post(reverse('logout'), follow=True)
        self.assertContains(r, 'Cerraste sesión')

    def test_recuperar_clave_envia_correo_html(self):
        from django.core import mail
        User.objects.create_user('eli', 'eli@usm.cl', 'ClaveMuySegura!26')
        r = self.client.post(reverse('password_reset'), {'email': 'eli@usm.cl'})
        self.assertRedirects(r, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Recupera tu clave de VitaSansano')
        self.assertIn('Crear nueva clave', mail.outbox[0].alternatives[0][0])

    def test_paginas_de_confirmacion_usan_la_tarjeta_comun(self):
        r = self.client.get(reverse('password_reset_done'))
        self.assertContains(r, 'estado-badge')
        self.assertContains(r, 'Correo enviado')
