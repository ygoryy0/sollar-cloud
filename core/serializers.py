from rest_framework import serializers
from .models import Residencia, Leitura

class ResidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Residencia
        fields = '__all__' # Pega todos os campos (nome, cep, potencia, etc)

class LeituraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leitura
        fields = '__all__'