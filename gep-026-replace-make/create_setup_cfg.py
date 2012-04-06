import os, sys, sysconfig
import imp
import glob, shutil
import codecs

from distutils2 import logger

_FILENAME = 'setup.cfg'

platform = Linux
    FreeBSD
    MacOS
    Windows
requires-dist = pygtk
    pycairo
    pygobject
Keywords = Genealogy
    Pedigree
    Ancestry
    Birth
    Marriage
    Death
    Family
    Family-tree
    GEDCOM 

classifier =
    Development Status :: 5 - Production/Stable
    Environment :: Console
    Environment :: MacOS X
    Environment :: Plugins
    Environment :: Web Environment
    Environment :: Win32 (MS Windows)
    Environment :: X11 Applications :: GTK
    Framework :: Django
    Intended Audience :: Education
    Intended Audience :: End Users/Desktop
    Intended Audience :: Other Audience
    Intended Audience :: Science/Research
    License :: OSI Approved :: GNU General Public License (GPL)
    Natural Language :: Bulgarian
    Natural Language :: Catalan
    Natural Language :: Chinese (Simplified)
    Natural Language :: Croatian
    Natural Language :: Czech
    Natural Language :: Danish
    Natural Language :: Dutch
    Natural Language :: English
    Natural Language :: Esperanto
    Natural Language :: Finnish
    Natural Language :: French
    Natural Language :: German
    Natural Language :: Hebrew
    Natural Language :: Hungarian
    Natural Language :: Italian
    Natural Language :: Japanese
    Natural Language :: Norwegian
    Natural Language :: Polish
    Natural Language :: Portuguese (Brazilian)
    Natural Language :: Portuguese
    Natural Language :: Russian
    Natural Language :: Slovak
    Natural Language :: Slovenian
    Natural Language :: Spanish
    Natural Language :: Swedish
    Natural Language :: Ukranian
    Natural Language :: Vietnamese
    Operating System :: MacOS
    Operating System :: Microsoft :: Windows
    Operating System :: Other OS
    Operating System :: POSIX :: BSD
    Operating System :: POSIX :: Linux
    Operating System :: POSIX :: SunOS/Solaris
    Operating System :: Unix
    Programming Language :: Python
    Programming Language :: Python :: 2.7
    Topic :: Database
    Topic :: Desktop Environment :: Gnome
    Topic :: Education
    Topic :: Multimedia
    Topic :: Other/Nonlisted Topic
    Topic :: Scientific/Engineering :: Visualization
    Topic :: Sociology :: Genealogy

packages = gramps
    gramps.cli
    gramps.data
    gramps.gen
    gramps.glade
    gramps.gui
    gramps.images
    gramps.plugins
    gramps.webapp

package_data =
    gramps = *.py
             DateHandler/*.py
             docgen/*.py
             Filters/*.py
             Filters/*/*.py
             Filters/Rules/*/*.py
             GrampsLocale/*.py
             GrampsLogger/*.py
             Merge/*.py
             Simple/*.py
    gramps.cli = *.py
                 plug/*.py
    gramps.data = *.txt
                  *.xml
    gramps.gen = *.py
                 db/*.py
                 display/*.py
                 lib/*.py
                 mime/*.py
                 plug/*.py
                 plug/*/*.py
                 proxy/*.py
                 utils/*.py
    gramps.glade = *.glade
                   glade/catalog/*.py
                   catalog/*.xml
    gramps.gui = *.py
                 editors/*.py
                 editors/*/*.py
                 plug/*.py
                 plug/*/*.py
                 selectors/*.py
                 views/*.py
                 views/treemodels/*.py
                 widgets/*.py
    gramps.images = */*.png
                    */*.svg
                    *.png
                    *.jpg
                    *.ico
                    *.gif
    gramps.plugins = *.py
                     */*.py
                     lib/*.xml
                     lib/maps/*.py
                     webstuff/css/*.css
                     webstuff/images/*.svg
                     webstuff/images/*.png
                     webstuff/images/*.gif
                     *.glade
                     */*.glade
    gramps.webapp = *.py
                    webstuff/css/*.css
                    webstuff/images/*.svg
                    webstuff/images/*.png
                    webstuff/images/*.gif
                    grampsdb/fixtures/initial_data.json
                    */*.py
                    sqlite.db
                    grampsdb/*.py
                    fixtures/initial_data.json
                    templatetags/*py

resources =
    data/ gramps.desktop = {data}/share/applications
    gramps/images/ gramps.png = {data}/share/pixmaps
    data/ gramps.xml = {data}/share/mime/packages
    data/ gramps.mime = {data}/share/mime-info
    data/ gramps.keys = {data}/share/mime-info
    data/ gnome-mime-application-x-gedcom.png = {data}/share/icons/gnome/48x48/mimetypes
    data/ gnome-mime-application-x-geneweb.png = {data}/share/icons/gnome/48x48/mimetypes
    data/ gnome-mime-application-x-gramps.png = {data}/share/icons/gnome/48x48/mimetypes
    data/ gnome-mime-application-x-gramps-package.png = {data}/share/icons/gnome/48x48/mimetypes
    data/ gnome-mime-application-x-gramps-xml.png = {data}/share/icons/gnome/48x48/mimetypes
    data/ gnome-mime-application-x-gedcom.svg = {data}/share/icons/gnome/scalable/mimetypes
    data/ gnome-mime-application-x-geneweb.svg = {data}/share/icons/gnome/scalable/mimetypes
    data/ gnome-mime-application-x-gramps.svg = {data}/share/icons/gnome/scalable/mimetypes
    data/ gnome-mime-application-x-gramps-package.svg = {data}/share/icons/gnome/scalable/mimetypes
    data/ gnome-mime-application-x-gramps-xml.svg = {data}/share/icons/gnome/scalable/mimetypes
    data/man/ gramps.1.in = {data}/share/man/man1
    data/man/cs/ gramps.1.in = {data}/share/man/cs/man1
    data/man/fr/ gramps.1.in = {data}/share/man/fr/man1
    data/man/nl/ gramps.1.in = {data}/share/man/nl/man1
    data/man/pl/ gramps.1.in = {data}/share/man/pl/man1
    data/man/sv/ gramps.1.in = {data}/share/man/sv/man1
    COPYING = {data}/share/doc/gramps
    FAQ = {data}/share/doc/gramps
    INSTALL = {data}/share/doc/gramps
    NEWS = {data}/share/doc/gramps
    README = {data}/share/doc/gramps
    TODO = {data}/share/doc/gramps

const_file_in = os.path.join('gramps', 'const.py.in')
const_file = os.path.join('gramps', 'const.py')
if (os.path.exists(const_file_in) and not os.path.exists(const_file)):
    shutil.copy(const_file_in, const_file)
from gramps.const import VERSION as GRAMPS_VERSION

data_opts = {'name': '',
             'version': GRAMPS_VERSION,
             'author' : '',
             'author_email' : '',
             'maintainer' : '',
             'maintainer_email' : '',
             'classifier': self.classifiers,
             'packages': [],
             'modules': [],
             'platform': [],
             'resources': [],
             'extra_files': [],
             'scripts': [],
         }


    def _write_cfg(self):
        if os.path.exists(_FILENAME):
            if os.path.exists('%s.old' % _FILENAME):
                message = ("ERROR: %(name)s.old backup exists, please check "
                           "that current %(name)s is correct and remove "
                           "%(name)s.old" % {'name': _FILENAME})
                logger.error(message)
                return
            shutil.move(_FILENAME, '%s.old' % _FILENAME)

        fp = codecs.open(_FILENAME, 'w', encoding='utf-8')




