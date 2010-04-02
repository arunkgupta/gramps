#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2003-2004  Donald N. Allingham
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
# internationalization
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
import pango

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
from DisplayModels import PeopleModel
import ManagedWindow

column_names = [
    _('Name'),
    _('ID') ,
    _('Gender'),
    _('Birth Date'),
    _('Birth Place'),
    _('Death Date'),
    _('Death Place'),
    _('Spouse'),
    _('Last Change'),
    ]

#-------------------------------------------------------------------------
#
# SelectPerson
#
#-------------------------------------------------------------------------
class SelectPerson(ManagedWindow.ManagedWindow):

    def __init__(self, dbstate, uistate, track=[], title='',
                 filter=None, skip=[]):
        if title:
            self.title = title
        else:
            self.title = _("Select Person")

        ManagedWindow.ManagedWindow.__init__(self, uistate, track, self)

        self.renderer = gtk.CellRendererText()
        self.renderer.set_property('ellipsize',pango.ELLIPSIZE_END)
        self.dbstate = dbstate
        self.glade = glade.XML(const.GLADE_FILE,"select_person","gramps")
        self.plist =  self.glade.get_widget('plist')
        self.showall =  self.glade.get_widget('showall')
        self.notebook =  self.glade.get_widget('notebook')
        self.plist.connect('row-activated', self._on_row_activated)
        self.plist.connect('key-press-event', self._key_press)
        self.selection = self.plist.get_selection()
        self.selection.set_mode(gtk.SELECTION_SINGLE)

        window = self.glade.get_widget('select_person')
        title_label = self.glade.get_widget('title')
        self.set_window(window,title_label,self.title)

        self.filter = filter
        if self.filter:
            self.showall.show()

        self.skip = skip

        self.model = PeopleModel(self.dbstate.db,
                                 (PeopleModel.FAST, filter),
                                 skip=skip)

        self.add_columns(self.plist)
        self.plist.set_model(self.model)
        self.showall.connect('toggled',self.show_toggle)
        self.show()

    def show_toggle(self, obj):
        if obj.get_active():
            filt = None
        else:
            filt = self.filter

        self.model = PeopleModel(self.dbstate.db,
                     (PeopleModel.FAST, filt),
                     skip=self.skip)
        self.plist.set_model(self.model)

    def build_menu_names(self, obj):
        return (self.title, None)

    def add_columns(self, tree):

        try:
            column = gtk.TreeViewColumn(
                _('Name'),
                self.renderer,
                text=0,
                foreground=self.model.marker_color_column)
            
        except AttributeError:
            column = gtk.TreeViewColumn(_('Name'), self.renderer, text=0)
            
        column.set_resizable(True)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(225)
        tree.append_column(column)

        for pair in self.dbstate.db.get_person_column_order():
            if not pair[0]:
                continue
            name = column_names[pair[1]]
            try:
                column = gtk.TreeViewColumn(
                    name, self.renderer, markup=pair[1],
                    foreground=self.model.marker_color_column)
            except AttributeError:
                column = gtk.TreeViewColumn(
                    name, self.renderer, markup=pair[1])
                
            column.set_resizable(True)
            column.set_fixed_width(pair[2])
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            tree.append_column(column)
        
    def select_function(self,store,path,iter,id_list):
        id_list.append(self.model.get_value(iter,PeopleModel.COLUMN_INT_ID))

    def get_selected_ids(self):
        mlist = []
        self.plist.get_selection().selected_foreach(self.select_function,mlist)
        return mlist

    def run(self):
        val = self.window.run()
        if val == gtk.RESPONSE_OK:
            idlist = self.get_selected_ids()
            self.close()
            if idlist and idlist[0]:
                return_value = self.dbstate.db.get_person_from_handle(idlist[0])
            else:
                return_value = None
            return return_value
        elif val != gtk.RESPONSE_DELETE_EVENT:
            self.close()
            return None

    def _key_press(self, obj, event):
        if not event.state or event.state  in (gtk.gdk.MOD2_MASK, ):
            if event.keyval in (gtk.keysyms.Return, gtk.keysyms.KP_Enter):
                store, paths = self.selection.get_selected_rows()
                if paths and len(paths[0]) == 1 :
                    if self.plist.row_expanded(paths[0]):
                        self.plist.collapse_row(paths[0])
                    else:
                        self.plist.expand_row(paths[0], 0)
                    return True
        return False

    def _on_row_activated(self, treeview, path, view_col):
        store, paths = self.selection.get_selected_rows()
        if paths and len(paths[0]) == 2 :
            self.window.response(gtk.RESPONSE_OK)
