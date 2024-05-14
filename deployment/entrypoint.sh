#!/bin/sh

python manage.py collectstatic --no-input
gunicorn fathaker.wsgi:application --workers 3 --bind 0.0.0.0:8000
