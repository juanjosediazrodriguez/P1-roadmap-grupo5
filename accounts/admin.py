from django.contrib import admin
from .models import Interest, Technology, CareerGoal, Preference

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'description']
    search_fields = ['name']

@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'icon']
    list_filter = ['category']
    search_fields = ['name']

@admin.register(CareerGoal)
class CareerGoalAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'description']
    search_fields = ['name']

@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ['id', 'career_goal', 'created_at', 'updated_at']
    filter_horizontal = ['interests', 'technologies']
    readonly_fields = ['created_at', 'updated_at']