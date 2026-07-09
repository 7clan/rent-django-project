from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .api_views import (
    ApartmentViewSet,
    FloorViewSet,
    PaymentViewSet,
    RenterViewSet,
    YearlyRentViewSet,
)

router = DefaultRouter()
router.register("floors", FloorViewSet, basename="api-floor")
router.register("apartments", ApartmentViewSet, basename="api-apartment")
router.register("yearly-rents", YearlyRentViewSet, basename="api-yearly-rent")
router.register("renters", RenterViewSet, basename="api-renter")
router.register("payments", PaymentViewSet, basename="api-payment")

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
