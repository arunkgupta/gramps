# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
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
# $Id$

from distutils.core import setup
import os
import imp

from gramps.const import VERSION as GRAMPS_VERSION

def is_package(path):
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
        )

def find_packages(path, base="" ):
    """ Find all packages in path """
    packages = {}
    for item in os.listdir(path):
        dir = os.path.join(path, item)
        if is_package( dir ):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir
            packages.update(find_packages(dir, module_name))
    return packages
    
packages = find_packages("gramps")

def non_python_files(path):
    """ Return all non-python-file filenames in path """
    result = []
    all_results = []
    module_suffixes = [info[0] for info in imp.get_suffixes()]
    ignore_dirs = ['.', 'guiQML']
    for item in os.listdir(path):
        name = os.path.join(path, item)
        if (
            os.path.isfile(name) and
            os.path.splitext(item)[1] not in module_suffixes
            ):
            result.append(name)
        elif os.path.isdir(name) and item.lower() not in ignore_dirs:
            all_results.extend(non_python_files(name))
    if result:
        all_results.append((path, result))
    return all_results

data_files = non_python_files('gramps/glade')
data_files = non_python_files('gramps/images')

setup (
    name             = 'gramps',
    version          = GRAMPS_VERSION,
    author           = 'Gramps Development Team',
    author_email     = 'benny.malengier@gmail.com',
    url              = 'http://gramps-project.org/',
    download_url     = 'http://gramps-project.org/download/',
    license          = "GPLv2 or greater",
    description      = "Gramps (Genealogical Research and Analysis Management Programming System)",
    long_description = ('Gramps(Genealogical Research and Analysis Management Programming '
                        'System) is a GNOME based genealogy program supporting a Python based plugin system.'),
    data_files       = data_files,
    package_dir      = packages,
    packages         = packages.keys(),
    platforms        = ['Linux', 'FreeBSD', 'Mac OSX', 'Windows'],
)
