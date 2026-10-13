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