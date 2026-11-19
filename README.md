# Proyecto Inicial - Equipazo USM (Grupo 8)

Aplicación web en Django para la recomendación de hábitos alimenticios y rutinas de ejercicio.

## Instrucciones de ejecución local

1. Clonar el repositorio en una carpeta vacía.
2. Crear y activar un entorno virtual:
   `py -m venv entorno`
   `.\entorno\Scripts\activate` (Para Windows)
3. Instalar las dependencias (Django y el SDK de Gemini):
   `pip install -r requirements.txt`
4. Aplicar las migraciones de la base de datos local:
   `py manage.py migrate`
5. (Opcional) Crear un administrador para revisar los datos en `/admin/`:
   `py manage.py createsuperuser`
6. Iniciar el servidor:
   `py manage.py runserver`
7. Ejecutar las pruebas automáticas:
   `py manage.py test core`

### Variables de entorno
| Variable | Uso | Por defecto |
|---|---|---|
| `GEMINI_API_KEY` | Clave de la API de Gemini. Sin ella se usa el plan base por reglas. | (vacía) |
| `GEMINI_MODEL` | Modelo de Gemini a usar. | `gemini-3.5-flash-lite` |
| `DJANGO_DEBUG` | `0` para producción. | `1` |
| `DJANGO_SECRET_KEY` | Obligatoria si `DJANGO_DEBUG=0`. | clave de desarrollo |
| `DJANGO_ALLOWED_HOSTS` | Dominios permitidos, separados por coma. | (vacía) |

> Las variables se pueden definir en un archivo `.env` junto a `manage.py` (ver `.env.example`).

### Correo de verificación (activación de cuenta)
Al registrarse, el usuario recibe un correo con un enlace para activar su cuenta. Para que llegue **al correo real**:

1. Copia `.env.example` como `.env`.
2. Completa `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD`.
   Con Gmail: activa la verificación en 2 pasos y crea una *contraseña de aplicación* en
   https://myaccount.google.com/apppasswords (no uses tu contraseña normal).
3. Prueba la configuración: `py manage.py sendtestemail tu_correo@usm.cl`
4. Reinicia `runserver`.

Si `EMAIL_HOST` está vacío, los correos se imprimen en la terminal (modo desarrollo).
Si una cuenta no se activó, al intentar iniciar sesión con la clave correcta se reenvía el enlace automáticamente.

## Probar la funcionalidad corazón
Al levantar el servidor, navega a las vistas de inicio de sesión o registro. Puedes ingresar datos biométricos de prueba (peso, altura) y seleccionar bloques horarios libres para visualizar el cálculo del IMC y la recomendación de la rutina generada.
## Estructura del proyecto

```
proyecto-inicial-django/
├── manage.py
├── requirements.txt
├── .env.example                 # plantilla de variables de entorno (copiar como .env)
├── mi_proyecto/                 # configuración de Django (settings, urls raíz, wsgi/asgi)
└── core/                        # la aplicación
    ├── models.py                # PerfilSansano (datos + IMC) y PlanSemanal (plan generado)
    ├── forms.py                 # registro @usm.cl y encuesta (ModelForm)
    ├── views.py                 # páginas públicas, cuentas, encuesta y portal
    ├── urls.py
    ├── admin.py
    ├── servicios.py             # orquesta la generación y guardado del plan
    ├── ia.py                    # llamada a Gemini y validación de su respuesta
    ├── planes_base.py           # plan de respaldo por reglas (perfiles P1-P9)
    ├── rutinas.py               # rutinas de ejercicio según el tiempo libre
    ├── horarios.py              # bloques, módulos y ventanas libres
    ├── constantes.py            # opciones compartidas (días, módulos, objetivos...)
    ├── migrations/
    ├── tests/                   # pruebas, un archivo por tema
    ├── static/core/
    │   ├── css/                 # base.css + un archivo por sección del sitio
    │   └── img/
    └── templates/core/
        ├── base.html            # layout común (barra superior / barra lateral)
        ├── inicio.html          # portada pública
        ├── cuentas/             # login, registro, cambio y recuperación de clave
        ├── plan/                # encuesta (formulario.html) y portal
        ├── includes/            # piezas reutilizables (mensajes, tarjeta de estado)
        └── emails/              # correos de activación y recuperación (HTML + texto)
```

Convenciones:
- Las plantillas viven en `templates/core/` (mismo nombre que la app y que `static/core/`) para evitar choques con otras apps.
- Los estilos no van dentro de las plantillas: cada página carga su archivo desde `static/core/css/` en el bloque `extra_head`.
- Las piezas que se repiten en varias páginas van en `templates/core/includes/`.
