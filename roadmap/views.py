from django.shortcuts import render, get_object_or_404
from .models import Specialization

def specialization_list(request):
    specializations = Specialization.objects.all()
    return render(request, 'roadmap/home.html', {
        'specializations': specializations,
        
    })

def specialization_detail(request, pk):
    specialization = get_object_or_404(Specialization, pk=pk)
    courses = specialization.courses.all()
    return render(request, 'roadmap/courses.html', {
        'specialization': specialization,
        'courses': courses,
    })


# Create your views here.
