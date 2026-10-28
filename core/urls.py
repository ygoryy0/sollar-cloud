from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResidenciaViewSet, LeituraViewSet, PrevisaoSolarView, DashboardView, LoginView

router = DefaultRouter()
router.register(r'residencias', ResidenciaViewSet)
router.register(r'leituras', LeituraViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('previsao-solar/', PrevisaoSolarView.as_view(), name='previsao-solar'),
    path('dashboard/<int:residencia_id>/', DashboardView.as_view(), name='dashboard-api'),
    path('login/', LoginView.as_view(), name='login'),
]