from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    SEMESTER_CHOICES = [(i, f'Semestre {i}') for i in range(1, 11)]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    current_semester = models.IntegerField(
        choices=SEMESTER_CHOICES,
        default=1,
        help_text="Semestre actual del estudiante"
    )
    institutional_email = models.EmailField(
        blank=True, 
        null=True,
        help_text="Correo institucional EAFIT"
    )
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        help_text="Foto de perfil del estudiante"
    )
    ENGLISH_LEVEL_CHOICES = [
        ('NONE', 'Sin nivel'),
        ('A1',   'A1'),
        ('A2',   'A2'),
        ('B1',   'B1'),
        ('B2',   'B2'),
        ('C1',   'C1'),
        ('C2',   'C2'),
    ]

    english_level = models.CharField(
        max_length=4,
        choices=ENGLISH_LEVEL_CHOICES,
        default='NONE',
        help_text="Nivel de inglés certificado o completado"
    )

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, default='fa-star')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class CareerGoal(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, default='fa-bullseye')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Preference(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='preference'
    )
    interests = models.ManyToManyField(Interest, blank=True, related_name='preferences')
    career_goal = models.ForeignKey(
        CareerGoal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferences'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Preference'
        verbose_name_plural = 'Preferences'

    def __str__(self):
        return f"Preferencia Global #{self.id}"