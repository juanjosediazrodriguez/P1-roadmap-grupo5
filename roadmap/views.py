from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Specialization, Course, Track, EmphasisLine, CourseSpecialization
from accounts.models import Preference
from collections import defaultdict
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import IntegerField, Value, Q
from .models import UmbrellaCourseOption

from django.http import JsonResponse
from django.template.loader import render_to_string

# Mapeo de intereses a nombres de especializaciones en la BD
INTEREST_SPECIALIZATION_MAP = {
    "Desarrollo de Software": ["Desarrollo de Software"],
    "Ciencia de Datos":       ["Data Science", "Data Analytics", "Data Engineer"],
    "Inteligencia Artificial":["Inteligencia Artificial"],
    "Ciberseguridad":         ["Ciberseguridad"],
    "Computación en la Nube": ["Desarrollo de Software"],
    "Gestión de Proyectos":   ["Desarrollo de Software", "Sistemas de Información"],
    "Investigación":          ["Data Science", "Inteligencia Artificial"],
    "Emprendimiento":         ["Desarrollo de Software", "Sistemas de Información"],
}

def get_base_courses():
    """
    Retorna los cursos base de la carrera:
    - Incluye cursos paraguas (is_umbrella=True)
    - Excluye cursos que son opciones de paraguas (los que aparecen en UmbrellaCourseOption)
    """
    
    # IDs de cursos que son opciones de algún paraguas
    option_ids = set(UmbrellaCourseOption.objects.values_list('option_course_id', flat=True))
    
    # Obtener todos los cursos base
    courses = Course.objects.filter(
        category__in=['BASIC_SCIENCE', 'BASIC_ENGINEERING', 'NFI', 'DISCIPLINARY', 
                      'PROFESSIONAL_TRACK', 'FLEXIBLE_TRACK', 'PRACTICE', 'EMPHASIS']
    )
    
    # Filtrar en Python para excluir opciones
    filtered_courses = [c for c in courses if c.id not in option_ids]
    
    # Ordenar manualmente por semestre y código
    filtered_courses.sort(key=lambda c: (c.semester_suggested, c.code))
    
    return filtered_courses


def get_specialization_courses(preference):
    """Retorna cursos de especializaciones según las preferencias del usuario"""
    if not preference:
        return []

    # Determinar qué especializaciones aplican según los intereses
    target_specializations = set()
    for interest in preference.interests.all():
        for spec_name in INTEREST_SPECIALIZATION_MAP.get(interest.name, []):
            target_specializations.add(spec_name)

    # Si no hay intereses, mostrar todas las especializaciones
    if not target_specializations:
        specs = Specialization.objects.all()
    else:
        specs = Specialization.objects.filter(name__in=target_specializations)

    # Obtener cursos de esas especializaciones
    courses = list(Course.objects.filter(
        specializations__in=specs,
        category='SPECIALIZATION'
    ).distinct())
    
    # Ordenar manualmente
    courses.sort(key=lambda c: (c.semester_suggested, c.code))
    
    return courses


