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

from .constantes import BLOQUES_VALIDOS, DIAS
from .forms import RegistroSansanoForm, EncuestaPerfilForm
from .models import PerfilSansano
from . import planes_base


def inicio(request):
    return redirect('login')


def iniciar_sesion(request):
    if request.method == 'POST':
        formulario = AuthenticationForm(request, data=request.POST)
        if formulario.is_valid():
            login(request, formulario.get_user())
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
            PerfilSansano.objects.update_or_create(
                usuario=request.user,
                defaults={
                    'peso': form.cleaned_data['peso'],
                    'altura': form.cleaned_data['altura'],
                    'bloques_libres': form.cleaned_data['bloques'],
                    'tiempo_transporte_min': form.cleaned_data['tiempo_transporte_min'],
                },
            )
            return redirect('portal')
    else:
        form = EncuestaPerfilForm()

    # Valores a mostrar: lo que se envió (si hubo error) o lo ya guardado
    if request.method == 'POST':
        peso_val = request.POST.get('peso', '')
        altura_val = request.POST.get('altura', '')
        transporte_val = request.POST.get('tiempo_transporte_min', '')
        elegidos = {d: request.POST.getlist(d) for d in DIAS}
    else:
        peso_val = perfil.peso if perfil else ''
        altura_val = perfil.altura if perfil else ''
        transporte_val = (perfil.tiempo_transporte_min if perfil and perfil.tiempo_transporte_min is not None else '')
        elegidos = perfil.bloques_libres if perfil else {}

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

    if imc is not None:
        categoria = planes_base.clasificar_imc(imc)
        tipo_imc = planes_base.ETIQUETAS[categoria]
        rutina_alimentacion = planes_base.PLAN_ALIMENTACION[categoria]
        rutina_ejercicios = planes_base.ejercicios_base(categoria, bloques_libres)
        alerta = planes_base.alerta_profesional(imc)

    return render(request, 'core2/portal.html', {
        'perfil': perfil,
        'tipo_imc': tipo_imc,
        'rutina': rutina_alimentacion,
        'ejercicios': rutina_ejercicios,
        'bloques_libres': bloques_libres,
        'aviso_salud': planes_base.AVISO_SALUD,
        'alerta_profesional': alerta,
    })
