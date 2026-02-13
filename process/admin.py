from django.contrib import admin
from .models import Renter, Payment, Floor, Apartment,YearlyRent

@admin.register(Renter)
class RenterAdmin(admin.ModelAdmin):
    list_display = ("name", "apartment", "total_paid", "expected_payments", "balance")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("renter", "amount", "date_paid", "payment_type")
    list_filter = ("payment_type", "date_paid")

class ApartmentInline(admin.TabularInline):
    model = Apartment
    extra = 1

@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ("number", "apartment_count")
    list_filter = ("number",)
    inlines = [ApartmentInline]

    def apartment_count(self, obj):
        return obj.apartments.count()
    apartment_count.short_description = "Number of Apartments"

@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "floor")
    list_filter = ("floor",)
@admin.register(YearlyRent)
class YearlyRentAdmin(admin.ModelAdmin):
    list_display = ("apartment", "year", "price")
    list_filter = ("year", "apartment")