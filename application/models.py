import datetime
import time

import requests
from flask import current_app, json
from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, Sequence, String, Table, JSON,
    create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker


def to_dict(self):
    return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


Base = declarative_base()
Base.to_dict = to_dict
user_models = Table('user_models', Base.metadata,
                   Column('user_id', ForeignKey('users.id'), primary_key=True),
                   Column('model_id', ForeignKey('models.id'), primary_key=True))


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45), unique=True, nullable=True)
    party_id = Column(Integer, unique=True, nullable=False)
    info = Column(JSON)

    models = relationship('Model',
                         secondary=user_models,
                         back_populates='users')

    jobs = relationship('Job',
                        back_populates='user')
                  

    def __init__(self, name=None, party_id=party_id):
        self.name = name
        self.party_id = party_id

    def __repr__(self):
        return '<User %r>' % (self.name)

    def get_id(self):
        return self.user_id


class Model(Base):
    __tablename__ = 'models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fate_id = Column(String(500), unique=True)
    fate_version = Column(String(500), unique=False)
    info = Column(JSON)

    user = relationship('User',
                         secondary=user_models,
                         back_populates='models')

    def __init__(self, fate_id, fate_version, info=None):
        self.fate_id = fate_id
        self.fate_version = fate_version
        self.info = info

    def __repr__(self):
        return "<Model(%r, %r)>" % (self.fate_id, self.fate_version)


class TrainOrders(Base):
    __tablename__ = 'trainOrders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_type = Column(String(50), unique=False)
    model_params = Column(JSON)
    party_list = Column(JSON)
    data_info = Column(JSON)
    fate_id = Column(String(50), unique=True)


class InferOrders(Base):
    __tablename__ = 'inferOrders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String(50), unique=False)
    data_info = Column(JSON)
    fate_id = Column(String(50), unique=True)
    info = Column(JSON)

