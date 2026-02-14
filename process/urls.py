from django.urls import path
from . import views
from django.shortcuts import render


urlpatterns = [

   path('floors/', views.FloorListView.as_view(), name='floor-list'),

    path('renter/<int:pk>/', views.RenterDetailView.as_view(), name='renter-detail'),

    path('main-page/', views.floor_page, name='floor-page'),
   path('add_payment/<int:renter_id>/', views.add_payment, name='add_payment'),
   path('api/expected/', views.expected_payments_api, name='expected_api'),
   path('add_yearly_rent/<int:renter_id>/', views.add_yearly_rent, name='add_yearly_rent'),
 path('login-jwt/', views.login_jwt, name='login_jwt'),
    path('', lambda request: render(request, 'process/login.html'), name='login-page'),

]