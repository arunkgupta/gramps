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
from maps.constants import PERSON
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
        _LOG.debug("GeoPerson : __init__")
        GeoGraphyView.__init__(self, pdata, dbstate, uistate, nav_group,
                               _("Person places map"), PERSON)
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
        return _('GeoPerson')

    def get_stock(self):
        """
        Returns the name of the stock icon to use for the display.
        This assumes that this icon has already been registered 
        as a stock icon.
        """
        _LOG.debug("get_stock")
        return 'geo-show-person'
    
    def get_viewtype_stock(self):
        """Type of view in category
        """
        _LOG.debug("get_viewtype_stock")
        return 'geo-show-person'

    def build_wiget(self):
        """
        Specifies the UIManager XML code that defines the menus and buttons
        associated with the interface.
        """
        _LOG.debug("build_wiget")
        return GeoGraphyView.build_wiget(self)

    def additional_ui(self):
        """
        Specifies the UIManager XML code that defines the menus and buttons
        associated with the interface.
        """
        _LOG.debug("additional_ui")
        return _UI_DEF

    def define_actions(self):
        """
        Required define_actions function for NavigationView. Builds the action
        group information required. 
        """
        GeoGraphyView.define_actions(self)

    def navigation_group(self):
        """
        Return the navigation group.
        """
        return self.nav_group

    def navigation_type(self):
        """
        Indicates the navigation type. Navigation type can be the string
        name of any of the primary objects.
        """
        _LOG.debug("navigation_type")
        return 'Person'

    def set_active(self):
        """
        Set view active when we enter into this view.
        """
        self.key_active_changed = self.dbstate.connect(
            'active-changed', self._goto_active_person)
        hobj = self.get_history()
        self.active_signal = hobj.connect(
            'active-changed', self._goto_active_person)
        self._goto_active_person()
        GeoGraphyView.set_active(self)

    def set_inactive(self):
        """
        Set view inactive when switching to another view.
        """
        self.dbstate.disconnect(self.key_active_changed)

    def on_delete(self):
        """
        Save all modified environment
        """
        GeoGraphyView.on_delete(self)
        self._config.save()

    def goto_handle(self, handle=None):
        """
        Rebuild the tree with the given person handle as the root.
        """
        _LOG.debug("goto_handle")
        self.dirty = True
        if handle:
            person = self.dbstate.db.get_person_from_handle(handle)
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
            self._createmap(self)
        except AttributeError, msg:
            _LOG.debug("build_tree error")
        pass

    def _goto_active_person(self, handle=None):
        """
        Here when the Geography page is loaded
        """
        if not self.uistate.get_active('Person'):
            return
        self._createmap(self)

    def _createmap(self,obj):
        """
        Create all markers for each people's event in the database which has 
        a lat/lon.
        """
        _LOG.debug("_createmap")
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
        self.center = True
        if person is not None:
            # For each event, if we have a place, set a marker.
            for event_ref in person.get_event_ref_list():
                if not event_ref:
                    continue
                event = dbstate.db.get_event_from_handle(event_ref.ref)
                eventyear = event.get_date_object().to_calendar(self.cal).get_year()
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
                                                        descr1, self.center, 
                                                        eventyear,
                                                        event.get_type(),
                                                        person.gramps_id,
                                                        place.gramps_id,
                                                        event.gramps_id
                                                        )
                            self.center = False
                        else:
                            self._append_to_places_without_coord(
                                                        place.gramps_id, descr)
            self.sort = sorted(self.place_list,
                               key=operator.itemgetter(7)
                              )
            self._create_markers()

    def bubble_message(self, event, lat, lon, marks):
        _LOG.debug("bubble_message")
        menu = gtk.Menu()
        menu.set_title("person")
        message = ""
        oldplace = ""
        for mark in marks:
            if oldplace != "":
                add_item = gtk.MenuItem(message)
                add_item.connect("activate", self.selected_event, event, lat , lon, mark)
                add_item.show()
                menu.append(add_item)
            if mark[0] != oldplace:
                message = "%s :" % mark[0]
                add_item = gtk.MenuItem(message)
                add_item.connect("activate", self.selected_place, event, lat , lon, mark)
                add_item.show()
                menu.append(add_item)
                add_item = gtk.MenuItem()
                add_item.show()
                menu.append(add_item)
                oldplace = mark[0]
            message = "%s : %s" % ( mark[2], mark[1] )
        add_item = gtk.MenuItem(message)
        add_item.connect("activate", self.selected_event, event, lat , lon, mark)
        add_item.show()
        menu.append(add_item)
        menu.popup(None, None, None, 0, event.time)
        return 1

