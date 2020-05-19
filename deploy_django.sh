#!bin bash
# deploying

source venv/bin/activate && python manage.py collectstatic && service apache2 restart