def generate_roadmap(preference):
    """
    Genera roadmap combinando:
    - Cursos base de la carrera (semestres 1-8)
    - Cursos de especialización según preferencias (semestres 9-10)
    """
    
    # Definir el orden de prioridad de categorías
    category_order = {
        'BASIC_SCIENCE': 1,
        'BASIC_ENGINEERING': 2,
        'DISCIPLINARY': 3,
        'PROFESSIONAL_TRACK': 4,
        'EMPHASIS': 5,
        'FLEXIBLE_TRACK': 6,
        'PRACTICE': 7,
        'NFI': 8,
        'SPECIALIZATION': 9,
    }
    
    # 1. Obtener cursos base (siempre se muestran)
    base_courses = list(get_base_courses())
    
    spec_courses = []
    
    # 2. Combinar todos los cursos
    all_courses = base_courses + spec_courses
    
    # 3. Ordenar todos los cursos
    all_courses.sort(key=lambda c: (c.semester_suggested, category_order.get(c.category, 99), c.code))
    
    # 4. Agrupar por semestre
    roadmap = defaultdict(list)
    for course in all_courses:
        roadmap[course.semester_suggested].append(course)
    
    # 5. Obtener TODOS los cursos que necesitan modal (recursivamente)
    def collect_all_courses(course_ids):
        """Recolecta recursivamente todos los cursos relacionados"""
        result = set(course_ids)
        # Obtener todas las opciones de los cursos actuales
        options = UmbrellaCourseOption.objects.filter(
            umbrella_course_id__in=course_ids
        ).select_related('option_course')
        
        new_ids = set()
        for opt in options:
            if opt.option_course_id not in result:
                new_ids.add(opt.option_course_id)
        
        if new_ids:
            result.update(collect_all_courses(new_ids))
        
        return result
    
    # Obtener IDs de todos los cursos en el roadmap
    current_ids = [c.id for c in all_courses]
    all_needed_ids = collect_all_courses(current_ids)
    
    # Obtener los objetos Course
    all_courses_for_modals = list(Course.objects.filter(id__in=all_needed_ids))
    
    # Devolver también las opciones
    return dict(sorted(roadmap.items())), all_courses_for_modals


@login_required
def roadmap_view(request):
    preference, _ = Preference.objects.get_or_create(user=request.user)
    roadmap_by_semester, all_options = generate_roadmap(preference)

    # Construir lista de semestres
    semesters = [
        {
            'number': sem,
            'courses': courses,
            'total_credits': sum(c.credits for c in courses),
        }
        for sem, courses in roadmap_by_semester.items()
        if courses
    ]

    return render(request, 'roadmap/roadmap.html', {
        'semesters': semesters,
        'preference': preference,
        'all_options': all_options,
    })

# ========== ESPECIALIZACIONES ==========

@login_required
def specialization_list(request):
    query = request.GET.get('q', '')
    specializations = Specialization.objects.filter(name__icontains=query)
    return render(request, 'roadmap/specializations/specializations.html', {
        'specializations': specializations,
        'query': query,
    })


@login_required
def specialization_detail(request, pk):
    specialization = get_object_or_404(Specialization, pk=pk)
    
    # Obtener cursos con su metadata de especialización
    course_specializations = CourseSpecialization.objects.filter(
        specialization=specialization
    ).select_related('course')
    
    # Agrupar por semestre dentro de la especialización
    semester_courses = defaultdict(list)
    for cs in course_specializations:
        semester_courses[cs.semester_in_specialization].append(cs.course)
    
    # Calcular créditos por semestre de especialización
    semester_credits = []
    for sem_num in sorted(semester_courses.keys()):
        courses = semester_courses[sem_num]
        total_credits = sum(c.credits for c in courses)
        semester_credits.append({
            'semester_number': sem_num,
            'courses': courses,
            'total': total_credits
        })
    
    # Para búsqueda
    courses_query = request.GET.get('q', '')
    all_courses = [cs.course for cs in course_specializations]
    
    if courses_query:
        all_courses = [c for c in all_courses if courses_query.lower() in c.name.lower() or courses_query.lower() in c.code.lower()]
    
    return render(request, 'roadmap/specializations/specialization_detail.html', {
        'specialization': specialization,
        'courses': all_courses,
        'query': courses_query,
        'semester_credits': semester_credits,  # Ahora con semestre 1,2
    })


def specialization_search(request):
    query = request.GET.get('q', '')

    if query:
        specializations = Specialization.objects.filter(name__icontains=query)
    else:
        specializations = Specialization.objects.all()

    html = render_to_string(
        'roadmap/partials/specialization_list.html',
        {'specializations': specializations}
    )

    return JsonResponse({'html': html})

