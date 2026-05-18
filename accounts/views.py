from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Interest, CareerGoal, Preference, UserProfile
from roadmap.models import Specialization, EmphasisLine, Track, RoadmapState
from roadmap.views import (
    get_specialization_suggestions,
    get_track_suggestions,
    get_emphasis_suggestions,
)
from django.conf import settings
from google import genai
import json  # Lo usaremos para procesar la respuesta estructurada de la IA

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
    return redirect('logout_success')

def logout_success_view(request):
    return render(request, 'logout_success.html')

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
        # --- INICIO DE LA LÓGICA CON IA ---
        
        # 1. Recuperamos los datos del usuario
        intereses_usuario = ", ".join([i.name for i in preference.interests.all()])
        meta_usuario = preference.career_goal.name if preference.career_goal else "No definida"
        
        # 2. OBTENEMOS LAS OPCIONES REALES QUE EXISTEN EN LA BASE DE DATOS
        opciones_especializaciones = ", ".join([s.name for s in Specialization.objects.all()])
        opciones_enfasis = ", ".join([e.name for e in EmphasisLine.objects.all()])
        opciones_tracks = ", ".join([t.name for t in Track.objects.filter(track_type='PROFESSIONAL')])
        
        # 3. Diseñamos el Prompt dándole las opciones reales como opciones obligatorias
        prompt = f"""
        Eres un asesor académico experto de la universidad EAFIT para la carrera de Ingeniería de Sistemas.
        
        El estudiante tiene las siguientes preferencias:
        - Intereses tecnológicos: {intereses_usuario}
        - Meta profesional/Objetivo de carrera: {meta_usuario}
        
        Tu tarea es seleccionar la mejor opción para el estudiante basándote estrictamente en las listas de opciones reales que existen en la universidad. 
        No puedes inventar nombres. Debes elegir uno de los nombres exactos que te proporciono a continuación:

        OPCIONES REALES DISPONIBLES:
        - Especializaciones disponibles (Elige una de estas): [{opciones_especializaciones}]
        - Líneas de Énfasis disponibles (Elige una de estas): [{opciones_enfasis}]
        - Trayectorias (Tracks) disponibles (Elige una de estas): [{opciones_tracks}]
        
        Debes responder ÚNICAMENTE con un objeto JSON válido, con la siguiente estructura:
        {{
            "specialization": {{"name": "Nombre exacto elegido de la lista", "reasons": ["Razón 1", "Razón 2"]}},
            "emphasis": {{"name": "Nombre exacto elegido de la lista", "reasons": ["Razón 1", "Razón 2"]}},
            "track": {{"name": "Nombre exacto elegido de la lista", "reasons": ["Razón 1", "Razón 2"]}}
        }}
        """
        
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            config = {
                "response_mime_type": "application/json"
            }
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=config 
            )
            
            data_ia = json.loads(response.text.strip())
            
            # 4. Buscamos en la base de datos usando el nombre EXACTO que eligió la IA
            nombre_spec = data_ia['specialization']['name'].strip()
            obj_spec = Specialization.objects.filter(name__iexact=nombre_spec).first() or Specialization.objects.first()
            
            nombre_emphasis = data_ia['emphasis']['name'].strip()
            obj_emphasis = EmphasisLine.objects.filter(name__iexact=nombre_emphasis).first() or EmphasisLine.objects.first()
            
            nombre_track = data_ia['track']['name'].strip()
            obj_track = Track.objects.filter(name__iexact=nombre_track).first() or Track.objects.filter(track_type='PROFESSIONAL').first()

            # 5. Armamos el contexto para el HTML
            specialization_suggestion = {
                'specialization': obj_spec,
                'score': 100,
                'reasons': data_ia['specialization']['reasons']
            }
            emphasis_suggestion = {
                'emphasis': obj_emphasis,
                'score': 100,
                'reasons': data_ia['emphasis']['reasons']
            }
            track_suggestion = {
                'track': obj_track,
                'score': 100,
                'reasons': data_ia['track']['reasons']
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            if not specialization_suggestion:
                fallback_spec = Specialization.objects.order_by('name').first()
                if fallback_spec:
                    specialization_suggestion = {
                        'specialization': fallback_spec,
                        'score': 1,
                        'reasons': ['Recomendación base por disponibilidad (Fallback debido a error de IA)'],
                    }

            if not emphasis_suggestion:
                fallback_emphasis = EmphasisLine.objects.order_by('name').first()
                if fallback_emphasis:
                    emphasis_suggestion = {
                        'emphasis': fallback_emphasis,
                        'score': 1,
                        'reasons': ['Recomendación base por disponibilidad (Fallback debido a error de IA)'],
                    }

            if not track_suggestion:
                fallback_track = Track.objects.filter(track_type='PROFESSIONAL').order_by('name').first()
                if fallback_track:
                    track_suggestion = {
                        'track': fallback_track,
                        'score': 1,
                        'reasons': ['Recomendación base por disponibilidad (Fallback debido a error de IA)'],
                    }
        # --- FIN DE LA LÓGICA CON IA ---

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

@login_required
def profile_view(request):
    """Vista para mostrar y actualizar datos basicos del perfil del estudiante."""
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_preference = get_or_create_user_preference(request.user)

    # Obtener máximo semestre del roadmap del usuario
    max_roadmap_semester = 9  # fallback
    try:
        roadmap_state = RoadmapState.objects.get(user=request.user)
        semester_keys = [int(k) for k in roadmap_state.state.get('semester_map', {}).keys()]
        if semester_keys:
            max_roadmap_semester = max(semester_keys)
    except RoadmapState.DoesNotExist:
        pass

    if request.method == 'POST':
        english_level = request.POST.get('english_level', 'NONE')
        institutional_email = (request.POST.get('institutional_email') or '').strip()
        current_semester_raw = (request.POST.get('current_semester') or '').strip()

        if institutional_email and not institutional_email.lower().endswith('@eafit.edu.co'):
            messages.error(request, 'El correo institucional debe terminar en @eafit.edu.co')
            return redirect('profile')

        try:
            current_semester = int(current_semester_raw)
        except ValueError:
            messages.error(request, 'El semestre debe ser un numero entero.')
            return redirect('profile')

        if current_semester < 1:
            messages.error(request, 'El semestre debe ser un numero entero mayor o igual a 1.')
            return redirect('profile')

        # Si supera el máximo del roadmap, se ajusta silenciosamente al máximo
        if current_semester > max_roadmap_semester:
            current_semester = max_roadmap_semester

        user_profile.institutional_email = institutional_email or None
        user_profile.current_semester = current_semester
        user_profile.english_level = english_level
        user_profile.save()

        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('profile')

    context = {
        'user_profile': user_profile,
        'user_preference': user_preference,
        'max_roadmap_semester': max_roadmap_semester,
    }

    return render(request, 'profile.html', context)