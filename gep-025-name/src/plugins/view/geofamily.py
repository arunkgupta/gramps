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
Geography for one family
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
_LOG = logging.getLogger("GeoGraphy.geofamily")

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
from Filters.SideBar import FamilySidebarFilter
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
class GeoFamily(GeoGraphyView):
    """
    The view used to render person map.
    """

    def __init__(self, pdata, dbstate, uistate, nav_group=0):
        _LOG.debug("GeoFamily : __init__")
        GeoGraphyView.__init__(self, _('Family places map'),
                                      pdata, dbstate, uistate, 
                                      dbstate.db.get_family_bookmarks(), 
                                      Bookmarks.FamilyBookmarks,
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
        return _('GeoFamily')

    def get_stock(self):
        """
        Returns the name of the stock icon to use for the display.
        This assumes that this icon has already been registered 
        as a stock icon.
        """
        _LOG.debug("get_stock")
        return 'geo-show-family'
    
    def get_viewtype_stock(self):
        """Type of view in category
        """
        _LOG.debug("get_viewtype_stock")
        return 'geo-show-family'

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
        return 'Family'

    def get_bookmarks(self):
        """
        Return the bookmark object
        """
        return self.dbstate.db.get_family_bookmarks()

    def goto_handle(self, handle=None):
        """
        Rebuild the tree with the given person handle as the root.
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
        if not self.uistate.get_active('Family') and self.uistate.get_active('Family'):
            return
        if self.uistate.get_active('Family'):
            _LOG.debug("build_tree for active family")
            self._createmap(self.uistate.get_active('Family'))
        else:
            _LOG.debug("build_tree for active person")
            self._createmap(self.uistate.get_active('Person'))

    def _createpersonmarkers(self, dbstate, person, comment):
        """
        Create all markers for the specified person.
        """
        self.cal = config.get('preferences.calendar-format-report')
        latitude = longitude = ""
        if person:
            event_ref = person.get_birth_ref()
            if event_ref:
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
                        if comment:
                            descr1 = _("%s : birth place.") % comment
                        else:
                            descr1 = _("birth place.")
                        descr = place.get_title()
                        # place.get_longitude and place.get_latitude return
                        # one string. We have coordinates when the two values
                        # contains non null string.
                        if ( longitude and latitude ):
                            self._append_to_places_list(descr,
                                                        gen.lib.EventType.BIRTH,
                                                        _nd.display(person),
                                                        latitude, longitude,
                                                        descr1,
                                                        int(self.center),
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
            latitude = longitude = ""
            event_ref = person.get_death_ref()
            if event_ref:
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
                        if comment:
                            descr1 = _("%s : death place.") % comment
                        else:
                            descr1 = _("death place.")
                        if ( longitude and latitude ):
                            self._append_to_places_list(descr,
                                                        gen.lib.EventType.DEATH,
                                                        _nd.display(person),
                                                        latitude, longitude,
                                                        descr1,
                                                        int(self.center),
                                                        eventyear,
                                                        event.get_type(),
                                                        person.gramps_id,
                                                        place.gramps_id,
                                                        event.gramps_id
                                                        )
                            self.center = False


    def _createmap_for_one_family(self, family):
        """
        Create all markers for one family : all event's places with a lat/lon.
        """
        _LOG.debug("_createmap_for_one_family")
        dbstate = self.dbstate
        try:
            person = dbstate.db.get_person_from_handle(family.get_father_handle())
        except:
            _LOG.debug("_createmap_for_one_family : no family")
            return
        if person is None: # family without father ?
            _LOG.debug("family without father. mother ?")
            person = dbstate.db.get_person_from_handle(family.get_mother_handle())
        if person is None:
            _LOG.debug("no family bookmark. use active person")
            person = dbstate.db.get_person_from_handle(self.uistate.get_active('Person'))
        if person is not None:
            family_list = person.get_family_handle_list()
            if len(family_list) > 0:
                fhandle = family_list[0] # first is primary
                fam = dbstate.db.get_family_from_handle(fhandle)
                handle = fam.get_father_handle()
                father = dbstate.db.get_person_from_handle(handle)
                if father:
                    comment = _("Father : %s : %s") % ( father.gramps_id,
                                                             _nd.display(father)
                                                            )
                    self._createpersonmarkers(dbstate, father, comment)
                handle = fam.get_mother_handle()
                mother = dbstate.db.get_person_from_handle(handle)
                if mother:
                    comment = _("Mother : %s : %s") % ( mother.gramps_id,
                                                             _nd.display(mother)
                                                            )
                    self._createpersonmarkers(dbstate, mother, comment)
                index = 0
                child_ref_list = fam.get_child_ref_list()
                if child_ref_list:
                    for child_ref in child_ref_list:
                        child = dbstate.db.get_person_from_handle(child_ref.ref)
                        if child:
                            index += 1
                            comment = _("Child : %(id)s - %(index)d "
                                        ": %(name)s") % {
                                            'id'    : child.gramps_id,
                                            'index' : index,
                                            'name'  : _nd.display(child)
                                         }
                            self._createpersonmarkers(dbstate, child, comment)
            else:
                comment = _("Person : %(id)s %(name)s has no family.") % {
                                'id' : person.gramps_id ,
                                'name' : _nd.display(person)
                                }
                self._createpersonmarkers(dbstate, person, comment)

    def _createmap(self, family_x):
        """
        Create all markers for each people's event in the database which has 
        a lat/lon.
        """
        _LOG.debug("_createmap")
        self.place_list = []
        self.place_without_coordinates = []
        self.minlat = self.maxlat = self.minlon = self.maxlon = 0.0
        self.minyear = 9999
        self.maxyear = 0
        self.center = True
        family = self.dbstate.db.get_family_from_handle(family_x)
        if family is None:
            person = self.dbstate.db.get_person_from_handle(self.uistate.get_active('Person'))
            if not person:
                return
            family_list = person.get_family_handle_list()
            for family_hdl in family_list:
                family = self.dbstate.db.get_family_from_handle(family_hdl)
                if family is not None:
                    _LOG.debug("_createmap except family : %s" % family)
                    self._createmap_for_one_family(family)
        else:
            self._createmap_for_one_family(family)
        self.sort = sorted(self.place_list,
                           key=operator.itemgetter(3, 4, 7)
                          )
        self._create_markers()

    def bubble_message(self, event, lat, lon, marks):
        _LOG.debug("bubble_message")
        menu = gtk.Menu()
        menu.set_title("family")
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
                    modify.connect("activate", self.edit_place, event, lat, lon, marks)
                    itemoption.append(modify)
                    center = gtk.MenuItem(_("Center on this place"))
                    center.show()
                    center.connect("activate", self.center_here, event, lat, lon, marks)
                    itemoption.append(center)
                message = "%s :" % mark[0]
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
            message = "%s" % mark[5]
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
        return

