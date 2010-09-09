# Django settings for gramps project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('admin', 'your_email@domain.com'),
)

MANAGERS = ADMINS
DATABASE_ENGINE = 'sqlite3'           
DATABASE_NAME = '/home/dblank/gramps/gep-013-server/src/gen/web/gramps.sql' 
DATABASE_USER = ''             
DATABASE_PASSWORD = ''         
DATABASE_HOST = ''             
DATABASE_PORT = ''             
TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
MEDIA_ROOT = ''
MEDIA_URL = ''
ADMIN_MEDIA_PREFIX = '/gramps-media/'
SECRET_KEY = 'zd@%vslj5sqhx94_8)0hsx*rk9tj3^ly$x+^*tq4bggr&uh$ac'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'gen.web.urls'

TEMPLATE_DIRS = (
    # Use absolute paths, not relative paths.
    "/home/dblank/gramps/gep-013-server/src/data/templates",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'gen.web.grampsdb',
#    'django_extensions',
)

# Had to add these to use settings.configure():
DATABASE_OPTIONS = ''
URL_VALIDATOR_USER_AGENT = ''
DEFAULT_INDEX_TABLESPACE = ''
DEFAULT_TABLESPACE = ''
CACHE_BACKEND = 'locmem://'
TRANSACTIONS_MANAGED = False
LOCALE_PATHS = tuple()

VIEWS = [('People', 'person', 'Person'), 
         ('Families', 'family', 'Family'),
         ('Events', 'event', 'Event'),
         ('Notes', 'note', 'Note'),
         ('Media', 'media', 'Media'),
         ('Sources', 'source', 'Source'),
         ('Places', 'place', 'Place'),
         ('Repositories', 'repository', 'Repository'),
         ]

