
from .models import Floor
from .models import Apartment, Renter, Payment
from django import forms
from django.forms import ModelForm

class RenterForm(ModelForm):
    class Meta:
        model = Renter
        fields = ['name', 'email', 'phone', 'apartment', 'floor', 'start_date']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter renter name', 'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email address', 'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter phone number', 'class': 'form-input'}),
            'apartment': forms.Select(attrs={'class': 'form-select'}),
            'floor': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'placeholder': 'Start date'}),
        }

class FloorForm(ModelForm):
    class Meta:
        model = Floor
        fields = ['number']
        widgets = {
            'number': forms.NumberInput(attrs={'placeholder': 'Enter floor number', 'class': 'form-input'}),
        }

class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'

class ApartmentForm(ModelForm):
    class Meta:
        model = Apartment
        fields = ['floor']
        widgets = {
            'floor': forms.Select(attrs={'class': 'form-select'}),
        }
        