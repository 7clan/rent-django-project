
from .models import Floor
from .models import Apartment, Renter, Payment
from django import forms
from django.forms import ModelForm

class RenterForm(ModelForm):
    class Meta:
        model = Renter
        fields = '__all__'
class FloorForm(ModelForm):
    class Meta:
        model = Floor
        fields = '__all__'
class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'
class ApartmentForm(ModelForm):
    class Meta:
        model = Apartment
        fields = '__all__'
        