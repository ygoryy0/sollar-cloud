from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Residencia, Leitura
from .serializers import ResidenciaSerializer, LeituraSerializer
import requests

class ResidenciaViewSet(viewsets.ModelViewSet):
    queryset = Residencia.objects.all()
    serializer_class = ResidenciaSerializer

class LeituraViewSet(viewsets.ModelViewSet):
    queryset = Leitura.objects.all()
    serializer_class = LeituraSerializer

# NOVA ROTA: Previsão Solar
class PrevisaoSolarView(APIView):
    def get(self, request):
        # Pega os dados que o frontend vai enviar (latitude, longitude, etc)
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        inclinacao = request.query_params.get('tilt', 20)
        azimute = request.query_params.get('azimuth', 180)
        potencia_kwp = float(request.query_params.get('potencia', 5.4))

        if not lat or not lon:
            return Response({"erro": "Latitude e Longitude são obrigatórias"}, status=status.HTTP_400_BAD_REQUEST)

        # Chama a Open-Meteo
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=global_tilted_irradiance,temperature_2m&tilt={inclinacao}&azimuth={azimute}&forecast_days=7&timezone=auto"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            irradiancia = data.get('hourly', {}).get('global_tilted_irradiance', [])
            temperaturas = data.get('hourly', {}).get('temperature_2m', [])
            tempos = data.get('hourly', {}).get('time', [])

            geracao_diaria = {}
            eficiencia = 0.97
            perdas = 0.10

            # Faz o cálculo solar em Python
            for i in range(len(tempos)):
                dia = tempos[i].split('T')[0]
                irr = max(0, irradiancia[i] or 0)
                temp = temperaturas[i] or 25

                fator_temp = 1 - 0.0035 * (temp - 25) 
                pot_dc = potencia_kwp * (irr / 1000) * fator_temp
                pot_ac = pot_dc * eficiencia * (1 - perdas)

                if dia not in geracao_diaria:
                    geracao_diaria[dia] = 0
                geracao_diaria[dia] += pot_ac

            # Devolve os dados calculados para o HTML
            return Response({
                "status": "sucesso",
                "localizacao": {"lat": lat, "lon": lon},
                "geracao_diaria_kwh": geracao_diaria
            })

        except requests.RequestException as e:
            return Response({"erro": f"Erro ao consultar Open-Meteo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)