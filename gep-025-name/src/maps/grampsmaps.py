# -*- python -*-
# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011       Serge Noiraud
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

# $Id: geography.py 16552 2011-02-03 10:31:37Z snoiraud $

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import sys
import os
import gobject
import time

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
_LOG = logging.getLogger("maps.osmgpsmap")

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# Gramps Modules
#
#-------------------------------------------------------------------------
import const
import constants
from gen.ggettext import sgettext as _
from gen.ggettext import ngettext
from config import config

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
GEOGRAPHY_PATH = os.path.join(const.HOME_DIR, "maps")

#-------------------------------------------------------------------------
#
# osmGpsMap
#
#-------------------------------------------------------------------------
sys.path.append(os.path.join(const.ROOT_DIR, 'maps'))

try:
    import osmgpsmap
except:
    _LOG.debug("import error for osmgpsmap")
    raise

class DummyMapNoGpsPoint(osmgpsmap.GpsMap):
    def do_draw_gps_point(self, drawable):
        pass
gobject.type_register(DummyMapNoGpsPoint)

class DummyLayer(gobject.GObject, osmgpsmap.GpsMapLayer):
    def __init__(self):
        gobject.GObject.__init__(self)
        #_LOG.debug("__init__ DummyLayer")

    def do_draw(self, gpsmap, gdkdrawable):
        #_LOG.debug("do_draw in DummyLayer")
        pass

    def do_render(self, gpsmap):
        #_LOG.debug("do_render in DummyLayer")
        pass

    def do_busy(self):
        #_LOG.debug("do_busy in DummyLayer")
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        _LOG.debug("do_button_press in DummyLayer")
        point = osmgpsmap.point_new_degrees(0.0, 0.0)
        gpsmap.convert_screen_to_geographic(int(gdkeventbutton.x), int(gdkeventbutton.y), point)
        #tooltip.set_markup("%+.4f, %+.4f" % point.get_degrees())
        return False
gobject.type_register(DummyLayer)

class osmGpsMap():
    def __init__(self):
        self.vbox = None
        self.cross_map = None
        self.osm = None
        self.show_tooltips = True

    def build_widget(self):
        _LOG.debug("build_widget in osmgpsmap")
        self.vbox = gtk.VBox(False, 0)
        cache_path = os.path.join(const.HOME_DIR, 'maps')
        if not os.path.isdir(cache_path):
            try:
                os.mkdir(cache_path, 0700)
            except:
                ErrorDialog( _("Could not create media directory %s") %
                             cache_path )
            return

        self.change_map(None,config.get("geography.map_service"))
        #if self.vbox.get_children():
        #    print "get child : ", self.vbox.get_children().widget
        #self.vbox.pack_start(self.osm)
        return self.vbox

    def on_delete(self):
        """
        Save all modified environment
        """
        _LOG.debug("on_delete in osmgpsmap")
        pass

    def change_map(self, obj, map_type):
        _LOG.debug("change_map")
        if obj is not None:
            self.osm.layer_remove_all()
            self.osm.image_remove_all()
            self.vbox.remove(self.osm)
            self.osm.destroy()
        tiles_path=os.path.join(GEOGRAPHY_PATH, constants.tiles_path[map_type])
        config.set("geography.map_service", map_type)
        if 0:
            self.osm = DummyMapNoGpsPoint()
        else:
            self.osm = osmgpsmap.GpsMap(tile_cache=tiles_path,
                                        map_source=constants.map_type[map_type])
        self.current_map = osmgpsmap.GpsMapOsd( show_dpad=False, show_zoom=True)
        self.osm.layer_add(self.current_map)
        self.osm.layer_add( DummyLayer())
        self.cross_map = osmgpsmap.GpsMapOsd( show_crosshair=False)
        self.set_crosshair(config.get("geography.show_cross"))
        self.osm.set_center_and_zoom(config.get("geography.center-lat"),
                                     config.get("geography.center-lon"),
                                     config.get("geography.zoom") )

        self.osm.connect('button_release_event', self.map_clicked)
        self.osm.connect('changed', self.zoom_changed)
        self.osm.show()
        self.vbox.pack_start(self.osm)
        if obj is not None:
            self._createmap(obj)

    def load_map_clicked(self, button):
        _LOG.debug("load_map_clicked")
        uri = self.repouri_entry.get_text()
        format = self.image_format_entry.get_text()
        if uri and format:
            if self.osm:
                #remove old map
                self.vbox.remove(self.osm)
            try:
                self.osm = osmgpsmap.GpsMap(
                    repo_uri=uri,
                    image_format=format
                )
            except Exception, e:
                print "ERROR:", e
                self.osm = osm.GpsMap()

            self.vbox.pack_start(self.osm, True)
            self.osm.connect('button_release_event', self.map_clicked)
            self.osm.show()

    def zoom_changed(self, zoom):
        _LOG.debug("zoom_changed")
        config.set("geography.zoom",self.osm.props.zoom)
        self.save_center(self.osm.props.latitude, self.osm.props.longitude)

    def cache_clicked(self, button):
        _LOG.debug("cache_clicked")
        bbox = self.osm.get_bbox()
        self.osm.download_maps(
            *bbox,
            zoom_start=self.osm.props.zoom,
            zoom_end=self.osm.props.max_zoom
        )

    def on_query_tooltip(self, widget, x, y, keyboard_tip, tooltip, data=None):
        _LOG.debug("on_query_tooltip")
	if keyboard_tip:
            _LOG.debug("on_query_tooltip keyboard_tip")
	    return False
		
	if self.show_tooltips:
	    p = osmgpsmap.point_new_degrees(0.0, 0.0)
	    self.osm.convert_screen_to_geographic(x, y, p)
	    lat,lon = p.get_degrees()
	    tooltip.set_markup("%+.4f, %+.4f" % p.get_degrees())
	    return True
	
	return False

    def save_center(self, lat, lon):
        """
        Save the longitude and lontitude in case we switch between maps.
        """
        config.set("geography.center-lat",lat)
        config.set("geography.center-lon",lon)

    def map_clicked(self, osm, event):
        _LOG.debug("map_clicked")
        lat,lon = self.osm.get_event_location(event).get_degrees()
        if event.button == 1:
            _LOG.debug("map_clicked btn 1")
            # do we click on a marker ?
            marker = self.is_there_a_marker_here(event, lat, lon)
        elif event.button == 2:
            _LOG.debug("map_clicked btn 2")
            self.osm.gps_add(lat, lon, heading=osmgpsmap.INVALID);
        elif event.button == 3:
            _LOG.debug("map_clicked btn 3")
            self.build_nav_menu(osm, event, lat, lon )
        else:
            _LOG.debug("map_clicked other")
            self.save_center(lat,lon)

    def is_there_a_marker_here(self, lat, lon):
        raise NotImplementedError

    def set_crosshair(self,active):
        """
        Show or hide the crosshair ?
        """
        _LOG.debug("set crosshair : %d" % active )
        if active:
            self.cross_map = osmgpsmap.GpsMapOsd( show_crosshair=True)
            self.osm.layer_add( self.cross_map )
            # The two following are to force the map to update
            self.osm.zoom_in()
            self.osm.zoom_out()
            #self.osm.map_scroll(0,0)
        else:
            self.osm.layer_remove(self.cross_map)
        pass
