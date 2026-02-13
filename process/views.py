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
from .forms import RenterForm, FloorForm, ApartmentForm

SECRET_KEY = "your_super_secret_key"  # use settings.SECRET_KEY in production

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
        return context

# ---------------- FLOOR PAGE ----------------

@csrf_exempt
@jwt_required
def floor_page(request):
    floor_form = FloorForm()
    apartment_form = ApartmentForm()
    renter_form = RenterForm()

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except:
            data = request.POST
        action = data.get("ac")

        if action == "add_floor":
            floor_form = FloorForm(data)
            if floor_form.is_valid():
                floor_form.save()
                return JsonResponse({"success": True})
        elif action == "add_apartment":
            apartment_form = ApartmentForm(data)
            if apartment_form.is_valid():
                apartment_form.save()
                return JsonResponse({"success": True})
        elif action == "add_renter":
            renter_form = RenterForm(data)
            if renter_form.is_valid():
                renter_form.save()
                return JsonResponse({"success": True})
        return JsonResponse({"error": "Invalid data"}, status=400)

    context = {
        "floor_form": floor_form,
        "apartment_form": apartment_form,
        "renter_form": renter_form,
        "all_floors": Floor.objects.all(),
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

# ---------------- ADD PAYMENT ----------------
@csrf_exempt
@jwt_required
def add_payment(request, renter_id):
    renter = Renter.objects.get(id=renter_id)
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except:
            data = request.POST
        amount = data.get("amount")
        year_month_covered = data.get("year_month_covered")
        month_date = datetime.strptime(year_month_covered, "%Y-%m").date().replace(day=1)
        
        Payment.objects.create(
            renter=renter,
            amount=amount,
            month_covered=month_date,
            date_paid=timezone.now().date(),
            payment_type="monthly"  # or set according to your data
        )
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid request"}, status=400)
