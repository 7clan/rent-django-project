from rest_framework import serializers

from .models import Apartment, Floor, Payment, Renter, YearlyRent


class YearlyRentSerializer(serializers.ModelSerializer):
    class Meta:
        model = YearlyRent
        fields = ["id", "apartment", "year", "price"]


class ApartmentSerializer(serializers.ModelSerializer):
    yearly_rents = YearlyRentSerializer(many=True, read_only=True)
    current_renter = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Apartment
        fields = ["id", "name", "floor", "current_renter", "yearly_rents"]


class FloorSerializer(serializers.ModelSerializer):
    apartments = ApartmentSerializer(many=True, read_only=True)

    class Meta:
        model = Floor
        fields = ["id", "name", "number", "apartments"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "renter",
            "amount",
            "date_paid",
            "payment_type",
            "month_covered",
        ]


class RenterSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(read_only=True)
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    expected_payments = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    missed_months = serializers.ListField(child=serializers.CharField(), read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Renter
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "apartment",
            "floor",
            "start_date",
            "move_out_date",
            "is_active",
            "total_paid",
            "expected_payments",
            "balance",
            "missed_months",
            "payments",
        ]
