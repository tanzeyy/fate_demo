export PYTHONOPTIMIZE=1
celery -A celery_worker.celery worker --loglevel=DEBUG