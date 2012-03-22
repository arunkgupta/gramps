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

from distutils.cmd import Command
from distutils.core import setup
from distutils.command.build import build
from distutils.command.install_data import install_data
from distutils.command.install import INSTALL_SCHEMES
import distutils.command.clean

import sys
import glob
import os, os.path
import subprocess
import platform
import shutil

try:
    import py2exe
except:
    pass

# get the root directory so that everything can be absolute...
ROOT_DIR = os.getcwd()

PO_DIR = os.path.join(ROOT_DIR, 'po')
MO_DIR = os.path.join(ROOT_DIR, 'build', 'mo')

if sys.version < '2.6':
    sys.exit('Error: Python-2.6 or newer is required. Current version:\n %s'
             % sys.version)

if os.name == 'nt':
    script = [os.path.join(ROOT_DIR, 'windows','gramps.pyw')]
elif os.name == 'darwin':
    script = [os.path.join(ROOT_DIR, 'mac','gramps.launcher.sh')]
else:
    # os.name == 'posix'
    script = [os.path.join(ROOT_DIR, 'gramps.sh')]

if platform.system() == 'FreeBSD':
    man_dir = 'man'
else:
    man_dir = os.path.join('share', 'man')

class osx_install_data(install_data):
    # On MacOS, the platform-specific lib dir is /System/Library/Framework/Python/.../
    # which is wrong. Python 2.5 supplied with MacOS 10.5 has an Apple-specific fix
    # for this in distutils.command.install_data#306. It fixes install_lib but not
    # install_data, which is why we roll our own install_data class.

    def finalize_options(self):
        # By the time finalize_options is called, install.install_lib is set to the
        # fixed directory, so we set the installdir to install_lib. The
        # install_data class uses ('install_data', 'install_dir') instead.
        self.set_undefined_options('install', ('install_lib', 'install_dir'))
        install_data.finalize_options(self)

if sys.platform == "darwin":
    cmdclasses = {'install_data': osx_install_data} 
else: 
    cmdclasses = {'install_data': install_data} 

def fullsplit(path, result = None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

def modules_check():
    '''Check if necessary modules is installed.
    The function is executed by distutils (by the install command).'''
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

# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

'''
Custom command for 'python setup.py build' ...
'''
class BuildData(build):
    def initialize_options(self):
        
        if os.name == 'posix':
            # initial makefiles ... create launcher and generate const.py
            # see script !
            const_file    = os.path.join(os.getcwd(), 'gramps', 'const.py')
            const_in_file = os.path.join(os.getcwd(), 'gramps', 'const.py.in')
            if (os.path.isfile(const_in_file) and not os.path.isfile(const_file)):
                shutil.copy(const_in_file, const_file)

            gramps_build_dir = os.path.join(os.getcwd(), 'build', 'gramps')
            if (not os.path.isdir(gramps_build_dir) and not os.path.islink(gramps_build_dir)):
                os.makedirs(gramps_build_dir)

            # related translations files
            os.system('intltool-merge -d po/ data/gramps.desktop.in data/gramps.desktop')
            os.system('intltool-merge -x po/ data/gramps.xml.in data/gramps.xml')
            os.system('intltool-merge -k po/ data/gramps.keys.in data/gramps.keys')
            
    def run (self):
        
        # Run upgrade pre script
        # /!\ should be gramps.sh with variables
        
        for po in glob.glob(os.path.join(PO_DIR, '*.po')):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(MO_DIR, lang, 'gramps.mo')
            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                os.makedirs(directory)
            if os.name == 'posix':
                os.system('msgfmt %s/%s.po -o %s' % (PO_DIR, lang, mo))
            print (directory)
                
    def finalize_options(self):
        pass
            
'''
Custom command for 'python setup.py install' ...
'''
class InstallData(install_data):
    def run (self):
        
        install_data.run(self)
    
    def finalize_options(self):
        
        if os.name == 'posix':
            #update the XDG Shared MIME-Info database cache
            sys.stdout.write('Updating the Shared MIME-Info database cache.\n')
            subprocess.call(["update-mime-database", os.path.join(sys.prefix, 'share', 'mime')])

            # update the mime.types database (debian, ubuntu)
            # sys.stdout.write('Updating the mime.types database\n')
            # subprocess.call("update-mime")

            # update the XDG .desktop file database
            sys.stdout.write('Updating the .desktop file database.\n')
            subprocess.call(["update-desktop-database"])
            
            # ldconfig
            
'''
Standard command for 'python setup.py install' ...
'''
class Install(Command):
    
    description = "Attempt an install and generate a log file"
    
    user_options = [('fake', None, 'Override')]
    
    def initialize_options(self):
        pass
    
    def run(self):
        pass
        
    def finalize_options(self):
        pass

'''
Custom command for uninstalling
'''
class UnInstall(Command):
    
    description = "Attempt an uninstall from an install log file"

    user_options = [('log=', None, 'Installation record filename')]

    def initialize_options(self):
        self.log = 'log'

    def finalize_options(self):
        pass

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
                print ("removing %s" % repr(file))
            if not self.dry_run:
                try:
                    os.unlink(file)
                except OSError, e:
                    warn("could not delete: %s" % repr(file))
            elif not os.path.isdir(file):
                print ("skipping %s" % repr(file))

        dirs = set()
        for file in reversed(sorted(files)):
            dir = os.path.dirname(file)
            if dir not in dirs and os.path.isdir(dir) and len(os.listdir(dir)) == 0:
                dirs.add(dir)
                # Only nuke empty Python library directories, else we could destroy
                # e.g. locale directories we're the only app with a .mo installed for.
            if dir.find("dist-packages") > 0:
                print ("removing %s" % repr(dir))
                if not self.dry_run:
                    try:
                        os.rmdir(dir)
                    except OSError, e:
                        warn("could not remove directory: %s" % str(e))
            else:
                print ("skipping empty directory %s" % repr(dir))

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
    Natural Language :: Portuguese (Portugal)
    Natural Language :: Russian
    Natural Language :: Slovak
    Natural Language :: Slovenian
    Natural Language :: Spanish
    Natural Language :: Swedish
    Natural Language :: Ukrainian
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

def main():
    # turn off warnings when deprecated modules are imported
    import warnings
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    setup(# PyPI Metadata (PEP 301)
        name         = "gramps",
        version      = "3.5.0",
        description  = 'Gramps (Genealogical Research and Analysis Management Programming System)',
        author       = 'Gramps Development Team',
        author_email = 'don@gramps-project.org',
        url          = 'http://gramps-project.org',
       license       = 'GNU GPL v2 or greater',
        classifiers  = [x for x in CLASSIFIERS.split("\n") if x],
        platforms    = ["Many"],

        requires     = ['pygtk', 'pycairo', 'pygobject'],
        scripts      = script,
        cmdclass     = {
                    'build': BuildData,
                    'install': InstallData, # override Install!
                    #'install_data': InstallData, # python setup.py --help-commands
                    'uninstall': UnInstall} 
    )

# --install-platlib
if __name__ == '__main__':
    main()
