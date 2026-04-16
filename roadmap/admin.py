from django.contrib import admin
from .models import Specialization, Course, CourseSpecialization, Track, TrackCourse, EmphasisLine, EmphasisLineCourse, UmbrellaCourseOption

class CourseSpecializationInline(admin.TabularInline):
    """Inline para gestionar la relación many-to-many con tabla intermedia"""
    model = CourseSpecialization
    extra = 1
    fields = ['specialization', 'semester_in_specialization', 'is_elective']
    autocomplete_fields = ['specialization']


class UmbrellaCourseOptionInline(admin.TabularInline):
    """Inline para gestionar las opciones de cursos paraguas"""
    model = UmbrellaCourseOption
    extra = 1
    fk_name = 'umbrella_course'  # Importante: especificar que este inline es para el umbrella_course
    fields = ['option_course']
    autocomplete_fields = ['option_course']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('umbrella_course', 'option_course')


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
    
    # Mostrar los cursos relacionados como inline
    inlines = [CourseSpecializationInline]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'credits', 'semester_suggested', 'language', 'is_umbrella']
    list_filter = ['semester_suggested', 'language', 'is_umbrella', 'category']
    search_fields = ['code', 'name']
    
    # Para los campos que son ManyToManyField directos (sin tabla intermedia)
    filter_horizontal = ['prerequisites', 'corequisites']
    
    # Para los campos con tabla intermedia, usamos inlines
    inlines = [CourseSpecializationInline]
    
    # Si es un curso paraguas, mostramos sus opciones
    def get_inlines(self, request, obj=None):
        inlines = super().get_inlines(request, obj)
        if obj and obj.is_umbrella:
            inlines = list(inlines) + [UmbrellaCourseOptionInline]
        return inlines
    
    # Organización de campos
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'credits', 'description')
        }),
        ('Clasificación', {
            'fields': ('semester_suggested', 'language', 'category', 'is_umbrella')
        }),
        ('Relaciones', {
            'fields': ('prerequisites', 'corequisites'),
            'description': 'Las especializaciones y opciones paraguas se gestionan en las secciones de abajo'
        }),
    )
    
    # Para facilitar la búsqueda de cursos en prerequisites/corequisites
    autocomplete_fields = ['prerequisites', 'corequisites']


@admin.register(UmbrellaCourseOption)
class UmbrellaCourseOptionAdmin(admin.ModelAdmin):
    list_display = ['umbrella_course', 'option_course']
    list_filter = ['umbrella_course__is_umbrella']
    search_fields = ['umbrella_course__name', 'option_course__name']
    autocomplete_fields = ['umbrella_course', 'option_course']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('umbrella_course', 'option_course')


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ['name', 'track_type', 'credits_required']
    list_filter = ['track_type']
    search_fields = ['name']


class TrackCourseInline(admin.TabularInline):
    model = TrackCourse
    extra = 1
    fields = ['course', 'semester_in_track', 'is_elective']
    autocomplete_fields = ['course']


@admin.register(EmphasisLine)
class EmphasisLineAdmin(admin.ModelAdmin):
    list_display = ['name', 'credits_required', 'specialization']
    list_filter = ['specialization']
    search_fields = ['name']


class EmphasisLineCourseInline(admin.TabularInline):
    model = EmphasisLineCourse
    extra = 1
    fields = ['course', 'semester_in_line', 'is_elective']
    autocomplete_fields = ['course']