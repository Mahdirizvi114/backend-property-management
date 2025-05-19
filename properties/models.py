from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta

class HousingUnit(models.Model):
    OCCUPANCY_STATUS = (
        ('occupied', 'Occupied'),
        ('vacant', 'Vacant'),
    )
    
    unit_name = models.CharField(max_length=100)
    address = models.TextField()
    location = models.CharField(max_length=100)
    property_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_units')
    data_entry_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_units')
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tenant_name = models.CharField(max_length=100, blank=True)
    tenant_phone = models.CharField(max_length=20, blank=True)
    tenant_email = models.EmailField(blank=True)
    occupancy_status = models.CharField(max_length=10, choices=OCCUPANCY_STATUS, default='vacant')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.unit_name

    @classmethod
    def get_dashboard_stats(cls, user=None):
        queryset = cls.objects.all()
        if user and not user.is_staff:
            queryset = queryset.filter(data_entry_user=user)
        
        total_properties = queryset.count()
        occupied_units = queryset.filter(occupancy_status='occupied').count()
        vacant_units = queryset.filter(occupancy_status='vacant').count()
        
        return {
            'total_properties': total_properties,
            'occupied_units': occupied_units,
            'vacant_units': vacant_units
        }

class Transaction(models.Model):
    PAYMENT_MODES = (
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('online', 'Online'),
    )
    
    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('pending', 'Pending'),
    )
    
    housing_unit = models.ForeignKey(HousingUnit, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES)
    reference_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.housing_unit.unit_name} - {self.payment_date}"

    class Meta:
        ordering = ['-payment_date']

    @classmethod
    def get_dashboard_stats(cls, user=None):
        queryset = cls.objects.all()
        if user and not user.is_staff:
            queryset = queryset.filter(housing_unit__data_entry_user=user)
        
        now = timezone.now()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total_collected = queryset.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
        monthly_collected = queryset.filter(
            status='paid',
            payment_date__gte=first_day_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        pending_amount = queryset.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'total_rent_collected': float(total_collected),
            'rent_collected_this_month': float(monthly_collected),
            'rent_pending': float(pending_amount)
        }

class RentalRate(models.Model):
    housing_unit = models.OneToOneField(HousingUnit, on_delete=models.CASCADE, related_name='rental_rate')
    base_rate = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    maintenance_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    utility_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    effective_from = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rates for {self.housing_unit.unit_name}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username