from django.core.management.base import BaseCommand
from accounts.models import Interest, Technology, CareerGoal

class Command(BaseCommand):
    help = 'Popula la base de datos con intereses, tecnologías y metas profesionales'

    def handle(self, *args, **kwargs):
        # Intereses
        interests_data = [
            {"name": "Desarrollo de Software", "icon": "fa-code", "description": "Creación de aplicaciones y sistemas"},
            {"name": "Ciencia de Datos", "icon": "fa-chart-line", "description": "Análisis y visualización de datos"},
            {"name": "Inteligencia Artificial", "icon": "fa-brain", "description": "Machine Learning y Deep Learning"},
            {"name": "Ciberseguridad", "icon": "fa-shield-alt", "description": "Protección de sistemas y datos"},
            {"name": "Computación en la Nube", "icon": "fa-cloud", "description": "AWS, Azure, Google Cloud"},
            {"name": "Gestión de Proyectos", "icon": "fa-tasks", "description": "Metodologías ágiles y tradicionales"},
            {"name": "Investigación", "icon": "fa-flask", "description": "Investigación académica y aplicada"},
            {"name": "Emprendimiento", "icon": "fa-rocket", "description": "Creación de startups y negocios tech"},
        ]
        
        for data in interests_data:
            obj, created = Interest.objects.update_or_create(
                name=data["name"],
                defaults={
                    "icon": data["icon"], 
                    "description": data["description"]
                }
            )
            if created:
                self.stdout.write(f'Interés creado: {data["name"]}')
            else:
                self.stdout.write(f'Interés actualizado: {data["name"]}')

        # Tecnologías
        technologies_data = [
            {"name": "Python", "category": "backend", "icon": "fa-brands fa-python"},
            {"name": "React", "category": "devops", "icon": "fa-brands fa-react"}, 
            {"name": "Java", "category": "backend", "icon": "fa-brands fa-java"},      
            {"name": "JavaScript", "category": "frontend", "icon": "fa-brands fa-js"}, 
            {"name": "C++", "category": "systems", "icon": "fa-code"}, 
            {"name": "SQL", "category": "database", "icon": "fa-database"},  
            {"name": "AWS", "category": "cloud", "icon": "fa-brands fa-aws"},         
            {"name": "Docker", "category": "devops", "icon": "fa-brands fa-docker"},  
            {"name": "Kubernetes", "category": "devops", "icon": "fa-cubes"},  
            {"name": "TensorFlow", "category": "ai", "icon": "fa-brain"},
        ]
        
        for data in technologies_data:
            obj, created = Technology.objects.update_or_create(
                name=data["name"],
                defaults={
                    "category": data["category"], 
                    "icon": data["icon"]
                }
            )
            if created:
                self.stdout.write(f'Tecnología creada: {data["name"]}')
            else:
                self.stdout.write(f'Tecnología actualizada: {data["name"]}')

        # Metas profesionales
        goals_data = [
            {"name": "Industria", "icon": "fa-building", "description": "Trabajo en empresas tecnológicas"},
            {"name": "Startup", "icon": "fa-lightbulb", "description": "Emprendimiento propio"},
            {"name": "Investigación", "icon": "fa-university", "description": "Academia e investigación"},
            {"name": "Freelance", "icon": "fa-laptop", "description": "Trabajo independiente"},
            {"name": "Posgrado", "icon": "fa-graduation-cap", "description": "Estudios avanzados"},
        ]
        
        for data in goals_data:
            obj, created = CareerGoal.objects.update_or_create(
                name=data["name"],
                defaults={
                    "icon": data["icon"], 
                    "description": data["description"]
                }
            )
            if created:
                self.stdout.write(f'Meta creada: {data["name"]}')
            else:
                self.stdout.write(f'Meta actualizada: {data["name"]}')

        self.stdout.write(self.style.SUCCESS('Datos poblados/actualizados exitosamente'))