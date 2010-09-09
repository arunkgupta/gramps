#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2003-2006  Donald N. Allingham
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

# $Id:_BaseSelector.py 9912 2008-01-22 09:17:46Z acraphae $

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk
import pango

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import ManagedWindow
from Filters import SearchBar
from DisplayModels import PeopleModel
from glade import Glade

#-------------------------------------------------------------------------
#
# SelectEvent
#
#-------------------------------------------------------------------------
class BaseSelector(ManagedWindow.ManagedWindow):
    """Base class for the selectors, showing a dialog from which to select
        one of the primary objects
    """
    
    NONE   = -1
    TEXT   =  0
    MARKUP =  1
    IMAGE  =  2

    def __init__(self, dbstate, uistate, track=[], filter=None, skip=set(),
                 show_search_bar = True):
        """Set up the dialog with the dbstate and uistate, track of parent
            windows for ManagedWindow, initial filter for the model, skip with
            set of handles to skip in the view, and search_bar to show the 
            SearchBar at the top or not. 
        """
        self.filter = filter

        # Set window title, some selectors may set self.title in their __init__
        if not hasattr(self, 'title'):
            self.title = self.get_window_title()

        ManagedWindow.ManagedWindow.__init__(self, uistate, track, self)

        self.renderer = gtk.CellRendererText()
        self.renderer.set_property('ellipsize',pango.ELLIPSIZE_END)

        self.db = dbstate.db
        
        self.glade = Glade()
                
        window = self.glade.toplevel
        self.showall =  self.glade.get_object('showall')
        title_label = self.glade.get_object('title')
        vbox = self.glade.get_object('select_person_vbox')
        self.tree =  self.glade.get_object('plist')
        self.tree.set_headers_visible(True)
        self.tree.set_headers_clickable(True)
        self.tree.connect('row-activated', self._on_row_activated)
        self.tree.grab_focus()
        
        self.colinfo = self.column_view_names()
        #add the search bar
        self.search_bar = SearchBar(dbstate, uistate, self.build_tree)
        filter_box = self.search_bar.build()
        self.setup_filter()
        vbox.pack_start(filter_box, False, False)
        vbox.reorder_child(filter_box, 1)

        self.set_window(window,title_label,self.title)
        
        #set up sorting
        self.sort_col = 0
        self.setupcols = True
        self.columns = []
        self.sortorder = gtk.SORT_ASCENDING

        self.skip_list=skip
        self.build_tree()
        self.selection = self.tree.get_selection()
        
        self._local_init()
        self._set_size()

        self.show()
        #show or hide search bar?
        self.set_show_search_bar(show_search_bar)
        #Hide showall always (used in person selector only)
        if self.filter is not None:
            self.showall.show()
        else:
            self.showall.hide()

    def add_columns(self,tree):
        tree.set_fixed_height_mode(True)
        titles = self.get_column_titles()
        for ix in range(len(titles)):
            item = titles[ix]
            if item[2] == BaseSelector.NONE:
                continue
            elif item[2] == BaseSelector.TEXT:
                column = gtk.TreeViewColumn(item[0],self.renderer,text=ix)
            elif item[2] == BaseSelector.MARKUP:
                column = gtk.TreeViewColumn(item[0],self.renderer,markup=ix)
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            column.set_fixed_width(item[1])
            column.set_resizable(True)
            #connect click
            column.connect('clicked', self.column_clicked, ix)
            column.set_clickable(True)
            ##column.set_sort_column_id(ix) # model has its own sort implemented
            self.columns.append(column)
            tree.append_column(column)           
        
    def build_menu_names(self, obj):
        return (self.title, None)

    def get_selected_ids(self):
        mlist = []
        self.selection.selected_foreach(self.select_function,mlist)
        return mlist

    def select_function(self,store,path,iter,id_list):
        handle_column = self.get_handle_column()
        id_list.append(self.model.get_value(iter, handle_column))

    def run(self):
        val = self.window.run()
        if val == gtk.RESPONSE_OK:
            id_list = self.get_selected_ids()
            self.close()
            if id_list and id_list[0]:
                return self.get_from_handle_func()(id_list[0])
        elif val != gtk.RESPONSE_DELETE_EVENT:
            self.close()
        return None

    def _on_row_activated(self, treeview, path, view_col):
        self.window.response(gtk.RESPONSE_OK)

    def _local_init(self):
        # define selector-specific init routine
        pass

    def get_window_title(self):
        assert False, "Must be defined in the subclass"

    def get_model_class(self):
        assert False, "Must be defined in the subclass"
        
    def get_column_titles(self):
        assert False, "Must be defined in the subclass"

    def get_from_handle_func(self):
        assert False, "Must be defined in the subclass"
        
    def get_handle_column(self):
        # return 3
        assert False, "Must be defined in the subclass"
        
    def set_show_search_bar(self, value):
        """make the search bar at the top shown
        """
        self.show_search_bar = value
        if not self.search_bar :
            return
        if self.show_search_bar :
            self.search_bar.show()
        else :
            self.search_bar.hide()
            
    def begintree(self, store, path, node, sel_list):
        handle_column = self.get_handle_column()
        handle = store.get_value(node, handle_column)
        sel_list.append(handle)
        
    def first_selected(self):
        """ first selected entry in the Selector tree
        """
        mlist = []
        self.selection.selected_foreach(self.begintree, mlist)
        return mlist[0] if mlist else None
            
    def column_order(self):
        """
        Column order for db columns
        
        Derived classes must override this function.
        """
        raise NotImplementedError
    
    def column_view_names(self):
        """
        Get correct column view names on which model is based
        
        Derived classes must override this function.
        """
        raise NotImplementedError
            
    def setup_filter(self):
        """
        Builds the default filters and add them to the filter bar.
        """
        cols = []
        for pair in [pair for pair in self.column_order() if pair[0]]:
            cols.append((self.colinfo[pair[1]], pair[1]))
        self.search_bar.setup_filter(cols)
        
    def build_tree(self):
        """
        Builds the selection people see in the Selector
        """
        #search info for the 
        filter_info = (False, self.search_bar.get_value())
        #set up cols the first time
        if self.setupcols :
            self.add_columns(self.tree)
            
        #reset the model with correct sorting
        if self.get_model_class() is PeopleModel:
            self.model = PeopleModel(self.db,
                                     (PeopleModel.FAST, self.filter),
                                     skip=self.skip_list)
        else:
            self.model = self.get_model_class()(self.db, self.sort_col,
                                                self.sortorder,
                                                sort_map=self.column_order(),
                                                skip=self.skip_list,
                                                search=filter_info)
        
        self.tree.set_model(self.model)

        #sorting arrow in column header (not on start, only on click)
        if not self.setupcols :
            for i in xrange(len(self.columns)):
                enable_sort_flag = (i==self.sort_col)
                self.columns[i].set_sort_indicator(enable_sort_flag)
            self.columns[self.sort_col].set_sort_order(self.sortorder)

        # set the search column to be the sorted column
        if self.get_model_class() is PeopleModel:
            search_col = 0
        else:
            search_col = self.column_order()[self.sort_col][1]
        self.tree.set_search_column(search_col)
        
        self.setupcols = False
        
    def column_clicked(self, obj, data):
        if self.sort_col != data:
            self.sortorder = gtk.SORT_ASCENDING
        else:
            if (self.columns[data].get_sort_order() == gtk.SORT_DESCENDING
                or not self.columns[data].get_sort_indicator()):
                self.sortorder = gtk.SORT_ASCENDING
            else:
                self.sortorder = gtk.SORT_DESCENDING

        self.sort_col = data
        handle = self.first_selected()

        self.build_tree()

        if handle:
            path = self.model.on_get_path(handle)
            self.selection.select_path(path)
            self.tree.scroll_to_cell(path, None, 1, 0.5, 0)
            
        return True

    def show_toggle(self, obj):
        filter = None if obj.get_active() else self.filter

        self.model = PeopleModel(self.db, (PeopleModel.FAST, filter),
                     skip=self.skip_list)
        self.tree.set_model(self.model)
        self.tree.grab_focus()
