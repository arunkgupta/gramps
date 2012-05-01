# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009         Douglas S. Blank <doug.blank@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# $Id$
#

""" Django settings for gramps project. """

# Need to be able to import Gramps files from here.

import const
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

INTERNAL_IPS = ('127.0.0.1',)

ADMINS = (
    ('admin', 'your_email@domain.com'),
)

MANAGERS = ADMINS
DATABASE_ROUTERS = []
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(const.WEB_DIR, 'sqlite.db'),
    }
}
DATABASE_ENGINE = 'sqlite3'           
DATABASE_NAME = os.path.join(const.WEB_DIR, 'sqlite.db')
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
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'webapp.urls'

TEMPLATE_DIRS = (
    # Use absolute paths, not relative paths.
    os.path.join(const.DATA_DIR, "templates"),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
#    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "webapp.grampsdb.views.context_processor",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'webapp.grampsdb',
#    'django_extensions',
#    'debug_toolbar',
)

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
    )

def custom_show_toolbar(request):
    return True # Always show toolbar, for example purposes only.

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
#    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
#    'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
    'HIDE_DJANGO_SQL': False,
    }

AUTH_PROFILE_MODULE = "grampsdb.Profile"

# Had to add these to use settings.configure():
DATABASE_OPTIONS = ''
URL_VALIDATOR_USER_AGENT = ''
DEFAULT_INDEX_TABLESPACE = ''
DEFAULT_TABLESPACE = ''
CACHE_BACKEND = 'locmem://'
TRANSACTIONS_MANAGED = False
LOCALE_PATHS = tuple()

# Changes for Django 1.3:
CACHES = {}
USE_L10N = True
FORMAT_MODULE_PATH = ""
## End Changes for Django 1.3

# Changes for Django 1.4:
USE_TZ = True
## End Changes for Django 1.4

# In versions < 2.7 python does not properly copy methods when doing a 
# deepcopy. This workaround makes the copy work properly. When Gramps no longer
# supports python 2.6, this workaround can be removed.
import sys
if sys.version_info < (2, 7) :
    import copy
    import types
    def _deepcopy_method(x, memo):
        return type(x)(x.im_func, copy.deepcopy(x.im_self, memo), x.im_class)
    copy._deepcopy_dispatch[types.MethodType] = _deepcopy_method
