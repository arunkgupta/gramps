# -*- python -*-
# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011  Serge Noiraud
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

# $Id: geoview.py 15649 2010-07-23 07:27:32Z ldnp $

"""
Geography for places
"""
#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
import os
import sys
import urlparse
import const
import operator
import locale
from gtk.keysyms import Tab as KEY_TAB
import socket
import gtk

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
_LOG = logging.getLogger("GeoGraphy.geoplaces")

#-------------------------------------------------------------------------
#
# Gramps Modules
#
#-------------------------------------------------------------------------
import gen.lib
import Utils
import config
import Errors
from gen.display.name import displayer as _nd
from PlaceUtils import conv_lat_lon
from gui.views.pageview import PageView
from gui.editors import EditPlace
from gui.selectors.selectplace import SelectPlace
from Filters.SideBar import PlaceSidebarFilter
from gui.views.navigationview import NavigationView
import Bookmarks
from Utils import navigation_label
from maps.geography import GeoGraphyView

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------

_UI_DEF = '''\
<ui>
<menubar name="MenuBar">
<menu action="GoMenu">
  <placeholder name="CommonGo">
    <menuitem action="Back"/>
    <menuitem action="Forward"/>
    <separator/>
  </placeholder>
</menu>
<menu action="BookMenu">
  <placeholder name="AddEditBook">
    <menuitem action="AddBook"/>
    <menuitem action="EditBook"/>
  </placeholder>
</menu>
</menubar>
<toolbar name="ToolBar">
<placeholder name="CommonNavigation">
  <toolitem action="Back"/>  
  <toolitem action="Forward"/>  
</placeholder>
</toolbar>
</ui>
'''

#-------------------------------------------------------------------------
#
# GeoView
#
#-------------------------------------------------------------------------
class GeoPlaces(GeoGraphyView):
    """
    The view used to render places map.
    """

    def __init__(self, pdata, dbstate, uistate, nav_group=0):
        _LOG.debug("GeoPlaces : __init__")
        GeoGraphyView.__init__(self, _('Places places map'),
                                      pdata, dbstate, uistate, 
                                      dbstate.db.get_place_bookmarks(), 
                                      Bookmarks.PlaceBookmarks,
                                      nav_group)
        self.dbstate = dbstate
        self.uistate = uistate
        self.place_list = []
        self.place_without_coordinates = []
        self.minlat = self.maxlat = self.minlon = self.maxlon = 0.0
        self.minyear = 9999
        self.maxyear = 0
        self.center = True
        self.nbplaces = 0
        self.nbmarkers = 0
        self.sort = []
        self.additional_uis.append(self.additional_ui())

    def get_title(self):
        """
        Used to set the titlebar in the configuration window.
        """
        _LOG.debug("get_title")
        return _('GeoPlaces')

    def get_stock(self):
        """
        Returns the name of the stock icon to use for the display.
        This assumes that this icon has already been registered 
        as a stock icon.
        """
        _LOG.debug("get_stock")
        return 'geo-show-place'
    
    def get_viewtype_stock(self):
        """Type of view in category
        """
        _LOG.debug("get_viewtype_stock")
        return 'geo-show-place'

    def additional_ui(self):
        """
        Specifies the UIManager XML code that defines the menus and buttons
        associated with the interface.
        """
        _LOG.debug("additional_ui")
        return _UI_DEF

    def navigation_type(self):
        """
        Indicates the navigation type. Navigation type can be the string
        name of any of the primary objects.
        """
        _LOG.debug("navigation_type")
        return 'Place'

    def get_bookmarks(self):
        """
        Return the bookmark object
        """
        return self.dbstate.db.get_place_bookmarks()

    def goto_handle(self, handle=None):
        """
        Rebuild the tree with the given places handle as the root.
        """
        _LOG.debug("goto_handle")
        if handle:
            self.change_active(handle)
            self._createmap(handle)
        self.uistate.modify_statusbar(self.dbstate)

    def build_tree(self):
        """
        This is called by the parent class when the view becomes visible. Since
        all handling of visibility is now in rebuild_trees, see that for more
        information.
        """
        _LOG.debug("build_tree")
        try:
            active = self.get_active()
            if active:
                self._createmap(active)
        except AttributeError, msg:
            _LOG.debug("build_tree error")

    def _create_one_place(self,place):
        """
        Create one entry for one place with a lat/lon.
        """
        _LOG.debug("_create_one_place")
        descr = place.get_title()
        descr1 = _("Id : %s") % place.gramps_id
        longitude = place.get_longitude()
        latitude = place.get_latitude()
        latitude, longitude = conv_lat_lon(latitude, longitude, "D.D8")
        # place.get_longitude and place.get_latitude return
        # one string. We have coordinates when the two values
        # contains non null string.
        if ( longitude and latitude ):
            self._append_to_places_list(descr, None, "",
                                        latitude, longitude,
                                        descr1, self.center, None,
                                        gen.lib.EventType.UNKNOWN,
                                        None, # person.gramps_id
                                        place.gramps_id,
                                        None # event.gramps_id
                                       )
            self.center = False
        else:
            self._append_to_places_without_coord(place.gramps_id, descr)

    def _createmap(self,place_x):
        """
        Create all markers for each people's event in the database which has 
        a lat/lon.
        """
        _LOG.debug("_createmap")
        dbstate = self.dbstate
        self.cal = config.get('preferences.calendar-format-report')
        self.place_list = []
        self.place_without_coordinates = []
        self.minlat = 0.0
        self.maxlat = 0.0
        self.minlon = 0.0
        self.maxlon = 0.0
        self.minyear = 9999
        self.maxyear = 0
        self.without = 0
        latitude = ""
        longitude = ""
        self.center = True

        try:
            _LOG.debug("_createmap try")
            place = dbstate.db.get_place_from_handle(place_x)
            self._create_one_place(place)
        except:
            _LOG.debug("_createmap except")
            places_handle = dbstate.db.iter_place_handles()
            for place_hdl in places_handle:
                place = dbstate.db.get_place_from_handle(place_hdl)
                self._create_one_place(place)
        self.sort = sorted(self.place_list,
                           key=operator.itemgetter(7)
                          )
        self._create_markers()

    def bubble_message(self, event, lat, lon, marks):
        _LOG.debug("bubble_message")
        menu = gtk.Menu()
        menu.set_title("places")
        message = ""
        for mark in marks:
            if message != "":
                add_item = gtk.MenuItem(message)
                add_item.connect("activate", self.selected_place, event, lat , lon, mark)
                add_item.show()
                menu.append(add_item)
            message = message + "%s" % mark[0]
        add_item = gtk.MenuItem(message)
        add_item.connect("activate", self.selected_place, event, lat , lon, mark)
        add_item.show()
        menu.append(add_item)
        menu.popup(None, None, None, 0, event.time)
        return 1

