#!/usr/bin/env bash
export LC_ALL=zh_CN.utf8
export LANG=zh_CN.utf8
export FLASK_APP="application"
export FLASK_ENV="development"
export PYTHONOPTIMIZE=1
python manage.py runserver --no-reload --host=0.0.0.0
