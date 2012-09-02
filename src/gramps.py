#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2009       Benny Malengier
# Copyright (C) 2009-2010  Stephen George
# Copyright (C) 2010       Doug Blank <doug.blank@gmail.com>
# Copyright (C) 2011       Paul Franklin
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

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import sys
## hack to avoid mentioning 'utf8' encoding everywhere unicode or str is is used
reload(sys)
sys.setdefaultencoding('utf8')
##
import os
import signal
import gettext
_ = gettext.gettext
import locale
import logging

LOG = logging.getLogger(".")

from subprocess import Popen, PIPE

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.const import APP_GRAMPS, USER_DIRLIST, HOME_DIR, VERSION_TUPLE
from gen.constfunc import win
#-------------------------------------------------------------------------
#
# Setup logging
#
# Ideally, this needs to be done before any Gramps modules are imported, so that
# any code that is executed as the modules are imported can log errors or
# warnings. Errors and warnings are particularly applicable to TransUtils and
# setting up internationalisation in this module. const and constfunc have to be
# imported before this code is executed because they are used in this code.
#-------------------------------------------------------------------------
"""Setup basic logging support."""

# Setup a formatter
form = logging.Formatter(fmt="%(relativeCreated)d: %(levelname)s: %(filename)s: line %(lineno)d: %(message)s")

# Create the log handlers
if win():
    # If running in GUI mode redirect stdout and stderr to log file
    if hasattr(sys.stdout, "fileno") and sys.stdout.fileno() < 0:
        logfile = os.path.join(HOME_DIR, 
            "Gramps%s%s.log") % (VERSION_TUPLE[0], 
            VERSION_TUPLE[1])
        # We now carry out the first step in build_user_paths(), to make sure
        # that the user home directory is available to store the log file. When
        # build_user_paths() is called, the call is protected by a try...except
        # block, and any failure will be logged. However, if the creation of the
        # user directory fails here, there is no way to report the failure,
        # because stdout/stderr are not available, and neither is the logfile.
        if os.path.islink(HOME_DIR):
            pass # ok
        elif not os.path.isdir(HOME_DIR):
            os.makedirs(HOME_DIR)
        sys.stdout = sys.stderr = open(logfile, "w")
stderrh = logging.StreamHandler(sys.stderr)
stderrh.setFormatter(form)
stderrh.setLevel(logging.DEBUG)

# Setup the base level logger, this one gets
# everything.
l = logging.getLogger()
l.setLevel(logging.WARNING)
l.addHandler(stderrh)

# put a hook on to catch any completely unhandled exceptions.
def exc_hook(type, value, tb):
    if type == KeyboardInterrupt:
        # Ctrl-C is not a bug.
        return
    if type == IOError:
        # strange Windows logging error on close
        return
    import traceback
    LOG.error("Unhandled exception\n" +
              "".join(traceback.format_exception(type, value, tb)))

sys.excepthook = exc_hook

from gen.mime import mime_type_is_defined
from gen.utils.trans import LOCALEDOMAIN, LOCALEDIR, setup_windows_gettext
#-------------------------------------------------------------------------
#
# Load internationalization setup
#
#-------------------------------------------------------------------------

#the order in which bindtextdomain on gettext and on locale is called
#appears important, so we refrain from doing first all gettext.
#
#setup_gettext()
gettext.bindtextdomain(LOCALEDOMAIN, LOCALEDIR)
try:
    locale.setlocale(locale.LC_ALL,'')
except:
    logging.warning(_("WARNING: Setting locale failed. Please fix the "
        "LC_* and/or the LANG environment variables to prevent this error"))
    try:
        # It is probably not necessary to set the locale to 'C'
        # because the locale will just stay at whatever it was,
        # which at startup is "C".
        # however this is done here just to make sure that the locale
        # functions are working 
        locale.setlocale(locale.LC_ALL,'C')
    except:
        logging.warning(_("ERROR: Setting the 'C' locale didn't work either"))
        # FIXME: This should propagate the exception,
        # if that doesn't break Gramps under Windows
        # raise

gettext.textdomain(LOCALEDOMAIN)
gettext.install(LOCALEDOMAIN, localedir=None, unicode=1) #None is sys default locale

if hasattr(os, "uname"):
    operating_system = os.uname()[0]
else:
    operating_system = sys.platform

if win(): # Windows
    setup_windows_gettext()
elif operating_system == 'FreeBSD':
    try:
        gettext.bindtextdomain(LOCALEDOMAIN, LOCALEDIR)
    except locale.Error:
        logging.warning('No translation in some Gtk.Builder strings, ')
elif operating_system == 'OpenBSD':
    pass
else: # normal case
    try:
        locale.bindtextdomain(LOCALEDOMAIN, LOCALEDIR)
        #locale.textdomain(LOCALEDOMAIN)
    except locale.Error:
        logging.warning('No translation in some Gtk.Builder strings, ')

