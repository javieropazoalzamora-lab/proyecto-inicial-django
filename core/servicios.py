"""Orquesta la generación y el guardado del plan semanal."""
import hashlib
import json
import logging

from . import ia, planes_base
from .horarios import ventanas_con_minutos, viaje_del_dia
from .constantes import DIAS, ETIQUETAS_DIA
from .models import PlanSemanal

logger = logging.getLogger(__name__)

AVISO_ALERGIAS = "Revisa que ningún plato contenga ingredientes a los que eres alérgico o intolerante."


def construir_datos(perfil):
    """Datos anónimos para el plan y para la IA (sin nombre, usuario ni correo)."""
    return {
        'imc': perfil.imc,
        'categoria_imc': planes_base.clasificar_imc(perfil.imc),
        'bloques_libres': perfil.bloques_libres,
        'ventanas_libres': {d: ventanas_con_minutos(perfil.bloques_libres.get(d), (perfil.clases or {}).get(d))
                            for d in DIAS},
        # Solo días con clases: primera/última clase y, si hay transporte, cuándo sale y llega a casa
        'dias_con_clases': {d: v for d in DIAS
                            if (v := viaje_del_dia((perfil.clases or {}).get(d), perfil.tiempo_transporte_min))},
        'tiempo_transporte_min': perfil.tiempo_transporte_min,
        'actividad_fisica': perfil.actividad_fisica,
        'objetivo': perfil.objetivo,
        'tipo_dieta': perfil.tipo_dieta,
        'alergias': perfil.alergias,
        'presupuesto': perfil.presupuesto,
        'tiempo_cocina': perfil.tiempo_cocina,
        'lugar_entrenamiento': perfil.lugar_entrenamiento,
        'tiene_lesion': perfil.tiene_lesion,
    }


def _huella(datos):
    return hashlib.sha256(json.dumps(datos, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def huella_actual(perfil):
    return _huella(construir_datos(perfil))


def plan_vigente(perfil, plan):
    """True si el plan guardado corresponde a los datos actuales del perfil."""
    return plan is not None and plan.huella == huella_actual(perfil)


def generar_y_guardar_plan(perfil, usar_ia=True):
    """Genera (una vez) el plan del perfil y lo guarda. Nunca lanza por fallos de la IA."""
    datos = construir_datos(perfil)
    huella = _huella(datos)
    existente = PlanSemanal.objects.filter(usuario=perfil.usuario).first()

    if existente and existente.huella == huella and (existente.origen == 'ia' or not usar_ia):
        return existente  # mismos datos: no se gasta otra llamada a la API

    contenido, origen = None, 'respaldo'
    if usar_ia and perfil.mayor_de_edad:
        try:
            contenido = ia.generar_plan_ia(datos)
            origen = 'ia'
        except ia.PlanIAError as exc:
            logger.warning("Plan IA no disponible, se usa el de respaldo: %s", exc)
    if contenido is None:
        contenido = planes_base.plan_respaldo(datos)

    if origen == 'ia' and datos['alergias']:
        contenido['advertencia'] = AVISO_ALERGIAS
    if origen == 'ia' and datos['tipo_dieta'] == 'vegana':
        contenido['advertencia'] = ((contenido['advertencia'] or '') +
                                    " Revisa que el menú sea 100% vegano.").strip()
    if origen == 'ia' and datos['tiene_lesion']:
        contenido['advertencia'] = ((contenido['advertencia'] or '') +
                                    " Indicaste una molestia o lesión: consulta a un profesional antes de entrenar.").strip()

    plan, _ = PlanSemanal.objects.update_or_create(
        usuario=perfil.usuario,
        defaults={'contenido': contenido, 'origen': origen, 'huella': huella},
    )
    return plan


def plan_a_contexto(contenido):
    """Convierte el plan guardado a los dicts que usa portal.html: rutina y ejercicios."""
    rutina, ejercicios = {}, {}
    for dia in DIAS:
        d = contenido['dias'][dia]
        rutina[ETIQUETAS_DIA[dia]] = {k: d.get(k, '') for k in ('desayuno', 'almuerzo', 'once', 'colacion')}
        ejercicios[ETIQUETAS_DIA[dia]] = d['actividad']
    return rutina, ejercicios
