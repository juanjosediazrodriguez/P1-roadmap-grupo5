# P1-roadmap

Aplicación Django para visualizar el roadmap académico de Ingeniería de Sistemas, con soporte para trayectorias profesionalizantes, líneas de énfasis, especializaciones y descarga del roadmap en PDF.

## Requisitos previos

- **Python 3.10 o superior** — [descargar](https://www.python.org/downloads/)
- **pip** — incluido con Python 3.10+
- **Git** — [descargar](https://git-scm.com/)
- **Clave de API de Gemini** — necesaria para el sistema de recomendaciones con IA ([obtener gratis en Google AI Studio](https://aistudio.google.com/))

### Dependencias Python (instaladas automáticamente con `pip install -r requirements.txt`)

| Paquete | Uso |
|---|---|
| `django` | Framework web |
| `python-dotenv` | Carga variables de entorno desde `.env` |
| `google-genai` | Recomendaciones con IA (Gemini) |
| `xhtml2pdf` | Generación de PDF del roadmap |
| `matplotlib` | Gráficas |
| `pandas` | Procesamiento de datos |

## Cómo correr el proyecto

### 1. Clonar el repositorio

```bash
git clone https://github.com/juanjosediazrodriguez/P1-roadmap-grupo5.git
cd P1-roadmap-grupo5
```

### 2. Crear el archivo `.env`

Crea un archivo llamado `.env` en la raíz del proyecto con el siguiente contenido:

```text
GEMINI_API_KEY=tu_clave_secreta_aqui
```

> Este archivo está en `.gitignore` y nunca se sube al repositorio.

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Aplicar las migraciones

```bash
python manage.py migrate
```

### 5. Cargar los datos iniciales

```bash
python manage.py loaddata courses.json
python manage.py loaddata specializations.json
python manage.py loaddata tracks.json
python manage.py loaddata emphasis.json
python manage.py loaddata umbrellaoptions.json
python manage.py loaddata coursespecialization.json
python manage.py loaddata trackcourse.json
python manage.py loaddata emphasiscourse.json
python manage.py loaddata preferences_data.json
```

### 6. Crear superusuario (para el admin)

```bash
python manage.py createsuperuser
```

### 7. Correr el servidor

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
python manage.py dumpdata accounts.Interest accounts.CareerGoal accounts.Preference --indent 2 > accounts/fixtures/preferences_data.json
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
## Configuración de Recomendaciones con IA (Gemini)

Para el sistema de recomendaciones automáticas por IA, utilizamos la API gratuita de Gemini. Como las credenciales son secretas, cada desarrollador debe configurar su entorno local:

1. Ve a [Google AI Studio](https://aistudio.google.com/) e inicia sesión con tu cuenta de Google.
2. Haz clic en **Create API Key** y copia la clave generada.
3. En la raíz del proyecto, crea un archivo llamado `.env` (este archivo está ignorado en Git).
4. Agrega tu clave dentro del archivo con el siguiente formato:
   ```text
   GEMINI_API_KEY=tu_clave_secreta_aqui
5. Asegúrate de instalar los nuevos requerimientos ejecutando:
   ```bash 
   pip install -r requirements.txt   