#-------------------------------------------------------------------------
#
# Minimum version check
#
#-------------------------------------------------------------------------

MIN_PYTHON_VERSION = (2, 7, 0, '', 0)
if not sys.version_info >= MIN_PYTHON_VERSION :
    logging.warning(_("Your Python version does not meet the "
             "requirements. At least python %(v1)d.%(v2)d.%(v3)d is needed to"
             " start Gramps.\n\n"
             "Gramps will terminate now.") % {
             'v1': MIN_PYTHON_VERSION[0], 
             'v2': MIN_PYTHON_VERSION[1],
             'v3': MIN_PYTHON_VERSION[2]})
    sys.exit(1)

#-------------------------------------------------------------------------
#
# gramps libraries
#
#-------------------------------------------------------------------------
try:
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)
except:
    pass

args = sys.argv

def build_user_paths():
    """ check/make user-dirs on each Gramps session"""
    for path in USER_DIRLIST:
        if os.path.islink(path):
            pass # ok
        elif not os.path.isdir(path):
            os.makedirs(path)

def show_settings():
    """
    Shows settings of all of the major components.
    """
    py_str = '%d.%d.%d' % sys.version_info[:3]
    try:
        from gi.repository import Gtk
        try:
            gtkver_str = '%d.%d.%d' % (Gtk.get_major_version(), 
                        Gtk.get_minor_version(), Gtk.get_micro_version())
        except : # any failure to 'get' the version
            gtkver_str = 'unknown version'
    except ImportError:
        gtkver_str = 'not found'
    # no DISPLAY is a RuntimeError in an older pygtk (e.g. 2.17 in Fedora 14)
    except RuntimeError:
        gtkver_str = 'DISPLAY not set'
    #exept TypeError: To handle back formatting on version split

    try:
        from gi.repository import GObject
        try:
            gobjectver_str = '%d.%d.%d' % GObject.pygobject_version
        except :# any failure to 'get' the version
            gobjectver_str = 'unknown version'

    except ImportError:
        gobjectver_str = 'not found'

    try:
        import cairo
        try:
            cairover_str = '%d.%d.%d' % cairo.version_info 
        except :# any failure to 'get' the version
            cairover_str = 'unknown version'

    except ImportError:
        cairover_str = 'not found'

    try:
        from gi import Repository
        repository = Repository.get_default()
        if repository.enumerate_versions("OsmGpsMap"):
            from gi.repository import OsmGpsMap as osmgpsmap
            try:
                osmgpsmap_str = osmgpsmap._version
            except :# any failure to 'get' the version
                osmgpsmap_str = 'unknown version'
        else:
            osmgpsmap_str = 'not found'

    except ImportError:
        osmgpsmap_str = 'not found'

    try:
        import pyexiv2
        try:
            pyexiv2_str = '%d.%d.%d' % pyexiv2.version_info 
        except :# any failure to 'get' the version
            pyexiv2_str = 'unknown version'

    except ImportError:
        pyexiv2_str = 'not found'

    from gen.config import config
    usebsddb3 = config.get('preferences.use-bsddb3')
    try:
        if usebsddb3:
            import bsddb3 as bsddb
        else:
            import bsddb
        bsddb_str = bsddb.__version__
        bsddb_db_str = str(bsddb.db.version())
    except:
        bsddb_str = 'not found'
        bsddb_db_str = 'not found'

    try: 
        from gen.const import VERSION
        gramps_str = VERSION
    except:
        gramps_str = 'not found'

    if hasattr(os, "uname"):
        kernel = os.uname()[2]
    else:
        kernel = None

    lang_str = os.environ.get('LANG','not set')
    language_str = os.environ.get('LANGUAGE','not set')
    grampsi18n_str = os.environ.get('GRAMPSI18N','not set')
    grampshome_str = os.environ.get('GRAMPSHOME','not set')
    grampsdir_str = os.environ.get('GRAMPSDIR','not set')

    try:
        dotversion_str = Popen(['dot', '-V'], stderr=PIPE).communicate(input=None)[1]
        if dotversion_str:
            dotversion_str = dotversion_str.replace('\n','')
    except:
        dotversion_str = 'Graphviz not in system PATH'

    try:
        if win():
            gsversion_str = Popen(['gswin32c', '--version'], stdout=PIPE).communicate(input=None)[0]
        else:
            gsversion_str = Popen(['gs', '--version'], stdout=PIPE).communicate(input=None)[0]
        if gsversion_str:
            gsversion_str = gsversion_str.replace('\n', '')
    except:
        gsversion_str = 'Ghostscript not in system PATH'

    os_path = os.environ.get('PATH','not set')
    os_path = os_path.split(os.pathsep)
    
    print "Gramps Settings:"
    print "----------------"
    print ' python    : %s' % py_str
    print ' gramps    : %s' % gramps_str
    print ' gtk++     : %s' % gtkver_str
    print ' gobject   : %s' % gobjectver_str
    if usebsddb3:
        print ' Using bsddb3'
    else:
        print ' Not using bsddb3'
    print ' bsddb     : %s' % bsddb_str
    print ' bsddb.db  : %s' % bsddb_db_str
    print ' cairo     : %s' % cairover_str
    print ' osmgpsmap : %s' % osmgpsmap_str
    print ' pyexiv2   : %s' % pyexiv2_str
    print ' o.s.      : %s' % operating_system
    if kernel:
        print ' kernel    : %s' % kernel
    print
    print "Environment settings:"
    print "---------------------"
    print ' LANG      : %s' % lang_str
    print ' LANGUAGE  : %s' % language_str
    print ' GRAMPSI18N: %s' % grampsi18n_str
    print ' GRAMPSHOME: %s' % grampshome_str
    print ' GRAMPSDIR : %s' % grampsdir_str
    print ' PYTHONPATH:'
    for folder in sys.path:
        print "   ", folder
    print
    print "Non-python dependencies:"
    print "------------------------"
    print ' Graphviz  : %s' % dotversion_str
    print ' Ghostscr. : %s' % gsversion_str
    print
    print "System PATH env variable:"
    print "-------------------------"
    for folder in os_path:
        print "    ", folder
    print

