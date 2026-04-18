from django.urls import path
from . import views

urlpatterns = [
    path('', views.roadmap_view, name='roadmap'),
    
    # Especializaciones
    path('specializations/', views.specialization_list, name='specialization_list'),
    path('specialization/<int:pk>/', views.specialization_detail, name='specialization_detail'),
    path('search/specializations/', views.specialization_search, name='specialization_search'),
    path('specialization/<int:pk>/search/', views.specialization_course_search, name='specialization_course_search'),
    path('specialization/<int:pk>/roadmap/', views.specialization_roadmap, name='specialization_roadmap'),
    
    # Trayectorias
    path('tracks/', views.track_list, name='track_list'),
    path('tracks/profesionalizantes/', views.track_professional_list, name='track_professional_list'),
    path('tracks/flexibles/', views.track_flexible_list, name='track_flexible_list'),
    path('track/<int:pk>/', views.track_detail, name='track_detail'),
    path('search/tracks/', views.track_search, name='track_search'),
    path('track/<int:pk>/search/', views.track_course_search, name='track_course_search'),
    path('track/<int:pk>/roadmap/', views.track_roadmap, name='track_roadmap'),
    
    # Líneas de Énfasis
    path('emphasis/', views.emphasis_line_list, name='emphasis_line_list'),
    path('emphasis/<int:pk>/', views.emphasis_line_detail, name='emphasis_line_detail'),
    path('search/emphasis/', views.emphasis_line_search, name='emphasis_line_search'),
    path('emphasis/<int:pk>/search/', views.emphasis_course_search, name='emphasis_course_search'),

    # Guardar y cargar estado del roadmap
    path('roadmap/state/save/', views.save_roadmap_state, name='save_roadmap_state'),
    path('roadmap/state/load/', views.load_roadmap_state, name='load_roadmap_state'),
]