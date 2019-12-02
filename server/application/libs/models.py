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
    client_url = Column(String(100))

    models = relationship('Model',
                         secondary=user_models,
                         back_populates='users')
                  

    def __init__(self, name=None, party_id=party_id):
        self.name = name
        self.party_id = party_id

    def __repr__(self):
        return '<User %r>' % (self.id)

    def get_id(self):
        return self.user_id


class Model(Base):
    __tablename__ = 'models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fate_id = Column(String(500), unique=False)
    fate_version = Column(String(500), unique=False)
    info = Column(JSON)

    users = relationship('User',
                         secondary=user_models,
                         back_populates='models')

    orders = relationship("Order", back_populates='model')


    def __init__(self, fate_id, fate_version, info=None):
        self.fate_id = fate_id
        self.fate_version = fate_version
        self.info = info

    def __repr__(self):
        return "<Model(%r, %r)>" % (self.fate_id, self.fate_version)


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(10))
    order_info = Column(JSON)
    job_info = Column(JSON)

    model_id = Column(Integer, ForeignKey('models.id'))
    model = relationship("Model", foreign_keys=model_id,  back_populates='orders')

    def __init__(self, type, order_info, job_info):
        self.order_info = order_info
        self.job_info = job_info
        self.type = type
