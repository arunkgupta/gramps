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

# $Id$

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
import ManagedWindow
from DisplayTabs import GrampsTab
import Config

#-------------------------------------------------------------------------
#
# Classes
#
#-------------------------------------------------------------------------

class RefTab(GrampsTab):
    """
    This class provides a simple tabpage for use on EditReference
    """

    def __init__(self, dbstate, uistate, track, name, widget):
        """
        @param dbstate: The database state. Contains a reference to
        the database, along with other state information. The GrampsTab
        uses this to access the database and to pass to and created
        child windows (such as edit dialogs).
        @type dbstate: DbState
        @param uistate: The UI state. Used primarily to pass to any created
        subwindows.
        @type uistate: DisplayState
        @param track: The window tracking mechanism used to manage windows.
        This is only used to pass to generted child windows.
        @type track: list
        @param name: Notebook label name
        @type name: str/unicode
        @param widget: widget to be shown in the tab
        @type widge: gtk widget
        """
        GrampsTab.__init__(self, dbstate, uistate, track, name)
        eventbox = gtk.EventBox()
        eventbox.add(widget)
        self.pack_start(eventbox)
        self._set_label(show_image=False)
        widget.connect('key_press_event', self.key_pressed)
        self.show_all()

    def is_empty(self):
        """
        Override base class
        """
        return False

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
            label.connect('drag_motion',
                          self._switch_page_on_dnd,
                          notebook,
                          page_no)
            child.set_parent_notebook(notebook)
        notebook.connect('key-press-event', self.key_pressed, notebook)

    def key_pressed(self, obj, event, notebook):
        """
        Handles the key being pressed on the notebook, pass to key press of
        current page.
        """
        pag = notebook.get_current_page()
        if not pag == -1:
            notebook.get_nth_page(pag).key_pressed(obj, event)

    def _switch_page_on_dnd(self, widget, context, x, y, time, notebook, page_no):
        if notebook.get_current_page() != page_no:
            notebook.set_current_page(page_no)

    def _add_tab(self, notebook,page):
        notebook.insert_page(page, page.get_tab_widget())
        page.add_db_signal_callback(self._add_db_signal)
        page.label.set_use_underline(True)
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
        #the window key for managedwindow identification. No need to return None
        if self.source and self.source.get_handle():
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

    def define_help_button(self, button, tag, webpage='', section=''):
        import GrampsDisplay
        button.connect('clicked', lambda x: GrampsDisplay.help(tag, webpage,
                                                               section))
        button.set_sensitive(True)

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
