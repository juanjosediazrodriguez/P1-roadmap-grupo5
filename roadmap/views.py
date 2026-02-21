from django.shortcuts import render, get_object_or_404
from .models import Specialization
from collections import defaultdict
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import IntegerField, Value

from django.http import JsonResponse
from django.template.loader import render_to_string

def specialization_list(request):
    query = request.GET.get('q', '')
    specializations = Specialization.objects.filter(name__icontains=query)
    return render(request, 'roadmap/home.html', {
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
