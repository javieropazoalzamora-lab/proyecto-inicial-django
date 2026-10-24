from django.shortcuts import render

# Constantes de datos
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

HABITOS = {
    "Bajo peso": [
        "Haz 5 comidas al día, sin saltarte el desayuno.",
        "Lleva colaciones calóricas y nutritivas: frutos secos, plátano, yogurt.",
        "Incluye proteínas en cada comida (huevo, legumbres, pollo)."
    ],
    "Peso normal": [
        "Mantén horarios regulares de comida, incluso en semana de pruebas.",
        "Lleva colaciones simples: fruta, frutos secos o un sándwich integral.",
        "Toma al menos 2 litros de agua al día."
    ],
    "Sobrepeso": [
        "Prepara tu almuerzo en casa los días con más carga académica.",
        "Cambia bebidas azucaradas por agua o infusiones sin azúcar.",
        "Evita comer frente al computador mientras estudias."
    ],
    "Obesidad": [
        "Planifica tus comidas de la semana el domingo para no improvisar.",
        "Prioriza verduras y proteínas; reduce frituras y comida rápida.",
        "Se recomienda consultar con un profesional de la salud o nutricionista."
    ]
}

EJERCICIOS = {
    "Bajo peso": ["Fuerza con peso corporal (30 min)", "Caminata suave (30 min)", "Fuerza con peso corporal (30 min)"],
    "Peso normal": ["Trote suave (30 min)", "Fuerza con peso corporal (30 min)", "Caminata rápida (30 min)", "Estiramientos o yoga (30 min)"],
    "Sobrepeso": ["Caminata rápida (40 min)", "Bicicleta o trote suave (30 min)", "Fuerza con peso corporal (30 min)"],
    "Obesidad": ["Caminata a ritmo cómodo (30 min)", "Estiramientos (20 min)", "Caminata a ritmo cómodo (30 min)"]
}

# Funciones lógicas del Back-end
def calcular_imc(peso, altura):
    return peso / (altura ** 2)

def clasificar_imc(imc):
    if imc < 18.5:
        return "Bajo peso"
    elif imc < 25:
        return "Peso normal"
    elif imc < 30:
        return "Sobrepeso"
    else:
        return "Obesidad"

def generar_habitos(categoria):
    return HABITOS[categoria]

def organizar_rutina(categoria, disponibilidad):
    rutina = {}
    lista_ejercicios = EJERCICIOS[categoria]
    contador = 0
    for dia in DIAS:
        bloque = disponibilidad.get(dia)
        if not bloque:
            rutina[dia] = "Descanso (sin bloque libre)"
        else:
            ejercicio = lista_ejercicios[contador % len(lista_ejercicios)]
            rutina[dia] = f"{bloque} -> {ejercicio}"
            contador += 1
    return rutina


from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import PerfilSansano
import ast # Para convertir el texto de bloques libres a un diccionario real

@login_required
def vista_principal(request):
    try:
        perfil = PerfilSansano.objects.get(usuario=request.user)
    except PerfilSansano.DoesNotExist:
        # Si el usuario no ha llenado la encuesta, lo mandamos allá
        return redirect('formulario') 

    # 1. Recuperar los datos
    peso = perfil.peso
    altura = perfil.altura
    # Convertir el texto guardado en un diccionario real de Python
    disponibilidad = ast.literal_eval(perfil.bloques_libres) 
    
    # 2. Hacer los cálculos con tu lógica
    imc = calcular_imc(peso, altura)
    categoria = clasificar_imc(imc)
    habitos = generar_habitos(categoria)
    rutina = organizar_rutina(categoria, disponibilidad)

    # 3. Preparar los datos para enviarlos al diseño visual
    contexto = {
        'imc': round(imc, 1),
        'categoria': categoria,
        'habitos': habitos,
        'rutina': rutina,
        'peso_actual': peso,
        # Puedes calcular una meta básica, por ejemplo, perder 4kg si hay sobrepeso, o ganar si hay bajo peso.
        # Por ahora lo dejamos fijo o puedes crear una función para esto.
        'meta_peso': peso - 4 if categoria in ['Sobrepeso', 'Obesidad'] else (peso + 4 if categoria == 'Bajo peso' else peso), 
    }

    # 4. Enviar todo a la plantilla de resultados (asegúrate de que el nombre del archivo html sea el correcto)
    return render(request, 'core2/inicio.html', contexto)

# Asegúrate de tener estas importaciones en la parte superior
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import PerfilSansano
@login_required
def encuesta_datos(request):
    if request.method == 'POST':
        peso = request.POST.get('peso')
        altura = request.POST.get('altura')
        
        dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        bloques = {dia: request.POST.get(dia, 'Sin tiempo libre') for dia in dias}
        
        PerfilSansano.objects.update_or_create(
            usuario=request.user,
            defaults={
                'peso': float(peso.replace(',', '.')),
                'altura': float(altura.replace(',', '.')),
                'bloques_libres': str(bloques)
            }
        )
        return redirect('inicio')
        
    return render(request, 'core2/formulario.html')