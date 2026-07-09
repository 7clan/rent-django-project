from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Apartment, Floor, Payment, Renter, YearlyRent
from .forms import RenterForm


class RenterPaymentStatusTests(TestCase):
    def test_month_covered_controls_paid_month_display(self):
        floor = Floor.objects.create(number=1)
        apartment = Apartment.objects.create(floor=floor)
        YearlyRent.objects.create(apartment=apartment, year=2026, price="12000.00")
        renter = Renter.objects.create(
            name="Test Renter",
            email="renter@example.com",
            phone="70123456",
            apartment=apartment,
            floor=floor,
            start_date=date(2026, 1, 1),
        )
        Payment.objects.create(
            renter=renter,
            amount="1000.00",
            date_paid=date(2026, 7, 9),
            payment_type="monthly",
            month_covered=date(2026, 3, 1),
        )

        statuses = {
            item["month"]: item
            for item in renter.payment_status_by_month()
        }

        self.assertTrue(statuses["2026-03"]["is_paid"])
        self.assertFalse(statuses["2026-07"]["is_paid"])

    def test_partial_payment_does_not_mark_month_paid(self):
        floor = Floor.objects.create(number=2)
        apartment = Apartment.objects.create(floor=floor)
        YearlyRent.objects.create(apartment=apartment, year=2026, price="12000.00")
        renter = Renter.objects.create(
            name="Partial Renter",
            email="partial@example.com",
            phone="70999999",
            apartment=apartment,
            floor=floor,
            start_date=date(2026, 1, 1),
        )
        Payment.objects.create(
            renter=renter,
            amount="400.00",
            date_paid=date(2026, 7, 9),
            payment_type="monthly",
            month_covered=date(2026, 3, 1),
        )

        statuses = {
            item["month"]: item
            for item in renter.payment_status_by_month()
        }

        self.assertFalse(statuses["2026-03"]["is_paid"])
        self.assertEqual(statuses["2026-03"]["expected_amount"], 1000)
        self.assertEqual(statuses["2026-03"]["paid_amount"], 400)
        self.assertEqual(statuses["2026-03"]["remaining_amount"], 600)

    def test_payment_before_start_date_is_still_shown(self):
        floor = Floor.objects.create(number=3)
        apartment = Apartment.objects.create(floor=floor)
        YearlyRent.objects.create(apartment=apartment, year=2025, price="1200.00")
        renter = Renter.objects.create(
            name="Ali Hassan",
            email="ali@example.com",
            phone="70111111",
            apartment=apartment,
            floor=floor,
            start_date=date(2025, 3, 6),
        )
        Payment.objects.create(
            renter=renter,
            amount="100.00",
            date_paid=date(2026, 7, 9),
            payment_type="monthly",
            month_covered=date(2025, 2, 1),
        )

        statuses = {
            item["month"]: item
            for item in renter.payment_status_by_month()
        }

        self.assertTrue(statuses["2025-02"]["is_paid"])

    def test_months_before_renter_start_month_are_not_due(self):
        floor = Floor.objects.create(number=7)
        apartment = Apartment.objects.create(floor=floor)
        YearlyRent.objects.create(apartment=apartment, year=2026, price="1200.00")
        renter = Renter.objects.create(
            name="March Renter",
            email="",
            phone="70000007",
            apartment=apartment,
            floor=floor,
            start_date=date(2026, 3, 15),
        )

        statuses = {
            item["month"]: item
            for item in renter.payment_status_by_month()
        }

        self.assertEqual(statuses["2026-01"]["status_label"], "DONE")
        self.assertEqual(statuses["2026-01"]["expected_amount"], 0)
        self.assertEqual(statuses["2026-02"]["status_label"], "DONE")
        self.assertEqual(statuses["2026-02"]["expected_amount"], 0)
        self.assertEqual(statuses["2026-03"]["status_label"], "UNPAID")
        self.assertEqual(statuses["2026-03"]["expected_amount"], 100)

    def test_active_future_months_are_not_marked_done(self):
        floor = Floor.objects.create(number=8)
        apartment = Apartment.objects.create(floor=floor)
        YearlyRent.objects.create(apartment=apartment, year=2099, price="1200.00")
        renter = Renter.objects.create(
            name="Future Renter",
            email="",
            phone="70000008",
            apartment=apartment,
            floor=floor,
            start_date=date(2099, 1, 1),
        )

        status = renter.payment_status_for_month(date(2099, 8, 1))

        self.assertEqual(status["status_label"], "UNPAID")
        self.assertEqual(status["status_type"], "unpaid")
        self.assertFalse(status["is_paid"])
        self.assertEqual(status["expected_amount"], 100)

    def test_months_after_move_out_are_not_due(self):
        floor = Floor.objects.create(number=9)
        apartment = Apartment.objects.create(floor=floor)
        YearlyRent.objects.create(apartment=apartment, year=2026, price="1200.00")
        renter = Renter.objects.create(
            name="Moved Renter",
            email="",
            phone="70000009",
            apartment=apartment,
            floor=floor,
            start_date=date(2026, 1, 1),
            move_out_date=date(2026, 7, 1),
        )

        status = renter.payment_status_for_month(date(2026, 8, 1))

        self.assertEqual(status["status_label"], "DONE")
        self.assertEqual(status["status_type"], "not_due")
        self.assertEqual(status["expected_amount"], 0)


class RenterOccupancyTests(TestCase):
    def test_apartment_can_only_have_one_active_renter(self):
        floor = Floor.objects.create(number=4)
        apartment = Apartment.objects.create(floor=floor)
        Renter.objects.create(
            name="First Renter",
            email="",
            phone="70000001",
            apartment=apartment,
            floor=floor,
            start_date=date(2026, 1, 1),
        )

        with self.assertRaises(ValidationError):
            Renter.objects.create(
                name="Second Renter",
                email="",
                phone="70000002",
                apartment=apartment,
                floor=floor,
                start_date=date(2026, 2, 1),
            )

    def test_apartment_is_available_after_renter_leaves(self):
        floor = Floor.objects.create(number=5)
        apartment = Apartment.objects.create(floor=floor)
        old_renter = Renter.objects.create(
            name="Old Renter",
            email="",
            phone="70000003",
            apartment=apartment,
            floor=floor,
            start_date=date(2026, 1, 1),
        )
        old_renter.move_out_date = date(2026, 2, 1)
        old_renter.save()

        new_renter = Renter.objects.create(
            name="New Renter",
            email="",
            phone="70000004",
            apartment=apartment,
            floor=floor,
            start_date=date(2026, 3, 1),
        )

        self.assertEqual(apartment.current_renter, new_renter)

    def test_renter_form_does_not_show_floor_or_occupied_apartments(self):
        floor = Floor.objects.create(number=6)
        occupied = Apartment.objects.create(floor=floor)
        available = Apartment.objects.create(floor=floor)
        Renter.objects.create(
            name="Current Renter",
            email="",
            phone="70000005",
            apartment=occupied,
            floor=floor,
            start_date=date(2026, 1, 1),
        )

        form = RenterForm()

        self.assertNotIn("floor", form.fields)
        self.assertFalse(form.fields["email"].required)
        self.assertNotIn(occupied, form.fields["apartment"].queryset)
        self.assertIn(available, form.fields["apartment"].queryset)
