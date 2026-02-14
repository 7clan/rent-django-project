from django.shortcuts import render, redirect
from django.views.generic import DetailView, ListView
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth import authenticate
from functools import wraps
import jwt
from datetime import datetime, timedelta
import json

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import Renter, Floor, Apartment, Payment
from .models import YearlyRent
from .forms import RenterForm, FloorForm, ApartmentForm

from django.conf import settings
SECRET_KEY = settings.SECRET_KEY
 # use settings.SECRET_KEY in production

# ---------------- JWT LOGIN ----------------
@csrf_exempt
def login_jwt(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    
    try:
        data = json.loads(request.body.decode("utf-8"))
        username = data.get("username")
        password = data.get("password")
    except:
        username = request.POST.get("username")
        password = request.POST.get("password")

    user = authenticate(username=username, password=password)
    if user:
        payload = {
            "user_id": user.id,
            "username": user.username,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        response = JsonResponse({"token": token})
        # Set JWT as HttpOnly cookie
        response.set_cookie("jwt_token", token, httponly=True, samesite="Lax")
        return response

    return JsonResponse({"error": "Invalid credentials"}, status=401)


# ---------------- JWT REQUIRED DECORATOR ----------------
def jwt_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header:
            try:
                prefix, token = auth_header.split()
                if prefix.lower() != "bearer":
                    return JsonResponse({"error": "Unauthorized"}, status=401)
            except:
                return JsonResponse({"error": "Unauthorized"}, status=401)
        else:
            # fallback: check cookie
            token = request.COOKIES.get("jwt_token")
            if not token:
                return JsonResponse({"error": "Unauthorized"}, status=401)

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = payload["user_id"]
        except Exception:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        return view_func(request, *args, **kwargs)
    return wrapper


# ---------------- RENTER DETAIL VIEW ----------------
@method_decorator(csrf_exempt, name='dispatch')
class RenterDetailView(DetailView):
    model = Renter
    template_name = "process/renter_detail.html"
    context_object_name = "renter"

    @method_decorator(jwt_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        months = [f"{i:02}" for i in range(1, 13)]
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        normalized_payments = {}
        for m, paid in self.object.payment_status_by_month():
            year, month = m.split("-")
            normalized_payments[f"{year}-{int(month):02}"] = paid
        current_year = self.object.start_date.year
        end_year = datetime.now().year
        years = list(range(current_year, end_year + 1))
        table = []
        for i, month in enumerate(months):
            row = {"month_name": month_names[i], "statuses": []}
            for year in years:
                ym = f"{year}-{month}"
                row["statuses"].append(normalized_payments.get(ym, False))
            table.append(row)
        context["years"] = years
        context["payments_by_month"] = table
        # compute expected unpaid total using missed months and YearlyRent for the apartment
        missed = self.object.missed_months()
        expected_unpaid = 0.0
        for ym in missed:
            try:
                year = int(ym.split('-')[0])
            except Exception:
                continue
            try:
                yr = YearlyRent.objects.get(apartment=self.object.apartment, year=year)
                monthly = float(yr.price)
            except YearlyRent.DoesNotExist:
                monthly = 0.0
            expected_unpaid += monthly
        context['expected_unpaid'] = round(expected_unpaid, 2)
        context['missed_months'] = missed
        return context

# ---------------- FLOOR PAGE ----------------

@csrf_exempt
@jwt_required
def floor_page(request):
    floor_form = FloorForm()
    apartment_form = ApartmentForm()
    renter_form = RenterForm()

    if request.method == "POST":
        # Get the action from form data
        action = request.POST.get("ac")

        if action == "add_floor":
            floor_form = FloorForm(request.POST)
            if floor_form.is_valid():
                floor_form.save()
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"error": "Invalid data", "errors": floor_form.errors}, status=400)
        elif action == "add_apartment":
            apartment_form = ApartmentForm(request.POST)
            if apartment_form.is_valid():
                apartment_form.save()
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"error": "Invalid data", "errors": apartment_form.errors}, status=400)
        elif action == "add_renter":
            # Prevent creating or assigning renter to an apartment that already has a renter
            apartment_id = request.POST.get('apartment') or request.POST.get('apartment_id')
            if apartment_id:
                try:
                    apt = Apartment.objects.get(id=apartment_id)
                except Apartment.DoesNotExist:
                    return JsonResponse({"error": "Selected apartment does not exist"}, status=400)
                # if an existing renter is already linked to this apartment, block creation
                if hasattr(apt, 'renter'):
                    return JsonResponse({"error": "This apartment already has a renter"}, status=400)

            renter_form = RenterForm(request.POST)
            if renter_form.is_valid():
                renter_form.save()
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"error": "Invalid data", "errors": renter_form.errors}, status=400)
        return JsonResponse({"error": "Invalid data"}, status=400)

    context = {
        "floor_form": floor_form,
        "apartment_form": apartment_form,
        "renter_form": renter_form,
        "all_floors": Floor.objects.all(),
        "all_apartments": Apartment.objects.all(),
    }
    return render(request, "process/FLOOR.html", context)

