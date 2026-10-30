# Proyecto Inicial - Equipazo USM (Grupo 8)

Aplicación web en Django para la recomendación de hábitos alimenticios y rutinas de ejercicio.

## Instrucciones de ejecución local

1. Clonar el repositorio en una carpeta vacía.
2. Crear y activar un entorno virtual:
   `py -m venv entorno`
   `.\entorno\Scripts\activate` (Para Windows)
3. Instalar Django:
   `pip install django`
4. Aplicar las migraciones de la base de datos local:
   `py manage.py migrate`
5. Iniciar el servidor:
   `py manage.py runserver`

## Probar la funcionalidad corazón
Al levantar el servidor, navega a las vistas de inicio de sesión o registro. Puedes ingresar datos biométricos de prueba (peso, altura) y seleccionar bloques horarios libres para visualizar el cálculo del IMC y la recomendación de la rutina generada.