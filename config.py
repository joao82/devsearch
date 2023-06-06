import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, os.environ.get("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMINS = os.environ.get("ADMINS")
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")
    POSTS_PER_PAGE = 6
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    OAUTHLIB_INSECURE_TRANSPORT = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = 1
    ENV = "development"
    DEVELOPMENT = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, os.environ.get("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OAUTHLIB_INSECURE_TRANSPORT = True
