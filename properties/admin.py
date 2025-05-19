from django.contrib import admin
from .models import HousingUnit, Transaction, RentalRate, UserProfile

admin.site.register(HousingUnit)
admin.site.register(Transaction)
admin.site.register(RentalRate)
admin.site.register(UserProfile)
