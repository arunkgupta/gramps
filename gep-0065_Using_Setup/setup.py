# Gramps - a GTK+/GNOME based genealogy program
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
# testing a setup.py for Gramps
#
# $ID$

import sys
from glob import glob
import os
import subprocess
import platform
import shutil

try:
    import py2exe
except:
    pass

ROOT_DIR = os.getcwd()

PO_DIR = os.path.join(ROOT_DIR, 'po')
MO_DIR = os.path.join(ROOT_DIR, 'build', 'mo')

if os.name == 'nt':
    script = os.path.join(ROOT_DIR, 'windows','gramps.pyw')
elif os.name == 'darwin':
    script = os.path.join(ROOT_DIR, 'mac','gramps.launcher.sh')
else:
    # os.name == 'posix'
    script = os.path.join(ROOT_DIR, 'gramps.sh')

if platform.system() == 'FreeBSD':
    man_dir = 'man'
else:
    man_dir = os.path.join('share', 'man')

# copy gramps/const.py.in to gramps/const.py
const_file_in = os.path.join(ROOT_DIR, 'gramps', 'const.py.in')
const_file    = os.path.join(ROOT_DIR, 'gramps', 'const.py')
if (os.path.exists(const_file_in) and not os.path.exists(const_file)):
    shutil.copy(const_file_in, const_file)

# if this system is posix, then copy gramps.sh.in to gramps.sh
if os.name == "posix":
    gramps_launcher_in = os.path.join(ROOT_DIR, 'gramps.sh.in')
    gramps_launcher    = os.path.join(ROOT_DIR, 'gramps.sh')
    if (os.path.exists(gramps_launcher_in) and not os.path.exists(gramps_launcher)):
        shutil.copy(gramps_launcher_in, gramps_launcher)

from distutils.core import setup

def gramps():
    return {'gramps': [
            '*.py', 
            'DateHandler/*.py',
            'docgen/*.py',
            'Filters/*.py',
            'Filters/*/*.py',
            'Filters/Rules/*/*.py',
            'GrampsLocale/*.py',
            'GrampsLogger/*.py',
            'Merge/*.py',
            'Simple/*.py'],
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
            'templatetags/*py']
    }

def os_files():
    if (os.name == 'nt' or os.name == 'darwin'):
        return [
                # application icon
                (os.path.join('share', 'pixmaps'), [os.path.join('gramps', 'images', 'ped24.ico')]),
                (os.path.join('share', 'pixmaps'), [os.path.join('gramps', 'images', 'gramps.png')]),
                (os.path.join('share', 'icons', 'scalable'),
                        glob(os.path.join('gramps', 'images', 'scalable', '*.svg'))),
                (os.path.join('share', 'icons', '16x16'),
                        glob(os.path.join('gramps', 'images', '16x16', '*.png'))),
                (os.path.join('share', 'icons', '22x22'),
                        glob(os.path.join('gramps', 'images', '22x22' ,'*.png'))),
                (os.path.join('share', 'icons', '48x48'),
                        glob(os.path.join('gramps', 'images', '48x48', '*.png'))),
                # doc
                ('share', ['COPYING']),
                ('share', ['FAQ']),
                ('share', ['INSTALL']),
                ('share', ['NEWS']),
                ('share', ['README']),
                ('share', ['TODO'])
        ]
    else:
        return [
                # XDG application description
                ('share/applications', ['data/gramps.desktop']),
                # XDG application icon
                ('share/pixmaps', ['gramps/images/gramps.png']),
                # XDG desktop mime types cache
                ('share/mime/packages', ['data/gramps.xml']),
                # mime.types
                ('share/mime-info', ['data/gramps.mime']),
                ('share/mime-info', ['data/gramps.keys']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gedcom.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-geneweb.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gramps.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gramps-package.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gramps-xml.png']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gedcom.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-geneweb.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gramps.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gramps-package.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gramps-xml.svg']),
                # man-page, /!\ should be gramps.1 with variables
                # migration to sphinx/docutils/gettext environment ?
                (os.path.join(man_dir, 'man1'), ['data/man/gramps.1.in']),
                (os.path.join(man_dir, 'cs', 'man1'), ['data/man/cs/gramps.1.in']),
                (os.path.join(man_dir, 'fr', 'man1'), ['data/man/fr/gramps.1.in']),
                (os.path.join(man_dir, 'nl', 'man1'), ['data/man/nl/gramps.1.in']),
                (os.path.join(man_dir, 'pl', 'man1'), ['data/man/pl/gramps.1.in']),
                (os.path.join(man_dir, 'sv', 'man1'), ['data/man/sv/gramps.1.in']),
                # icons 
                ('share/icons/hicolor/scalable/apps', glob('gramps/images/scalable/*.svg')),
                ('share/icons/hicolor/16x16/apps', glob('gramps/images/16x16/*.png')),
                ('share/icons/hicolor/22x22/apps', glob('gramps/images/22x22/*.png')),
                ('share/icons/hicolor/48x48/apps', glob('gramps/images/48x48/*.png')),
                # doc
                ('share/doc/gramps', ['COPYING']),
                ('share/doc/gramps', ['FAQ']),
                ('share/doc/gramps', ['INSTALL']),
                ('share/doc/gramps', ['NEWS']),
                ('share/doc/gramps', ['README']),
                ('share/doc/gramps', ['TODO'])
        ]

def trans_files():
    '''
    List of available compiled translations; ready for installation
    '''
    translation_files = []
    for mo in glob(os.path.join(MO_DIR, '*', 'gramps.mo')):
        lang = os.path.basename(os.path.dirname(mo))
        if os.name == 'posix':
            dest = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
        else :
            dest = os.path.join('locale', lang, 'LC_MESSAGES')
        translation_files.append((dest, [mo]))
    return translation_files

from gramps.const import VERSION

setup (
    name             = 'gramps',
    version          = VERSION,
    author           = 'Gramps Development Team',
    author_email     = 'benny.malengier@gmail.com',
    url              = 'http://gramps-project.org/',
    download_url     = 'http://sourceforge.net/projects/gramps/files/Stable/3.3.1/',
    license          = "GPLv2 or greater",
    long_description = ('gramps (Genealogical Research and Analysis Management Programming '
                        'System) is a GNOME based genealogy program supporting a Python based plugin system.'),
    packages         = ['gramps',
                        'gramps.cli',
                        'gramps.data',
                        'gramps.gen',
                        'gramps.glade',
                        'gramps.gui',
                        'gramps.guiQML',
                        'gramps.images',
                        'gramps.plugins',
                        'gramps.webapp'],
    package_dir      = {'gramps' : 'gramps'},
    package_data     = gramps(),
    data_files       = trans_files() + os_files(),
    platforms        = ['Linux', 'FreeBSD', 'Mac OSX', 'Windows'],
    scripts          = [script],
)
