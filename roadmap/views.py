from django.shortcuts import render, get_object_or_404
from .models import Specialization, Course
from collections import defaultdict
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import IntegerField, Value

from django.http import JsonResponse
from django.template.loader import render_to_string
from accounts.models import Preference

# Mapeo de intereses a nombres de especializaciones en la BD
INTEREST_SPECIALIZATION_MAP = {
    "Desarrollo de Software": ["Desarrollo de software"],
    "Ciencia de Datos":       ["Data Science", "Data Analytics", "Data Engineer"],
    "Inteligencia Artificial":["Machine Learning"],
    "Ciberseguridad":         ["Ciberseguridad"],
    "Computación en la Nube": ["Desarrollo de software"],
    "Gestión de Proyectos":   ["Desarrollo de software"],
    "Investigación":          ["Data Science", "Machine Learning"],
    "Emprendimiento":         ["Desarrollo de software"],
}

def generate_roadmap(preference):
    """
    Agente algorítmico: recibe las preferencias del usuario y devuelve
    un dict {semestre: [cursos]} ordenado por semestre sugerido.
    """
    if not preference:
        return {}

    # 1. Determinar qué especializaciones aplican según los intereses
    target_specializations = set()
    for interest in preference.interests.all():
        for spec_name in INTEREST_SPECIALIZATION_MAP.get(interest.name, []):
            target_specializations.add(spec_name)

    # Si no hay intereses, mostrar todas las especializaciones
    if not target_specializations:
        specs = Specialization.objects.all()
    else:
        specs = Specialization.objects.filter(name__in=target_specializations)

    # 2. Obtener cursos de esas especializaciones sin duplicados
    courses = (
        Course.objects.filter(specializations__in=specs)
        .distinct()
        .prefetch_related('prerequisites')
        .order_by('semester_suggested', 'code')
    )

    # 3. Agrupar por semestre
    roadmap = defaultdict(list)
    for course in courses:
        roadmap[course.semester_suggested].append(course)

    return dict(sorted(roadmap.items()))

def specialization_list(request):
    query = request.GET.get('q', '')
    specializations = Specialization.objects.filter(name__icontains=query)
    return render(request, 'roadmap/specializations.html', {
        'specializations': specializations,
        'query': query,
    })


def specialization_detail(request, pk):
    specialization = get_object_or_404(Specialization, pk=pk)
    courses = specialization.courses.all()
    courses_query = request.GET.get('q', '')
    courses = courses.filter(name__icontains=courses_query)
     # Agrupar y sumar créditos por semestre sugerido
    semester_credits_qs = (
        courses.values("semester_suggested")
        .annotate(total=Coalesce(Sum("credits"), Value(0), output_field=IntegerField()))
        .order_by("semester_suggested")
    )

    # Convertir a lista de dicts para el template
    semester_credits = list(semester_credits_qs)
    return render(request, 'roadmap/courses.html', {
        'specialization': specialization,
        'courses': courses,
        'query': courses_query,
        'semester_credits': semester_credits,
    })

# Vista para búsqueda de especializaciones vía AJAX
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

MAX_CREDITS_PER_SEMESTER = 21
MAX_SEMESTERS = 9

def generate_specialization_roadmap(specialization):
    """
    Genera un roadmap para una especialización respetando:
    - El semestre sugerido de cada curso como punto de partida
    - Máximo 21 créditos por semestre
    - Máximo 9 semestres
    """
    courses = (
        specialization.courses
        .prefetch_related('prerequisites')
        .order_by('semester_suggested', 'code')
    )

    semester_credits = defaultdict(int)
    semester_courses = defaultdict(list)

    for course in courses:
        target = course.semester_suggested
        # Si el semestre está lleno, pasar al siguiente hasta que quepa
        while (
            semester_credits[target] + course.credits > MAX_CREDITS_PER_SEMESTER
            and target <= MAX_SEMESTERS
        ):
            target += 1
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


def specialization_roadmap(request, pk):
    specialization = get_object_or_404(Specialization, pk=pk)
    semesters = generate_specialization_roadmap(specialization)
    return render(request, 'roadmap/specialization_roadmap.html', {
        'specialization': specialization,
        'semesters': semesters,
    })


def roadmap_view(request):
    preference = Preference.objects.first()
    roadmap_by_semester = generate_roadmap(preference)

    # Construir lista de semestres con sus cursos y total de créditos
    semesters = [
        {
            'number': sem,
            'courses': courses,
            'total_credits': sum(c.credits for c in courses),
        }
        for sem, courses in roadmap_by_semester.items()
    ]

    return render(request, 'roadmap/roadmap.html', {
        'semesters': semesters,
        'preference': preference,
    })


# Vista para búsqueda de cursos vía AJAX
def course_search(request, pk):
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
