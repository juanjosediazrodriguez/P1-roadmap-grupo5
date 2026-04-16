from django.contrib import admin
from .models import Interest, CareerGoal, Preference

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'description']
    search_fields = ['name']


@admin.register(CareerGoal)
class CareerGoalAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'description']
    search_fields = ['name']

@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ['id', 'career_goal', 'created_at', 'updated_at']
    filter_horizontal = ['interests']
    readonly_fields = ['created_at', 'updated_at']