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
BUILD_DIR = 'build'

PO_DIR = 'po'
MO_DIR = os.path.join(BUILD_DIR, 'mo')

all_classifiers = set()

all_classifiers.update([
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Environment :: MacOS X',
    'Environment :: Plugins',
    'Environment :: Web Environment',
    'Environment :: Win32 (MS Windows)',
    'Environment :: X11 Applications :: GTK',
    'Framework :: Django',
    'Intended Audience :: Education',
    'Intended Audience :: End Users/Desktop',
    'Intended Audience :: Other Audience',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: Bulgarian',
    'Natural Language :: Catalan',
    'Natural Language :: Chinese (Simplified)',
    'Natural Language :: Croatian',
    'Natural Language :: Czech',
    'Natural Language :: Danish',
    'Natural Language :: Dutch',
    'Natural Language :: English',
    'Natural Language :: Esperanto',
    'Natural Language :: Finnish',
    'Natural Language :: French',
    'Natural Language :: German',
    'Natural Language :: Hebrew',
    'Natural Language :: Hungarian',
    'Natural Language :: Italian',
    'Natural Language :: Japanese',
    'Natural Language :: Norwegian',
     'Natural Language :: Polish',
     'Natural Language :: Portuguese (Brazilian)',
    'Natural Language :: Portuguese',
    'Natural Language :: Russian',
    'Natural Language :: Slovak',
    'Natural Language :: Slovenian',
    'Natural Language :: Spanish',
    'Natural Language :: Swedish',
    'Natural Language :: Ukranian',
    'Natural Language :: Vietnamese',
    'Operating System :: MacOS',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: Other OS',
    'Operating System :: POSIX :: BSD',
    'Operating System :: POSIX :: Linux',
    'Operating System :: POSIX :: SunOS/Solaris',
    'Operating System :: Unix',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Topic :: Database',
    'Topic :: Desktop Environment :: Gnome',
    'Topic :: Education',
    'Topic :: Multimedia',
    'Topic :: Other/Nonlisted Topic',
    'Topic :: Scientific/Engineering :: Visualization',
    'Topic :: Sociology :: Genealogy'
    ])

#------------------------------------------------
#        Helper functions
#------------------------------------------------
def create_gramps_trans():
    '''
    Translate the language files into gramps.mo
    '''
    for po in glob.glob(os.path.join(PO_DIR, '*.po')):
        lang = os.path.basename(po[:-3])
        mo = os.path.join(MO_DIR, lang, 'gramps.mo')
        directory = os.path.dirname(mo)
        if not(os.path.isdir(directory) or os.path.islink(directory)):
            print('Creating directory: %s' % directory)
            os.makedirs(directory)

        if newer(po, mo):
            try:
                bash_string = 'msgfmt %s/%s.po -o %s' % (PO_DIR, lang, mo)
                result = subprocess.call(bash_string, shell=True)
                if result != 0:
                    print(('msgfmt returned %d' % result))
            except Exception, e:
                print('Building language translation files failed.')
                print(('Error: %s' % str(e)))
                sys.exit(1)
            print(('Compiling %s >> %s...' % (po, mo)))

def create_gramps_man():
    '''
    compresses Gramps manual files
    '''
    for dir, dirs, files in os.walk(os.path.join('data', 'man')):
        file = False
        for f in files:
            if f == 'gramps.1.in':
                file = os.path.join(dir, f)
                break

        if file:
            newdir = os.path.join(BUILD_DIR, dir)
            if not(os.path.isdir(newdir) or os.path.islink(newdir)):
                os.makedirs(newdir)

            newfile = os.path.join(newdir, 'gramps.1')
            shutil.copy(file, newfile)

            import gzip
            man_file_gz = os.path.join(newdir, 'gramps.1.gz')
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

                os.remove(newfile)
                file = False

def create_gramps_intl():
    '''
    merge translation files into desktop and mime files
    '''
    newdir = os.path.join(BUILD_DIR, 'data')
    if not(os.path.isdir(newdir) or os.path.islink(newdir)):
        os.makedirs(newdir)

    for searchfile in ['gramps.desktop', 'gramps.keys', 'gramps.xml']:
        data_file = os.path.join('data', searchfile) + '.in'

        newfile = os.path.join(newdir, searchfile)
        if not os.path.exists(newfile):
            bash_string = None

            # gramps desktop icon
            if searchfile.endswith('.desktop'):
                bash_string = 'intltool-merge -d %s/ %s %s' % (PO_DIR, data_file, newfile)

            # gramps mime
            elif searchfile.endswith('.keys'):
                bash_string = 'intltool-merge -k %s/ %s %s' % (PO_DIR, data_file, newfile)

            # gramps mime
            elif searchfile.endswith('.xml'):
                bash_string = 'intltool-merge -x %s/ %s %s' % (PO_DIR, data_file, newfile)

            if bash_string:
                result = subprocess.call(bash_string, shell=True)
                if result != 0:
                    print('ERROR: %s was not merged into the translation files!' % searchfile)
                    sys.exit(1)

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
    Pre-Build hook to build all language files for Gramps translations
    '''
    print('BUILD')

    crete_gramps_trans()

def build_man(build_cmd):
    '''
    Pre-build hook to compress man files into gzipped format
    '''

    create_gramps_man()

def build_intl(build_cmd):
    '''
    Post-build hook to run internationisation scripts.
    '''

    create_gramps_intl()

def install_template(install_cmd):
    '''
    Pre-install hook to populate template files.
    '''
    print(('INSTALL', install_cmd.install_dir))

def manifest_builder(distribution, manifest):
    '''
    Manifest builder.
    '''
    print(("manifest_builder", manifest.files))
