from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Interest, CareerGoal, Preference
from roadmap.views import get_specialization_suggestions

def get_or_create_global_preference():
    """Obtiene o crea la única preferencia global"""
    preferences = Preference.objects.all()
    if preferences.exists():
        return preferences.first()
    else:
        return Preference.objects.create()

def preferences_view(request):
    interests = Interest.objects.all()
    goals = CareerGoal.objects.all()
    
    # Obtener la preferencia global (única)
    preference = get_or_create_global_preference()
    
    # Obtener IDs seleccionados para marcar en el formulario
    selected_interests = [str(i.id) for i in preference.interests.all()]
    selected_goal = str(preference.career_goal.id) if preference.career_goal else None
    
    suggestions = get_specialization_suggestions(preference)
    
    context = {
        'interests': interests,
        'goals': goals,
        'preference': preference,
        'selected_interests': selected_interests,
        'selected_goal': selected_goal,
        'suggestions': suggestions,
    }
    
    return render(request, 'preferences.html', context)


def save_preferences(request):
    if request.method == 'POST':
        selected_interests = request.POST.getlist('interests')
        selected_goal = request.POST.get('career_goal')
        
        # Validar que haya al menos una selección
        if not (selected_interests or selected_goal):
            messages.warning(request, 'Por favor selecciona al menos una preferencia')
            return redirect('preferences')
        
        # Obtener la preferencia global (única)
        preference = get_or_create_global_preference()
        
        # Convertir strings a integers para set()
        if selected_interests:
            # Convertir a integers
            interest_ids = [int(id) for id in selected_interests if id]
            preference.interests.set(interest_ids)
        else:
            preference.interests.clear()
        
        if selected_goal:
            preference.career_goal_id = int(selected_goal)
        else:
            preference.career_goal = None
        
        preference.save()
        
        messages.success(request, 'Preferencias guardadas exitosamente')
        return redirect('preferences')
    
    return redirect('preferences')