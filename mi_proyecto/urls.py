from django.contrib import admin
from django.urls import path
from recomendador import views  # Importamos a nuestro "Cocinero"

urlpatterns = [
    path('admin/', admin.site.urls),
    # Cuando alguien entre a /salud/, ejecuta la vista_principal
    path('salud/', views.vista_principal, name='inicio'), 
]