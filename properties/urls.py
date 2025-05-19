from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'housing-units', views.HousingUnitViewSet)
router.register(r'transactions', views.TransactionViewSet)
router.register(r'rental-rates', views.RentalRateViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', views.login_view, name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('reports/generate/', views.generate_report, name='generate-report'),
]