#!/usr/bin/env bash
# Script de build para Render. Se ejecuta en cada deploy.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Los fixtures traen PKs explicitos: cargarlos en cada deploy sobrescribiria
# cualquier curso editado desde el admin. Por eso solo corren bajo demanda.
# Poner LOAD_FIXTURES=true para el primer deploy y volverla a false despues.
if [[ "${LOAD_FIXTURES}" == "true" ]]; then
  python manage.py loaddata courses.json
  python manage.py loaddata specializations.json
  python manage.py loaddata tracks.json
  python manage.py loaddata emphasis.json
  python manage.py loaddata umbrellaoptions.json
  python manage.py loaddata coursespecialization.json
  python manage.py loaddata trackcourse.json
  python manage.py loaddata emphasiscourse.json
  python manage.py loaddata preferences_data.json
fi

# Crea el superusuario solo si se definieron las tres variables DJANGO_SUPERUSER_*.
# createsuperuser --noinput es idempotente: si el usuario ya existe, no falla.
if [[ -n "${DJANGO_SUPERUSER_USERNAME}" && -n "${DJANGO_SUPERUSER_PASSWORD}" ]]; then
  python manage.py createsuperuser --no-input || true
fi
