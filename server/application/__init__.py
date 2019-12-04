import os

from flask import Flask
from flask_cors import CORS
from celery import Celery
from instance import config

celery = Celery(__name__, backend=config.CELERY_RESULT_BACKEND, broker=config.CELERY_BROKER_URL)

def register_celery(app):
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

def create_app(test_config=None):
    # Create and configure the app.
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing.
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in.
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists.
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    with app.app_context():
        from .libs import db
        db.init_app(app)

    from . import model
    app.register_blueprint(model.bp)

    register_celery(app)

    return app