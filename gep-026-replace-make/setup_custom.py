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

'''
Gramps customisation hooks for distutils2/packaging module.
'''

#------------------------------------------------
#        Python modules
#------------------------------------------------
import os, sys, glob, codecs
import commands

#-------------------------------------------
#        Distutils2, Packaging modules
#-------------------------------------------
#pylint: disable=F0401
try:
    from distutils2.util import convert_path, newer
except ImportError:
    try:
        from packaging.util import convert_path, newer
    except ImportError:
        # no DistUtils2 or Packaging is NOT installed!
        # Python-2.6, Python-2.7/ Distutils2, or Python-3.3/ Packaging
        raise SystemExit('Distutils2, Packaging, or Distutils is Required!\n',
                         'You need to have one of these installed.')

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
INTLTOOL_FILES = None
ALL_LINGUAS = None

def customize_config(content):
    '''
    Global hook.
    '''
    global INTLTOOL_FILES, ALL_LINGUAS
    INTLTOOL_FILES = get_field(content, 'x-intltool-merge')
    ALL_LINGUAS = get_field(content, 'x-locales')

def get_field(content, key):
    '''
    Retrieve a custom field from the configuration file.
    '''
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
    for lang in ALL_LINGUAS:
        po_file = os.path.join('po', lang + '.po')
        mo_file = os.path.join(build_cmd.build_base, 'mo', lang, 'gramps.mo')

        mo_dir = os.path.dirname(mo_file)
        if not(os.path.isdir(mo_dir) or os.path.islink(mo_dir)):
            os.makedirs(mo_dir)

        if newer(po_file, mo_file):
            cmd = 'msgfmt %s -o %s' % (po_file, mo_file)
            if os.system(cmd) != 0:
                msg = 'ERROR: Building language translation files failed.'
                raise SystemExit(msg)
            print(('Compiling %s >> %s...' % (po_file, mo_file)))

        target = '{datadir}/locale/' + lang + '/LC_MESSAGES/gramps.mo'
        data_files[mo_file] = target

def build_man(build_cmd):
    '''
    Compresses Gramps manual files
    '''
    data_files = build_cmd.distribution.data_files
    build_data = build_cmd.build_base + '/data/'
    for man_dir, dirs, files in os.walk(os.path.join('data', 'man')):
        if 'gramps.1.in' in files:
            filename = os.path.join(man_dir, 'gramps.1.in')
            newdir = os.path.join(build_cmd.build_base, man_dir)
            if not(os.path.isdir(newdir) or os.path.islink(newdir)):
                os.makedirs(newdir)

            newfile = os.path.join(newdir, 'gramps.1')
            version = build_cmd.distribution.metadata['version']
            subst_vars = ((u'@VERSION@', version), )
            substitute_variables(filename, newfile, subst_vars)

            import gzip
            man_file_gz = os.path.join(newdir, 'gramps.1.gz')
            if os.path.exists(man_file_gz):
                if newer(newfile, man_file_gz):
                    os.remove(man_file_gz)
                else:
                    filename = False
                    os.remove(newfile)

            while filename:
                f_in = open(newfile, 'rb')
                f_out = gzip.open(man_file_gz, 'wb')
                f_out.writelines(f_in)
                f_out.close()
                f_in.close()

                print('Compiling manual file, %s...' % man_file_gz)

                os.remove(newfile)
                filename = False

            lang = man_dir[8:]
            src = build_data + 'man' + lang + '/gramps.1.gz'
            target = '{man}' + lang + '/man1'
            data_files[src] = target

def build_intl(build_cmd):
    '''
    Merge translation files into desktop and mime files
    '''
    if intltool_version() < (0, 25, 0):
        return
    
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

    for in_file in INTLTOOL_FILES:
        merge(base, in_file, '-x', po_dir='/tmp', cache=False)
        data_files[base + '/' + in_file] = '{purelib}/' + in_file

