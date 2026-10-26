from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('registro/', views.registrar_usuario, name='registro'),
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('encuesta/', views.encuesta_datos, name='encuesta_datos'),
    path('portal/', views.portal, name='portal'),
]