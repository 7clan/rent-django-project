from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Apartment, Floor, Payment, Renter, YearlyRent
from .serializers import (
    ApartmentSerializer,
    FloorSerializer,
    PaymentSerializer,
    RenterSerializer,
    YearlyRentSerializer,
)


class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.prefetch_related("apartments").order_by("number")
    serializer_class = FloorSerializer
    permission_classes = [IsAuthenticated]


class ApartmentViewSet(viewsets.ModelViewSet):
    queryset = Apartment.objects.select_related("floor").prefetch_related("yearly_rents").order_by("id")
    serializer_class = ApartmentSerializer
    permission_classes = [IsAuthenticated]


class YearlyRentViewSet(viewsets.ModelViewSet):
    queryset = YearlyRent.objects.select_related("apartment", "apartment__floor").order_by("year")
    serializer_class = YearlyRentSerializer
    permission_classes = [IsAuthenticated]


class RenterViewSet(viewsets.ModelViewSet):
    queryset = (
        Renter.objects.select_related("floor", "apartment")
        .prefetch_related("payments", "apartment__yearly_rents")
        .order_by("name")
    )
    serializer_class = RenterSerializer
    permission_classes = [IsAuthenticated]


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("renter").order_by("-date_paid")
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
