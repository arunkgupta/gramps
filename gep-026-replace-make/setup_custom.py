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
import os, sys, glob, codecs
import commands

from fractions import Fraction

#-------------------------------------------
#        Distutils2, Packaging modules
#-------------------------------------------
try:
    from distutils2.util import convert_path, newer
except ImportError:
    try:
        from packaging.util import convert_path, newer
    except ImportError:
        # no Distutils, Distutils2, packaging is NOT installed!
        raise SystemExit('Distutils2, Packaging, or Distutils is Required!\n',
                         'You need to have one of these installed.')

#------------------------------------------------
#        Constants
#------------------------------------------------
PO_DIR = 'po'

#------------------------------------------------
#        helper function
#------------------------------------------------
def intltool_version():
    '''
    Return the version of intltool as a tuple.
    '''
    cmd = 'intltool-update --version | head -1 | cut -d" " -f3'
    retcode, version_str = commands.getstatusoutput(cmd)
    if retcode != 0:
        return None
    else:
        return tuple([int(num) for num in version_str.split('.')])

#------------------------------------------------
#        Setup/ Command Hooks
#------------------------------------------------
intltool_merge_files = None

def customize_config(content):
    '''
    Global hook.
    '''
    global intltool_merge_files
    intltool_merge_files = get_field(content, 'x-intltool-merge')

def get_field(content, key):
    result = []
    field = content['files'].get(key)
    if field:
        for entry in field.split('\n'):
            if entry:
                if '=' in entry:
                    entry = [item.strip() for item in entry.split('=')]
                result.append(entry)
    return result

def build_trans(build_cmd):
    '''
    Translate the language files into gramps.mo
    '''
    data_files = build_cmd.distribution.data_files
    for po in sorted(glob.glob(os.path.join(PO_DIR, '*.po'))):
        lang = os.path.basename(po[:-3])
        mo = os.path.join(build_cmd.build_base, 'mo', lang, 'gramps.mo')

        directory = os.path.dirname(mo)
        if not(os.path.isdir(directory) or os.path.islink(directory)):
            os.makedirs(directory)

        if newer(po, mo):
            cmd = 'msgfmt %s/%s.po -o %s' % (PO_DIR, lang, mo)
            if os.system(cmd) != 0:
                raise SystemExit('ERROR: Building language translation files failed.')
            print(('Compiling %s >> %s...' % (po, mo)))

        data_files[mo] = '{datadir}/locale/' + lang + '/LC_MESSAGES/gramps.mo'            

def build_man(build_cmd):
    '''
    Compresses Gramps manual files
    '''
    data_files = build_cmd.distribution.data_files
    build_data = build_cmd.build_base + '/data/'
    for dir, dirs, files in os.walk(os.path.join('data', 'man')):
        file = False
        for f in files:
            if f == 'gramps.1.in':
                file = os.path.join(dir, f)
                break

        if file:
            newdir = os.path.join(build_cmd.build_base, dir)
            if not(os.path.isdir(newdir) or os.path.islink(newdir)):
                os.makedirs(newdir)

            newfile = os.path.join(newdir, 'gramps.1')
            version = build_cmd.distribution.metadata['version']
            subst_vars = ((u'@VERSION@', version), )
            substitute_variables(file, newfile, subst_vars)

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

                print('Compiling manual file, %s...' % man_file_gz)

                os.remove(newfile)
                file = False

            lang = dir[8:]
            src = build_data + 'man' + lang + '/gramps.1.gz'
            target = '{man}' + lang + '/man1'
            data_files[src] = target

def build_intl(build_cmd):
    '''
    Merge translation files into desktop and mime files
    '''
    if intltool_version() < (0, 25, 0):
        return
    
    metadata = build_cmd.distribution.metadata
    data_files = build_cmd.distribution.data_files
    base = build_cmd.build_base

    merge_files = (('data/gramps.desktop',
                    '{datadir}/applications/gramps.desktop',
                    '-d'),
                    ('data/gramps.keys',
                    '{datadir}/mime-info/gramps.keys',
                    '-k'),
                    ('data/gramps.xml',
                    '{datadir}/mime/packages/gramps.xml',
                    '-x'))

    for in_file, target, option in merge_files:
        merge(base, in_file, option)
        data_files[base + '/' + in_file] = target

    for in_file in intltool_merge_files:
        merge(base, in_file, '-x', po_dir='/tmp')
        data_files[base + '/' + in_file] = '{purelib}/' + in_file

def merge(build_base, filename, option, po_dir='po'):
    filename = convert_path(filename)
    newfile = os.path.join(build_base, filename)
    newdir = os.path.dirname(newfile)
    if not(os.path.isdir(newdir) or os.path.islink(newdir)):
        os.makedirs(newdir)

    datafile = filename + '.in'
    if (not os.path.exists(newfile) and os.path.exists(datafile)):
        cmd = ('intltool-merge %(opt)s %(po_dir)s %(in_file)s %(out_file)s') % {
                'opt' : option, 
                'po_dir' : po_dir,
                'in_file' : datafile, 
                'out_file' : newfile}
        if os.system(cmd) != 0:
            raise SystemExit('ERROR: %s was not merged into the translation files!\n' 
                                                                 % newfile)

def install_template(install_cmd):
    '''
    Pre-install hook to populate template files.
    '''
    write_gramps_sh(install_cmd)
    write_const_py(install_cmd)

def write_gramps_sh(install_cmd):
    f = open('gramps.sh', 'w')
    f.write('#! /bin/sh\n')
    package = 'gramps'
    f.write('export GRAMPSDIR=%sgramps\n' % install_cmd.install_lib)
    f.write('exec %s -O $GRAMPSDIR/gramps.py "$@"\n' % sys.executable)
    f.close()

def write_const_py(install_cmd):
    const_py_in = os.path.join('gramps', 'const.py.in')
    const_py = os.path.join('gramps', 'const.py')

    version = install_cmd.distribution.metadata['version']
    prefix = install_cmd.install_base
    sysconfdir = os.path.join(prefix, 'etc') # Is this correct?
    
    subst_vars = ((u'@VERSIONSTRING@', version), 
                  (u'@prefix@', prefix),
                  (u'@sysconfdir@', sysconfdir))
                  
    substitute_variables(const_py_in, const_py, subst_vars)

def substitute_variables(filename_in, filename_out, subst_vars):
    f_in = codecs.open(filename_in, encoding='utf-8')
    f_out = codecs.open(filename_out, encoding='utf-8', mode='w')
    for line in f_in:
        for variable, substitution in subst_vars:
            line = line.replace(variable, substitution)
        f_out.write(line)
    f_in.close()
    f_out.close()

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
