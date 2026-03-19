from django.shortcuts import render, get_object_or_404
from .models import Specialization
from collections import defaultdict
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import IntegerField, Value

from django.http import JsonResponse
from django.template.loader import render_to_string

import unicodedata

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

import unicodedata

def normalize_text(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    return text


def get_specialization_suggestions(preference):
    if not preference:
        return []

    scores = {
        "ciberseguridad": {"score": 0, "reasons": []},
        "data analytics": {"score": 0, "reasons": []},
        "data engineer": {"score": 0, "reasons": []},
        "data science": {"score": 0, "reasons": []},
        "desarrollo de software": {"score": 0, "reasons": []},
        "machine learning": {"score": 0, "reasons": []},
    }

    # Reglas por áreas de interés
    interest_rules = {
        "ciberseguridad": {
            "ciberseguridad": 5,
        },
        "ciencia de datos": {
            "data analytics": 5,
            "data engineer": 4,
            "data science": 5,
            "machine learning": 4,
        },
        "computacion en la nube": {
            "data engineer": 5,
            "ciberseguridad": 3,
        },
        "desarrollo de software": {
            "desarrollo de software": 5,
            "data engineer": 3,
        },
        "emprendimiento": {
            "desarrollo de software": 3,
            "data analytics": 2,
        },
        "gestion de proyectos": {
            "desarrollo de software": 3,
            "data analytics": 2,
            "data engineer": 2,
        },
        "inteligencia artificial": {
            "machine learning": 5,
            "data science": 4,
        },
        "investigacion": {
            "data science": 4,
            "machine learning": 4,
            "data analytics": 2,
        },
    }

    # Reglas por tecnologías
    tech_rules = {
        "aws": {
            "data engineer": 4,
            "ciberseguridad": 3,
        },
        "c++": {
            "desarrollo de software": 3,
            "machine learning": 1,
        },
        "docker": {
            "data engineer": 3,
            "ciberseguridad": 2,
            "desarrollo de software": 2,
        },
        "java": {
            "desarrollo de software": 4,
            "data engineer": 2,
        },
        "javascript": {
            "desarrollo de software": 5,
        },
        "kubernetes": {
            "data engineer": 4,
            "ciberseguridad": 2,
        },
        "python": {
            "data science": 4,
            "machine learning": 5,
            "data analytics": 3,
            "data engineer": 2,
            "ciberseguridad": 1,
            "desarrollo de software": 2,
        },
        "react": {
            "desarrollo de software": 5,
        },
        "sql": {
            "data analytics": 5,
            "data science": 3,
            "data engineer": 4,
        },
        "tensorflow": {
            "machine learning": 5,
            "data science": 4,
        },
    }

    # Reglas por meta profesional
    goal_rules = {
        "freelance": {
            "desarrollo de software": 4,
            "data analytics": 2,
            "ciberseguridad": 2,
        },
        "industria": {
            "data engineer": 4,
            "desarrollo de software": 4,
            "data analytics": 3,
            "ciberseguridad": 3,
            "data science": 3,
        },
        "investigacion": {
            "data science": 4,
            "machine learning": 5,
        },
        "posgrado": {
            "data science": 4,
            "machine learning": 5,
        },
        "startup": {
            "desarrollo de software": 4,
            "data engineer": 3,
            "data analytics": 2,
        },
    }

    # Aplicar intereses
    for interest in preference.interests.all():
        interest_name = normalize_text(interest.name)
        if interest_name in interest_rules:
            for spec_name, points in interest_rules[interest_name].items():
                scores[spec_name]["score"] += points
                scores[spec_name]["reasons"].append(
                    f"Coincide con tu interés en {interest.name}"
                )

    # Aplicar tecnologías
    for tech in preference.technologies.all():
        tech_name = normalize_text(tech.name)
        if tech_name in tech_rules:
            for spec_name, points in tech_rules[tech_name].items():
                scores[spec_name]["score"] += points
                scores[spec_name]["reasons"].append(
                    f"Se relaciona con tu tecnología preferida: {tech.name}"
                )

    # Aplicar meta profesional
    if preference.career_goal:
        goal_name = normalize_text(preference.career_goal.name)
        if goal_name in goal_rules:
            for spec_name, points in goal_rules[goal_name].items():
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