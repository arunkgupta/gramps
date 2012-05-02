
#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import os, sys, glob, shutil, subprocess
import codecs

# if hasattr(os, 'uname'):
#    (osname, host, release, version, machine) = os.uname()

# verify Python version first, and import modules
version_info = sys.version_info[0:3]
try:
    assert version_info >= (2,6, 0)
except AssertionError:
    sys.exit('gramps needs Python >= 2.6.0.  You currently have: \n%s' % version_info)

#------------------------------------------------
#        Distutils2, Packaging, Distutils modules
#------------------------------------------------
try:
    from distutils2 import logger as _LOG
    from distutils2.util import find_packages, convert_path, newer
except ImportError:
    try:
        from packaging import logger as _LOG
        from packaging.util import find_packages, convert_path, newer
    except ImportError:
        try:
            from distutils import log as _LOG
            from distutils.util import find_packages, convert_path, newer
        except ImportError:
           # no Distutils, Distutils2, packaging is NOT installed!
           sys.exit('Distutils2, Packaging, or Distutils is Required!\n',
                    'You need to have one of these installed.')

#------------------------------------------------
#        Gramps modules
#------------------------------------------------
# get list of classifiers 
from setup_custom import (all_classifiers, create_gramps_trans, create_gramps_man,
                          create_gramps_intl)   

gramps_sh_in   = 'gramps.sh.in'
gramps_sh_data = 'gramps.sh'
if not os.path.exists(gramps_sh_data):
    shutil.copy(gramps_sh_in, gramps_sh_data)

const_py_in    = os.path.join('gramps', 'const.py.in')
const_py_data  = os.path.join('gramps', 'const.py')
if not os.path.exists(const_py_data):
    shutil.copy(const_py_in, const_py_data)

#------------------------------------------------
#        Constants
#------------------------------------------------
_FILENAME = 'setup.cfg'
VERSION = '3.5.0'
BUILD_DIR = 'build'

PO_DIR = 'po'
MO_DIR = os.path.join(BUILD_DIR, 'mo')

#-----------------------
#        Helper functions
#-----------------------
def find_child_dir(top, root=''):
    top = convert_path(top)
    if not os.path.isdir(os.path.join(root, top)):
        return []
    dir_list = [top]
    to_do = [top]
    while to_do:
        where = to_do.pop(0)
        for name in os.listdir(os.path.join(root, where)):
            fn = os.path.join(root, where, name)
            if os.path.isdir(fn):

                if '.' not in name: # exclude hidden subversion directories
                    to_do.append(os.path.join(where, name))
                    dir_list.append(os.path.join(where, name))
    return dir_list

'''
    Creates the setup configuration file, 'setup.cfg'
'''
class ConfigWriter(object):
    def __init__(self):
        self.__file = None

    def open(self, filename):
        try: 
            self.__file = codecs.open(filename, 'w', encoding='utf-8')
        except IOError:
            print('Error: Failed to create setup.cfg')
            self.__file = None
            
    def close(self):
        if self.__file:
            self.__file.close()
            self.__file = None

    def write(self, value):
        if not self.__file:
            return
        self.__file.write(value)

    def write_section(self, name):
        if not self.__file:
            return
        self.__file.write('[%s]\n' % name)

    def write_value(self, name, value):
        if not self.__file:
            return
        self.__file.write('%s = %s\n' % (name, value))
        
    def write_list(self, name, value_list):
        if not self.__file:
            return
        self.__file.write('%s =\n' % name)
        for value in value_list:
            self.__file.write('    %s\n' % value)
        
    def write_dict(self, name, value_dict):
        if not self.__file:
            return
        self.__file.write('%s =\n' % name)
        for key in list(value_dict.keys()):
            self.__file.write('    %s = \n' % key)
            for value in value_dict[key]:
                self.__file.write('        %s\n' % value)

    def write_colon_value(self, name, value):
        if not self.__file:
            return
        self.__file.write('%s: %s\n' % (name, value))

    def write_colon_list(self, name, value_list):
        if not self.__file:
            return
        self.__file.write('%s:\n' % name)
        for value in value_list:
            self.__file.write('       %s\n' % value)
        
