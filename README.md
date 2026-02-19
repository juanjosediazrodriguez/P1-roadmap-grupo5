# P1-roadmap

Aplicación Django para visualizar el roadmap de cursos por especialización.

## Requisitos previos

- Python 3.10 o superior
- Django instalado (`pip install django`)

## Cómo correr el proyecto

### 1. Clonar el repositorio

git clone <url-del-repo>
cd P1-roadmap-grupo5

### 2. Aplicar las migraciones

python manage.py migrate

### 3. Cargar los datos iniciales

python manage.py loaddata specializations.json

### 4. Crear superusuario (para el admin)

python manage.py createsuperuser

### 5. Correr el servidor

python manage.py runserver

Abrir en el navegador: http://127.0.0.1:8000/
Admin: http://127.0.0.1:8000/admin/
