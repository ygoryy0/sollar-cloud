from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from .models import Residencia, Leitura
from .serializers import ResidenciaSerializer, LeituraSerializer
import requests
import datetime

class ResidenciaViewSet(viewsets.ModelViewSet):
    queryset = Residencia.objects.all()
    serializer_class = ResidenciaSerializer

class LeituraViewSet(viewsets.ModelViewSet):
    queryset = Leitura.objects.all()
    serializer_class = LeituraSerializer

class PrevisaoSolarView(APIView):
    def get(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        inclinacao = request.query_params.get('tilt', 20)
        azimute = request.query_params.get('azimuth', 180)
        potencia_kwp = float(request.query_params.get('potencia', 5.4))

        if not lat or not lon:
            return Response({"erro": "Latitude e Longitude são obrigatórias"}, status=status.HTTP_400_BAD_REQUEST)

        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=global_tilted_irradiance&daily=weather_code,temperature_2m_max,temperature_2m_min&tilt={inclinacao}&azimuth={azimute}&forecast_days=7&timezone=auto"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            tempos = data.get('hourly', {}).get('time', [])
            irradiancias = data.get('hourly', {}).get('global_tilted_irradiance', [])
            
            dias = data.get('daily', {}).get('time', [])
            climas = data.get('daily', {}).get('weather_code', [])
            temp_max = data.get('daily', {}).get('temperature_2m_max', [])
            temp_min = data.get('daily', {}).get('temperature_2m_min', [])

            geracao_diaria = {}
            eficiencia = 0.97
            perdas = 0.10

            # Calcula geração hora a hora
            for i in range(len(tempos)):
                dia = tempos[i].split('T')[0]
                irr = max(0, irradiancias[i] or 0)
                pot_dc = potencia_kwp * (irr / 1000) 
                pot_ac = pot_dc * eficiencia * (1 - perdas)

                if dia not in geracao_diaria:
                    geracao_diaria[dia] = 0
                geracao_diaria[dia] += pot_ac

            previsao_formatada = []
            
            # Dicionário para traduzir o dia da semana
            dias_semana_pt = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}

            for i, dia_str in enumerate(dias):
                data_obj = datetime.datetime.strptime(dia_str, '%Y-%m-%d')
                
                codigo = climas[i]
                icone = '☀️'
                tempo = 'Ensolarado'
                if codigo in [1, 2, 3]: icone, tempo = '⛅', 'Parcial. nublado'
                elif codigo in [45, 48]: icone, tempo = '🌫️', 'Nevoeiro'
                elif codigo in [51, 53, 55, 61, 63, 65, 80, 81, 82]: icone, tempo = '🌧️', 'Chuva'
                elif codigo in [71, 73, 75, 77]: icone, tempo = '❄️', 'Neve'
                elif codigo in [95, 96, 99]: icone, tempo = '⛈️', 'Tempestade'

                previsao_formatada.append({
                    "data": dia_str,
                    "dia_semana": dias_semana_pt[data_obj.weekday()], # Traduzido aqui
                    "dia_mes": data_obj.strftime('%d/%m'),
                    "icone": icone,
                    "tempo": tempo,
                    "temp_max": round(temp_max[i]),
                    "temp_min": round(temp_min[i]),
                    "geracao_kwh": round(geracao_diaria.get(dia_str, 0), 1)
                })

            return Response({
                "status": "sucesso",
                "previsao": previsao_formatada
            })

        except requests.RequestException as e:
            return Response({"erro": f"Erro na API: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardView(APIView):
    def get(self, request, residencia_id):
        try:
            res = Residencia.objects.get(id=residencia_id)
        except Residencia.DoesNotExist:
            return Response({"erro": "Residência não encontrada"}, status=404)

        leituras = res.leituras.all()
        
        total_consumo = float(leituras.aggregate(Sum('consumo_kwh'))['consumo_kwh__sum'] or 0)
        total_geracao = float(leituras.aggregate(Sum('geracao_kwh'))['geracao_kwh__sum'] or 0)
        
        autoconsumo = min(total_consumo, total_geracao)
        excedente = max(0.0, total_geracao - total_consumo)
        consumo_rede = max(0.0, total_consumo - total_geracao)
        
        tarifa = float(res.tarifa)
        custo_rede = consumo_rede * tarifa
        custo_fio_b = excedente * 0.28 * 0.60 * tarifa
        fatura_estimada = custo_rede + custo_fio_b
        
        return Response({
            "residencia": {
                "nome": res.nome,
                "apelido": res.apelido,
                "potencia": float(res.potencia_instalada),
                "cep": res.cep
            },
            "metricas": {
                "consumo_total": total_consumo,
                "geracao_total": total_geracao,
                "autoconsumo": autoconsumo,
                "excedente": excedente,
                "consumo_rede": consumo_rede,
                "fatura": fatura_estimada
            }
        })