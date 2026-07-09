
from .models import Floor
from .models import Apartment, Renter, Payment, YearlyRent
from django import forms
from django.forms import ModelForm

class RenterForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        occupied_apartments = Renter.objects.filter(
            move_out_date__isnull=True,
        ).values_list("apartment_id", flat=True)
        self.fields["apartment"].queryset = Apartment.objects.exclude(
            id__in=occupied_apartments,
        )
        self.fields["email"].required = False

    class Meta:
        model = Renter
        fields = ["name", "email", "phone", "apartment", "start_date"]
        labels = {
            "name": "Renter name",
            "email": "Renter email (optional)",
            "phone": "Renter phone",
            "apartment": "Apartment",
            "start_date": "Rent start date",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Example: Ali Hassan"}),
            "email": forms.EmailInput(attrs={"placeholder": "Example: ali@example.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "Example: 70123456"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
        }
class FloorForm(ModelForm):
    class Meta:
        model = Floor
        fields = '__all__'
        labels = {
            "name": "Floor name",
            "number": "Floor number",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Example: First floor"}),
            "number": forms.NumberInput(attrs={"placeholder": "Example: 1"}),
        }
class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'
class ApartmentForm(ModelForm):
    class Meta:
        model = Apartment
        fields = '__all__'
        labels = {
            "name": "Apartment name/number",
            "floor": "Floor",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Example: A1 or Apartment 101"}),
        }

class YearlyRentForm(ModelForm):
    class Meta:
        model = YearlyRent
        fields = '__all__'
        labels = {
            "apartment": "Apartment",
            "year": "Year",
            "price": "Yearly rent",
        }
        widgets = {
            "year": forms.NumberInput(attrs={"placeholder": "Example: 2026"}),
            "price": forms.NumberInput(attrs={"placeholder": "Example: 12000", "step": "0.01"}),
        }
        
