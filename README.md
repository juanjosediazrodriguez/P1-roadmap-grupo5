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

Copia la plantilla `.env.example` a `.env` y rellena tu clave:

```bash
cp .env.example .env
```

```text
GEMINI_API_KEY=tu_clave_secreta_aqui
```

> Este archivo está en `.gitignore` y nunca se sube al repositorio.
>
> En local no necesitas configurar nada más: sin `DATABASE_URL` el proyecto usa SQLite y `DEBUG` queda en `True`, igual que siempre.

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
   ```

---

## Despliegue en producción (Render + Supabase)

La app se despliega en [Render](https://render.com) (capa gratuita) con la base de datos Postgres en [Supabase](https://supabase.com). El repo ya trae `render.yaml` y `build.sh`; no hay que configurar servidores a mano.

### 1. Crear la base de datos en Supabase

1. Crear una cuenta y un proyecto en [supabase.com](https://supabase.com).
2. En **Connect**, copiar la connection string del **pooler en session mode**:

   ```text
   postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
   ```

> ### ⚠️ No uses la conexión directa
>
> La connection string **directa** (`db.[ref].supabase.co`) resuelve **solo a IPv6**, y el tráfico saliente de Render es **únicamente IPv4**. Si usas esa, el deploy falla con un error de conexión poco descriptivo. Hay que usar el host del pooler (`...pooler.supabase.com`).
>
> Y del pooler, usar el **puerto 5432** (*session mode*), que funciona con Django sin cambiar nada. El puerto **6543** es *transaction mode* y exigiría desactivar los prepared statements en `settings.py` (`OPTIONS={"prepare_threshold": None}`, `DISABLE_SERVER_SIDE_CURSORS=True` y `conn_max_age=0`).

### 2. Crear el servicio en Render

1. En Render: **New → Blueprint**, y apuntar al repositorio de GitHub. Render lee `render.yaml` automáticamente.
2. Cargar en el panel las variables marcadas como secretas (no van en el repo):

| Variable | Valor |
|---|---|
| `DATABASE_URL` | La connection string de Supabase (pooler, puerto 5432) |
| `GEMINI_API_KEY` | Tu clave de Google AI Studio |
| `LOAD_FIXTURES` | `true` **solo para el primer deploy** (ver abajo) |
| `DJANGO_SUPERUSER_USERNAME` | Opcional: crea el superusuario del admin |
| `DJANGO_SUPERUSER_EMAIL` | Opcional |
| `DJANGO_SUPERUSER_PASSWORD` | Opcional |

`SECRET_KEY` la genera Render sola, y `DEBUG` ya viene en `False` desde `render.yaml`.

### 3. Después del primer deploy

**Poner `LOAD_FIXTURES` en `false`.** Los fixtures traen PKs explícitos, así que si se quedan activos sobrescriben en cada deploy cualquier curso que se haya editado desde el admin.

### Variables de entorno

| Variable | Default | Para qué sirve |
|---|---|---|
| `SECRET_KEY` | clave de dev | Clave criptográfica de Django |
| `DEBUG` | `True` | En producción **debe** ser `False` |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Hosts permitidos, separados por comas |
| `DATABASE_URL` | *(vacío → SQLite)* | Conexión a Postgres |
| `GEMINI_API_KEY` | — | Recomendaciones con IA |
| `LOAD_FIXTURES` | `false` | Si es `true`, el build carga los fixtures |

En local no necesitas ninguna salvo `GEMINI_API_KEY`: los defaults reproducen el comportamiento de siempre (SQLite + `DEBUG=True`).

### Probar la configuración de producción en local

```bash
python manage.py collectstatic --no-input
DEBUG=False ALLOWED_HOSTS=127.0.0.1 python manage.py runserver
```

Si el CSS y el logo cargan, WhiteNoise está bien configurado.

> **Nota sobre las capas gratuitas — importante antes de una sustentación:**
>
> - **Render** duerme el servicio tras ~15 minutos de inactividad; el primer request tras la pausa tarda ~30-50 segundos, pero se despierta solo.
> - **Supabase** *pausa* el proyecto tras **7 días sin actividad de base de datos**, y reactivarlo es **manual** desde el dashboard (avisa por correo antes). Si el proyecto pasa una semana sin uso, entra al panel de Supabase y reactívalo **con antelación** — mientras esté pausado, la app está caída.