def specialization_roadmap(request, pk):
    specialization = get_object_or_404(Specialization, pk=pk)
    semesters = generate_specialization_roadmap(specialization)
    return render(request, 'roadmap/specializations/specialization_roadmap.html', {
        'specialization': specialization,
        'semesters': semesters,
    })


def specialization_course_search(request, pk):
    query = request.GET.get('q', '')
    specialization = get_object_or_404(Specialization, pk=pk)

    if query:
        courses = specialization.courses.filter(name__icontains=query)
    else:
        courses = specialization.courses.all()

    html = render_to_string(
        'roadmap/partials/course_list.html',
        {'courses': courses}
    )

    return JsonResponse({'html': html})


MAX_CREDITS_PER_SEMESTER = 21
MAX_SEMESTERS = 9


def generate_specialization_roadmap(specialization):
    """
    Genera un roadmap para una especialización usando semester_in_specialization (1-2)
    """
    course_specializations = CourseSpecialization.objects.filter(
        specialization=specialization
    ).select_related('course')
    
    semester_credits = defaultdict(int)
    semester_courses = defaultdict(list)
    
    for cs in course_specializations:
        target = cs.semester_in_specialization  # Usamos el semestre de especialización
        semester_courses[target].append(cs.course)
        semester_credits[target] += cs.course.credits
    
    return [
        {
            'number': sem,
            'courses': semester_courses[sem],
            'total_credits': semester_credits[sem],
        }
        for sem in sorted(semester_courses.keys())
    ]

# ========== TRAYECTORIAS ==========

@login_required
def track_list(request):
    """Vista principal de trayectorias (redirige a profesionalizantes por defecto)"""
    return redirect('track_professional_list')


@login_required
def track_professional_list(request):
    """Lista de trayectorias profesionalizantes"""
    query = request.GET.get('q', '')
    tracks = Track.objects.filter(
        track_type='PROFESSIONAL',
        name__icontains=query
    )
    return render(request, 'roadmap/tracks/tracks.html', {
        'tracks': tracks,
        'query': query,
        'track_type': 'PROFESSIONAL',
    })


@login_required
def track_flexible_list(request):
    """Lista de trayectorias flexibles"""
    query = request.GET.get('q', '')
    tracks = Track.objects.filter(
        track_type='FLEXIBLE',
        name__icontains=query
    )
    return render(request, 'roadmap/tracks/tracks.html', {
        'tracks': tracks,
        'query': query,
        'track_type': 'FLEXIBLE',
    })


@login_required
def track_detail(request, pk):
    """Vista detallada de una trayectoria"""
    track = get_object_or_404(Track, pk=pk)
    
    # Obtener cursos de la trayectoria
    track_courses = track.track_courses.select_related('course').order_by('semester_in_track')
    courses = [tc.course for tc in track_courses]
    
    # Agrupar créditos por semestre
    semester_credits_qs = (
        Course.objects.filter(id__in=[c.id for c in courses])
        .values("semester_suggested")
        .annotate(total=Coalesce(Sum("credits"), Value(0), output_field=IntegerField()))
        .order_by("semester_suggested")
    )
    
    semester_credits = list(semester_credits_qs)
    
    return render(request, 'roadmap/tracks/track_detail.html', {
        'track': track,
        'courses': courses,
        'semester_credits': semester_credits,
    })


def track_roadmap(request, pk):
    """Genera el roadmap de una trayectoria"""
    track = get_object_or_404(Track, pk=pk)
    
    # Obtener cursos de la trayectoria
    track_courses = track.track_courses.select_related('course').order_by('semester_in_track')
    courses = [tc.course for tc in track_courses]
    
    # Generar semestres para el roadmap
    semesters = generate_track_roadmap(courses)
    
    return render(request, 'roadmap/tracks/track_roadmap.html', {
        'track': track,
        'semesters': semesters,
    })


