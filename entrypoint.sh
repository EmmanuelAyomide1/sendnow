#!/bin/sh

if [ "$DATABASE" = "postgres" ] && [ "$DEBUG" = "1" ]
then
    echo "Waiting for response..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
        sleep 0.1
    done

    echo "PostgreSQL Started!"

fi

# python manage.py flush --no-input
# python manage.py makemigrations
python manage.py migrate
# python manage.py collectstatic --no-input --clear

# Data migration single command
# python manage.py migrate_data_to_django

exec "$@"