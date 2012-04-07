# -*- coding: utf-8 -*-
#!/usr/bin/env python

#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009-2011 Rob G. Healey <robhealey1@gmail.com>
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

# $Id$

# ***********************************************
# Python Modules
# ***********************************************
import os, sys, sysconfig
import imp
import glob, shutil
import codecs

#------------------------------------------------
#        Distutils/ Distutils2 modules
#------------------------------------------------
from distutils2 import logger

const_file_in = os.path.join('gramps', 'const.py.in')
const_file = os.path.join('gramps', 'const.py')
if (os.path.exists(const_file_in) and not os.path.exists(const_file)):
    shutil.copy(const_file_in, const_file)
from gramps.const import VERSION as GRAMPS_VERSION

#------------------------------------------------
#        Constants
#------------------------------------------------
_FILENAME = 'setup.cfg'

platform = ('Linux', 'FreeBSD', 'Mac OSX', 'Windows')

requires = ('pygtk2', 'pycairo', 'pygobject2')

Keywords = ('Genealogy', 'Pedigree', 'Ancestry', 'Birth', 'Marriage',
            'Death', 'Family', 'Family-tree', 'GEDCOM')

classifier = '''
    Development Status :: 5 - Production/Stable
    Environment :: Console
    Environment :: MacOS X
    Environment :: Plugins
    Environment :: Web Environment
    Environment :: Win32 (MS Windows)
    Environment :: X11 Applications :: GTK
    Framework :: Django
    Intended Audience :: Education
    Intended Audience :: End Users/Desktop
    Intended Audience :: Other Audience
    Intended Audience :: Science/Research
    License :: OSI Approved :: GNU General Public License (GPL)
    Natural Language :: Bulgarian
    Natural Language :: Catalan
    Natural Language :: Chinese (Simplified)
    Natural Language :: Croatian
    Natural Language :: Czech
    Natural Language :: Danish
    Natural Language :: Dutch
    Natural Language :: English
    Natural Language :: Esperanto
    Natural Language :: Finnish
    Natural Language :: French
    Natural Language :: German
    Natural Language :: Hebrew
    Natural Language :: Hungarian
    Natural Language :: Italian
    Natural Language :: Japanese
    Natural Language :: Norwegian
    Natural Language :: Polish
    Natural Language :: Portuguese (Brazilian)
    Natural Language :: Portuguese
    Natural Language :: Russian
    Natural Language :: Slovak
    Natural Language :: Slovenian
    Natural Language :: Spanish
    Natural Language :: Swedish
    Natural Language :: Ukranian
    Natural Language :: Vietnamese
    Operating System :: MacOS
    Operating System :: Microsoft :: Windows
    Operating System :: Other OS
    Operating System :: POSIX :: BSD
    Operating System :: POSIX :: Linux
    Operating System :: POSIX :: SunOS/Solaris
    Operating System :: Unix
    Programming Language :: Python
    Programming Language :: Python :: 2.7
    Topic :: Database
    Topic :: Desktop Environment :: Gnome
    Topic :: Education
    Topic :: Multimedia
    Topic :: Other/Nonlisted Topic
    Topic :: Scientific/Engineering :: Visualization
    Topic :: Sociology :: Genealogy
'''

packages = ['gramps', 'gramps.cli', 'gramps.data', 'gramps.gen', 'gramps.glade',
            'gramps.gui', 'gramps.images', 'gramps.plugins', 'gramps.webapp']
package_data = dict((section, list()) for section in packages if section not in ['gramps.images', 'gramps.plugins'])
extra_files = dict(section, list()) for section in packages if section in ['gramps.images', 'gramps.plugins'])

