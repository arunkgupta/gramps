#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
#               2009       Gary Burton
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
import gtk

# $Id$ 

"""
The EditLdsOrd module provides the EditLdsOrd class. This provides a
mechanism for the user to edit personal LDS information.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from gtk import glade

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import Config
import gen.lib
from BasicUtils import name_displayer
import LdsUtils

from _EditSecondary import EditSecondary
from ObjectEntries import PlaceEntry

from DisplayTabs import SourceEmbedList,NoteTab
from widgets import (PrivacyButton, MonitoredDate, 
                     MonitoredMenu, MonitoredStrMenu)

_DATA_MAP = {
    gen.lib.LdsOrd.BAPTISM : [
        gen.lib.LdsOrd.STATUS_NONE,
        gen.lib.LdsOrd.STATUS_CHILD,
        gen.lib.LdsOrd.STATUS_CLEARED,
        gen.lib.LdsOrd.STATUS_COMPLETED,
        gen.lib.LdsOrd.STATUS_INFANT,
        gen.lib.LdsOrd.STATUS_PRE_1970,
        gen.lib.LdsOrd.STATUS_QUALIFIED,
        gen.lib.LdsOrd.STATUS_STILLBORN,
        gen.lib.LdsOrd.STATUS_SUBMITTED,
        gen.lib.LdsOrd.STATUS_UNCLEARED,
        ],
    gen.lib.LdsOrd.CONFIRMATION : [
        gen.lib.LdsOrd.STATUS_NONE,
        gen.lib.LdsOrd.STATUS_CHILD,
        gen.lib.LdsOrd.STATUS_CLEARED,
        gen.lib.LdsOrd.STATUS_COMPLETED,
        gen.lib.LdsOrd.STATUS_INFANT,
        gen.lib.LdsOrd.STATUS_PRE_1970,
        gen.lib.LdsOrd.STATUS_QUALIFIED,
        gen.lib.LdsOrd.STATUS_STILLBORN,
        gen.lib.LdsOrd.STATUS_SUBMITTED,
        gen.lib.LdsOrd.STATUS_UNCLEARED,
        ],
    gen.lib.LdsOrd.ENDOWMENT: [
        gen.lib.LdsOrd.STATUS_NONE,
        gen.lib.LdsOrd.STATUS_CHILD,
        gen.lib.LdsOrd.STATUS_CLEARED,
        gen.lib.LdsOrd.STATUS_COMPLETED,
        gen.lib.LdsOrd.STATUS_INFANT,
        gen.lib.LdsOrd.STATUS_PRE_1970,
        gen.lib.LdsOrd.STATUS_QUALIFIED,
        gen.lib.LdsOrd.STATUS_STILLBORN,
        gen.lib.LdsOrd.STATUS_SUBMITTED,
        gen.lib.LdsOrd.STATUS_UNCLEARED,
        ],
    gen.lib.LdsOrd.SEAL_TO_PARENTS:[
        gen.lib.LdsOrd.STATUS_NONE,
        gen.lib.LdsOrd.STATUS_BIC,
        gen.lib.LdsOrd.STATUS_CLEARED,
        gen.lib.LdsOrd.STATUS_COMPLETED,
        gen.lib.LdsOrd.STATUS_DNS,
        gen.lib.LdsOrd.STATUS_PRE_1970,
        gen.lib.LdsOrd.STATUS_QUALIFIED,
        gen.lib.LdsOrd.STATUS_STILLBORN,
        gen.lib.LdsOrd.STATUS_SUBMITTED,
        gen.lib.LdsOrd.STATUS_UNCLEARED,
        ],
    gen.lib.LdsOrd.SEAL_TO_SPOUSE :[
        gen.lib.LdsOrd.STATUS_NONE,
        gen.lib.LdsOrd.STATUS_CANCELED,
        gen.lib.LdsOrd.STATUS_CLEARED,
        gen.lib.LdsOrd.STATUS_COMPLETED,
        gen.lib.LdsOrd.STATUS_DNS,
        gen.lib.LdsOrd.STATUS_PRE_1970,
        gen.lib.LdsOrd.STATUS_QUALIFIED,
        gen.lib.LdsOrd.STATUS_DNS_CAN,
        gen.lib.LdsOrd.STATUS_SUBMITTED,
        gen.lib.LdsOrd.STATUS_UNCLEARED,
        ],
    }

#-------------------------------------------------------------------------
#
# EditLdsOrd class
#
#-------------------------------------------------------------------------
class EditLdsOrd(EditSecondary):
    """
    Displays a dialog that allows the user to edit an attribute.
    """

    def __init__(self, state, uistate, track, attrib, callback):
        """
        Displays the dialog box.

        parent - The class that called the Address editor.
        attrib - The attribute that is to be edited
        title - The title of the dialog box
        list - list of options for the pop down menu
        """
        EditSecondary.__init__(self, state, uistate, track, attrib, callback)

    def _local_init(self):
        self.width_key = Config.LDS_WIDTH
        self.height_key = Config.LDS_HEIGHT
        self.top = glade.XML(const.GLADE_FILE, "lds_person_edit","gramps")
        self.set_window(self.top.get_widget("lds_person_edit"),
                        self.top.get_widget('title'),
                        _('LDS Ordinance Editor'))
        self.share_btn = self.top.get_widget('share_place')
        self.add_del_btn = self.top.get_widget('add_del_place')

    def _connect_signals(self):
        self.parents_select.connect('clicked',self.select_parents_clicked)
        self.define_cancel_button(self.top.get_widget('cancel'))
        self.define_help_button(self.top.get_widget('help'))
        self.define_ok_button(self.top.get_widget('ok'),self.save)

    def _get_types(self):
        return (gen.lib.LdsOrd.BAPTISM,
                gen.lib.LdsOrd.ENDOWMENT,
                gen.lib.LdsOrd.CONFIRMATION,
                gen.lib.LdsOrd.SEAL_TO_PARENTS)

    def _setup_fields(self):

        self.parents_label = self.top.get_widget('parents_label')
        self.parents = self.top.get_widget('parents')
        self.parents_select = self.top.get_widget('parents_select')

        self.priv = PrivacyButton(
            self.top.get_widget("private"),
            self.obj, self.db.readonly)

        self.date_field = MonitoredDate(
            self.top.get_widget("date_entry"),
            self.top.get_widget("date_stat"),
            self.obj.get_date_object(),
            self.uistate,
            self.track,
            self.db.readonly)

        self.place_field = PlaceEntry(
            self.dbstate,
            self.uistate,
            self.track,
            self.top.get_widget("place"),
            self.obj.set_place_handle,
            self.obj.get_place_handle,
            self.add_del_btn,
            self.share_btn)

        self.type_menu = MonitoredMenu(
            self.top.get_widget('type'),
            self.obj.set_type,
            self.obj.get_type,
            [(item[1],item[0]) for item in gen.lib.LdsOrd._TYPE_MAP
             if item[0] in self._get_types()],
            self.db.readonly,
            changed=self.ord_type_changed)

        self.temple_menu = MonitoredStrMenu(
            self.top.get_widget('temple'),
            self.obj.set_temple,
            self.obj.get_temple,
            LdsUtils.TEMPLES.name_code_data(),
            self.db.readonly)

        self.status_menu = MonitoredMenu(
            self.top.get_widget('status'),
            self.obj.set_status,
            self.obj.get_status,
            [(item[1],item[0]) for item in gen.lib.LdsOrd._STATUS_MAP
             if item[0] in _DATA_MAP[self.obj.get_type()] ],
            self.db.readonly)

        self.ord_type_changed()
        self.update_parent_label()

    def ord_type_changed(self):
        if self.obj.get_type() == gen.lib.LdsOrd.BAPTISM:
            self.parents.hide()
            self.parents_label.hide()
            self.parents_select.hide()
        elif self.obj.get_type() == gen.lib.LdsOrd.ENDOWMENT:
            self.parents.hide()
            self.parents_label.hide()
            self.parents_select.hide()
        elif self.obj.get_type() == gen.lib.LdsOrd.SEAL_TO_PARENTS:
            self.parents.show()
            self.parents_label.show()
            self.parents_select.show()
        new_data = [(item[1],item[0]) for item in gen.lib.LdsOrd._STATUS_MAP
                    if item[0] in _DATA_MAP[self.obj.get_type()] ]
        self.status_menu.change_menu(new_data)

    def _create_tabbed_pages(self):
        notebook = gtk.Notebook()
        self.srcref_list = self._add_tab(
            notebook,
            SourceEmbedList(self.dbstate,self.uistate, self.track,self.obj))
        
        self.note_tab = self._add_tab(
            notebook,
            NoteTab(self.dbstate, self.uistate, self.track,
                    self.obj.get_note_list(),
                    notetype=gen.lib.NoteType.LDS))
        
        self._setup_notebook_tabs( notebook)
        notebook.show_all()
        self.top.get_widget('vbox').pack_start(notebook,True)

    def select_parents_clicked(self, obj):
        from Selectors import selector_factory
        SelectFamily = selector_factory('Family')

        dialog = SelectFamily(self.dbstate,self.uistate,self.track)
        family = dialog.run()
        if family:
            self.obj.set_family_handle(family.handle)
        self.update_parent_label()

    def update_parent_label(self):
        handle = self.obj.get_family_handle()
        if handle:
            family = self.dbstate.db.get_family_from_handle(handle)
            f = self.dbstate.db.get_person_from_handle(
                family.get_father_handle())
            m = self.dbstate.db.get_person_from_handle(
                family.get_mother_handle())
            if f and m:
                label = _("%(father)s and %(mother)s [%(gramps_id)s]") % {
                    'father' : name_displayer.display(f),
                    'mother' : name_displayer.display(m),
                    'gramps_id' : family.gramps_id,
                    }
            elif f:
                label = _("%(father)s [%(gramps_id)s]") % {
                    'father' : name_displayer.display(f),
                    'gramps_id' : family.gramps_id,
                    }
            elif m:
                label = _("%(mother)s [%(gramps_id)s]") % {
                    'mother' : name_displayer.display(m),
                    'gramps_id' : family.gramps_id,
                    }
            else:
                # No translation for bare gramps_id
                label = "[%(gramps_id)s]" % {
                    'gramps_id' : family.gramps_id,
                    }
        else:
            label = ""

        self.parents.set_text(label)

    def build_menu_names(self, attrib):
        label = _("LDS Ordinance")
        return (label, _('LDS Ordinance Editor'))

    def save(self,*obj):
        """
        Called when the OK button is pressed. Gets data from the
        form and updates the LdsOrd data structure.
        """
        if self.callback:
            self.callback(self.obj)
        self.close()

#-------------------------------------------------------------------------
#
# EditFamilyLdsOrd
#
#-------------------------------------------------------------------------
class EditFamilyLdsOrd(EditSecondary):
    """
    Displays a dialog that allows the user to edit an attribute.
    """

    def __init__(self, state, uistate, track, attrib, callback):
        """
        Displays the dialog box.

        parent - The class that called the Address editor.
        attrib - The attribute that is to be edited
        title - The title of the dialog box
        list - list of options for the pop down menu
        """
        EditSecondary.__init__(self, state, uistate, track, attrib, callback)

    def _local_init(self):
        self.top = glade.XML(const.GLADE_FILE, "lds_person_edit","gramps")
        self.set_window(self.top.get_widget("lds_person_edit"),
                        self.top.get_widget('title'),
                        _('LDS Ordinance Editor'))
        self.share_btn = self.top.get_widget('share_place')
        self.add_del_btn = self.top.get_widget('add_del_place')

    def _connect_signals(self):
        self.define_cancel_button(self.top.get_widget('cancel'))
        self.define_help_button(self.top.get_widget('help'))
        self.define_ok_button(self.top.get_widget('ok'),self.save)

    def _get_types(self):
        return (gen.lib.LdsOrd.SEAL_TO_SPOUSE,)

    def _setup_fields(self):

        self.parents_label = self.top.get_widget('parents_label')
        self.parents = self.top.get_widget('parents')
        self.parents_select = self.top.get_widget('parents_select')

        self.priv = PrivacyButton(
            self.top.get_widget("private"),
            self.obj, self.db.readonly)

        self.date_field = MonitoredDate(
            self.top.get_widget("date_entry"),
            self.top.get_widget("date_stat"),
            self.obj.get_date_object(),
            self.uistate,
            self.track,
            self.db.readonly)

        self.place_field = PlaceEntry(
            self.dbstate,
            self.uistate,
            self.track,
            self.top.get_widget("place"),
            self.obj.set_place_handle,
            self.obj.get_place_handle,
            self.add_del_btn,
            self.share_btn)

        self.type_menu = MonitoredMenu(
            self.top.get_widget('type'),
            self.obj.set_type,
            self.obj.get_type,
            [(item[1],item[0]) for item in gen.lib.LdsOrd._TYPE_MAP
             if item[0] in self._get_types()],
            self.db.readonly)

        self.temple_menu = MonitoredStrMenu(
            self.top.get_widget('temple'),
            self.obj.set_temple,
            self.obj.get_temple,
            LdsUtils.TEMPLES.name_code_data(),
            self.db.readonly)

        self.status_menu = MonitoredMenu(
            self.top.get_widget('status'),
            self.obj.set_status,
            self.obj.get_status,
            [(item[1],item[0]) for item in gen.lib.LdsOrd._STATUS_MAP
             if item[0] in _DATA_MAP[self.obj.get_type()]],
            self.db.readonly)

    def _create_tabbed_pages(self):
        notebook = gtk.Notebook()
        self.srcref_list = self._add_tab(
            notebook,
            SourceEmbedList(self.dbstate,self.uistate, self.track,self.obj))
        
        self.note_tab = self._add_tab(
            notebook,
            NoteTab(self.dbstate, self.uistate, self.track,
                    self.obj.get_note_list(),
                    notetype=gen.lib.NoteType.LDS))
        
        notebook.show_all()
        self.top.get_widget('vbox').pack_start(notebook,True)

    def build_menu_names(self, attrib):
        label = _("LDS Ordinance")
        return (label, _('LDS Ordinance Editor'))

    def save(self,*obj):
        """
        Called when the OK button is pressed. Gets data from the
        form and updates the LdsOrd data structure.
        """
        if self.callback:
            self.callback(self.obj)
        self.close()
