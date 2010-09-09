#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
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
from gen.ggettext import gettext as _
import locale

#-------------------------------------------------------------------------
#
# gtk
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gui import widgets
import gen.lib
import DateHandler

from Filters.SideBar import SidebarFilter
from Filters.Rules.Person import (RegExpName, SearchName, RegExpIdOf, 
                                  MatchIdOf, IsMale, IsFemale, HasUnknownGender,
                                  HasMarkerOf, HasEvent, HasTag,
                                  HasBirth, HasDeath, HasNoteRegexp, 
                                  HasNoteMatchingSubstringOf, MatchesFilter)
from Filters import GenericFilter, build_filter_model, Rules

def extract_text(entry_widget):
    """
    Extract the text from the entry widget, strips off any extra spaces, 
    and converts the string to unicode. 
    
    For some strange reason a gtk bug prevents the extracted string from being 
    of type unicode.
    
    """
    return unicode(entry_widget.get_text().strip())

#-------------------------------------------------------------------------
#
# PersonSidebarFilter class
#
#-------------------------------------------------------------------------
class PersonSidebarFilter(SidebarFilter):

    def __init__(self, dbstate, uistate, clicked):
        self.clicked_func = clicked
        self.filter_name = gtk.Entry()
        self.filter_id = gtk.Entry()
        self.filter_birth = gtk.Entry()
        self.filter_death = gtk.Entry()
        self.filter_event = gen.lib.Event()
        self.filter_event.set_type((gen.lib.EventType.CUSTOM, u''))
        self.etype = gtk.ComboBoxEntry()
        self.event_menu = widgets.MonitoredDataType(
            self.etype, 
            self.filter_event.set_type, 
            self.filter_event.get_type)

        self.filter_marker = gen.lib.Person()
        self.filter_marker.set_marker((gen.lib.MarkerType.CUSTOM, u''))
        self.mtype = gtk.ComboBoxEntry()
        self.marker_menu = widgets.MonitoredDataType(
            self.mtype, 
            self.filter_marker.set_marker, 
            self.filter_marker.get_marker)

        self.tag = gtk.ComboBox()

        self.filter_note = gtk.Entry()
        self.filter_gender = gtk.combo_box_new_text()
        map(self.filter_gender.append_text, 
            [ _('any'), _('male'), _('female'), _('unknown') ])
        self.filter_gender.set_active(0)
            
        self.filter_regex = gtk.CheckButton(_('Use regular expressions'))

        self.generic = gtk.ComboBox()

        SidebarFilter.__init__(self, dbstate, uistate, "Person")

        self.update_tag_list()

    def create_widget(self):
        cell = gtk.CellRendererText()
        cell.set_property('width', self._FILTER_WIDTH)
        cell.set_property('ellipsize', self._FILTER_ELLIPSIZE)
        self.generic.pack_start(cell, True)
        self.generic.add_attribute(cell, 'text', 0)
        self.on_filters_changed('Person')

        cell = gtk.CellRendererText()
        cell.set_property('width', self._FILTER_WIDTH)
        cell.set_property('ellipsize', self._FILTER_ELLIPSIZE)
        self.tag.pack_start(cell, True)
        self.tag.add_attribute(cell, 'text', 0)

        exdate1 = gen.lib.Date()
        exdate2 = gen.lib.Date()
        exdate1.set(gen.lib.Date.QUAL_NONE, gen.lib.Date.MOD_RANGE, 
                    gen.lib.Date.CAL_GREGORIAN, (0, 0, 1800, False, 
                                                0, 0, 1900, False))
        exdate2.set(gen.lib.Date.QUAL_NONE, gen.lib.Date.MOD_BEFORE, 
                    gen.lib.Date.CAL_GREGORIAN, (0, 0, 1850, False))

        msg1 = DateHandler.displayer.display(exdate1)
        msg2 = DateHandler.displayer.display(exdate2)

        self.add_text_entry(_('Name'), self.filter_name)
        self.add_text_entry(_('ID'), self.filter_id)
        self.add_entry(_('Gender'), self.filter_gender)
        self.add_text_entry(_('Birth date'), self.filter_birth, 
                            _('example: "%s" or "%s"') % (msg1, msg2))
        self.add_text_entry(_('Death date'), self.filter_death, 
                            _('example: "%s" or "%s"') % (msg1, msg2))
        self.add_entry(_('Event'), self.etype)
        self.add_entry(_('Marker'), self.mtype)
        self.add_entry(_('Tag'), self.tag)
        self.add_text_entry(_('Note'), self.filter_note)
        self.add_filter_entry(_('Custom filter'), self.generic)
        self.add_entry(None, self.filter_regex)

    def clear(self, obj):
        self.filter_name.set_text(u'')
        self.filter_id.set_text(u'')
        self.filter_birth.set_text(u'')
        self.filter_death.set_text(u'')
        self.filter_note.set_text(u'')
        self.filter_gender.set_active(0)
        self.etype.child.set_text(u'')
        self.mtype.child.set_text(u'')
        self.tag.set_active(0)
        self.generic.set_active(0)

    def get_filter(self):
        """
        Extracts the text strings from the sidebar, and uses them to build up
        a new filter.
        """

        # extract text values from the entry widgets
        name = extract_text(self.filter_name)
        gid = extract_text(self.filter_id)
        birth = extract_text(self.filter_birth)
        death = extract_text(self.filter_death)
        note = extract_text(self.filter_note)

        # extract remaining data from the menus
        etype = self.filter_event.get_type().xml_str()
        mtype = self.filter_marker.get_marker().xml_str()
        gender = self.filter_gender.get_active()
        regex = self.filter_regex.get_active()
        generic = self.generic.get_active() > 0
        tag = self.tag.get_active() > 0

        # check to see if the filter is empty. If it is empty, then
        # we don't build a filter

        empty = not (name or gid or birth or death or etype or mtype 
                     or note or gender or regex or generic or tag)
        if empty:
            generic_filter = None
        else:
            # build a GenericFilter
            generic_filter = GenericFilter()
            
            # if the name is not empty, choose either the regular expression
            # version or the normal text match
            if name:
                if regex:
                    rule = RegExpName([name])
                else:
                    rule = SearchName([name])
                generic_filter.add_rule(rule)

            # if the id is not empty, choose either the regular expression
            # version or the normal text match
            if gid:
                if regex:
                    rule = RegExpIdOf([gid])
                else:
                    rule = MatchIdOf([gid])
                generic_filter.add_rule(rule)

            # check the gender, and select the right rule based on gender
            if gender > 0:
                if gender == 1:
                    generic_filter.add_rule(IsMale([]))
                elif gender == 2:
                    generic_filter.add_rule(IsFemale([]))
                else:
                    generic_filter.add_rule(HasUnknownGender([]))

            # check the Marker type
            if mtype:
                rule = HasMarkerOf([mtype])
                generic_filter.add_rule(rule)
   
            # check the Tag
            if tag:
                model = self.tag.get_model()
                node = self.tag.get_active_iter()
                attr = model.get_value(node, 0)
                rule = HasTag([attr])
                generic_filter.add_rule(rule)
                
            # Build an event filter if needed
            if etype:
                rule = HasEvent([etype, u'', u'', u''])
                generic_filter.add_rule(rule)
                
            # Build birth event filter if needed
            # Arguments for the HasBirth filter are Date, Place, and Description
            # Since the value we extracted to the "birth" variable is the 
            # request date, we pass it as the first argument
            if birth:
                rule = HasBirth([birth, u'', u''])
                generic_filter.add_rule(rule)

            # Build death event filter if needed
            if death:
                rule = HasDeath([death, u'', u''])
                generic_filter.add_rule(rule)

            # Build note filter if needed
            if note:
                if regex:
                    rule = HasNoteRegexp([note])
                else:
                    rule = HasNoteMatchingSubstringOf([note])
                generic_filter.add_rule(rule)

        if self.generic.get_active() != 0:
            model = self.generic.get_model()
            node = self.generic.get_active_iter()
            obj = model.get_value(node, 0)
            rule = MatchesFilter([obj])
            generic_filter.add_rule(rule)

        return generic_filter

    def on_filters_changed(self, name_space):
        if name_space == 'Person':
            all_filter = GenericFilter()
            all_filter.set_name(_("None"))
            all_filter.add_rule(Rules.Person.Everyone([]))
            self.generic.set_model(build_filter_model('Person', [all_filter]))
            self.generic.set_active(0)

    def on_db_changed(self, db):
        """
        Called when the database is changed.
        """
        self.update_tag_list()

    def on_tags_changed(self):
        """
        Called when tags are changed.
        """
        self.update_tag_list()
        
    def update_tag_list(self):
        """
        Update the list of tags in the tag filter.
        """
        model = gtk.ListStore(str)
        model.append(('',))
        for tag in sorted(self.dbstate.db.get_all_tags(), key=locale.strxfrm):
            model.append((tag,))
        self.tag.set_model(model)
        self.tag.set_active(0)
