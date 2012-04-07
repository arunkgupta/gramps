# -*- coding: utf-8 -*-
#!/usr/bin/env python

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
import os, sys, sysconfig
import imp
import glob, shutil
import codecs

#------------------------------------------------
#        Distutils/ Distutils2 modules
#------------------------------------------------
from distutils2 import logger

const_file_in = os.path.join('gramps', 'const.py.in')
const_file = os.path.join('gramps', 'const.py')
if (os.path.exists(const_file_in) and not os.path.exists(const_file)):
    shutil.copy(const_file_in, const_file)
from gramps.const import VERSION as GRAMPS_VERSION

#------------------------------------------------
#        Constants
#------------------------------------------------
_FILENAME = 'setup.cfg'

def main():
    '''
    create all the data files and writes them out to setup.cfg
    '''
    opt_data['name'] = 'gramps'

    opt_data['version'] = GRAMPS_VERSION

    opt_data['Home-page'] = 'http://gramps-project.org/'

    opt_data['download-url'] = 'http://gramps-project.org/download/'

    opt_data['author'] = 'Donald N. Allingham'

    opt_data['author_email'] = ''

    opt_data['maintainer'] = 'Gramps Development Team'

    opt_data['maintainer_email'] = 'benny.malengier@gmail.com'

    opt_data['description'] = '''gramps (Genealogical Research and Analysis Management Programming
System) is a GNOME based genealogy program supporting a Python based plugin system.
'''

    opt_data['summary'] = 'Gramps (Genealogical Research and Analysis Management Programming System)'

    opt_data['license'] = 'GPL v2 or greater'

    opt_data['platform'] = [
        'Linux',
        'FreeBSD',
        'Mac OSX',
        'Windows'
    ]

    opt_data['requires-dist'] = [
        'pygtk2',
        'pycairo',
        'pygobject2'
    ]

    opt_data['keywords'] = [
        'Genealogy',
        'Pedigree',
        'Ancestry',
        'Birth',
        'Marriage',
        'Death',
        'Family',
        'Family-tree',
        'GEDCOM'
    ]

    opt_data['classifier'] = [
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
    ]

    _packages = [
        'gramps',
        'gramps.cli',
        'gramps.data',
        'gramps.gen',
        'gramps.glade',
        'gramps.gui',
        'gramps.images',
        'gramps.plugins',
        'gramps.webapp'
    ]
    opt_data['packages'] = _packages

    opt_data['package_data'] = dict((section, list()) for section in _packages
        if section not in ['gramps.images', 'gramps.plugins'])

    opt_data['extra_files'] = dict((section, list()) for section in _packages
        if section in ['gramps.images', 'gramps.plugins'])

    all_files = {
        'gramps' : [
            '*.py',
            'DateHandler/*.py',
            'docgen/*.py',
            'Filters/*.py',
            'Filters/*/*.py',
            'Filters/Rules/*/*.py',
            'GrampsLocale/*.py',
            'GrampsLogger/*.py',
            'Merge/*.py',
            'Simple/*.py',
            'TestPlan.txt',
            'test/*.py'],
        'gramps.cli': [
            '*.py',
            'plug/*.py'],
        'gramps.data': [
            '*.txt',
            '*.xml'],
        'gramps.gen': [
            '*.py',
            'db/*.py',
            'display/*.py',
            'lib/*.py',
            'mime/*.py',
            'plug/*.py',
            'plug/*/*.py',
            'proxy/*.py',
            'test/*.py',
            'utils/*.py'],
        'gramps.glade': [
            '*.glade',
            'glade/catalog/*.py',
            'catalog/*.xml'],
        'gramps.gui': [
            '*.py',
            'editors/*.py',
            'editors/*/*.py',
            'plug/*.py',
            'plug/*/*.py',
            'selectors/*.py',
            'views/*.py',
            'views/treemodels/*.py',
            'widgets/*.py'],
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
        'gramps.webapp': [
            '*.py',
            'webstuff/css/*.css',
            'webstuff/images/*.svg',
            'webstuff/images/*.png',
            'webstuff/images/*.gif',
            'grampsdb/fixtures/initial_data.json',
            '*/*.py',
            'sqlite.db',
            'grampsdb/*.py',
            'fixtures/initial_data.json',
            'templatetags/*py'],
    }
    for section in all_files:
        directory = section
        if '.' in directory:
            directory = '/'.join(directory.split('.'))
        tmp_filenames = []
        for file_match in all_files[section]:
            tmp_filenames.append((glob.glob(os.path.join(directory, file_match))))
            if section in opt_data['package_data']:
                opt_data['package_data'][section] = tmp_filenames
            else:
                opt_data['extra_files'][section] = tmp_filenames

    opt_data['resources'] = [
        'data/ gramps.desktop = {data}/share/applications',
        'gramps/images/ gramps.png = {data}/share/pixmaps',
        'data/ gramps.xml = {data}/share/mime/packages',
        'data/ gramps.mime = {data}/share/mime-info',
        'data/ gramps.keys = {data}/share/mime-info',
        'data/ gnome-mime-application-x-gedcom.png = {data}/share/icons/gnome/48x48/mimetypes',
        'data/ gnome-mime-application-x-geneweb.png = {data}/share/icons/gnome/48x48/mimetypes',
        'data/ gnome-mime-application-x-gramps.png = {data}/share/icons/gnome/48x48/mimetypes',
        'data/ gnome-mime-application-x-gramps-package.png = {data}/share/icons/gnome/48x48/mimetypes',
        'data/ gnome-mime-application-x-gramps-xml.png = {data}/share/icons/gnome/48x48/mimetypes',
        'data/ gnome-mime-application-x-gedcom.svg = {data}/share/icons/gnome/scalable/mimetypes',
        'data/ gnome-mime-application-x-geneweb.svg = {data}/share/icons/gnome/scalable/mimetypes',
        'data/ gnome-mime-application-x-gramps.svg = {data}/share/icons/gnome/scalable/mimetypes',
        'data/ gnome-mime-application-x-gramps-package.svg = {data}/share/icons/gnome/scalable/mimetypes',
        'data/ gnome-mime-application-x-gramps-xml.svg = {data}/share/icons/gnome/scalable/mimetypes',
        'data/man/ gramps.1.in = {data}/share/man/man1',
        'data/man/cs/ gramps.1.in = {data}/share/man/cs/man1',
        'data/man/fr/ gramps.1.in = {data}/share/man/fr/man1',
        'data/man/nl/ gramps.1.in = {data}/share/man/nl/man1',
        'data/man/pl/ gramps.1.in = {data}/share/man/pl/man1',
        'data/man/sv/ gramps.1.in = {data}/share/man/sv/man1',
        'COPYING = {data}/share/doc/gramps',
        'FAQ = {data}/share/doc/gramps',
        'INSTALL = {data}/share/doc/gramps',
        'NEWS = {data}/share/doc/gramps',
        'README = {data}/share/doc/gramps',
        'TODO = {data}/share/doc/gramps',
    ]

    opt_data['scripts'] = 'gramps.sh'

    if os.path.exists(_FILENAME):
        if os.path.exists('%s.old' % _FILENAME):
            message = ("ERROR: %(name)s.old backup exists, please check "
                       "that current %(name)s is correct and remove "
                       "%(name)s.old" % {'name': _FILENAME})
            logger.error(message)
            return
        shutil.move(_FILENAME, '%s.old' % _FILENAME)

    try: 
        fp = codecs.open(_FILENAME, 'w', encoding='utf-8')

        try:
            fp.write(u'[metadata]\n')
            # TODO use metadata module instead of hard-coding field-specific
            # behavior here

            # simple string entries
            for name in ('name', 'version', 'summary', 'download_url'):
                fp.write(u'%s = %s\n' % (name, opt_data.get(name, 'UNKNOWN')))

            # optional string entries
            if ('keywords' in opt_data and opt_data['keywords']):
                # XXX shoud use comma to separate, not space
                fp.write(u'keywords = %s\n' % ' '.join(opt_data['keywords']))

            for name in ('Home-page', 'author', 'author_email',
                         'maintainer', 'maintainer_email', 'description-file'):
                if (name in opt_data and opt_data[name]):
                   fp.write(u'%s = %s\n' % (name.decode('utf-8'),
                                             opt_data[name].decode('utf-8')))

            if ('description' in opt_data and opt_data['description']):
                fp.write(
                         u'description = %s\n'
                         % u'\n       |'.join(opt_data['description'].split('\n')))

            # multiple use string entries
            for name in ('platform', 'supported-platform', 'classifier',
                         'requires-dist', 'provides-dist', 'obsoletes-dist', 'requires-external'):
                if not(name in opt_data and opt_data[name]):
                    continue
                fp.write(u'%s = ' % name)
                fp.write(u''.join('    %s\n' % val
                                  for val in opt_data[name]).lstrip())

            fp.write(u'\n[files]\n')

            for name in ('packages', 'modules', 'scripts', 'extra_files'):
                if not(name in self.data and self.data[name]):
                    continue
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

            if self.data.get('resources'):
                fp.write(u'resources =\n')
                for src, dest in self.data['resources']:
                    fp.write(u'    %s = %s\n' % (src, dest))
                fp.write(u'\n')

        finally:
            fp.close()

if __name__ == "__main__":
    main()
