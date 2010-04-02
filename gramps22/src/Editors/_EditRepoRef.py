#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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

# $Id: _EditSourceRef.py 6155 2006-03-16 20:24:27Z rshura $

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

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import Config

from DisplayTabs import NoteTab,AddrEmbedList,WebEmbedList,SourceBackRefList
from GrampsWidgets import *
from _EditReference import EditReference

#-------------------------------------------------------------------------
#
# EditRepoRef class
#
#-------------------------------------------------------------------------
class EditRepoRef(EditReference):

    WIDTH_KEY = Config.REPO_REF_WIDTH
    HEIGHT_KEY = Config.REPO_REF_HEIGHT

    def __init__(self, state, uistate, track, source, source_ref, update):

        EditReference.__init__(self, state, uistate, track, source,
                               source_ref, update)

    def _local_init(self):
        
        self.top = gtk.glade.XML(const.gladeFile, "repository_ref_edit","gramps")
        
        self.set_window(self.top.get_widget('repository_ref_edit'),
                        self.top.get_widget('repo_title'),        
                        _('Repository Reference Editor'))

        self.define_warn_box(self.top.get_widget("warn_box"))
        self.define_expander(self.top.get_widget("src_expander"))

    def _connect_signals(self):
        self.define_ok_button(self.top.get_widget('ok'),self.ok_clicked)
        self.define_cancel_button(self.top.get_widget('cancel'))
        
    def _setup_fields(self):
        self.callno = MonitoredEntry(
            self.top.get_widget("call_number"),
            self.source_ref.set_call_number,
            self.source_ref.get_call_number,
            self.db.readonly)
        
        self.gid = MonitoredEntry(
            self.top.get_widget('gid'),
            self.source.set_gramps_id,
            self.source.get_gramps_id,
            self.db.readonly)

        self.privacy = PrivacyButton(
            self.top.get_widget("private"),
            self.source,
            self.db.readonly)

        self.title = MonitoredEntry(
            self.top.get_widget('repo_name'),
            self.source.set_name,
            self.source.get_name,
            self.db.readonly)
        
        self.type_selector = MonitoredDataType(
            self.top.get_widget("media_type"),
            self.source_ref.set_media_type,
            self.source_ref.get_media_type,
            self.db.readonly,
            self.db.get_source_media_types(),
            )

        self.media_type_selector = MonitoredDataType(
            self.top.get_widget("repo_type"),
            self.source.set_type,
            self.source.get_type,
            self.db.readonly,
            self.db.get_repository_types(),
            )

    def _create_tabbed_pages(self):
        """
        Creates the notebook tabs and inserts them into the main
        window.
        """

        notebook_src = self.top.get_widget('notebook_src')
        notebook_ref = self.top.get_widget('notebook_ref')

        self.note_tab = self._add_tab(
            notebook_src,
            NoteTab(self.dbstate, self.uistate, self.track,
                    self.source.get_note_object()))
        
        self.comment_tab = self._add_tab(
            notebook_ref,
            NoteTab(self.dbstate, self.uistate, self.track,
                    self.source_ref.get_note_object()))

        self.address_tab = self._add_tab(
            notebook_src,
            AddrEmbedList(self.dbstate,self.uistate,self.track,
                          self.source.get_address_list()))

        self.web_list = self._add_tab(
            notebook_src,
            WebEmbedList(self.dbstate,self.uistate,self.track,
                         self.source.get_url_list()))

        self.backref_tab = self._add_tab(
            notebook_src,
            SourceBackRefList(self.dbstate, self.uistate, self.track,
                              self.db.find_backlink_handles(self.source.handle),
                              self.enable_warnbox))

        self._setup_notebook_tabs( notebook_src)
        self._setup_notebook_tabs( notebook_ref)

    def build_menu_names(self,sourceref):
        if self.source:
            source_name = self.source.get_name()
            submenu_label = _('Repository: %s')  % source_name
        else:
            submenu_label = _('New Repository')
        return (_('Repo Reference Editor'),submenu_label)
        
    def ok_clicked(self,obj):

        trans = self.db.transaction_begin()
        if self.source.handle:
            self.db.commit_repository(self.source,trans)
            self.db.transaction_commit(trans,_("Modify Repository"))
        else:
            self.db.add_repository(self.source,trans)
            self.db.transaction_commit(trans,_("Add Repository"))
            self.source_ref.ref = self.source.handle

        if self.update:
            self.update((self.source_ref,self.source))

        self.close()
