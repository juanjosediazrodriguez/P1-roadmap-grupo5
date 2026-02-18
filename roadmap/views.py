from django.shortcuts import render
from .models import Specialization

def specialization_list(request):
    specializations = Specialization.objects.all()
    return render(request, 'roadmap/home.html', {
        'specializations': specializations,
    })



# Create your views here.
