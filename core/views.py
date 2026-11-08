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
            # --- NUEVA LÓGICA DE REDIRECCIÓN INTELIGENTE ---
            # Verificamos si el usuario ya cuenta con un perfil registrado
            if PerfilSansano.objects.filter(usuario=usuario).exists():
                return redirect('portal')
            else:
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
        # 1. Obtener peso, altura y nivel de actividad física
        peso_str = request.POST.get('peso', '0').replace(',', '.')
        altura_str = request.POST.get('altura', '0').replace(',', '.')
        actividad_fisica = request.POST.get('actividad_fisica', 'moderada') # NUEVO
        
        try:
            peso = float(peso_str)
            altura = float(altura_str)
        except ValueError:
            peso = 0.0
            altura = 0.0

        # Si la altura la ingresan en centímetros (ej: 175), la pasamos a metros (1.75)
        altura_m = altura / 100 if altura > 3 else altura

        # 2. Calcular el IMC
        imc = round(peso / (altura_m ** 2), 2) if altura_m > 0 else 0.0

        # 3. Obtener el bloque seleccionado para cada día
        dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        bloques = {}
        
        for dia in dias:
            bloque_seleccionado = request.POST.get(dia)
            if bloque_seleccionado in BLOQUES_VALIDOS:
                bloques[dia] = bloque_seleccionado
            else:
                bloques[dia] = 'Sin tiempo libre'

        # 4. Guardar o actualizar en la base de datos incluyendo la actividad física
        PerfilSansano.objects.update_or_create(
            usuario=request.user,
            defaults={
                'peso': peso,
                'altura': altura,
                'imc': imc,
                'actividad_fisica': actividad_fisica, # NUEVO: Guardar en BD
                'bloques_libres': str(bloques)
            }
        )

        return redirect('portal')

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
        actividad = getattr(perfil, 'actividad_fisica', 'moderada')
        bloques_libres = ast.literal_eval(perfil.bloques_libres) if perfil.bloques_libres else {}
    except PerfilSansano.DoesNotExist:
        perfil = None
        imc = None
        actividad = 'moderada'
        bloques_libres = {}

    rutina_alimentacion = {}
    rutina_ejercicios = {}
    tipo_imc = "Sin datos"

    if imc is not None:
        # --- 1. MATRIZ DE 9 PERFILES (P1 a P9) SEGÚN PDF ---
        if imc < 18.5:
            if actividad == 'leve':
                tipo_imc = "P1: Ganar peso (Actividad baja)"
                rutina_alimentacion = {
                    'Lunes': {'Desayuno': 'Pan con palta y huevo (2 rebanadas pan integral, palta, 1 huevo revuelto y 1 vaso de leche)', 'Almuerzo': 'Pollo con arroz y ensalada (1 presa al horno, 1 taza de arroz y ensalada con aceite de oliva)', 'Once': 'Sándwich de queso y jamón (2 panes con queso, jamón y palta. Té o leche)', 'Colación': 'Frutos secos con pasas (1 puñado de nueces/almendras con pasas)'},
                    'Martes': {'Desayuno': 'Avena con leche y plátano (1 taza de avena en leche entera, 1 plátano y nueces)', 'Almuerzo': 'Lentejas con arroz y huevo (1 plato de lentejas, 1/2 taza de arroz y 1 huevo cocido)', 'Once': 'Yogur con fruta y frutos secos (1 yogur entero, fruta picada y frutos secos)', 'Colación': 'Batido de plátano (1 plátano licuado con leche entera y mantequilla de maní)'},
                    'Miércoles': {'Desayuno': 'Tostadas con queso y fruta (2 tostadas con queso, 1 fruta y 1 vaso de leche)', 'Almuerzo': 'Carne con puré (1 trozo de carne guisada, 1 taza de puré y ensalada de tomate)', 'Once': 'Pan con palta y huevo (2 panes con palta y huevo cocido, 1 vaso de leche)', 'Colación': 'Yogur con avena (1 yogur entero con 1 cda. de avena)'},
                    'Jueves': {'Desayuno': 'Yogur con granola y fruta (1 yogur entero con granola y plátano)', 'Almuerzo': 'Fideos con salsa de carne (1 plato de fideos con carne molida y verduras. Postre: 1 fruta)', 'Once': 'Sándwich de pollo (2 panes con pollo desmenuzado, palta y tomate)', 'Colación': 'Pan con mantequilla de maní (1 pan con mantequilla de maní)'},
                    'Viernes': {'Desayuno': 'Panqueques de avena (2 panqueques de avena, huevo y plátano con miel y leche)', 'Almuerzo': 'Pescado con papas (1 filete de pescado al horno, 2 papas cocidas y ensalada)', 'Once': 'Tostadas con queso y mermelada (2 tostadas con queso fresco y mermelada + leche)', 'Colación': 'Fruta con queso (1 fruta de temporada y 1 lámina de queso)'},
                    'Sábado': {'Desayuno': 'Huevos con pan y jugo (2 huevos revueltos, 2 panes, palta y jugo natural)', 'Almuerzo': 'Cazuela de pollo (1 plato con pollo, papa, choclo, zapallo y 1/2 taza de arroz)', 'Once': 'Panqueques con plátano (2 panqueques con plátano y miel + leche)', 'Colación': 'Galletas de avena (2 galletas de avena y 1 vaso de leche)'},
                    'Domingo': {'Desayuno': 'Pan con mantequilla de maní (2 rebanadas con mantequilla de maní, plátano y leche)', 'Almuerzo': 'Porotos con fideos (1 plato de porotos con fideos y zapallo, ensalada y fruta)', 'Once': 'Pan con queso y huevo (2 panes con queso derretido y huevo revuelto + leche)', 'Colación': 'Plátano con yogur (1 plátano con yogur entero y miel)'}
                }
            elif actividad == 'moderada':
                tipo_imc = "P2: Ganar peso (Actividad media)"
                rutina_alimentacion = {
                    'Lunes': {'Desayuno': 'Pan con palta y huevo (3 rebanadas pan integral, palta, 2 huevos revueltos y leche)', 'Almuerzo': 'Pollo con arroz y ensalada (1 presa de pollo, 1.5 tazas de arroz y ensalada)', 'Once': 'Sándwich de queso y jamón (2 panes con queso, jamón y palta + leche)', 'Colación': 'Frutos secos con pasas (1 puñado de nueces o almendras con pasas)'},
                    'Martes': {'Desayuno': 'Avena con leche y plátano (1.5 tazas de avena en leche entera, plátano y nueces)', 'Almuerzo': 'Lentejas con arroz y huevo (1 plato grande de lentejas, 1/2 taza de arroz y huevo)', 'Once': 'Yogur con fruta y frutos secos (1 yogur entero, fruta picada y frutos secos)', 'Colación': 'Batido de plátano (1 plátano licuado con leche y mantequilla de maní)'},
                    'Miércoles': {'Desayuno': 'Tostadas con queso y fruta (3 tostadas con queso, 1 fruta y 1 vaso de leche)', 'Almuerzo': 'Carne con puré (1 trozo de carne, 1.5 tazas de puré y ensalada de tomate)', 'Once': 'Pan con palta y huevo (2 panes con palta y huevo cocido + leche)', 'Colación': 'Yogur con avena (1 yogur entero con 2 cdas. de avena)'},
                    'Jueves': {'Desayuno': 'Yogur con granola y fruta (1 yogur entero con 4 cdas. de granola y plátano)', 'Almuerzo': 'Fideos con salsa de carne (1.5 platos de fideos con carne molida y verduras + fruta)', 'Once': 'Sándwich de pollo (2 panes con pollo desmenuzado, palta y tomate)', 'Colación': 'Pan con mantequilla de maní (1 pan con mantequilla de maní)'},
                    'Viernes': {'Desayuno': 'Panqueques de avena (3 panqueques de avena, huevo y plátano con miel + leche)', 'Almuerzo': 'Pescado con papas (1 filete de pescado al horno, 3 papas cocidas y ensalada)', 'Once': 'Tostadas con queso y mermelada (3 tostadas con queso fresco y mermelada + leche)', 'Colación': 'Fruta con queso (1 fruta y 2 láminas de queso)'},
                    'Sábado': {'Desayuno': 'Huevos con pan y jugo (2 huevos revueltos, 3 panes, palta y jugo natural)', 'Almuerzo': 'Cazuela de pollo (1 plato grande con pollo, papa, choclo, zapallo y 1 taza de arroz)', 'Once': 'Panqueques con plátano (3 panqueques con plátano y miel + leche)', 'Colación': 'Galletas de avena (3 galletas de avena y 1 vaso de leche)'},
                    'Domingo': {'Desayuno': 'Pan con mantequilla de maní (3 rebanadas con mantequilla de maní y plátano + leche)', 'Almuerzo': 'Porotos con fideos (1 plato grande de porotos con fideos, zapallo, ensalada y fruta)', 'Once': 'Pan con queso y huevo (2 panes con queso derretido y huevo revuelto + leche)', 'Colación': 'Plátano con yogur (1 plátano con yogur entero y miel)'}
                }
            else: # alta
                tipo_imc = "P3: Ganar peso (Actividad alta)"
                rutina_alimentacion = {
                    'Lunes': {'Desayuno': 'Pan con palta y huevo (3 rebanadas pan integral, palta, 2 huevos revueltos y leche)', 'Almuerzo': 'Pollo con arroz y ensalada (1 presa de pollo, 2 tazas de arroz y ensalada)', 'Once': 'Sándwich de queso y jamón (3 panes con queso, jamón y palta + leche)', 'Colación': 'Frutos secos con pasas (2 puñados de nueces o almendras con pasas)'},
                    'Martes': {'Desayuno': 'Avena con leche y plátano (2 tazas de avena en leche entera, plátano y nueces)', 'Almuerzo': 'Lentejas con arroz y huevo (1 plato grande de lentejas, 1 taza de arroz y huevo)', 'Once': 'Yogur con fruta y frutos secos (1 yogur entero, fruta y 2 puñados de frutos secos)', 'Colación': 'Batido de plátano (1 plátano con leche entera y mantequilla de maní)'},
                    'Miércoles': {'Desayuno': 'Tostadas con queso y fruta (4 tostadas con queso, 1 fruta y 1 vaso de leche)', 'Almuerzo': 'Carne con puré (1 trozo de carne, 2 tazas de puré y ensalada de tomate)', 'Once': 'Pan con palta y huevo (3 panes con palta y huevo cocido + leche)', 'Colación': 'Yogur con avena (1 yogur entero con 3 cdas. de avena)'},
                    'Jueves': {'Desayuno': 'Yogur con granola y fruta (1 yogur entero con 6 cdas. de granola y plátano)', 'Almuerzo': 'Fideos con salsa de carne (2 platos de fideos con carne molida, verduras + fruta)', 'Once': 'Sándwich de pollo (3 panes con pollo desmenuzado, palta y tomate)', 'Colación': 'Pan con mantequilla de maní (2 panes con mantequilla de maní)'},
                    'Viernes': {'Desayuno': 'Panqueques de avena (4 panqueques de avena, huevo y plátano con miel + leche)', 'Almuerzo': 'Pescado con papas (1 filete de pescado al horno, 4 papas cocidas y ensalada)', 'Once': 'Tostadas con queso y mermelada (4 tostadas con queso fresco y mermelada + leche)', 'Colación': 'Fruta con queso (1 fruta de temporada y 2 láminas de queso)'},
                    'Sábado': {'Desayuno': 'Huevos con pan y jugo (3 huevos revueltos, 3 panes, palta y jugo natural)', 'Almuerzo': 'Cazuela de pollo (1 plato grande con pollo, papa, choclo, zapallo y 1 taza de arroz)', 'Once': 'Panqueques con plátano (3 panqueques con plátano y miel + leche)', 'Colación': 'Galletas de avena (4 galletas de avena y 1 vaso de leche)'},
                    'Domingo': {'Desayuno': 'Pan con mantequilla de maní (3 rebanadas con mantequilla de maní y plátano + leche)', 'Almuerzo': 'Porotos con fideos (1 plato grande de porotos con fideos, zapallo, ensalada y fruta)', 'Once': 'Pan con queso y huevo (3 panes con queso derretido y huevo revuelto + leche)', 'Colación': 'Plátano con yogur (1 plátano con yogur entero y miel)'}
                }

        elif 18.5 <= imc <= 24.9:
            if actividad == 'leve':
                tipo_imc = "P4: Mantener peso (Actividad baja)"
                rutina_alimentacion = {
                    'Lunes': {'Desayuno': 'Pan integral con palta (1 rebanada con palta y 1 huevo, té o café)', 'Almuerzo': 'Pollo con arroz y ensalada (1 presa de pollo sin piel, 1/2 taza de arroz y ensalada)', 'Once': 'Sándwich de pavo y palta (1 pan con pavo, palta y tomate)', 'Colación': 'Fruta de temporada (1 manzana, pera o naranja)'},
                    'Martes': {'Desayuno': 'Yogur con fruta y avena (1 yogur natural, fruta y 2 cdas. de avena)', 'Almuerzo': 'Lentejas con verduras (1 plato de lentejas con zanahoria y zapallo + ensalada)', 'Once': 'Yogur con granola (1 yogur natural con 1 cda. de granola)', 'Colación': 'Yogur natural (1 yogur natural sin azúcar con fruta)'},
                    'Miércoles': {'Desayuno': 'Pan con queso fresco (1 pan con queso fresco y tomate + té)', 'Almuerzo': 'Pescado al horno con ensalada (1 filete de pescado, ensalada y 1 papa cocida)', 'Once': 'Pan con queso fresco (1 pan con queso fresco y tomate)', 'Colación': 'Zanahoria con hummus (Palitos de zanahoria con 1 cda. de hummus)'},
                    'Jueves': {'Desayuno': 'Avena con leche (1 taza de avena en leche semidescremada, fruta y canela)', 'Almuerzo': 'Fideos con atún y verduras (1/2 plato de fideos con atún, tomate y verduras)', 'Once': 'Fruta con almendras (1 fruta y 5 almendras)', 'Colación': 'Frutos secos (1 puñado de nueces o almendras)'},
                    'Viernes': {'Desayuno': 'Tostadas con huevo y fruta (2 rebanadas pan integral, 1 huevo y fruta)', 'Almuerzo': 'Carne magra con arroz (1 trozo de carne, 1/2 taza de arroz y verduras salteadas)', 'Once': 'Huevos revueltos con verduras (1 huevo revuelto con tomate, cebolla y pan)', 'Colación': 'Plátano (1 plátano solo)'},
                    'Sábado': {'Desayuno': 'Pan con queso fresco y tomate (1 pan con queso fresco y tomate + fruta)', 'Almuerzo': 'Cazuela de vacuno (1 plato mediano con carne, papa, choclo y zapallo)', 'Once': 'Sándwich de atún (1 pan con atún, tomate y lechuga)', 'Colación': 'Galletas de avena (1 galleta de avena casera y té)'},
                    'Domingo': {'Desayuno': 'Panqueques de avena (1 panqueque de avena y plátano con yogur natural)', 'Almuerzo': 'Garbanzos con arroz (1 plato de garbanzos, 1/2 taza de arroz y ensalada)', 'Once': 'Pan con huevo (1 pan con huevo revuelto y tomate + té)', 'Colación': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)'}
                }
            elif actividad == 'moderada':
                tipo_imc = "P5: Mantener peso (Actividad media)"
                rutina_alimentacion = {
                    'Lunes': {'Desayuno': 'Pan integral con palta (2 rebanadas pan integral con palta y 1 huevo)', 'Almuerzo': 'Pollo con arroz y ensalada (1 presa de pollo sin piel, 3/4 taza de arroz y ensalada)', 'Once': 'Sándwich de pavo y palta (1 pan con pechuga de pavo, palta y tomate)', 'Colación': 'Fruta de temporada (1 manzana, pera o naranja)'},
                    'Martes': {'Desayuno': 'Yogur con fruta y avena (1 yogur natural, fruta y 3 cdas. de avena)', 'Almuerzo': 'Lentejas con verduras (1 plato de lentejas con verduras y ensalada)', 'Once': 'Yogur con granola (1 yogur natural con 2 cdas. de granola)', 'Colación': 'Yogur natural (1 yogur natural con fruta)'},
                    'Miércoles': {'Desayuno': 'Tostadas con huevo y fruta (2 rebanadas pan integral, 1 huevo y fruta)', 'Almuerzo': 'Pescado al horno con ensalada (1 filete, ensalada y 1 papa cocida)', 'Once': 'Pan con queso fresco (1 pan con queso fresco y tomate)', 'Colación': 'Zanahoria con hummus (Palitos de zanahoria con 2 cdas. de hummus)'},
                    'Jueves': {'Desayuno': 'Avena con leche (1 taza de avena en leche semidescremada, fruta y canela)', 'Almuerzo': 'Fideos con atún y verduras (1 plato de fideos con atún y verduras)', 'Once': 'Fruta con almendras (1 fruta y 8 almendras)', 'Colación': 'Frutos secos (1 puñado de nueces o almendras)'},
                    'Viernes': {'Desayuno': 'Pan con queso fresco y tomate (2 panes con queso fresco, tomate y fruta)', 'Almuerzo': 'Carne magra con arroz (1 trozo de carne, 3/4 taza de arroz y verduras)', 'Once': 'Tostadas con palta (2 tostadas con palta y 1 huevo cocido)', 'Colación': 'Plátano (1 plátano solo)'},
                    'Sábado': {'Desayuno': 'Huevos revueltos con verduras (2 huevos revueltos con tomate, cebolla y 2 panes)', 'Almuerzo': 'Cazuela de vacuno (1 plato mediano con carne, papa, choclo y zapallo)', 'Once': 'Sándwich de atún (1 pan con atún, tomate y lechuga)', 'Colación': 'Galletas de avena (2 galletas de avena caseras y té)'},
                    'Domingo': {'Desayuno': 'Panqueques de avena (2 panqueques de avena y plátano con yogur natural)', 'Almuerzo': 'Garbanzos con arroz (1 plato de garbanzos, 1/2 taza de arroz y ensalada)', 'Once': 'Pan con huevo (1 pan con huevo revuelto y tomate)', 'Colación': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)'}
                }
            else: # alta
                tipo_imc = "P6: Mantener peso (Actividad alta)"
                rutina_alimentacion = {
                    'Lunes': {'Desayuno': 'Pan integral con palta (2 rebanadas pan integral con palta y 2 huevos)', 'Almuerzo': 'Pollo con arroz y ensalada (1 presa de pollo sin piel, 1 taza de arroz y ensalada)', 'Once': 'Sándwich de pavo y palta (2 panes con pavo, palta y tomate)', 'Colación': 'Fruta de temporada (1 manzana, pera o naranja)'},
                    'Martes': {'Desayuno': 'Yogur con fruta y avena (1 yogur natural, fruta y 4 cdas. de avena)', 'Almuerzo': 'Lentejas con verduras (1 plato grande de lentejas con verduras y ensalada)', 'Once': 'Yogur con granola (1 yogur natural con 3 cdas. de granola)', 'Colación': 'Yogur natural (1 yogur natural con fruta y 1 cda. de avena)'},
                    'Miércoles': {'Desayuno': 'Tostadas con huevo y fruta (3 rebanadas pan integral, 1 huevo y fruta)', 'Almuerzo': 'Pescado al horno con ensalada (1 filete, ensalada y 2 papas cocidas)', 'Once': 'Pan con queso fresco (2 panes con queso fresco y tomate)', 'Colación': 'Zanahoria con hummus (Palitos de zanahoria con 3 cdas. de hummus)'},
                    'Jueves': {'Desayuno': 'Avena con leche (1.5 tazas de avena en leche semidescremada, fruta y canela)', 'Almuerzo': 'Fideos con atún y verduras (1.5 platos de fideos con atún y verduras)', 'Once': 'Fruta con almendras (1 fruta y 10 almendras)', 'Colación': 'Frutos secos (1 puñado de nueces o almendras)'},
                    'Viernes': {'Desayuno': 'Pan con queso fresco y tomate (2 panes con queso fresco, tomate y fruta)', 'Almuerzo': 'Carne magra con arroz (1 trozo de carne, 1 taza de arroz y verduras)', 'Once': 'Tostadas con palta (2 tostadas con palta y 1 huevo cocido)', 'Colación': 'Plátano con mantequilla de maní (1 plátano con 1 cda. de mantequilla de maní)'},
                    'Sábado': {'Desayuno': 'Huevos revueltos con verduras (3 huevos revueltos con tomate, cebolla y 2 panes)', 'Almuerzo': 'Cazuela de vacuno (1 plato grande con carne, papa, choclo y zapallo)', 'Once': 'Sándwich de atún (2 panes con atún, tomate y lechuga)', 'Colación': 'Galletas de avena (3 galletas de avena caseras y té)'},
                    'Domingo': {'Desayuno': 'Panqueques de avena (3 panqueques de avena y plátano con yogur natural)', 'Almuerzo': 'Garbanzos con arroz (1 plato grande de garbanzos, 1 taza de arroz y ensalada)', 'Once': 'Pan con huevo (2 panes con huevo revuelto y tomate)', 'Colación': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)'}
                }

        else:
            if actividad == 'leve':
                tipo_imc = "P7: Reducir grasa corporal (Actividad baja)"
                rutina_alimentacion = {
                    'Lunes': {'Desayuno': 'Pan integral con queso fresco (1 rebanada con queso fresco, tomate, 1 huevo cocido)', 'Almuerzo': 'Pollo a la plancha con ensalada (1 presa sin piel, ensalada y 1/2 taza de arroz)', 'Once': 'Pan integral con palta (1 rebanada con 2 cdas. de palta)', 'Colación': 'Fruta entera (1 manzana, pera o naranja)'},
                    'Martes': {'Desayuno': 'Yogur natural con fruta (1 yogur sin azúcar, 1/2 taza de fruta y avena)', 'Almuerzo': 'Lentejas con verduras (1 plato mediano de lentejas con zapallo, zanahoria y ensalada)', 'Once': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)', 'Colación': 'Verduras crudas (Zanahoria, pepino o apio en palitos con limón)'},
                    'Miércoles': {'Desayuno': 'Tostada con huevo revuelto (1 pan integral con 1 huevo revuelto y tomate)', 'Almuerzo': 'Pescado al horno con verduras (1 filete, 1 taza de verduras al vapor y 1/2 taza de quinoa)', 'Once': 'Pan integral con pavo (1 pan integral con pechuga de pavo y tomate)', 'Colación': 'Yogur natural (1 yogur natural sin azúcar)'},
                    'Jueves': {'Desayuno': 'Avena con fruta (1/2 taza de avena en agua o leche descremada con manzana)', 'Almuerzo': 'Ensalada con pollo (Lechuga, tomate, pollo desmenuzado, 1/2 taza de garbanzos y limón)', 'Once': 'Yogur con fruta (1 yogur natural sin azúcar con fruta picada)', 'Colación': 'Zanahoria con hummus (Palitos de zanahoria con 1 cda. de hummus)'},
                    'Viernes': {'Desayuno': 'Pan con palta (1 rebanada pan integral con 2 cdas. de palta y fruta)', 'Almuerzo': 'Atún con legumbres y ensalada (1/2 lata de atún, 1/2 taza de porotos/garbanzos y ensalada)', 'Once': 'Pan con queso fresco (1 rebanada con queso fresco y pepino)', 'Colación': 'Fruta con almendras (1 fruta y 3 almendras)'},
                    'Sábado': {'Desayuno': 'Huevos con verduras (1 huevo revuelto con espinaca o tomate y pan integral)', 'Almuerzo': 'Carne magra con verduras (1 trozo pequeño de carne, verduras y 1 papa cocida)', 'Once': 'Tostada con atún (1 tostada integral con atún y tomate)', 'Colación': 'Huevo cocido (1 huevo cocido con tomate)'},
                    'Domingo': {'Desayuno': 'Yogur con avena y plátano (1 yogur natural con avena y 1/2 plátano)', 'Almuerzo': 'Sopa de verduras con pollo (1 plato de sopa con pollo, zapallo, zanahoria y choclo + ensalada)', 'Once': 'Fruta con almendras (1 fruta y 3 almendras)', 'Colación': 'Fruta picada con canela (1 taza de fruta picada con canela)'}
                }
            elif actividad == 'moderada':
                tipo_imc = "P8: Reducir grasa corporal (Actividad media)"
                rutina_alimentacion = {
                    'Lunes': {'Desayuno': 'Pan integral con queso fresco (1 rebanada con queso fresco, tomate, 1 huevo cocido)', 'Almuerzo': 'Pollo a la plancha con ensalada (1 presa sin piel, ensalada y 1/2 taza de arroz)', 'Once': 'Pan integral con palta (1 rebanada con 2 cdas. de palta)', 'Colación': 'Fruta entera (1 manzana, pera o naranja)'},
                    'Martes': {'Desayuno': 'Yogur natural con fruta (1 yogur sin azúcar, fruta y 2 cdas. de avena)', 'Almuerzo': 'Lentejas con verduras (1 plato mediano de lentejas con zapallo y ensalada)', 'Once': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)', 'Colación': 'Verduras crudas (Zanahoria, pepino o apio en palitos con limón)'},
                    'Miércoles': {'Desayuno': 'Tostada con huevo revuelto (2 rebanadas pan integral con 1 huevo revuelto y tomate)', 'Almuerzo': 'Pescado al horno con verduras (1 filete, 1.5 tazas de verduras al vapor y 1/2 taza de quinoa)', 'Once': 'Pan integral con pavo (1 pan integral con pechuga de pavo y tomate)', 'Colación': 'Yogur natural (1 yogur natural sin azúcar)'},
                    'Jueves': {'Desayuno': 'Avena con fruta (1/2 taza de avena en agua o leche descremada con manzana)', 'Almuerzo': 'Ensalada con pollo (Lechuga, tomate, pollo desmenuzado, 1/2 taza de garbanzos y limón)', 'Once': 'Yogur con fruta (1 yogur natural sin azúcar con fruta picada)', 'Colación': 'Zanahoria con hummus (Palitos de zanahoria con 2 cdas. de hummus)'},
                    'Viernes': {'Desayuno': 'Pan con palta (1 rebanada pan integral con 2 cdas. de palta y fruta)', 'Almuerzo': 'Atún con legumbres y ensalada (1 lata de atún, 1/2 taza de porotos/garbanzos y ensalada)', 'Once': 'Pan con queso fresco (1 rebanada con queso fresco y pepino)', 'Colación': 'Fruta con almendras (1 fruta y 5 almendras)'},
                    'Sábado': {'Desayuno': 'Huevos con verduras (2 huevos revueltos con espinaca o tomate y pan integral)', 'Almuerzo': 'Carne magra con verduras (1 trozo pequeño de carne, verduras y 1 papa cocida)', 'Once': 'Tostada con atún (1 tostada integral con atún y tomate)', 'Colación': 'Huevo cocido (1 huevo cocido con tomate)'},
                    'Domingo': {'Desayuno': 'Yogur con avena y plátano (1 yogur natural con 3 cdas. de avena y 1/2 plátano)', 'Almuerzo': 'Sopa de verduras con pollo (1 plato de sopa con pollo, zapallo, zanahoria y choclo + ensalada)', 'Once': 'Fruta con almendras (1 fruta y 5 almendras)', 'Colación': 'Fruta picada con canela (1 taza de fruta picada con canela)'}
                }
            else: # alta
                tipo_imc = "P9: Reducir grasa corporal (Actividad alta)"
                rutina_alimentacion = {
                    'Lunes': {'Desayuno': 'Pan integral con queso fresco (2 rebanadas con queso fresco, tomate, 1 huevo cocido)', 'Almuerzo': 'Pollo a la plancha con ensalada (1 presa sin piel, ensalada y 3/4 taza de arroz)', 'Once': 'Pan integral con palta (2 rebanadas con 2 cdas. de palta)', 'Colación': 'Fruta entera (1 manzana, pera o naranja)'},
                    'Martes': {'Desayuno': 'Yogur natural con fruta (1 yogur sin azúcar, fruta y 3 cdas. de avena)', 'Almuerzo': 'Lentejas con verduras (1 plato de lentejas con zapallo, zanahoria y ensalada)', 'Once': 'Huevo cocido y fruta (1 huevo cocido y 1 fruta)', 'Colación': 'Verduras crudas (Zanahoria, pepino o apio en palitos con limón)'},
                    'Miércoles': {'Desayuno': 'Tostada con huevo revuelto (2 rebanadas pan integral con 2 huevos revueltos y tomate)', 'Almuerzo': 'Pescado al horno con verduras (1 filete, 2 tazas de verduras al vapor y 1/2 taza de quinoa)', 'Once': 'Pan integral con pavo (2 panes integrales con pechuga de pavo y tomate)', 'Colación': 'Yogur natural / Zanahoria con hummus (1 yogur natural sin azúcar / Palitos con hummus)'},
                    'Jueves': {'Desayuno': 'Avena con fruta (1 taza de avena en agua o leche descremada con manzana)', 'Almuerzo': 'Ensalada con pollo (Lechuga, tomate, pollo desmenuzado, 1/2 taza de garbanzos y limón)', 'Once': 'Yogur con fruta (1 yogur natural sin azúcar con fruta picada)', 'Colación': 'Zanahoria con hummus (Palitos de zanahoria con 2 cdas. de hummus)'},
                    'Viernes': {'Desayuno': 'Pan con palta (2 rebanadas pan integral con 2 cdas. de palta y fruta)', 'Almuerzo': 'Atún con legumbres y ensalada (1 lata de atún, 1 taza de porotos/garbanzos y ensalada)', 'Once': 'Pan con queso fresco (2 rebanadas con queso fresco y pepino)', 'Colación': 'Fruta con almendras (1 fruta y 5 almendras)'},
                    'Sábado': {'Desayuno': 'Huevos con verduras (2 huevos revueltos con espinaca o tomate y 2 panes integrales)', 'Almuerzo': 'Carne magra con verduras (1 trozo de carne, verduras y 2 papas cocidas)', 'Once': 'Tostada con atún (2 tostadas integrales con atún y tomate)', 'Colación': 'Huevo cocido (1 huevo cocido con tomate)'},
                    'Domingo': {'Desayuno': 'Yogur con avena y plátano (1 yogur natural con 4 cdas. de avena y 1/2 plátano)', 'Almuerzo': 'Sopa de verduras con pollo (1 plato grande de sopa con pollo, verduras y choclo + ensalada)', 'Once': 'Fruta con almendras (1 fruta y 8 almendras)', 'Colación': 'Fruta picada con canela (1.5 tazas de fruta picada con canela)'}
                }

        # --- 2. LÓGICA DE EJERCICIOS ---
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        for dia in dias_semana:
            bloque_dia = bloques_libres.get(dia, 'Sin tiempo libre')
            if bloque_dia == 'Sin tiempo libre':
                rutina_ejercicios[dia.capitalize()] = "Día libre / Descanso (Sin bloques disponibles)"
            else:
                if imc < 18.5:
                    rutina_ejercicios[dia.capitalize()] = f"Bloque {bloque_dia}: Rutina de fuerza moderada (ganancia muscular)."
                elif 18.5 <= imc <= 24.9:
                    rutina_ejercicios[dia.capitalize()] = f"Bloque {bloque_dia}: Combinado: 30 min de cardio + tonificación."
                else:
                    rutina_ejercicios[dia.capitalize()] = f"Bloque {bloque_dia}: Quema grasa / Cardio sostenido en el bloque libre."

    return render(request, 'core2/portal.html', {
        'perfil': perfil,
        'tipo_imc': tipo_imc,
        'rutina': rutina_alimentacion,
        'ejercicios': rutina_ejercicios,
        'bloques_libres': bloques_libres
    })