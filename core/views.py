from rest_framework import viewsets
from .models import Residencia, Leitura
from .serializers import ResidenciaSerializer, LeituraSerializer

class ResidenciaViewSet(viewsets.ModelViewSet):
    queryset = Residencia.objects.all()
    serializer_class = ResidenciaSerializer

class LeituraViewSet(viewsets.ModelViewSet):
    queryset = Leitura.objects.all()
    serializer_class = LeituraSerializer