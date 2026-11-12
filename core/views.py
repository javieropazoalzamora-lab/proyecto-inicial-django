from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .constantes import (ACTIVIDADES, BLOQUES_VALIDOS, DIAS, ETIQUETAS_DIA, DIETAS, LUGARES, OBJETIVOS,
                         PRESUPUESTOS, TIEMPOS_COCINA)
from .forms import RegistroSansanoForm, EncuestaPerfilForm
from .models import PerfilSansano, PlanSemanal
from . import planes_base, servicios


def inicio(request):
    return redirect('login')


def iniciar_sesion(request):
    if request.method == 'POST':
        formulario = AuthenticationForm(request, data=request.POST)
        if formulario.is_valid():
            usuario = formulario.get_user()
            login(request, usuario)
            # Si ya completó la encuesta va directo al portal; si no, a la encuesta
            if PerfilSansano.objects.filter(usuario=usuario).exists():
                return redirect('portal')
            return redirect('encuesta_datos')
    else:
        formulario = AuthenticationForm()
    return render(request, 'core2/login.html', {'form': formulario})


def registrar_usuario(request):
    if request.method == 'POST':
        form = RegistroSansanoForm(request.POST)
        if form.is_valid():
            # Cuentas anteriores con este correo que nunca se activaron: se descartan,
            # para que nadie pueda "reservar" el correo de otra persona.
            User.objects.filter(email__iexact=form.cleaned_data['email'], is_active=False).delete()
            usuario = form.save(commit=False)
            usuario.is_active = False  # La cuenta nace bloqueada hasta verificar el correo
            usuario.save()

            dominio = get_current_site(request).domain
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)
            enlace = f"http://{dominio}/activar/{uid}/{token}/"

            asunto = "Activa tu cuenta de Recomendador USM"
            mensaje = f"Haz clic en este enlace para confirmar tu correo @usm.cl e iniciar sesión:\n\n{enlace}"
            EmailMessage(asunto, mensaje, to=[usuario.email]).send()

            return HttpResponse("Cuenta creada. Revisa tu correo institucional para activarla.")
    else:
        form = RegistroSansanoForm()
    return render(request, 'core2/registro.html', {'form': form})


def activar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        usuario = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        usuario = None

    if usuario is not None and default_token_generator.check_token(usuario, token):
        usuario.is_active = True
        usuario.save()
        login(request, usuario)
        return redirect('encuesta_datos')
    return HttpResponse("El enlace de activación es inválido o ya expiró.")


def cerrar_sesion(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def encuesta_datos(request):
    """Encuesta de perfil (única vista; sirve para crear y para editar)."""
    perfil = PerfilSansano.objects.filter(usuario=request.user).first()

    if request.method == 'POST':
        form = EncuestaPerfilForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            perfil, _ = PerfilSansano.objects.update_or_create(
                usuario=request.user,
                defaults={
                    'peso': cd['peso'],
                    'altura': cd['altura'],
                    'bloques_libres': cd['bloques'],
                    'tiempo_transporte_min': cd['tiempo_transporte_min'],
                    'mayor_de_edad': cd['mayor_de_edad'],
                    'actividad_fisica': cd['actividad_fisica'],
                    'objetivo': cd['objetivo'],
                    'tipo_dieta': cd['tipo_dieta'],
                    'alergias': cd['alergias'],
                    'presupuesto': cd['presupuesto'],
                    'tiempo_cocina': cd['tiempo_cocina'],
                    'lugar_entrenamiento': cd['lugar_entrenamiento'],
                    'tiene_lesion': cd['tiene_lesion'],
                },
            )
            # Se genera UNA vez aquí (IA con respaldo); el portal solo lee el plan guardado.
            servicios.generar_y_guardar_plan(perfil)
            return redirect('portal')
    else:
        form = EncuestaPerfilForm()

    # Valores a mostrar: lo que se envió (si hubo error) o lo ya guardado
    if request.method == 'POST':
        peso_val = request.POST.get('peso', '')
        altura_val = request.POST.get('altura', '')
        transporte_val = request.POST.get('tiempo_transporte_min', '')
        elegidos = {d: request.POST.getlist(d) for d in DIAS}
        actual = {k: request.POST.get(k, '') for k in
                  ('actividad_fisica', 'objetivo', 'tipo_dieta', 'presupuesto', 'tiempo_cocina', 'lugar_entrenamiento', 'alergias')}
        actual['mayor_de_edad'] = 'mayor_de_edad' in request.POST
        actual['tiene_lesion'] = 'tiene_lesion' in request.POST
    else:
        peso_val = perfil.peso if perfil else ''
        altura_val = perfil.altura if perfil else ''
        transporte_val = (perfil.tiempo_transporte_min if perfil and perfil.tiempo_transporte_min is not None else '')
        elegidos = perfil.bloques_libres if perfil else {}
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

    dias_ui = [
        {
            'clave': d,
            'etiqueta': d.capitalize() if d != 'miercoles' else 'Miércoles',
            'bloques': [{'valor': b, 'marcado': b in (elegidos.get(d) or [])} for b in BLOQUES_VALIDOS],
        }
        for d in DIAS
    ]
    if d_sab := next((x for x in dias_ui if x['clave'] == 'sabado'), None):
        d_sab['etiqueta'] = 'Sábado'

    return render(request, 'core2/formulario.html', {
        'bloques_horarios': BLOQUES_VALIDOS,
        'perfil': perfil,
        'form': form,
        'dias_ui': dias_ui,
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

    if imc is not None:
        tipo_imc = planes_base.perfil_alimentacion(imc, perfil.actividad_fisica)[1]['etiqueta']
        alerta = planes_base.alerta_profesional(imc)
        plan = PlanSemanal.objects.filter(usuario=request.user).first()
        if plan is None:
            # Perfiles anteriores a la IA: plan por reglas, sin llamar a la API desde el portal.
            plan = servicios.generar_y_guardar_plan(perfil, usar_ia=False)
        rutina_alimentacion, rutina_ejercicios = servicios.plan_a_contexto(plan.contenido)
        for dia in DIAS:
            d = plan.contenido['dias'][dia]
            semana.append({
                'dia': ETIQUETAS_DIA[dia],
                'desayuno': d['desayuno'], 'almuerzo': d['almuerzo'], 'once': d['once'],
                'colacion': d.get('colacion', ''),
                'actividad': d['actividad'],
                'descanso': not bloques_libres.get(dia),
                'bloques': ('' if any(b in d['actividad'] for b in (bloques_libres.get(dia) or []))
                            else ' · '.join(bloques_libres.get(dia) or [])),
            })

    return render(request, 'core2/portal.html', {
        'perfil': perfil,
        'tipo_imc': tipo_imc,
        'rutina': rutina_alimentacion,
        'ejercicios': rutina_ejercicios,
        'bloques_libres': bloques_libres,
        'aviso_salud': planes_base.AVISO_SALUD,
        'alerta_profesional': alerta,
        'plan': plan,
        'semana': semana,
        'resumen_plan': plan.contenido.get('resumen') if plan else None,
        'consejos': plan.contenido.get('consejos', []) if plan else [],
        'advertencia_plan': plan.contenido.get('advertencia') if plan else None,
        'plan_con_ia': bool(plan and plan.origen == 'ia'),
        'falta_completar': bool(perfil and not perfil.mayor_de_edad),
    })
