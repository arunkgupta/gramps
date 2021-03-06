#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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

# webapp/reports.py
# $Id$

# imports for import/export:

from gramps.gen.dbstate import DbState
from gramps.cli.grampscli import CLIManager
from gramps.gen.plug import BasePluginManager
import os

# Example for running a report:
# ------------------------------
# from gramps.cli.plug import run_report
# from django.conf import settings
# import webapp.settings as default_settings
# try:
#     settings.configure(default_settings)
# except:
#     pass
# import dbdjango
# db = dbdjango.DbDjango()
# run_report(db, "ancestor_report", off="txt", of="ar.txt", pid="I0363")

def get_plugin_options(db, pid):
    """
    Get the default options and help for this plugin.
    """
    dbstate = DbState()
    climanager = CLIManager(dbstate, False) # do not load db_loader
    climanager.do_reg_plugins(dbstate, None)
    pmgr = BasePluginManager.get_instance()
    pdata = pmgr.get_plugin(pid)
    if hasattr(pdata, "optionclass") and pdata.optionclass:
        mod = pmgr.load_plugin(pdata)
        optionclass = eval("mod." + pdata.optionclass)
        optioninstance = optionclass("Name", db)
        optioninstance.load_previous_values()
        return optioninstance.options_dict, optioninstance.options_help
    else:
        return {}, {}

def import_file(db, filename, user):
    """
    Import a file (such as a GEDCOM file) into the given db.

    >>> import_file(DbDjango(), "/home/user/Untitled_1.ged", User())
    """
    from grampsdb.models import Person
    dbstate = DbState()
    climanager = CLIManager(dbstate, False) # do not load db_loader
    climanager.do_reg_plugins(dbstate, None)
    pmgr = BasePluginManager.get_instance()
    (name, ext) = os.path.splitext(os.path.basename(filename))
    format = ext[1:].lower()
    import_list = pmgr.get_reg_importers()
    for pdata in import_list:
        if format == pdata.extension:
            mod = pmgr.load_plugin(pdata)
            if not mod:
                for item in pmgr.get_fail_list():
                    name, error_tuple, pdata = item
                    # (filename, (exception-type, exception, traceback), pdata)
                    etype, exception, traceback = error_tuple
                    print "ERROR:", name, exception
                return False
            import_function = getattr(mod, pdata.import_function)
            db.prepare_import()
            retval = import_function(db, filename, user)
            db.commit_import()
            # FIXME: need to call probably_alive
            for person in Person.objects.all():
                person.probably_alive = not bool(person.death)
                person.save()
            return retval
    return False

def download(url, filename=None):
    import urllib2
    import shutil
    import urlparse
    def getFilename(url,openUrl):
        if 'Content-Disposition' in openUrl.info():
            # If the response has Content-Disposition, try to get filename from it
            cd = dict(map(
                lambda x: x.strip().split('=') if '=' in x else (x.strip(),''),
                openUrl.info().split(';')))
            if 'filename' in cd:
                fname = cd['filename'].strip("\"'")
                if fname: return fname
        # if no filename was found above, parse it out of the final URL.
        return os.path.basename(urlparse.urlsplit(openUrl.url)[2])
    r = urllib2.urlopen(urllib2.Request(url))
    success = None
    try:
        filename = filename or "/tmp/%s" % getFilename(url,r)
        with open(filename, 'wb') as f:
            shutil.copyfileobj(r,f)
        success = filename
    finally:
        r.close()
    return success

def export_file(db, filename, user):
    """
    Export the db to a file (such as a GEDCOM file).

    >>> export_file(DbDjango(), "/home/user/Untitled_1.ged", User())
    """
    dbstate = DbState()
    climanager = CLIManager(dbstate, False) # do not load db_loader
    climanager.do_reg_plugins(dbstate, None)
    pmgr = BasePluginManager.get_instance()
    (name, ext) = os.path.splitext(os.path.basename(filename))
    format = ext[1:].lower()
    export_list = pmgr.get_reg_exporters()
    for pdata in export_list:
        if format == pdata.extension:
            mod = pmgr.load_plugin(pdata)
            if not mod:
                for item in pmgr.get_fail_list():
                    name, error_tuple, pdata = item
                    etype, exception, traceback = error_tuple
                    print "ERROR:", name, exception
                return False
            export_function = getattr(mod, pdata.export_function)
            export_function(db, filename, user)
            return True
    return False

