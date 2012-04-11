#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2012 Rob G. Healey <robhealey1@gmail.com>
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

# $I$

#------------------------------------------------
#        Python modules
#------------------------------------------------
import os, shutil
import codecs
from ConfigParser import RawConfigParser

#------------------------------------------------
#        Distutils/ Distutils2 modules
#------------------------------------------------
from distutils.core import setup

# copy const file from gramps/const.py.in to gramps/const.py
const_in_file = os.path.join('gramps', 'const.py.in')
const_file    = os.path.join('gramps', 'const.py')
if (os.path.exists(const_in_file) and not os.path.exists(const_file)):
    shutil.copy(const_in_file, const_file)

# copy gramps script launcher from gramps.sh.in to gramps.sh
gramps_script_in   = 'gramps.sh.in'
gramps_script_file = 'gramps.sh'
if (os.path.exists(gramps_script_in) and not os.path.exists(gramps_script_file)):
    shutil.copy(gramps_script_in, gramps_script_file)


def split_multiline(value):
    return [element for element in (line.strip() for line in value.split('\n'))
            if element]

def split_elements(value):
    return [v.strip() for v in value.split(',')]

def split_files(value):
    return [str(v) for v in split_multiline(value)]


def cfg_to_args(path='setup.cfg'):
    opts_to_args = {
        'metadata': (
            ('name', 'name', None),
            ('version', 'version', None),
            ('author', 'author', None),
            ('author-email', 'author_email', None),
            ('maintainer', 'maintainer', None),
            ('maintainer-email', 'maintainer_email', None),
            ('home-page', 'url', None),
            ('summary', 'description', None),
            ('description', 'long_description', None),
            ('download-url', 'download_url', None),
            ('classifier', 'classifiers', split_multiline),
            ('platform', 'platforms', split_multiline),
            ('license', 'license', None),
            ('keywords', 'keywords', split_elements),
            ),
        'files': (
            ('packages', 'packages', split_files),
            ('modules', 'py_modules', split_files),
            ('scripts', 'scripts', split_files),
            ('package_data', 'package_data', split_files),
            ),
        }
    config = RawConfigParser()
    config.optionxform = lambda x: x.lower().replace('_', '-')
    fp = codecs.open(path, encoding='utf-8')
    try:
        config.readfp(fp)
    finally:
        fp.close()
    kwargs = {}
    for section in opts_to_args:
        for optname, argname, xform in opts_to_args[section]:
            if config.has_option(section, optname):
                value = config.get(section, optname)
                if xform:
                    value = xform(value)
                kwargs[argname] = value
    # Handle `description-file`
    if ('long_description' not in kwargs and
            config.has_option('metadata', 'description-file')):
        filenames = config.get('metadata', 'description-file')
        for filename in split_multiline(filenames):
            descriptions = []
            fp = open(filename)
            try:
                descriptions.append(fp.read())
            finally:
                fp.close()
        kwargs['long_description'] = '\n\n'.join(descriptions)
    # Handle `package_data`
    if 'package_data' in kwargs:
        package_data = {}
        for data in kwargs['package_data']:
            key, value = data.split('=', 1)
            globs = package_data.setdefault(key.strip(), [])
            globs.extend(split_elements(value))
        kwargs['package_data'] = package_data
    return kwargs

setup_kwargs = cfg_to_args('setup.cfg')
setup(**setup_kwargs)
