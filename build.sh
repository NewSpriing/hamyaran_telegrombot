#!/bin/bash
pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate