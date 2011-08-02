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

# $Id$

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os
import sys
import locale
import random
import time
import platform

from TransUtils import sgettext as _

#-------------------------------------------------------------------------
#
# GNOME/GTK
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from BasicUtils import name_displayer
import gen.lib
import Errors
from QuestionDialog import WarningDialog, ErrorDialog

from const import TEMP_DIR, USER_HOME, WINDOWS, MACOS, LINUX
import shutil

#-------------------------------------------------------------------------
#
# Constants from config .ini keys
#
#-------------------------------------------------------------------------
#obtain the values once, they do not change!
try:
    import Config
    _MAX_AGE_PROB_ALIVE   = Config.get(Config.MAX_AGE_PROB_ALIVE)
    _MAX_SIB_AGE_DIFF     = Config.get(Config.MAX_SIB_AGE_DIFF)
    _MIN_GENERATION_YEARS = Config.get(Config.MIN_GENERATION_YEARS)
    _AVG_GENERATION_GAP   = Config.get(Config.AVG_GENERATION_GAP)
except ImportError:
    # Utils used as module not part of GRAMPS
    _MAX_AGE_PROB_ALIVE   = 110
    _MAX_SIB_AGE_DIFF     = 20
    _MIN_GENERATION_YEARS = 13
    _AVG_GENERATION_GAP   = 20

#-------------------------------------------------------------------------
#
# Integer to String  mappings for constants
#
#-------------------------------------------------------------------------
gender = {
    gen.lib.Person.MALE    : _("male"), 
    gen.lib.Person.FEMALE  : _("female"), 
    gen.lib.Person.UNKNOWN : _("unknown"), 
    }

def format_gender( type):
    return gender.get(type[0], _("Invalid"))

confidence = {
    gen.lib.SourceRef.CONF_VERY_HIGH : _("Very High"), 
    gen.lib.SourceRef.CONF_HIGH      : _("High"), 
    gen.lib.SourceRef.CONF_NORMAL    : _("Normal"), 
    gen.lib.SourceRef.CONF_LOW       : _("Low"), 
    gen.lib.SourceRef.CONF_VERY_LOW  : _("Very Low"), 
   }

family_rel_descriptions = {
    gen.lib.FamilyRelType.MARRIED     : _("A legal or common-law relationship "
                                         "between a husband and wife"), 
    gen.lib.FamilyRelType.UNMARRIED   : _("No legal or common-law relationship "
                                         "between man and woman"), 
    gen.lib.FamilyRelType.CIVIL_UNION : _("An established relationship between "
                                         "members of the same sex"), 
    gen.lib.FamilyRelType.UNKNOWN     : _("Unknown relationship between a man "
                                         "and woman"), 
    gen.lib.FamilyRelType.CUSTOM      : _("An unspecified relationship between "
                                         "a man and woman"), 
    }


#-------------------------------------------------------------------------
#
# modified flag
#
#-------------------------------------------------------------------------
_history_brokenFlag = 0

def history_broken():
    global _history_brokenFlag
    _history_brokenFlag = 1

data_recover_msg = _('The data can only be recovered by Undo operation '
            'or by quitting with abandoning changes.')

def fix_encoding(value):
    if not isinstance(value, unicode):
        try:
            return unicode(value)
        except:
            try:
                codeset = locale.getpreferredencoding()
            except:
                codeset = "UTF-8"
            return unicode(value, codeset)
    else:
        return value

def xml_lang():
    loc = locale.getlocale()
    if loc[0] is None:
        return ""
    else:
        return loc[0].replace('_', '-')

#-------------------------------------------------------------------------
#
# force_unicode
#
#-------------------------------------------------------------------------

def force_unicode(n):
    if not isinstance(n, unicode):
        return (unicode(n).lower(), unicode(n))
    else:
        return (n.lower(), n)

#-------------------------------------------------------------------------
#
# Clears the modified flag.  Should be called after data is saved.
#
#-------------------------------------------------------------------------
def clearHistory_broken():
    global _history_brokenFlag
    _history_brokenFlag = 0

def wasHistory_broken():
    return _history_brokenFlag

#-------------------------------------------------------------------------
#
# Short hand function to return either the person's name, or an empty
# string if the person is None
#
#-------------------------------------------------------------------------

def family_name(family, db, noname=_("unknown")):
    """Builds a name for the family from the parents names"""

    father_handle = family.get_father_handle()
    mother_handle = family.get_mother_handle()
    father = db.get_person_from_handle(father_handle)
    mother = db.get_person_from_handle(mother_handle)
    if father and mother:
        fname = name_displayer.display(father)
        mname = name_displayer.display(mother)
        name = _("%(father)s and %(mother)s") % {
                    "father" : fname, 
                    "mother" : mname}
    elif father:
        name = name_displayer.display(father)
    elif mother:
        name = name_displayer.display(mother)
    else:
        name = noname
    return name

