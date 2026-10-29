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

@login_required
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

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import PerfilSansano
import ast  # Para convertir el string de bloques guardado de vuelta en diccionario

@login_required
def portal(request):
    try:
        perfil = PerfilSansano.objects.get(usuario=request.user)
        imc = perfil.imc
        # Convertir el string de bloques guardado en el modelo de vuelta a un diccionario de Python
        bloques_libres = ast.literal_eval(perfil.bloques_libres) if perfil.bloques_libres else {}
    except PerfilSansano.DoesNotExist:
        perfil = None
        imc = None
        bloques_libres = {}

    rutina_alimentacion = {}
    rutina_ejercicios = {}
    tipo_imc = "Sin datos"

    if imc is not None:
        # --- 1. CLASIFICACIÓN Y DIETA (Igual que antes) ---
        if imc < 18.5:
            tipo_imc = "Bajo peso (Dieta hipercalórica saludable)"
            rutina_alimentacion = {
                'Lunes': {'desayuno': 'Avena con leche entera, plátano y mantequilla de maní', 'almuerzo': 'Arroz, pechuga de pollo a la plancha, palta y ensalada', 'once': 'Pan con huevo revuelto y un vaso de leche'},
                'Martes': {'desayuno': 'Pan con palta y un huevo duro, vaso de leche', 'almuerzo': 'Puré de papas con carne vacuna y ensalada mixta', 'once': 'Yogurt con granola y frutos secos'},
                'Miércoles': {'desayuno': 'Pancakes de avena y plátano con miel', 'almuerzo': 'Fideos con salsa boloñesa y queso rallado', 'once': 'Té con pan y queso mantecoso'},
                'Jueves': {'desayuno': 'Batido de plátano, avena, leche y mantequilla de maní', 'almuerzo': 'Arroz con atún, huevo duro y ensalada', 'once': 'Galletas de avena con leche'},
                'Viernes': {'desayuno': 'Tostadas con mantequilla de maní y rodajas de plátano', 'almuerzo': 'Lentejas con arroz y trozos de zapallo', 'once': 'Pan con palta y un vaso de leche'},
                'Sábado': {'desayuno': 'Revuelto de huevos con jamón y pan tostado', 'almuerzo': 'Carne al horno con papas doradas y ensalada', 'once': 'Queque casero con té o leche'},
                'Domingo': {'desayuno': 'Pudín de chía con leche y frutas', 'almuerzo': 'Pescado al horno con puré y ensalada', 'once': 'Pan con queso y un vaso de jugo natural'}
            }
        elif 18.5 <= imc < 25:
            tipo_imc = "Peso normal (Dieta equilibrada)"
            rutina_alimentacion = {
                'Lunes': {'desayuno': 'Yogurt descremado con avena y fruta fresca', 'almuerzo': 'Pechuga de pollo con quinoa y ensalada verde', 'once': 'Infusión con tostadas integrales y quesillo'},
                'Martes': {'desayuno': 'Tostada integral con palta y huevo pochado', 'almuerzo': 'Pescado al horno con papas cocidas y brócoli', 'once': 'Fruta y un puñado de almendras'},
                'Miércoles': {'desayuno': 'Batido verde (espinaca, manzana, plátano y agua)', 'almuerzo': 'Lentejas guisadas con verduras y un huevo duro', 'once': 'Yogurt con semillas de chía'},
                'Jueves': {'desayuno': 'Pan integral con jamón de pavo y queso fresco', 'almuerzo': 'Arroz integral con carne magra y ensalada mixta', 'once': 'Té con panqueques de avena'},
                'Viernes': {'desayuno': 'Omelette de claras con espinaca y tomate', 'almuerzo': 'Fideos integrales con salsa de tomate natural y pavo', 'once': 'Infusión con galletas de arroz y palta'},
                'Sábado': {'desayuno': 'Pancakes saludables de avena y plátano', 'almuerzo': 'Carne magra a la plancha con puré de zapallo y ensalada', 'once': 'Leche con pan integral y quesillo'},
                'Domingo': {'desayuno': 'Fruta picada con yogurt natural y nueces', 'almuerzo': 'Garbanzos salteados con verduras y pollo desmenuzado', 'once': 'Infusión con tostadas y mermelada sin azúcar'}
            }
        elif 25 <= imc < 30:
            tipo_imc = "Sobrepeso (Dieta de control calórico)"
            rutina_alimentacion = {
                'Lunes': {'desayuno': 'Infusión sin azúcar con tostada integral y quesillo light', 'almuerzo': 'Pechuga de pollo a la plancha con ensalada abundante de lechuga y tomate', 'once': 'Yogurt descremado con infusión'},
                'Martes': {'desayuno': 'Leche descremada con frutillas', 'almuerzo': 'Merluza al horno con puré de zapallo italiano y ensalada verde', 'once': 'Infusión con pan integral y palta (porción moderada)'},
                'Miércoles': {'desayuno': 'Yogurt descremado con avena', 'almuerzo': 'Sopa de verduras y porción pequeña de carne magra con ensalada', 'once': 'Infusión con galletas de arroz y quesillo'},
                'Jueves': {'desayuno': 'Omelette de claras con champiñones', 'almuerzo': 'Ensalada grande de atún al agua con huevo duro y verduras', 'once': 'Té con tostada integral y huevo'},
                'Viernes': {'desayuno': 'Infusión con pan integral y quesillo light', 'almuerzo': 'Pollo desmenuzado con mix de verduras salteadas y quinoa', 'once': 'Yogurt descremado'},
                'Sábado': {'desayuno': 'Pudín de chía con leche descremada y frutos rojos', 'almuerzo': 'Carne magra al horno con ensalada de brócoli y coliflor', 'once': 'Infusión con tostadas integrales'},
                'Domingo': {'desayuno': 'Huevos revueltos con tomate y té', 'almuerzo': 'Pescado al vapor con espárragos y ensalada mixta', 'once': 'Infusión con pan integral y quesillo'}
            }
        else:
            tipo_imc = "Obesidad (Dieta hipocalórica supervisada)"
            rutina_alimentacion = {
                'Lunes': {'desayuno': 'Infusión sin azúcar con una tostada integral y un huevo revuelto', 'almuerzo': 'Pechuga de pollo a la plancha con gran cantidad de ensalada verde', 'once': 'Yogurt descremado sin azúcar'},
                'Martes': {'desayuno': 'Leche descremada con avena y una fruta pequeña', 'almuerzo': 'Pescado blanco al horno con zapallo italiano y brócoli al vapor', 'once': 'Infusión con pan integral y quesillo descremado'},
                'Miércoles': {'desayuno': 'Infusión con dos huevos duros', 'almuerzo': 'Ensalada verde abundante con atún al agua y media porción de legumbres', 'once': 'Yogurt descremado con semillas'},
                'Jueves': {'desayuno': 'Batido de frutos rojos con leche descremada', 'almuerzo': 'Carne magra desgrasada con ensalada mixta de pepino y lechuga', 'once': 'Infusión con galletas de arroz'},
                'Viernes': {'desayuno': 'Infusión sin azúcar con tostada integral y poca palta', 'almuerzo': 'Pechuga de pavo al horno con verduras al vapor (sin aceite)', 'once': 'Infusión con un huevo duro'},
                'Sábado': {'desayuno': 'Omelette de claras con espinaca y tomate', 'almuerzo': 'Sopa clara de verduras y filete de pescado con espárragos', 'once': 'Yogurt descremado'},
                'Domingo': {'desayuno': 'Infusión con pan integral y quesillo', 'almuerzo': 'Ensalada grande con pollo grillado y verduras cocidas', 'once': 'Infusión con tostadas integrales'}
            }

       # // --- 2. LÓGICA DE EJERCICIOS SEGÚN DISPONIBILIDAD Y IMC ---
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        
        for dia in dias_semana:
            # Obtenemos el bloque que eligió para ese día (ej. '8:15-9:25' o 'Sin tiempo libre')
            bloque_dia = bloques_libres.get(dia, 'Sin tiempo libre')
            
            # Si el usuario marcó 'Sin tiempo libre', se respeta como día de descanso
            if bloque_dia == 'Sin tiempo libre':
                rutina_ejercicios[dia.capitalize()] = "Día libre / Descanso (Sin bloques disponibles)"
            else:
                # Si tiene tiempo libre, adaptamos el ejercicio según su IMC
                if imc < 18.5:
                    rutina_ejercicios[dia.capitalize()] = f"Bloque {bloque_dia}: Rutina de fuerza moderada (ganancia muscular) + descanso intermedio."
                elif 18.5 <= imc < 25:
                    rutina_ejercicios[dia.capitalize()] = f"Bloque {bloque_dia}: Combinado: 30 min de cardio + ejercicios de tonificación."
                elif 25 <= imc < 30:
                    rutina_ejercicios[dia.capitalize()] = f"Bloque {bloque_dia}: Quema grasa: Cardio sostenido (trote suave / caminata rápida) en el bloque libre."
                else:
                    rutina_ejercicios[dia.capitalize()] = f"Bloque {bloque_dia}: Bajo impacto: Caminata activa o elíptica durante el bloque disponible."

    return render(request, 'core2/portal.html', {
        'perfil': perfil,
        'tipo_imc': tipo_imc,
        'rutina': rutina_alimentacion,
        'ejercicios': rutina_ejercicios,
        'bloques_libres': bloques_libres
    })