def merge(build_base, filename, option, po_dir='po', cache=True):
    '''
    Run the intltool-merge command.
    '''
    filename = convert_path(filename)
    newfile = os.path.join(build_base, filename)
    newdir = os.path.dirname(newfile)
    if not(os.path.isdir(newdir) or os.path.islink(newdir)):
        os.makedirs(newdir)

    option += ' -u'
    if cache:
        cache_file = os.path.join('po', '.intltool-merge-cache')
        option += ' -c ' + cache_file

    datafile = filename + '.in'
    if (not os.path.exists(newfile) and os.path.exists(datafile)):
        cmd = (('LC_ALL=C intltool-merge %(opt)s %(po_dir)s %(in_file)s '
                '%(out_file)s') % 
              {'opt' : option, 
               'po_dir' : po_dir,
               'in_file' : datafile, 
               'out_file' : newfile})
        if os.system(cmd) != 0:
            msg = ('ERROR: %s was not merged into the translation files!\n' % 
                    newfile)
            raise SystemExit(msg)

def install_template(install_cmd):
    '''
    Pre-install hook to populate template files.
    '''
    data_files = install_cmd.distribution.data_files
    write_gramps_sh(install_cmd)
    data_files['gramps.sh'] = '{scripts}/gramps.sh'
    write_const_py(install_cmd)
    data_files['gramps/const.py'] = '{purelib}/gramps/const.py'

def write_gramps_sh(install_cmd):
    '''
    Write the gramps.sh file.
    '''
    f_out = open('gramps.sh', 'w')
    f_out.write('#! /bin/sh\n')
    f_out.write('export GRAMPSDIR=%sgramps\n' % install_cmd.install_lib)
    f_out.write('exec %s -O $GRAMPSDIR/gramps.py "$@"\n' % sys.executable)
    f_out.close()

def write_const_py(install_cmd):
    '''
    Write the const.py file.
    '''
    const_py_in = os.path.join('gramps', 'const.py.in')
    const_py = os.path.join('gramps', 'const.py')

    version = install_cmd.distribution.metadata['version']
    prefix = install_cmd.install_data
    sysconfdir = os.path.join(prefix, 'etc') # Is this correct?
    
    subst_vars = ((u'@VERSIONSTRING@', version), 
                  (u'@prefix@', prefix),
                  (u'@sysconfdir@', sysconfdir))
                  
    substitute_variables(const_py_in, const_py, subst_vars)

def substitute_variables(filename_in, filename_out, subst_vars):
    '''
    Substitute variables in a file.
    '''
    f_in = codecs.open(filename_in, encoding='utf-8')
    f_out = codecs.open(filename_out, encoding='utf-8', mode='w')
    for line in f_in:
        for variable, substitution in subst_vars:
            line = line.replace(variable, substitution)
        f_out.write(line)
    f_in.close()
    f_out.close()

def change_files(install_cmd):
    '''
    post-hook to Change the file permissions of the local build directory
        after install
    '''
    if not hasattr(os, 'chmod'):
        return
    cmd = 'chmod -R --quiet 777 ./build'
    if os.system(cmd) != 0:
        msg = ('You will need to be administrator to delete the build '
                'directory.')
        raise SystemExit(msg)
    print('Chnging permissions of the local build directory...')

def update_posix(install_cmd):
    '''
    post-hook to update Linux systems after install

    these commands are not system stoppers, so there is no reason for
            system exit on failure to run.
    '''
    if os.name != 'posix':
        return
    # these commands will be ran on a Unix/ Linux system after install only...
    for cmd, options in (
            ('ldconfig',                ''),
            ('update-desktop-database', '&> /dev/null'),
            ('update-mime-database',    '/usr/share/mime &> /dev/null'),
            ('gtk-update-icon-cache',   '--quiet /usr/share/icons/hicolor')):
        sys_cmd = ('%(command)s %(opts)s') % {
                    'command' : cmd, 'opts' : options}
        os.system(sys_cmd)

def manifest_builder(distribution, manifest):
    '''
    Manifest builder.
    '''
    # This doesn't work for svn version 1.7.x which has a different file
    # structure.
    manifest.clear()
    for dirpath, dirnames, filenames in os.walk(os.curdir):
        svn_path = os.path.join(dirpath, '.svn', 'text-base', '*.svn-base')
        files = [os.path.join(dirpath, os.path.basename(x)[:-9]) 
                 for x in glob.glob(svn_path)]
        manifest.extend(files)
        if '.svn' in dirnames:
            dirnames.remove('.svn')