def family_upper_name(family, db):
    """Builds a name for the family from the parents names"""
    father_handle = family.get_father_handle()
    mother_handle = family.get_mother_handle()
    father = db.get_person_from_handle(father_handle)
    mother = db.get_person_from_handle(mother_handle)
    if father and mother:
        fname = father.get_primary_name().get_upper_name()
        mname = mother.get_primary_name().get_upper_name()
        name = _("%(father)s and %(mother)s") % {
            'father' : fname, 
            'mother' : mname 
            }
    elif father:
        name = father.get_primary_name().get_upper_name()
    else:
        name = mother.get_primary_name().get_upper_name()
    return name
        
#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def redraw_list(dlist, clist, func):
    clist.clear()
    
    index = 0
    for obj in dlist:
        col = 0
        node = clist.append()
        for data in func(obj):
            clist.set_value(node, col, data)
            col = col + 1
        index = index + 1
    return index

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def delete_selected(obj, dlist):
    sel = obj.get_selection()
    model, node = sel.get_selected()
    if node:
        index = model.get_path(node)[0]
        del dlist[index]
    return 1

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def add_menuitem(menu, msg, obj, func):
    item = gtk.MenuItem(msg)
    item.set_data('o', obj)
    item.connect("activate", func)
    item.show()
    menu.append(item)

#-------------------------------------------------------------------------
#
# Platform determination functions
#
#-------------------------------------------------------------------------

def lin():
    """
    Return True if a linux system
    Note: Normally do as linux in else statement of a check !
    """
    if platform.system() in LINUX:
        return True
    return False
    
def mac():
    """
    Return True if a Macintosh system
    """
    if platform.system() in MACOS:
        return True
    return False

def win():
    """
    Return True if a windows system
    """
    if platform.system() in WINDOWS:
        return True
    return False

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def find_file( filename):
    # try the filename we got
    try:
        fname = filename
        if os.path.isfile( filename):
            return( filename)
    except:
        pass
    
    # Build list of alternate encodings
    encodings = set()

    for enc in [sys.getfilesystemencoding, locale.getpreferredencoding]:
        try:
            encodings.add(enc)
        except:
            pass
    encodings.add('UTF-8')
    encodings.add('ISO-8859-1')

    for enc in encodings:
        try:
            fname = filename.encode(enc)
            if os.path.isfile( fname):
                return fname
        except:
            pass

    # not found
    return ''

def find_folder( filename):
    # try the filename we got
    try:
        fname = filename
        if os.path.isdir( filename):
            return( filename)
    except:
        pass
    
    # Build list of elternate encodings
    try:
        encodings = [sys.getfilesystemencoding(), 
                     locale.getpreferredencoding(), 
                     'UTF-8', 'ISO-8859-1']
    except:
        encodings = [sys.getfilesystemencoding(), 'UTF-8', 'ISO-8859-1']
    encodings = list(set(encodings))
    for enc in encodings:
        try:
            fname = filename.encode(enc)
            if os.path.isdir( fname):
                return fname
        except:
            pass

    # not found
    return ''

def get_unicode_path(path):
    """
    Return the Unicode version of a path string.

    @type  path: str
    @param path: The path to be converted to Unicode
    @rtype:      unicode
    @return:     The Unicode version of path.
    """
    if os.sys.platform == "win32":
        return unicode(path)
    else:
        return unicode(path,sys.getfilesystemencoding())

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def build_string_optmenu(mapping, start_val):
    index = 0
    start_index = 0
    keys = mapping.keys()
    keys.sort()
    myMenu = gtk.Menu()

    for key in keys:
        if key == "default":
            menuitem = gtk.MenuItem(_("default"))
        else:
            menuitem = gtk.MenuItem(key)
        menuitem.set_data("d", mapping[key])
        menuitem.set_data("l", key)
        menuitem.show()
        myMenu.append(menuitem)
        if key == start_val:
            start_index = index
        index = index + 1
    
    if start_index:
        myMenu.set_active(start_index)
    return myMenu


#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def build_columns(tree, list):
    cnum = 0
    for name in list:
        renderer = gtk.CellRendererText()
        renderer.set_fixed_height_from_font(1)
        column = gtk.TreeViewColumn(name[0], renderer, text=cnum)
        column.set_min_width(name[1])
        if name[2] >= 0:
            column.set_sort_column_id(name[2])
        if name[0] == '':
            column.set_clickable(True)
            column.set_visible(False)
        cnum = cnum + 1
        tree.append_column(column)

