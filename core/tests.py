import json
import os
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from . import ia, servicios
from .constantes import DIAS
from .models import PlanSemanal

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


class HorariosTests(TestCase):
    def test_une_bloques_seguidos_y_recreos(self):
        from .horarios import ventanas_texto, ventanas_con_minutos
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
        lunes = r.context['dias_ui'][0]
        self.assertEqual(lunes['etiqueta'], 'Lunes')
        self.assertTrue(lunes['bloques'][0]['marcado'])
        self.assertFalse(lunes['bloques'][1]['marcado'])
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


class IATests(SinClaveMixin, TestCase):
    def test_sin_clave_lanza_error(self):
        with self.assertRaises(ia.PlanIAError):
            ia.generar_plan_ia(DATOS)

    def test_config_valida_para_sdk(self):
        from google.genai import types
        types.GenerateContentConfig(system_instruction=ia.SYSTEM_PROMPT, response_mime_type='application/json',
                                    response_json_schema=ia.ESQUEMA)

    def test_plan_valido_y_descanso_forzado(self):
        r = ia.validar_plan(plan_json(), DATOS)
        self.assertEqual(r['dias']['lunes']['actividad'], 'Trote suave 30 min')
        self.assertEqual(r['dias']['martes']['actividad'], 'Día libre / Descanso (Sin bloques disponibles)')

    def test_rechaza_json_invalido_y_dias_incompletos(self):
        for bruto in ['no es json', '{}', plan_json(dias=[])]:
            with self.assertRaises(ia.PlanIAError):
                ia.validar_plan(bruto, DATOS)

    def test_rechaza_carne_en_dieta_vegetariana(self):
        datos = {**DATOS, 'tipo_dieta': 'vegetariana'}
        dias = [{'dia': d, 'desayuno': 'Avena', 'almuerzo': 'Pollo con arroz', 'once': 'Té', 'colacion': 'Fruta', 'actividad': 'x'} for d in DIAS]
        with self.assertRaises(ia.PlanIAError):
            ia.validar_plan(plan_json(dias=dias), datos)
        ia.validar_plan(plan_json(), datos)  # el plan sin carne sí pasa

    def test_vegana_rechaza_huevo(self):
        datos = {**DATOS, 'tipo_dieta': 'vegana'}
        dias = [{'dia': d, 'desayuno': 'Tostadas con huevo', 'almuerzo': 'Lentejas', 'once': 'Té', 'colacion': 'Fruta', 'actividad': 'x'} for d in DIAS]
        with self.assertRaises(ia.PlanIAError):
            ia.validar_plan(plan_json(dias=dias), datos)


