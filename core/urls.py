from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResidenciaViewSet, LeituraViewSet

router = DefaultRouter()
router.register(r'residencias', ResidenciaViewSet)
router.register(r'leituras', LeituraViewSet)

urlpatterns = [
    path('', include(router.urls)),
]