#-------------------------------------------------------------------------
#
#  Iterate over ancestors.
#
#-------------------------------------------------------------------------
def for_each_ancestor(db, start, func, data):
    """
    Recursively iterate (breadth-first) over ancestors of
    people listed in start.
    Call func(data, pid) for the Id of each person encountered.
    Exit and return 1, as soon as func returns true.
    Return 0 otherwise.
    """
    todo = start
    done_ids = set()
    while len(todo):
        p_handle = todo.pop()
        p = db.get_person_from_handle(p_handle)
        # Don't process the same handle twice.  This can happen
        # if there is a cycle in the database, or if the
        # initial list contains X and some of X's ancestors.
        if p_handle in done_ids:
            continue
        done_ids.add(p_handle)
        if func(data, p_handle):
            return 1
        for fam_handle in p.get_parent_family_handle_list():
            fam = db.get_family_from_handle(fam_handle)
            if fam:
                f_handle = fam.get_father_handle()
                m_handle = fam.get_mother_handle()
                if f_handle: todo.append(f_handle)
                if m_handle: todo.append(m_handle)
    return 0

def title(n):
    return '<span weight="bold" size="larger">%s</span>' % n

def set_title_label(xmlobj, t):
    title_label = xmlobj.get_widget('title')
    title_label.set_text('<span weight="bold" size="larger">%s</span>' % t)
    title_label.set_use_markup(True)

from warnings import warn
def set_titles(window, title, t, msg=None):
    warn('The Utils.set_titles is deprecated. Use ManagedWindow methods')

def gfloat(val):
    """Convert to floating number, taking care of possible locale differences.
    
    Useful for reading float values from text entry fields 
    while under non-English locale.
    """

    try:
        return float(val)
    except:
        try:
            return float(val.replace('.', ', '))
        except:
            return float(val.replace(', ', '.'))
    return 0.0

def gformat(val):
    """Performs ('%.3f' % val) formatting with the resulting string always 
    using dot ('.') as a decimal point.
    
    Useful for writing float values into XML when under non-English locale.
    """

    decimal_point = locale.localeconv()['decimal_point']
    return_val = "%.3f" % val
    return return_val.replace(decimal_point, '.')

def search_for(name):
    if name.startswith( '"' ):
        name = name.split('"')[1]
    else:
        name = name.split()[0]
    if os.sys.platform == "win32":
        for i in os.environ['PATH'].split(';'):
            fname = os.path.join(i, name)
            if os.access(fname, os.X_OK) and not os.path.isdir(fname):
                return 1
    else:
        for i in os.environ['PATH'].split(':'):
            fname = os.path.join(i, name)
            if os.access(fname, os.X_OK) and not os.path.isdir(fname):
                return 1
    return 0
                  
#-------------------------------------------------------------------------
#
#  Change label appearance
#
#-------------------------------------------------------------------------
def bold_label(label, widget=None):
    if label.__class__ == gtk.Label:
        text = unicode(label.get_text())
        text = text.replace('<i>', '')
        text = text.replace('</i>', '')
        label.set_text("<b>%s</b>" % text )
        label.set_use_markup(True)
    else:
        clist = label.get_children()
        text = unicode(clist[1].get_text())
        text = text.replace('<i>', '')
        text = text.replace('</i>', '')
        clist[0].show()
        clist[1].set_text("<b>%s</b>" % text )
        clist[1].set_use_markup(True)
    if widget:
        widget.window.set_cursor(None)
        
def unbold_label(label, widget=None):
    if label.__class__ == gtk.Label:
        text = unicode(label.get_text())
        text = text.replace('<b>', '')
        text = text.replace('</b>', '')
        text = text.replace('<i>', '')
        text = text.replace('</i>', '')
        label.set_text(text)
        label.set_use_markup(False)
    else:
        clist = label.get_children()
        text = unicode(clist[1].get_text())
        text = text.replace('<b>', '')
        text = text.replace('</b>', '')
        text = text.replace('<i>', '')
        text = text.replace('</i>', '')
        clist[0].hide()
        clist[1].set_text(text)
        clist[1].set_use_markup(False)
    if widget:
        widget.window.set_cursor(None)

