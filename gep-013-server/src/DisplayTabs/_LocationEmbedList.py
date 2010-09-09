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
# Python classes
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS classes
#
#-------------------------------------------------------------------------
import gen.lib
import Errors
from DdTargets import DdTargets
from _LocationModel import LocationModel
from _EmbeddedList import EmbeddedList

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
class LocationEmbedList(EmbeddedList):

    _HANDLE_COL = 5
    _DND_TYPE   = DdTargets.LOCATION
    
    #index = column in model. Value =
    #  (name, sortcol in model, width, markup/text, weigth_col
    _column_names = [
        (_('Street'),         0, 150, 0, -1), 
        (_('City'),           1, 100, 0, -1), 
        (_('County'),         2, 100, 0, -1), 
        (_('State/Province'), 3, 100, 0, -1), 
        (_('Country'),        4, 75, 0, -1), 
        ]
    
    def __init__(self, dbstate, uistate, track, data):
        self.data = data
        EmbeddedList.__init__(self, dbstate, uistate, track, 
                              _('Alternate _Locations'), LocationModel, 
                              move_buttons=True)

    def get_data(self):
        return self.data

    def column_order(self):
        return ((1, 0), (1, 1), (1, 2), (1, 3), (1, 4))

    def add_button_clicked(self, obj):
        loc = gen.lib.Location()
        try:
            from Editors import EditLocation
            
            EditLocation(self.dbstate, self.uistate, self.track, 
                         loc, self.add_callback)
        except Errors.WindowActiveError:
            pass

    def add_callback(self, name):
        self.get_data().append(name)
        self.rebuild()

    def edit_button_clicked(self, obj):
        loc = self.get_selected()
        if loc:
            try:
                from Editors import EditLocation
                
                EditLocation(self.dbstate, self.uistate, self.track, 
                             loc, self.edit_callback)
            except Errors.WindowActiveError:
                pass

    def edit_callback(self, name):
        self.rebuild()