def generate_track_roadmap(courses):
    """Genera semestres para el roadmap de una trayectoria"""
    # Ordenar cursos por semestre sugerido
    sorted_courses = sorted(courses, key=lambda c: c.semester_suggested)
    
    semester_credits = defaultdict(int)
    semester_courses = defaultdict(list)
    
    for course in sorted_courses:
        target = course.semester_suggested
        semester_courses[target].append(course)
        semester_credits[target] += course.credits
    
    return [
        {
            'number': sem,
            'courses': semester_courses[sem],
            'total_credits': semester_credits[sem],
        }
        for sem in sorted(semester_courses.keys())
    ]


def track_search(request):
    """Búsqueda AJAX para trayectorias"""
    query = request.GET.get('q', '')
    track_type = request.GET.get('type', 'PROFESSIONAL')
    
    if query:
        tracks = Track.objects.filter(
            track_type=track_type,
            name__icontains=query
        )
    else:
        tracks = Track.objects.filter(track_type=track_type)
    
    html = render_to_string(
        'roadmap/partials/track_list.html',
        {'tracks': tracks, 'track_type': track_type}
    )
    
    return JsonResponse({'html': html})

def track_course_search(request, pk):
    """Búsqueda de cursos dentro de una trayectoria"""
    query = request.GET.get('q', '')
    track = get_object_or_404(Track, pk=pk)
    
    track_courses = track.track_courses.select_related('course')
    if query:
        track_courses = track_courses.filter(course__name__icontains=query)
    
    courses = [tc.course for tc in track_courses]
    
    html = render_to_string(
        'roadmap/partials/course_list.html',
        {'courses': courses}
    )
    return JsonResponse({'html': html})

# ========== LÍNEAS DE ÉNFASIS ==========

@login_required
def emphasis_line_list(request):
    """Lista de todas las líneas de énfasis"""
    query = request.GET.get('q', '')
    emphasis_lines = EmphasisLine.objects.filter(name__icontains=query)
    
    return render(request, 'roadmap/emphasis/emphasis_lines.html', {
        'emphasis_lines': emphasis_lines,
        'query': query,
    })


@login_required
def emphasis_line_detail(request, pk):
    """Vista detallada de una línea de énfasis"""
    emphasis_line = get_object_or_404(EmphasisLine, pk=pk)
    
    # Buscar el curso paraguas asociado a esta línea de énfasis
    umbrella_course = Course.objects.filter(
        name__icontains='Línea de Énfasis',
        category='EMPHASIS',
        is_umbrella=True
    ).first()
    
    # Obtener los cursos específicos de la línea a través de EmphasisLineCourse
    line_courses = emphasis_line.line_courses.select_related('course').order_by('semester_in_line')
    courses = [lc.course for lc in line_courses]
    
    # Agrupar créditos por semestre sugerido
    semester_credits_qs = (
        Course.objects.filter(id__in=[c.id for c in courses])
        .values("semester_suggested")
        .annotate(total=Coalesce(Sum("credits"), Value(0), output_field=IntegerField()))
        .order_by("semester_suggested")
    )
    
    semester_credits = list(semester_credits_qs)
    
    return render(request, 'roadmap/emphasis/emphasis_line_detail.html', {
        'emphasis_line': emphasis_line,
        'courses': courses,
        'semester_credits': semester_credits,
        'umbrella_course': umbrella_course,  # Pasar el curso paraguas para el modal
    })


def emphasis_line_search(request):
    """Búsqueda AJAX para líneas de énfasis"""
    query = request.GET.get('q', '')
    
    if query:
        emphasis_lines = EmphasisLine.objects.filter(name__icontains=query)
    else:
        emphasis_lines = EmphasisLine.objects.all()
    
    html = render_to_string(
        'roadmap/partials/emphasis_line_list.html',
        {'emphasis_lines': emphasis_lines}
    )
    
    return JsonResponse({'html': html})