def temp_label(label, widget=None):
    if label.__class__ == gtk.Label:
        text = unicode(label.get_text())
        text = text.replace('<b>', '')
        text = text.replace('</b>', '')
        label.set_text("<i>%s</i>" % text )
        label.set_use_markup(True)
    else:
        clist = label.get_children()
        text = unicode(clist[1].get_text())
        text = text.replace('<b>', '')
        text = text.replace('</b>', '')
        clist[0].hide()
        clist[1].set_text("<i>%s</i>" % text )
        clist[1].set_use_markup(True)
    if widget:
        widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))

#-------------------------------------------------------------------------
#
# create_id
#
#-------------------------------------------------------------------------
rand = random.Random(time.time())

def create_id():
    return "%08x%08x" % ( int(time.time()*10000), 
                          rand.randint(0, sys.maxint))

#-------------------------------------------------------------------------
#
# probably_alive
#
#-------------------------------------------------------------------------
def probably_alive(person, db, current_date=None, limit=0):
    """Return true if the person may be alive on current_date.

    This works by a process of emlimination. If we can't find a good
    reason to believe that someone is dead then we assume they must
    be alive.

    current_date - a date object that is not estimated or modified
                   (defaults to today)
    limit        - number of years to check beyond death_date
    """
    if current_date is None:
        current_date = gen.lib.Date()
        # yr, mon, day:
        current_date.set_yr_mon_day(*time.localtime(time.time())[0:3])

    death_date = None
    # If the recorded death year is before current year then
    # things are simple.
    death_ref = person.get_death_ref()
    if death_ref and death_ref.get_role() == gen.lib.EventRoleType.PRIMARY:
        death = db.get_event_from_handle(death_ref.ref)
        if death.get_date_object().get_start_date() != gen.lib.Date.EMPTY:
            death_date = death.get_date_object()
            if death_date.copy_offset_ymd(year=limit).match(current_date, "<<"):
                return False

    # Look for Cause Of Death, Burial or Cremation events.
    # These are fairly good indications that someone's not alive.
    for ev_ref in person.get_primary_event_ref_list():
        ev = db.get_event_from_handle(ev_ref.ref)
        if ev and ev.type in [gen.lib.EventType.CAUSE_DEATH, 
                              gen.lib.EventType.BURIAL, 
                              gen.lib.EventType.CREMATION]:
            if not death_date:
                death_date = ev.get_date_object()
            if ev.get_date_object().get_start_date() != gen.lib.Date.EMPTY:
                if ev.get_date_object().copy_offset_ymd(year=limit).match(current_date,"<<"):
                    return False
        # For any other event of this person, check whether it happened
        # too long ago. If so then the person is likely dead now.
        elif ev and too_old(ev.get_date_object(), current_date.get_year()):
            return False

    birth_date = None
    # If they were born within 100 years before current year then
    # assume they are alive (we already know they are not dead).
    birth_ref = person.get_birth_ref()
    if birth_ref and birth_ref.get_role() == gen.lib.EventRoleType.PRIMARY:
        birth = db.get_event_from_handle(birth_ref.ref)
        if (birth.get_date_object().get_start_date() != gen.lib.Date.EMPTY):
            if not birth_date:
                birth_date = birth.get_date_object()
            # Check whether the birth event is too old because the
            # code above did not look at birth, only at other events
            birth_obj = birth.get_date_object()
            if birth_obj.get_valid():
                # only if this is a valid birth date:
                if birth_obj.match(current_date,">>"):
                    return False
                if too_old(birth_obj, current_date.get_year()):
                    return False
                if not_too_old(birth_obj, current_date.get_year()):
                    return True
    
    if not birth_date and death_date:
        if death_date.match(current_date.copy_offset_ymd(year=_MAX_AGE_PROB_ALIVE), ">>"):
            # person died more than MAX after current year
            return False

    # Neither birth nor death events are available. Try looking
    # at siblings. If a sibling was born more than 120 years past, 
    # or more than 20 future, then probably this person is
    # not alive. If the sibling died more than 120 years
    # past, or more than 120 years future, then probably not alive.

    family_list = person.get_parent_family_handle_list()
    for family_handle in family_list:
        family = db.get_family_from_handle(family_handle)
        for child_ref in family.get_child_ref_list():
            child_handle = child_ref.ref
            child = db.get_person_from_handle(child_handle)
            child_birth_ref = child.get_birth_ref()
            if child_birth_ref:
                child_birth = db.get_event_from_handle(child_birth_ref.ref)
                dobj = child_birth.get_date_object()
                if dobj.get_start_date() != gen.lib.Date.EMPTY:
                    # if sibling birth date too far away, then not alive:
                    year = dobj.get_year()
                    if year != 0:
                        if not (current_date.copy_offset_ymd(-(_MAX_AGE_PROB_ALIVE + _MAX_SIB_AGE_DIFF)).match(dobj,"<<") and
                                dobj.match(current_date.copy_offset_ymd(_MAX_SIB_AGE_DIFF),"<<")):
                            return False
            child_death_ref = child.get_death_ref()
            if child_death_ref:
                child_death = db.get_event_from_handle(child_death_ref.ref)
                dobj = child_death.get_date_object()
                if dobj.get_start_date() != gen.lib.Date.EMPTY:
                    # if sibling death date too far away, then not alive:
                    year = dobj.get_year()
                    if year != 0:
                        if not (current_date.copy_offset_ymd(-(_MAX_AGE_PROB_ALIVE + _MAX_SIB_AGE_DIFF)).match(dobj,"<<") and
                                dobj.match(current_date.copy_offset_ymd(_MAX_AGE_PROB_ALIVE),"<<")):
                            return False

    # Try looking for descendants that were born more than a lifespan
    # ago.

    def descendants_too_old (person, years):
        for family_handle in person.get_family_handle_list():
            family = db.get_family_from_handle(family_handle)
            
            for child_ref in family.get_child_ref_list():
                child_handle = child_ref.ref
                child = db.get_person_from_handle(child_handle)
                child_birth_ref = child.get_birth_ref()
                if child_birth_ref:
                    child_birth = db.get_event_from_handle(child_birth_ref.ref)
                    dobj = child_birth.get_date_object()
                    if dobj.get_start_date() != gen.lib.Date.EMPTY:
                        d = gen.lib.Date(dobj)
                        val = d.get_start_date()
                        val = d.get_year() - years
                        d.set_year(val)
                        if not not_too_old (d, current_date.get_year()):
                            return True

                child_death_ref = child.get_death_ref()
                if child_death_ref:
                    child_death = db.get_event_from_handle(child_death_ref.ref)
                    dobj = child_death.get_date_object()
                    if dobj.get_start_date() != gen.lib.Date.EMPTY:
                        if not not_too_old (dobj, current_date.get_year()):
                            return True

                if descendants_too_old (child, years + _MIN_GENERATION_YEARS):
                    return True
                
        return False

    # If there are descendants that are too old for the person to have
    # been alive in the current year then they must be dead.

    try:
        if descendants_too_old(person, _MIN_GENERATION_YEARS):
            return False
    except RuntimeError:
        raise Errors.DatabaseError(
            _("Database error: %s is defined as his or her own ancestor") %
            name_displayer.display(person))

    def ancestors_too_old(person, year):
        family_handle = person.get_main_parents_family_handle()
        
        if family_handle:                
            family = db.get_family_from_handle(family_handle)
            father_handle = family.get_father_handle()
            if father_handle:
                father = db.get_person_from_handle(father_handle)
                father_birth_ref = father.get_birth_ref()
                if father_birth_ref and father_birth_ref.get_role() == gen.lib.EventRoleType.PRIMARY:
                    father_birth = db.get_event_from_handle(
                        father_birth_ref.ref)
                    dobj = father_birth.get_date_object()
                    if dobj.get_start_date() != gen.lib.Date.EMPTY:
                        if not not_too_old (dobj, year - _AVG_GENERATION_GAP):
                            return True

                father_death_ref = father.get_death_ref()
                if father_death_ref and father_death_ref.get_role() == gen.lib.EventRoleType.PRIMARY:
                    father_death = db.get_event_from_handle(
                        father_death_ref.ref)
                    dobj = father_death.get_date_object()
                    if dobj.get_start_date() != gen.lib.Date.EMPTY:
                        if dobj.get_year() < year - _AVG_GENERATION_GAP:
                            return True

                if ancestors_too_old (father, year - _AVG_GENERATION_GAP):
                    return True

            mother_handle = family.get_mother_handle()
            if mother_handle:
                mother = db.get_person_from_handle(mother_handle)
                mother_birth_ref = mother.get_birth_ref()
                if mother_birth_ref and mother_birth_ref.get_role() == gen.lib.EventRoleType.PRIMARY:
                    mother_birth = db.get_event_from_handle(mother_birth_ref.ref)
                    dobj = mother_birth.get_date_object()
                    if dobj.get_start_date() != gen.lib.Date.EMPTY:
                        if not not_too_old (dobj, year - _AVG_GENERATION_GAP):
                            return True

                mother_death_ref = mother.get_death_ref()
                if mother_death_ref and mother_death_ref.get_role() == gen.lib.EventRoleType.PRIMARY:
                    mother_death = db.get_event_from_handle(
                        mother_death_ref.ref)
                    dobj = mother_death.get_date_object()
                    if dobj.get_start_date() != gen.lib.Date.EMPTY:
                        if dobj.get_year() < year - _AVG_GENERATION_GAP:
                            return True

                if ancestors_too_old (mother, year - _AVG_GENERATION_GAP):
                    return True

        return False

    # If there are ancestors that would be too old in the current year
    # then assume our person must be dead too.
    if ancestors_too_old (person, current_date.get_year()):
        return False

    # If we can't find any reason to believe that they are dead we
    # must assume they are alive.
    return True

