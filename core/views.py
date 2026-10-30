from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import PerfilSansano
from .forms import RegistroSansanoForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.http import HttpResponse

BLOQUES_VALIDOS = [
    '8:15-9:25', 
    '9:40-10:50', 
    '11:05-12:15', 
    '12:30-13:40', 
    '14:40-15:50', 
    '16:05-17:15', 
    '17:30-18:40'
]
# 1. Vista de Inicio (La que causaba el error)
def inicio(request):
    return redirect('login') 

# 2. Vista de Login (Renombrada para coincidir con urls.py)
def iniciar_sesion(request):
    if request.method == 'POST':
        formulario = AuthenticationForm(request, data=request.POST)
        if formulario.is_valid():
            usuario = formulario.get_user()
            login(request, usuario)
            return redirect('encuesta_datos') 
    else:
        formulario = AuthenticationForm()
    return render(request, 'core2/login.html', {'form': formulario})

# 3. Vista de Registro con restricción @usm.cl
def registrar_usuario(request):
    if request.method == 'POST':
        form = RegistroSansanoForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.is_active = False  # La cuenta nace bloqueada
            usuario.save()
            
            # Generar enlace criptográfico de un solo uso
            dominio = get_current_site(request).domain
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)
            enlace = f"http://{dominio}/activar/{uid}/{token}/"
            
            # Construir y enviar el correo
            asunto = "Activa tu cuenta de Recomendador USM"
            mensaje = f"Haz clic en este enlace para confirmar tu correo @usm.cl e iniciar sesión:\n\n{enlace}"
            correo = EmailMessage(asunto, mensaje, to=[usuario.email])
            correo.send()
            
            # Retorna texto plano temporal para evitar crear otro HTML
            return HttpResponse("Cuenta creada. Revisa tu correo institucional para activarla.")
    else:
        form = RegistroSansanoForm()
    return render(request, 'core2/registro.html', {'form': form})

def activar_cuenta(request, uidb64, token):
    try:
        # Desencriptar el ID para buscar al usuario
        uid = force_str(urlsafe_base64_decode(uidb64))
        usuario = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        usuario = None

    # Verificar que el usuario existe y que el token no ha sido alterado ni usado
    if usuario is not None and default_token_generator.check_token(usuario, token):
        usuario.is_active = True
        usuario.save()
        login(request, usuario)
        return redirect('encuesta_datos')
    else:
        return HttpResponse("El enlace de activación es inválido o ya expiró.")

# 4. Vista para cerrar sesión
def cerrar_sesion(request):
    logout(request)
    return redirect('login')

# 5. Vista de Encuesta (Renombrada para coincidir con urls.py)
@login_required
def editar_perfil(request):
    # Busca si el usuario ya tiene datos guardados
    try:
        perfil = PerfilSansano.objects.get(usuario=request.user)
    except PerfilSansano.DoesNotExist:
        perfil = None

    if request.method == 'POST':
        peso = request.POST.get('peso')
        altura = request.POST.get('altura')
        
        dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        bloques = {dia: request.POST.get(dia, 'Sin tiempo libre') for dia in dias}
        
        if peso and altura:
            PerfilSansano.objects.update_or_create(
                usuario=request.user,
                defaults={
                    'peso': float(peso.replace(',', '.')),
                    'altura': float(altura.replace(',', '.')),
                    'bloques_libres': str(bloques)
                }
            )
        return redirect('portal')
        
    return render(request, 'core2/formulario.html', {'perfil': perfil})

@login_required(login_url='login')
def encuesta_datos(request):
    if request.method == 'POST':
        # 1. Obtener peso y altura enviados desde el formulario
        peso_str = request.POST.get('peso', '0').replace(',', '.')
        altura_str = request.POST.get('altura', '0').replace(',', '.')
        
        try:
            peso = float(peso_str)
            altura = float(altura_str)
        except ValueError:
            peso = 0.0
            altura = 0.0

        # Si la altura la ingresan en centímetros (ej: 175), la pasamos a metros (1.75)
        altura_m = altura / 100 if altura > 3 else altura

        # 2. Calcular el IMC (IMC = peso / altura^2)
        imc = round(peso / (altura_m ** 2), 2) if altura_m > 0 else 0.0

        # 3. Obtener el bloque seleccionado para cada día
        dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        bloques = {}
        
        for dia in dias:
            bloque_seleccionado = request.POST.get(dia)
            # Validamos que el bloque seleccionado esté dentro de las opciones permitidas
            if bloque_seleccionado in BLOQUES_VALIDOS:
                bloques[dia] = bloque_seleccionado
            else:
                bloques[dia] = 'Sin tiempo libre'

        # 4. Guardar o actualizar en la base de datos
        PerfilSansano.objects.update_or_create(
            usuario=request.user,
            defaults={
                'peso': peso,
                'altura': altura,
                'imc': imc,                     # Campo para almacenar el IMC
                'bloques_libres': str(bloques)  # Guarda el diccionario como texto o JSON
            }
        )

        # 5. Redirigir a la vista del portal tras presionar "Generar"
        return redirect('portal')

    # Si es petición GET, se renderiza el formulario
    return render(request, 'core2/formulario.html', {
        'bloques_horarios': BLOQUES_VALIDOS
    })

# 6. Vista del Portal
@login_required
def portal(request):
    return render(request, 'core2/portal.html')