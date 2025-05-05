#!/bin/sh

# python manage.py flush --no-input
python manage.py wait_for_db
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

exec "$@"
