from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('registro/', views.registrar_usuario, name='registro'),
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('encuesta/', views.encuesta_datos, name='encuesta_datos'),
    path('portal/', views.portal, name='portal'),
    path('activar/<uidb64>/<token>/', views.activar_cuenta, name='activar_cuenta'),
    path('ajustes/clave/', auth_views.PasswordChangeView.as_view(template_name='core2/cambiar_clave.html'), name='cambiar_clave'),
    path('ajustes/clave/lista/', auth_views.PasswordChangeDoneView.as_view(template_name='core2/clave_cambiada.html'), name='password_change_done'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('recuperar/', auth_views.PasswordResetView.as_view(template_name='core2/password_reset.html'), name='password_reset'),
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='core2/password_reset_done.html'), name='password_reset_done'),
    path('recuperar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core2/password_reset_confirm.html'), name='password_reset_confirm'),
    path('recuperar/completo/', auth_views.PasswordResetCompleteView.as_view(template_name='core2/password_reset_complete.html'), name='password_reset_complete'),
]