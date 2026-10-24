from django.contrib import admin
from django.urls import path
from recomendador import views as recomendador_views
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('salud/', recomendador_views.vista_principal, name='inicio'), 
    path('login/', core_views.iniciar_sesion, name='login'),
    path('formulario/', core_views.encuesta_datos, name='formulario'),
]