def not_too_old(date, current_year=None):
    if not current_year:
        time_struct = time.localtime(time.time())
        current_year = time_struct[0]
    year = date.get_year()
    return (year != 0 and abs(current_year - year) < _MAX_AGE_PROB_ALIVE)

def too_old(date, current_year=None):
    if current_year:
        the_current_year = current_year
    else:
        time_struct = time.localtime(time.time())
        the_current_year = time_struct[0]
    year = date.get_year()
    return (year != 0 and abs(the_current_year - year) > _MAX_AGE_PROB_ALIVE)

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def get_referents(handle, db, primary_objects):
    """ Find objects that refer to an object.
    
    This function is the base for other get_<object>_referents finctions.
    
    """
    # Use one pass through the reference map to grab all the references
    object_list = [item for item in db.find_backlink_handles(handle)]
    
    # Then form the object-specific lists
    the_lists = ()

    for primary in primary_objects:
        primary_list = [item[1] for item in object_list if item[0] == primary]
        the_lists = the_lists + (primary_list, )

    return the_lists

def get_source_referents(source_handle, db):
    """ Find objects that refer the source.

    This function finds all primary objects that refer (directly or through
    secondary child-objects) to a given source handle in a given database.
    
    """
    _primaries = ('Person', 'Family', 'Event', 'Place', 
                  'Source', 'MediaObject', 'Repository')
    
    return (get_referents(source_handle, db, _primaries))

