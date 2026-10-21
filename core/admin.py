from django.contrib import admin
from .models import Residencia, Leitura

@admin.register(Residencia)
class ResidenciaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'apelido', 'cidade', 'estado', 'potencia_instalada')

@admin.register(Leitura)
class LeituraAdmin(admin.ModelAdmin):
    list_display = ('residencia', 'data_hora', 'consumo_kwh', 'geracao_kwh')