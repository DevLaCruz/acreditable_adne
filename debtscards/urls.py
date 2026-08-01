from django.urls import path
from . import views

urlpatterns = [
    path('clients/', views.client_list, name='client_list'),
    path('clients/new/', views.client_create, name='client_create'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:client_id>/new-card/', views.card_create, name='card_create'),
    path('cards/<int:card_id>/', views.card_detail, name='card_detail'),
    path('cards/<int:card_id>/pay/', views.payment_add, name='payment_add'),
]