# ---------------- FLOOR LIST ----------------

class FloorListView(ListView):
    model = Floor
    template_name = "process/FLOOR.html"
    context_object_name = "all_floors"

    @method_decorator(jwt_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # include the same form/context as the function-based view so the template
        # renders correctly when using this class-based view (e.g. /floors/)
        context['floor_form'] = FloorForm()
        context['apartment_form'] = ApartmentForm()
        context['renter_form'] = RenterForm()
        context['all_apartments'] = Apartment.objects.all()
        return context

# ---------------- ADD PAYMENT ----------------
@csrf_exempt
@jwt_required
def add_payment(request, renter_id):
    try:
        renter = Renter.objects.get(id=renter_id)
    except Renter.DoesNotExist:
        return JsonResponse({"error": "Renter not found"}, status=404)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except:
            data = request.POST
        
        try:
            amount = data.get("amount")
            payment_type = data.get("payment_type") or 'monthly'

            if payment_type == 'monthly':
                year_month_covered = data.get("year_month_covered")
                if not amount or not year_month_covered:
                    return JsonResponse({"error": "Missing amount or month"}, status=400)
                month_date = datetime.strptime(year_month_covered, "%Y-%m").date().replace(day=1)
                payment = Payment.objects.create(
                    renter=renter,
                    amount=amount,
                    month_covered=month_date,
                    date_paid=timezone.now().date(),
                    payment_type="monthly"
                )
            elif payment_type == 'yearly':
                year_covered = data.get('year_covered')
                # if amount not provided, try to compute from YearlyRent (monthly * 12)
                if not year_covered:
                    return JsonResponse({"error": "Missing year for yearly payment"}, status=400)
                try:
                    y = int(year_covered)
                except Exception:
                    return JsonResponse({"error": "Invalid year"}, status=400)
                if not amount:
                    try:
                        yr = YearlyRent.objects.get(apartment=renter.apartment, year=y)
                        amount = float(yr.price) * 12.0
                    except YearlyRent.DoesNotExist:
                        amount = 0.0
                month_date = datetime(y, 1, 1).date()
                payment = Payment.objects.create(
                    renter=renter,
                    amount=amount,
                    month_covered=month_date,
                    date_paid=timezone.now().date(),
                    payment_type="yearly"
                )
            else:
                return JsonResponse({"error": "Invalid payment_type"}, status=400)
            # compute updated totals to send back to client
            total_paid = float(renter.total_paid())
            expected_total = float(renter.expected_payments())
            # expected_unpaid: sum of monthly rents for missed months
            missed = renter.missed_months()
            expected_unpaid = 0.0
            for ym in missed:
                try:
                    y = int(ym.split('-')[0])
                except Exception:
                    continue
                try:
                    yr = YearlyRent.objects.get(apartment=renter.apartment, year=y)
                    monthly = float(yr.price)
                except YearlyRent.DoesNotExist:
                    monthly = 0.0
                expected_unpaid += monthly

            balance = total_paid - expected_total

            # respond with canonical month covered and payment_type so client can update UI reliably
            month_str = payment.month_covered.strftime("%Y-%m") if payment.month_covered else None
            return JsonResponse({
                "success": True,
                "payment_id": payment.id,
                "month": month_str,
                "payment_type": payment.payment_type,
                "total_paid": round(total_paid, 2),
                "expected_total": round(expected_total, 2),
                "expected_unpaid": round(expected_unpaid, 2),
                "balance": round(balance, 2)
            })
        except ValueError as e:
            return JsonResponse({"error": f"Invalid date format: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Error creating payment: {str(e)}"}, status=400)
    
    return JsonResponse({"error": "Invalid request"}, status=400)


# ---------------- EXPECTED PAYMENTS API ----------------
@csrf_exempt
def expected_payments_api(request):
    apartment = request.GET.get('apartment')
    start_date = request.GET.get('start_date')
    if not apartment or not start_date:
        return JsonResponse({'error': 'missing params'}, status=400)
    try:
        start = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    except Exception:
        return JsonResponse({'error': 'bad date'}, status=400)
    try:
        apt = Apartment.objects.get(pk=apartment)
    except Apartment.DoesNotExist:
        return JsonResponse({'error': 'apartment not found'}, status=404)
    today = datetime.date.today()
    if start > today:
        return JsonResponse({'error': 'start in future'}, status=400)
    # iterate months and sum expected monthly from YearlyRent
    months = 0
    expected_total = 0.0
    cur = start
    while cur <= today:
        months += 1
        year = cur.year
        # find YearlyRent for this year
        try:
            yr = YearlyRent.objects.get(apartment=apt, year=year)
            # price is monthly amount for that year
            monthly = float(yr.price)
        except YearlyRent.DoesNotExist:
            monthly = 0.0
        expected_total += monthly
        # move to first day of next month
        if cur.month == 12:
            cur = datetime.date(cur.year + 1, 1, cur.day)
        else:
            next_month = cur.month + 1
            # keep same day if possible else cap to 28 to avoid invalid date
            try:
                cur = datetime.date(cur.year, next_month, cur.day)
            except Exception:
                cur = datetime.date(cur.year, next_month, 28)
    return JsonResponse({'months_count': months, 'expected_total': round(expected_total, 2), 'months': months})


@csrf_exempt
def add_yearly_rent(request, renter_id):
    try:
        renter = Renter.objects.get(id=renter_id)
    except Renter.DoesNotExist:
        return JsonResponse({"error": "Renter not found"}, status=404)

    if request.method == "POST":
        # accept both form-encoded POST and JSON body (some client scripts send JSON)
        try:
            payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        except Exception:
            payload = {}

        year = payload.get('year') or request.POST.get('year') or request.POST.get('year_input')
        price = payload.get('monthly_price') or payload.get('price') or request.POST.get('monthly_price') or request.POST.get('price')
        if not year or not price:
            return JsonResponse({"error": "year and monthly_price required"}, status=400)
        try:
            year_i = int(year)
            price_f = float(price)
        except Exception:
            return JsonResponse({"error": "invalid year or price"}, status=400)

        # ensure apartment exists
        apt = renter.apartment
        if not apt:
            return JsonResponse({"error": "Renter has no apartment assigned"}, status=400)

        # create or update yearly rent (price is monthly amount)
        yr, created = YearlyRent.objects.update_or_create(
            apartment=apt,
            year=year_i,
            defaults={"price": price_f}
        )

        # If the request was sent as JSON/AJAX, return JSON so client-side handlers can parse it.
        content_type = (request.headers.get('Content-Type') or '')
        accept = (request.headers.get('Accept') or '')
        is_ajax = ('application/json' in content_type) or (request.headers.get('X-Requested-With') == 'XMLHttpRequest') or ('application/json' in accept)

        if is_ajax:
            return JsonResponse({"success": True, "year": year_i, "monthly_price": round(price_f, 2)})

        # Otherwise, if the requester has a jwt token, redirect to renter detail; else return JSON
        has_token = bool(request.COOKIES.get('jwt_token') or request.headers.get('Authorization'))
        if has_token:
            return redirect(renter.get_absolute_url())
        return JsonResponse({"success": True, "year": year_i, "monthly_price": round(price_f, 2)})

    # GET not allowed
    return JsonResponse({"error": "POST required"}, status=400)
