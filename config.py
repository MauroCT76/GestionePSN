import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-psn-catania'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///gestione_psn.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False