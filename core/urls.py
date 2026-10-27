from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResidenciaViewSet, LeituraViewSet, PrevisaoSolarView, DashboardView

router = DefaultRouter()
router.register(r'residencias', ResidenciaViewSet)
router.register(r'leituras', LeituraViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('previsao-solar/', PrevisaoSolarView.as_view(), name='previsao-solar'),
    # Rota do Dashboard:
    path('dashboard/<int:residencia_id>/', DashboardView.as_view(), name='dashboard-api'),
]