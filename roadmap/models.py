from django.db import models
from accounts.models import UserProfile, Preference
from django.contrib.auth.models import User


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Specialization'
        verbose_name_plural = 'Specializations'
    
    def __str__(self):
        return self.name


class Course(models.Model):
    LANGUAGE_CHOICES = [
        ('ES', 'Español'),
        ('EN', 'English'),
        ('BOTH', 'Bilingüe'),
    ]
    
    CATEGORY_CHOICES = [
        ('BASIC_SCIENCE', 'Ciencias Básicas'),
        ('BASIC_ENGINEERING', 'Básicas en Ingeniería'),
        ('NFI', 'NFI'),
        ('DISCIPLINARY', 'Disciplinar'),
        ('PROFESSIONAL_TRACK', 'Trayectoria Profesionalizante'),
        ('FLEXIBLE_TRACK', 'Trayectoria Flexible'),
        ('PRACTICE', 'Práctica'),
        ('EMPHASIS', 'Énfasis'),
        ('SPECIALIZATION', 'Especialización'),
    ]
    
    code = models.CharField(max_length=10, unique=True, blank=True, null=True,
                            help_text="Código del curso (puede ser nulo para cursos paraguas)")
    name = models.CharField(max_length=200)
    credits = models.IntegerField()
    description = models.TextField()
    semester_suggested = models.IntegerField(
        help_text="Semestre sugerido del plan de estudios (1-10)"
    )
    language = models.CharField(
        max_length=4,
        choices=LANGUAGE_CHOICES,
        default='ES',
        blank=True,
        null=True
    )
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='DISCIPLINARY',
        help_text="Categoría del curso según el plan de estudios"
    )
    
    # Relación de cursos paraguas (autorreferencial)
    is_umbrella = models.BooleanField(
        default=False,
        help_text="Si es un curso paraguas (ej: 'Electiva Matemática I' que tiene múltiples opciones)"
    )
    available_options = models.ManyToManyField(
        'self',
        through='UmbrellaCourseOption',
        symmetrical=False,
        related_name='available_for_umbrellas',
        blank=True
    )
    
    # Relaciones existentes
    specializations = models.ManyToManyField(
        Specialization, 
        through='CourseSpecialization',
        related_name='courses',
        blank=True
    )
    
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='prerequisite_for',
        blank=True
    )
    
    corequisites = models.ManyToManyField(
        'self',
        symmetrical=True,
        blank=True
    )
    
    class Meta:
        ordering = ['semester_suggested', 'code']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
    
    def __str__(self):
        if self.code:
            return f"{self.code} - {self.name}"
        return f"[Paraguas] {self.name}"
    
    def get_all_prerequisites(self):
        """Retorna todos los prerequisitos de forma recursiva"""
        prereqs = set()
        for prereq in self.prerequisites.all():
            prereqs.add(prereq)
            prereqs.update(prereq.get_all_prerequisites())
        return prereqs

class UmbrellaCourseOption(models.Model):
    """Relación entre cursos paraguas y sus opciones disponibles"""
    umbrella_course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='umbrella_options',
        limit_choices_to={'is_umbrella': True}
    )
    option_course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='options_for_umbrellas'
    )
    
    class Meta:
        unique_together = ['umbrella_course', 'option_course']
        verbose_name = 'Umbrella Course Option'
        verbose_name_plural = 'Umbrella Courses Options'
    
    def __str__(self):
        return f"{self.umbrella_course.code} → {self.option_course.code}"

class CourseSpecialization(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE)
    semester_in_specialization = models.IntegerField(
        help_text="Semestre dentro de la especialización (1-4)"
    )
    is_elective = models.BooleanField(
        default=True, 
        help_text="True = electivo, False = obligatorio fijo"
    )
    
    class Meta:
        unique_together = ['course', 'specialization']
        verbose_name = 'Curso de Especialización'
        verbose_name_plural = 'Cursos de Especialización'
    
    def __str__(self):
        return f"{self.specialization.name} - {self.course.code}"


class Track(models.Model):
    """Trayectorias (profesionalizantes y flexibles)"""
    TRACK_TYPES = [
        ('PROFESSIONAL', 'Profesionalizante'),
        ('FLEXIBLE', 'Flexible'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    track_type = models.CharField(max_length=20, choices=TRACK_TYPES)
    credits_required = models.IntegerField(
        default=0, 
        help_text="Créditos necesarios para completar la trayectoria"
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Track'
        verbose_name_plural = 'Tracks'
    
    def __str__(self):
        return f"{self.name} ({self.get_track_type_display()})"


class TrackCourse(models.Model):
    """Tabla intermedia para cursos en trayectorias"""
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='track_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_tracks')
    semester_in_track = models.IntegerField(
        help_text="Semestre dentro de la trayectoria (1-4)"
    )
    is_elective = models.BooleanField(
        default=True, 
        help_text="True = electivo, False = obligatorio fijo"
    )
    
    class Meta:
        unique_together = ['track', 'course']
        ordering = ['semester_in_track']
        verbose_name = 'Curso de Trayectoria'
        verbose_name_plural = 'Cursos de Trayectorias'
    
    def __str__(self):
        return f"{self.track.name} - {self.course.code} (Sem {self.semester_in_track})"


class EmphasisLine(models.Model):
    """Línea de énfasis"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    credits_required = models.IntegerField(
        default=0, 
        help_text="Créditos necesarios para completar la línea"
    )
    
    # Conexión con especialización (nullable)
    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emphasis_lines',
        help_text="Especialización a la que conduce esta línea"
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Emphasis Line'
        verbose_name_plural = 'Emphasis Lines'
    
    def __str__(self):
        return self.name


class EmphasisLineCourse(models.Model):
    """Tabla intermedia para cursos en líneas de énfasis"""
    emphasis_line = models.ForeignKey(
        EmphasisLine, 
        on_delete=models.CASCADE, 
        related_name='line_courses'
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='course_lines'
    )
    semester_in_line = models.IntegerField(
        help_text="Semestre dentro de la línea (1-2)"
    )
    is_elective = models.BooleanField(
        default=True, 
        help_text="True = electivo, False = obligatorio fijo"
    )
    
    class Meta:
        unique_together = ['emphasis_line', 'course']
        ordering = ['semester_in_line']
        verbose_name = 'Curso de Línea'
        verbose_name_plural = 'Cursos de Líneas'
    
    def __str__(self):
        return f"{self.emphasis_line.name} - {self.course.code} (Sem {self.semester_in_line})"
    
class RoadmapState(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='roadmap_state'
    )
    state = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Roadmap de {self.user.username}"