def get_media_referents(media_handle, db):
    """ Find objects that refer the media object.

    This function finds all primary objects that refer
    to a given media handle in a given database.
    
    """
    _primaries = ('Person', 'Family', 'Event', 'Place', 'Source')
    
    return (get_referents(media_handle, db, _primaries))

def get_note_referents(note_handle, db):
    """ Find objects that refer a note object.
    
    This function finds all primary objects that refer
    to a given note handle in a given database.
    
    """
    _primaries = ('Person', 'Family', 'Event', 'Place', 
                  'Source', 'MediaObject', 'Repository')
    
    return (get_referents(note_handle, db, _primaries))

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
_NEW_NAME_PATTERN = '%s%sUntitled_%d.%s'

def get_new_filename(ext, folder='~/'):
    ix = 1
    while os.path.isfile(os.path.expanduser(_NEW_NAME_PATTERN %
                                            (folder, os.path.sep, ix, ext))):
        ix = ix + 1
    return os.path.expanduser(_NEW_NAME_PATTERN % (folder, os.path.sep, ix, ext))

def get_empty_tempdir(dirname):
    """ Return path to TEMP_DIR/dirname, a guaranteed empty directory

    makes intervening directories if required
    fails if _file_ by that name already exists, 
    or for inadequate permissions to delete dir/files or create dir(s)

    """
    dirpath = os.path.join(TEMP_DIR,dirname)
    if os.path.isdir(dirpath):
        shutil.rmtree(dirpath)
    os.makedirs(dirpath)
    return dirpath

def rm_tempdir(path):
    """Remove a tempdir created with get_empty_tempdir"""
    if path.startswith(TEMP_DIR) and os.path.isdir(path):
        shutil.rmtree(path)

def cast_to_bool(val):
    if val == str(True):
        return True
    return False

def get_type_converter(val):
    """
    Return function that converts strings into the type of val.
    """
    val_type = type(val)
    if val_type in (str, unicode):
        return unicode
    elif val_type == int:
        return int
    elif val_type == float:
        return float
    elif val_type == bool:
        return cast_to_bool
    elif val_type in (list, tuple):
        return list

def type_name(val):
    """
    Return the name the type of val.
    
    Only numbers and strings are supported.
    The rest becomes strings (unicode).
    """
    val_type = type(val)
    if val_type == int:
        return 'int'
    elif val_type == float:
        return 'float'
    elif val_type == bool:
        return 'bool'
    elif val_type in (str, unicode):
        return 'unicode'
    return 'unicode'

