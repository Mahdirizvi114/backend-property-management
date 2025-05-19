from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime
from .models import HousingUnit, Transaction, RentalRate, UserProfile, User
from .serializers import (
    HousingUnitSerializer, TransactionSerializer, LoginSerializer,
    UserSerializer, RentalRateSerializer, DashboardStatsSerializer
)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    user = request.user if not request.user.is_staff else None
    
    housing_stats = HousingUnit.get_dashboard_stats(user)
    transaction_stats = Transaction.get_dashboard_stats(user)
    
    stats = {
        **housing_stats,
        **transaction_stats
    }
    
    serializer = DashboardStatsSerializer(stats)
    return Response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

class HousingUnitViewSet(viewsets.ModelViewSet):
    queryset = HousingUnit.objects.all()
    serializer_class = HousingUnitSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return HousingUnit.objects.all()
        return HousingUnit.objects.filter(data_entry_user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(property_manager=self.request.user)

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Transaction.objects.all()
        return Transaction.objects.filter(
            housing_unit__data_entry_user=self.request.user
        )
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class RentalRateViewSet(viewsets.ModelViewSet):
    queryset = RentalRate.objects.all()
    serializer_class = RentalRateSerializer
    permission_classes = [permissions.IsAdminUser]

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def generate_report(request):
    report_type = request.query_params.get('type', 'transactions')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if report_type == 'transactions':
        queryset = Transaction.objects.all()
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
            
        data = TransactionSerializer(queryset, many=True).data
    else:
        queryset = HousingUnit.objects.all()
        data = HousingUnitSerializer(queryset, many=True).data
    
    return Response(data)