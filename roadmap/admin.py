from django.contrib import admin
from .models import Specialization, Course

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'credits', 'semester_suggested', 'language']
    list_filter = ['semester_suggested', 'language', 'specializations']
    search_fields = ['code', 'name']
    filter_horizontal = ['specializations', 'prerequisites', 'corequisites']

# Register your models here.
