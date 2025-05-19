from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import HousingUnit, Transaction, RentalRate, UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'date_of_birth', 'profile_picture']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'password2', 'email', 'first_name', 'last_name', 'is_staff', 'profile']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        validated_data.pop('password2')
        
        user = User.objects.create_user(**validated_data)
        
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        else:
            UserProfile.objects.create(user=user)
            
        return user

class RentalRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalRate
        fields = '__all__'

class HousingUnitSerializer(serializers.ModelSerializer):
    property_manager = UserSerializer(read_only=True)
    data_entry_user = UserSerializer(read_only=True)
    rental_rate = RentalRateSerializer(read_only=True)
    
    class Meta:
        model = HousingUnit
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    housing_unit = HousingUnitSerializer(read_only=True)
    housing_unit_id = serializers.IntegerField(write_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['created_by']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class DashboardStatsSerializer(serializers.Serializer):
    total_rent_collected = serializers.DecimalField(max_digits=10, decimal_places=2)
    rent_collected_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_properties = serializers.IntegerField()
    rent_pending = serializers.DecimalField(max_digits=10, decimal_places=2)
    occupied_units = serializers.IntegerField()
    vacant_units = serializers.IntegerField()