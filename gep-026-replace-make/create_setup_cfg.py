# -*- coding: utf-8 -*-
#!/usr/bin/env python

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

# $Id$

# ***********************************************
# Python Modules
# ***********************************************
import glob
import sysconfig

import sys
import os
import subprocess
import platform
import shutil

try:
    import py2exe
except:
    pass
import codecs

#------------------------------------------------
#        Distutils/ Distutils2 modules
#------------------------------------------------
try:
    from distutils2.util import newer
except ImportError:
    from distutils.util import newer

#------------------------------------------------
#        Gramps modules
#------------------------------------------------
from classifiers import all_classifiers

#------------------------------------------------
#        Constants
#------------------------------------------------
_FILENAME = 'setup.cfg'

curr_ver = 'You currently have Python-%d.%d.%d installed.' % sys.version_info[0:3]
if sys.version_info < (2, 6):
    sys.exit('Error: Python-%d.%d.%d or newer is required.\n %s\n'
             % (2, 6, 0, curr_ver))

# get the root directory so that everything can be absolute paths
if os.name != "nt" and os.name != "darwin":
    ROOT_DIR = os.path.dirname(__file__)
else:
    # test for sys.frozen to detect a py2exe executable on Windows
    if hasattr(sys, "frozen"):
        ROOT_DIR = os.path.abspath(os.path.dirname(
            unicode(sys.executable, sys.getfilesystemencoding())))
    else:
        ROOT_DIR = os.path.abspath(os.path.dirname(
            unicode(__file__, sys.getfilesystemencoding())))
if ROOT_DIR != '':
    os.chdir(ROOT_DIR)

PO_DIR     = os.path.join(ROOT_DIR, 'po')
MO_DIR     = os.path.join(ROOT_DIR, 'build', 'mo')

if os.name == 'nt':
    script = [os.path.join(ROOT_DIR, 'windows','gramps.pyw')]
elif os.name == 'darwin':
    script = [os.path.join(ROOT_DIR, 'mac','gramps.launcher.sh')]
else:
    # os.name == 'posix'
    script = [os.path.join(ROOT_DIR, 'gramps.sh')]

if platform.system() == 'FreeBSD':
    MAN_DIR = 'man'
else:
    MAN_DIR = os.path.join('data', 'man')

