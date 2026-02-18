from django.urls import path
from . import views

urlpatterns = [
    path('', views.specialization_list, name='specialization_list'),
]