def get_type_converter_by_name(val_str):
    """
    Return function that converts strings into the type given by val_str.
    
    Only numbers and strings are supported.
    The rest becomes strings (unicode).
    """
    if val_str == 'int':
        return int
    elif val_str == 'float':
        return float
    elif val_str == 'bool':
        return cast_to_bool
    elif val_str in ('str', 'unicode'):
        return unicode
    return unicode

def relative_path(original, base):
    """
    Calculate the relative path from base to original, with base a directory,
    and original an absolute path
    On problems, original is returned unchanged
    """
    if not os.path.isdir(base):
        return original
    #original and base must be absolute paths
    if not os.path.isabs(base):
        return original
    if not os.path.isabs(original):
        return original
    original = os.path.normpath(original)
    base = os.path.normpath(base)
    
    # If the db_dir and obj_dir are on different drives (win only)
    # then there cannot be a relative path. Return original obj_path
    (base_drive, base) = os.path.splitdrive(base) 
    (orig_drive, orig_name) = os.path.splitdrive(original)
    if base_drive.upper() != orig_drive.upper():
        return original

    # Starting from the filepath root, work out how much of the filepath is
    # shared by base and target.
    base_list = (base).split(os.sep)
    target_list = (orig_name).split(os.sep)
    # make sure '/home/person' and 'c:/home/person' both give 
    #   list ['home', 'person']
    base_list = [word for word in base_list if word]
    target_list = [word for word in target_list if word]
    i = -1
    for i in range(min(len(base_list), len(target_list))):
        if base_list[i] <> target_list[i]: break
    else:
        #if break did not happen we are here at end, and add 1.
        i += 1
    rel_list = [os.pardir] * (len(base_list)-i) + target_list[i:]
    return os.path.join(*rel_list)

def media_path(db):
    """
    Given a database, return the mediapath to use as basedir for media
    """
    mpath = db.get_mediapath()
    if mpath is None:
        #use home dir
        mpath = USER_HOME
    return mpath

def media_path_full(db, filename):
    """
    Given a database and a filename of a media, return the media filename
    is full form, eg 'graves/tomb.png' becomes '/home/me/genea/graves/tomb.png
    """
    if os.path.isabs(filename):
        return filename
    mpath = media_path(db)
    return os.path.join(mpath, filename)
    

class ProgressMeter(object):
    """
    Progress meter class for GRAMPS.
    
    The progress meter has two modes:
    
    MODE_FRACTION is used when you know the number of steps that will be taken.
    Set the total number of steps, and then call step() that many times. 
    The progress bar will progress from left to right.
    
    MODE_ACTIVITY is used when you don't know the number of steps that will be
    taken. Set up the total number of steps for the bar to get from one end of
    the bar to the other. Then, call step() as many times as you want. The bar
    will move from left to right until you stop calling step. 
    """
    
    MODE_FRACTION = 0
    MODE_ACTIVITY = 1
    
    def __init__(self, title, header=''):
        """
        Specify the title and the current pass header.
        """
        self.__mode = ProgressMeter.MODE_FRACTION
        self.__pbar_max = 100.0
        self.__pbar_index = 0.0
        self.__old_val = -1
        
        self.__dialog = gtk.Dialog()
        self.__dialog.connect('delete_event', self.__warn)
        self.__dialog.set_has_separator(False)
        self.__dialog.set_title(title)
        self.__dialog.set_border_width(12)
        self.__dialog.vbox.set_spacing(10)
        self.__dialog.vbox.set_border_width(24)
        self.__dialog.set_size_request(350, 125)
        
        tlbl = gtk.Label('<span size="larger" weight="bold">%s</span>' % title)
        tlbl.set_use_markup(True)
        self.__dialog.vbox.add(tlbl)
        
        self.__lbl = gtk.Label(header)
        self.__lbl.set_use_markup(True)
        self.__dialog.vbox.add(self.__lbl)
 
        self.__pbar = gtk.ProgressBar()
        self.__dialog.vbox.add(self.__pbar)
        
        self.__dialog.show_all()
        if header == '':
            self.__lbl.hide()

    def set_pass(self, header="", total=100, mode=MODE_FRACTION):
        """
        Reset for another pass. Provide a new header and define number
        of steps to be used.
        """
        self.__mode = mode
        self.__pbar_max = total
        self.__pbar_index = 0.0
        
        self.__lbl.set_text(header)
        if header == '':
            self.__lbl.hide()
        else:
            self.__lbl.show()

        if self.__mode is ProgressMeter.MODE_FRACTION:
            self.__pbar.set_fraction(0.0)
        else: # ProgressMeter.MODE_ACTIVITY
            self.__pbar.set_pulse_step(1.0/self.__pbar_max)
        
        while gtk.events_pending():
            gtk.main_iteration()

    def step(self):
        """Click the progress bar over to the next value.  Be paranoid
        and insure that it doesn't go over 100%."""
        
        if self.__mode is ProgressMeter.MODE_FRACTION:
            self.__pbar_index = self.__pbar_index + 1.0
            
            if self.__pbar_index > self.__pbar_max:
                self.__pbar_index = self.__pbar_max
    
            try:
                val = int(100*self.__pbar_index/self.__pbar_max)
            except ZeroDivisionError:
                val = 0
    
            if val != self.__old_val:
                self.__pbar.set_text("%d%%" % val)
                self.__pbar.set_fraction(val/100.0)
                self.__old_val = val
        else: # ProgressMeter.MODE_ACTIVITY
            self.__pbar.pulse()
            
        while gtk.events_pending():
            gtk.main_iteration()

    def __warn(self, *obj):
        """
        Don't let the user close the progress dialog.
        """
        WarningDialog(
            _("Attempt to force closing the dialog"), 
            _("Please do not force closing this important dialog."), 
            self.__dialog)
        return True

    def close(self):
        """
        Close the progress meter
        """
        self.__dialog.destroy()
        
