#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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

# $Id$

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import Config
import gen.lib
from glade import Glade
from DisplayTabs import (SourceEmbedList, NoteTab, GalleryTab, 
                         EventBackRefList, AttrEmbedList)
from widgets import (PrivacyButton, MonitoredEntry,
                     MonitoredDate, MonitoredDataType)
from _EditReference import RefTab, EditReference

from ObjectEntries import PlaceEntry

#-------------------------------------------------------------------------
#
# EditEventRef class
#
#-------------------------------------------------------------------------
class EditEventRef(EditReference):

    def __init__(self, state, uistate, track, event, event_ref, update):
        EditReference.__init__(self, state, uistate, track, event, event_ref,
                               update)
        self._init_event()

    def _local_init(self):
        self.width_key = Config.EVENT_REF_WIDTH
        self.height_key = Config.EVENT_REF_HEIGHT
        
        self.top = Glade()
        self.set_window(self.top.toplevel,
                        self.top.get_object('eer_title'),
                        _('Event Reference Editor'))
        self.define_warn_box(self.top.get_object("eer_warning"))
        self.define_expander(self.top.get_object("eer_expander"))
        self.share_btn = self.top.get_object('share_place')
        self.add_del_btn = self.top.get_object('add_del_place')

        tblref =  self.top.get_object('table64')
        notebook = self.top.get_object('notebook_ref')
        #recreate start page as GrampsTab
        notebook.remove_page(0)
        self.reftab = RefTab(self.dbstate, self.uistate, self.track, 
                              _('General'), tblref)
        tblref =  self.top.get_object('table62')
        notebook = self.top.get_object('notebook')
        #recreate start page as GrampsTab
        notebook.remove_page(0)
        self.primtab = RefTab(self.dbstate, self.uistate, self.track, 
                              _('_General'), tblref)

    def _init_event(self):
        self.commit_event = self.db.commit_personal_event
        self.add_event = self.db.add_person_event

    def get_custom_events(self):
        return self.db.get_person_event_types()

    def _connect_signals(self):
        self.define_ok_button(self.top.get_object('ok'),self.ok_clicked)
        self.define_cancel_button(self.top.get_object('cancel'))
        # FIXME: activate when help page is available
        #self.define_help_button(self.top.get_object('help'))

    def _setup_fields(self):
        
        self.ref_privacy = PrivacyButton(
            self.top.get_object('eer_ref_priv'),
            self.source_ref, self.db.readonly)

        self.descr_field = MonitoredEntry(
            self.top.get_object("eer_description"),
            self.source.set_description,
            self.source.get_description,
            self.db.readonly)

        self.gid = MonitoredEntry(
            self.top.get_object("gid"),
            self.source.set_gramps_id,
            self.source.get_gramps_id,
            self.db.readonly)

        self.place_field = PlaceEntry(
            self.dbstate,
            self.uistate,
            self.track,
            self.top.get_object("eer_place"),
            self.source.set_place_handle,
            self.source.get_place_handle,
            self.share_btn,
            self.add_del_btn)

        self.ev_privacy = PrivacyButton(
            self.top.get_object("eer_ev_priv"),
            self.source, self.db.readonly)
                
        self.role_selector = MonitoredDataType(
            self.top.get_object('eer_role_combo'),
            self.source_ref.set_role,
            self.source_ref.get_role,
            self.db.readonly,
            self.db.get_event_roles()
            )

        self.event_menu = MonitoredDataType(
            self.top.get_object("eer_type_combo"),
            self.source.set_type,
            self.source.get_type,
            self.db.readonly,
            custom_values=self.get_custom_events())

        self.date_check = MonitoredDate(
            self.top.get_object("eer_date_entry"),
            self.top.get_object("eer_date_stat"),
            self.source.get_date_object(),
            self.uistate,
            self.track,
            self.db.readonly)

    def _create_tabbed_pages(self):
        """
        Create the notebook tabs and inserts them into the main
        window.
        """

        notebook = self.top.get_object('notebook')
        notebook_ref = self.top.get_object('notebook_ref')

        self._add_tab(notebook, self.primtab)
        self._add_tab(notebook_ref, self.reftab)
        self.track_ref_for_deletion("primtab")
        self.track_ref_for_deletion("reftab")

        self.srcref_list = SourceEmbedList(self.dbstate,
                                           self.uistate,
                                           self.track,
                                           self.source)
        self._add_tab(notebook, self.srcref_list)
        self.track_ref_for_deletion("srcref_list")

        self.attr_list = AttrEmbedList(self.dbstate,
                                       self.uistate,
                                       self.track,
                                       self.source.get_attribute_list())
        self._add_tab(notebook, self.attr_list)
        self.track_ref_for_deletion("attr_list")

        self.note_tab = NoteTab(self.dbstate,
                                self.uistate,
                                self.track,
                                self.source.get_note_list(),
                                notetype=gen.lib.NoteType.EVENT)
        self._add_tab(notebook, self.note_tab)
        self.track_ref_for_deletion("note_tab")
        
        self.note_ref_tab = NoteTab(self.dbstate,
                                    self.uistate,
                                    self.track,
                                    self.source_ref.get_note_list(),
                                    notetype=gen.lib.NoteType.EVENTREF)
        self._add_tab(notebook_ref, self.note_ref_tab)
        self.track_ref_for_deletion("note_ref_tab")
        
        self.gallery_tab = GalleryTab(self.dbstate,
                                      self.uistate,
                                      self.track,
                                      self.source.get_media_list())
        self._add_tab(notebook, self.gallery_tab)
        self.track_ref_for_deletion("gallery_tab")

        self.backref_tab = EventBackRefList(self.dbstate,
                             self.uistate,
                             self.track,
                             self.db.find_backlink_handles(self.source.handle),
                             self.enable_warnbox)
        self._add_tab(notebook, self.backref_tab)
        self.track_ref_for_deletion("backref_tab")

        self.attr_ref_list = AttrEmbedList(self.dbstate,
                                           self.uistate,
                                           self.track,
                                           self.source_ref.get_attribute_list())
        self._add_tab(notebook_ref, self.attr_ref_list)
        self.track_ref_for_deletion("attr_ref_list")

        self._setup_notebook_tabs( notebook)
        self._setup_notebook_tabs( notebook_ref)

    def build_menu_names(self,eventref):
        if self.source:
            event_name = str(self.source.get_type())
            submenu_label = _('Event: %s')  % event_name
        else:
            submenu_label = _('New Event')
        return (_('Event Reference Editor'),submenu_label)
        
    def ok_clicked(self, obj):

        trans = self.db.transaction_begin()
        if self.source.handle:
            self.commit_event(self.source,trans)
            self.db.transaction_commit(trans,_("Modify Event"))
        else:
            self.add_event(self.source,trans)
            self.db.transaction_commit(trans,_("Add Event"))
            self.source_ref.ref = self.source.handle
        
        if self.update:
            self.update(self.source_ref,self.source)

        self.close()

class EditFamilyEventRef(EditEventRef):

    def __init__(self, state, uistate, track, event, event_ref, update):
        
        EditEventRef.__init__(self, state, uistate, track, event,
                              event_ref, update)
        
    def _init_event(self):
        self.commit_event = self.db.commit_family_event
        self.add_event = self.db.add_family_event

    def get_custom_events(self):
        return [ gen.lib.EventType((gen.lib.EventType.CUSTOM,val)) \
                 for val in self.dbstate.db.get_family_event_types()]