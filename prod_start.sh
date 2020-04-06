python manage.py migrate
gunicorn waste_storage.wsgi:application

