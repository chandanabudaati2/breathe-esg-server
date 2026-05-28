web: python manage.py migrate && python manage.py create_default_superuser && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