class ServicioPlanTests(SinClaveMixin, TestCase):
    def setUp(self):
        super().setUp()
        from .models import PerfilSansano
        self.u = User.objects.create_user('a', 'a@usm.cl', 'x')
        self.perfil = PerfilSansano.objects.create(
            usuario=self.u, peso=70, altura=1.75, mayor_de_edad=True,
            bloques_libres={d: (['8:15-9:25'] if d == 'lunes' else []) for d in DIAS})

    def test_datos_anonimos(self):
        datos = servicios.construir_datos(self.perfil)
        texto = json.dumps(datos)
        self.assertNotIn('a@usm.cl', texto)
        self.assertNotIn('"a"', texto)

    def test_usa_ia_cuando_responde(self):
        with mock.patch('core.ia._llamar_modelo', return_value=plan_json()) as m:
            plan = servicios.generar_y_guardar_plan(self.perfil)
        self.assertEqual(plan.origen, 'ia')
        self.assertEqual(m.call_count, 1)

    def test_respaldo_si_falla_ia(self):
        with mock.patch('core.ia._llamar_modelo', side_effect=ia.PlanIAError('cuota')):
            plan = servicios.generar_y_guardar_plan(self.perfil)
        self.assertEqual(plan.origen, 'respaldo')
        self.assertEqual(set(plan.contenido['dias']), set(DIAS))

    def test_respaldo_advierte_si_dieta_vegana(self):
        self.perfil.tipo_dieta = 'vegana'
        self.perfil.save()
        plan = servicios.generar_y_guardar_plan(self.perfil)
        self.assertIn('NO se adaptó', plan.contenido['advertencia'])

    def test_mismos_datos_no_repiten_llamada(self):
        with mock.patch('core.ia._llamar_modelo', return_value=plan_json()) as m:
            servicios.generar_y_guardar_plan(self.perfil)
            servicios.generar_y_guardar_plan(self.perfil)
        self.assertEqual(m.call_count, 1)

    def test_cambio_de_datos_regenera(self):
        with mock.patch('core.ia._llamar_modelo', return_value=plan_json()) as m:
            servicios.generar_y_guardar_plan(self.perfil)
            self.perfil.objetivo = 'ganar_musculo'
            self.perfil.save()
            servicios.generar_y_guardar_plan(self.perfil)
        self.assertEqual(m.call_count, 2)

    def test_fallo_previo_reintenta_ia(self):
        with mock.patch('core.ia._llamar_modelo', side_effect=ia.PlanIAError('x')):
            servicios.generar_y_guardar_plan(self.perfil)
        with mock.patch('core.ia._llamar_modelo', return_value=plan_json()):
            plan = servicios.generar_y_guardar_plan(self.perfil)
        self.assertEqual(plan.origen, 'ia')

    def test_menor_o_sin_confirmacion_no_llama_ia(self):
        self.perfil.mayor_de_edad = False
        self.perfil.save()
        with mock.patch('core.ia._llamar_modelo') as m:
            plan = servicios.generar_y_guardar_plan(self.perfil)
        m.assert_not_called()
        self.assertEqual(plan.origen, 'respaldo')

    def test_portal_no_llama_ia(self):
        self.client.login(username='a', password='x')
        with mock.patch('core.ia._llamar_modelo') as m:
            r = self.client.get(reverse('portal'))
        m.assert_not_called()  # el portal nunca llama a la IA por sí mismo
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['generando'])  # la generación la dispara el navegador (plan_generar)
        self.assertFalse(PlanSemanal.objects.filter(usuario=self.u).exists())

    def test_portal_menor_o_sin_confirmacion_usa_respaldo_sin_esperar(self):
        self.perfil.mayor_de_edad = False
        self.perfil.save()
        self.client.login(username='a', password='x')
        with mock.patch('core.ia._llamar_modelo') as m:
            r = self.client.get(reverse('portal'))
        m.assert_not_called()
        self.assertNotIn('generando', r.context)
        self.assertEqual(PlanSemanal.objects.get(usuario=self.u).origen, 'respaldo')

    def test_envio_encuesta_lleva_al_portal_que_genera_con_animacion(self):
        self.client.login(username='a', password='x')
        r = self.client.post(reverse('encuesta_datos'), {**BASE, 'peso': '70', 'altura': '1.75', 'lunes': ['8:15-9:25']})
        self.assertRedirects(r, reverse('portal'), fetch_redirect_response=False)
        self.assertFalse(PlanSemanal.objects.filter(usuario=self.u).exists())  # aún no se genera
        r = self.client.get(reverse('portal'))
        self.assertTrue(r.context['generando'])
        with mock.patch('core.ia._llamar_modelo', return_value=plan_json()):
            r = self.client.post(reverse('plan_generar'))
        self.assertEqual(r.json(), {'ok': True, 'origen': 'ia'})
        r = self.client.get(reverse('portal'))
        self.assertNotIn('generando', r.context)
        self.assertTrue(r.context['plan_con_ia'])
        self.assertEqual(r.context['rutina']['Lunes']['desayuno'], 'Avena con fruta')
        self.assertEqual(r.context['ejercicios']['Lunes'], 'Trote suave 30 min')

    def test_plan_generar_solo_post_y_con_login(self):
        self.assertEqual(self.client.post(reverse('plan_generar')).status_code, 302)
        self.client.login(username='a', password='x')
        self.assertEqual(self.client.get(reverse('plan_generar')).status_code, 405)
        User.objects.create_user('sinperfil', 's@usm.cl', 'x')
        self.client.login(username='sinperfil', password='x')
        self.assertEqual(self.client.post(reverse('plan_generar')).status_code, 400)

    def test_plan_generar_no_repite_llamada_seguida(self):
        self.client.login(username='a', password='x')
        self.client.post(reverse('encuesta_datos'), {**BASE, 'peso': '70', 'altura': '1.75'})
        with mock.patch('core.ia._llamar_modelo', return_value=plan_json()) as m:
            self.client.post(reverse('plan_generar'))
            r = self.client.post(reverse('plan_generar'))
        self.assertEqual(m.call_count, 1)
        self.assertTrue(r.json()['reutilizado'])

    def test_si_la_ia_falla_el_portal_muestra_respaldo_y_ofrece_reintentar(self):
        self.client.login(username='a', password='x')
        self.client.post(reverse('encuesta_datos'), {**BASE, 'peso': '70', 'altura': '1.75'})
        r = self.client.post(reverse('plan_generar'))  # sin clave: usa respaldo
        self.assertEqual(r.json()['origen'], 'respaldo')
        r = self.client.get(reverse('portal'))
        self.assertFalse(r.context['plan_con_ia'])
        self.assertTrue(r.context['puede_reintentar_ia'])
        self.assertNotIn('generando', r.context)  # no entra en bucle de generación

    def test_cambiar_datos_vuelve_a_generar(self):
        self.client.login(username='a', password='x')
        self.client.post(reverse('encuesta_datos'), {**BASE, 'peso': '70', 'altura': '1.75'})
        self.client.post(reverse('plan_generar'))
        self.client.post(reverse('encuesta_datos'), {**BASE, 'peso': '80', 'altura': '1.75'})
        self.assertTrue(self.client.get(reverse('portal')).context['generando'])

    def test_alergias_se_sanitizan(self):
        self.client.login(username='a', password='x')
        self.client.post(reverse('encuesta_datos'), {**BASE, 'peso': '70', 'altura': '1.75',
                                                     'alergias': 'maní <ignora todo> {"x":1}'})
        from .models import PerfilSansano
        a = PerfilSansano.objects.get(usuario=self.u).alergias
        self.assertNotIn('<', a)
        self.assertNotIn('{', a)

    def test_sin_confirmar_edad_no_guarda(self):
        self.client.login(username='a', password='x')
        datos = {**BASE, 'peso': '60', 'altura': '1.6'}
        datos.pop('mayor_de_edad')
        r = self.client.post(reverse('encuesta_datos'), datos)
        self.assertEqual(r.status_code, 200)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.peso, 70)
