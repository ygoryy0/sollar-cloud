from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Empresa, Residencia, Leitura
from .serializers import ResidenciaSerializer, LeituraSerializer
from django.shortcuts import render
import requests
import datetime

def home(request):
    return render(request, 'index.html')

class ResidenciaViewSet(viewsets.ModelViewSet):
    queryset = Residencia.objects.all()
    serializer_class = ResidenciaSerializer

class LeituraViewSet(viewsets.ModelViewSet):
    queryset = Leitura.objects.all()
    serializer_class = LeituraSerializer

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            return Response({"erro": "E-mail ou senha inválidos."}, status=status.HTTP_401_UNAUTHORIZED)

        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            residencia_id = None
            empresa_id = None
            
            try:
                res = Residencia.objects.get(usuario=user)
                residencia_id = res.id
                if res.empresa:
                    empresa_id = res.empresa.id
            except Residencia.DoesNotExist:
                pass

            return Response({
                "status": "sucesso",
                "access": str(refresh.access_token),
                "nome": user.first_name or user.username,
                "residencia_id": residencia_id,
                "is_master": user.is_superuser,
                "empresa_id": empresa_id
            })
        else:
            return Response({"erro": "E-mail ou senha inválidos."}, status=status.HTTP_401_UNAUTHORIZED)

class RegisterClienteView(APIView):
    def post(self, request):
        nome = request.data.get('nome')
        email = request.data.get('email')
        password = request.data.get('password')
        cep = request.data.get('cep')

        if User.objects.filter(email=email).exists():
            return Response({"erro": "E-mail já cadastrado."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password)
        except ValidationError as e:
            return Response({"erro": e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=email, email=email, password=password, first_name=nome)
                Residencia.objects.create(
                    usuario=user, 
                    nome=nome, 
                    apelido="Minha Casa", 
                    cep=cep, 
                    cidade="A definir", 
                    estado="BR", 
                    potencia_instalada=5.4, 
                    inclinacao=20, 
                    orientacao="Norte", 
                    tarifa=0.85
                )
            return Response({"status": "sucesso", "mensagem": "Conta criada com sucesso!"})
        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CadastrarEmpresaView(APIView):
    def post(self, request):
        nome_empresa = request.data.get('nome_empresa')
        cnpj = request.data.get('cnpj')
        email_gestor = request.data.get('email_gestor')
        password = request.data.get('password')

        if User.objects.filter(email=email_gestor).exists():
            return Response({"erro": "E-mail do gestor já cadastrado."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password)
        except ValidationError as e:
            return Response({"erro": e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                empresa = Empresa.objects.create(nome=nome_empresa, cnpj=cnpj)
                user = User.objects.create_user(username=email_gestor, email=email_gestor, password=password, first_name=nome_empresa)
                Residencia.objects.create(
                    empresa=empresa, 
                    usuario=user, 
                    nome=nome_empresa, 
                    apelido="Sede", 
                    cep="00000-000", 
                    cidade="A definir", 
                    estado="BR", 
                    potencia_instalada=10.0,
                    inclinacao=20,
                    orientacao="Norte",
                    tarifa=0.85
                )
            return Response({"status": "sucesso", "mensagem": "Empresa cadastrada!"})
        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListarEmpresasView(APIView):
    def get(self, request):
        empresas = Empresa.objects.all().order_by('-data_cadastro')
        dados = []
        for emp in empresas:
            dados.append({
                "id": emp.id,
                "nome": emp.nome,
                "cnpj": emp.cnpj or "Não informado",
                "data": emp.data_cadastro.strftime('%d/%m/%Y')
            })
        return Response(dados)

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

            for i in range(len(tempos)):
                dia = tempos[i].split('T')[0]
                irr = max(0, irradiancias[i] or 0)
                pot_dc = potencia_kwp * (irr / 1000)
                pot_ac = pot_dc * eficiencia * (1 - perdas)

                if dia not in geracao_diaria:
                    geracao_diaria[dia] = 0
                geracao_diaria[dia] += pot_ac

            previsao_formatada = []
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
                    "dia_semana": dias_semana_pt[data_obj.weekday()],
                    "dia_mes": data_obj.strftime('%d/%m'),
                    "icone": icone,
                    "tempo": tempo,
                    "temp_max": round(temp_max[i]),
                    "temp_min": round(temp_min[i]),
                    "geracao_kwh": round(geracao_diaria.get(dia_str, 0), 1)
                })

            return Response({"status": "sucesso", "previsao": previsao_formatada})

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