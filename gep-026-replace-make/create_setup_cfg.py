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
import os, sys
import glob, shutil
import codecs

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
            'classifier'         : [x for x in all_classifiers.split('\n')],
            'keywords'           : [],
            'license'            : 'GPL v2 or greater',
            'platform'           : [],
            'requires-dist'      : [],
            'provides-dist'      : [],
            'obsoletes-dist'     : [],
            'requires-externals' : [], 
            'requires-python'    : '>= 2.6',
            'packages'           : [],
            'package_data'       : dict(),
            'modules'            : [],
            'resources'          : [],
            'extra_files'        : [],
            'data_files'         : dict(),
            'scripts'            : [],
         }

        self.data['summary'] = 'Gramps (Genealogical Research and Analysis Management Programming System)'

        self.data['description'] = '''gramps (Genealogical Research and Analysis Management Programming
        System) is a GNOME based genealogy program supporting a Python based plugin system.'''

        self.data['project-url'] = [
            'Repository, https://gramps.svn.sourceforge.net/svnroot/gramps/trunk',
            'Wiki, http://www.gramps-project.org/wiki/index.php?title=Main_page',
            'Bug tracker, http://bugs.gramps-project.org']

        self.data['platform'] = [
            'Linux',
            'FreeBSD',
            'MacOS',
            'Windows']

        self.data['keywords'] = [
            'Genealogy',
            'Pedigree',
            'Ancestry',
            'Birth',
            'Marriage',
            'Death',
            'Family',
            'Family-tree',
            'GEDCOM']

        # these packages have a __init__.py within them, so they are pure python packages,
        # the remaining four are data or extra files...
        # this list has been taken from, 
        self.data['packages'] = [
            'gramps',
            'gramps.cli',
            'gramps.gen',
            'gramps.gui',
            'gramps.webapp']

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

#        self.data['data_files'] = {
#            '../debian'  : ['*.*'],
#            '../data'    : ['*.*'],
#            '../docs'    : ['*.*'],
#            '../help'    : ['*.*'],
#            '../mac'     : ['*.*'],
#            '../po'      : ['*.*'],
#            '../test'    : ['*.*'],
#            '../windows' : ['*.*'],
#        }

        self.data['requires-dist'] = [
            'pygtk2',
            'pycairo',
            'pygobject2']

        self.data['resources'] = [
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
            '../TODO = {doc}']

    def multi_string(self, data):
        return (u''.join('    %s\n' % val
                         for val in data).lstrip())

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
                     'author', 'author-email', 'maintainer', 'maintainer-email'):
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

        for name in ('packages', 'modules', 'scripts'):
            if (name in self.data and self.data[name]):
                fp.write(u'%s = %s\n'
                         % (name, u'\n    '.join(self.data[name]).strip()))

        if self.data.get('package_data'):
            fp.write(u'package_data =\n')
            for pkg, spec in sorted(self.data['package_data'].items()):
                # put one spec per line, indented under the package name
                indent = u' ' * (len(pkg) + 7)
                spec = (u'\n' + indent).join(spec)
                fp.write(u'    %s = %s\n' % (pkg, spec))
            fp.write(u'\n')

        if ('data_files' in self.data and self.data['data_files']):
            fp.write(u'data_files = [\n')
            for dir, filematch in sorted(self.data['data_files'].items()):
                fp.write(u"    ('%s', %s),\n" % (dir, filematch))
            fp.write(u']\n\n')

        if self.data.get('resources'):
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
    cs.main()
    cs.convert_gramps_sh()
    cs.convert_const_file()
