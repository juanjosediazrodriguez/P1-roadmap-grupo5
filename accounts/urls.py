from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('preferences/', views.preferences_view, name='preferences'),
    path('preferences/save/', views.save_preferences, name='save_preferences'),
    path('preferences/delete/', views.delete_preferences, name='delete_preferences'),
    path('profile/', views.profile_view, name='profile'),
]
