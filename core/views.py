from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import PerfilSansano

def iniciar_sesion(request):
    if request.method == 'POST':
        formulario = AuthenticationForm(request, data=request.POST)
        if formulario.is_valid():
            usuario = formulario.get_user()
            login(request, usuario)
            return redirect('inicio') 
    else:
        formulario = AuthenticationForm()
    return render(request, 'core2/login.html', {'form': formulario})

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