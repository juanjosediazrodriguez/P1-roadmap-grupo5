from django.db import models


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=7, blank=True, null=True)  # Hex color
    
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
    
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    credits = models.IntegerField()
    description = models.TextField()
    semester_suggested = models.IntegerField(
        help_text="Semestre sugerido del plan de estudios (1-10)"
    )
    language = models.CharField(
        max_length=4,
        choices=LANGUAGE_CHOICES,
        default='ES'
    )
    
    # Relaciones
    specializations = models.ManyToManyField(
        Specialization,
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
        related_name='corequisite_with',
        blank=True
    )
    
    class Meta:
        ordering = ['semester_suggested', 'code']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_all_prerequisites(self):
        """Retorna todos los prerequisitos de forma recursiva"""
        prereqs = set()
        for prereq in self.prerequisites.all():
            prereqs.add(prereq)
            prereqs.update(prereq.get_all_prerequisites())
        return prereqs
    
    def can_enroll(self, completed_courses):
        """Valida si el estudiante puede inscribir el curso (RF15)"""
        required = set(self.prerequisites.all())
        completed = set(completed_courses)
        return required.issubset(completed)

# Create your models here.
