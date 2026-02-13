from django.urls import path
from . import views
from django.shortcuts import render


urlpatterns = [

   path('floors/', views.FloorListView.as_view(), name='floor-list'),

    path('renter/<int:pk>/', views.RenterDetailView.as_view(), name='renter-detail'),

    path('main-page/', views.floor_page, name='floor-page'),
    path('add_payment/<int:renter_id>/', views.add_payment, name='add_payment'),
 path('login-jwt/', views.login_jwt, name='login_jwt'),
    path('', lambda request: render(request, 'process/login.html'), name='login-page'),

]