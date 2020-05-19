#!/bin/bash
# My first script

cd frontend/ && yarn build && cd .. && python manage.py collectstatic && sudo service apache2 restart  
