# P1-roadmap

Aplicación Django para visualizar el roadmap de cursos por especialización.

## Requisitos previos

- Python 3.10 o superior
- Django instalado (`pip install django`)

## Cómo correr el proyecto

### 1. Clonar el repositorio

```bash
git clone <url del proyecto>
cd P1-roadmap-grupo5
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Aplicar las migraciones

```bash
python manage.py migrate
```

### 4. Cargar los datos iniciales

```bash
python manage.py loaddata specializations.json
python manage.py loaddata tracks.json
python manage.py loaddata emphasis.json
python manage.py loaddata courses.json
python manage.py loaddata umbrellaoptions.json
python manage.py loaddata coursespecialization.json
python manage.py loaddata trackcourse.json
python manage.py loaddata emphasiscourse.json
python manage.py loaddata preferences_data.json
```

### 5. Crear superusuario (para el admin)

```bash
python manage.py createsuperuser
```

### 6. Correr el servidor

```bash
python manage.py runserver
```

Abrir en el navegador: http://127.0.0.1:8000/

Admin: http://127.0.0.1:8000/admin/

---

## Actualizar datos del equipo

Cuando alguien agrega o modifica especializaciones o cursos desde el admin, debe exportar y compartir los datos con el equipo.

### Si agregas o modificas datos (tú)

**Exportar datos para los modelos:**

```bash
# Especializaciones
python manage.py dumpdata roadmap.Specialization --indent 2 > roadmap/fixtures/specializations.json

# Trayectorias
python manage.py dumpdata roadmap.Track --indent 2 > roadmap/fixtures/tracks.json

# Líneas de énfasis
python manage.py dumpdata roadmap.EmphasisLine --indent 2 > roadmap/fixtures/emphasis.json

# Cursos (incluye paraguas y opciones)
python manage.py dumpdata roadmap.Course --indent 2 > roadmap/fixtures/courses.json

# Relaciones paraguas
python manage.py dumpdata roadmap.UmbrellaCourseOption --indent 2 > roadmap/fixtures/umbrellaoptions.json

# Relaciones cursos-especializaciones
python manage.py dumpdata roadmap.CourseSpecialization --indent 2 > roadmap/fixtures/coursespecialization.json

# Relaciones cursos-trayectorias
python manage.py dumpdata roadmap.TrackCourse --indent 2 > roadmap/fixtures/trackcourse.json

# Relaciones cursos-énfasis
python manage.py dumpdata roadmap.EmphasisLineCourse --indent 2 > roadmap/fixtures/emphasiscourse.json

# Preferencias de usuario (accounts)
python manage.py dumpdata accounts.Interest accounts.Technology accounts.CareerGoal accounts.Preference --indent 2 > accounts/fixtures/preferences_data.json
```

**Subir al repositorio:**

```bash
git add roadmap/fixtures/ accounts/fixtures/
git commit -m "Actualizar fixtures con nuevos datos"
git push
```

### Si un compañero subió datos nuevos (tú recibes)

**1. Bajar los cambios:**

```bash
git pull origin main
```

**2. Cargar los datos actualizados:**

```bash
python manage.py loaddata specializations.json
python manage.py loaddata tracks.json
python manage.py loaddata emphasis.json
python manage.py loaddata courses.json
python manage.py loaddata umbrellaoptions.json
python manage.py loaddata coursespecialization.json
python manage.py loaddata trackcourse.json
python manage.py loaddata emphasiscourse.json
python manage.py loaddata preferences_data.json
```