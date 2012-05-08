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
#        Python modules
#------------------------------------------------
import os, sys, glob, shutil, subprocess

#------------------------------------------------
#        gramps modules
#------------------------------------------------
from xx_distutils import *

#-------------------------------------------
#        Distutils2, Packaging, Distutils modules
#-------------------------------------------
try:
    from distutils2 import logger as _LOG
    from distutils2.util import convert_path, newer
except ImportError:
    try:
        from packaging import logger as _LOG
        from packaging.util import convert_path, newer
    except ImportError:
        try:
            from distutils import log as _LOG
            from distutils.util import convert_path, newer
        except ImportError:
            # no Distutils, Distutils2, packaging is NOT installed!
            sys.exit('Distutils2, Packaging, or Distutils is Required!\n',
                     'You need to have one of these installed.')

#------------------------------------------------
#        Constants
#------------------------------------------------
PO_DIR = 'po'

#------------------------------------------------
#        Setup/ Command Hooks
#------------------------------------------------
def customize_config(metadata):
    '''
    Global hook.
    '''
    print('GLOBAL')

def build_trans(build_cmd):
    '''
    Translate the language files into gramps.mo
    '''
    data_files = build_cmd.distribution.data_files
    for po in glob.glob(os.path.join(PO_DIR, '*.po')):
        lang = os.path.basename(po[:-3])
        mo = os.path.join(build_cmd.build_base, 'mo', lang, '%s.mo' % PACKAGENAME)

        directory = os.path.dirname(mo)
        if not(os.path.isdir(directory) or os.path.islink(directory)):
            os.makedirs(directory)

        if newer(po, mo):
            cmd = 'msgfmt %s/%s.po -o %s' % (PO_DIR, lang, mo)
            if os.system(cmd) != 0:
                raise SystemExit('Error while compiling translation files.')
            print(('Compiling %s >> %s...' % (po, mo)))

            dest = os.path.join('{datadir}', 'locale', lang, 'LC_MESSAGES', '%s.mo' % PACKAGENAME)
            data_files[mo] = dest            

def build_man(build_cmd):
    '''
    Compresses Gramps manual files
    '''
    data_files = build_cmd.distribution.data_files
    build_data = os.path.join(build_cmd.build_base, 'data')
    for dir, dirs, files in os.walk(os.path.join('data', 'man')):
        file = False
        for f in files:
            searchfile = '%s.1.in' % PACKAGENAME
            if f == searchfile:
                file = os.path.join(dir, f)
                break

        if file:
            newdir = os.path.join(build_cmd.build_base, dir)
            if not(os.path.isdir(newdir) or os.path.islink(newdir)):
                os.makedirs(newdir)

            newfile = os.path.join(newdir, '%s.1' % PACKAGENAME)
            shutil.copy(file, newfile)

            import gzip
            man_file_gz = os.path.join(newdir, '%s.1.gz'% PACKAGENAME)
            if os.path.exists(man_file_gz):
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

                print('Compiling manual file, %s...' % man_file_gz)

                os.remove(newfile)
                file = False

            lang = dir[8:]
            src = os.path.join(build_data, 'man', lang, '%s.1.gz' % PACKAGENAME)
            target = os.path.join('{man}', lang, 'man1')
            data_files[src] = target

def build_intl(build_cmd):
    '''
    Merge translation files into desktop and mime files
    '''
    for filename, option in [
        (os.path.join('data', '%s.desktop' % PACKAGENAME),                   '-d'),
        (os.path.join('data', '%s.keys' % PACKAGENAME),                      '-k'),
        (os.path.join('data', '%s.xml' % PACKAGENAME),                       '-x'),
        (os.path.join('%s', 'data', 'tips.xml' % PACKAGENAME),               '-x'),
        (os.path.join('%s', 'plugins', 'lib', 'holidays.xml' $ PACKAGENAME), '-x')]:

        newfile = os.path.join(build_cmd.build_base, filename)
        newdir = os.path.dirname(newfile)
        if not(os.path.isdir(newdir) or os.path.islink(newdir)):
            os.makedirs(newdir)

        datafile = filename + '.in'
        if (not os.path.exists(newfile) and os.path.exists(datafile)):
            cmd = '/usr/bin/intltool-merge %s po/ %s %s' % (
                    option, datafile, newfile)
            if os.system(cmd) != 0:
                raise SystemExit('ERROR: while building XDG files.')

    data_files = build_cmd.distribution.data_files
    build_data = os.path.join(build_cmd.build_base, 'data')
    data_files[os.path.join(build_data, '%s.desktop' % PACKAGENAME)] = os.path.join('{datadir}', 'applications')
    data_files[os.path.join(build_data, '%s.xml' % PACKAGENAME)]     = os.path.join('{datadir}', 'mime', 'packages')
    data_files[os.path.join(build_data, '%s.keys' % PACKAGENAME)]    = os.path.join('{datadir}', 'mime-info')

def install_template(install_cmd):
    '''
    Pre-install hook to populate template files.
    '''
    write_gramps_sh(install_cmd.install_lib, 
                    install_cmd.distribution.metadata['name'])
    write_const_py()

def write_gramps_sh(install_lib, package):
    f = open('%s.sh', 'w' % PACKAGENAME)
    f.write('#! /bin/sh\n')
    f.write('export GRAMPSDIR=%s%s\n' % (install_lib, PACKAGENAME))
    f.write('exec %s -O $GRAMPSDIR/%s.py "$@"\n' % (sys.executable, PACKAGENAME))
    f.close()

def write_const_py():
    const_py_in    = os.path.join(PACKAGENAME, 'const.py.in')
    const_py_data  = os.path.join(PACKAGENAME, 'const.py')
    if not os.path.exists(const_py_data):
        shutil.copy(const_py_in, const_py_data)

def manifest_builder(distribution, manifest):
    '''
    Manifest builder.
    '''
    manifest.clear()
    for dirpath, dirnames, filenames in os.walk(os.curdir):
        svn_path = os.path.join(dirpath, '.svn', 'text-base', '*.svn-base')
        files = [os.path.join(dirpath, os.path.basename(x)[:-9]) 
                 for x in glob.glob(svn_path)]
        manifest.extend(files)
        if '.svn' in dirnames:
            dirnames.remove('.svn')
