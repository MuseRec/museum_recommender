"""
Django settings for museum_webapp project.

Generated by 'django-admin startproject' using Django 3.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
# STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
#original:
SECRET_KEY='l5il)#1h#d&_sbt+*svpu&6wkz$dz(gz93&)ew3l2u=tyjz*a-'


SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
#DEBUG = os.getenv('DEBUG')
DEBUG = True


ALLOWED_HOSTS = ['127.0.0.1','10.99.96.155', '130.88..36.13', 'artdatastudy.its.manchester.ac.uk',]

CONTEXT = os.environ.get('CONTEXT', default = 'user')

if CONTEXT == 'focus':
    DATA_REP_TYPE = 'concatenated'

if CONTEXT == 'user':
    CONDITIONS = ['meta', 'image', 'concatenated']
    CONDITION_INDEXES = {'meta': 0, 'image': 1, 'concatenated': 2}
    ORDER = ['random', 'model']
    ORDER_INDEXES = {'random': 0, 'model': 1}
    SELECTION_UPPER_BOUND = 10
    SELECTION_LOWER_BOUND = 5
    INITIAL_ARTWORKS = [
        'ACC_ACC_ACA_59-001', 'BCN_ELYM_1999_091-001', 'TATE_TATE_T00733_10-001',
        'CW_FAG_FAMAG_2004_17_27-001', 'ASH_ASHM_WA1955_66-001', 'TATE_TATE_N05390_10-001',
        'SFK_SED_MA_1992_9_395-001', 'LLR_NTLMS_1965_094_1-001', 'ABD_AAG_ag002265-001',
        'NG_NG_NG6394-001', 'NGS_NGS_AR00230-001', 'NTV_PH_66-001', 
        'ABD_RGU_10186-001', 'CHE_CEC_PCF119-001', 'WS_LMT_002_022A-001',
        'LLR_AWC_0829-001', 'VA_PC_2006BA0177-001', 'NWM_ALU_PCF1-001',
        'GL_GM_1719-001', 'CAM_CCF_781-001', 'SYO_BHA_90003666-001',
        'NY_MAG_HARAG_267-001', 'NTS_BROD_2009_597-001', 'STF_SAMS_G98_003_0002-001',
        'ACC_ACC_ACC1_1947-001', 'HSW_DMAG_1976_94-001', 'ACC_ACC_AC_5490-001',
        'NOT_NSDC_36_70-001', 'ACC_ACC_AC_1370-001', 'NG_NG_NG1079-001',
    ]
    NUMBER_OF_STEPS = 5

# Application definition
INSTALLED_APPS = [
    'museum_site.apps.MuseumSiteConfig',
    'collector.apps.CollectorConfig',
    'recommendations.apps.RecommendationsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}

ROOT_URLCONF = 'museum_webapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'museum_webapp.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
if os.getenv('TRAVIS', None):
    SECRET_KEY = 'l5il)#1h#d&_sbt+*svpu&6wkz$dz(gz93&)ew3l2u=tyjz*a-'
    DEBUG = False 
    TEMPLATE_DEBUG = True

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR , 'db.sqlite3'),
        }
    }
else:
    SECRET_KEY = 'l5il)#1h#d&_sbt+*svpu&6wkz$dz(gz93&)ew3l2u=tyjz*a-'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'museum_recsys_db',
            #'USER': os.getenv('DB_USER'),
            #'PASSWORD': os.getenv('DB_PW'),
            'USER': 'museum_db_user',
            'PASSWORD': '0qhzf}5Bf{ek',
            'HOST': '127.0.0.1',
            'PORT': '3306'
        }
    }

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [    os.path.join(BASE_DIR, 'static')]