def emphasis_course_search(request, pk):
    """Búsqueda de cursos dentro de una línea de énfasis"""
    query = request.GET.get('q', '')
    emphasis_line = get_object_or_404(EmphasisLine, pk=pk)
    
    line_courses = emphasis_line.line_courses.select_related('course')
    if query:
        line_courses = line_courses.filter(course__name__icontains=query)
    
    courses = [lc.course for lc in line_courses]
    
    html = render_to_string(
        'roadmap/partials/course_list.html',
        {'courses': courses}
    )
    return JsonResponse({'html': html})

# ========== NORMALIZACIÓN DE TEXTO ==========

def normalize_text(text):
    if not text:
        return ""
    import unicodedata
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    return text

# ========== SISTEMA DE RECOMENDACIONES ==========

def get_specialization_suggestions(preference):
    if not preference:
        return []

    # Usar los nombres reales de las especializaciones en la BD
    scores = {
        "desarrollo de software": {"score": 0, "reasons": []},
        "sistemas de informacion": {"score": 0, "reasons": []},
        "inteligencia artificial": {"score": 0, "reasons": []},
        "ciberseguridad": {"score": 0, "reasons": []},
    }

    # Reglas por áreas de interés
    interest_rules = {
        "ciberseguridad": {
            "ciberseguridad": 5,
        },
        "ciencia de datos": {
            "inteligencia artificial": 4,
            "sistemas de informacion": 3,
        },
        "computacion en la nube": {
            "desarrollo de software": 4,
            "sistemas de informacion": 3,
            "ciberseguridad": 3,
        },
        "desarrollo de software": {
            "desarrollo de software": 5,
            "sistemas de informacion": 3,
        },
        "emprendimiento": {
            "desarrollo de software": 4,
            "sistemas de informacion": 3,
        },
        "gestion de proyectos": {
            "sistemas de informacion": 4,
            "desarrollo de software": 3,
        },
        "inteligencia artificial": {
            "inteligencia artificial": 5,
            "desarrollo de software": 2,
        },
        "investigacion": {
            "inteligencia artificial": 4,
            "ciencia de datos": 3,
            "sistemas de informacion": 2,
        },
    }

    # Reglas por meta profesional
    goal_rules = {
        "freelance": {
            "desarrollo de software": 4,
            "ciberseguridad": 2,
        },
        "industria": {
            "desarrollo de software": 4,
            "sistemas de informacion": 4,
            "inteligencia artificial": 3,
            "ciberseguridad": 3,
        },
        "investigacion": {
            "inteligencia artificial": 5,
            "sistemas de informacion": 2,
        },
        "posgrado": {
            "inteligencia artificial": 5,
            "desarrollo de software": 2,
            "sistemas de informacion": 2,
        },
        "startup": {
            "desarrollo de software": 5,
            "sistemas de informacion": 3,
        },
    }

    # Aplicar intereses
    for interest in preference.interests.all():
        interest_name = normalize_text(interest.name)
        if interest_name in interest_rules:
            for spec_name, points in interest_rules[interest_name].items():
                if spec_name in scores:
                    scores[spec_name]["score"] += points
                    scores[spec_name]["reasons"].append(
                        f"Coincide con tu interés en {interest.name}"
                    )

    # Aplicar meta profesional
    if preference.career_goal:
        goal_name = normalize_text(preference.career_goal.name)
        if goal_name in goal_rules:
            for spec_name, points in goal_rules[goal_name].items():
                if spec_name in scores:
                    scores[spec_name]["score"] += points
                    scores[spec_name]["reasons"].append(
                        f"Se alinea con tu meta profesional: {preference.career_goal.name}"
                    )

    suggestions = []

    for specialization in Specialization.objects.all():
        spec_name = normalize_text(specialization.name)

        if spec_name in scores and scores[spec_name]["score"] > 0:
            suggestions.append({
                "specialization": specialization,
                "score": scores[spec_name]["score"],
                "reasons": list(dict.fromkeys(scores[spec_name]["reasons"])),
            })

    suggestions.sort(key=lambda item: item["score"], reverse=True)
    return suggestions