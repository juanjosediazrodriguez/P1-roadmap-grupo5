from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Interest, CareerGoal, Preference, UserProfile
from roadmap.models import Specialization, EmphasisLine, Track
from roadmap.views import (
    get_specialization_suggestions,
    get_track_suggestions,
    get_emphasis_suggestions,
)


def get_or_create_user_preference(user):
    preference, _ = Preference.objects.get_or_create(user=user)
    return preference


def login_view(request):
    if request.user.is_authenticated:
        return redirect('roadmap')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'roadmap')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('roadmap')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.username}! Tu cuenta fue creada exitosamente.')
            return redirect('preferences')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def preferences_view(request):
    interests = Interest.objects.all()
    goals = CareerGoal.objects.all()

    preference = get_or_create_user_preference(request.user)

    selected_interests = [str(i.id) for i in preference.interests.all()]
    selected_goal = str(preference.career_goal.id) if preference.career_goal else None

    has_active_preferences = bool(selected_interests or selected_goal)

    specialization_suggestion = None
    emphasis_suggestion = None
    track_suggestion = None

    if has_active_preferences:
        specialization_suggestions = get_specialization_suggestions(preference)
        emphasis_suggestions = get_emphasis_suggestions(preference)
        track_suggestions = get_track_suggestions(preference)

        specialization_suggestion = specialization_suggestions[0] if specialization_suggestions else None
        emphasis_suggestion = emphasis_suggestions[0] if emphasis_suggestions else None
        track_suggestion = track_suggestions[0] if track_suggestions else None

        # Fallbacks para garantizar una recomendación por tipo cuando sí hay preferencias activas.
        if not specialization_suggestion:
            fallback_spec = Specialization.objects.order_by('name').first()
            if fallback_spec:
                specialization_suggestion = {
                    'specialization': fallback_spec,
                    'score': 1,
                    'reasons': ['Recomendación base por disponibilidad de especialización'],
                }

        if not emphasis_suggestion:
            fallback_emphasis = EmphasisLine.objects.order_by('name').first()
            if fallback_emphasis:
                emphasis_suggestion = {
                    'emphasis': fallback_emphasis,
                    'score': 1,
                    'reasons': ['Recomendación base por disponibilidad de línea de énfasis'],
                }

        if not track_suggestion:
            fallback_track = Track.objects.filter(track_type='PROFESSIONAL').order_by('name').first()
            if fallback_track:
                track_suggestion = {
                    'track': fallback_track,
                    'score': 1,
                    'reasons': ['Recomendación base por disponibilidad de trayectoria profesionalizante'],
                }

    context = {
        'interests': interests,
        'goals': goals,
        'preference': preference,
        'selected_interests': selected_interests,
        'selected_goal': selected_goal,
        'specialization_suggestion': specialization_suggestion,
        'emphasis_suggestion': emphasis_suggestion,
        'track_suggestion': track_suggestion,
    }

    return render(request, 'preferences.html', context)


@login_required
def save_preferences(request):
    if request.method == 'POST':
        selected_interests = request.POST.getlist('interests')
        selected_goal = request.POST.get('career_goal')

        if not (selected_interests or selected_goal):
            messages.warning(request, 'Por favor selecciona al menos una preferencia')
            return redirect('preferences')

        preference = get_or_create_user_preference(request.user)

        if selected_interests:
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

def delete_preferences(request):
    if request.method == 'POST':
        preference = get_or_create_user_preference(request.user)
        preference.interests.clear()
        preference.career_goal = None
        preference.save()
        messages.success(request, 'Preferencias eliminadas exitosamente')
    return redirect('preferences')
