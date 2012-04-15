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
import os
import codecs
import shutil

#------------------------------------------------
#        Gramps modules
#------------------------------------------------
from classifiers import all_classifiers

#------------------------------------------------
#        Distutils/ Distutils2 modules
#------------------------------------------------
from distutils2 import logger
from distutils2.util import find_packages, convert_path

gramps_in   = 'gramps.sh.in'
gramps_data = 'gramps.sh'
if (not os.path.exists(gramps_data) and os.path.exists(gramps_in)):
    shutil.copy(gramps_in, gramps_data)

const_in   = os.path.join('gramps', 'const.py.in')
const_data = os.path.join('gramps', 'const.py')
if (not os.path.exists(const_data) and os.path.exists(const_in)):
    shutil.copy(const_in, const_data)

#------------------------------------------------
#        Constants
#------------------------------------------------
_FILENAME = 'setup.cfg'
VERSION = '3.5.0'

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

    def write_section(self, name):
        if not self.__file:
            return
        self.__file.write(u'[%s]\n' % name)

    def write_value(self, name, value):
        if not self.__file:
            return
        self.__file.write(u'%s = %s\n' % (name, value))

    def write_list(self, name, value_list):
        if not self.__file:
            return
        self.__file.write(u'%s =\n' % name)
        for value in value_list:
            self.__file.write(u'    %s\n' % value)
        
    def write_dict(self, name, value_dict):
        if not self.__file:
            return
        self.__file.write(u'%s =\n' % name)
        for key in value_dict.keys():
            self.__file.write(u'    %s = \n' % key)
            for value in value_dict[key]:
                self.__file.write(u'        %s\n' % value)

    def write_colon_value(self, name, value):
        if not self.__file:
            return
        self.__file.write(u'%s: %s\n' % (name, value))

    def write_colon_list(self, name, value_list):
        if not self.__file:
            return
        self.__file.write(u'%s:\n' % name)
        for value in value_list:
            self.__file.write(u'    %s\n' % value)
        
class CreateSetup(object):
    def __init__(self):
        # turn off warnings when deprecated modules are imported
        import warnings
        warnings.filterwarnings("ignore",category=DeprecationWarning)

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
        self.data['platforms'] = ['Linux', 'FreeBSD', 'MacOS', 'Windows']
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
        self.data['requires-dist'] = sorted([
            'pygtk2',
            'pycairo',
            'pygobject2'])

        self.data['provides-dist'] = None

        self.data['obsoletes-dist'] = [
            'gramps < %s' % VERSION]

        self.data['requires-Python'] = '>= 2.6'

        self.data['project-url'] = [
            'Repository, https://gramps.svn.sourceforge.net/svnroot/gramps/trunk',
            'Wiki, http://www.gramps-project.org/wiki/index.php?title=Main_page',
            'Bug tracker, http://bugs.gramps-project.org']

        exclude_list = ['gramps.guiQML', 
                        'gramps.guiQML.*', 
                        'gramps.test', 
                        'gramps.test.*', 
                        'gramps.webapp', 
                        'gramps.webapp.*']
        packages = find_packages(exclude=exclude_list)
        self.data['packages'] = sorted(packages)
        
        data_list = ['glade', 'images', 'plugins']
        package_data = []
        for top_dir in data_list:
            package_data += find_child_dir(top_dir, root='gramps')
        self.data['package_data'] = {'gramps': [dir_name + '/*.*' 
                                    for dir_name in package_data]}
        
        extra_list = ['debian', 'docs', 'help', 'mac', 'po', 'test', 'windows',
                      'gramps/test', 'gramps/webapp']
        extra_files = []
        for top_dir in extra_list:
            extra_files += find_child_dir(top_dir)
        self.data['extra_files'] = [dir_name + '/*' 
                                    for dir_name in extra_files]

        self.data['scripts'] = ['gramps.sh']

        self.data['resources'] = [
            'data/ gramps.desktop = {data}/share/applications',
            'data/ gramps.xml = {data}/share/mime/packages',
            'data/ gramps.mime = {data}/share/mime-info',
            'data/ gramps.keys = {data}/share/mime-info',
            'data/ *.png = {data}/share/icons/gnome/48x48/mimetypes',
            'data/ *.svg = {data}/share/icons/gnome/scalable/mimetypes',
            'gramps/images/ gramps.png = {icon}',
            'data/man/ gramps.1.in = {man}/man1',
            'data/man/cs/ gramps.1.in = {man}/cs/man1',
            'data/man/fr/ gramps.1.in = {man}/fr/man1',
            'data/man/nl/ gramps.1.in = {man}/nl/man1',
            'data/man/pl/ gramps.1.in = {man}/pl/man1',
            'data/man/sv/ gramps.1.in = {man}/sv/man1',
            'example/**/*.* = {doc}',
            'COPYING = {doc}',
            'FAQ = {doc}',
            'INSTALL = {doc}',
            'LICENSE = {doc}',
            'NEWS = {doc}',
            'README = {doc}',
            'TODO = {doc}']

    def main(self):
        
        cw = ConfigWriter()
        cw.open(_FILENAME)
        
        cw.write_section('metadata')
        
        for name in ('name', 'version', 'author', 'author-email', 'maintainer', 
                     'maintainer-email', 'Home-page', 'summary', 'description',
                     'download-url', 'license'):
            cw.write_value(name, self.data[name])

        for name in ('classifiers', 'platforms', 'keywords', 'requires-dist',
                     'provides-dist', 'obsoletes-dist'):
            if self.data[name]:
                cw.write_list(name, self.data[name])

        for name in ['requires-Python']:
            cw.write_colon_value(name, self.data[name])

        for name in ['project-url']:
            cw.write_colon_list(name, self.data[name])

        cw.write_section('files')

        for name in ('packages', 'scripts', 'resources', 'extra_files'):
            cw.write_list(name, self.data[name])

        for name in ('package_data',):
            cw.write_dict(name, self.data[name])

        cw.write_section('global')
        cw.write_value('setup_hooks', 'setup_custom.customize_config')

        cw.write_section('build')
        cw.write_value('post-hook.itnl', 'setup_custom.build_itnl')

        cw.write_section('install_scripts')
        cw.write_value('pre-hook.template', 'setup_custom.install_template')

        cw.write_section('sdist')
        cw.write_value('manifest-builders', 'setup_custom.manifest_builder')

        cw.close()

if __name__ == "__main__":
    cs = CreateSetup()
    cs.main()
