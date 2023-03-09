#!/bin/sh

set -o errexit
set -o nounset

python manage.py wait_for_db
python manage.py migrate
python manage.py create_admin
python manage.py collectstatic --no-input
gunicorn imaginarium.wsgi:application --bind 0.0.0.0:8000