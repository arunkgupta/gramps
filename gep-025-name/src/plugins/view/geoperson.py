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
Geography for one person
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
import glib

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
_LOG = logging.getLogger("GeoGraphy.geoperson")

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
from Filters.SideBar import PersonSidebarFilter
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
    <menuitem action="HomePerson"/>
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
  <toolitem action="HomePerson"/>
</placeholder>
</toolbar>
</ui>
'''

#-------------------------------------------------------------------------
#
# GeoView
#
#-------------------------------------------------------------------------
class GeoPerson(GeoGraphyView):
    """
    The view used to render person map.
    """

    def __init__(self, pdata, dbstate, uistate, nav_group=0):
        GeoGraphyView.__init__(self, _("Person places map"),
                                      pdata, dbstate, uistate, 
                                      dbstate.db.get_bookmarks(), 
                                      Bookmarks.PersonBookmarks,
                                      nav_group)
        self.dbstate = dbstate
        self.uistate = uistate
        self.place_list = []
        self.place_without_coordinates = []
        self.minlat = self.maxlat = self.minlon = self.maxlon = 0.0
        self.minyear = 9999
        self.maxyear = 0
        self.nbplaces = 0
        self.nbmarkers = 0
        self.sort = []
        self.additional_uis.append(self.additional_ui())

    def get_title(self):
        """
        Used to set the titlebar in the configuration window.
        """
        return _('GeoPerson')

    def get_stock(self):
        """
        Returns the name of the stock icon to use for the display.
        This assumes that this icon has already been registered 
        as a stock icon.
        """
        return 'geo-show-person'
    
    def get_viewtype_stock(self):
        """Type of view in category
        """
        return 'geo-show-person'

    def additional_ui(self):
        """
        Specifies the UIManager XML code that defines the menus and buttons
        associated with the interface.
        """
        return _UI_DEF

    def navigation_type(self):
        """
        Indicates the navigation type. Navigation type can be the string
        name of any of the primary objects.
        """
        return 'Person'

    def get_bookmarks(self):
        """
        Return the bookmark object
        """
        return self.dbstate.db.get_bookmarks()

    def goto_handle(self, handle=None):
        """
        Rebuild the tree with the given person handle as the root.
        """
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
        active = self.get_active()
        self._createmap(active)

    def animate(self, menu, marks, index, stepyear):
        """
        Create all movements for the people's event.
        Yes, you can see the person moving.
        """
        if len(marks) == 0:
            self.already_started = False
            return False
        i = int(index)
        ni = i + 1
        if ni == len(marks) :
            self.already_started = False
            return False
        startlat = float(marks[i][3])
        startlon = float(marks[i][4])
	heading = 1
	if index == 0 and stepyear == 0:
            self.remove_all_gps()
            self.osm.gps_add(startlat, startlon, heading)
        endlat = float(marks[ni][3])
        endlon = float(marks[ni][4])
        # year format = YYYYMMDD ( for sort )
        startyear = str(marks[i][6])[0:4]
        endyear = str(marks[ni][6])[0:4]
        endmov = str(marks[len(marks)-1][6])[0:4]
        years = int(endyear) - int(startyear)
        if years < 1:
            years = 1
        latstep = ( endlat - startlat ) / years
        lonstep = ( endlon - startlon ) / years
        stepyear = 1 if stepyear < 1 else stepyear
	startlat += ( latstep * stepyear )
	startlon += ( lonstep * stepyear )
        if ( int(startyear) + stepyear ) > int(endmov) :
            self.already_started = False
            return False
	self.osm.gps_add(startlat, startlon, heading)
        stepyear += 1
        difflat = ( startlat - endlat ) if startlat > endlat else \
                                           ( endlat - startlat )
        difflon = ( startlon - endlon ) if startlon > endlon else \
                                           ( endlon - startlon )
        if ( difflat == 0.0 and difflon == 0.0 ):
            i += 1
            if ( int(startyear) + stepyear ) > int(endmov) :
                self.already_started = False
                return False
            stepyear = 1
        # 100ms => 1s per 10 years. 
        # For a 100 years person, it takes 10 secondes.
        glib.timeout_add(100, self.animate, menu, marks, i, stepyear)
	return False

    def _createmap(self,obj):
        """
        Create all markers for each people's event in the database which has 
        a lat/lon.
        """
        dbstate = self.dbstate
        self.cal = config.get('preferences.calendar-format-report')
        self.place_list = []
        self.place_without_coordinates = []
        self.minlat = self.maxlat = self.minlon = self.maxlon = 0.0
        self.minyear = 9999
        self.maxyear = 0
        latitude = ""
        longitude = ""
        person_handle = self.uistate.get_active('Person')
        person = dbstate.db.get_person_from_handle(person_handle)
        if person is not None:
            # For each event, if we have a place, set a marker.
            for event_ref in person.get_event_ref_list():
                if not event_ref:
                    continue
                event = dbstate.db.get_event_from_handle(event_ref.ref)
                eyear = str("%04d" % event.get_date_object().to_calendar(self.cal).get_year()) + \
                          str("%02d" % event.get_date_object().to_calendar(self.cal).get_month()) + \
                          str("%02d" % event.get_date_object().to_calendar(self.cal).get_day())
                place_handle = event.get_place_handle()
                if place_handle:
                    place = dbstate.db.get_place_from_handle(place_handle)
                    if place:
                        longitude = place.get_longitude()
                        latitude = place.get_latitude()
                        latitude, longitude = conv_lat_lon(latitude,
                                                           longitude, "D.D8")
                        descr = place.get_title()
                        evt = gen.lib.EventType(event.get_type())
                        descr1 = _("%(eventtype)s : %(name)s") % {
                                        'eventtype': evt,
                                        'name': _nd.display(person)}
                        # place.get_longitude and place.get_latitude return
                        # one string. We have coordinates when the two values
                        # contains non null string.
                        if ( longitude and latitude ):
                            self._append_to_places_list(descr, evt,
                                                        _nd.display(person),
                                                        latitude, longitude,
                                                        descr1, eyear,
                                                        event.get_type(),
                                                        person.gramps_id,
                                                        place.gramps_id,
                                                        event.gramps_id,
                                                        None
                                                        )
                        else:
                            self._append_to_places_without_coord(
                                                        place.gramps_id, descr)
            family_list = person.get_family_handle_list()
            for family_hdl in family_list:
                family = self.dbstate.db.get_family_from_handle(family_hdl)
                if family is not None:
                    fhandle = family_list[0] # first is primary
                    fam = dbstate.db.get_family_from_handle(fhandle)
                    handle = fam.get_father_handle()
                    father = dbstate.db.get_person_from_handle(handle)
                    if father:
                        descr1 = "%s - " % _nd.display(father)
                    handle = fam.get_mother_handle()
                    mother = dbstate.db.get_person_from_handle(handle)
                    if mother:
                        descr1 = "%s%s" % ( descr1, _nd.display(mother))
                    for event_ref in family.get_event_ref_list():
                        if event_ref:
                            event = dbstate.db.get_event_from_handle(event_ref.ref)
                            if event.get_place_handle():
                                place_handle = event.get_place_handle()
                                if place_handle:
                                    place = dbstate.db.get_place_from_handle(place_handle)
                                    if place:
                                        longitude = place.get_longitude()
                                        latitude = place.get_latitude()
                                        latitude, longitude = conv_lat_lon(latitude,
                                                                           longitude, "D.D8")
                                        descr = place.get_title()
                                        evt = gen.lib.EventType(event.get_type())
                                        eyear = str("%04d" % event.get_date_object().to_calendar(self.cal).get_year()) + \
                                                  str("%02d" % event.get_date_object().to_calendar(self.cal).get_month()) + \
                                                  str("%02d" % event.get_date_object().to_calendar(self.cal).get_day())
                                        if ( longitude and latitude ):
                                            self._append_to_places_list(descr,
                                                 evt, _nd.display(person),
                                                 latitude, longitude,
                                                 descr1, eyear,
                                                 event.get_type(),
                                                 person.gramps_id,
                                                 place.gramps_id,
                                                 event.gramps_id,
                                                 None
                                                 )
                                        else:
                                            self._append_to_places_without_coord( place.gramps_id, descr)

            self.sort = sorted(self.place_list,
                               key=operator.itemgetter(6)
                              )
            self._create_markers()

    def bubble_message(self, event, lat, lon, marks):
        menu = gtk.Menu()
        menu.set_title("person")
        message = ""
        oldplace = ""
        prevmark = None
        for mark in marks:
            if oldplace != "":
                add_item = gtk.MenuItem(message)
                add_item.show()
                menu.append(add_item)
                itemoption = gtk.Menu()
                itemoption.set_title(message)
                itemoption.show()
                add_item.set_submenu(itemoption)
                modify = gtk.MenuItem(_("Edit event"))
                modify.show()
                modify.connect("activate", self.edit_event,
                               event, lat, lon, prevmark)
                itemoption.append(modify)
                center = gtk.MenuItem(_("Center on this place"))
                center.show()
                center.connect("activate", self.center_here,
                               event, lat, lon, prevmark)
                itemoption.append(center)
            if mark[0] != oldplace:
                if message != "":
                    add_item = gtk.MenuItem()
                    add_item.show()
                    menu.append(add_item)
                    itemoption = gtk.Menu()
                    itemoption.set_title(message)
                    itemoption.show()
                    add_item.set_submenu(itemoption)
                    modify = gtk.MenuItem(_("Edit event"))
                    modify.show()
                    modify.connect("activate", self.edit_event,
                                   event, lat, lon, mark)
                    itemoption.append(modify)
                    center = gtk.MenuItem(_("Center on this place"))
                    center.show()
                    center.connect("activate", self.center_here,
                                   event, lat, lon, mark)
                    itemoption.append(center)
                message = "%s :" % mark[0]
                self.add_place_bubble_message(event, lat, lon,
                                              marks, menu, message, mark)
                oldplace = mark[0]
            message = "%s : %s" % ( mark[2], mark[1] )
            prevmark = mark
        add_item = gtk.MenuItem(message)
        add_item.show()
        menu.append(add_item)
        itemoption = gtk.Menu()
        itemoption.set_title(message)
        itemoption.show()
        add_item.set_submenu(itemoption)
        modify = gtk.MenuItem(_("Edit event"))
        modify.show()
        modify.connect("activate", self.edit_event, event, lat, lon, prevmark)
        itemoption.append(modify)
        center = gtk.MenuItem(_("Center on this place"))
        center.show()
        center.connect("activate", self.center_here, event, lat, lon, prevmark)
        itemoption.append(center)
        menu.popup(None, None, None, 0, event.time)
        return 1

    def add_specific_menu(self, menu, event, lat, lon): 
        """ 
        Add specific entry to the navigation menu.
        """ 
        add_item = gtk.MenuItem()
        add_item.show()
        menu.append(add_item)
        add_item = gtk.MenuItem(_("Animate"))
        add_item.connect("activate", self.animate, self.sort, 0, 0)
        add_item.show()
        menu.append(add_item)
        return

