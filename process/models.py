from django.db import models
from django.utils import timezone
from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.urls import reverse

class Floor(models.Model):
    name = models.CharField(max_length=100, blank=True)
    number = models.IntegerField(unique=True)

    def __str__(self):
        if self.name:
            return f"{self.name} (Floor {self.number})"
        return f"Floor {self.number}"




class Apartment(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=True)
    floor = models.ForeignKey(Floor, related_name="apartments", on_delete=models.CASCADE, null=True)
   

    def __str__(self):
        apartment_name = self.name or f"Apartment {self.id}"
        if self.floor:
            return f"{apartment_name} on {self.floor}"
        return apartment_name

    @property
    def current_renter(self):
        return self.renters.filter(move_out_date__isnull=True).first()

    class Meta:
        verbose_name = "Apartment"
        verbose_name_plural = "Apartments"

class YearlyRent(models.Model):
    apartment = models.ForeignKey(Apartment, related_name="yearly_rents", on_delete=models.CASCADE)
    year = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("apartment", "year")

    def __str__(self):
        return f"{self.apartment} - {self.year}: {self.price}"
        
class Renter(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15)
    apartment = models.ForeignKey(Apartment, related_name="renters", on_delete=models.CASCADE)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    move_out_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        return self.move_out_date is None

    def clean(self):
        if self.apartment:
            self.floor = self.apartment.floor

        if self.apartment and self.move_out_date is None:
            active_renters = Renter.objects.filter(
                apartment=self.apartment,
                move_out_date__isnull=True,
            )
            if self.pk:
                active_renters = active_renters.exclude(pk=self.pk)
            if active_renters.exists():
                raise ValidationError({
                    "apartment": "This apartment already has an active renter. Mark that renter as left before adding someone new."
                })

        if self.move_out_date and self.move_out_date < self.start_date:
            raise ValidationError({
                "move_out_date": "Move-out date cannot be before the rent start date."
            })

    def save(self, *args, **kwargs):
        if self.apartment:
            self.floor = self.apartment.floor
        self.full_clean()
        return super().save(*args, **kwargs)

    # ----- Payment Calculations -----
    def months_since_start(self):
        today = self.move_out_date or date.today()
        return (today.year - self.start_date.year) * 12 + (today.month - self.start_date.month) + 1

    def expected_payments(self):
        """Expected payments per month based on yearly rents of the apartment."""
        return sum(item["expected_amount"] for item in self.payment_status_by_month())

    def total_paid(self):
        return sum(p.amount for p in self.payments.all())

    def balance(self):
        """Positive = overpaid, Negative = owes money"""
        return self.total_paid() - self.expected_payments()

    def missed_months(self):
        """
        Return a list of months (YYYY-MM) that the renter didn’t pay.
        Uses month-by-month calculation, even if yearly rent changes."""
        paid_months = set()

        for p in self.payments.all():
            start = p.month_covered or p.date_paid.replace(day=1)
            if p.payment_type == "monthly":
                paid_months.add(start.strftime("%Y-%m"))
            elif p.payment_type == "yearly":
                for i in range(12):
                    m = start + relativedelta(months=i)
                    paid_months.add(m.strftime("%Y-%m"))

        missed = []
        current = self.start_date.replace(day=1)
        end_date = self.move_out_date or date.today()
        today = end_date.replace(day=1)

        while current <= today:
            ym = current.strftime("%Y-%m")
            if ym not in paid_months:
                missed.append(ym)
            current += relativedelta(months=1)

        return missed

    def get_absolute_url(self):
        return reverse("renter-detail", kwargs={"pk": self.pk})

    def payment_status_by_month(self):
        """Returns a list of tuples: (month, paid: True/False) for display purposes"""
        paid_months = set()
        for p in self.payments.all():
            start = p.month_covered or p.date_paid.replace(day=1)
            if p.payment_type == "monthly":
                paid_months.add(start.strftime("%Y-%m"))
            elif p.payment_type == "yearly":
                for i in range(12):
                    m = start + relativedelta(months=i)
                    paid_months.add(m.strftime("%Y-%m"))

        status = []
        current = self.start_date.replace(day=1)
        end_date = self.move_out_date or date.today()
        today = end_date.replace(month=12, day=1)

        while current <= today:
            ym = current.strftime("%Y-%m")
            status.append((ym, ym in paid_months))
            current += relativedelta(months=1)

        return status

    def monthly_rent_for_year(self, year):
        try:
            yearly_rent = self.apartment.yearly_rents.get(year=year)
        except YearlyRent.DoesNotExist:
            return Decimal("0.00")
        return yearly_rent.price / Decimal("12")

    def payment_totals_by_month(self):
        totals = {}
        for p in self.payments.all():
            start = p.month_covered or p.date_paid.replace(day=1)
            if p.payment_type == "monthly":
                month_key = start.strftime("%Y-%m")
                totals[month_key] = totals.get(month_key, Decimal("0.00")) + p.amount
            elif p.payment_type == "yearly":
                monthly_amount = p.amount / Decimal("12")
                for i in range(12):
                    m = start + relativedelta(months=i)
                    month_key = m.strftime("%Y-%m")
                    totals[month_key] = totals.get(month_key, Decimal("0.00")) + monthly_amount
        return totals

    def first_payment_month(self):
        first_month = None
        for p in self.payments.all():
            start = p.month_covered or p.date_paid.replace(day=1)
            start = start.replace(day=1)
            if first_month is None or start < first_month:
                first_month = start
        return first_month

    def payment_status_for_month(self, month_date, paid_totals=None):
        paid_totals = paid_totals or self.payment_totals_by_month()
        month_date = month_date.replace(day=1)
        month_key = month_date.strftime("%Y-%m")
        paid_amount = paid_totals.get(month_key, Decimal("0.00"))
        start_month = self.start_date.replace(day=1)
        move_out_month = self.move_out_date.replace(day=1) if self.move_out_date else None

        if month_date < start_month:
            return {
                "month": month_key,
                "expected_amount": Decimal("0.00"),
                "paid_amount": paid_amount,
                "remaining_amount": Decimal("0.00"),
                "is_paid": True,
                "status_label": "DONE",
                "status_type": "not_due",
            }

        if move_out_month and month_date > move_out_month:
            return {
                "month": month_key,
                "expected_amount": Decimal("0.00"),
                "paid_amount": paid_amount,
                "remaining_amount": Decimal("0.00"),
                "is_paid": True,
                "status_label": "DONE",
                "status_type": "not_due",
            }

        expected_amount = self.monthly_rent_for_year(month_date.year)
        remaining_amount = max(expected_amount - paid_amount, Decimal("0.00"))
        is_paid = expected_amount > 0 and paid_amount >= expected_amount
        return {
            "month": month_key,
            "expected_amount": expected_amount,
            "paid_amount": paid_amount,
            "remaining_amount": remaining_amount,
            "is_paid": is_paid,
            "status_label": "PAID" if is_paid else "UNPAID",
            "status_type": "paid" if is_paid else "unpaid",
        }

    def payment_status_by_month(self):
        """Returns monthly payment amounts and full-payment status."""
        paid_totals = self.payment_totals_by_month()
        status = []
        current = self.start_date.replace(month=1, day=1)
        first_payment_month = self.first_payment_month()
        if first_payment_month and first_payment_month < current:
            current = first_payment_month.replace(month=1, day=1)
        end_date = self.move_out_date or date.today()
        today = end_date.replace(month=12, day=1)

        while current <= today:
            status.append(self.payment_status_for_month(current, paid_totals))
            current += relativedelta(months=1)

        return status

    def missed_months(self):
        return [
            item["month"]
            for item in self.payment_status_by_month()
            if item["expected_amount"] > 0 and not item["is_paid"]
        ]


class Payment(models.Model):
    PAYMENT_TYPES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    renter = models.ForeignKey(Renter, related_name="payments", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField(default=timezone.now)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPES, default="monthly")
    month_covered = models.DateField(help_text="First day of the month this payment covers", blank=True, null=True)

    def __str__(self):
        if self.month_covered:
            return f"{self.payment_type.title()} payment of {self.amount} by {self.renter.name} for {self.month_covered.strftime('%Y-%m')}"
        return f"{self.payment_type.title()} payment of {self.amount} by {self.renter.name} on {self.date_paid}"
