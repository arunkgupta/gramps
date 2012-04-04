import os, sys, glob
import codecs

# determine if we have Distutils2 installed on this computer?
DISTUTILS2_URL = 'http://pypi.python.org/pypi/Distutils2'
try:
    import distutils2
except:
    sys.exit('Error:  You do not have Distutils2 installed. \n'
             'You may download it from here: \n %s'
             % DISTUTILS2_URL)

# determine if this computer has Python-2.6.x or later installed or not?
if sys.version < '2.6':
    sys.exit('Error: Python-2.6 or newer is required. Current version: \n %s'
             % sys.version)

# if the setup.cfg file already exists, delete it?
_existing_file = os.path.join(os.getcwd(), 'setup.cfg')
if os.path.isfile(existing_file):
    os.remove(existing_file)

[metadata]
name = Gramps3
version = 3.4.0
description = Gramps (Genealogical Research and Analysis Management Programming System)
home-page = http://gramps-project.org/
download-url = http://gramps-project.org/download/
author = Gramps Development Team
author-email = 
license = GPL v2 or greater

Keywords = '''
    Genealogy
    Pedigree
    Ancestry
    Birth
    Marriage
    Death
    Family
    Family-tree
    GEDCOM
'''

CLASSIFIERS = '''
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
'''
CLASSIFIERS = [x for x in CLASSIFIERS.split('\n')]

[files]
package_dir = {'gramps' : 'gramps'},
scripts = gramps.sh

extra_files = '''
    AUTHORS
    COPYING
    FAQ
    INSTALL
    LICENSE
    log
    NEWS
    README
    RELEASE_NOTES
    setup.py
    setup.cfg
    TODO
'''
extra_files = [x for x in extra_files.split('\n')]

packages = '''
    gramps
    gramps.cli
    gramps.data
    gramps.gen
    gramps.glade
    gramps.gui
    gramps.images
    gramps.plugins
    gramps.webapp
'''
packages = [x for x in packages.split('\n')]

def gramps():
    return {'gramps': [
                '*.py', 
                'DateHandler/*.py',
                'docgen/*.py',
                'Filters/*.py',
                'Filters/*/*.py',
                'Filters/Rules/*/*.py',
                'GrampsLocale/*.py',
                'GrampsLogger/*.py',
                'Merge/*.py',
                'Simple/*.py'],
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
                'utils/*.py'],
            'gramps/glade': [
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
                'templatetags/*py']
            }

package_index_list = {}
data_index_list = {}
sections_list = []
for section, filenames in gramps().items():
    rest = []
    if '.' in section:
        section, rest = section.split('.', 1)

    unusable_dirs = [".", "test", "guiQML"]
    tmp_package_list = []
    if ((section in unusable_dirs) or (rest in unusable_dirs)):
        coontinue
    else:
        directory = '/'.join([section, rest])
        dirpath = os.path.join(directory, filenames)
        for fname in glob.glob(dirpath):
            tmp_package_list.append(fname)
        if '__init__.py' in tmp_package_list:
           package_index_list[section] = tmp_package_list
        else:
            data_index_list[section] = tmp_package_list
    sctions_list.append(section)

resources = '''
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
'''

[build_ext]
# needed so that tests work without mucking with sys.path
inplace = 1
