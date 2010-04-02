#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2004  Donald N. Allingham
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
Handles the place view for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# GTK modules
#
#-------------------------------------------------------------------------
import gtk
import gtk.gdk

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
import RelLib
import EditPlace
import DisplayModels
import const

from QuestionDialog import QuestionDialog, ErrorDialog
from gettext import gettext as _

column_names = [
    _('Place Name'),
    _('ID'),
    _('Church Parish'),
    _('ZIP/Postal Code'),
    _('City'),
    _('County'),
    _('State'),
    _('Country'),
    _('Longitude'),
    _('Latitude'),
    _('Last Changed'),
    ]

_HANDLE_COL = len(column_names)
#-------------------------------------------------------------------------
#
# PlaceView class
#
#-------------------------------------------------------------------------
class PlaceView:
    
    def __init__(self,parent,db,glade):
        self.parent = parent
        self.parent.connect('database-changed',self.change_db)

        self.glade  = glade
        self.list   = glade.get_widget("place_list")
        self.list.connect('button-press-event',self.button_press)
        self.list.connect('key-press-event',self.key_press)
        self.selection = self.list.get_selection()
        self.selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.renderer = gtk.CellRendererText()
        self.model = DisplayModels.PlaceModel(self.parent.db)
            
        self.list.set_model(self.model)
        self.topWindow = self.glade.get_widget("gramps")
        self.sort_col = 0
        
        self.columns = []
        self.change_db(db)

    def column_clicked(self,obj,data):
        if self.sort_col != data:
            order = gtk.SORT_ASCENDING
        else:
            if (self.columns[data].get_sort_order() == gtk.SORT_DESCENDING
                or self.columns[data].get_sort_indicator() == False):
                order = gtk.SORT_ASCENDING
            else:
                order = gtk.SORT_DESCENDING
        self.sort_col = data
        handle = self.first_selected()
        colmap = self.parent.db.get_place_column_order()

        self.model = DisplayModels.PlaceModel(self.parent.db,
                                              self.scol_map[self.sort_col],order)
        self.list.set_model(self.model)

        
        if handle:
            path = self.model.on_get_path(handle)
            self.selection.select_path(path)
            self.list.scroll_to_cell(path,None,1,0.5,0)
        for i in range(0,len(self.columns)):
            self.columns[i].set_sort_indicator(i==self.sort_col)
        self.columns[self.sort_col].set_sort_order(order)

    def build_columns(self):
        for column in self.columns:
            self.list.remove_column(column)
            
        column = gtk.TreeViewColumn(_('Place Name'), self.renderer,text=0)
        column.set_resizable(True)
        column.set_min_width(225)
        column.connect('clicked',self.column_clicked,0)
        column.set_clickable(True)
        self.list.append_column(column)
        self.scol_map = [0]
        self.columns = [column]

        index = 1
        for pair in self.parent.db.get_place_column_order():
            if not pair[0]:
                continue
            self.scol_map.append(pair[1])
            name = column_names[pair[1]]
            column = gtk.TreeViewColumn(name, self.renderer, text=pair[1])
            column.set_resizable(True)
            column.set_min_width(75)
            column.set_clickable(True)
            column.connect('clicked',self.column_clicked,index)
            index += 1
            self.columns.append(column)
            self.list.append_column(column)

    def place_add(self,handle_list):
        for handle in handle_list:
            self.model.add_row_by_handle(handle)

    def place_update(self,handle_list):
        for handle in handle_list:
            self.model.update_row_by_handle(handle)

    def place_delete(self,handle_list):
        for handle in handle_list:
            self.model.delete_row_by_handle(handle)

    def change_db(self,db):
        db.connect('place-add',    self.place_add)
        db.connect('place-update', self.place_update)
        db.connect('place-delete', self.place_delete)
        db.connect('place-rebuild',self.build_tree)

        self.build_columns()
        self.build_tree()

    def build_tree(self):
        self.model = DisplayModels.PlaceModel(self.parent.db)
        self.list.set_model(self.model)
        self.selection = self.list.get_selection()
        self.selection.set_mode(gtk.SELECTION_MULTIPLE)

    def button_press(self,obj,event):
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            mlist = []
            self.selection.selected_foreach(self.blist,mlist)
            if mlist:
                place = self.parent.db.get_place_from_handle(mlist[0])
                EditPlace.EditPlace(self.parent,place,self.topWindow)
            return 1
        elif event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            self.build_context_menu(event)
            return 1
        return 0

    def key_press(self,obj,event):
        if event.keyval == gtk.gdk.keyval_from_name("Return") \
                                        and not event.state:
            self.on_edit_clicked(obj)
            return 1
        return 0

    def build_context_menu(self,event):
        """Builds the menu with editing operations on the place's list"""
        
        mlist = []
        self.selection.selected_foreach(self.blist,mlist)
        if mlist:
            sel_sensitivity = 1
        else:
            sel_sensitivity = 0
        entries = [
            (gtk.STOCK_ADD, self.on_add_place_clicked,1),
            (gtk.STOCK_REMOVE, self.on_delete_clicked,sel_sensitivity),
            (_("Edit"), self.on_edit_clicked,sel_sensitivity),
        ]

        menu = gtk.Menu()
        menu.set_title(_('Place Menu'))
        for stock_id,callback,sensitivity in entries:
            item = gtk.ImageMenuItem(stock_id)
            if callback:
                item.connect("activate",callback)
            item.set_sensitive(sensitivity)
            item.show()
            menu.append(item)
        menu.popup(None,None,None,event.button,event.time)

    def on_add_place_clicked(self,obj):
        EditPlace.EditPlace(self.parent,RelLib.Place())

    def delete_place(self,place):
        trans = self.parent.db.transaction_begin()
        place_handle = place.get_handle()
        self.parent.db.remove_place(place_handle,trans)
        title_msg = _("Delete Place (%s)") % place.get_title()
        self.parent.db.transaction_commit(trans,title_msg)

    def is_used(self,place_handle):
        for handle in self.parent.db.get_person_handles(sort_handles=False):
            person = self.parent.db.get_person_from_handle(handle)
            if person.has_handle_reference('Place',place_handle):
                return True

        for handle in self.parent.db.get_family_handles():
            family = self.parent.db.get_family_from_handle(handle)
            if family.has_handle_reference('Place',place_handle):
                return True

        for handle in self.parent.db.get_event_handles():
            event = self.parent.db.get_event_from_handle(handle)
            if event.has_handle_reference('Place',place_handle):
                return True

        return False    

    def on_delete_clicked(self,obj):
        mlist = []
        self.selection.selected_foreach(self.blist,mlist)
        
        for place_handle in mlist:
            place = self.parent.db.get_place_from_handle(place_handle)
            if self.is_used(place_handle):
                ans = EditPlace.DeletePlaceQuery(place,self.parent.db)
                QuestionDialog(
                    _('Delete %s?') %  place.get_title(),
                    _('This place is currently being used by at least one '
                      'record in the database. Deleting it will remove it '
                      'from the database and remove it from all records '
                      'that reference it.'),
                    _('_Delete Place'),
                    ans.query_response)
            else:
                self.delete_place(place)
                
    def on_edit_clicked(self,obj):
        """Display the selected places in the EditPlace display"""
        mlist = []
        self.selection.selected_foreach(self.blist,mlist)

        for place_handle in mlist:
            place = self.parent.db.get_place_from_handle(place_handle)
            EditPlace.EditPlace(self.parent, place,self.topWindow)

    def first_selected(self):
        mlist = []
        self.selection.selected_foreach(self.blist,mlist)
        if mlist:
            return mlist[0]
        else:
            return None

    def blist(self,store,path,iter,list):
        handle = store.get_value(iter,_HANDLE_COL)
        list.append(handle)

    def merge(self):
        mlist = []
        self.selection.selected_foreach(self.blist,mlist)
        
        if len(mlist) != 2:
            msg = _("Cannot merge places.")
            msg2 = _("Exactly two places must be selected to perform a merge. "
                "A second place can be selected by holding down the "
                "control key while clicking on the desired place.")
            ErrorDialog(msg,msg2)
        else:
            import MergeData
            MergeData.MergePlaces(self.parent.db,mlist[0],mlist[1],self.build_tree)
