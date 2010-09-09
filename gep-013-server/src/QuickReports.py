#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007  B. Malengier
# Copyright (C) 2008  Brian G. Matherly
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

"""
This module provides the functions to build the quick report context menu's
"""

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
from gettext import gettext as _
from cStringIO import StringIO

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
log = logging.getLogger(".QuickReports")

#-------------------------------------------------------------------------
#
# GNOME modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------

from gen.plug import PluginManager
from ReportBase  import (CATEGORY_QR_PERSON, CATEGORY_QR_FAMILY,
                        CATEGORY_QR_EVENT, CATEGORY_QR_SOURCE, CATEGORY_QR_MISC,
                        CATEGORY_QR_PLACE, CATEGORY_QR_REPOSITORY)


def create_quickreport_menu(category,dbstate,uistate, handle) :
    """ This functions querries the registered quick reports with 
            quick_report_list of _PluginMgr.py
        It collects the reports of the requested category, which must be one of
                        CATEGORY_QR_PERSON, CATEGORY_QR_FAMILY,
                        CATEGORY_QR_EVENT, CATEGORY_QR_SOURCE,
                        CATEGORY_QR_PLACE, CATEGORY_QR_REPOSITORY
        It constructs the ui string of the quick report menu, and it's actions
        The action callback function is constructed, using the dbstate and the
            handle as input method.
        A tuple is returned, containing the ui string of the quick report menu,
        and its associated actions
    """

    actions = []
    ofile = StringIO()
    ofile.write('<menu action="QuickReport">')
    
    actions.append(('QuickReport', None, _("Quick View"), None, None, None))
        
    menu = gtk.Menu()
    menu.show()
    
    #select the reports to show
    showlst = []
    pmgr = PluginManager.get_instance()
    for item in pmgr.get_quick_report_list():
        if not item[8] and item[2] == category :
            #add tuple function, translated name, name, status
            showlst.append((item[0], item[1], item[3], item[5]))
            
    showlst.sort(by_menu_name)
    for report in showlst:
        new_key = report[2].replace(' ', '-')
        ofile.write('<menuitem action="%s"/>' % new_key)
        actions.append((new_key, None, report[1], None, None, 
                make_quick_report_callback(report, category, 
                                           dbstate, uistate, handle)))
    ofile.write('</menu>')
    
    return (ofile.getvalue(), actions)

def by_menu_name(first, second):
    return cmp(first[1], second[1])

def make_quick_report_callback(lst, category, dbstate, uistate, handle):
    return lambda x: run_report(dbstate, uistate, category, handle, lst[0])

def get_quick_report_list(qv_category=None):
    """
    Returns a list of quick views: [(translated name, category, name, status)]
    CATEGORY_QR_PERSON, CATEGORY_QR_FAMILY, CATEGORY_QR_EVENT, 
    CATEGORY_QR_SOURCE, CATEGORY_QR_MISC, CATEGORY_QR_PLACE, 
    CATEGORY_QR_REPOSITORY or None for all
    """
    names = []
    pmgr = PluginManager.get_instance()
    for item in pmgr.get_quick_report_list():
        if qv_category == item[2] or qv_category is None:
            names.append(item[1:]) # (see below for item struct)
    return names

def run_quick_report_by_name(dbstate, uistate, report_name, handle, **kwargs):
    # [0] - function 
    # [1] - translated name
    # [2] - category
    # [3] - name
    # [5] - status
    report = None
    pmgr = PluginManager.get_instance()
    for item in pmgr.get_quick_report_list():
        if item[3] == report_name:
            report = item
            break
    if report:
        return run_report(dbstate, uistate, report[2], handle, report[0], **kwargs)
    else:
        raise AttributeError, ("No such quick report '%s'" % report_name)

def run_quick_report_by_name_direct(report_name, database, document, handle):
    """
    Useful for running one quick report from another
    """
    from docgen import TextBufDoc
    from Simple import make_basic_stylesheet
    report = None
    pmgr = PluginManager.get_instance()
    for item in pmgr.get_quick_report_list():
        if item[3] == report_name:
            report = item
            break
    if report:
        # FIXME: allow auto lookup of obj like below?
        d = TextBufDoc(make_basic_stylesheet(), None)
        d.dbstate = document.dbstate
        d.uistate = document.uistate
        d.open("")
        retval = report[0](database, d, handle)
        d.close()
        return retval
    else:
        raise AttributeError, ("No such quick report '%s'" % report_name)
                            
def run_report(dbstate, uistate, category, handle, func, **kwargs):
        """
        Run a Quick Report.
        kwargs can take an optional document=obj to pass the report
        the document, rather than putting it in a new window.
        """
        from docgen import TextBufDoc
        from Simple import make_basic_stylesheet
        container = None
        if handle:
            d = TextBufDoc(make_basic_stylesheet(), None)
            d.dbstate = dbstate
            d.uistate = uistate
            if "container" in kwargs:
                container = kwargs["container"]
                del kwargs["container"]
                d.change_active = False
            else:
                d.change_active = True
            if isinstance(handle, basestring): # a handle
                if category == CATEGORY_QR_PERSON :
                    obj = dbstate.db.get_person_from_handle(handle)
                elif category == CATEGORY_QR_FAMILY :
                    obj = dbstate.db.get_family_from_handle(handle)
                elif category == CATEGORY_QR_EVENT :
                    obj = dbstate.db.get_event_from_handle(handle)
                elif category == CATEGORY_QR_SOURCE :
                    obj = dbstate.db.get_source_from_handle(handle)
                elif category == CATEGORY_QR_PLACE :
                    obj = dbstate.db.get_place_from_handle(handle)
                elif category == CATEGORY_QR_REPOSITORY :
                    obj = dbstate.db.get_repository_from_handle(handle)
                elif category == CATEGORY_QR_MISC:
                    obj = handle
                else: 
                    obj = None
            else: # allow caller to send object directly
                obj = handle
            if obj:
                if container:
                    result = d.open("", container=container)
                    func(dbstate.db, d, obj, **kwargs)
                    return result
                else:
                    d.open("")
                    retval = func(dbstate.db, d, obj, **kwargs)
                    d.close()
                    return retval
            else:
                print "QuickView Error: failed to run report: no obj"
        else:
            print "QuickView Error: handle is not set"
