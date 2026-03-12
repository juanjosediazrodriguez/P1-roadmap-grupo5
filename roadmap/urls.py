from django.urls import path
from . import views

urlpatterns = [
    path('', views.specialization_list, name='specialization_list'),
    path('specialization/<int:pk>/', views.specialization_detail, name='specialization_detail'),
    path('search/specializations/', views.specialization_search, name='specialization_search'),
    path('specialization/<int:pk>/search/', views.course_search, name='course_search'),
    
]
