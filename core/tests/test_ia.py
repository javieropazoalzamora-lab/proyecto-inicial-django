"""Validación del plan de la IA y orquestación del servicio de planes."""
import json
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .. import ia
from .. import servicios
from ..constantes import DIAS
from ..models import PlanSemanal
from .utilidades import BASE, SinClaveMixin, plan_json, DATOS


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
        from ..models import PerfilSansano
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
        # La IA no mandó rutina estructurada: se usa la rutina base y su resumen
        self.assertIn('45 min', r.context['ejercicios']['Lunes'])
        self.assertContains(r, 'Fuerza con peso corporal')

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
        from ..models import PerfilSansano
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
