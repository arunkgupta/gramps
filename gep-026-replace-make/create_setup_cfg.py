
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
import os
import codecs

#------------------------------------------------
#        Distutils2, Packaging, Distutils modules
#------------------------------------------------
try:
    from distutils2.util import find_packages, convert_path
except ImportError:
    try:
        from packaging.util import find_packages, convert_path
    except ImportError:
        try:
            from distutils.util import find_packages, convert_path
        except ImportError:
           # no Distutils, Distutils2, packaging is NOT installed!
           sys.exit('Distutils2, Packaging, or Distutils is Required!\n',
                    'You need to have one of these installed.')

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
config_file = codecs.open('setup.cfg', 'w', encoding='utf-8')
config_file.write('''[metadata]
name = gramps
version = 3.5.0
summary = Gramps (Genealogical Research and Analysis Management Programming System)
description = Gramps (Genealogical Research and Analysis Management Programming System) is a GNOME based genealogy program supporting a Python based plugin system.
Home-page = http://gramps-project.org
download-url = http://gramps-project.org/download/
author = Donald N. Allingham
author-email = don@gramps-project.org
maintainer = Gramps Development Team
maintainer-email = benny.malengier@gmail.com
license = GPL v2 or greater
classifiers =
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
platforms =
    FreeBSD
    Linux
    MacOS
    Windows
keywords =
    Ancestry
    Birth
    Death
    Family
    Family-tree
    GEDCOM
    Genealogy
    Marriage
    Pedigree
requires-Python: >= 2.6.0
requires-dist =
    distutils2
    librsvg2
    osm-gps-map >= 0.7.3
    pyexiv2 >= 0.3.0
    pygtk2 >= 2.0
    python-osmgpsmap >= 0.7.3
obsoletes-dist =
    gramps < 3.5.0
Requires-External: exiv2-devel (>=0.22)
project-url:
       Bug Tracker, http://bugs.gramps-project.org/
       Documentation, http://www.gramps-project.org/wiki/index.php?title=Main_page
       Downloads, http://gramps-project.org/download/

[files]
packages =
''')

exclude_list = ['gramps.guiQML', 
                'gramps.guiQML.*', 
                'gramps.test', 
                'gramps.test.*', 
                'gramps.webapp', 
                'gramps.webapp.*']
packages = find_packages(exclude=exclude_list)
for package in sorted(packages):
    config_file.write('    %s\n' % package)
        
config_file.write('''package_data =
    gramps =
''')
# excludes webapp, gramps-connect, as this will be packaged as gramps-connect...
data_list = ['data', 'glade', 'images', 'plugins']
package_data = []
for top_dir in data_list:
    package_data += find_child_dir(top_dir, root='gramps')
for dir_name in package_data:
    config_file.write('        %s/*.*\n' % dir_name)

config_file.write('extra_files =\n')
extra_list = ['debian', 'docs', 'help', 'mac', 'test', 'windows', 'gramps/test']
extra_files = []
for top_dir in extra_list:
    extra_files += find_child_dir(top_dir)
for dir_name in extra_files:
    config_file.write('    %s/*\n' % dir_name)

config_file.write('''scripts =
    gramps.sh
resources =
    data/ gramps.mime = {datadir}/mime-info
    data/ *.png = {datadir}/icons/gnome/48x48/mimetypes
    data/ *.svg = {datadir}/icons/gnome/scalable/mimetypes
    gramps/images/ gramps.png = {icon}
    example/**/*.* = {doc}
    AUTHORS = {doc}
    COPYING = {doc}
    FAQ = {doc}
    INSTALL = {doc}
    LICENSE = {doc}
    NEWS = {doc}
    README = {doc}
    TODO = {doc}

[global]
setup_hooks = setup_custom.customize_config

[sdist]
manifest-builders = setup_custom.manifest_builder

[build]
pre-hook.trans = setup_custom.build_trans
pre-hook.man = setup_custom.build_man
pre-hook.intl = setup_custom.build_intl

[install_dist]
pre-hook.template = setup_custom.install_template
''')
config_file.close()
