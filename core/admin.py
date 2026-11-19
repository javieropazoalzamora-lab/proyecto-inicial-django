from django.contrib import admin

from .models import PerfilSansano, PlanSemanal


@admin.register(PerfilSansano)
class PerfilSansanoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'peso', 'altura', 'imc', 'objetivo', 'actividad_fisica', 'mayor_de_edad')
    list_filter = ('objetivo', 'actividad_fisica', 'tipo_dieta', 'mayor_de_edad')
    search_fields = ('usuario__username', 'usuario__email')


@admin.register(PlanSemanal)
class PlanSemanalAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'origen', 'actualizado')
    list_filter = ('origen',)
    search_fields = ('usuario__username',)
    readonly_fields = ('huella', 'actualizado')
