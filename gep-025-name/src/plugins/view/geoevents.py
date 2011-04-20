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
Geography for events
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
_LOG = logging.getLogger("GeoGraphy.geoevents")

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
from Filters.SideBar import EventSidebarFilter
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
class GeoEvents(GeoGraphyView):
    """
    The view used to render events map.
    """

    def __init__(self, pdata, dbstate, uistate, nav_group=0):
        _LOG.debug("GeoEvents : __init__")
        GeoGraphyView.__init__(self, _('Events places map'),
                                      pdata, dbstate, uistate, 
                                      dbstate.db.get_event_bookmarks(), 
                                      Bookmarks.EventBookmarks,
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
        return _('GeoEvents')

    def get_stock(self):
        """
        Returns the name of the stock icon to use for the display.
        This assumes that this icon has already been registered 
        as a stock icon.
        """
        _LOG.debug("get_stock")
        return 'geo-show-events'
    
    def get_viewtype_stock(self):
        """Type of view in category
        """
        _LOG.debug("get_viewtype_stock")
        return 'geo-show-events'

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
        return 'Event'

    def get_bookmarks(self):
        """
        Return the bookmark object
        """
        return self.dbstate.db.get_event_bookmarks()

    def goto_handle(self, handle=None):
        """
        Rebuild the tree with the given events handle as the root.
        """
        _LOG.debug("goto_handle")
        if handle:
            self.change_active(handle)
            self._createmap(handle)
        self.uistate.modify_statusbar(self.dbstate)

    def show_all_events(self, menu, event, lat, lon):
        """
        Ask to show all events.
        """
        _LOG.debug("show_all_events")
        self._createmap(None)

    def build_tree(self):
        """
        This is called by the parent class when the view becomes visible. Since
        all handling of visibility is now in rebuild_trees, see that for more
        information.
        """
        _LOG.debug("build_tree")
        active = self.uistate.get_active('Event')
        if active:
            self._createmap(active)
        else:
            self._createmap(None)

    def _createmap_for_one_event(self,event):
        """
        Create all markers for each people's event in the database which has 
        a lat/lon.
        """
        _LOG.debug("_createmap")
        dbstate = self.dbstate
        descr2 = ""
        place_handle = event.get_place_handle()
        eventyear = event.get_date_object().to_calendar(self.cal).get_year()
        if place_handle:
            place = dbstate.db.get_place_from_handle(place_handle)
            if place:
                descr1 = place.get_title()
                longitude = place.get_longitude()
                latitude = place.get_latitude()
                latitude, longitude = conv_lat_lon(latitude, longitude,
                                                   "D.D8")
                # place.get_longitude and place.get_latitude return
                # one string. We have coordinates when the two values
                # contains non null string.
                if ( longitude and latitude ):
                    person_list = [
                        dbstate.db.get_person_from_handle(ref_handle)
                        for (ref_type, ref_handle) in
                            dbstate.db.find_backlink_handles(event.handle)
                                if ref_type == 'Person'
                                  ]
                    #descr2 = "%s" % event.get_type()
                    if person_list:
                        for person in person_list:
                            #descr2 = ("%(description)s - %(name)s") % {
                            #            'description' : descr2,
                            #            'name' : _nd.display(person)}
                            descr2 = ("%s") % _nd.display(person)
                        #descr = ("%(eventtype)s;"+
                        descr = (
                                 "%(description)s"
                                 #) % { 'eventtype': gen.lib.EventType(
                                 #                       event.get_type()
                                 #                       ),
                                 ) % { 
                                       #'place': place.get_title(),
                                       'description': descr2}
                    else:
                        descr = ("%(eventtype)s; %(place)s") % {
                                       'eventtype': gen.lib.EventType(
                                                        event.get_type()
                                                        ),
                                       'place': place.get_title()}
                    self._append_to_places_list(descr1, descr,
                                                descr,
                                                latitude, longitude,
                                                descr2, self.center,
                                                eventyear,
                                                event.get_type(),
                                                None, # person.gramps_id
                                                place.gramps_id,
                                                event.gramps_id
                                                )
                    self.center = False
                else:
                    descr = place.get_title()
                    self._append_to_places_without_coord(
                         place.gramps_id, descr)

    def _createmap(self,obj):
        """
        Create all markers for each people's event in the database which has 
        a lat/lon.
        """
        _LOG.debug("_createmap")
        dbstate = self.dbstate
        self.place_list = []
        self.place_without_coordinates = []
        self.minlat = self.maxlat = self.minlon = self.maxlon = 0.0
        self.minyear = 9999
        self.maxyear = 0
        latitude = ""
        longitude = ""
        self.without = 0
        self.center = True
        self.cal = config.get('preferences.calendar-format-report')

        if obj is None:
            events_handle = dbstate.db.iter_event_handles()
            for event_hdl in events_handle:
                event = dbstate.db.get_event_from_handle(event_hdl)
                self._createmap_for_one_event(event)
        else:
            event = dbstate.db.get_event_from_handle(obj)
            self._createmap_for_one_event(event)
        self.sort = sorted(self.place_list,
                           key=operator.itemgetter(7)
                          )
        self._create_markers()

    def bubble_message(self, event, lat, lon, marks):
        _LOG.debug("bubble_message")
        menu = gtk.Menu()
        menu.set_title("events")
        message = ""
        oldplace = ""
        for mark in marks:
            if message != "":
                add_item = gtk.MenuItem(message)
                add_item.show()
                menu.append(add_item)
                itemoption = gtk.Menu()
                itemoption.set_title(message)
                itemoption.show()
                add_item.set_submenu(itemoption)
                modify = gtk.MenuItem(_("Edit event"))
                modify.show()
                modify.connect("activate", self.edit_event, event, lat, lon, marks)
                itemoption.append(modify)
                center = gtk.MenuItem(_("Center on this place"))
                center.show()
                center.connect("activate", self.center_here, event, lat, lon, marks)
                itemoption.append(center)
            if mark[0] != oldplace:
                if message != "":
                    add_item = gtk.MenuItem(message)
                    add_item.show()
                    menu.append(add_item)
                    itemoption = gtk.Menu()
                    itemoption.set_title(message)
                    itemoption.show()
                    add_item.set_submenu(itemoption)
                    modify = gtk.MenuItem(_("Edit event"))
                    modify.show()
                    modify.connect("activate", self.edit_event, event, lat, lon, marks)
                    itemoption.append(modify)
                    center = gtk.MenuItem(_("Center on this place"))
                    center.show()
                    center.connect("activate", self.center_here, event, lat, lon, marks)
                    itemoption.append(center)
                message = "%s :" % mark[0]
                add_item = gtk.MenuItem()
                add_item.show()
                menu.append(add_item)
                add_item = gtk.MenuItem(message)
                add_item.show()
                menu.append(add_item)
                itemoption = gtk.Menu()
                itemoption.set_title(message)
                itemoption.show()
                add_item.set_submenu(itemoption)
                modify = gtk.MenuItem(_("Edit place"))
                modify.show()
                modify.connect("activate", self.edit_place, event, lat, lon, marks)
                itemoption.append(modify)
                center = gtk.MenuItem(_("Center on this place"))
                center.show()
                center.connect("activate", self.center_here, event, lat, lon, marks)
                itemoption.append(center)
                add_item = gtk.MenuItem()
                add_item.show()
                menu.append(add_item)
                oldplace = mark[0]
            message = "%s : %s" % (gen.lib.EventType( mark[8] ), mark[5] )
        add_item = gtk.MenuItem(message)
        add_item.show()
        menu.append(add_item)
        itemoption = gtk.Menu()
        itemoption.set_title(message)
        itemoption.show()
        add_item.set_submenu(itemoption)
        modify = gtk.MenuItem(_("Edit event"))
        modify.show()
        modify.connect("activate", self.edit_event, event, lat, lon, marks)
        itemoption.append(modify)
        center = gtk.MenuItem(_("Center on this place"))
        center.show()
        center.connect("activate", self.center_here, event, lat, lon, marks)
        itemoption.append(center)
        menu.popup(None, None, None, 0, event.time)
        return 1

    def add_specific_menu(self, menu, event, lat, lon): 
        """ 
        Add specific entry to the navigation menu.
        """ 
        _LOG.debug("add_specific_menu")
        add_item = gtk.MenuItem()
        add_item.show()
        menu.append(add_item)
        add_item = gtk.MenuItem(_("Show all events"))
        add_item.connect("activate", self.show_all_events, event, lat , lon)
        add_item.show()
        menu.append(add_item)

