import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://postgres:123@localhost:5432/cactocash'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'zezinho_das_sariemas@#'