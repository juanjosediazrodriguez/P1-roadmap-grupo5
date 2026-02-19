from django.shortcuts import render, get_object_or_404
from .models import Specialization

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
    return render(request, 'roadmap/courses.html', {
        'specialization': specialization,
        'courses': courses,
        'query': courses_query,
    })


# Create your views here.