'''
    Sets up the data argument fields and sends them out to be written
'''
class CreateSetup(object):
    def __init__(self):
        # turn off warnings when deprecated modules are imported
        import warnings
        warnings.filterwarnings('ignore',category=DeprecationWarning)

        self.data = {}

        self.data['name'] = 'gramps'
        self.data['version'] = VERSION
        self.data['author'] = 'Donald N. Allingham'
        self.data['author-email'] = 'don@gramps-project.org'
        self.data['maintainer'] = 'Gramps Development Team'
        self.data['maintainer-email'] = 'benny.malengier@gmail.com'
        self.data['Home-page'] = 'http://gramps-project.org'
        self.data['summary'] = ('Gramps (Genealogical Research and Analysis '
                                'Management Programming System)')
        self.data['description'] = ('Gramps (Genealogical Research and '
                                    'Analysis Management Programming System) '
                                    'is a GNOME based genealogy program '
                                    'supporting a Python based plugin system.')
        self.data['download-url'] = 'http://gramps-project.org/download/'
        self.data['classifiers'] = sorted([x for x in all_classifiers])
        self.data['platforms'] = sorted(['Linux', 'FreeBSD', 'MacOS', 'Windows'])
        self.data['license'] = 'GPL v2 or greater'
        self.data['keywords'] = sorted(['Genealogy',
            'Pedigree',
            'Ancestry',
            'Birth',
            'Marriage',
            'Death',
            'Family',
            'Family-tree',
            'GEDCOM'])

        self.data['requires-Python'] = '>= 2.6.0'

        self.data['requires-dist'] = sorted([
            'pygtk2',
            'python3-cairo',
            'pygobject3',
            'librsvg2', 
            'pyexiv2 >= 0.3.0',
            'osm-gps-map >= 0.7.3',
            'python-osmgpsmap >= 0.7.3'])

        self.data['Requires-External'] = 'exiv2-devel (>=0.23)'

        self.data['obsoletes-dist'] = ['gramps < 3.5.0']

        self.data['project-url'] = [
            'Bug Tracker, http://bugs.gramps-project.org/', 
            'Documentation, http://www.gramps-project.org/wiki/index.php?title=Main_page',
            'Downloads, http://gramps-project.org/download/']

        exclude_list = ['gramps.guiQML', 
                        'gramps.guiQML.*', 
                        'gramps.test', 
                        'gramps.test.*', 
                        'gramps.webapp', 
                        'gramps.webapp.*']
        packages = find_packages(exclude=exclude_list)
        self.data['packages'] = sorted(packages)
        
        data_list = ['data', 'glade', 'images', 'plugins', 'webapp']
        package_data = []
        for top_dir in data_list:
            package_data += find_child_dir(top_dir, root='gramps')
        self.data['package_data'] = {'gramps': [dir_name + '/*.*' 
                                    for dir_name in package_data]}
        
        extra_list = ['debian', 'docs', 'help', 'mac', 'test', 'windows',
                      'gramps/test']
        extra_files = []
        for top_dir in extra_list:
            extra_files += find_child_dir(top_dir)
        self.data['extra_files'] = [dir_name + '/*' 
                                    for dir_name in extra_files]

        self.data['scripts'] = ['gramps.sh']

        resources = [
            'build/data/ gramps.desktop = {data}/share/applications',
            'build/data/ gramps.xml = {data}/share/mime/packages',
            'build/data/ gramps.keys = {data}/share/mime-info',
            'data/ gramps.mime = {data}/share/mime-info',
            'data/ *.png = {datadir}/icons/gnome/48x48/mimetypes',
            'data/ *.svg = {datadir}/icons/gnome/scalable/mimetypes',
            'gramps/images/ gramps.png = {icon}',
            'build/data/man/ gramps.1.gz = {man}/man1',
            'build/data/man/cs/ gramps.1.gz = {man}/cs/man1',
            'build/data/man/fr/ gramps.1.gz = {man}/fr/man1',
            'build/data/man/nl/ gramps.1.gz = {man}/nl/man1',
            'build/data/man/pl/ gramps.1.gz = {man}/pl/man1',
            'build/data/man/sv/ gramps.1.gz = {man}/sv/man1',
            'example/**/*.* = {doc}',
            'AUTHORS = {doc}',
            'COPYING = {doc}',
            'FAQ = {doc}',
            'INSTALL = {doc}',
            'LICENSE = {doc}',
            'MANIFEST = {doc}',
            'NEWS = {doc}',
            'README = {doc}',
            'TODO = {doc}',
            'TestPlan.txt = {doc}',
            'create_setup_cfg.py = {purelib}',
            'setup.cfg = {purelib}',
            'setup.py = {purelib}',
            'setup_custom.py = {purelib}']

        for po in glob.glob(os.path.join(PO_DIR, '*.po')):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(MO_DIR, lang, 'gramps.mo')
            directory = os.path.dirname(mo)
            mach_obj_fname = os.path.basename(mo)
            resources.append('%s/ %s = {datadir}/locale/%s/gramps.mo' % (
                    directory, mach_obj_fname, lang))
        self.data['resources'] = resources

    def main(self):
        
        create_gramps_trans()
        create_gramps_man()
        create_gramps_intl()

        cw = ConfigWriter()
        try:
            cw.open(_FILENAME)
        except (IOError, OSError):
            self.__file = None
        
        cw.write_section('metadata')
        
        for name in ('name', 'version', 'author', 'author-email', 'maintainer', 
                     'maintainer-email', 'Home-page', 'summary', 'description',
                     'download-url', 'license'):
            cw.write_value(name, self.data[name])

        for name in ['classifiers']:
            cw.write_list(name, self.data[name])
        cw.write('\n')

        for name in ('platforms', 'keywords',):
            cw.write_list(name, self.data[name])

        for name in ('requires-Python',):
            cw.write_colon_value(name, self.data[name])

        for name in ['requires-dist', 'obsoletes-dist']:
            cw.write_list(name, self.data[name])

        for name in ('Requires-External',):
            cw.write_colon_value(name, self.data[name])

        for name in ('project-url',):
            cw.write_colon_list(name, self.data[name])
        cw.write('\n')

        cw.write_section('files')

        for name in ('packages', 'scripts', 'resources', 'extra_files'):
            cw.write_list(name, self.data[name])

        for name in ('package_data',):
            cw.write_dict(name, self.data[name])
        cw.write('\n')

#        cw.write_section('Global')
#        cw.write_value('setup_hooks', 'setup_custom.customize_config')
#
#        cw.write_section('build')
#        cw.write_value('pre-hook.trans', 'setup_custom.build_trans')
#        cw.write_value('pre-hook.man', 'setup_custom.build_man')
#        cw.write_value('post-hook.intl', 'setup_custom.build_intl')
#
#        cw.write_section('install_scripts')
#        cw.write_value('pre-hook.template', 'setup_custom.install_template')
#
#        cw.write_section('install')
#        cw.write_value('post-hook.update', 'setup_custom.update_mime')
#
#        cw.write_section('sdist')
#        cw.write_value('manifest-builders', 'setup_custom.manifest_builder')

        cw.close()

if __name__ == '__main__':
    cs = CreateSetup()
    cs.main()
