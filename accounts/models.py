from django.db import models
from django.contrib.auth.models import User

class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, default='fa-star')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Technology(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    icon = models.CharField(max_length=50, default='fa-code')

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
    # Solo UNA preferencia global (por eso singleton)
    interests = models.ManyToManyField(Interest, blank=True, related_name='preferences')
    technologies = models.ManyToManyField(Technology, blank=True, related_name='preferences')
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