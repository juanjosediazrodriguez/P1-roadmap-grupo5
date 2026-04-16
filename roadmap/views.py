from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Specialization, Course, Track, EmphasisLine, CourseSpecialization, TrackCourse, EmphasisLineCourse
from accounts.models import Preference
from collections import defaultdict
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import IntegerField, Value, Q
from .models import UmbrellaCourseOption
from django.http import JsonResponse
from django.template.loader import render_to_string
import json as _json

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

def _course_to_dict(course):
    return {
        'id':                 course.id,
        'code':               course.code or '',
        'name':               course.name,
        'credits':            course.credits,
        'category':           course.category,
        'semester_suggested': course.semester_suggested,
        'language':           course.language or '',
        'description':        course.description,
        'is_umbrella':        course.is_umbrella,
        'prerequisites': [
            {'id': p.id, 'code': p.code or '', 'name': p.name}
            for p in course.prerequisites.all()
        ],
        'corequisites': [
            {'id': c.id, 'code': c.code or '', 'name': c.name}
            for c in course.corequisites.all()
        ],
        'available_options': [
            {'id': o.id, 'code': o.code or '', 'name': o.name,
             'credits': o.credits, 'category': o.category,
             'is_umbrella': o.is_umbrella}
            for o in course.available_options.all()
        ],
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

    semesters = [
        {
            'number': sem,
            'courses': courses,
            'total_credits': sum(c.credits for c in courses),
        }
        for sem, courses in roadmap_by_semester.items()
        if courses
    ]

    # ── course_map: id -> dict con prereqs/coreqs (para el JS) ──────────────
    all_course_ids = set()
    for sem_data in semesters:
        for c in sem_data['courses']:
            all_course_ids.add(c.id)
    all_course_ids.update(c.id for c in all_options)

    courses_qs = Course.objects.filter(id__in=all_course_ids).prefetch_related(
        'prerequisites', 'corequisites', 'available_options'
    )
    course_map = {str(c.id): _course_to_dict(c) for c in courses_qs}

    # ── semester_map: semNum -> [courseId, ...] ──────────────────────────────
    semester_map = {}
    for sem_data in semesters:
        semester_map[str(sem_data['number'])] = [c.id for c in sem_data['courses']]

    # ── Datos de trayectorias profesionalizantes ─────────────────────────────
    # Mapa: umbrella_course_pk (182-186) -> Track model pk (1-5)
    PROF_UMBRELLA_TO_TRACK_ID = {182: 1, 183: 2, 184: 3, 185: 4, 186: 5}
    tracks_data = {}
    for umbrella_pk, track_id in PROF_UMBRELLA_TO_TRACK_ID.items():
        try:
            track = Track.objects.get(pk=track_id)
        except Track.DoesNotExist:
            continue
        track_course_qs = TrackCourse.objects.filter(track=track).select_related(
            'course'
        ).prefetch_related('course__prerequisites', 'course__corequisites')

        courses_sem6, courses_sem7 = [], []
        for tc in track_course_qs:
            cd = _course_to_dict(tc.course)
            course_map[str(tc.course.id)] = cd
            if tc.semester_in_track == 1:
                courses_sem6.append(cd)
            else:
                courses_sem7.append(cd)

        tracks_data[str(umbrella_pk)] = {
            'track_id':     track_id,
            'name':         track.name,
            'courses_sem6': courses_sem6,
            'courses_sem7': courses_sem7,
        }

    # ── Datos de líneas de énfasis ───────────────────────────────────────────
    emphasis_data = {}
    for line in EmphasisLine.objects.prefetch_related(
        'line_courses__course__prerequisites',
        'line_courses__course__corequisites',
    ):
        line_courses = []
        for lc in line.line_courses.select_related('course').order_by('semester_in_line'):
            cd = _course_to_dict(lc.course)
            course_map[str(lc.course.id)] = cd
            line_courses.append({**cd, 'semester_in_line': lc.semester_in_line})
        emphasis_data[str(line.pk)] = {'name': line.name, 'courses': line_courses}

    # ── Opciones de NFI y Electivas de Matemáticas ───────────────────────────
    nfi_electiva_pks = [23, 24, 25, 26, 32]
    umbrella_options_data = {}
    for umb_pk in nfi_electiva_pks:
        opts = UmbrellaCourseOption.objects.filter(
            umbrella_course_id=umb_pk
        ).select_related('option_course').prefetch_related(
            'option_course__prerequisites', 'option_course__corequisites'
        )
        opt_list = []
        for o in opts:
            cd = _course_to_dict(o.option_course)
            course_map[str(o.option_course.id)] = cd
            opt_list.append(cd)
        umbrella_options_data[str(umb_pk)] = opt_list

    # ── Opciones de TRACK-PROF1 (207) y TRACK-PROF2 (208) ───────────────────
    prof_umbrella_options = {}
    for prof_pk in [207, 208]:
        opts = UmbrellaCourseOption.objects.filter(
            umbrella_course_id=prof_pk
        ).select_related('option_course')
        prof_umbrella_options[str(prof_pk)] = [
            {'id': o.option_course.id, 'code': o.option_course.code or '',
             'name': o.option_course.name, 'credits': o.option_course.credits}
            for o in opts
        ]

    # ── Opciones de EMPHASIS-LINE (211) ─────────────────────────────────────
    emphasis_umbrella_options = {}
    opts_211 = UmbrellaCourseOption.objects.filter(
        umbrella_course_id=211
    ).select_related('option_course')
    emphasis_umbrella_options['211'] = [
        {'id': o.option_course.id, 'code': o.option_course.code or '',
         'name': o.option_course.name, 'credits': o.option_course.credits}
        for o in opts_211
    ]

    # ── Mapa: umbrella_pk del énfasis-collector -> EmphasisLine pk ───────────
    # DATA-SCI (214) tiene como opciones los cursos 56-61 que pertenecen
    # a la EmphasisLine pk=1. Este mapa conecta ambos.
    emphasis_umbrella_to_line = {}
    for line in EmphasisLine.objects.all():
        line_course_ids = set(
            EmphasisLineCourse.objects.filter(
                emphasis_line=line
            ).values_list('course_id', flat=True)
        )
        for umb_pk_val in UmbrellaCourseOption.objects.values_list(
            'umbrella_course_id', flat=True
        ).distinct():
            umb_option_ids = set(
                UmbrellaCourseOption.objects.filter(
                    umbrella_course_id=umb_pk_val
                ).values_list('option_course_id', flat=True)
            )
            if line_course_ids and line_course_ids == umb_option_ids:
                emphasis_umbrella_to_line[str(umb_pk_val)] = line.pk
                break

    # ── JSON para el motor JS ────────────────────────────────────────────────
    roadmap_json = _json.dumps({
        'semester_map':              semester_map,
        'course_map':                course_map,
        'tracks':                    tracks_data,
        'emphasis_lines':            emphasis_data,
        'umbrella_options':          umbrella_options_data,
        'prof_umbrella_options':     prof_umbrella_options,
        'emphasis_umbrella_options': emphasis_umbrella_options,
        'emphasis_umbrella_to_line': emphasis_umbrella_to_line,
        'prof_slots':                {'slot1': 207, 'slot2': 208},
        'flex_umbrella_pks':         [209, 210, 212, 213],
        'emphasis_line_umbrella_pk': 211,
        'nfi_umbrella_pks':          [23, 24, 25],
        'electiva_mat_umbrella_pks': [26, 32],
    }, ensure_ascii=False)

    return render(request, 'roadmap/roadmap.html', {
        'semesters':    semesters,
        'preference':   preference,
        'all_options':  all_options,
        'roadmap_json': roadmap_json,
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