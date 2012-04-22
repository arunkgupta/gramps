#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2012 Nick Hall
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
#
# $Id$

#------------------------------------------------
#        python modules
#------------------------------------------------
import os, sys, glob, shutil
sys.path.append(os.getcwd())

#------------------------------------------------
#        Distutils2 modules
#------------------------------------------------
from distutils2.util import newer

def customize_config(metadata):
    '''
    Global hook.
    '''
    print('GLOBAL')

def build_trans(build_cmd):
    '''
    Pre-Build hook to build all language files for Gramps translations
    '''
    print('BUILD')

    for po in glob.glob(os.path.join('po', '*.po')):
        lang = os.path.basename(po[:-3])
        mo = os.path.join('po', lang, 'gramps.mo')
        directory = os.path.dirname(mo)
        if not os.path.exists(directory):
            os.makedirs(directory)

        if newer(po, mo):
            try:
                bash_string = 'msgfmt %s/%s.po -o %s' % (PO_DIR, lang, mo)
                result = subprocess.call(bash_string, shell=True)
                if result != 0:
                    raise Warning, "msgfmt returned %d" % result
            except Exception, e:
                sys.stdout.write("Building language translation files failed.")
                sys.stdout.write("Error: %s" % str(e))
                sys.exit(1)

def build_man(build_cmd):
    '''
    Pre-build hook to compress man files into gzipped format
    '''

    for dir, dirs, files in os.walk(os.path.join('data', 'man')):
        file = False
        for f in files:
            file = os.path.join(dir, f)
            if f == 'gramps.1.in':
                break
        if file:
            newfile = os.path.join(dir, 'gramps.1')
            shutil.copy(file, newfile)

            import gzip
            man_file_gz = os.path.join(dir, 'gramps.1.gz')
            if man_file_gz in files:
                if newer(newfile, man_file_gz):
                    os.remove(man_file_gz)
                else:
                    file = False
                    os.remove(newfile)
            while file:
                f_in = open(newfile, 'rb')
                f_out = gzip.open(man_file_gz, 'wb')
                f_out.writelines(f_in)
                f_out.close()
                f_in.close()
                print >> sys.stdout, 'Compressing gramps man files into gzipped format.'

                os.remove(newfile)
                file = False

def build_intl(build_cmd):
    '''
    Post-build hook to run internationisation scripts.
    '''

    if not os.path.exists(os.path.join('data', 'gramps.desktop')):
        os.system('intltool-merge -d po/ data/gramps.desktop.in data/gramps.desktop')

    if not os.path.exists(os.path.join('data', 'gramps.xml')):
        os.system('intltool-merge -x po/ data/gramps.xml.in data/gramps.xml')

    if not os.path.exists(os.path.join('data', 'gramps.keys')):
        os.system('intltool-merge -k po/ data/gramps.keys.in data/gramps.keys')

def install_template(install_cmd):
    '''
    Pre-install hook to populate template files.
    '''
    print('INSTALL', install_cmd.install_dir)

def manifest_builder(distribution, manifest):
    '''
    Manifest builder.
    '''
    print("manifest_builder", manifest.files)