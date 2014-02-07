from .base import *
import dj_database_url

DEBUG = True

DATABASES = {
    'default': dj_database_url.config()
}

AWS_STORAGE_BUCKET_NAME = '404monitor'
S3_URL = 'http://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME

STATIC_URL = S3_URL