def run():
    error = []
    
    try:
        build_user_paths()   
    except OSError, msg:
        error += [(_("Configuration error:"), str(msg))]
        return error
    except msg:
        LOG.error("Error reading configuration.", exc_info=True)
        return [(_("Error reading configuration"), str(msg))]
        
    if not mime_type_is_defined(APP_GRAMPS):
        error += [(_("Configuration error:"), 
                    _("A definition for the MIME-type %s could not "
                      "be found \n\n Possibly the installation of Gramps "
                      "was incomplete. Make sure the MIME-types "
                      "of Gramps are properly installed.")
                    % APP_GRAMPS)]
    
    #we start with parsing the arguments to determine if we have a cli or a
    # gui session

    if "-v" in sys.argv or "--version" in sys.argv:
        show_settings()
        return error

    from cli.argparser import ArgParser
    argv_copy = sys.argv[:]
    argpars = ArgParser(argv_copy)

    # Calls to LOG must be after setup_logging() and ArgParser() 
    LOG = logging.getLogger(".locale")
    if hasattr(locale, 'LC_CTYPE'):
        LOG.debug('Using locale: LC_CTYPE %s %s' %
                         locale.getlocale(locale.LC_CTYPE))
    else:
        LOG.debug('locale: LC_CTYPE is not defined')
    if hasattr(locale, 'LC_COLLATE'):
        LOG.debug('Using locale: LC_COLLATE %s %s' %
                         locale.getlocale(locale.LC_COLLATE))
    else:
        LOG.debug('locale: LC_COLLATE is not defined')
    if hasattr(locale, 'LC_TIME'):
        LOG.debug('Using locale: LC_TIME %s %s' %
                         locale.getlocale(locale.LC_TIME))
    else:
        LOG.debug('locale: LC_TIME is not defined')
    if hasattr(locale, 'LC_MONETARY'):
        LOG.debug('Using locale: LC_MONETARY %s %s' %
                         locale.getlocale(locale.LC_MONETARY))
    else:
        LOG.debug('locale: LC_MONETARY is not defined')
    if hasattr(locale, 'LC_MESSAGES'):
        LOG.debug('Using locale: LC_MESSAGES %s %s' %
                         locale.getlocale(locale.LC_MESSAGES))
    else:
        LOG.debug('locale: LC_MESSAGES is not defined')
    if hasattr(locale, 'LC_NUMERIC'):
        LOG.debug('Using locale: LC_NUMERIC %s %s' %
                         locale.getlocale(locale.LC_NUMERIC))
    else:
        LOG.debug('locale: LC_NUMERIC is not defined')
    if 'LANG' in os.environ:
        LOG.debug('Using LANG: %s' %
                         os.environ.get('LANG'))
    else:
        LOG.debug('environment: LANG is not defined')
    if 'LANGUAGE' in os.environ:
        LOG.debug('Using LANGUAGE: %s' %
                         os.environ.get('LANGUAGE'))
    else:
        LOG.debug('environment: LANGUAGE is not defined')
    
    if argpars.need_gui():
        #A GUI is needed, set it up
        if "--qml" in sys.argv:
            from guiQML.grampsqml import startqml
            startqml(error, argpars)
        else:
            try:
                from gui.grampsgui import startgtkloop
            # no DISPLAY is a RuntimeError in an older pygtk (e.g. F14's 2.17)
            except RuntimeError, msg:
                error += [(_("Configuration error:"), str(msg))]
                return error
            startgtkloop(error, argpars)
    else:
        #CLI use of GRAMPS
        argpars.print_help()
        argpars.print_usage()
        from cli.grampscli import startcli
        startcli(error, argpars)

errors = run()
if errors and isinstance(errors, list):
    for error in errors:
        logging.warning(error[0] + error[1])
