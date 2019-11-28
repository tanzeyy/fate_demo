import click
from flask import current_app, g
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


engine = create_engine(
    current_app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True, isolation_level="READ UNCOMMITTED")
Session = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine))

def get_db():
    if 'db' not in g:
        g.db = Session()

    return g.db

@current_app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        Session.remove()


def init_app(app):
    app.teardown_appcontext(close_db)