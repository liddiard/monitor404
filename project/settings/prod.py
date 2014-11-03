from .base import *
import dj_database_url

DEBUG = False

DATABASES = {
    'default': dj_database_url.config()
}

REGISTRATION_OPEN = True

# static files

AWS_STORAGE_BUCKET_NAME = 'monitor404'
S3_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME

STATIC_URL = S3_URL


# email

MANDRILL_API_KEY = os.environ['MANDRILL_API_KEY']
EMAIL_BACKEND = "djrill.mail.backends.djrill.DjrillBackend"

DEFAULT_FROM_EMAIL = "monitor404 <no-reply@monitor404.com>"
