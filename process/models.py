from django.db import models
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta
from django.urls import reverse

class Floor(models.Model):
    number = models.IntegerField(unique=True)

    def __str__(self):
        return f"Floor {self.number}"




class Apartment(models.Model):
    id = models.AutoField(primary_key=True)
    floor = models.ForeignKey(Floor, related_name="apartments", on_delete=models.CASCADE, null=True)
   

    def __str__(self):
        return f"Apartment {self.id} on Floor {self.floor.number}"

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
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    apartment = models.OneToOneField(Apartment, on_delete=models.CASCADE)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)

    def __str__(self):
        return self.name

    # ----- Payment Calculations -----
    def months_since_start(self):
        today = date.today()
        return (today.year - self.start_date.year) * 12 + (today.month - self.start_date.month) + 1

    def expected_payments(self):
        """Expected payments per month based on yearly rents of the apartment."""
        total = 0
        today = date.today().replace(day=1)
        current = self.start_date.replace(day=1)

        while current <= today:
            try:
                year_rent = self.apartment.yearly_rents.get(year=current.year)
                monthly_rent = year_rent.price / 12
                total += monthly_rent
            except YearlyRent.DoesNotExist:
                total += 0
            current += relativedelta(months=1)

        return total

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
        today = date.today().replace(day=1)

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
            start = p.date_paid.replace(day=1)
            if p.payment_type == "monthly":
                paid_months.add(start.strftime("%Y-%m"))
            elif p.payment_type == "yearly":
                for i in range(12):
                    m = start + relativedelta(months=i)
                    paid_months.add(m.strftime("%Y-%m"))

        status = []
        current = self.start_date.replace(day=1)
        today = date.today().replace(day=1)

        while current <= today:
            ym = current.strftime("%Y-%m")
            status.append((ym, ym in paid_months))
            current += relativedelta(months=1)

        return status


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
