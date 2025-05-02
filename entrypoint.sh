#!/bin/sh

# python manage.py flush --no-input
python manage.py wait_for_db
python manage.py migrate
python manage.py collectstatic --no-input

exec "$@"