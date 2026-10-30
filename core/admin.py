from django.contrib import admin
from .models import Empresa, Residencia, Leitura

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'data_cadastro')

@admin.register(Residencia)
class ResidenciaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'apelido', 'empresa', 'cidade', 'estado', 'potencia_instalada')

@admin.register(Leitura)
class LeituraAdmin(admin.ModelAdmin):
    list_display = ('residencia', 'data_hora', 'consumo_kwh', 'geracao_kwh')