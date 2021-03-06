from .base import *
import dj_database_url

DEBUG = True

DATABASES = {
    'default': dj_database_url.config()
}

REGISTRATION_OPEN = True

# static files

AWS_STORAGE_BUCKET_NAME = 'monitor404'
S3_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME

STATIC_URL = S3_URL


# email settings

EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = os.environ['SENDGRID_USERNAME']
EMAIL_HOST_PASSWORD = os.environ['SENDGRID_PASSWORD']
EMAIL_PORT = 587
EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = "monitor404.com <no-reply@monitor404.com>"
