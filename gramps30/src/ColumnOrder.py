#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2003  Donald N. Allingham
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

"""
Handle the column ordering
"""

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _
import logging

#-------------------------------------------------------------------------
#
# GTK modules
#
#-------------------------------------------------------------------------
import gtk
from gtk import glade
import gobject

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import const
import ManagedWindow

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
__LOG = logging.getLogger(".ColumnOrder")


class ColumnOrder(ManagedWindow.ManagedWindow):
    """
    Column ordering selection dialog
    """

    def __init__(self, win_name, uistate, arglist, column_names, callback):
        """
        Create the Column Ordering dialog
        """
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self)
        
        self.glade = glade.XML(const.GLADE_FILE, "columns", "gramps")

        self.set_window(self.glade.get_widget('columns'), None, win_name)

        self.tree = self.glade.get_widget('list')
        self.arglist = arglist
        self.callback = callback

        self.model = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, 
                                   gobject.TYPE_INT, object)
        
        self.tree.set_model(self.model)

        checkbox = gtk.CellRendererToggle()
        checkbox.connect('toggled', toggled, self.model)
        renderer = gtk.CellRendererText()
        
        column_n = gtk.TreeViewColumn(_('Display'), checkbox, active=0)
        column_n.set_min_width(50)
        self.tree.append_column(column_n)

        column_n = gtk.TreeViewColumn(_('Column Name'),  renderer, text=1)
        column_n.set_min_width(225)
        self.tree.append_column(column_n)

        self.glade.get_widget('okbutton').connect('clicked',
                                                  self.ok_clicked)
        self.glade.get_widget('cancelbutton').connect('clicked',
                                                      self.cancel_clicked)

        for item in self.arglist:
            node = self.model.append()
            self.model.set(node,
                           0, item[0],
                           1, column_names[item[1]],
                           2, item[1],
                           3, item)

    def build_menu_names(self, obj):
        """
        Build the information for the Managed Window menu entries
        """
        return (_('Column Editor'), _('Column Editor'))

    def ok_clicked(self, obj):
        """
        called with the OK button is pressed
        """
        newlist = []
        for i in range(0, len(self.arglist)):
            node = self.model.get_iter((int(i), ))
            enable = self.model.get_value(node, 0)
            index = self.model.get_value(node, 2)
            value = self.model.get_value(node, 3)
            newlist.append((enable, index, value[2]))

        self.callback(newlist)
        self.close()

    def cancel_clicked(self, obj):
        """
        Called with the Cancel button is pressed.
        """
        self.close()

def toggled(cell, path, model):
    """
    Called when the cell information is changed, updating the
    data model so the that change occurs.
    """
    node = model.get_iter((int(path), ))
    value = not model.get_value(node, 0)
    model.set(node, 0, value)