'''
    This will create the setup.cfg for use in setup.py.

    Use case:
        * to be used before you do anything in gramps to build, compile, or install Gramps...

$ python create_setup_cfg.py ...
'''
class CreateSetup(object):
    def __init__(self):
        self.data = {
            'name'               : 'gramps',
            'version'            : '3.5.0',
             'home-page'         : 'http://gramps-project.org/',
             'download-url'      : 'http://gramps-project.org/download/',
             'author'            : 'Donald N. Allingham',
            'author-email'       : 'don@gramps-project.org',
            'maintainer'         : 'Gramps Development Team',
            'maintainer-email'   : 'benny.malengier@gmail.com',
            'summary'            : '',
            'description'        : '',
            'classifier'         : sorted([x for x in all_classifiers]),
            'keywords'           : [],
            'license'            : 'GPL v2 or greater',
            'platform'           : [],
            'requires-dist'      : [],
            'provides-dist'      : [],
            'obsoletes-dist'     : [],
            'requires-externals' : [], 
            'requires-python'    : '>= 2.6',
            'packages'           : [],
            'package_dir'        : {'gramps' : 'gramps'},
            'package_data'       : dict(),
            'modules'            : [],
            'resources'          : [],
            'extra_files'        : [],
            'data_files'         : [],
            'scripts'            : script,
         }

    def create_data_files(self):
        '''
        creates translation_files, man, and gramps *.in files
        '''
        _INTLTOOL_MERGE = os.path.join(ROOT_DIR, '.intltool-merge')

        # add trans_string to these files and convert file...
        if not os.path.exists(os.path.join(ROOT_DIR, 'data', 'gramps.desktop')):
            sys.stdout.write('Merging language files into gramps.desktop...\n')
            os.system('%s -d po/ data/gramps.desktop.in data/gramps.desktop' % _INTLTOOL_MERGE)

        if not os.path.exists(os.path.join(ROOT_DIR, 'data', 'gramps.xml')):
            sys.stdout.write('Merging languages into gramps.xml...\n')
            os.system('%s -x po/ data/gramps.xml.in data/gramps.xml' % _INTLTOOL_MERGE)

        if not os.path.exists(os.path.join(ROOT_DIR, 'data', 'gramps.keys')):
            sys.stdout.write('Merging languages into gramps keys...\n')
            os.system('%s -k po/ data/gramps.keys.in data/gramps.keys' _INTLTOOL_MERGE)

        sys.stdout.write('Creating gramps manual files...\n')
        gramps_man_in_file = os.path.join(MAN_DIR, 'gramps.1.in')
        gramps_man_file    = os.path.join(MAN_DIR, 'gramps.1')
        if (os.path.exists(gramps_man_in_file) and not os.path.exists(gramps_man_file)):
            shutil.copy(gramps_man_in_file, gramps_man_file)

        gramps_man_file_gz = os.path.join(MAN_DIR, 'gramps.1.gz')
        if newer(gramps_man_file, gramps_man_file_gz):
            if os.path.isfile(gramps_man_file_gz):
                os.remove(gramps_man_file_gz)

            import gzip

            f_in = open(gramps_man_file, 'rb')
            f_out = gzip.open(gramps_man_file_gz, 'wb')
            f_out.writelines(f_in)
            f_out.close()
            f_in.close()
            sys.stdout.write('Merging gramps man file into gzipped file.\n\n')

        for po in glob.glob(os.path.join(PO_DIR, '*.po')):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(MO_DIR, lang, 'gramps.mo')
            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                sys.stdout.write('creating %s\n' % directory)
                os.makedirs(directory)

            if newer(po, mo):
                sys.stdout.write('compiling %s -> %s\n' % (po, mo))
                try:
                    bash_string = 'msgfmt %s/%s.po -o %s' % (PO_DIR, lang, mo)
                    result = subprocess.call(bash_string, shell=True)
                    if result != 0:
                        raise Warning, "msgfmt returned %d" % result
                except Exception, e:
                    sys.stdout.write("Building gettext files failed!\n")
                    sys.stdout.write("Error: %s\n" % str(e))
                    sys.exit(1)

    def os_files(self):
        # Windows or MacOSX
        if (os.name == 'nt' or os.name == 'darwin'):
            return [
                # application icon
                (os.path.join('share', 'pixmaps'), [os.path.join('gramps', 'images', 'ped24.ico')]),
                (os.path.join('share', 'pixmaps'), [os.path.join('gramps', 'images', 'gramps.png')]),
                (os.path.join('share', 'icons', 'scalable'),
                        glob.glob(os.path.join('gramps', 'images', 'scalable', '*.svg'))),
                (os.path.join('share', 'icons', '16x16'),
                        glob.glob(os.path.join('gramps', 'images', '16x16', '*.png'))),
                (os.path.join('share', 'icons', '22x22'),
                        glob.glob(os.path.join('gramps', 'images', '22x22' ,'*.png'))),
                (os.path.join('share', 'icons', '48x48'),
                        glob.glob(os.path.join('gramps', 'images', '48x48', '*.png'))),
                # doc
                ('share', ['AUTHORS']),
                ('share', ['COPYING']),
                ('share', ['FAQ']),
                ('share', ['INSTALL']),
                ('share', ['LICENSE']),
                ('share', ['NEWS']),
                ('share', ['README']),
                ('share', ['TODO'])
            ]
        else:
            # Linux or FreeBSD
            return [
                # XDG application description
                ('share/applications', ['data/gramps.desktop']),

                # XDG application icon
                ('share/pixmaps', ['gramps/images/gramps.png']),

                # XDG desktop mime types cache
                ('share/mime/packages', ['data/gramps.xml']),

                # mime.types
                ('share/mime-info', ['data/gramps.mime']),
                ('share/mime-info', ['data/gramps.keys']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gedcom.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-geneweb.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gramps.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gramps-package.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gramps-xml.png']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gedcom.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-geneweb.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gramps.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gramps-package.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gramps-xml.svg']),

                # man-page, /!\ should be gramps.1 with variables
                # migration to sphinx/docutils/gettext environment ?
                (os.path.join(MAN_DIR, 'man1'), ['data/man/gramps.1.in']),
                (os.path.join(MAN_DIR, 'cs', 'man1'), ['data/man/cs/gramps.1.in']),
                (os.path.join(MAN_DIR, 'fr', 'man1'), ['data/man/fr/gramps.1.in']),
                (os.path.join(MAN_DIR, 'nl', 'man1'), ['data/man/nl/gramps.1.in']),
                (os.path.join(MAN_DIR, 'pl', 'man1'), ['data/man/pl/gramps.1.in']),
                (os.path.join(MAN_DIR, 'sv', 'man1'), ['data/man/sv/gramps.1.in']),
                # icons 
                ('share/icons/hicolor/scalable/apps', glob.glob('gramps/images/scalable/*.svg')),
                ('share/icons/hicolor/16x16/apps', glob.glob('gramps/images/16x16/*.png')),
                ('share/icons/hicolor/22x22/apps', glob.glob('gramps/images/22x22/*.png')),
                ('share/icons/hicolor/48x48/apps', glob.glob('gramps/images/48x48/*.png')),
                # doc
                ('share/doc/gramps', ['COPYING']),
                ('share/doc/gramps', ['FAQ']),
                ('share/doc/gramps', ['INSTALL']),
                ('share/doc/gramps', ['NEWS']),
                ('share/doc/gramps', ['README']),
                ('share/doc/gramps', ['TODO'])
            ]

    def trans_files(self):
        '''
        List of available compiled translations; ready for installation
        '''
        translation_files = []
        for mo in glob.glob(os.path.join(MO_DIR, '*', 'gramps.mo')):
            lang = os.path.basename(os.path.dirname(mo))
            if os.name == 'posix':
                dest = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
            else :
                dest = os.path.join('locale', lang, 'LC_MESSAGES')
            translation_files.append((dest, [mo]))
        return translation_files

    def define_data_fields(self):
        '''
        defines the data fields that are not already set
        '''
        self.data['summary'] = 'Gramps (Genealogical Research and Analysis Management Programming System)'

        self.data['description'] = '''gramps (Genealogical Research and Analysis Management Programming
        System) is a GNOME based genealogy program supporting a Python based plugin system.'''

        self.data['project-url'] = [
            'Repository, https://gramps.svn.sourceforge.net/svnroot/gramps/trunk',
            'Wiki, http://www.gramps-project.org/wiki/index.php?title=Main_page',
            'Bug tracker, http://bugs.gramps-project.org']

        self.data['platform'] = sorted([
            'Linux',
            'FreeBSD',
            'MacOS',
            'Windows'])

        self.data['keywords'] = sorted([
            'Genealogy',
            'Pedigree',
            'Ancestry',
            'Birth',
            'Marriage',
            'Death',
            'Family',
            'Family-tree',
            'GEDCOM'])

        # these packages have a __init__.py within them, so they are pure python packages,
        # the remaining four are data or extra files...
        # this list has been taken from, 
        self.data['packages'] = ([
            'gramps',
            'gramps.cli',
            'gramps.gen',
            'gramps.gui',
            'gramps.webapp'])

        # these files coe from directories/ packages that do NOT have an __init__.py file...
        self.data['package_data'] = {
            'gramps.data': [
                '*.txt',
                '*.xml'],
            'gramps.glade': [
                '*.glade',
                'glade/catalog/*.py',
                'catalog/*.xml'],
            'gramps.images': [
                '*/*.png',
                 '*/*.svg',
                '*.png',
                '*.jpg',
                '*.ico',
                 '*.gif'],
            'gramps.plugins': [
                '*.py',
                '*/*.py',
                'lib/*.xml',
                'lib/maps/*.py',
                'webstuff/css/*.css',
                'webstuff/images/*.svg',
                'webstuff/images/*.png',
                'webstuff/images/*.gif',            
                '*.glade',
                '*/*.glade'],
        }

        self.data['scripts'] = ['gramps.sh']

        self.data['extra_files'] = sorted([
            'debian/*',
            'docs/*',
            'docs/*/*',
            'help/*',
            'mac/*',
            'po/*',
            'po/*/*',
            'test/*',
            'test/*/*',
            'windows/*',
            'windows/*/*'])

        self.data['extra_files'] = self.os_files() + self.trans_files()

        self.data['requires-dist'] = sorted([
            'pygtk2',
            'pycairo',
            'pygobject2'])

        # destination categories are: {config}, {appdata}, {appdata.arch}, {appdata.persistent},
        # {appdata.disposable}, {help}, {icon}, {scripts}, {doc}, {info}, {man}, {distribution.name}
        self.data['resources'] = sorted([
            '../example/* = {purelib}/gramps',
            'glade/* = {purelib}',
            'images/* = {purelib}',
            'plugins/* = {purelib}',
            '../data/gramps.desktop = {data}/share/applications',
            'images/gramps.png = {icon}',
            '../data/gramps.xml = {data}/share/mime/packages',
            '../data/gramps.mime = {data}/share/mime-info',
            '../data/gramps.keys = {data}/share/mime-info',
            '../data/*.png = {data}/share/icons/gnome/48x48/mimetypes',
            '../data/*.svg = {data}/share/icons/gnome/scalable/mimetypes',
            '../data/man/gramps.1.in = {man}/man1',
            '../data/man/cs/gramps.1.in = {man}/cs/man1',
            '../data/man/fr/gramps.1.in = {man}/fr/man1',
            '../data/man/nl/gramps.1.in = {man}/nl/man1',
            '../data/man/pl/gramps.1.in = {man}/pl/man1',
            '../data/man/sv/gramps.1.in = {man}/sv/man1',
            '../COPYING = {doc}',
            '../FAQ = {doc}',
            '../INSTALL = {doc}',
            '../NEWS = {doc}',
            '../README = {doc}',
            '../TODO = {doc}'])
        
    def multi_string(self, data):
        return (u''.join('    %s\n' % val
                         for val in data).lstrip())

    def no_strip_multi(self, data):
        return (u''.join('    %s\n' % val for val in data))

    def main(self):
        if os.path.exists(_FILENAME):
            if os.path.exists('%s.old' % _FILENAME):
                os.remove('%s.old' % _FILENAME)
            else:
                shutil.move(_FILENAME, '%s.old' % _FILENAME)

        try: 
            fp = codecs.open(_FILENAME, 'w', encoding='utf-8')
        except (IOError, OSError):
            sys.exit('ERROR:  Failed to write %s file' % _FILENAME)
            
        fp.write(u'[metadata]\n')

        for name in ('name', 'version', 'summary', 'description', 'home-page', 'download-url',
                     'author', 'author-email', 'maintainer', 'maintainer-email', 'license'):
            fp.write(u'%s = %s\n' % (name, self.data.get(name, 'UNKNOWN')))

        if ('project-url' in self.data and self.data['project-url']):
            fp.write(u'project-url:\n')
            for line in self.data['project-url']:
                fp.write(u'    %s\n' % line)

        for name in ('keywords', 'platform', 'supported-platform', 'classifier',
                     'requires-dist', 'provides-dist', 'obsoletes-dist', 'requires-externals'):
            if (name in self.data and self.data[name]):
                fp.write(u'%s = ' % name)
                fp.write(self.multi_string(self.data[name]))

        if ('requires-python' in self.data and self.data['requires-python']):
            fp.write(u'requires-python = %s\n' % self.data['requires-python'])
        fp.write(u'\n')

        fp.write(u'[files]\n')

        if ('package_dir' in self.data and self.data['package_dir']):
            fp.write(u'package_dir = %s\n' % self.data['package_dir'])

        for name in ('packages', 'modules'):
            if (name in self.data and self.data[name]):
                fp.write(u'%s = %s\n'
                         % (name, u'\n    '.join(self.data[name]).strip()))

        if ('package_data' in self.data and self.data['package_data']):
            fp.write(u'package_data =\n')
            for pkg, spec in sorted(self.data['package_data'].items()):
                # put one spec per line, indented under the package name
                indent = u' ' * (len(pkg) + 7)
                spec = (u'\n' + indent).join(spec)
                fp.write(u'    %s = %s\n' % (pkg, spec))
            fp.write(u'\n')

        if ('data_files' in self.data and self.data['data_files']):
            fp.write(u'data_files = \n')
            fp.write(self.no_strip_multi(self.data['data_files']))

        if ('resources' in self.data and self.data['resources']):
            fp.write(u'resources =\n')
            #for src, dest in self.data['resources']:
            #fp.write(u'    %s = %s\n' % (src, dest))
            for entry in self.data['resources']:
                fp.write(u'    %s\n' % entry)                
            fp.write(u'\n')

        fp.close()

    # make absolute sure that this file exists?
    def convert_gramps_sh(self):
        gramps_sh_in   = 'gramps.sh.in'
        gramps_sh_file = 'gramps.sh'
        if (os.path.exists(gramps_sh_in) and not os.path.exists(gramps_sh_file)):
            shutil.copy(gramps_sh_in, gramps_sh_file)

    # make absolute sure that this file exists?
    def convert_const_file(self):
        const_py_in   = os.path.join('gramps', 'const.py.in')
        const_py_file = os.path.join('gramps', 'const.py')
        if (os.path.exists(const_py_in) and not os.path.exists(const_py_file)):
            shutil.copy(const_py_in, const_py_file)

if __name__ == "__main__":
    cs = CreateSetup()
    cs.create_data_files()
    cs.define_data_fields()
    cs.main()
    cs.convert_gramps_sh()
    cs.convert_const_file()
