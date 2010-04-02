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

# $Id$

#-------------------------------------------------------------------------
#
# internationalization
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
from DisplayModels import PlaceModel
from _BaseSelector import BaseSelector
import Config

#-------------------------------------------------------------------------
#
# SelectPlace
#
#-------------------------------------------------------------------------
class SelectPlace(BaseSelector):

    def _local_init(self):
        """
        Perform local initialisation for this class
        """
        self.width_key = Config.PLACE_SEL_WIDTH
        self.height_key = Config.PLACE_SEL_HEIGHT

    def get_window_title(self):
        return _("Select Place")
        
    def get_model_class(self):
        return PlaceModel

    def get_column_titles(self):
        return [
            (_('Title'), 350, BaseSelector.TEXT),
            (_('ID'),     75, BaseSelector.TEXT)
            ]

    def get_from_handle_func(self):
        return self.db.get_place_from_handle
        
    def get_handle_column(self):
        return PlaceModel.HANDLE_COL
    
    def column_order(self):
        """
        returns a tuple indicating the column order of the model
        """
        return self.db.get_place_column_order()
    
    def column_view_names(self):
        """
        Get correct column view names on which model is based
        """
        import DataViews
        return DataViews.PlaceView.COLUMN_NAMES
