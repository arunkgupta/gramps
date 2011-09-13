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
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk
from gtk import glade

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import Config
import gen.lib

from widgets import MonitoredEntry, MonitoredDataType, PrivacyButton
from DisplayTabs import AddrEmbedList, WebEmbedList, NoteTab, SourceBackRefList
from Editors._EditPrimary import EditPrimary
from QuestionDialog import ErrorDialog

class EditRepository(EditPrimary):

    def __init__(self, dbstate, uistate, track, repository):

        EditPrimary.__init__(self, dbstate, uistate, track, repository, 
                             dbstate.db.get_repository_from_handle, 
                             dbstate.db.get_repository_from_gramps_id)

    def empty_object(self):
        return gen.lib.Repository()

    def get_menu_title(self):
        if self.obj.get_handle():
            title = self.obj.get_name()
            if title:
                title = _('Repository') + ": " + title
            else:
                title = _('Repository')
        else:
            title = _('New Repository')
        return title

    def _local_init(self):
        self.width_key = Config.REPO_WIDTH
        self.height_key = Config.REPO_HEIGHT
        self.glade = glade.XML(const.GLADE_FILE, "repository_editor","gramps")

        self.set_window(self.glade.get_widget("repository_editor"), None, 
                        self.get_menu_title())

    def build_menu_names(self, source):
        return (_('Edit Repository'), self.get_menu_title())        

    def _setup_fields(self):
        
        self.name = MonitoredEntry(self.glade.get_widget("repository_name"),
                                   self.obj.set_name, self.obj.get_name,
                                   self.db.readonly)

        self.type = MonitoredDataType(self.glade.get_widget("repository_type"),
                                      self.obj.set_type, self.obj.get_type,
                                      self.db.readonly,
                                      self.db.get_repository_types(),
            )

        self.call_number = MonitoredEntry(self.glade.get_widget('gid'),
                                          self.obj.set_gramps_id,
                                          self.obj.get_gramps_id, 
                                          self.db.readonly)

        self.privacy = PrivacyButton(self.glade.get_widget("private"), 
                                     self.obj, self.db.readonly)

    def _create_tabbed_pages(self):
        
        notebook = gtk.Notebook()

        self.addr_tab = self._add_tab(
                        notebook,
                        AddrEmbedList(self.dbstate, self.uistate, self.track,
                                      self.obj.get_address_list()))

        self.url_tab = self._add_tab(
                        notebook,
                        WebEmbedList(self.dbstate, self.uistate, self.track,
                                     self.obj.get_url_list()))
        
        self.note_tab = self._add_tab(
                        notebook,
                        NoteTab(self.dbstate, self.uistate, self.track,
                                self.obj.get_note_list(), self.get_menu_title(),
                                notetype=gen.lib.NoteType.REPO))

        self.backref_tab = self._add_tab(
                        notebook,
                        SourceBackRefList(self.dbstate, self.uistate, self.track,
                               self.db.find_backlink_handles(self.obj.handle)))

        self._setup_notebook_tabs( notebook)
        notebook.show_all()
        self.glade.get_widget("vbox").pack_start(notebook, True, True)

    def _connect_signals(self):
        self.define_help_button(self.glade.get_widget('help'))
        self.define_cancel_button(self.glade.get_widget('cancel'))
        self.define_ok_button(self.glade.get_widget('ok'), self.save)

    def save(self, *obj):
        self.ok_button.set_sensitive(False)
        if self.object_is_empty():
            ErrorDialog(_("Cannot save repository"),
                        _("No data exists for this repository. Please "
                          "enter data or cancel the edit."))
            self.ok_button.set_sensitive(True)
            return

        (uses_dupe_id, id) = self._uses_duplicate_id()
        if uses_dupe_id:
            prim_object = self.get_from_gramps_id(id)
            name = prim_object.get_name()
            msg1 = _("Cannot save repository. ID already exists.")
            msg2 = _("You have attempted to use the existing GRAMPS ID with "
                         "value %(id)s. This value is already used by '" 
                         "%(prim_object)s'. Please enter a different ID or leave "
                         "blank to get the next available ID value.") % {
                         'id' : id, 'prim_object' : name }
            ErrorDialog(msg1, msg2)
            self.ok_button.set_sensitive(True)
            return

        trans = self.db.transaction_begin()
        if not self.obj.get_handle():
            self.db.add_repository(self.obj, trans)
            msg = _("Add Repository (%s)") % self.obj.get_name()
        else:
            if not self.obj.get_gramps_id():
                self.obj.set_gramps_id(self.db.find_next_repository_gramps_id())
            self.db.commit_repository(self.obj, trans)
            msg = _("Edit Repository (%s)") % self.obj.get_name()
            
        self.db.transaction_commit(trans, msg)
        self.close()

    def _cleanup_on_exit(self):
        self.backref_tab.close()

class DelRepositoryQuery(object):
    def __init__(self, dbstate, uistate, repository, sources):
        self.obj = repository
        self.db = dbstate.db
        self.uistate = uistate
        self.sources = sources

    def query_response(self):
        trans = self.db.transaction_begin()
        
        repos_handle_list = [self.obj.get_handle()]

        for handle in self.sources:
            source = self.db.get_source_from_handle(handle)
            source.remove_repo_references(repos_handle_list)
            self.db.commit_source(source, trans)

        self.db.remove_repository(self.obj.get_handle(), trans)
        self.db.transaction_commit(
            trans, _("Delete Repository (%s)") % self.obj.get_name())