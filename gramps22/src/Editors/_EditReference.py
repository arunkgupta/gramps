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

# $Id: _EditSourceRef.py 6068 2006-03-04 06:34:48Z dallingham $

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import ManagedWindow
from GrampsWidgets import *
import Config

#-------------------------------------------------------------------------
#
# EditReference class
#
#-------------------------------------------------------------------------
class EditReference(ManagedWindow.ManagedWindow):

    WIDTH_KEY = None
    HEIGHT_KEY = None

    def __init__(self, state, uistate, track, source, source_ref, update):
        self.db = state.db
        self.dbstate = state
        self.uistate = uistate
        self.source_ref = source_ref
        self.source = source
        self.source_added = False
        self.update = update
        self.signal_keys = []
        self.warn_box = None

        ManagedWindow.ManagedWindow.__init__(self, uistate, track, source_ref)

        self._local_init()
        self._set_size()
        self._create_tabbed_pages()
        self._setup_fields()
        self._connect_signals()
        self.show()
        self._post_init()

    def _set_size(self):
        if self.WIDTH_KEY:
            width = Config.get(self.WIDTH_KEY)
            height = Config.get(self.HEIGHT_KEY)
            self.window.resize(width, height)

    def _local_init(self):
        """
        Derived class should do any pre-window initalization in this task.
        """
        pass

    def define_warn_box(self,box):
        self.warn_box = box

    def enable_warnbox(self):
        self.warn_box.show()

    def define_expander(self,expander):
        expander.set_expanded(True)

    def _post_init(self):
        """
        Derived class should do any post-window initalization in this task.
        """
        pass

    def _setup_notebook_tabs(self, notebook):
        for child in notebook.get_children():
            label = notebook.get_tab_label(child)
            page_no = notebook.page_num(child)
            label.drag_dest_set(0, [], 0)
            label.connect('drag_motion', self._switch_page_on_dnd,notebook,page_no)
    
    def _switch_page_on_dnd(self, widget, context, x, y, time, notebook, page_no):
        if notebook.get_current_page() != page_no:
            notebook.set_current_page(page_no)

    def _add_tab(self,notebook,page):
        notebook.insert_page(page, page.get_tab_widget())
        page.add_db_signal_callback(self._add_db_signal)
        return page

    def _add_db_signal(self, name, callback):
        self.signal_keys.append(self.db.connect(name,callback))
        
    def _connect_signals(self):
        pass

    def _setup_fields(self):
        pass

    def _create_tabbed_pages(self):
        pass

    def build_window_key(self,sourceref):
        if self.source:
            return self.source.get_handle()
        else:
            return id(self)

    def define_ok_button(self, button, function):
        button.connect('clicked',function)
        button.set_sensitive(not self.db.readonly)

    def define_cancel_button(self, button):
        button.connect('clicked',self.close_and_cancel)

    def close_and_cancel(self, obj):
        self._cleanup_on_exit()
        self.close(obj)

    def define_help_button(self,button,tag):
        import GrampsDisplay
        button.connect('clicked', lambda x: GrampsDisplay.help(tag))

    def _cleanup_on_exit(self):
        pass

    def close(self,*obj):
        for key in self.signal_keys:
            self.db.disconnect(key)
        self._save_size()
        ManagedWindow.ManagedWindow.close(self)

    def _save_size(self):
        if self.HEIGHT_KEY:
            (width, height) = self.window.get_size()
            Config.set(self.WIDTH_KEY, width)
            Config.set(self.HEIGHT_KEY, height)
            Config.sync()
