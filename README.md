# P1-roadmap

Aplicación Django para visualizar el roadmap de cursos por especialización.

## Requisitos previos

- Python 3.10 o superior
- Django instalado (`pip install django`)

## Cómo correr el proyecto

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd P1-roadmap-grupo5
```

### 2. Aplicar las migraciones

```bash
python manage.py migrate
```

### 3. Cargar los datos iniciales

```bash
python manage.py loaddata specializations.json
```

### 4. Crear superusuario (para el admin)

```bash
python manage.py createsuperuser
```

### 5. Correr el servidor

```bash
python manage.py runserver
```

Abrir en el navegador: http://127.0.0.1:8000/

Admin: http://127.0.0.1:8000/admin/

---

## Actualizar datos del equipo

Cuando alguien agrega o modifica especializaciones o cursos desde el admin, debe exportar y compartir los datos con el equipo.

### Si agregas o modificas datos (tú)

**1. Exportar especializaciones:**

```bash
python manage.py dumpdata roadmap.Specialization --indent 2 > roadmap/fixtures/specializations.json
```

**2. Exportar cursos (si también modificaste cursos):**

```bash
python manage.py dumpdata roadmap.Course --indent 2 > roadmap/fixtures/courses.json
```

**3. Subir al repositorio:**

```bash
git add roadmap/fixtures/
git commit -m "Update fixtures with new data"
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
```

O si también hay cursos:

```bash
python manage.py loaddata specializations.json courses.json
```