all_files = {
    'gramps' : [
        '*.py',
        'DateHandler/*.py',
        'docgen/*.py',
        'Filters/*.py',
        'Filters/*/*.py',
        'Filters/Rules/*/*.py',
        'GrampsLocale/*.py',
        'GrampsLogger/*.py',
        'Merge/*.py',
        'Simple/*.py',
        'TestPlan.txt',
        'test/*.py'],
    'gramps.cli': [
        '*.py',
        'plug/*.py'],
    'gramps.data': [
        '*.txt',
        '*.xml'],
    'gramps.gen': [
        '*.py',
        'db/*.py',
        'display/*.py',
        'lib/*.py',
        'mime/*.py',
        'plug/*.py',
        'plug/*/*.py',
        'proxy/*.py',
        'test/*.py',
        'utils/*.py'],
    'gramps.glade': [
        '*.glade',
        'glade/catalog/*.py',
        'catalog/*.xml'],
    'gramps.gui': [
        '*.py',
        'editors/*.py',
        'editors/*/*.py',
        'plug/*.py',
        'plug/*/*.py',
        'selectors/*.py',
        'views/*.py',
        'views/treemodels/*.py',
        'widgets/*.py'],
    'gramps.images': [
        '*/*.png',
        '*/*.svg',
        '*.png',
        '*.jpg',
        '*.ico',
        '*.gif'],
    'gramps.plugins': [
        '*.py',
        '*/*.py',
        'lib/*.xml',
        'lib/maps/*.py',
        'webstuff/css/*.css',
        'webstuff/images/*.svg',
        'webstuff/images/*.png',
        'webstuff/images/*.gif',            
        '*.glade',
        '*/*.glade'],
    'gramps.webapp': [
        '*.py',
        'webstuff/css/*.css',
        'webstuff/images/*.svg',
        'webstuff/images/*.png',
        'webstuff/images/*.gif',
        'grampsdb/fixtures/initial_data.json',
        '*/*.py',
        'sqlite.db',
        'grampsdb/*.py',
        'fixtures/initial_data.json',
        'templatetags/*py'],
    }

for section in all_files:
    directory = section
    if '.' in directory:
        directory = '/'.join(directory.split('.'))

    tmp_filenames = []
    for file_match in all_files[section]:
        tmp_filenames.append((glob.glob(os.path.join(directory, file_match))))
        if section in package_data:
            package_data[section] = tmp_filenames
        else:
            extra_files[section] = tmp_filenames

resources = '''data/ gramps.desktop = {data}/share/applications
    gramps/images/ gramps.png = {data}/share/pixmaps
    data/ gramps.xml = {data}/share/mime/packages
    data/ gramps.mime = {data}/share/mime-info
    data/ gramps.keys = {data}/share/mime-info
    data/ gnome-mime-application-x-gedcom.png = {data}/share/icons/gnome/48x48/mimetypes
    data/ gnome-mime-application-x-geneweb.png = {data}/share/icons/gnome/48x48/mimetypes
    data/ gnome-mime-application-x-gramps.png = {data}/share/icons/gnome/48x48/mimetypes
    data/ gnome-mime-application-x-gramps-package.png = {data}/share/icons/gnome/48x48/mimetypes
    data/ gnome-mime-application-x-gramps-xml.png = {data}/share/icons/gnome/48x48/mimetypes
    data/ gnome-mime-application-x-gedcom.svg = {data}/share/icons/gnome/scalable/mimetypes
    data/ gnome-mime-application-x-geneweb.svg = {data}/share/icons/gnome/scalable/mimetypes
    data/ gnome-mime-application-x-gramps.svg = {data}/share/icons/gnome/scalable/mimetypes
    data/ gnome-mime-application-x-gramps-package.svg = {data}/share/icons/gnome/scalable/mimetypes
    data/ gnome-mime-application-x-gramps-xml.svg = {data}/share/icons/gnome/scalable/mimetypes
    data/man/ gramps.1.in = {data}/share/man/man1
    data/man/cs/ gramps.1.in = {data}/share/man/cs/man1
    data/man/fr/ gramps.1.in = {data}/share/man/fr/man1
    data/man/nl/ gramps.1.in = {data}/share/man/nl/man1
    data/man/pl/ gramps.1.in = {data}/share/man/pl/man1
    data/man/sv/ gramps.1.in = {data}/share/man/sv/man1
    COPYING = {data}/share/doc/gramps
    FAQ = {data}/share/doc/gramps
    INSTALL = {data}/share/doc/gramps
    NEWS = {data}/share/doc/gramps
    README = {data}/share/doc/gramps
    TODO = {data}/share/doc/gramps
'''

data_opts = {'name': 'gramps',
             'version': GRAMPS_VERSION,
             'author' : 'Donald N. Allingham',
             'author_email' : 'UNKNOWN',
             'maintainer' : 'Gramps Development Team',
             'maintainer_email' : 'benny.malengier@gmail.com',
             'classifier': classifiers,
             'packages': packages,
             'package_data' : package_data,
             'modules': ,
             'platform': [],
             'resources': [],
             'extra_files': [],
             'scripts': [],
         }


def _write_cfg(self):
    if os.path.exists(_FILENAME):
        if os.path.exists('%s.old' % _FILENAME):
            message = ("ERROR: %(name)s.old backup exists, please check "
                       "that current %(name)s is correct and remove "
                       "%(name)s.old" % {'name': _FILENAME})
            logger.error(message)
            return
        shutil.move(_FILENAME, '%s.old' % _FILENAME)

    fp = codecs.open(_FILENAME, 'w', encoding='utf-8')
