import click
from flask import current_app, g
from flask.cli import with_appcontext
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .models import Base

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


def init_db():
    Base.metadata.create_all(engine)


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initilized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
