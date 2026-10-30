from django.db import models
from django.contrib.auth.models import User

class Empresa(models.Model):
    nome = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class Residencia(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name='residencias')
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=100)
    apelido = models.CharField(max_length=50)
    cep = models.CharField(max_length=9)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    potencia_instalada = models.DecimalField(max_digits=5, decimal_places=2, help_text="Em kWp")
    inclinacao = models.IntegerField(default=20)
    orientacao = models.CharField(max_length=20, default="Norte")
    tarifa = models.DecimalField(max_digits=5, decimal_places=2, default=0.85)
    
    def __str__(self):
        return f"{self.nome} ({self.apelido})"

class Leitura(models.Model):
    residencia = models.ForeignKey(Residencia, on_delete=models.CASCADE, related_name='leituras')
    data_hora = models.DateTimeField()
    consumo_kwh = models.DecimalField(max_digits=8, decimal_places=2)
    geracao_kwh = models.DecimalField(max_digits=8, decimal_places=2)
    
    def __str__(self):
        return f"Leitura {self.residencia.apelido} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"