from django.contrib import admin
from .models import ConjuntoGraficas, RegistroEnergia


@admin.register(ConjuntoGraficas)
class ConjuntoGraficasAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_carga', 'total_registros')
    search_fields = ('nombre',)


@admin.register(RegistroEnergia)
class RegistroEnergiaAdmin(admin.ModelAdmin):
    list_display = ('conjunto', 'fecha', 'tipo_energia', 'id_cliente', 'total')
    list_filter = ('tipo_energia', 'conjunto')
    search_fields = ('id_cliente',)
