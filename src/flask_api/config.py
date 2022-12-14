from datetime import timedelta
from os import environ


class Config:
    # Flask
    FLASK_ENV = environ.get('FLASK_ENV', 'production')
    PROPAGATE_EXCEPTIONS = True
    SECRET_KEY = environ.get('SECRET_KEY', 'Super_key!')

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (f'postgresql://{environ.get("DB_USERNAME")}:{environ.get("DB_PASSWORD")}@'
                               f'{environ.get("DB_HOST")}:{environ.get("DB_PORT", 5432)}/{environ.get("DB_NAME")}')

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Extended
    JWT_SECRET_KEY = environ.get('JWT_SECRET_KEY')
    JWT_ERROR_MESSAGE_KEY = 'message'
    JWT_TOKEN_LOCATION = 'headers'
    JWT_COOKIE_SECURE = environ.get('JWT_COOKIE_SECURE', True)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(weeks=4)

    # REST-X
    RESTX_MASK_SWAGGER = False

    # REDIS
    REDIS_URL = environ.get('REDIS_URL')

    # JAEGER
    JAEGER_URL = environ.get('JAEGER_URL', default='localhost')

    # Google OAuth2
    GOOGLE_CLIENT_ID = environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

    # Yandex OAuth2
    YANDEX_CLIENT_ID = environ.get('YANDEX_CLIENT_ID')
    YANDEX_CLIENT_SECRET = environ.get('YANDEX_CLIENT_SECRET')
    YANDEX_API_BASE_URL = 'https://login.yandex.ru/'
    YANDEX_ACCESS_TOKEN_URL = 'https://oauth.yandex.ru/token'
    YANDEX_AUTHORIZE_URL = 'https://oauth.yandex.ru/authorize'
