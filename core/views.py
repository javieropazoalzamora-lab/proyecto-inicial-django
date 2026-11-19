import logging

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode, url_has_allowed_host_and_scheme

from .constantes import (DIAS_CORTOS, MODULOS, ACTIVIDADES, BLOQUES_VALIDOS, DIAS, ETIQUETAS_DIA, DIETAS, LUGARES, OBJETIVOS,
                         PRESUPUESTOS, TIEMPOS_COCINA)
from .forms import RegistroSansanoForm, EncuestaPerfilForm
from .models import PerfilSansano, PlanSemanal
from . import planes_base, servicios
from .horarios import ventanas_texto, modulos_cubiertos, modulos_desde_post, viaje_del_dia

logger = logging.getLogger(__name__)


# ============================================================================
# Páginas públicas
# ============================================================================

def inicio(request):
    return render(request, 'core/inicio.html')


# ============================================================================
# Cuentas: login, registro, activación por correo y logout
# ============================================================================

def _destino_seguro(request):
    """Devuelve ?next= solo si apunta a este mismo sitio (evita redirecciones abiertas)."""
    destino = request.POST.get('next') or request.GET.get('next')
    if destino and url_has_allowed_host_and_scheme(
            destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return destino
    return None


def _destino_por_defecto(usuario):
    # Si ya completó la encuesta va directo al portal; si no, a la encuesta
    if PerfilSansano.objects.filter(usuario=usuario).exists():
        return redirect('portal')
    return redirect('encuesta_datos')


def _enviar_correo_activacion(request, usuario):
    """Envía el correo de verificación (HTML + texto plano). Lanza la excepción si el envío falla."""
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    contexto = {
        'usuario': usuario,
        # build_absolute_uri respeta el dominio y el esquema real (http/https)
        'enlace': request.build_absolute_uri(reverse('activar_cuenta', args=[uid, token])),
        'dias_validez': max(settings.PASSWORD_RESET_TIMEOUT // 86400, 1),
    }
    correo = EmailMultiAlternatives(
        subject="Activa tu cuenta de VitaSansano",
        body=render_to_string('core/emails/activacion.txt', contexto),
        to=[usuario.email],
    )
    correo.attach_alternative(render_to_string('core/emails/activacion.html', contexto), 'text/html')
    correo.send()


def iniciar_sesion(request):
    if request.user.is_authenticated:
        return _destino_por_defecto(request.user)
    cuenta_pendiente = False
    if request.method == 'POST':
        formulario = AuthenticationForm(request, data=request.POST)
        if formulario.is_valid():
            usuario = formulario.get_user()
            login(request, usuario)
            messages.success(request, f"¡Hola de nuevo, {usuario.username}!")
            destino = _destino_seguro(request)
            return redirect(destino) if destino else _destino_por_defecto(usuario)
        # Clave correcta pero cuenta sin activar: se explica y se reenvía el correo.
        # (Solo quien conoce la clave ve este aviso, así que no revela qué cuentas existen.)
        pendiente = User.objects.filter(username=request.POST.get('username', ''), is_active=False).first()
        if pendiente and pendiente.check_password(request.POST.get('password', '')):
            cuenta_pendiente = True
            try:
                _enviar_correo_activacion(request, pendiente)
                messages.warning(request, f"Tu cuenta aún no está activada. Te reenviamos el enlace a "
                                          f"{pendiente.email} (revisa también la carpeta de spam).")
            except Exception:
                logger.exception("No se pudo reenviar el correo de activación")
                messages.error(request, "Tu cuenta aún no está activada y no pudimos reenviar el correo. "
                                        "Intenta más tarde.")
    else:
        formulario = AuthenticationForm(request)
    return render(request, 'core/cuentas/login.html', {
        'form': formulario, 'next': _destino_seguro(request) or '', 'cuenta_pendiente': cuenta_pendiente})


def registrar_usuario(request):
    if request.user.is_authenticated:
        return _destino_por_defecto(request.user)
    if request.method == 'POST':
        form = RegistroSansanoForm(request.POST)
        if form.is_valid():
            try:
                # Todo o nada: si el correo no se puede enviar, la cuenta no queda creada.
                with transaction.atomic():
                    # Cuentas anteriores con este correo que nunca se activaron: se descartan,
                    # para que nadie pueda "reservar" el correo de otra persona.
                    User.objects.filter(email__iexact=form.cleaned_data['email'], is_active=False).delete()
                    usuario = form.save(commit=False)
                    usuario.is_active = False  # La cuenta nace bloqueada hasta verificar el correo
                    usuario.save()
                    _enviar_correo_activacion(request, usuario)
            except Exception:
                logger.exception("Falló el envío del correo de activación")
                messages.error(request, "No pudimos enviar el correo de verificación. Revisa que la dirección "
                                        "sea correcta e inténtalo de nuevo en unos minutos.")
            else:
                messages.success(request, f"¡Cuenta creada! Te enviamos un enlace de activación a {usuario.email}. "
                                          "Ábrelo para entrar (revisa también la carpeta de spam).")
                return redirect('login')
    else:
        form = RegistroSansanoForm()
    return render(request, 'core/cuentas/registro.html', {'form': form})


def activar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        usuario = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        usuario = None

    if usuario is not None and default_token_generator.check_token(usuario, token):
        usuario.is_active = True
        usuario.save(update_fields=['is_active'])
        login(request, usuario)
        messages.success(request, "¡Correo verificado! Completa la encuesta para generar tu plan semanal.")
        return redirect('encuesta_datos')
    messages.error(request, "El enlace de activación no es válido o ya venció. Si tu cuenta sigue sin activar, "
                            "inicia sesión con tu clave y te enviaremos uno nuevo.")
    return redirect('login')


@require_POST
def cerrar_sesion(request):
    # Solo por POST (con token CSRF): un <img src="/logout/"> en otro sitio ya no cierra tu sesión.
    logout(request)
    messages.info(request, "Cerraste sesión. ¡Hasta pronto!")
    return redirect(settings.LOGOUT_REDIRECT_URL)


# ============================================================================
# Encuesta de perfil (Mis datos y horarios)
# ============================================================================

def construir_grilla(estados):
    """estados: {dia: (libres, clases)} -> filas por módulo con el estado de cada día."""
    filas = []
    for n, ini, fin in MODULOS:
        celdas = []
        for d in DIAS:
            libres, clases = estados[d]
            estado = 'clase' if n in clases else 'libre' if n in libres else ''
            celdas.append({'dia': d, 'etiqueta': ETIQUETAS_DIA[d], 'estado': estado})
        filas.append({'n': n, 'ini': ini, 'fin': fin, 'celdas': celdas})
    return filas


@login_required
def encuesta_datos(request):
    """Encuesta de perfil (única vista; sirve para crear y para editar)."""
    perfil = PerfilSansano.objects.filter(usuario=request.user).first()

    if request.method == 'POST':
        form = EncuestaPerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            es_nuevo = perfil is None
            perfil = form.save(commit=False)
            perfil.usuario = request.user   # el dueño SIEMPRE es quien inició sesión
            perfil.save()
            if es_nuevo:
                messages.success(request, "¡Encuesta guardada! Estamos preparando tu plan semanal.")
            else:
                messages.success(request, "Tus datos se actualizaron. Si cambiaron, tu plan se vuelve a generar.")
            # El plan se genera en el portal (con animación) mediante plan_generar.
            return redirect('portal')
        # (Los errores ya se listan en detalle dentro de formulario.html.)
        # Un ModelForm inválido deja el objeto en memoria con los datos erróneos: se recarga el guardado.
        perfil = PerfilSansano.objects.filter(usuario=request.user).first()
    else:
        form = EncuestaPerfilForm(instance=perfil)

    # Valores a mostrar: lo que se envió (si hubo error) o lo ya guardado
    if request.method == 'POST':
        peso_val = request.POST.get('peso', '')
        altura_val = request.POST.get('altura', '')
        transporte_val = request.POST.get('tiempo_transporte_min', '')
        estados = {d: modulos_desde_post(request.POST, d) for d in DIAS}
        actual = {k: request.POST.get(k, '') for k in
                  ('actividad_fisica', 'objetivo', 'tipo_dieta', 'presupuesto', 'tiempo_cocina', 'lugar_entrenamiento', 'alergias')}
        actual['mayor_de_edad'] = 'mayor_de_edad' in request.POST
        actual['tiene_lesion'] = 'tiene_lesion' in request.POST
    else:
        peso_val = perfil.peso if perfil else ''
        altura_val = perfil.altura if perfil else ''
        transporte_val = (perfil.tiempo_transporte_min if perfil and perfil.tiempo_transporte_min is not None else '')
        estados = {d: (modulos_cubiertos((perfil.bloques_libres or {}).get(d)) - set((perfil.clases or {}).get(d, [])),
                       set((perfil.clases or {}).get(d, []))) if perfil else (set(), set()) for d in DIAS}
        actual = {
            'actividad_fisica': perfil.actividad_fisica if perfil else 'moderada',
            'objetivo': perfil.objetivo if perfil else 'mantener',
            'tipo_dieta': perfil.tipo_dieta if perfil else 'omnivora',
            'presupuesto': perfil.presupuesto if perfil else 'medio',
            'tiempo_cocina': perfil.tiempo_cocina if perfil else 'normal',
            'lugar_entrenamiento': perfil.lugar_entrenamiento if perfil else 'casa',
            'alergias': perfil.alergias if perfil else '',
            'mayor_de_edad': bool(perfil and perfil.mayor_de_edad),
            'tiene_lesion': bool(perfil and perfil.tiene_lesion),
        }

    def opciones(choices, clave):
        return [{'valor': v, 'etiqueta': e, 'marcado': v == actual[clave]} for v, e in choices]

    grilla = construir_grilla(estados)

    return render(request, 'core/plan/formulario.html', {
        'bloques_horarios': BLOQUES_VALIDOS,
        'perfil': perfil,
        'form': form,
        'grilla': grilla,
        'dias_cols': [{'clave': d, 'corta': DIAS_CORTOS[d], 'etiqueta': ETIQUETAS_DIA[d]} for d in DIAS],
        'peso_val': peso_val,
        'altura_val': altura_val,
        'transporte_val': transporte_val,
        'opc_actividad': opciones(ACTIVIDADES, 'actividad_fisica'),
        'opc_objetivo': opciones(OBJETIVOS, 'objetivo'),
        'opc_dieta': opciones(DIETAS, 'tipo_dieta'),
        'opc_presupuesto': opciones(PRESUPUESTOS, 'presupuesto'),
        'opc_cocina': opciones(TIEMPOS_COCINA, 'tiempo_cocina'),
        'opc_lugar': opciones(LUGARES, 'lugar_entrenamiento'),
        'alergias_val': actual['alergias'],
        'mayor_val': actual['mayor_de_edad'],
        'lesion_val': actual['tiene_lesion'],
    })


# Compatibilidad con urls.py existente: ambas rutas usan la misma vista.
editar_perfil = encuesta_datos


# ============================================================================
# Portal: plan semanal
# ============================================================================

@login_required
def portal(request):
    perfil = PerfilSansano.objects.filter(usuario=request.user).first()
    imc = perfil.imc if perfil else None

    rutina_alimentacion = {}
    rutina_ejercicios = {}
    tipo_imc = "Sin datos"
    bloques_libres = perfil.bloques_libres if perfil else {}
    alerta = None
    plan = None
    semana = []
    grilla = []

    if imc is not None:
        tipo_imc = planes_base.perfil_alimentacion(imc, perfil.actividad_fisica)[1]['etiqueta']
        alerta = planes_base.alerta_profesional(imc)
        plan = PlanSemanal.objects.filter(usuario=request.user).first()
        if not servicios.plan_vigente(perfil, plan):
            if perfil.mayor_de_edad:
                # Hay que (re)generar: el portal muestra la animación y el navegador llama a plan_generar.
                return render(request, 'core/plan/portal.html', {
                    'perfil': perfil, 'generando': True, 'aviso_salud': planes_base.AVISO_SALUD,
                })
            # Sin confirmación de mayoría de edad no se usa IA: plan por reglas, sin esperar.
            plan = servicios.generar_y_guardar_plan(perfil, usar_ia=False)
        rutina_alimentacion, rutina_ejercicios = servicios.plan_a_contexto(plan.contenido)
        clases_perfil = perfil.clases or {}
        grilla = construir_grilla({
            d: (modulos_cubiertos(bloques_libres.get(d)) - set(clases_perfil.get(d, [])), set(clases_perfil.get(d, [])))
            for d in DIAS})
        for dia in DIAS:
            d = plan.contenido['dias'][dia]
            semana.append({
                'dia': ETIQUETAS_DIA[dia],
                'desayuno': d['desayuno'], 'almuerzo': d['almuerzo'], 'once': d['once'],
                'colacion': d.get('colacion', ''),
                'actividad': d['actividad'],
                'rutina': d.get('rutina'),
                'descanso': not bloques_libres.get(dia),
                'viaje': viaje_del_dia(clases_perfil.get(dia), perfil.tiempo_transporte_min),
                # El horario se muestra aparte solo si el texto de la actividad no lo repite
                'bloques': ('' if not d.get('rutina') and any(v in d['actividad'] for v in ventanas_texto(bloques_libres.get(dia)))
                            else ' · '.join(ventanas_texto(bloques_libres.get(dia)))),
            })

    return render(request, 'core/plan/portal.html', {
        'perfil': perfil,
        'tipo_imc': tipo_imc,
        'rutina': rutina_alimentacion,
        'ejercicios': rutina_ejercicios,
        'bloques_libres': bloques_libres,
        'aviso_salud': planes_base.AVISO_SALUD,
        'alerta_profesional': alerta,
        'plan': plan,
        'semana': semana,
        'grilla': grilla,
        'hay_clases': any((perfil.clases or {}).values()) if perfil else False,
        'dias_cols': [{'clave': d, 'corta': DIAS_CORTOS[d], 'etiqueta': ETIQUETAS_DIA[d]} for d in DIAS],
        'resumen_plan': plan.contenido.get('resumen') if plan else None,
        'consejos': plan.contenido.get('consejos', []) if plan else [],
        'advertencia_plan': plan.contenido.get('advertencia') if plan else None,
        'plan_con_ia': bool(plan and plan.origen == 'ia'),
        'falta_completar': bool(perfil and not perfil.mayor_de_edad),
        'puede_reintentar_ia': bool(plan and plan.origen == 'respaldo' and perfil.mayor_de_edad),
    })


ESPERA_MIN_SEG = 15


@login_required
@require_POST
def plan_generar(request):
    """Genera (con IA y respaldo) y guarda el plan. Lo llama el portal por fetch."""
    perfil = PerfilSansano.objects.filter(usuario=request.user).first()
    if perfil is None or perfil.imc is None:
        return JsonResponse({'ok': False, 'error': 'Falta completar la encuesta.'}, status=400)
    plan = PlanSemanal.objects.filter(usuario=request.user).first()
    if plan and plan.huella == servicios.huella_actual(perfil) and \
            (timezone.now() - plan.actualizado).total_seconds() < ESPERA_MIN_SEG:
        # Evita gastar cuota con clics repetidos: se devuelve el plan que ya está guardado.
        return JsonResponse({'ok': True, 'origen': plan.origen, 'reutilizado': True})
    plan = servicios.generar_y_guardar_plan(perfil, usar_ia=perfil.mayor_de_edad)
    return JsonResponse({'ok': True, 'origen': plan.origen})