def open_file_with_default_application( file_path ):
    """
    Launch a program to open an arbitrary file. The file will be opened using 
    whatever program is configured on the host as the default program for that 
    type of file.
    
    @param file_path: The path to the file to be opened.
        Example: "c:\foo.txt"
    @type file_path: string
    @return: nothing
    """
    norm_path = os.path.normpath( file_path )
    
    if not os.path.exists(norm_path):
        ErrorDialog(_("Error Opening File"), _("File does not exist"))
        return
        
    if os.sys.platform == 'win32':
        try:
            os.startfile(norm_path)
        except WindowsError, msg:
            ErrorDialog(_("Error Opening File"), str(msg))
    else:
        search = os.environ['PATH'].split(':')
        if os.sys.platform == 'darwin':
            utility = 'open'
        else:
            utility = 'xdg-open'
        for lpath in search:
            prog = os.path.join(lpath, utility)
            if os.path.isfile(prog):
                os.spawnvpe(os.P_NOWAIT, prog, [prog, norm_path], os.environ)
                return

def profile(func, *args):
    import hotshot.stats

    prf = hotshot.Profile('mystats.profile')
    print "Start"
    prf.runcall(func, *args)
    print "Finished"
    prf.close()
    print "Loading profile"
    stats = hotshot.stats.load('mystats.profile')
    print "done"
    stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(100)
    stats.print_callers(100)
    
#-------------------------------------------------------------------------
#
# Keyword translation interface 
#
#-------------------------------------------------------------------------

# keyword, code, translated standard, translated upper
KEYWORDS = [("title",     "t", _("Person|Title"),     _("Person|TITLE")),
            ("given",     "f", _("Given"),     _("GIVEN")),
            ("prefix",    "p", _("Prefix"),    _("PREFIX")),
            ("surname",   "l", _("Surname"),   _("SURNAME")),
            ("suffix",    "s", _("Suffix"),    _("SUFFIX")),
            ("patronymic","y", _("Patronymic"),_("PATRONYMIC")),
            ("call",      "c", _("Call"),      _("CALL")),
            ("common",    "x", _("Common"),    _("COMMON")),
            ("initials",  "i", _("Initials"),  _("INITIALS"))
            ]
KEY_TO_TRANS = {}
TRANS_TO_KEY = {}
for (key, code, standard, upper) in KEYWORDS:
    KEY_TO_TRANS[key] = standard
    KEY_TO_TRANS[key.upper()] = upper
    KEY_TO_TRANS["%" + ("%s" % code)] = standard
    KEY_TO_TRANS["%" + ("%s" % code.upper())] = upper
    TRANS_TO_KEY[standard.lower()] = key
    TRANS_TO_KEY[standard] = key
    TRANS_TO_KEY[upper] = key.upper()

def get_translation_from_keyword(keyword):
    """ Return the translation of keyword """
    return KEY_TO_TRANS.get(keyword, keyword)

def get_keyword_from_translation(word):
    """ Return the keyword of translation """
    return TRANS_TO_KEY.get(word, word)

def get_keywords():
    """ Get all keywords, longest to shortest """
    keys = KEY_TO_TRANS.keys()
    keys.sort(lambda a,b: -cmp(len(a), len(b)))
    return keys

def get_translations():
    """ Get all translations, longest to shortest """
    trans = TRANS_TO_KEY.keys()
    trans.sort(lambda a,b: -cmp(len(a), len(b)))
    return trans
    