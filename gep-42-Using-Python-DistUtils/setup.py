# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Gramps - a GTK+/GNOME based genealogy program
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
# testing a setup.py for Gramps
#
# for linux install: "python setup.py install --prefix=/usr -f"
# for windows exe creation: "python setup.py py2exe"
#
# $ID:$

#-----------------------------------------------------
#        DisUtils modules
#-----------------------------------------------------
from distutils.cmd import Command
from distutils import log
from distutils.core import setup
from distutils.command.build import build
from distutils.command.install_data import install_data
from distutils.command.install import INSTALL_SCHEMES, install
from distutils.command.clean import clean

from distutils.spawn import find_executable

from distutils.dist import Distribution
from distutils.dep_util import newer
from distutils.log import warn, info, error
from distutils.errors import DistutilsFileError

#-----------------------------------------------------
#        Python modules
#-----------------------------------------------------
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

# get the root directory so that everything can be absolute paths...
ROOT_DIR = os.getcwd()

PO_DIR = os.path.join(ROOT_DIR, 'po')
MO_DIR = os.path.join(ROOT_DIR, 'build', 'mo')

if sys.version < '2.6':
    sys.exit('Error: Python-2.6 or newer is required. Current version:\n %s'
             % sys.version)

def modules_check():
    '''Check if necessary modules is installed.
    The function is executed by distutils(by the install command).'''
    try:
        try:
            import gtk.glade
        except RuntimeError:
            print ("Error importing GTK - is there no windowing environment available ? \n"
                   "We're going to ignore this error and live dangerously. Please make \n"
                   "sure you have pygtk > 2.16 and gtk available!")
    except ImportError:
        raise
    mod_list = [
        ('pygtk','gtk'),
        ('pycairo','cairo'),
        'pygobject',
        ]
    ok = 1
    for m in mod_list:
        if type(m)==tuple:
            have_mod = False
            for mod in m:
                try:
                    exec('import %s'% mod)
                except ImportError:
                    pass
                else:
                    have_mod = True
            if not have_mod:
                ok = False
                print ('Error: %s is Python module is required to install %s'
                    % (' or '.join(m), name.title()))
        else:
            try:
                exec('import %s' % m)
            except ImportError:
                ok = False
                print ('Error: %s Python module is required to install %s'
                  % (m, name.title()))
    if not ok:
        sys.exit(1)

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
    MAN_DIR = os.path.join('share', 'man')

SYSTEM_PREFIX = os.path.normpath(sys.prefix)

class osx_install_data(install_data):
    def initialize_options(self):
        pass

    # On MacOS, the platform-specific lib dir is /System/Library/Framework/Python/.../
    # which is wrong. Python 2.5 supplied with MacOS 10.5 has an Apple-specific fix
    # for this in distutils.command.install_data#306. It fixes install_lib but not
    # install_data, which is why we roll our own install_data class.

    def run(self):
        install_data.run(self)

    def finalize_options(self):
        # By the time finalize_options is called, install.install_lib is set to the
        # fixed directory, so we set the installdir to install_lib. The
        # install_data class uses('install_data', 'install_dir') instead.
        self.set_undefined_options('install', ('install_lib', 'install_dir'))
        install_data.finalize_options(self)

# copy gramps/const.py.in to gramps/const.py ...
const_file_in = os.path.join(ROOT_DIR, 'gramps', 'const.py.in')
const_file    = os.path.join(ROOT_DIR, 'gramps', 'const.py')
if (os.path.exists(const_file_in) and not os.path.exists(const_file)):
    shutil.copy(const_file_in, const_file)
from gramps.const import VERSION as GRAMPS_VERSION

# if this system is posix, then copy gramps.sh.in to gramps.sh
if os.name == "posix":
    gramps_launcher_in = os.path.join(ROOT_DIR, 'gramps.sh.in')
    gramps_launcher    = os.path.join(ROOT_DIR, 'gramps.sh')
    if (os.path.exists(gramps_launcher_in) and not os.path.exists(gramps_launcher)):
        shutil.copy(gramps_launcher_in, gramps_launcher)

# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

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
            'gramps/data': [
            '*.txt',
            '*.xml'],
            'gramps/gen': [
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
            'gramps/gui': [
            '*.py',
            'editors/*.py',
            'editors/*/*.py',
            'plug/*.py',
            'plug/*/*.py',
            'selectors/*.py',
            'views/*.py',
            'views/treemodels/*.py',
            'widgets/*.py'],
            'gramps/images': [
            '*/*.png',
            '*/*.svg',
            '*.png',
            '*.jpg',
            '*.ico',
            '*.gif'],
            'gramps/plugins': [
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
            'gramps/webapp': [
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
package_files = []
for directory, files in gramps().items():
    for file in files:
        package = glob.glob(os.path.join(ROOT_DIR, directory, file))
        package_files.append(package)
        info('Adding %s to the list of packages' % package)

def os_files():
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
                ('share', ['COPYING']),
                ('share', ['FAQ']),
                ('share', ['INSTALL']),
                ('share', ['NEWS']),
                ('share', ['README']),
                ('share', ['TODO'])
        ]
    else:
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

def trans_files():
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

class GrampsDist(Distribution):
  global_options = Distribution.global_options + [
    ("without-gettext", None, "Don't build/install gettext .mo files"),
    ("without-icon-cache", None, "Don't attempt to run gtk-update-icon-cache")]

  def __init__(self, *args):
    self.without_gettext = False
    self.without_icon_cache = False
    Distribution.__init__(self, *args)

'''
        Standard command for 'python setup.py build' ...
'''
class GrampsBuildData(build):
    def run(self):
        build.run(self)

        if self.distribution.without_gettext:
            return

        if os.name != 'posix':
            return

        gramps_build_dir = os.path.join(ROOT_DIR, 'build', 'gramps')
        if (not os.path.isdir(gramps_build_dir) and not os.path.islink(gramps_build_dir)):
            os.makedirs(gramps_build_dir)

        for filecmd in ['intltool-extract.in', 'intltool-merge.in', 'intltool-update.in']:
            file = os.path.join(ROOT_DIR, filecmd)
            newfile, rest = file.split('.in')
            shutil.copy(file, newfile)

        # add trans_string to these files and convert file...
        os.system('intltool-merge -d po/ data/gramps.desktop.in data/gramps.desktop')
        os.system('intltool-merge -x po/ data/gramps.xml.in data/gramps.xml')
        os.system('intltool-merge -k po/ data/gramps.keys.in data/gramps.keys')

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
            info('Merging gramps man file into gzipped file.')

        for po in glob.glob(os.path.join(PO_DIR, '*.po')):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(MO_DIR, lang, 'gramps.mo')
            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                info('creating %s' % directory)
                os.makedirs(directory)

            if newer(po, mo):
                info('compiling %s -> %s' % (po, mo))
                try:
                    bash_string = 'msgfmt %s/%s.po -o %s' % (PO_DIR, lang, mo)
                    result = subprocess.call(bash_string, shell=True)
                    if result != 0:
                        raise Warning, "msgfmt returned %d" % result
                except Exception, e:
                    error("Building gettext files failed. Try setup.py --without-gettext [build|install]")
                    error("Error: %s" % str(e))
                    sys.exit(1)

        INTLTOOL_MERGE = 'intltool-merge'
        desktop_in = 'data/gramps.desktop.in'
        desktop_data = 'data/gramps.desktop'
        os.system ("C_ALL=C " + INTLTOOL_MERGE + " -d -u -c " + ROOT_DIR +
            "/po/.intltool-merge-cache " + ROOT_DIR + "/po " +
            desktop_in + " " + desktop_data)

'''
        Standard command for 'python setup.py install_data' ...
'''
class GrampsInstallData(install_data):
    description = "Attempt an install and generate a log file"
    user_options = [('fake', None, 'Override')]

    def initialize_options(self):
        pass

    def run(self):
        install_data.run(self)

        self.data_files.extend(self._find_mo_files())
        self.data_files.extend(self._find_desktop_file())

    def _find_desktop_file(self):
        return [("share/applications", ["data/gramps.desktop"])]

    def _find_mo_files(self):
        data_files = []
        if not self.distribution.without_gettext:
            for mo in glob.glob(os.path.join(MO_DIR, '*', 'gramps.mo')):
                lang = os.path.basename(os.path.dirname(mo))
                dest = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
                data_files.append((dest, [mo]))
        return data_files

    def finalize_options(self):
        if os.name == 'posix':
            #update the XDG Shared MIME-Info database cache
            info('Updating the Shared MIME-Info database cache.')
            subprocess.call(["update-mime-database", os.path.join(sys.prefix, 'share', 'mime')])

            # update the mime.types database (debian, ubuntu)
            # info('Updating the mime.types database.')
            # subprocess.call("update-mime")

            # update the XDG .desktop file database
            info('Updating the .desktop file database.')
            subprocess.call(["update-desktop-database"])
            
            # ldconfig

'''
        Standard command for 'python setup.py install' ...
'''
class GrampsInstall(install):
    description = "Attempt an install and generate a log file"
    user_options = [('fake', None, 'Override')]
    
    def initialize_options(self):
        pass
    
    def run(self):
        install.run(self)
        self.distribution.scripts = ['gramps']
        
    def finalize_options(self):
        pass

'''
        Standard command for 'python setup.py uninstall' ...
'''
class GrampsUninstall(Command):
    description = "Attempt an uninstall from an install log file"
    user_options = [('log=', None, 'Installation record filename')]

    def initialize_options(self):
        self.log = 'log'

    def get_command_name(self):
        return 'uninstall'

    def run(self):
        f = None
        self.ensure_filename('log')
        try:
            try:
                f = open(self.log)
                files = [file.strip() for file in f]
            except IOError, e:
                raise DistutilsFileError("unable to open log: %s", str(e))
        finally:
            if f:
                f.close()

        for file in files:
            if os.path.isfile(file) or os.path.islink(file):
                info("removing %s" % repr(file))
            if not self.dry_run:
                try:
                    os.unlink(file)
                except OSError, e:
                    warn("could not delete: %s" % repr(file))
            elif not os.path.isdir(file):
                info("skipping %s" % repr(file))

        dirs = set()
        for file in reversed(sorted(files)):
            dir = os.path.dirname(file)
            if dir not in dirs and os.path.isdir(dir) and len(os.listdir(dir)) == 0:
                dirs.add(dir)
                # Only nuke empty Python library directories, else we could destroy
                # e.g. locale directories we're the only app with a .mo installed for.
            if dir.find("site-packages/") > 0:
                info("Removing %s" % repr(dir))
                if not self.dry_run:
                    try:
                        os.rmdir(dir)
                    except OSError, e:
                        warn("could not remove directory: %s" % str(e))
            else:
                info("skipping empty directory %s" % repr(dir))

    def finalize_options(self):
        pass

'''
        Standard command for 'python setup.py clean' ...
'''
class GrampsClean(clean):
    def initialize_options(self):
        pass

    def run(self):
        clean.run(self)

    def finalize_options(self):
        pass

# turn off warnings when deprecated modules are imported
import warnings
warnings.filterwarnings("ignore", category = DeprecationWarning)

if "py2exe" in sys.argv:
    DATA_FILES = [("glade", glob.glob(os.path.join(ROOT_DIR, 'gramps', 'glade', '*.*')))]
    for lang in glob.glob(os.path.join(MO_DIR, '*.po')):
        lang = os.path.basename(os.path.dirname(lang))
        DATA_FILES.append(("locale/%s/LC_MESSAGES" % lang, ["locale/%s/LC_MESSAGES/gramps.mo" % lang]))

    setup (
       name              = "Gramps",
       version           = GRAMPS_VERSION,
        author           = 'Gramps Development Team',
        author_email     = 'benny.malengier@gmail.com',
        url              = 'http://gramps-project.org/',
        download_url     = 'http://sourceforge.net/projects/gramps/files/Stable/3.3.1/',
        license          = "GPLv2 or greater",
        description      = "Gramps(Genealogical Research and Analysis Management Programming System)",
        long_description = ('gramps(Genealogical Research and Analysis Management Programming '
                            'System) is a GNOME based genealogy program supporting a Python based plugin system.'),
       windows           = [{"script"        : script,
                            "icon_resources" : [(1, "gramps/images/favicon2.ico")]
                           }],
       options           = {"py2exe": {
                            "includes"     : "pango,cairo,pangocairo,atk,gobject,gtk,gtksourceview2,gio",
                            "dll_excludes" : [
                                "iconv.dll","intl.dll","libatk-1.0-0.dll",
                                "libgdk_pixbuf-2.0-0.dll","libgdk-win32-2.0-0.dll",
                                "libglib-2.0-0.dll","libgmodule-2.0-0.dll",
                                "libgobject-2.0-0.dll","libgthread-2.0-0.dll",
                                "libgtk-win32-2.0-0.dll","libpango-1.0-0.dll",
                                "libpangowin32-1.0-0.dll"]}
                           },
        data_files       = DATA_FILES + os_files() + trans_files(),
        packages         = package_files,
        scripts          = script,
        platforms        = ['Linux', 'FreeBSD', 'Mac OSX', 'Windows'],
    )
    shutil.copytree("C:\gtksourceview\share\gtksourceview-2.0", "dist\share\gtksourceview-2.0")
    info("remember to copy 7za.exe to the dist folder")

else:
    DATA_FILES       = [
                        ("share/icons/hicolor/scalable/apps", ["gramps/images/gramps.svg"]),
                        ("share/gramps/glade", glob.glob("gramps/glade/*.*")),
                        ("share/mime/packages", ["data/gramps.xml"]),
                        ("share/mime-info", ["data/gramps.mime", "data/gramps.keys"]),
                        ("share/application-registry", ["data/gramps.applications"]),
                        ("share/man/man1", ["data/man/gramps.1.gz"]) ]

    setup (
        name             = 'gramps',
        version          = GRAMPS_VERSION,
        author           = 'Gramps Development Team',
        author_email     = 'benny.malengier@gmail.com',
        url              = 'http://gramps-project.org/',
        download_url     = 'http://sourceforge.net/projects/gramps/files/Stable/3.3.1/',
        license          = "GPLv2 or greater",
        description      = "Gramps(Genealogical Research and Analysis Management Programming System)",
        long_description = ('Gramps(Genealogical Research and Analysis Management Programming '
                        'System) is a GNOME based genealogy program supporting a Python based plugin system.'),
        data_files       = DATA_FILES + os_files() + trans_files(),
        packages         = package_files,
        scripts          = script,
        platforms        = ['Linux', 'FreeBSD', 'Mac OSX', 'Windows'],
        cmdclass         = {'build'        : GrampsBuildData,
                            'install_data' : GrampsInstallData,
                            'install'      : GrampsInstall,
                            'uninstall'    : GrampsUninstall,
                            'clean'        : GrampsClean},
    )
    bash_string = "update-desktop-database"
    subprocess.call(bash_string, shell=True)
