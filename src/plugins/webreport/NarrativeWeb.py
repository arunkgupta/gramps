# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2007       Johan Gonqvist <johan.gronqvist@gmail.com>
# Copyright (C) 2007-2009  Gary Burton <gary.burton@zen.co.uk>
# Copyright (C) 2007-2009  Stephane Charette <stephanecharette@gmail.com>
# Copyright (C) 2008-2009  Brian G. Matherly
# Copyright (C) 2008       Jason M. Simanek <jason@bohemianalps.com>
# Copyright (C) 2008-2011  Rob G. Healey <robhealey1@gmail.com>	
# Copyright (C) 2010       Doug Blank <doug.blank@gmail.com>
# Copyright (C) 2010       Jakim Friant
# Copyright (C) 2010       Serge Noiraud
# Copyright (C) 2011       Tim G L Lyons
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

"""
Narrative Web Page generator.
"""
#------------------------------------------------
# python modules
#------------------------------------------------

from __future__ import print_function
from functools import partial
import gc
import os
import sys
import re
import copy
try:
    from hashlib import md5
except ImportError:
    from md5 import md5
import time, datetime
import locale
import shutil
import codecs
import tarfile
import tempfile
from cStringIO import StringIO
from textwrap import TextWrapper
from unicodedata import normalize
from collections import defaultdict
import re
from xml.sax.saxutils import escape

import operator
from decimal import Decimal, getcontext
getcontext().prec = 8

#------------------------------------------------
# Set up logging
#------------------------------------------------
import logging
log = logging.getLogger(".NarrativeWeb")

#------------------------------------------------
# GRAMPS module
#------------------------------------------------
from gen.ggettext import sgettext as _
import gen.lib
from gen.lib import UrlType, date, NoteType, EventRoleType
import const
import Sort
from gen.plug.menu import PersonOption, NumberOption, StringOption, \
                          BooleanOption, EnumeratedListOption, FilterOption, \
                          NoteOption, MediaOption, DestinationOption
from gen.plug.report import ( Report, Bibliography)
from gen.plug.report import utils as ReportUtils
from gen.plug.report import MenuReportOptions
                        
import Utils
import constfunc
import ThumbNails
import ImgManip
import gen.mime
from gen.display.name import displayer as _nd
from DateHandler import displayer as _dd
from gen.proxy import PrivateProxyDb, LivingProxyDb
from libhtmlconst import _CHARACTER_SETS, _CC, _COPY_OPTIONS

# import HTML Class from src/plugins/lib/libhtml.py
from libhtml import Html

# import styled notes from src/plugins/lib/libhtmlbackend.py
from libhtmlbackend import HtmlBackend, process_spaces

from libgedcom import make_gedcom_date
from PlaceUtils import conv_lat_lon
from gui.pluginmanager import GuiPluginManager

#------------------------------------------------
# constants
#------------------------------------------------
# javascript code for Google single Marker...
google_jsc = """
  var myLatLng = new google.maps.LatLng(%s, %s);

  function initialize() {
    var mapOptions = {
      scaleControl:    true,
      panControl:      true,
      backgroundColor: '#000000',
      draggable:       true,
      zoom:            10,
      center:          myLatLng,
      mapTypeId:       google.maps.MapTypeId.ROADMAP
    }
    var map = new google.maps.Map(document.getElementById("place_canvas"), mapOptions);

    var marker = new google.maps.Marker({
      position:  myLatLng,
      draggable: true,
      title:     "%s",
      map:       map
    });
  }"""

# javascript code for Google's FamilyLinks...
familylinks = """
  var tracelife = %s

  function initialize() {
    var myLatLng = new google.maps.LatLng(%s, %s);

    var mapOptions = {
      scaleControl:    true,
      panControl:      true,
      backgroundColor: '#000000',
      zoom:            %d,
      center:          myLatLng,
      mapTypeId:       google.maps.MapTypeId.ROADMAP
    }
    var map = new google.maps.Map(document.getElementById("map_canvas"), mapOptions);

    var flightPath = new google.maps.Polyline({
      path:          tracelife,
      strokeColor:   "#FF0000",
      strokeOpacity: 1.0,
      strokeWeight:  2
    });

   flightPath.setMap(map);
  }"""

# javascript for Google's Drop Markers...
dropmarkers = """
  var markers = [];
  var iterator = 0;

  var tracelife = %s
  var map;

  function initialize() {
    var mapOptions = {
      scaleControl: true,
      zoomControl:  true, 
      zoom:         %d,
      mapTypeId:    google.maps.MapTypeId.ROADMAP,
      center:       new google.maps.LatLng(0, 0)
    }
    map = new google.maps.Map(document.getElementById("map_canvas"), mapOptions);
  }

  function drop() {
    for (var i = 0; i < tracelife.length; i++) {
      setTimeout(function() {
        addMarker();
      }, i * 1000);
    }
  }

  function addMarker() {
    var location = tracelife[iterator];
    var myLatLng = new google.maps.LatLng(location[1], location[2]);

    markers.push(new google.maps.Marker({
      position:  myLatLng,
      map:       map,
      draggable: true,
      title:     location[0],
      animation: google.maps.Animation.DROP
    }));
    iterator++;
  }"""

# javascript for Google's Markers...
markers = """
  var tracelife = %s
  var map;

  function initialize() {
    var mapOptions = {
      scaleControl:    true,
      panControl:      true,
      backgroundColor: '#000000',
      zoom:            %d,
      center:          new google.maps.LatLng(0, 0),
      mapTypeId:       google.maps.MapTypeId.ROADMAP
    }
    map = new google.maps.Map(document.getElementById("map_canvas"), mapOptions);
    addMarkers();
  }

  function addMarkers() {
    var bounds = new google.maps.LatLngBounds();

    for (var i = 0; i < tracelife.length; i++) {
      var location = tracelife[i];
      var myLatLng = new google.maps.LatLng(location[1], location[2]);

      var marker = new google.maps.Marker({
        position:  myLatLng,
        draggable: true,
        title:     location[0],
        map:       map,
        zIndex:    location[3] 
      });
      bounds.extend(myLatLng);
      map.fitBounds(bounds);
    }
  }"""

canada_map = """
    var dm_wms = new OpenLayers.Layer.WMS(
      "Canadian Data",
      "http://www2.dmsolutions.ca/cgi-bin/mswms_gmap",
      {layers: "bathymetry,land_fn,park,drain_fn,drainage," +
         "prov_bound,fedlimit,rail,road,popplace",
         transparent: "true",
         format: "image/png"},
       {isBaseLayer: false});
     map.addLayers([wms, dm_wms]);
"""

# javascript code for OpenStreetMap single marker
openstreetmap_jsc = """
  OpenLayers.Lang.setCode("%s");

  function initialize(){
    var map = new OpenLayers.Map('place_canvas');

    var wms = new OpenLayers.Layer.WMS(
      "OpenLayers WMS",
      "http://vmap0.tiles.osgeo.org/wms/vmap0",
      {'layers':'basic'});
    map.addLayer(wms);

    map.setCenter(new OpenLayers.LonLat(0, 0), 0);

    var markers = new OpenLayers.Layer.Markers("Markers");
    map.addLayer(markers);

      marker = new OpenLayers.Marker(new OpenLayers.LonLat(%s, %s);
      markers.addMarker(marker); 
      map.addControl(new OpenLayers.Control.LayerSwitcher());
  }"""

# javascript for OpenStreetMap's markers...
osm_markers = """
  OpenLayers.Lang.setCode("%s");
  var map;

  var tracelife = %s

  function initialize(){
    map = new OpenLayers.Map('map_canvas');

    var wms = new OpenLayers.Layer.WMS(
      "OpenLayers WMS",
      "http://vmap0.tiles.osgeo.org/wms/vmap0",
      {'layers':'basic'});
    map.addLayer(wms);

    map.setCenter(new OpenLayers.LonLat(%s, %s), %d);

    var markers = new OpenLayers.Layer.Markers("Markers");
    map.addLayer(markers);

    addMarkers(markers, map);
  }

  function addMarkers(markers, map) {
    for (var i = 0; i < tracelife.length; i++) {
      var location = tracelife[i];

      marker = new OpenLayers.Marker(new OpenLayers.LonLat(location[0], location[1]));
      markers.addMarker(marker); 
      map.addControl(new OpenLayers.Control.LayerSwitcher());
    }
  }"""
# there is no need to add an ending "</script>",
# as it will be added automatically by libhtml()


# Translatable strings for variables within this plugin
# gettext carries a huge footprint with it.
AHEAD = _("Attributes")
BIRTH = _("Birth")
CITY = _("City")
COUNTY = _("County")
COUNTRY = _("Country")
DEATH = _("Death")
DHEAD = _("Date")
DESCRHEAD = _("Description")
_EVENT = _("Event")
GRAMPSID = _("Gramps&nbsp;ID")
LATITUDE = _("Latitude")
LOCALITY = _("Locality")
LONGITUDE = _("Longitude")
NHEAD = _("Notes")
PARENTS = _("Parents")
PARISH = _("Church Parish")
_PARTNER = _("Partner")
PHEAD = _("Place")
_PERSON = _("Person")
PHONE = _("Phone")
POSTAL = _("Postal Code")
SHEAD = _("Sources")
ST = _("Status")
STATE = _("State/ Province")
STREET = _("Street")
THEAD = _("Type")
TEMPLE = _("Temple")
VHEAD = _("Value")
ALT_LOCATIONS = _("Alternate Locations")
_UNKNOWN = _("Unknown")

# Events that are usually a family event
_EVENTMAP = set(
                [gen.lib.EventType.MARRIAGE, gen.lib.EventType.MARR_ALT, 
                 gen.lib.EventType.MARR_SETTL, gen.lib.EventType.MARR_LIC,
                 gen.lib.EventType.MARR_CONTR, gen.lib.EventType.MARR_BANNS,
                 gen.lib.EventType.ENGAGEMENT, gen.lib.EventType.DIVORCE,
                 gen.lib.EventType.DIV_FILING
                ]
              )
  
# define clear blank line for proper styling
fullclear = Html("div", class_ = "fullclear", inline = True)

# Names for stylesheets
_NARRATIVESCREEN = "narrative-screen.css"
_NARRATIVEPRINT = "narrative-print.css"

# variables for alphabet_navigation()
_KEYPERSON, _KEYPLACE, _KEYEVENT, _ALPHAEVENT = 0, 1, 2, 3

# Web page filename extensions
_WEB_EXT = ['.html', '.htm', '.shtml', '.php', '.php3', '.cgi']

_INCLUDE_LIVING_VALUE = 99 # Arbitrary number
_NAME_COL  = 3

_DEFAULT_MAX_IMG_WIDTH = 800   # resize images that are wider than this (settable in options)
_DEFAULT_MAX_IMG_HEIGHT = 600  # resize images that are taller than this (settable in options)
_WIDTH = 160
_HEIGHT = 64
_VGAP = 10
_HGAP = 30
_SHADOW = 5
_XOFFSET = 5
_WRONGMEDIAPATH = []

_NAME_STYLE_SHORT = 2
_NAME_STYLE_DEFAULT = 1
_NAME_STYLE_FIRST = 0
_NAME_STYLE_SPECIAL = None

wrapper = TextWrapper()
wrapper.break_log_words = True
wrapper.width = 20

PLUGMAN = GuiPluginManager.get_instance()
CSS = PLUGMAN.process_plugin_data('WEBSTUFF')


_html_dbl_quotes = re.compile(r'([^"]*) " ([^"]*) " (.*)', re.VERBOSE)
_html_sng_quotes = re.compile(r"([^']*) ' ([^']*) ' (.*)", re.VERBOSE)

# This command then defines the 'html_escape' option for escaping
# special characters for presentation in HTML based on the above list.
def html_escape(text):
    """Convert the text and replace some characters with a &# variant."""

    # First single characters, no quotes
    text = escape(text)

    # Deal with double quotes.
    m = _html_dbl_quotes.match(text)
    while m:
        text = "%s" "&#8220;" "%s" "&#8221;" "%s" % m.groups()
        m = _html_dbl_quotes.match(text)
    # Replace remaining double quotes.
    text = text.replace('"', '&#34;')

    # Deal with single quotes.
    text = text.replace("'s ", '&#8217;s ')
    m = _html_sng_quotes.match(text)
    while m:
        text = "%s" "&#8216;" "%s" "&#8217;" "%s" % m.groups()
        m = _html_sng_quotes.match(text)
    # Replace remaining single quotes.
    text = text.replace("'", '&#39;')

    return text

def name_to_md5(text):
    """This creates an MD5 hex string to be used as filename."""
    return md5(text).hexdigest()

def conf_priv(obj):
    if obj.get_privacy() != 0:
        return ' priv="%d"' % obj.get_privacy()
    else:
        return ''

def get_gendex_data(database, event_ref):
    """
    Given an event, return the date and place a strings
    """
    doe = "" # date of event
    poe = "" # place of event
    if event_ref:
        event = database.get_event_from_handle(event_ref.ref)
        if event:
            date = event.get_date_object()
            doe = format_date(date)
            if event.get_place_handle():
                place_handle = event.get_place_handle()
                if place_handle:
                    place = database.get_place_from_handle(place_handle)
                    if place:
                        location = place.get_main_location()
                        if location and not location.is_empty():
                            poe = ", ".join(l for l in
                                            [
                                                location.get_city().strip(),
                                                location.get_state().strip(),
                                                location.get_country().strip()
                                            ] if l)
    return doe, poe

def format_date(date):
    start = date.get_start_date()
    if start != gen.lib.Date.EMPTY:
        cal = date.get_calendar()
        mod = date.get_modifier()
        quality = date.get_quality()
        if mod == gen.lib.Date.MOD_SPAN:
            val = "FROM %s TO %s" % (
                make_gedcom_date(start, cal, mod, quality), 
                make_gedcom_date(date.get_stop_date(), cal, mod, quality))
        elif mod == gen.lib.Date.MOD_RANGE:
            val = "BET %s AND %s" % (
                make_gedcom_date(start, cal, mod, quality), 
                make_gedcom_date(date.get_stop_date(), cal, mod, quality))
        else:
            val = make_gedcom_date(start, cal, mod, quality)
        return val
    return ""

def copy_thumbnail(report, handle, photo, region=None):
    """
    Given a handle (and optional region) make (if needed) an
    up-to-date cache of a thumbnail, and call report.copy_file
    to copy the cached thumbnail to the website.
    Return the new path to the image.
    """
    to_dir = report.build_path('thumb', handle)
    to_path = os.path.join(to_dir, handle) + (
        ('%d,%d-%d,%d.png' % region) if region else '.png'
        )
    
    if photo.get_mime_type():
        from_path = ThumbNails.get_thumbnail_path(Utils.media_path_full(
                                                  report.database,
                                                  photo.get_path()),
                                                  photo.get_mime_type(),
                                                  region)
        if not os.path.isfile(from_path):
            from_path = CSS["Document"]["filename"]
    else:
        from_path = CSS["Document"]["filename"]
    report.copy_file(from_path, to_path)
    return to_path

#################################################
#
#    Manages all the functions, variables, and everything needed 
#    for all of the classes contained within this plugin
#################################################
class BasePage(object):
    def __init__(self, report, title, gid = None):
        self.up = False
        # class to do conversion of styled notes to html markup
        self._backend = HtmlBackend()
        self._backend.build_link = report.build_link

        self.report = report
        self.title_str = title
        self.gid = gid
        self.src_list = {}

        self.page_title = ""

        self.author = Utils.get_researcher().get_name()
        if self.author:
            self.author = self.author.replace(',,,', '')

        # TODO. All of these attributes are not necessary, because we have
        # also the options in self.options.  Besides, we need to check which
        # are still required.
        self.html_dir = report.options['target']
        self.ext = report.options['ext']
        self.noid = report.options['nogid']
        self.linkhome = report.options['linkhome']
        self.create_media = report.options['gallery']
        self.create_thumbs_only = report.options['create_thumbs_only']
        self.inc_families = report.options['inc_families']
        self.inc_events = report.options['inc_events']

    def display_relationships(self, individual, ppl_handle_list, place_lat_long):
        """
        Displays a person's relationships ...

        @param: family_handle_list -- families in this report database
        @param: ppl_handle_list -- people in this report database
        @param: place_lat_long -- for use in Family Map Pages
        """
        birthorder = self.report.options["birthorder"]

        family_list = individual.get_family_handle_list()
        if not family_list:
            return None

        with Html("div", class_ ="subsection", id ="families") as section:
            section += Html("h4", _("Families"), inline =True)

            table_class = "infolist"
            if len(family_list) > 1:
                table_class += " fixed_subtables"
            with Html("table", class_ = table_class) as table:
                section += table

                for fhandle in family_list:
                    family = self.dbase_.get_family_from_handle(fhandle)
                    if family:
                        self.display_spouse(family, table, ppl_handle_list, place_lat_long)

                        childlist = family.get_child_ref_list()
                        if childlist:
                            trow = Html("tr") + (
                                Html("td", "&nbsp;", class_ = "ColumnType", inline = True),
                                Html("td", _("Children"), class_ = "ColumnAttribute", inline = True)
                            )
                            table += trow

                            tcell = Html("td", class_ = "ColumnValue")
                            trow += tcell

                            ordered = Html("ol")
                            tcell += ordered 
                            childlist = [child_ref.ref for child_ref in childlist]

                            # add individual's children event places to family map...
                            if self.familymappages:
                                for handle in childlist:
                                    child = self.dbase_.get_person_from_handle(handle)
                                    if child:
                                        self._get_event_place(child, ppl_handle_list, place_lat_long)

                            children = add_birthdate(self.dbase_, childlist)
                            if birthorder:
                                children = sorted(children) 

                            ordered.extend(
                                self.display_child_link(chandle, ppl_handle_list)
                                    for birth_date, chandle in children
                            )

                        # family LDS ordinance list
                        family_lds_ordinance_list = family.get_lds_ord_list()
                        if family_lds_ordinance_list:
                            trow = Html("tr") + (
                                Html("td", "&nbsp;", class_ = "ColumnType", inline = True),
                                Html("td", _("LDS Ordinance"), class_ = "ColumnAttribute", inline = True),
                                Html("td", self.dump_ordinance(family, "Family"), class_ = "ColumnValue")
                            )
                            table += trow

                        # Family Attribute list
                        family_attribute_list = family.get_attribute_list()
                        if family_attribute_list:
                            trow = Html("tr") + (
                                Html("td", "&nbsp;", class_ ="ColumnType", inline =True),
                                Html("td", _("Attributes"), class_ ="ColumnAttribute", inline =True)
                            )
                            table += trow

                            tcell = Html("td", class_ = "ColumnValue")
                            trow += tcell

                            # we do not need the section variable for this instance of Attributes...
                            dummy, attrtable = self.display_attribute_header()
                            tcell += attrtable
                            self.display_attr_list(family_attribute_list, attrtable)
        return section

    def complete_people(self, tcell, first_person, handle_list, ppl_handle_list, up =True):
        """
        completes the person column for classes EventListPage and EventPage

        @param: tcell -- table cell from its caller
        @param: first_person -- Not used any more, done via css
        @param: handle_list -- handle list from the backlink of the event_handle
        """
        for (classname, handle) in handle_list:

            # personal event
            if classname == "Person":
                _obj = self.dbase_.get_person_from_handle(handle)
                if _obj:
                    use_link = check_person_database(handle, ppl_handle_list)
                    if use_link:
                        url = self.report.build_url_fname_html(handle, "ppl", up) 
                        tcell += Html("span", self.person_link(url, _obj,
                            _NAME_STYLE_DEFAULT, gid=_obj.get_gramps_id()), class_ ="person", inline =True)
                    else:
                        tcell += Html("span", self.get_name(_obj), class_="person",
                                      inline=True)

            # family event
            else:
                _obj = self.dbase_.get_family_from_handle(handle)
                if _obj:

                    # husband and spouse in this example, are called father and mother
                    husband, spouse = [False]*2
                    husband_handle = _obj.get_father_handle()
                    if husband_handle:
                        husband = self.dbase_.get_person_from_handle(husband_handle)
                    spouse_handle = _obj.get_mother_handle()
                    if spouse_handle:
                        spouse = self.dbase_.get_person_from_handle(spouse_handle)
                    if husband:
                        use_link = check_person_database(husband_handle, ppl_handle_list)
                        if use_link:
                            url = self.report.build_url_fname_html(husband_handle, "ppl", up)
                            hlink = self.person_link(url, husband, _NAME_STYLE_DEFAULT, gid = husband.get_gramps_id())
                        else:
                            hlink = self.get_name(husband)

                    if spouse:
                        use_link = check_person_database(spouse_handle, ppl_handle_list)
                        if use_link:
                            url = self.report.build_url_fname_html(spouse_handle, "ppl", up)
                            slink = self.person_link(url, spouse, _NAME_STYLE_DEFAULT, gid = spouse.get_gramps_id())
                        else:
                            slink = self.get_name(spouse)

                    if spouse and husband:
                        tcell += Html("span", hlink, class_ = "father", inline =True)
                        tcell += Html("span", slink, class_ = "mother", inline =True)
                    elif spouse:
                        tcell += Html("span", slink, class_ = "mother", inline =True)
                    elif husband:
                        tcell += Html("span", hlink, class_ = "father", inline =True)
        return tcell

    def dump_attribute(self, attr):
        """
        dump attribute for object presented in display_attr_list()

        @param: attr = attribute object
        """
        trow = Html("tr")

        trow.extend(
            Html("td", data or "&nbsp;", class_ = colclass,
                inline = True if (colclass == "Type" or "Sources") else False)
                for (data, colclass) in [
                    (str(attr.get_type()),                              "ColumnType"),
                    (attr.get_value(),                                  "ColumnValue"),
                    (self.dump_notes(attr.get_note_list()),             "ColumnNotes"),
                    (self.get_citation_links(attr.get_citation_list()), "ColumnSources")
                ]
        )  
        return trow

    def get_citation_links(self, citation_handle_list):
        """
        get citation link from the citation handle list

        @param: citation_handle_list = list of gen/lib/Citation
        """
        lnk = (self.report.cur_fname, self.page_title, self.gid)
        text = ""
        for citation_handle in citation_handle_list:
            citation = self.report.database.get_citation_from_handle(
                                                citation_handle)
            if citation:
            
                # Add the source information to src_list for use when displaying the
                # Sources page
                source_handle = citation.get_reference_handle()
                if source_handle in self.src_list:
                    if lnk not in self.src_list[source_handle]:
                        self.src_list[source_handle].append(lnk)
                else:
                    self.src_list[source_handle] = [lnk]
                
                # Add the citation information to the bibliography, and construct
                # the citation reference text
                index, key = self.bibli.add_reference(citation)
                id_ = "%d%s" % (index+1, key)
                text += ' [<a href="#sref%s">%s</a>]' % (id_, id_)
        return text

    def get_note_format(self, note, link_prefix_up):
        """
        will get the note from the database, and will return either the 
        styled text or plain note 
        """
        self.report.link_prefix_up = link_prefix_up

        # retrieve the body of the note
        note_text = note.get()
 
        # styled notes
        htmlnotetext = self.styled_note(note.get_styledtext(),
                                        note.get_format(), contains_html = 
                                        note.get_type() == NoteType.HTML_CODE)
        text = htmlnotetext or Html("p", note_text)

        # return text of the note to its callers
        return text

    def styled_note(self, styledtext, format, contains_html=False):
        """
        styledtext : assumed a StyledText object to write
        format : = 0 : Flowed, = 1 : Preformatted
        style_name : name of the style to use for default presentation
        """
        text = str(styledtext)

        if not text:
            return ''

        s_tags = styledtext.get_tags()
        markuptext = self._backend.add_markup_from_styled(text, s_tags,
                                                         split='\n')
        htmllist = Html("div", class_="grampsstylednote")
        if contains_html:
            htmllist += text
        else:
            linelist = []
            linenb = 1
            for line in markuptext.split('\n'):
                [line, sigcount] = process_spaces(line, format)
                if sigcount == 0:
                    # The rendering of an empty paragraph '<p></p>'
                    # is undefined so we use a non-breaking space
                    if linenb == 1:
                        linelist.append('&nbsp;')
                    htmllist.extend(Html('p') + linelist)
                    linelist = []
                    linenb = 1
                else:
                    if linenb > 1:
                        linelist[-1] += '<br />'
                    linelist.append(line)
                    linenb += 1
            if linenb > 1:
                htmllist.extend(Html('p') + linelist)
            # if the last line was blank, then as well as outputting the previous para,
            # which we have just done,
            # we also output a new blank para
            if sigcount == 0:
                linelist = ["&nbsp;"]
                htmllist.extend(Html('p') + linelist)
        return htmllist

    def dump_notes(self, notelist):
        """
        dump out of list of notes with very little elements of its own

        @param: notelist -- list of notes
        """
        if not notelist:
            return Html("div")

        # begin unordered list
        notesection = Html("div")
        for notehandle in notelist:
            this_note = self.report.database.get_note_from_handle(notehandle)
            if this_note is not None:
                notesection.extend(Html("i", str(this_note.type), class_="NoteType"))
                notesection.extend(self.get_note_format(this_note, True))
        return notesection

    def event_header_row(self):
        """
        creates the event header row for all events
        """
        trow = Html("tr")
        trow.extend(
            Html("th", trans, class_ =colclass, inline =True)
            for trans, colclass in  [
                (("Event"),        "ColumnEvent"),
                (_("Date"),        "ColumnDate"),
                (_("Pkace"),       "ColumnPlace"),
                (_("Notes"),       "ColumnNotes"),
                (_("Sources"),     "ColumnSources") ]
        )
        return trow

    def display_event_row(self, event, event_ref, place_lat_long, up, hyperlink, omit):
        """
        display the event row for IndividualPage

        @param: evt = Event object from report database
        @param: evt_ref = event reference
        @param: place_lat_long -- for use in Family Map Pages
        @param: up = add [".."] * 3 for subdirectories or not
        @param: hyperlink = add a hyperlink or not
        @params: omit = role to be omitted in output
        """
        event_gid = event.get_gramps_id()

        # check to see if place is already in self.place_list?
        lnk = (self.report.cur_fname, self.page_title, self.gid)
        place_handle = event.get_place_handle()
        if place_handle:
            if place_handle in self.place_list:
                if lnk not in self.place_list[place_handle]:
                    self.place_list[place_handle].append(lnk)
            else:
                self.place_list[place_handle] = [lnk]

            place = self.dbase_.get_place_from_handle(place_handle)
            if place:
                self.append_to_place_lat_long(place, event, place_lat_long)

        # begin event table row
        trow = Html("tr")

        # get event type and hyperlink to it or not?
        etype = str(event.get_type())
        
        event_role = event_ref.get_role()
        if not event_role == omit:
            etype += " (%s)" % event_role
        event_hyper = self.event_link(etype, event_ref.ref, event_gid, up) if hyperlink else etype
        trow += Html("td", event_hyper, class_ = "ColumnEvent")

        # get event data
        event_data = self.get_event_data(event, event_ref, up)

        trow.extend(
            Html("td", data or "&nbsp;", class_ =colclass,
                inline = (not data or colclass == "ColumnDate"))
            for (label, colclass, data) in event_data
        )

        # get event notes
        notelist = event.get_note_list()
        notelist.extend(event_ref.get_note_list())
        htmllist = self.dump_notes(notelist)
  
        # if the event or event reference has an attribute attached to it,
        # get the text and format it correctly?
        attrlist = event.get_attribute_list()
        attrlist.extend(event_ref.get_attribute_list())
        for attr in attrlist:
            htmllist.extend(Html(
                "p",
                _("%(type)s: %(value)s") % {
                'type'     : Html("b", attr.get_type()),
                'value'    : attr.get_value() } ))

            #also output notes attached to the attributes
            notelist = attr.get_note_list()
            if notelist:
                htmllist.extend(self.dump_notes(notelist))

        trow += Html("td", htmllist, class_ = "ColumnNotes")

        # get event source references
        srcrefs = self.get_citation_links(event.get_citation_list()) or "&nbsp;"
        trow += Html("td", srcrefs, class_ = "ColumnSources")

        # return events table row to its callers
        return trow

    def append_to_place_lat_long(self, place, event, place_lat_long):
        """
        Create a list of places with coordinates.
        """
        place_handle = place.get_handle()

        # 0 = latitude, 1 = longitude, 2 - placetitle,
        # 3 = place handle, 4 = event date, 5 = event type
        found = any(data[3] == place_handle for data in place_lat_long)
        if not found:
            placetitle = place.get_title()
            latitude  =  place.get_latitude()
            longitude = place.get_longitude()
            if (latitude and longitude):
                latitude, longitude = conv_lat_lon(latitude, longitude, "D.D8")
                if latitude is not None:
                    event_date = event.get_date_object()
                    etype = event.get_type()

                    # only allow Birth, Death, Census, Marriage, and Divorce events...
                    if etype in [gen.lib.EventType.BIRTH, gen.lib.EventType.DEATH, gen.lib.EventType.CENSUS,
                                 gen.lib.EventType.MARRIAGE, gen.lib.EventType.DIVORCE]:
                        place_lat_long.append([latitude, longitude, placetitle, place_handle, event_date, etype])

    def _get_event_place(self, person, ppl_handle_list, place_lat_long):
        """
        retrieve from a a person their events, and places for family map

        @param: person - person object from the database
        """
        if not person:
            return

        # check to see if this person is in the report database?
        use_link = check_person_database(person.get_handle(), ppl_handle_list)
        if use_link:
            evt_ref_list = person.get_event_ref_list()
            if evt_ref_list:
                for evt_ref in evt_ref_list:
                    event = self.dbase_.get_event_from_handle(evt_ref.ref)
                    if event:
                        place_handle = event.get_place_handle()
                        if place_handle:

                            place = self.dbase_.get_place_from_handle(place_handle)
                            if place:
                                self.append_to_place_lat_long(place, event, place_lat_long)

    def family_link(self, handle, name, gid = None, up = False):
        """
        create the url and link for FamilyPage
        """
        name = html_escape(name)
        url = self.report.build_url_fname_html(handle, "fam", up = up)

        # begin hyperlink
        hyper = Html("a", name, href = url, title = name)

        # attach gramps_id to hyperlink
        if not self.noid and gid:
            hyper += Html("span", " [%s]" % gid, class_ = "grampsid", inline =True)

        return hyper

    def event_link(self, eventtype, handle, gid = None, up = False):
        """
        creates a hyperlink for an event based on its type
        """
        if not self.inc_events:
            return eventtype

        url = self.report.build_url_fname_html(handle, "evt", up)
        hyper = Html("a", eventtype, href = url, title = eventtype)

        if not self.noid and gid:
            hyper += Html("span", " [%s]" % gid, class_ = "grampsid", inline = True)

        return hyper

    def format_family_events(self, event_ref_list, place_lat_long):
        """
        displays the event row for events such as marriage and divorce

        @param: eventlist - list of events
        """
        with Html("table", class_ = "infolist eventlist") as table:
            thead = Html("thead")
            table += thead

            # attach event header row
            thead += self.event_header_row()

            # begin table body
            tbody = Html("tbody")
            table += tbody 
   
            for evt_ref in event_ref_list:
                event = self.dbase_.get_event_from_handle(evt_ref.ref)

                # add event body row
                tbody += self.display_event_row(event, evt_ref, place_lat_long, 
                                            up =True, hyperlink =True,
                                            omit =EventRoleType.FAMILY)
        return table

    def get_event_data(self, evt, evt_ref, up, gid =None):
        """
        retrieve event data from event and evt_ref

        @param: evt = event from database
        @param: evt_ref = eent reference
        @param: up = either True or False; add subdirs or not?
        """
        place = None
        place_handle = evt.get_place_handle()
        if place_handle:
            place = self.dbase_.get_place_from_handle(place_handle)

        place_hyper = None
        if place: 
            place_name = ReportUtils.place_name(self.dbase_, place_handle)
            place_hyper = self.place_link(place_handle, place_name, up = up)

        # wrap it all up and return to its callers
        # position 0 = translatable label, position 1 = column class
        # position 2 = data
        return [
               (_("Date"),  "ColumnDate",  _dd.display(evt.get_date_object()) ),
               (_("Place"), "ColumnPlace", place_hyper) ]

    def dump_ordinance(self, ldsobj, LDSSealedType):
        """
        will dump the LDS Ordinance information for either
        a person or a family ...

        @param: ldsobj -- either person or family
        @param: LDSSealedType = either Sealed to Family or Spouse
        """
        objectldsord = ldsobj.get_lds_ord_list()
        if not objectldsord:
            return None

        # begin LDS ordinance table and table head
        with Html("table", class_ = "infolist ldsordlist") as table:
            thead = Html("thead")
            table += thead

            # begin HTML row
            trow = Html("tr")
            thead += trow

            trow.extend(
                Html("th", label, class_ = colclass, inline = True)
                    for (label, colclass) in [
                        [_("Type"),   "ColumnLDSType"],
                        [_("Date"),   "ColumnDate"],
                        [_("Temple"),  "ColumnLDSTemple"],
                        [_("Place"),   "ColumnLDSPlace"],
                        [_("Status"),  "ColumnLDSStatus"],
                        [_("Sources"), "ColumnLDSSources"]
                    ]
            )

            # start table body
            tbody = Html("tbody")
            table += tbody

            for ord in objectldsord:
                place_hyper = "&nbsp;"
                place_handle = ord.get_place_handle()
                if place_handle:
                    place = self.dbase_.get_place_from_handle(place_handle)
                    if place:
                        place_hyper = self.place_link(place_handle, place.get_title(),
                            place.get_gramps_id(), True)

                # begin ordinance rows
                trow = Html("tr")

                trow.extend(
                    Html("td", value or "&nbsp;", class_ = colclass,
                        inline = (not value or colclass == "ColumnDate"))
                        for (value, colclass) in [
                            (ord.type2xml(),                                   "ColumnType"),
                            (_dd.display(ord.get_date_object()),               "ColumnDate"),
                            (ord.get_temple(),                                 "ColumnLDSTemple"),
                            (place_hyper,                                      "ColumnLDSPlace"),
                            (ord.get_status(),                                 "ColumnLDSStatus"),
                            (self.get_citation_links(ord.get_citation_list()), "ColumnSources")
                        ]
                )
                tbody += trow
        return table

    def write_data_map(self, data_map):
        """
        writes out the data map for the different objects
        """
        if not data_map:
            return None

        # begin data map division and section title...
        with Html("div", class_ = "subsection", id = "data_map") as datamapdiv:
            datamapdiv += Html("h4", _("Data Map"), inline = True)

            with Html("table", class_ = "infolist") as table:
                datamapdiv += table

                thead = Html("thead")
                table += thead

                trow = Html("tr") + (
                    Html("th", _("Key"), class_ = "ColumnAttribute", inline = True),
                    Html("th", _("Value"), class_ = "ColumnValue", inline = True)
                )
                thead += trow

                tbody = Html("tbody")
                table += tbody

                for dataline in data_map:
                    trow = Html("tr") + (
                        Html("td", dataline.key(), class_ = "ColumnAttribute", inline = rue),
                        Html("td", dataline.value(), class_ = "ColumnValue", inline = True)
                    )
                    tbody += trow
        return datamapdiv

    def source_link(self, source, cindex = None, up = False):
        """
        creates a link to the source object

        @param: source -- source object from database
        @param: cindex - count index
        @param: up - rather to add back directories or not?
        """

        url = self.report.build_url_fname_html(source.get_handle(), "src", up)
        gid = source.get_gramps_id()
        title = html_escape(source.get_title())

        # begin hyperlink
        hyper = Html("a", title, 
                     href =url, 
                     title =_("Source Reference: %s") % title, 
                     inline =True)

        # if not None, add name reference to hyperlink element
        if cindex:
            hyper.attr += ' name ="sref%d"' % cindex

        # add GRAMPS ID
        if not self.noid and gid:
            hyper += Html("span", ' [%s]' % gid, class_ = "grampsid", inline = True)

        # return hyperlink to its callers
        return hyper

    def display_addr_list(self, addrlist, showsrc):
        """
        display a person's or repository's addresses ...

        @param: addrlist -- a list of address handles
        @param: showsrc -- True = show sources
                           False = do not show sources
                           None = djpe
        """

        if not addrlist:
            return None

        # begin addresses division and title
        with Html("div", class_ = "subsection", id = "Addresses") as section:
            section += Html("h4", _("Addresses"), inline = True)

            # write out addresses()
            section += self.dump_addresses(addrlist, showsrc)

        # return address division to its caller
        return section

    def dump_addresses(self, addrlist, showsrc):
        """
        will display an object's addresses, url list, note list, 
        and source references.

        @param: addrlist = either person or repository address list
        @param: showsrc = True  --  person and their sources
                          False -- repository with no sources
                          None  -- Address Book address with sources
        """
        if not addrlist:
            return None

        # begin summaryarea division
        with Html("div", id = "AddressTable") as summaryarea: 

            # begin address table
            with Html("table") as table:
                summaryarea += table

                # get table class based on showsrc
                if showsrc == True:
                    table.attr = 'class = "infolist addrlist"'
                elif showsrc == False: 
                    table.attr = 'class = "infolist repolist"'
                else:
                    table.attr = 'class = "infolist addressbook"' 

                # begin table head
                thead = Html("thead")
                table += thead

                trow = Html("tr")
                thead += trow

                addr_header = [
                      [DHEAD,         "Date"],
                      [STREET,        "StreetAddress"], 
                      [_("Locality"), "Locality"],   
                      [CITY,          "City"],
                      [STATE,         "State"],
                      [COUNTY,        "County"],
                      [POSTAL,        "Postalcode"],
                      [COUNTRY,       "Cntry"],
                      [PHONE,         "Phone"] ]

                # True, False, or None ** see docstring for explanation
                if showsrc in [True, None]:
                    addr_header.append([SHEAD,      "Sources"])

                trow.extend(
                    Html("th", label, class_ = "Colummn" + colclass, inline = True)
                    for (label, colclass) in addr_header
                )

                # begin table body
                tbody = Html("tbody")
                table += tbody

                # get address list from an object; either repository or person
                for address in addrlist:

                    trow = Html("tr")
                    tbody += trow

                    addr_data_row = [
                        (_dd.display(address.get_date_object()), "ColumnDate"),
                        (address.get_street(),                   "ColumnStreetAddress"),
                        (address.get_locality(),                 "ColumnLocality"),
                        (address.get_city(),                     "ColumnCity"),
                        (address.get_state(),                    "ColumnState"),
                        (address.get_county(),                   "ColumnCounty"),
                        (address.get_postal_code(),              "ColumnPostalCode"),
                        (address.get_country(),                  "ColumnCntry"),
                        (address.get_phone(),                    "ColumnPhone")
                    ]

                    # get source citation list
                    if showsrc in [True, None]:
                        addr_data_row.append([self.get_citation_links(address.get_citation_list()), "ColumnSources"])

                    trow.extend(
                        Html("td", value or "&nbsp;", class_= colclass, inline = True)
                            for (value, colclass) in addr_data_row
                    )
                    
                    # address: notelist
                    if showsrc is not None:
                        notelist = self.display_note_list(address.get_note_list())
                        if notelist is not None:
                            summaryarea += notelist
        return summaryarea

    def addressbook_link(self, person_handle, up = False):
        """
        creates a hyperlink for an address book link based on person's handle

        @param: person_handle = person's handle from the database
        #param: up = rather to add subdirs or not?
        """

        url = self.report.build_url_fname_html(person_handle, "addr", up)
        person = self.report.database.get_person_from_handle(person_handle)
        person_name = self.get_name(person)

        # return addressbook hyperlink to its caller
        return Html("a", person_name, href = url, title = html_escape(person_name))

    def get_copyright_license(self, copyright, up = False):
        """
        will return either the text or image of the copyright license
        """

        text = ''
        if copyright == 0:
            if self.author:
                year = date.Today().get_year()
                text = '&copy; %(year)d %(person)s' % {
                    'person' : self.author,
                    'year' : year}
        elif 0 < copyright < len(_CC):
            # Note. This is a URL
            fname = "/".join(["images", "somerights20.gif"])
            url = self.report.build_url_fname(fname, None, up = False)
            text = _CC[copyright] % {'gif_fname' : url}

        # return text or image to its callers
        return text

    def get_name(self, person, maiden_name = None):
        """ I5118

        Return person's name, unless maiden_name given, unless married_name 
        listed. 

        @param: person -- person object from database
        @param: maiden_name -- Female's family surname
        """

        # get name format for displaying names
        name_format = self.report.options['name_format']

        # Get all of a person's names
        primary_name = person.get_primary_name()
        married_name = None
        names = [primary_name] + person.get_alternate_names()
        for name in names:
            if int(name.get_type()) == gen.lib.NameType.MARRIED:
                married_name = name
                break # use first

        # Now, decide which to use:
        if maiden_name is not None:
            if married_name is not None:
                name = gen.lib.Name(married_name)
            else:
                name = gen.lib.Name(primary_name)
                surname_obj = name.get_primary_surname()
                surname_obj.set_surname(maiden_name)
        else:
            name = gen.lib.Name(primary_name)
        name.set_display_as(name_format)
        return _nd.display_name(name)

    def display_attribute_header(self):
        """
        display the attribute section and its table header
        """
        # begin attributes division and section title
        with Html("div", class_ = "subsection", id ="attributes") as section:
            section += Html("h4", _("Attributes"),  inline =True)

            # begin attributes table
            with Html("table", class_ = "infolist attrlist") as attrtable:
                section += attrtable

                thead = Html("thead")
                attrtable += thead

                trow = Html("tr")
                thead += trow

                trow.extend(
                    Html("th", label, class_ =colclass, inline = True)
                    for (label, colclass) in [
                        (_("Type"),    "ColumnType"),
                        (_("Value"),   "ColumnValue"),
                        (_("Notes"),   "ColumnNotes"),
                        (_("Sources"), "ColumnSources") ]
                )
        return section, attrtable

    def display_attr_list(self, attrlist, attrtable):
        """
        will display a list of attributes

        @param: attrlist -- a list of attributes
        @param: attrtable -- the table element that is being added to
        """
        tbody = Html("tbody")
        attrtable += tbody

        tbody.extend(
            self.dump_attribute(attr) for attr in attrlist
        )

    def write_footer(self):
        """
        Will create and display the footer section of each page...

        @param: bottom -- whether to specify location of footer section or not?
        """

        # begin footer division
        with Html("div", id = "footer") as footer:

            footer_note = self.report.options['footernote']
            if footer_note:
                note = self.get_note_format(
                    self.report.database.get_note_from_gramps_id(footer_note),
                    False
                    )
                user_footer = Html("div", id = 'user_footer')
                footer += user_footer
 
                # attach note
                user_footer += note

            msg = _('Generated by <a href = "%(homepage)s">'
                    'Gramps</a> %(version)s on %(date)s') % {
                'date': _dd.display(date.Today()), 
                'homepage' : const.URL_HOMEPAGE,
                'version': const.VERSION}

            # optional "link-home" feature; see bug report #2736
            if self.report.options['linkhome']:
                center_person = self.report.database.get_person_from_gramps_id(self.report.options['pid'])
                if center_person and center_person.handle in self.report.person_handles:
                    center_person_url = self.report.build_url_fname_html(
                        center_person.handle, "ppl", self.up)

                    person_name = self.get_name(center_person)
                    msg += _('<br />Created for <a href = "%s">%s</a>') % (
                                center_person_url, person_name)

            # creation author
            footer += Html("p", msg, id = 'createdate')

            # get copyright license for all pages
            copy_nr = self.report.copyright

            text = ''
            if copy_nr == 0:
                if self.author:
                    year = date.Today().get_year()
                    text = '&copy; %(year)d %(person)s' % {
                               'person' : self.author,
                               'year' : year}
            elif copy_nr < len(_CC):
                # Note. This is a URL
                fname = "/".join(["images", "somerights20.gif"])
                url = self.report.build_url_fname(fname, None, self.up)
                text = _CC[copy_nr] % {'gif_fname' : url}
            footer += Html("p", text, id = 'copyright')

        # return footer to its callers
        return footer

    def write_header(self, title):
        """
        Note. 'title' is used as currentsection in the navigation links and
        as part of the header title.
        """

        # Header constants
        xmllang = Utils.xml_lang()
        _META1 = 'name ="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=1"'
        _META2 = 'name ="apple-mobile-web-app-capable" content="yes"'
        _META3 = 'name="generator" content="%s %s %s"' % (
                    const.PROGRAM_NAME, const.VERSION, const.URL_HOMEPAGE)
        _META4 = 'name="author" content="%s"' % self.author

        # begin each html page...
        page, head, body = Html.page('%s - %s' % 
                                    (html_escape(self.title_str.strip()), 
                                     html_escape(title)),
                                    self.report.encoding, xmllang)

        # temporary fix for .php parsing error
        if self.ext in [".php", ".php3", ".cgi"]:
            del page[0]

        # create additional meta tags
        meta = Html("meta", attr = _META1) + (
                Html("meta", attr = _META2, indent = False),
                Html("meta", attr = _META3, indent =False),
                Html("meta", attr = _META4, indent = False)
        )

        # Link to _NARRATIVESCREEN  stylesheet
        fname = "/".join(["styles", _NARRATIVESCREEN])
        url2 = self.report.build_url_fname(fname, None, self.up)

        # Link to _NARRATIVEPRINT stylesheet
        fname = "/".join(["styles", _NARRATIVEPRINT])
        url3 = self.report.build_url_fname(fname, None, self.up)

        # Link to GRAMPS favicon
        fname = "/".join(['images', 'favicon2.ico'])
        url4 = self.report.build_url_image("favicon2.ico", "images", self.up)

        # create stylesheet and favicon links
        links = Html("link", href = url4, type = "image/x-icon", rel = "shortcut icon") + (
             Html("link", href = url2, type = "text/css", media = "screen", rel = "stylesheet", indent = False),
             Html("link", href = url3, type = "text/css", media = 'print',  rel = "stylesheet", indent = False)
             )

        # Link to Navigation Menus stylesheet
        if CSS[self.report.css]["navigation"]: 
            fname = "/".join(["styles", "narrative-menus.css"])
            url = self.report.build_url_fname(fname, None, self.up)
            links += Html("link", href = url, type = "text/css", media = "screen", rel = "stylesheet", indent = False)

        # add additional meta and link tags
        head += meta
        head += links

        # begin header section
        headerdiv = (Html("div", id = 'header') +
            Html("h1", html_escape(self.title_str), id = "SiteTitle", inline = True)
            )
        body += headerdiv

        header_note = self.report.options['headernote']
        if header_note:
            note = self.get_note_format(
                self.report.database.get_note_from_gramps_id(header_note),
                False
                )
            user_header = Html("div", id = 'user_header')
            headerdiv += user_header  
 
            # attach note
            user_header += note

        # Begin Navigation Menu
        body += self.display_nav_links(title)

        # return to its caller, page and body
        return page, head, body

    def display_nav_links(self, currentsection):
        """
        Creates the navigation menu

        @param: currentsection = which menu item are you on
        """
        # include repositories or not?
        inc_repos = True   
        if (not self.report.inc_repository or
            not len(self.report.database.get_repository_handles()) ):
                inc_repos = False

        # create media pages...
        _create_media_link = False
        if self.create_media:
            _create_media_link = True
            if self.create_thumbs_only:
                _create_media_link = False 

        # determine which menu items will be available?
        navs = [
            (self.report.index_fname,   _("Html|Home"),     self.report.use_home),
            (self.report.intro_fname,    _("Introduction"), self.report.use_intro),
            ('individuals',             _("Individuals"),   True),
            (self.report.surname_fname, _("Surnames"),      True),
            ('families',                _("Families"),      self.report.inc_families),
            ('places',                  _("Places"),        True),
            ('events',                  _("Events"),        self.report.inc_events), 
            ('media',                   _("Media"),         _create_media_link),
            ('thumbnails',              _("Thumbnails"),    True),
            ('sources',                 _("Sources"),       True),
            ('repositories',            _("Repositories"),  inc_repos),
            ("addressbook",             _("Address Book"),  self.report.inc_addressbook),
            ('download',                _("Download"),      self.report.inc_download),
            ('contact',                 _("Contact"),       self.report.use_contact)
        ]

        # Remove menu sections if they are not being created?
        navs = ((u, n) for u, n, c in navs if c)
        menu_items = [[url, text] for url, text in navs]

        number_items = len(menu_items)
        num_cols = 11
        num_rows = (number_items // num_cols) + 1

        with Html("div", id ="nav") as navigation:
            
            index = 0
            for rows in range(num_rows):
                unordered = Html("ul")
                navigation += unordered

                cols = 0
                while (cols != num_cols and index < number_items):
                    url_fname, nav_text = menu_items[index]

                    if not _has_webpage_extension(url_fname):
                        url_fname += self.ext

                    url = self.report.build_url_fname(url_fname, None, self.up)

                    # Define 'currentsection' to correctly set navlink item CSS id
                    # 'CurrentSection' for Navigation styling.
                    # Use 'self.report.cur_fname' to determine 'CurrentSection' for individual
                    # elements for Navigation styling.

                    # Figure out if we need <li class="CurrentSection"> of just <li>
                    cs = False
                    if nav_text == currentsection:
                        cs = True
                    elif nav_text == _("Surnames"):
                        if "srn" in self.report.cur_fname:
                            cs = True
                        elif _("Surnames") in currentsection:
                            cs = True
                    elif nav_text == _("Individuals"):
                        if "ppl" in self.report.cur_fname:
                            cs = True
                    elif nav_text == _("Families"):
                        if "fam" in self.report.cur_fname:
                            cs = True
                    elif nav_text == _("Sources"):
                        if "src" in self.report.cur_fname:
                            cs = True
                    elif nav_text == _("Places"):
                        if "plc" in self.report.cur_fname:
                            cs = True
                    elif nav_text == _("Events"):
                        if "evt" in self.report.cur_fname:
                            cs = True 
                    elif nav_text == _("Media"):
                        if "img" in self.report.cur_fname:
                            cs = True
                    elif nav_text == _("Address Book"):
                        if "addr" in self.report.cur_fname:
                            cs = True 

                    cs = 'class = "CurrentSection"' if cs else False
                    if not cs:
                        unordered += Html("li", inline =True) + (
                           Html("a", nav_text, href =url, title =nav_text)
                        )
                    else:
                        unordered += Html("li", attr =cs, inline =True) + (
                           Html("a", nav_text, href =url, title =nav_text)
                        )
                    index += 1
                    cols += 1

        # return navigation menu bar to its caller
        return navigation

    def add_image(self, option_name, height = 0):
        """
        will add an image (if present) to the page
        """

        pic_id = self.report.options[option_name]
        if pic_id:
            obj = self.report.database.get_object_from_gramps_id(pic_id)
            if obj is None:
                return None
            obj_handle = obj.handle
            mime_type = obj.get_mime_type()
            if mime_type and mime_type.startswith("image"):
                try:

                    newpath, thumb_path = self.report.prepare_copy_media(obj)
                    self.report.copy_file(Utils.media_path_full(
                        self.report.database, obj.get_path()), newpath)

                    # begin image
                    image = Html("img")
                    image.attr = ''
                    if height:
                        image.attr += 'height = "%d"'  % height

                    descr = html_escape(obj.get_description() )
                    newpath = self.report.build_url_fname(newpath)
                    image.attr += ' src = "%s" alt = "%s"' % (newpath, descr )

                    # return an image
                    return image   

                except (IOError, OSError), msg:
                    self.report.user.warn(_("Could not add photo to page"), 
                                          str(msg))

        # no image to return
        return None

    def media_ref_rect_regions(self, handle):

        """
        *************************************
        GRAMPS feature #2634 -- attempt to highlight subregions in media
        objects and link back to the relevant web page.

        This next section of code builds up the "records" we'll need to
        generate the html/css code to support the subregions
        *************************************
        """
        # get all of the backlinks to this media object; meaning all of
        # the people, events, places, etc..., that use this image
        _region_items = set()
        for (classname, newhandle) in self.dbase_.find_backlink_handles(handle, 
            include_classes = ["Person", "Family", "Event", "Place"]):

            # for each of the backlinks, get the relevant object from the db
            # and determine a few important things, such as a text name we
            # can use, and the URL to a relevant web page
            _obj     = None
            _name    = ""
            _linkurl = "#"
            if classname == "Person":
                # Is this a person for whom we have built a page:
                if newhandle in self.report.person_handles:
                    # If so, let's add a link to them:
                    _obj = self.dbase_.get_person_from_handle( newhandle )
                    if _obj:
                        # what is the shortest possible name we could use for this person?
                        _name = (_obj.get_primary_name().get_call_name() or
                                 _obj.get_primary_name().get_first_name() or
                                 _UNKNOWN
                                )
                        _linkurl = self.report.build_url_fname_html(_obj.handle, "ppl", True)
            elif classname == "Family":
                _obj = self.dbase_.get_family_from_handle( newhandle )
                partner1_handle = _obj.get_father_handle()
                partner2_handle = _obj.get_mother_handle()
                partner1 = None
                partner2 = None
                if partner1_handle:
                     partner1 = self.dbase_.get_person_from_handle(partner1_handle)
                if partner2_handle:
                    partner2 = self.dbase_.get_person_from_handle(partner2_handle)
                if partner2 and partner1:
                    _name = partner1.get_primary_name().get_first_name()
                    _linkurl = self.report.build_url_fname_html(partner1_handle, "ppl", True)  
                elif partner1:
                    _name = partner1.get_primary_name().get_first_name()
                    _linkurl = self.report.build_url_fname_html(partner1_handle, "ppl", True)  
                elif partner2:
                    _name = partner2.get_primary_name().get_first_name()
                    _linkurl = self.report.build_url_fname_html(partner2_handle, "ppl", True)
                if not _name:
                    _name = _UNKNOWN
            elif classname == "Event":
                _obj = self.dbase_.get_event_from_handle( newhandle )
                _name = _obj.get_description()
                if not _name:
                    _name = _UNKNOWN
                _linkurl = self.report.build_url_fname_html(_obj.handle, "evt", True) 
            elif classname == "Place":
                _obj = self.dbase_.get_place_from_handle(newhandle)
                _name = ReportUtils.place_name(self.dbase_, newhandle)
                if not _name:
                    _name = _UNKNOWN
                _linkurl = self.report.build_url_fname_html(newhandle, "plc", True)   

            # continue looking through the loop for an object...
            if _obj is None:
                continue

            # get a list of all media refs for this object
            media_list = _obj.get_media_list()

            # go media refs looking for one that points to this image
            for mediaref in media_list:

                # is this mediaref for this image?  do we have a rect?
                if mediaref.ref == handle and mediaref.rect is not None:

                    (x1, y1, x2, y2) = mediaref.rect
                    # GRAMPS gives us absolute coordinates,
                    # but we need relative width + height
                    w = x2 - x1
                    h = y2 - y1

                    # remember all this information, cause we'll need
                    # need it later when we output the <li>...</li> tags
                    item = (_name, x1, y1, w, h, _linkurl)
                    _region_items.add(item)
        """
        *************************************
        end of code that looks for and prepares the media object regions
        *************************************
        """

        # return media rectangles to its callers
        return _region_items

    def media_ref_region_to_object(self, media_handle, obj):
        """
        Return a region of this image if it refers to this object.
        """
        # get a list of all media refs for this object
        for mediaref in obj.get_media_list():
            # is this mediaref for this image?  do we have a rect?
            if (mediaref.ref == media_handle and 
                mediaref.rect is not None):
                return mediaref.rect # (x1, y1, x2, y2)
        return None

    def display_first_image_as_thumbnail(self, photolist, object):
        """
        Return the Html of the first image of photolist that is
        associated with object. First image might be a region in an
        image. Or, the first image might have regions defined in it.
        """

        if not photolist or not self.create_media:
            return None

        photo_handle = photolist[0].get_reference_handle()
        photo = self.report.database.get_object_from_handle(photo_handle)
        mime_type = photo.get_mime_type()
        descr = photo.get_description()

        # begin snapshot division
        with Html("div", class_ = "snapshot") as snapshot:

            if mime_type:

                # add link reference to media
                lnkref = (self.report.cur_fname, self.page_title, self.gid)
                self.report.add_lnkref_to_photo(photo, lnkref)

                region = self.media_ref_region_to_object(photo_handle, object)
                if region:

                    # make a thumbnail of this region
                    newpath = copy_thumbnail(self.report, photo_handle, photo, region)
                    newpath = self.report.build_url_fname(newpath, up = True)

                    snapshot += self.media_link(photo_handle, newpath, descr,
                                                up=True, usedescr=False)
                else:

                    real_path, newpath = self.report.prepare_copy_media(photo)
                    newpath = self.report.build_url_fname(newpath, up = True)
  
                    _region_items = self.media_ref_rect_regions(photo_handle)
                    if len(_region_items):
                        with Html("div", id = "GalleryDisplay") as mediadisplay:
                            snapshot += mediadisplay

                            ordered = Html("ol", class_ = "RegionBox")
                            mediadisplay += ordered
                            while len(_region_items):
                                (name, x, y, w, h, linkurl) = _region_items.pop()
                                ordered += Html("li", 
                                                style="left:%d%%; top:%d%%; width:%d%%; height:%d%%;"
                                                % (x, y, w, h)) + Html("a", name, href = linkurl)
                            # Need to add link to mediadisplay to get the links:
                            mediadisplay += self.media_link(photo_handle,
                                        newpath, descr, up=True, usedescr=False)
                    else:
                        try:

                            # begin hyperlink
                            # description is given only for the purpose of the alt tag in img element
                            snapshot += self.media_link(photo_handle, newpath,
                                                 descr, up=True, usedescr=False)

                        except (IOError, OSError), msg:
                            self.report.user.warn(_("Could not add photo to page"), str(msg))
            else:
                # begin hyperlink
                snapshot += self.doc_link(photo_handle, descr, up = True,
                                          usedescr = False)

                lnk = (self.report.cur_fname, self.page_title, self.gid)
                # FIXME. Is it OK to add to the photo_list of report?
                photo_list = self.report.photo_list
                if photo_handle in photo_list:
                    if lnk not in photo_list[photo_handle]:
                        photo_list[photo_handle].append(lnk)
                else:
                    photo_list[photo_handle] = [lnk]

        # return snapshot division to its callers
        return snapshot

    def display_additional_images_as_gallery(self, photolist, object):

        if not photolist or not self.create_media:
            return None

        # make referenced images have the same order as in media list:
        photolist_handles = {}
        for mediaref in photolist:
            photolist_handles[mediaref.get_reference_handle()] = mediaref
        photolist_ordered = []
        for photoref in copy.copy(object.get_media_list()):
            if photoref.ref in photolist_handles:
                photo = photolist_handles[photoref.ref]
                photolist_ordered.append(photo)
                try:
                    photolist.remove(photo)
                except ValueError:
                    log.warning("Error trying to remove '%s' from photolist" % (photo))
        # and add any that are left (should there be any?)
        photolist_ordered += photolist

        # begin individualgallery division and section title
        with Html("div", class_ = "subsection", id = "indivgallery") as section: 
            section += Html("h4", _("Media"), inline = True)

            displayed = []
            for mediaref in photolist_ordered:

                photo_handle = mediaref.get_reference_handle()
                photo = self.report.database.get_object_from_handle(photo_handle)

                if photo_handle in displayed:
                    continue
                mime_type = photo.get_mime_type()

                # get media description
                descr = photo.get_description()

                if mime_type:
                    try:

                        lnkref = (self.report.cur_fname, self.page_title, self.gid)
                        self.report.add_lnkref_to_photo(photo, lnkref)
                        real_path, newpath = self.report.prepare_copy_media(photo)

                        # create thumbnail url
                        # extension needs to be added as it is not already there
                        url = self.report.build_url_fname(photo_handle, "thumb", True) + ".png"
 
                        # begin hyperlink
                        section += self.media_link(photo_handle, url, descr, True)

                    except (IOError, OSError), msg:
                        self.report.user.warn(_("Could not add photo to page"), str(msg))
                else:
                    try:

                        # begin hyperlink
                        section += self.doc_link(photo_handle, descr, up = True)

                        lnk = (self.report.cur_fname, self.page_title, self.gid)
                        # FIXME. Is it OK to add to the photo_list of report?
                        photo_list = self.report.photo_list
                        if photo_handle in photo_list:
                            if lnk not in photo_list[photo_handle]:
                                photo_list[photo_handle].append(lnk)
                        else:
                            photo_list[photo_handle] = [lnk]
                    except (IOError, OSError), msg:
                        self.report.user.warn(_("Could not add photo to page"), str(msg))
                displayed.append(photo_handle)

        # add fullclear for proper styling
        section += fullclear

        # return indivgallery division to its caller
        return section

    def display_note_list(self, notelist = None):

        if not notelist:
            return None

        # begin narrative division
        with Html("div", class_ = "subsection narrative") as section:

            for notehandle in notelist:
                note = self.report.database.get_note_from_handle(notehandle)

                if note:
                    note_text = self.get_note_format(note, True)

                    # add section title
                    section += Html("h4", _("Narrative"), inline=True)

                    # attach note
                    section += note_text

        # return notes to its callers
        return section

    def display_url_list(self, urllist = None):

        if not urllist:
            return None

        # begin web links division
        with Html("div", class_ = "subsection", id = "WebLinks") as section:

            # begin web title
            section += Html("h4", _("Web Links"), inline = True)  

            # begin weblinks table
            with Html("table", class_ = "infolist weblinks") as table: 
                section += table

                thead = Html("thead")
                table += thead

                trow = Html("tr")
                thead += trow

                trow.extend(
                    Html('th', label, class_ = colclass, inline = True)
                        for (label, colclass) in [
                            (_("Type"),        "ColumnType"),
                            (_("Url"),         "ColumnPath"),
                            (_("Description"), "ColumnDescription")
                        ]
                    )

                tbody = Html("tbody")
                table += tbody

                for url in urllist:

                    trow = Html("tr")
                    tbody += trow
 
                    _type = url.get_type()
                    uri = url.get_path()
                    descr = url.get_description()

                    # Email address
                    if _type == UrlType.EMAIL:
                        if not uri.startswith("mailto:"):
                            uri = "mailto:%(email)s" % { 'email' : uri }

                    # Web Site address
                    elif _type == UrlType.WEB_HOME:
                        if not (uri.startswith("http://") or uri.startswith("https://")):
                            uri = "http://%(website)s" % { "website" : uri } 

                    # FTP server address
                    elif _type == UrlType.WEB_FTP:
                        if not (uri.startswith("ftp://") or uri.startswith("ftps://")):
                            uri = "ftp://%(ftpsite)s" % { "ftpsite" : uri }   

                    uri = Html("a", uri, href = uri, title = html_escape(descr))
                    trow.extend(
                        Html("td", data, class_ = colclass, inline = True)
                            for (data, colclass) in [
                                (str(_type), "ColumnType"),
                                (uri,        "ColumnPath"),
                                (descr,      "ColumnDescription")
                            ]
                    ) 
        return section

    def display_lds_ordinance(self, db_obj_):
        """
        display LDS information for a person or family
        """

        ldsordlist = db_obj_.lds_ord_list
        if not ldsordlist:
            return None

        # begin LDS Ordinance division and section title
        with Html("div", class_ = "subsection", id = "LDSOrdinance") as section:
            section += Html("h4", _("Latter-Day Saints/ LDS Ordinance"), inline = True)

            # ump individual LDS ordinance list
            section += self.dump_ordinance(db_obj_, "Person")

        # return section to its caller
        return section

    def display_ind_sources(self, srcobj):
        """
        will create the "Source References" section for an object
        """

        map(lambda i: self.bibli.add_reference(
                            self.report.database.get_citation_from_handle(i)), 
            srcobj.get_citation_list())
        sourcerefs = self.display_source_refs(self.bibli)

        # return to its callers
        return sourcerefs

    # Only used in IndividualPage.display_ind_sources(), and MediaPage.display_media_sources()
    def display_source_refs(self, bibli):
        if bibli.get_citation_count() == 0:
            return None

        with Html("div", class_ = "subsection", id = "sourcerefs") as section:
            section += Html("h4", _("Source References"), inline = True)

            ordered = Html("ol")

            cindex = 0
            citationlist = bibli.get_citation_list()
            for citation in citationlist:
                cindex += 1

                # Add this source to the global list of sources to be displayed
                # on each source page.
                lnk = (self.report.cur_fname, self.page_title, self.gid)
                shandle = citation.get_source_handle()
                if shandle in self.src_list:
                    if lnk not in self.src_list[shandle]:
                        self.src_list[shandle].append(lnk)
                else:
                    self.src_list[shandle] = [lnk]

                # Add this source and its references to the page
                source = self.dbase_.get_source_from_handle(shandle)
                if source is not None:
                    list = Html("li", self.source_link(source, cindex, up = True))
                else:
                    list = Html("li", "None")

                ordered1 = Html("ol")
                citation_ref_list = citation.get_ref_list()
                for key, sref in citation_ref_list:
                    cit_ref_li = Html("li", id="sref%d%s" % (cindex, key))
                    tmp = Html("ul")
                    confidence = Utils.confidence.get(sref.confidence, _('Unknown'))
                    if confidence == _('Normal'):
                        confidence = None
                    for (label, data) in [
                                          [_("Date"),       _dd.display(sref.date)],
                                          [_("Page"),       sref.page],
                                          [_("Confidence"), confidence] ]:
                        if data:
                            tmp += Html("li", "%s: %s" % (label, data))
                    for handle in sref.get_note_list():
                        this_note = self.dbase_.get_note_from_handle(handle)
                        if this_note is not None:
                            tmp += Html("li", "%s: %s" % (str(this_note.get_type() ),
                                                          self.get_note_format(this_note, True)
                                                          ))
                    if tmp:
                        cit_ref_li += tmp
                        ordered1 += cit_ref_li

                if citation_ref_list:
                    list += ordered1
                ordered += list
            section += ordered

        # return section to its caller
        return section

    def display_references(self, handlelist, up = False):

        if not handlelist:
            return None

        # begin references division and title
        with Html("div", class_ = "subsection", id = "references") as section:
            section += Html("h4", _("References"), inline = True)

            ordered = Html("ol")
            section += ordered 
            sortlist = sorted(handlelist, key=lambda x:locale.strxfrm(x[1]))
        
            for (path, name, gid) in sortlist:
                list = Html("li")
                ordered += list

                # Note. 'path' already has a filename extension
                url = self.report.build_url_fname(path, None, self.up)
                list += self.person_link(url, name or _UNKNOWN, None, gid = gid)

        # return references division to its caller
        return section

    def family_map_link(self, handle, url):
        """
        creates a link to the family map
        """
        return Html("a", _("Family Map"), href = url, title =_("Family Map"), class_ ="familymap", inline =True)

    def display_spouse(self, family, table, ppl_handle_list, place_lat_long):
        """
        display an individual's partner
        """
        gender = self.person.get_gender()
        reltype = family.get_relationship()

        if reltype == gen.lib.FamilyRelType.MARRIED:
            if gender == gen.lib.Person.FEMALE:
                relstr = _("Husband")
            elif gender == gen.lib.Person.MALE:
                relstr = _("Wife")
            else:
                relstr = _("Partner")
        else:
            relstr = _("Partner")

        spouse = False
        spouse_handle = ReportUtils.find_spouse(self.person, family)
        if spouse_handle:
            spouse = self.dbase_.get_person_from_handle(spouse_handle)
        rtype = str(family.get_relationship())

        # display family relationship status, and add spouse to FamilyMapPages
        if spouse:
            if self.familymappages:
                self._get_event_place(spouse, ppl_handle_list, place_lat_long)

            trow = Html("tr", class_ ="BeginFamily") + (
                Html("td", rtype, class_ ="ColumnType", inline =True),
                Html("td", relstr, class_ ="ColumnAttribute", inline =True)
            )
            table += trow
  
            tcell = Html("td", class_ ="ColumnValue")
            trow += tcell

            use_link = check_person_database(spouse_handle, ppl_handle_list)
            if use_link:
                url = self.report.build_url_fname_html(spouse_handle, "ppl", True)
                tcell += self.person_link(url, spouse, _NAME_STYLE_DEFAULT, gid =spouse.get_gramps_id())
            else:
                tcell += self.get_name(spouse)

        # display family events; such as marriage and divorce...
        family_events = family.get_event_ref_list()
        if family_events: 
            trow = Html("tr") + (
                Html("td", "&nbsp;", class_ = "ColumnType", inline = True),
                Html("td", "&nbsp;", class_ = "ColumnAttribute", inline = True),
                Html("td", self.format_family_events(family_events, place_lat_long), class_ = "ColumnValue")
            )
            table += trow

    def display_child_link(self, chandle, ppl_handle_list):
        """
        display child link ...
        """
        child = self.dbase_.get_person_from_handle(chandle)

        list = Html("li")
        use_link = check_person_database(chandle, ppl_handle_list)
        if use_link:
            url = self.report.build_url_fname_html(chandle, "ppl", True)
            list += self.person_link(url, child, _NAME_STYLE_DEFAULT, gid =child.get_gramps_id())
        else:
            list += self.get_name(child)
        return list

    def person_link(self, url, person, name_style, first = True, gid = None, thumbnailUrl = None):
        """
        creates a hyperlink for a person

        @param: person = person in database
        @param: namestyle = False -- first and suffix only
                          = True  -- name displayed in name_format variable
                          = None -- person is name
        @param: first = show person's name and gramps id if requested and available
        """
        # the only place that this will ever equal False
        # is first there is more than one event for a person
        if first:

            # see above for explanation
            if name_style:
                person_name = self.get_name(person)
            elif name_style == False:
                person_name = _get_short_name(person.gender, person.primary_name)
            elif name_style == None:    # abnormal specialty situation
                person_name = person

            # 1. start building link to image or person
            hyper = Html("a", href = url)

            # 2. insert thumbnail if there is one, otherwise insert class = "noThumb"
            if thumbnailUrl:
                hyper += Html("span", class_ = "thumbnail") + (
                    Html("img", src = thumbnailUrl, alt = "Image: " + person_name)
                )
            else:
                hyper.attr += ' class = "noThumb"'

            # 3. insert the person's name
            hyper += person_name

            # 3. insert gramps id if requested and available
            if (not self.noid and gid):
                hyper += Html("span", " [%s]" % gid, class_ = "grampsid", inline = True)

        else:
            hyper = "&nbsp;"

        # return hyperlink to its caller
        return hyper

    def media_link(self, handle, img_url, name, up, usedescr = True):
        """
        creates and returns a hyperlink to the thumbnail image

        @param: handle - photo handle
        @param: img_url - thumbnail url
        @param: name - photo description
        @param: up - whether to add "../../.." to url
        @param: usedescr - add media description
        """
        url = self.report.build_url_fname_html(handle, "img", up)
        name = html_escape(name)

        # begin thumbnail division
        with Html("div", class_ = "thumbnail") as thumbnail:

            # begin hyperlink
            if not self.create_thumbs_only:
                hyper = Html("a", href = url, title = name) + (
                    Html("img", src = img_url, alt = name)
                )
            else:
                hyper = Html("img", src =img_url, alt =name)
            thumbnail += hyper

            if usedescr:
                hyper += Html("p", name, inline = True)

        # return thumbnail division to its callers
        return thumbnail

    def doc_link(self, handle, name, up, usedescr = True):
        """
        create a hyperlink for the media object and returns it
  
        @param: handle - document handle
        @param: name - document name
        @param: up - whether to add "../../.." or not
        @param: usedescr - add description to hyperlink
        """
        url = self.report.build_url_fname(handle, "img", up)
        name = html_escape(name)

        # begin thumbnail division
        with Html("div", class_ = "thumbnail") as thumbnail:
            document_url = self.report.build_url_image("document.png", "images", up)

            if not self.create_thumbs_only:
                document_link = Html("a", href =url, title = name) + (
                    Html("img", src =document_url, alt =name)
                    )
            else:
                document_link = Html("img", src =document_url, alt =name)

            if usedescr:
                document_link += Html('br') + (
                    Html("span", name, inline =True)
                    )
            thumbnail += document_link

        # return thumbnail division to its callers
        return thumbnail

    def place_link(self, handle, name, gid = None, up = False):

        url = self.report.build_url_fname_html(handle, "plc", up)

        hyper = Html("a", html_escape(name), href = url, title = html_escape(name))
        if not self.noid and gid:
            hyper += Html("span", " [%s]" % gid, class_ = "grampsid", inline = True)

        # return hyperlink to its callers
        return hyper

    def dump_place(self, place, table):
        """
        dump a place's information from within the database

        @param: place -- place object from the database
        @param: table -- table from Placedetail
        """
        # add table body
        tbody = Html("tbody")
        table += tbody

        gid = place.gramps_id
        if not self.noid and gid:
            trow = Html("tr") + (
                Html("td", GRAMPSID, class_ = "ColumnAttribute", inline = True),
                Html("td", gid, class_ = "ColumnValue", inline = True)
            )
            tbody += trow

        data = place.get_latitude()
        if data != "":
            trow = Html('tr') + (
                Html("td", LATITUDE, class_ = "ColumnAttribute", inline = True),
                Html("td", data, class_ = "ColumnValue", inline = True)
            )
            tbody += trow
        data = place.get_longitude()
        if data != "":
            trow = Html('tr') + (
                Html("td", LONGITUDE, class_ = "ColumnAttribute", inline =True),
                Html("td", data, class_ = "ColumnValue", inline = True)
            )
            tbody += trow

        if place.main_loc:
            ml = place.get_main_location()
            if ml and not ml.is_empty(): 

                for (label, data) in [
                    (STREET,         ml.street),
                    (LOCALITY,       ml.locality), 
                    (CITY,           ml.city),
                    (PARISH,         ml.parish),
                    (COUNTY,         ml.county),
                    (STATE,          ml.state),
                    (POSTAL,         ml.postal),
                    (COUNTRY,        ml.country),
                    (_("Telephone"), ml.phone) ]:  
                    if data:
                        trow = Html("tr") + (
                            Html("td", label, class_ = "ColumnAttribute", inline = True),
                            Html("td", data, class_ = "ColumnValue", inline = True)
                        )
                        tbody += trow

        altloc = place.get_alternate_locations()
        if altloc:
            tbody += Html("tr") + Html("td", "&nbsp;", colspan = 2)
            trow = Html("tr") + (
                    Html("th", ALT_LOCATIONS, colspan = 2, class_ = "ColumnAttribute", inline = True),
            )
            tbody += trow
            for loc in (nonempt for nonempt in altloc if not nonempt.is_empty()):
                for (label, data) in [
                    (STREET,    loc.street),
                    (LOCALITY,  loc.locality), 
                    (CITY,      loc.city),
                    (PARISH,    loc.parish),
                    (COUNTY,    loc.county),
                    (STATE,     loc.state),
                    (POSTAL,    loc.postal),
                    (COUNTRY,   loc.country),]:
                    if data:
                        trow = Html("tr") + (
                            Html("td", label, class_ = "ColumnAttribute", inline = True),
                            Html("td", data, class_ = "ColumnValue", inline = True)
                        )
                        tbody += trow
                tbody += Html("tr") + Html("td", "&nbsp;", colspan = 2)

        # return place table to its callers
        return table

    def repository_link(self, handle, name, gid = None, up = False):
        """
        returns a hyperlink for repository links

        @param: handle -- repository handle
        @param: name -- repository title
        @param: gid -- gramps id
        @param: up -- whether to add backward reference
        """
        name = html_escape(name)

        url = self.report.build_url_fname_html(handle, 'repo', up)

        hyper = Html("a", name, href =url, title =name)
        if not self.noid and gid:
            hyper += Html("span", '[%s]' % gid, class_ ="grampsid", inline =True)
        return hyper

    def dump_repository_ref_list(self, repo_ref_list):
        """
        dumps the repository
        """

        # Repository list division...
        with Html("div", class_ ="subsection", id ="repositories") as repositories:
            repositories += Html("h4", _("Repositories"), inline = True)

            with Html("table", class_ ="infolist") as table:
                repositories += table

                thead = Html("thead")
                table += thead

                trow = Html("tr") + (
                    Html("th", _("Number"), class_ ="ColumnRowLabel", inline =True),
                    Html("th", _("Title"), class_ ="ColumnName", inline =True)
                )
                thead += trow

                tbody = Html("tbody")
                table += tbody

                index = 1
                for repo_ref in repo_ref_list:
                    repository = self.dbase_.get_repository_from_handle(repo_ref.ref)
                    if repository:
                    
                        trow = Html("tr") + (
                            Html("td", index, class_ ="ColumnRowLabel", inline =True),
                            Html("td", self.repository_link(repo_ref.ref, repository.get_name(),
                                                            repository.get_gramps_id(), self.up))
                        )
                        tbody += trow
        return repositories

    def dump_residence(self, has_res):
        """ creates a residence from the daTABASE """

        if not has_res:
            return None

        # begin residence division
        with Html("div", class_ = "content Residence") as residence:
            residence += Html("h4", _("Residence"), inline = True)

            with Html("table", class_ = "infolist place") as table:
                residence += table

                place_handle = has_res.get_place_handle()
                if place_handle:
                    place = self.report.database.get_place_from_handle(place_handle)
                    if place:
                        self.dump_place(place, table)

                descr = has_res.get_description()
                if descr:
    
                    trow = Html("tr")
                    if len(table) == 3:
                        # append description row to tbody element of dump_place
                        table[-2] += trow
                    else:
                        # append description row to table element
                        table += trow
    
                    trow.extend(Html("td", DESCRHEAD, class_ = "ColumnAttribute", inline = True))
                    trow.extend(Html("td", descr, class_ = "ColumnValue", inline=True))

        # return information to its callers
        return residence

# ---------------------------------------------------------------------------------------
#              # Web Page Fortmatter and writer                   
# ---------------------------------------------------------------------------------------
    def XHTMLWriter(self, htmlinstance, of):
        """
        Will format, write, and close the file

        of -- open file that is being written to
        htmlinstance -- web page created with libhtml
            src/plugins/lib/libhtml.py
        """

        htmlinstance.write(partial(print, file=of)) 

        # closes the file
        self.report.close_file(of)
#################################################
#
#    creates the Individual List Page
#
#################################################
class IndividualListPage(BasePage):
    def __init__(self, report, title, ppl_handle_list):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        # plugin variables for this module
        showbirth = report.options['showbirth']
        showdeath = report.options['showdeath']
        showpartner = report.options['showpartner']
        showparents = report.options['showparents']

        of = self.report.create_file("individuals")
        indlistpage, head, body = self.write_header(_("Individuals"))

        # begin Individuals division
        with Html("div", class_ = "content", id = "Individuals") as individuallist:
            body += individuallist

            # Individual List page message
            msg = _("This page contains an index of all the individuals in the "
                          "database, sorted by their last names. Selecting the person&#8217;s "
                          "name will take you to that person&#8217;s individual page.")
            individuallist += Html("p", msg, id = "description")

            # add alphabet navigation
            menu_set = get_first_letters(self.dbase_, ppl_handle_list, _KEYPERSON) 
            alpha_nav, menu_set = alphabet_navigation(menu_set)
            if alpha_nav is not None:
                individuallist += alpha_nav

            # begin table and table head
            with Html("table", class_ = "infolist primobjlist IndividualList") as table:
                individuallist += table
                thead = Html("thead")
                table += thead

                trow = Html("tr")
                thead += trow    

                # show surname and first name
                trow += Html("th", _("Surname"),    class_ = "ColumnSurname", inline = True)
                trow += Html("th", _("Given Name"), class_ = "ColumnName", inline = True)

                if showbirth:
                    trow += Html("th", _("Birth"), class_ = "ColumnDate", inline = True)

                if showdeath:
                    trow += Html("th", _("Death"), class_ = "ColumnDate", inline = True)

                if showpartner:
                    trow += Html("th", _("Partner"), class_ = "ColumnPartner", inline = True)

                if showparents:
                    trow += Html("th", _("Parents"), class_ = "ColumnParents", inline = True)

            tbody = Html("tbody")
            table += tbody

            ppl_handle_list = sort_people(self.dbase_, ppl_handle_list)
            letter = "!"
            for (surname, handle_list) in ppl_handle_list:
                first = True
                prev_letter = letter
                letter = first_letter(surname)
                for person_handle in handle_list:
                    person = self.dbase_.get_person_from_handle(person_handle)

                    # surname column
                    trow = Html("tr")
                    tbody += trow
                    tcell = Html("td", class_ = "ColumnSurname", inline = True)
                    trow += tcell
                    if first:
                        trow.attr = 'class = "BeginSurname"'
                        if surname:
                            if letter != prev_letter:
                                tcell += Html("a", surname, name = letter,
                                    id_ = letter,
                                    title = "Surname with letter " + letter)
                            else:
                                tcell += Html("a", surname,
                                    title = "Surname with letter " + letter)
                        else:
                            tcell += "&nbsp;"
                    else:
                        tcell += "&nbsp;"
                    first = False

                    # firstname column
                    url = self.report.build_url_fname_html(person.handle, "ppl")
                    trow += Html("td", self.person_link(url, person, _NAME_STYLE_FIRST, gid = person.gramps_id),
                        class_ = "ColumnName")

                    # birth column
                    if showbirth:
                        tcell = Html("td", class_ = "ColumnBirth", inline = True)
                        trow += tcell

                        birth_date = _find_birth_date(self.dbase_, person)
                        if birth_date is not None:
                            if birth_date.fallback:
                                tcell += Html('em', _dd.display(birth_date), inline = True)
                            else:
                                tcell += _dd.display(birth_date)
                        else:
                            tcell += "&nbsp;"

                    # death column
                    if showdeath:
                        tcell = Html("td", class_ = "ColumnDeath", inline = True)
                        trow += tcell

                        death_date = _find_death_date(self.dbase_, person)
                        if death_date is not None:
                            if death_date.fallback:
                                tcell += Html('em', _dd.display(death_date), inline = True)
                            else:
                                tcell += _dd.display(death_date)
                        else:
                            tcell += "&nbsp;"

                    # partner column
                    if showpartner:
                        tcell = Html("td", class_ = "ColumnPartner")
                        trow += tcell

                        family_list = person.get_family_handle_list()
                        first_family = True
                        partner_name = None
                        if family_list:
                            for family_handle in family_list:
                                family = self.dbase_.get_family_from_handle(family_handle)
                                partner_handle = ReportUtils.find_spouse(person, family)
                                if partner_handle:
                                    partner = self.dbase_.get_person_from_handle(partner_handle)
                                    if not first_family:
                                        tcell += ", "  
                                    use_link = check_person_database(partner_handle, ppl_handle_list)
                                    if use_link:
                                        url = self.report.build_url_fname_html(partner_handle, "ppl")
                                        tcell += self.person_link(url, partner, _NAME_STYLE_DEFAULT,
                                            gid = partner.get_gramps_id())
                                    else:
                                        tcell += self.get_name(partner)
                                    first_family = False
                        else:
                            tcell += "&nbsp;"

                    # parents column
                    if showparents:

                        parent_handle_list = person.get_parent_family_handle_list()
                        if parent_handle_list:
                            parent_handle = parent_handle_list[0]
                            family = self.dbase_.get_family_from_handle(parent_handle)
                            father_handle = family.get_father_handle()
                            mother_handle = family.get_mother_handle()
                            father = self.dbase_.get_person_from_handle(father_handle)
                            mother = self.dbase_.get_person_from_handle(mother_handle)
                            if father:
                                father_name = self.get_name(father)
                            if mother:
                                mother_name = self.get_name(mother)
                            samerow = False 
                            if mother and father:
                                tcell = Html("span", father_name, class_ = "father fatherNmother")
                                tcell += Html("span", mother_name, class_ = "mother")
                            elif mother:
                                tcell = Html("span", mother_name, class_ = "mother")
                            elif father:
                                tcell = Html("span", father_name, class_ = "father")
                            else:
                                tcell = "&nbsp;"
                                samerow = True
                        else:
                            tcell = "&nbsp;"
                            samerow = True
                        trow += Html("td", tcell, class_ = "ColumnParents", inline = samerow)

        # create clear line for proper styling
        # create footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(indlistpage, of)

#################################################
#
#    create the page from SurnameListPage
#
#################################################
class SurnamePage(BasePage):
    """
    This will create a list of individuals with the same surname
    """

    def __init__(self, report, title, surname, ppl_handle_list):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        # module variables
        showbirth = report.options['showbirth']
        showdeath = report.options['showdeath']
        showpartner = report.options['showpartner']
        showparents = report.options['showparents']

        of = self.report.create_file(name_to_md5(surname), "srn")
        self.up = True
        surnamepage, head, body = self.write_header("%s - %s" % (_("Surname"), surname))

        # begin SurnameDetail division
        with Html("div", class_ = "content", id = "SurnameDetail") as surnamedetail:
            body += surnamedetail

            # section title
            surnamedetail += Html("h3", html_escape(surname), inline = True)

            msg = _("This page contains an index of all the individuals in the "
                    "database with the surname of %s. Selecting the person&#8217;s name "
                    "will take you to that person&#8217;s individual page.") % surname
            surnamedetail += Html("p", msg, id = "description")

            # begin surname table and thead
            with Html("table", class_ = "infolist primobjlist surname") as table:
                surnamedetail += table
                thead = Html("thead")
                table += thead

                trow = Html("tr")
                thead += trow

                # Name Column
                trow += Html("th", _("Given Name"), class_ = "ColumnName", inline = True) 

                if showbirth:
                    trow += Html("th", _("Birth"), class_ = "ColumnDate", inline = True)

                if showdeath:
                    trow += Html("th", _("Death"), class_ = "ColumnDate", inline = True)

                if showpartner:
                    trow += Html("th", _("Partner"), class_ = "ColumnPartner", inline = True)

                if showparents:
                    trow += Html("th", _("Parents"), class_ = "ColumnParents", inline = True)

                # begin table body 
                tbody = Html("tbody")
                table += tbody

                for person_handle in ppl_handle_list:
 
                    person = self.dbase_.get_person_from_handle(person_handle)
                    trow = Html("tr")
                    tbody += trow

                    # firstname column
                    url = self.report.build_url_fname_html(person.handle, "ppl", True)
                    trow += Html("td", self.person_link(url, person, _NAME_STYLE_FIRST, gid = person.gramps_id),
                        class_ = "ColumnName")  

                    # birth column
                    if showbirth:
                        tcell = Html("td", class_ = "ColumnBirth", inline = True)
                        trow += tcell

                        birth_date = _find_birth_date(self.dbase_, person)
                        if birth_date is not None:
                            if birth_date.fallback:
                                tcell += Html('em', _dd.display(birth_date), inline = True)
                            else:
                                tcell += _dd.display(birth_date)
                        else:
                            tcell += "&nbsp;"

                    # death column
                    if showdeath:
                        tcell = Html("td", class_ = "ColumnDeath", inline = True)
                        trow += tcell

                        death_date = _find_death_date(self.dbase_, person)
                        if death_date is not None:
                            if death_date.fallback:
                                tcell += Html('em', _dd.display(death_date), inline = True)
                            else:
                                tcell += _dd.display(death_date)
                        else:
                            tcell += "&nbsp;"

                    # partner column
                    if showpartner:
                        tcell = Html("td", class_ = "ColumnPartner")
                        trow += tcell
                        family_list = person.get_family_handle_list()
                        first_family = True
                        if family_list:
                            for family_handle in family_list:
                                family = self.dbase_.get_family_from_handle(family_handle)
                                partner_handle = ReportUtils.find_spouse(person, family)
                                if partner_handle:
                                    partner = self.dbase_.get_person_from_handle(partner_handle)
                                    if not first_family:
                                        tcell += ','
                                    use_link = check_person_database(partner_handle, ppl_handle_list)
                                    if use_link:
                                        url = self.report.build_url_fname_html(partner_handle, "ppl", True) 
                                        tcell += self.person_link(url, partner, _NAME_STYLE_DEFAULT, 
                                            gid = partner.get_gramps_id())
                                    else:
                                        tcell += self.get_name(partner)
                                    first_family = False
                        else:
                            tcell += "&nbsp;"


                    # parents column
                    if showparents:
                        parent_handle_list = person.get_parent_family_handle_list()
                        if parent_handle_list:
                            parent_handle = parent_handle_list[0]
                            family = self.dbase_.get_family_from_handle(parent_handle)
                            father_id = family.get_father_handle()
                            mother_id = family.get_mother_handle()
                            father = self.dbase_.get_person_from_handle(father_id)
                            mother = self.dbase_.get_person_from_handle(mother_id)
                            if father:
                                father_name = self.get_name(father)
                            if mother:
                                mother_name = self.get_name(mother)
                            if mother and father:
                                tcell = Html("span", father_name, class_ = "father fatherNmother")
                                tcell += Html("span", mother_name, class_ = "mother")
                            elif mother:
                                tcell = Html("span", mother_name, class_ = "mother", inline = True)
                            elif father:
                                tcell = Html("span", father_name, class_ = "father", inline = True)
                            samerow = False
                        else:
                            tcell = "&nbsp;"
                            samerow = True
                        trow += Html("td", tcell, class_ = "ColumnParents", inline = samerow)

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(surnamepage, of)  

class FamilyListPage(BasePage):
    def __init__(self, report, title, ind_list, displayed):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        of = self.report.create_file("families")
        familiesListPage, head, body = self.write_header(_("Families"))

        # begin Family Division
        with Html("div", class_ ="content", id ="Relationships") as relationlist:
            body +=relationlist

            # Families list page message
            msg = _("This page contains an index of all the families/ relationships in the "
                          "database, sorted by their family name/ surname. Clicking on a person&#8217;s "
                          "name will take you to their family/ relationship&#8217;s page.")
            relationlist += Html("p", msg, id = "description")

            # add alphabet navigation
            menu_set = get_first_letters(self.dbase_, ind_list, _KEYPERSON) 
            alpha_nav, menu_set = alphabet_navigation(menu_set)
            if alpha_nav:
                relationlist += alpha_nav
            ltrs_displayed = {}

            # begin families table and table head
            with Html("table", class_ ="infolist relationships") as table:
                relationlist += table

                thead = Html("thead")
                table += thead

                trow = Html("tr")
                thead += trow

               # set up page columns
                trow.extend(
                    Html("th", trans, class_ =colclass, inline =True)    
                        for trans, colclass in [
                            (_("Letter"),    "ColumnRowLabel"),     
                            (_("Partner 1"), "ColumnPartner"),
                            (_("Partner 2"), "ColumnPartner"),
                            (_("Marriage"),  "ColumnDate"),
                            (_("Divorce"),   "ColumnDate")
                        ]
                )

                tbody = Html("tbody")
                table += tbody

                # begin displaying index list
                ppl_handle_list = sort_people(self.dbase_, ind_list)
                for (surname, handle_list) in ppl_handle_list:

                    if surname:      
                        letter = first_letter(surname)
                    else:
                        letter ='&nbsp;'

                    # get person from sorted database list
                    for phandle in handle_list:
                        person = self.dbase_.get_person_from_handle(phandle)
                        if person:
                            if phandle not in displayed:

                                family_handle_list = person.get_family_handle_list()
                                if family_handle_list:

                                    first_family = True
                                    for fhandle in family_handle_list:

                                        family = self.dbase_.get_family_from_handle(fhandle)
                                        if family:

                                            trow = Html("tr")
                                            tbody += trow

                                            tcell = Html("td", class_ ="ColumnRowLabel")
                                            trow += tcell 

                                            if letter not in ltrs_displayed:
                                                trow.attr = 'class ="BeginLetter"'
                                                tcell += Html("a", letter, name =letter,
                                                    title ="Families beginning with letter " + letter, inline =True)

                                                ltrs_displayed[letter] = True
                                            else:
                                                tcell += '&nbsp;'

                                            tcell = Html("td", class_ ="ColumnPartner")
                                            trow += tcell

                                            if first_family:
                                                trow.attr = 'class ="BeginFamily"'
 
                                                tcell += self.family_link(fhandle, self.get_name(person),
                                                    person.get_gramps_id())

                                                first_family = False
                                            else:
                                                tcell += '&nbsp;'

                                            tcell = Html("td", class_ ="ColumnPartner")
                                            trow += tcell

                                            # get partner if there is one listed?
                                            partner_handle = ReportUtils.find_spouse(person, family)
                                            if partner_handle:
                                                partner = self.dbase_.get_person_from_handle(partner_handle)
                                                if partner:
                                                    displayed.add(partner_handle)
                                                    use_link = check_person_database(partner_handle, ind_list)
                                                    if use_link:
                                                        tcell += self.family_link(fhandle, self.get_name(partner),
                                                            partner.get_gramps_id())
                                                    else:
                                                        tcell += self.get_name(partner)
                                            else:
                                                tcell += '&nbsp;'

                                            # family events; such as marriage and divorce events
                                            fam_evt_ref_list = family.get_event_ref_list()
                                            tcell1 = Html("td", class_ ="ColumnDate", inline =True)
                                            tcell2 = Html("td", class_ ="ColumnDate", inline =True)
                                            trow += (tcell1, tcell2)

                                            if fam_evt_ref_list:
                                                for evt_ref in fam_evt_ref_list:
                                                    event = self.dbase_.get_event_from_handle(evt_ref.ref)
                                                    if event:
                                                        evt_type = event.get_type()
                                                        if evt_type in [gen.lib.EventType.MARRIAGE,
                                                                        gen.lib.EventType.DIVORCE]:

                                                            if evt_type == gen.lib.EventType.MARRIAGE:
                                                                tcell1 += _dd.display(event.get_date_object())
                                                            else:
                                                                tcell1 += '&nbsp;'

                                                            if evt_type == gen.lib.EventType.DIVORCE:
                                                                tcell2 += _dd.display(event.get_date_object())
                                                            else:
                                                                tcell2 += '&nbsp;'
                                            else:
                                                tcell1 += '&nbsp;'
                                                tcell2 += '&nbsp;'
                                            first_family = False
                        displayed.add(phandle)           

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(familiesListPage, of)

class FamilyPage(BasePage):
    def __init__(self, report, title, person, family, place_list, ppl_handle_list, place_lat_long):
        if (not person or not family):
            return
        self.dbase_ = report.database

        self.bibli = Bibliography()
        self.person = person
        self.place_list = place_list

        BasePage.__init__(self, report, title, family.get_gramps_id())
        self.up = True

        birthorder = report.options["birthorder"]
        self.familymappages = report.options["familymappages"]

        of = self.report.create_file(family.get_handle(), "fam")
        familydetailpage, head, body = self.write_header(_("Family/ Relationship"))

        partner = False
        partner_handle = ReportUtils.find_spouse(person, family)
        if partner_handle:
            partner = self.dbase_.get_person_from_handle(partner_handle)

        # begin FamilyDetaill division
        with Html("div", class_ ="content", id ="RelationshipDetail") as relationshipdetail:
            body += relationshipdetail

            # family media list for initial thumbnail
            if self.create_media:
                family_media_list = family.get_media_list()
                thumbnail = self.display_first_image_as_thumbnail(family_media_list, family)
                if thumbnail:
                    relationshipdetail += thumbnail

            url = self.report.build_url_fname_html(person.get_handle(), 'ppl', up =self.up)
            person_link = self.person_link(url, person, _NAME_STYLE_DEFAULT, gid = person.get_gramps_id())

            if partner:
                use_link = check_person_database(partner_handle, ppl_handle_list)
                if use_link:
                    url = self.report.build_url_fname_html(partner_handle, 'ppl', up =self.up)
                    partner_link = self.person_link(url, partner, _NAME_STYLE_DEFAULT,
                        gid = partner.get_gramps_id())
                else:
                    partner_link = self.get_name(partner)

            # determine if husband and wife, husband only, or spouse only....
            self.page_title = _("Family of ")
            if person and partner:
                self.page_title += "%s and %s" % (person_link, partner_link)
            elif person:
               self.page_title += "%s" % person_link
            elif partner:
                self.page_title += "%s" % partner_link
            relationshipdetail += Html("h2", self.page_title, inline =True)


            # display relationships
            families = self.display_relationships(self.person, ppl_handle_list, place_lat_long)
            if families is not None:
                relationshipdetail += families

            # display additional images as gallery
            if self.create_media:
                addgallery = self.display_additional_images_as_gallery(family_media_list, family)
                if addgallery:
                    relationshipdetail += addgallery

            # Narrative subsection
            notelist = family.get_note_list()
            if notelist: 
                relationshipdetail += self.display_note_list(notelist)

            # display family LDS ordinance...
            family_lds_ordinance_list = family.get_lds_ord_list()
            if family_lds_ordinance_list:
                relationshipdetail += self.display_lds_ordinance(family)

            # get attribute list
            attrlist = family.get_attribute_list()
            if attrlist:
                attrsection, attrtable = self.display_attribute_header()
                self.display_attr_list(attrlist, attrtable)
                relationshipdetail += attrsection

            # source references
            srcrefs = self.display_ind_sources(family)
            if srcrefs:
                relationshipdetail += srcrefs            

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(familydetailpage, of)

class PlaceListPage(BasePage):
    def __init__(self, report, title, place_handles):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        of = self.report.create_file("places")
        placelistpage, head, body = self.write_header(_("Places"))

        # begin places division
        with Html("div", class_ = "content", id = "Places") as placelist:
            body += placelist

            # place list page message
            msg = _("This page contains an index of all the places in the "
                          "database, sorted by their title. Clicking on a place&#8217;s "
                          "title will take you to that place&#8217;s page.")
            placelist += Html("p", msg, id = "description")

            # begin alphabet navigation
            menu_set = get_first_letters(self.dbase_, place_handles, _KEYPLACE) 
            alpha_nav, menu_set = alphabet_navigation(menu_set)
            if alpha_nav is not None:
                placelist += alpha_nav

            # begin places table and table head
            with Html("table", class_ = "infolist primobjlist placelist") as table:
                placelist += table

                # begin table head
                thead = Html("thead")
                table += thead

                trow =  Html("tr")
                thead += trow

                trow.extend(
                    Html("th", label, class_ =colclass, inline =True)
                    for (label, colclass) in [
                        [_("Letter"),            "ColumnLetter"],
                        [_("Place Name | Name"), "ColumnName"],
                        [_("State"),             "ColumnState"],
                        [_("Country"),           "ColumnCountry"],
                        [_("Latitude"),          "ColumnLatitude"],
                        [_("Longitude"),         "ColumnLongitude"] ]
                )

                sort = Sort.Sort(self.dbase_)
                handle_list = sorted(place_handles, key = sort.by_place_title_key)
                last_letter = ''

                # begin table body
                tbody = Html("tbody")
                table += tbody

                for handle in handle_list:
                    place = self.dbase_.get_place_from_handle(handle)
                    if place: 
                        place_title = place.get_title()
                        ml = place.get_main_location()

                        if place_title:  
                            letter = first_letter(place_title)
                        else:
                            letter = '&nbsp;' 

                        trow = Html("tr")
                        tbody += trow

                        tcell = Html("td", class_ = "ColumnLetter", inline = True)
                        trow += tcell
                        if letter != last_letter:
                            last_letter = letter
                            trow.attr = 'class = "BeginLetter"'

                            tcell += Html("a", last_letter, name =last_letter, 
                                title = _("Places with letter %s" % last_letter))
                        else:
                            tcell += "&nbsp;"

                        trow += Html("td", self.place_link(place.get_handle(), place_title, place.get_gramps_id() ), 
                            class_ = "ColumnName")

                        trow.extend(
                            Html("td", data or "&nbsp;", class_ =colclass, inline =True)
                            for (colclass, data) in [
                                ["ColumnState",     ml.state],
                                ["ColumnCountry",   ml.country] ]
                        )

                        tcell1 = Html("td", class_ ="ColumnLatitude", inline =True)
                        tcell2 = Html("td", class_ ="ColumnLongitude", inline =True)
                        trow += (tcell1, tcell2)

                        if (place.lat and place.long):
                            latitude, longitude = conv_lat_lon(place.lat,
                                                               place.long,
                                                               "DEG")
                            tcell1 += latitude
                            tcell2 += longitude
                        else:
                            tcell1 += '&nbsp;'
                            tcell2 += '&nbsp;'
 
        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(placelistpage, of)

######################################################
#                                                    #
#                    Place Pages                     #
#                                                    #
######################################################
class PlacePage(BasePage):
    def __init__(self, report, title, place_handle, src_list, place_list):
        self.bibli = Bibliography()
        self.dbase_ = report.database
        place = self.dbase_.get_place_from_handle(place_handle)
        if not place:
            return None
        BasePage.__init__(self, report, title, place.get_gramps_id())

        of = self.report.create_file(place_handle, "plc")
        self.src_list = src_list
        self.up = True
        self.page_title = place.get_title()
        placepage, head, body = self.write_header(_("Places"))

        self.placemappages = self.report.options['placemappages']
        self.mapservice = self.report.options['mapservice']

        # begin PlaceDetail Division
        with Html("div", class_ = "content", id = "PlaceDetail") as placedetail:
            body += placedetail

            if self.create_media:
                media_list = place.get_media_list()
                thumbnail = self.display_first_image_as_thumbnail(media_list, place)
                if thumbnail is not None:
                    placedetail += thumbnail

            # add section title
            placedetail += Html("h3", html_escape(self.page_title), inline =True)

            # begin summaryarea division and places table
            with Html("div", id ='summaryarea') as summaryarea:
                placedetail += summaryarea

                with Html("table", class_ = "infolist place") as table:
                    summaryarea += table

                    # list the place fields
                    self.dump_place(place, table)

            # place gallery
            if self.create_media:
                placegallery = self.display_additional_images_as_gallery(media_list, place)
                if placegallery is not None:
                    placedetail += placegallery

            # place notes
            notelist = self.display_note_list(place.get_note_list())
            if notelist is not None:
                placedetail += notelist 

            # place urls
            urllinks = self.display_url_list(place.get_url_list())
            if urllinks is not None:
                placedetail += urllinks

            #for all plugins
                # if a place place_detail plugin
                # if plugin active
                # call_generate_page(report, title, place_handle, src_list, head, body, place, placedetail)

            # add place map here
            if self.placemappages:
                if (place and (place.lat and place.long)):
                    latitude, longitude = conv_lat_lon(place.get_latitude(), place.get_longitude(), "D.D8")
                    placetitle = place.get_title()

                    # add narrative-maps CSS...
                    fname = "/".join(["styles", "narrative-maps.css"])
                    url = self.report.build_url_fname(fname, None, self.up)
                    head += Html("link", href = url, type = "text/css", media = "screen", rel = "stylesheet")

                    # add MapService specific javascript code
                    if self.mapservice == "Google":
                        head += Html("script", type ="text/javascript",
                            src ="http://maps.googleapis.com/maps/api/js?sensor=false", inline =True)
                    else:
                        head += Html("script", type = "text/javascript",
                            src = "http://www.openlayers.org/api/OpenLayers.js", inline = True)

                    # section title
                    placedetail += Html("h4", _("Place Map"), inline =True)

                    # begin map_canvas division
                    with Html("div", id ="place_canvas", inline = True) as canvas:
                        placedetail += canvas

                        # begin inline javascript code
                        # because jsc is a docstring, it does NOT have to be properly indented
                        if self.mapservice == "Google":
                            with Html("script", type = "text/javascript", indent = False) as jsc:
                                head += jsc

                                # Google adds Latitude/ Longitude to its maps...
                                jsc += google_jsc % (latitude, longitude, placetitle)

                        else:
                            # OpenStreetMap (OSM) adds Longitude/ Latitude to its maps,
                            # and needs a country code in lowercase letters...
                            with Html("script", type = "text/javascript") as jsc:
                                canvas += jsc

                                jsc += openstreetmap_jsc % (Utils.xml_lang()[3:5].lower(), longitude, latitude)

            # add javascript function call to body element
            body.attr +=' onload = "initialize();" '

            # place references
            reflist = self.display_references(place_list[place.handle])
            if reflist is not None:
                placedetail += reflist

            # source references
            srcrefs = self.display_ind_sources(place) 
            if srcrefs is not None:
                placedetail += srcrefs

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(placepage, of)

class EventListPage(BasePage):
    def __init__(self, report, title, event_types, event_handle_list, ppl_handle_list):
        """
        Will create the event list page

        @param: event_types: a list of the type in the events database
        @param: event_handle_list -- a list of event handles
        """
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        of = self.report.create_file("events")
        eventslistpage, head, body = self.write_header(_("Events"))

        # begin events list  division
        with Html("div", class_ = "content", id = "EventList") as eventlist:
            body += eventlist

            msg = _("This page contains an index of all the events in the "
                    "database, sorted by their type and date (if one is "
                    "present). Clicking on an event&#8217;s Gramps ID "
                    "will open a page for that event.")
            eventlist += Html("p", msg, id = "description")

            # get alphabet navigation...
            menu_set = get_first_letters(self.dbase_, event_types, _ALPHAEVENT)
            alpha_nav, menu_set = alphabet_navigation(menu_set)
            if alpha_nav:
                eventlist += alpha_nav

            # begin alphabet event table
            with Html("table", class_ = "infolist primobjlist alphaevent") as table:
                eventlist += table

                thead = Html("thead")
                table += thead

                trow = Html("tr")
                thead += trow

                trow.extend(
                    Html("th", label, class_ = colclass, inline = True)
                        for (label, colclass) in [
                            (_("Letter"),    "ColumnRowLabel"),
                            (_("Type"),      "ColumnType"),
                            (_("Date"),      "ColumnDate"),
                            (_("Gramps ID"), "ColumnGRAMPSID"),
                            (_("Person"),    "ColumnPerson")
                        ]
                )

                tbody = Html("tbody")
                table += tbody

                prev_letter = ""
                # separate events by their type and then thier event handles
                for (evt_type, datalist) in sort_event_types(self.dbase_, event_types, event_handle_list):
                    first_letter = True
                    _EVENT_DISPLAYED = []

                    # sort datalist by date of event
                    datalist = sorted(datalist, key = self._getEventDate)
                    first_event = True

                    while datalist:
                        event_handle = datalist[0]
                        event = self.dbase_.get_event_from_handle(event_handle)
                        _type = event.get_type()
                        gid = event.get_gramps_id()

                        # check to see if we have listed this gramps_id yet?
                        if gid not in _EVENT_DISPLAYED:

                            # family event 
                            if int(_type) in _EVENTMAP:
                                handle_list = set(self.dbase_.find_backlink_handles(
                                    event_handle, 
                                    include_classes=['Family', 'Person']))

                            # personal event
                            else:
                                handle_list = set(self.dbase_.find_backlink_handles(
                                    event_handle, 
                                    include_classes=['Person']))
                            if handle_list:

                                trow = Html("tr")
                                tbody += trow

                                # set up hyperlinked letter for alphabet_navigation
                                tcell = Html("td", class_ = "ColumnLetter", inline = True)
                                trow += tcell

                                if evt_type:
                                    ltr = unicode(evt_type)[0].capitalize()
                                else:
                                    ltr = "&nbsp;"

                                if ltr != prev_letter:
                                    trow.attr = 'class = "BeginLetter BeginType"'
                                    tcell += Html("a", ltr, name = ltr, id_ = ltr,
                                        title = _("Event types beginning with letter " + ltr), inline = True)
                                    prev_letter = ltr
                                else:
                                    tcell += "&nbsp;" 
  
                                # display Event type if first in the list
                                tcell = Html("td", class_="ColumnType",
                                             title=evt_type, inline=True)
                                trow += tcell
                                if first_event:
                                    tcell += evt_type
                                    if trow.attr == "":
                                        trow.attr = 'class = "BeginType"'
                                else:
                                    tcell += "&nbsp;" 

                                # event date
                                tcell = Html("td", class_ = "ColumnDate", inline = True)
                                trow += tcell
                                date = gen.lib.Date.EMPTY
                                if event:
                                    date = event.get_date_object()
                                    if date and date is not gen.lib.Date.EMPTY:
                                        tcell += _dd.display(date)
                                else:
                                    tcell += "&nbsp;"   

                                # GRAMPS ID
                                trow += Html("td", class_ = "ColumnGRAMPSID") + (
                                    self.event_grampsid_link(event_handle, gid, None)
                                    )

                                # Person(s) column
                                tcell = Html("td", class_ = "ColumnPerson")
                                trow += tcell

                                # classname can either be a person or a family
                                first_person = True

                                # get person(s) for ColumnPerson
                                self.complete_people(tcell, first_person, handle_list,
                                                     ppl_handle_list, up =False)

                        _EVENT_DISPLAYED.append( gid )
                        first_event = False
                        datalist.remove(str(event_handle))

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page ut for processing
        # and close the file
        self.XHTMLWriter(eventslistpage, of)

    def _getEventDate(self, event_handle):
        event_date = gen.lib.Date.EMPTY
        event = self.report.database.get_event_from_handle(event_handle)
        if event:
            date = event.get_date_object()
            if date:

                # returns the date in YYYY-MM-DD format
                return gen.lib.Date(date.get_year_calendar("Gregorian"), date.get_month(), date.get_day())

        # return empty date string
        return event_date

    def event_grampsid_link(self, handle, grampsid, up):
        """
        create a hyperlink from event handle, but show grampsid
        """

        url = self.report.build_url_fname_html(handle, "evt", up)

        # return hyperlink to its caller
        return Html("a", grampsid, href = url, title = grampsid, inline = True)

class EventPage(BasePage):
    def __init__(self, report, title, event_handle, ppl_handle_list):
        """
        Creates the individual event page

        @param: title -- is the title of the web pages
        @param: event_handle -- the event handle for the database
        """
        self.dbase_ = report.database

        event = self.dbase_.get_event_from_handle(event_handle)
        if not event:
            return None

        event_media_list = event.get_media_list()
        BasePage.__init__(self, report, title, event.get_gramps_id())

        self.up = True
        subdirs = True
        self.bibli = Bibliography()

        of = self.report.create_file(event_handle, "evt")
        eventpage, head, body = self.write_header(_("Events"))

        # start event detail division
        with Html("div", class_ = "content", id = "EventDetail") as eventdetail:
            body += eventdetail

            thumbnail = self.display_first_image_as_thumbnail(event_media_list, event)
            if thumbnail is not None:
                eventdetail += thumbnail

            # display page title
            evt_type = str(event.get_type())
            title = "%(eventtype)s" % {'eventtype' : evt_type}
            eventdetail += Html("h3", title, inline = True)

            # begin eventdetail table
            with Html("table", class_ = "infolist eventlist") as table:
                eventdetail += table
 
                tbody = Html("tbody")
                table += tbody

                evt_gid = event.get_gramps_id()
                if not self.noid and evt_gid:
                    trow = Html("tr") + (
                        Html("td", _("Gramps ID"), class_ = "ColumnAttribute", inline = True),
                        Html("td", evt_gid, class_ = "ColumnGRAMPSID", inline = True)
                        )
                    tbody += trow
  
                # get event data
                """
                for more information: see get_event_data()
                """ 
                event_data = self.get_event_data(event, event_handle, subdirs, evt_gid)

                for (label, colclass, data) in event_data:
                    if data:
                        trow = Html("tr") + (
                            Html("td", label, class_ = "ColumnAttribute", inline = True),
                            Html('td', data, class_ = "Column" + colclass)
                            )
                        tbody += trow

                trow = Html("tr") + (
                    Html("td", _("Person(s)"), class_ = "ColumnAttribute", inline = True)
                    )
                tbody += trow

                tcell = Html("td", class_ = "ColumnPerson")
                trow += tcell

                # Person(s) field
                handle_list = set(self.dbase_.find_backlink_handles(event_handle,
                    include_classes = ['Family', 'Person'] if int(event.type) in _EVENTMAP else ['Person']))
                first_person = True

                # get person(s) for ColumnPerson
                self.complete_people(tcell, first_person, handle_list, ppl_handle_list)

            # Narrative subsection
            notelist = event.get_note_list()
            notelist = self.display_note_list(notelist)
            if notelist is not None:
                eventdetail += notelist

            # get attribute list
            attrlist = event.get_attribute_list()
            if attrlist:
                attrsection, attrtable = self.display_attribute_header()
                self.display_attr_list(attrlist, attrtable)
                eventdetail += attrsection

            # event source references
            srcrefs = self.display_ind_sources(event)
            if srcrefs is not None:
                eventdetail += srcrefs            

            # display additional images as gallery
            if self.create_media:
                addgallery = self.display_additional_images_as_gallery(event_media_list, event)
                if addgallery:
                    eventdetail += addgallery

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer) 

        # send page out for processing
        # and close the page
        self.XHTMLWriter(eventpage, of)

class MediaPage(BasePage):
    def __init__(self, report, title, handle, src_list, my_media_list, info):
        (prev, next, page_number, total_pages) = info
        self.dbase_ = report.database

        media = self.dbase_.get_object_from_handle(handle)
        # TODO. How do we pass my_media_list down for use in BasePage?
        BasePage.__init__(self, report, title, media.gramps_id)

        # get media rectangles
        _region_items = self.media_ref_rect_regions(handle)

        of = self.report.create_file(handle, "img")
        self.up = True

        self.src_list = src_list
        self.bibli = Bibliography()

        # get media type to be used primarily with "img" tags
        mime_type = media.get_mime_type()
        mtype = gen.mime.get_description(mime_type)

        if mime_type:
            note_only = False
            newpath = self.copy_source_file(handle, media)
            target_exists = newpath is not None
        else:
            note_only = True
            target_exists = False

        copy_thumbnail(self.report, handle, media)
        self.page_title = media.get_description()
        mediapage, head, body = self.write_header("%s - %s" % (_("Media"), self.page_title))

        # if there are media rectangle regions, attach behaviour style sheet
        if _region_items:

            fname = "/".join(["styles", "behaviour.css"])
            url = self.report.build_url_fname(fname, None, self.up)
            head += Html("link", href = url, type = "text/css", media = "screen", rel = "stylesheet")

        # begin MediaDetail division
        with Html("div", class_ = "content", id = "GalleryDetail") as mediadetail:
            body += mediadetail

            # media navigation
            with Html("div", id = "GalleryNav") as medianav: 
                mediadetail += medianav
                if prev:
                    medianav += self.media_nav_link(prev, _("Previous"), True)
                data = _('<strong id = "GalleryCurrent">%(page_number)d</strong> of '
                         '<strong id = "GalleryTotal">%(total_pages)d</strong>' ) % {
                         'page_number' : page_number, 'total_pages' : total_pages }
                medianav += Html("span", data, id = "GalleryPages")
                if next:
                    medianav += self.media_nav_link(next, _("Next"), True)

            # missing media error message
            errormsg = _("The file has been moved or deleted.")

            # begin summaryarea division
            with Html("div", id = "summaryarea") as summaryarea:
                mediadetail += summaryarea
                if mime_type:
                    if mime_type.startswith("image"):
                        if not target_exists:
                            with Html("div", id = "MediaDisplay") as mediadisplay:
                                summaryarea += mediadisplay
                                mediadisplay += Html("span", errormsg, class_ = "MissingImage")  
 
                        else:
                            # Check how big the image is relative to the requested 'initial'
                            # image size. If it's significantly bigger, scale it down to
                            # improve the site's responsiveness. We don't want the user to
                            # have to await a large download unnecessarily. Either way, set
                            # the display image size as requested.
                            orig_image_path = Utils.media_path_full(self.dbase_, media.get_path())
                            (width, height) = ImgManip.image_size(orig_image_path)
                            max_width = self.report.options['maxinitialimagewidth']
                            max_height = self.report.options['maxinitialimageheight']
                            if width != 0 and height != 0:
                                scale_w = (float(max_width)/width) or 1    # the 'or 1' is so that
                                                                           # a max of zero is ignored

                                scale_h = (float(max_height)/height) or 1
                            else:
                                scale_w = 1.0
                                scale_h = 1.0
                            scale = min(scale_w, scale_h, 1.0)
                            new_width = int(width*scale)
                            new_height = int(height*scale)
                            if scale < 0.8:
                                # scale factor is significant enough to warrant making a smaller image
                                initial_image_path = '%s_init.jpg' % os.path.splitext(newpath)[0]
                                size = [new_width, new_height]
                                initial_image_data = ImgManip.resize_to_jpeg_buffer(orig_image_path, size)
                                new_width = size[0] # In case it changed because of keeping the ratio
                                new_height = size[1]
                                if self.report.archive:
                                    filed, dest = tempfile.mkstemp()
                                    os.write(filed, initial_image_data)
                                    os.close(filed)
                                    self.report.archive.add(dest, initial_image_path)
                                else:
                                    filed = open(os.path.join(self.html_dir, initial_image_path), 'w')
                                    filed.write(initial_image_data)
                                    filed.close()
                            else:
                                # not worth actually making a smaller image
                                initial_image_path = newpath

                            # TODO. Convert disk path to URL.
                            url = self.report.build_url_fname(initial_image_path, None, self.up)
                            with Html("div", id="GalleryDisplay", style = 'width: %dpx; height: %dpx' % (new_width, 
                                new_height)) as mediadisplay:
                                summaryarea += mediadisplay

                                # Feature #2634; display the mouse-selectable regions.
                                # See the large block at the top of this function where
                                # the various regions are stored in _region_items
                                if _region_items:
                                    ordered = Html("ol", class_ = "RegionBox")
                                    mediadisplay += ordered
                                    while len(_region_items) > 0:
                                        (name, x, y, w, h, linkurl) = _region_items.pop()
                                        ordered += Html("li", style = "left:%d%%; top:%d%%; width:%d%%; height:%d%%;"
                                            % (x, y, w, h)) + (
                                            Html("a", name, href = linkurl)
                                        )       

                                # display the image
                                if initial_image_path != newpath:
                                    url = self.report.build_url_fname(newpath, 
                                                None, self.up)
                                mediadisplay += Html("a", href = url) + (
                                    Html("img", width = new_width, 
                                         height = new_height, src = url,
                                         alt = html_escape(self.page_title))
                                )
                    else:
                        dirname = tempfile.mkdtemp()
                        thmb_path = os.path.join(dirname, "document.png")
                        if ThumbNails.run_thumbnailer(mime_type,
                                                      Utils.media_path_full(self.dbase_, media.get_path()),
                                                      thmb_path, 320):
                            try:
                                path = self.report.build_path("preview", media.handle)
                                npath = os.path.join(path, media.handle) + ".png"
                                self.report.copy_file(thmb_path, npath)
                                path = npath
                                os.unlink(thmb_path)
                            except EnvironmentError:
                                path = os.path.join("images", "document.png")
                        else:
                            path = os.path.join("images", "document.png")
                        os.rmdir(dirname)

                        with Html("div", id = "GalleryDisplay") as mediadisplay:
                            summaryarea += mediadisplay

                            img_url = self.report.build_url_fname(path, None, self.up)
                            if target_exists:
                                # TODO. Convert disk path to URL
                                url = self.report.build_url_fname(newpath, None, self.up)
                                hyper = Html("a", href = url, title = html_escape(self.page_title)) + (
                                    Html("img", src = img_url, alt = html_escape(self.page_title))
                                    )
                                mediadisplay += hyper
                            else:
                                mediadisplay += Html("span", errormsg, class_ = "MissingImage")  
                else:
                    with Html("div", id = "GalleryDisplay") as mediadisplay:
                        summaryarea += mediadisplay
                        url = self.report.build_url_image("document.png", "images", self.up)
                        mediadisplay += Html("img", src = url, alt = html_escape(self.page_title),
                            title = html_escape(self.page_title))

                # media title
                title = Html("h3", html_escape(self.page_title.strip()), inline = True)
                summaryarea += title

                # begin media table
                with Html("table", class_ = "infolist gallery") as table: 
                    summaryarea += table

                    # GRAMPS ID
                    media_gid = media.gramps_id
                    if not self.noid and media_gid:
                        trow = Html("tr") + (
                            Html("td", GRAMPSID, class_ = "ColumnAttribute", inline = True),
                            Html("td", media_gid, class_ = "ColumnValue", inline = True)
                            )
                        table += trow

                    # mime type
                    if mime_type:   
                        trow = Html("tr") + (
                            Html("td", _("File Type"), class_ = "ColumnAttribute", inline = True),
                            Html("td", mime_type, class_ = "ColumnValue", inline = True)
                            )
                        table += trow

                    # media date
                    date = media.get_date_object()
                    if date and date is not gen.lib.Date.EMPTY:
                        trow = Html("tr") + (
                            Html("td", DHEAD, class_ = "ColumnAttribute", inline = True),
                            Html("td", _dd.display(date), class_ = "ColumnValue", inline = True)
                            )
                        table += trow

            # get media notes
            notelist = self.display_note_list(media.get_note_list() )
            if notelist is not None:
                mediadetail += notelist

            # get attribute list
            attrlist = media.get_attribute_list()
            if attrlist:
                attrsection, attrtable = self.display_attribute_header()
                self.display_attr_list(attrlist, attrtable)
                mediadetail += attrsection

            # get media sources
            srclist = self.display_media_sources(media)
            if srclist is not None:
                mediadetail += srclist

            # get media references 
            reflist = self.display_references(my_media_list)
            if reflist is not None:
                mediadetail += reflist

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(mediapage, of)

    def media_nav_link(self, handle, name, up = False):
        """
        Creates the Media Page Navigation hyperlinks for Next and Prev
        """
        url = self.report.build_url_fname_html(handle, "img", up)
        name = html_escape(name)
        return Html("a", name, name =name, id =name, href =url,  title =name, inline =True)

    def display_media_sources(self, photo):

        map(lambda i: self.bibli.add_reference(
                            self.report.database.get_citation_from_handle(i)), 
            photo.get_citation_list())
        sourcerefs = self.display_source_refs(self.bibli)

        # return source references to its caller
        return sourcerefs

    def copy_source_file(self, handle, photo):
        ext = os.path.splitext(photo.get_path())[1]
        to_dir = self.report.build_path('images', handle)
        newpath = os.path.join(to_dir, handle) + ext

        fullpath = Utils.media_path_full(self.dbase_, photo.get_path())
        if not os.path.isfile(fullpath):
            _WRONGMEDIAPATH.append([ photo.get_gramps_id(), fullpath])
            return None
        try:
            if self.report.archive:
                self.report.archive.add(fullpath, str(newpath))
            else:
                to_dir = os.path.join(self.html_dir, to_dir)
                if not os.path.isdir(to_dir):
                    os.makedirs(to_dir)
                shutil.copyfile(fullpath,
                                os.path.join(self.html_dir, newpath))
            return newpath
        except (IOError, OSError), msg:
            error = _("Missing media object:") +                               \
                     "%s (%s)" % (photo.get_description(), photo.get_gramps_id())
            self.report.user.warn(error, str(msg))
            return None

#################################################
#
#    Creates the Surname List page
#
#################################################
class SurnameListPage(BasePage):

    ORDER_BY_NAME = 0
    ORDER_BY_COUNT = 1

    def __init__(self, report, title, ppl_handle_list, order_by=ORDER_BY_NAME, filename = "surnames"):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        if order_by == self.ORDER_BY_NAME:
            of = self.report.create_file(filename)
            surnamelistpage, head, body = self.write_header(_('Surnames'))
        else:
            of = self.report.create_file("surnames_count")
            surnamelistpage, head, body = self.write_header(_('Surnames by person count'))

        # begin surnames division
        with Html("div", class_ = "content", id = "surnames") as surnamelist:
            body += surnamelist

            # page message
            msg = _( 'This page contains an index of all the '
                           'surnames in the database. Selecting a link '
                           'will lead to a list of individuals in the '
                           'database with this same surname.')
            surnamelist += Html("p", msg, id = "description")

            # add alphabet navigation...
            # only if surname list not surname count
            if order_by == self.ORDER_BY_NAME:
                menu_set = get_first_letters(self.dbase_, ppl_handle_list, _KEYPERSON)
                alpha_nav, menu_set = alphabet_navigation(menu_set)
                if alpha_nav is not None:
                    surnamelist += alpha_nav

            if order_by == self.ORDER_BY_COUNT:
                table_id = 'SortByCount'
            else:
                table_id = 'SortByName'

            # begin surnamelist table and table head 
            with Html("table", class_ = "infolist primobjlist surnamelist", id = table_id) as table:
                surnamelist += table

                thead = Html("thead")
                table += thead

                trow = Html("tr")
                thead += trow

                trow += Html("th", _("Letter"), class_ = "ColumnLetter", inline = True)

                # create table header surname hyperlink 
                fname = self.report.surname_fname + self.ext
                tcell = Html("th", class_ = "ColumnSurname", inline = True)
                trow += tcell
                hyper = Html("a", _("Surname"), href = fname, title = _("Surnames"))
                tcell += hyper

                # create table header number of people hyperlink
                fname = "surnames_count" + self.ext
                tcell = Html("th", class_ = "ColumnQuantity", inline = True)
                trow += tcell
                num_people = _("Number of People")
                hyper = Html("a", num_people, href = fname, title = num_people)
                tcell += hyper

                # begin table body
                with Html("tbody") as tbody:
                    table += tbody

                    ppl_handle_list = sort_people(self.dbase_, ppl_handle_list)
                    if order_by == self.ORDER_BY_COUNT:
                        temp_list = {}
                        for (surname, data_list) in ppl_handle_list:
                            index_val = "%90d_%s" % (999999999-len(data_list), surname)
                            temp_list[index_val] = (surname, data_list)

                        ppl_handle_list = (temp_list[key]
                            for key in sorted(temp_list, key = locale.strxfrm))

                    last_letter = ''
                    last_surname = ''

                    for (surname, data_list) in ppl_handle_list:
                        if len(surname) == 0:
                            continue

                        letter = first_letter(surname)

                        trow = Html("tr")
                        tbody += trow

                        tcell = Html("td", class_ = "ColumnLetter", inline = True)
                        trow += tcell

                        if letter != last_letter:
                            last_letter = letter
                            trow.attr = 'class = "BeginLetter"'

                            hyper = Html("a", last_letter, name = last_letter, 
                                    title = "Surnames with letter " + last_letter, inline = True)
                            tcell += hyper

                        elif surname != last_surname:
                            tcell += "&nbsp;"

                                
                            last_surname = surname

                        trow += Html("td", self.surname_link(name_to_md5(surname), surname), 
                                    class_ = "ColumnSurname", inline = True)

                        trow += Html("td", len(data_list), class_ = "ColumnQuantity", inline = True)

        # create footer section
        # add clearline for proper styling
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(surnamelistpage, of)  

    def surname_link(self, fname, name, opt_val = None, up = False):
        url = self.report.build_url_fname_html(fname, "srn", up)
        hyper = Html("a", name, href = url, title = html_escape(name), inline = True)
        if opt_val is not None:
            hyper += opt_val

        # return hyperlink to its caller
        return hyper

class IntroductionPage(BasePage):
    def __init__(self, report, title):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        of = self.report.create_file(report.intro_fname)
        intropage, head, body = self.write_header(_('Introduction'))

        # begin Introduction division
        with Html("div", class_ = "content", id = "Introduction") as section:
            body += section

            introimg = self.add_image('introimg')
            if introimg is not None:
                section += introimg

            note_id = report.options['intronote']
            if note_id:
                note = self.dbase_.get_note_from_gramps_id(note_id) 
                note_text = self.get_note_format(note, False)
 
                # attach note
                section += note_text

        # add clearline for proper styling
        # create footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(intropage, of)

class HomePage(BasePage):
    def __init__(self, report, title):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        of = self.report.create_file("index")
        homepage, head, body = self.write_header(_('Home'))

        # begin home division
        with Html("div", class_ = "content", id = "Home") as section:
            body += section

            homeimg = self.add_image('homeimg')
            if homeimg is not None:
                section += homeimg

            note_id = report.options['homenote']
            if note_id:
                note = self.dbase_.get_note_from_gramps_id(note_id)
                note_text = self.get_note_format(note, False)

                # attach note
                section += note_text

         # create clear line for proper styling
        # create footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(homepage, of)  

class SourceListPage(BasePage):
    def __init__(self, report, title, handle_set):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        handle_list = list(handle_set)
        source_dict = {}

        of = self.report.create_file("sources")
        sourcelistpage, head, body = self.write_header(_("Sources"))

        # begin source list division
        with Html("div", class_ = "content", id = "Sources") as sourceslist:
            body += sourceslist

            # Sort the sources
            for handle in handle_list:
                source = self.dbase_.get_source_from_handle(handle)
                if source is not None:
                    key = source.get_title() + str(source.get_gramps_id())
                    source_dict[key] = (source, handle)
            
            keys = sorted(source_dict, key=locale.strxfrm)

            msg = _("This page contains an index of all the sources in the "
                         "database, sorted by their title. Clicking on a source&#8217;s "
                         "title will take you to that source&#8217;s page.")
            sourceslist += Html("p", msg, id = "description")

            # begin sourcelist table and table head
            with Html("table", class_ = "infolist primobjlist sourcelist") as table:
                sourceslist += table 
                thead = Html("thead")
                table += thead

                trow = Html("tr")
                thead += trow

                header_row = [
                    (_("Number"),           "ColumnRowLabel"),
                    (_("Source Name|Name"), "ColumnName") ]

                trow.extend(
                    Html("th", label or "&nbsp;", class_ =colclass, inline =True)
                    for (label, colclass) in header_row)
                    
                # begin table body
                tbody = Html("tbody")
                table += tbody

                for index, key in enumerate(keys):
                    source, handle = source_dict[key]

                    trow = Html("tr") + (
                        Html("td", index + 1, class_ ="ColumnRowLabel", inline =True)
                    )
                    tbody += trow
                    trow.extend(
                        Html("td", self.source_link(source, None), class_ ="ColumnName")
                    )

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(sourcelistpage, of)

#################################################
#
#    Creates the individual source pages from SourceListPage
#
#################################################
class SourcePage(BasePage):
    def __init__(self, report, title, source_handle, src_list, ppl_handle_list):
        self.dbase_ = report.database
        source = self.dbase_.get_source_from_handle(source_handle)
        if not source:
            return

        self.page_title = source.get_title()
        BasePage.__init__(self, report, title, source.get_gramps_id())

        inc_events       = self.report.options['inc_events']
        inc_families     = self.report.options['inc_families']
        inc_repositories = self.report.options["inc_repository"]

        of = self.report.create_file(source_handle, "src")
        self.up = True
        sourcepage, head, body = self.write_header(_('Sources'))

        # begin source detail division
        with Html("div", class_ = "content", id = "SourceDetail") as sourcedetail:
            body += sourcedetail

            media_list = source.get_media_list()
            if (self.create_media and media_list):
                thumbnail = self.display_first_image_as_thumbnail(media_list, source)
                if thumbnail is not None:
                    sourcedetail += thumbnail

                    # remove thumbnail from list of media...
                    media_list.remove(media_list[0])

            # add section title
            sourcedetail += Html("h3", html_escape(source.get_title()), inline = True)

            # begin sources table
            with Html("table", class_ = "infolist source") as table:
                sourcedetail += table

                tbody = Html("tbody")
                table += tbody

                source_gid = False 
                if not self.noid and self.gid:
                    source_gid = source.get_gramps_id()

                for (label, value) in [
                    (_("Gramps ID"),               source_gid),
                    (_("Author"),                  source.get_author()),
                    (_("Publication information"), source.get_publication_info()),
                    (_("Abbreviation"),            source.get_abbreviation()) ]:
                    if value:
                        trow = Html("tr") + (
                            Html("td", label, class_ = "ColumnAttribute", inline = True),
                            Html("td", value, class_ = "ColumnValue", inline = True)
                        )
                        tbody += trow

            # Source notes
            notelist = self.display_note_list(source.get_note_list())
            if notelist is not None:
                sourcedetail += notelist

            # additional media from Source (if any?)
            if (self.create_media and media_list):
                sourcemedia = self.display_additional_images_as_gallery(media_list, source)
                if sourcemedia is not None:
                    sourcedetail += sourcemedia

            # Source Data Map...
            src_data_map = self.write_data_map(source.get_data_map())
            if src_data_map is not None:
                sourcedetail += src_data_map

            # Source Repository list
            if inc_repositories:
                repo_list = self.dump_repository_ref_list(source.get_reporef_list())
                if repo_list is not None:
                    sourcedetail += repo_list

            # begin Citation Referents and section title
            with Html("div", class_ ="subsection", id ="SourceCitationReferents") as section:
                sourcedetail += section
                section += Html("h4", _("Citation References"), inline =True)

                # get the Source and its Citation Referents too...
                (citation_list, citation_referents_list) = \
                    Utils.get_source_and_citation_referents(source_handle, self.dbase_)
                for (citation_handle, refs) in citation_referents_list:
                    citation = self.dbase_.get_citation_from_handle(citation_handle)
                    if citation:

                        # ordered list #1, Citation Volume/ Page...
                        ordered1 = Html("ol", class_ = "Col1")
                        section += ordered1

                        # list item 1 cannot be attached until the end.....
                        list1 = Html("li", citation.get_page())

                        (people_list, family_list, event_list, place_list, source_list, media_list, repo_list) = refs

                        # ordered list #2, Object Type...
                        ordered2 = Html("ol", class_ = "Col2 ObjectType")

                        # Citation Referents have Person objects... 
                        if people_list:

                            list2 = Html("li", _("Person(s)"))
                            ordered2 += list2

                            # only add the person handle if the individual is in the report database, and reove any duplication if any?
                            ppl_list = [phandle for phandle in people_list if check_person_database(phandle, ppl_handle_list)]

                            # Sort the person list by  the individual's surname...
                            ppl_list = sort_people(self.dbase_, ppl_list)

                            # ordered list #3, Surname...
                            ordered3 = Html("ol", class_ = "Col3 Surname")

                            displayed = []
                            for (surname, handle_list) in ppl_list:
                                if surname not in displayed:

                                    list3 = Html("li", surname)
                                    ordered3 += list3

                                    # ordered list #4, full name...
                                    ordered4 = Html("ol", class_ = "Col4 FullName")

                                    for handle in handle_list:
                                        individual = self.dbase_.get_person_from_handle(handle)
                                        if individual:

                                            url = self.report.build_url_fname_html(handle, "ppl", up = True)
                                            list4 = Html("li", self.person_link(url, individual, _NAME_STYLE_DEFAULT, 
                                                gid = individual.get_gramps_id()))
                                            ordered4 += list4

                                    list3 += ordered4
                                displayed.append(surname)
                            list2 += ordered3

                        # Citation Referents have Family objects... 
                        if (inc_families and family_list):

                            list2 = Html("li", _("Families"))
                            ordered2 += list2

                            # ordered list, Column 3, Husband and Wife...
                            ordered3 = Html("ol", class_ = "Col3 HusbandSpouse")

                            for handle in family_list:
                                family = self.dbase_.get_family_from_handle(fhandle)
                                if family:

                                    mother_handle = family.get_mother_handle()
                                    father_handle = family.get_father_handle()

                                    if (mother_handle and check_person_database(mother_handle, ppl_handle_list)):
                                        mother = self.dbase_.get_person_from_handle(mother_handle)
                                        if mother:
                                            mother_name = self.get_name(mother)
                                            wlink = self.family_link(handle, mother_name, family.get_gramps_id(), self.up)

                                    if (father_handle and check_person_database(father_handle, ppl_handle_list)):
                                        father = self.dbase_.get_person_from_handle(father_handle)
                                        if father:
                                            father_name = self.get_name(father)
                                            hlink = self.family_link(handle, father_name, family.get_gramps_id(), self.up)

                                    if mother and father:
                                        family_link = "%s %s %s" % (wlink, _("and"), hlink)
                                    elif mother:
                                        family_link = wlink 
                                    elif father:
                                        family_link = hlink
                                    else:
                                                family_link = ''
                                    list3 = family_link
                                    ordered3 += lis3
                            list2 += ordered3

                        # Citation Referents have Event Objects...
                        if (inc_events and event_list):

                            list2 = Html("li", _("Events"))
                            ordered2 += list2

                            # get event handles and types for these events...
                            event_handle_list, event_types = build_event_data_by_events(self.dbase_, event_list)
                            db_event_handles = self.dbase_.get_event_handles()

                            # Ordered list 3, Event Types
                            ordered3 = Html("ol", class_ = "Col3 EventTypes")

                            # separate events by their types and then thier event handles
                            for (etype, handle_list) in sort_event_types(self.dbase_, event_types, event_handle_list):

                                list3 = Html("li", etype)
                                ordered3 += list3

                                # Ordered list4, Event Date...
                                ordered4 = Html("ol", class_ = "Col4 EventDate")

                                for handle in handle_list:
                                   event = self.dbase_.get_event_from_handle(handle)
                                   if (event and handle in db_event_handles):
                                        list4 = Html("li", self.event_link(_dd.display(event.get_date_object()) or etype,
                                                                          handle, event.get_gramps_id(), self.up))
                                        ordered4 += list4
                                list3 += ordered4
                            list2 += ordered3

                        # Citation Referents have Place objects...
                        if place_list:
                            db_place_handles = self.dbase_.iter_place_handles()

                            list2 = Html("li", _("Places"))
                            ordered2 += list2

                            # Column and list 3, Place Link...
                            ordered3 = Html("ol", class_ = "Col3 PlaceLink")

                            for handle in place_list:
                                place = self.dbase_.get_place_from_handle(handle)
                                if (place and handle in db_place_handles):
                                    list3 = Html("li", self.place_link(handle, place.get_title(),
                                                                       place.get_gramps_id(), self.up))
                                    ordered3 += list3
                            list2 += ordered3

                        # Citation Referents has Source Objects...
                        if source_list:
                            db_source_handles = self.dbase_.iter_source_handles()

                            list2 = Html("li", _("Sources"))
                            ordered2 += list2

                            # Column and list 3, Source Link
                            ordered3 = Html("ol", class_ = "Col3 SourceLink")

                            for handle in source_list:
                                source = self.dbase_.get_source_from_handle(handle)
                                if (source and handle in db_source_handles):
                                    list3 = Html("li", self.source_link(source, up = self.up))
                                    ordered3 += list3
                            list2 += ordered3

                        # Citation Referents have Media Objects...
                        if (self.create_media and media_list):

                            list2 = Html("li", _("Media"))
                            ordered2 += list2

                            # Column and list 3, Media Link
                            ordered3 = Html("ol", class_ = "Col3 MediaLink")

                            for handle in media_list:
                                media = self.dbase_.get_object_from_handle(handle)
                                if media:

                                    mime_type = media.get_mime_type()
                                    if mime_type:
                                        try:
                                            real_path, newpath = self.report.prepare_copy_media(media)
                                            newpath = self.report.build_url_fname(newpath, up = True)

                                            list3 = Html("li", self.media_link(handle, newpath, media.get_description(),
                                                                               self.up, True))
                                        except:
                                            list3 += _("Media error...")
                                    else:
                                        try:
                                            list3 = Html("li", self.doc_link(handle, media.get_description(),
                                                                             self.up, True))
                                        except:
                                            list3 += _("Media error...")
                                    ordered3 += list3
                                list2 += ordered3

                        # Citation Referents have Repository Objects...
                        if (inc_repositories and repo_list):

                            list2 = Html("li", _("Repositories"))
                            ordered2 += list2

                            # Column and list 3, Repository Link...
                            ordered3 = tml("ol", class_ = "Col3 RepositoryLink")

                            for handle in repo_list:
                                repository = self.dbase_.get_repository_from_handle(handle)
                                if repository:
                                    list3 = Html("li", self.repository_link(handle, repository.get_name(),
                                                                            repository.get_gramps_id(), self.up))
                                    ordered3 += list3
                            list2 += ordered3

                        # these two are common to all of these seven object types...
                        list1 += ordered2
                        ordered1 += list1

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(sourcepage, of)

class MediaListPage(BasePage):
    def __init__(self, report, title):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        of = self.report.create_file("media")
        media_listpage, head, body = self.write_header(_('Media'))

        # begin gallery division
        with Html("div", class_ = "content", id = "Gallery") as media_list:
            body += media_list

            msg = _("This page contains an index of all the media objects "
                          "in the database, sorted by their title. Clicking on "
                          "the title will take you to that media object&#8217;s page.  "
                          "If you see media size dimensions above an image, click on the "
                          "image to see the full sized version.  ")
            media_list += Html("p", msg, id = "description")

            # begin gallery table and table head
            with Html("table", class_ = "infolist primobjlist gallerylist") as table:
                media_list += table

                # begin table head
                thead = Html("thead")
                table += thead

                trow = Html("tr")
                thead += trow

                trow.extend(
                    Html("th", trans, class_ =colclass, inline =True)
                    for trans, colclass in [
                        ["&nbsp;",          "ColumnRowLabel"],
                        [_("Media | Name"), "ColumnName"],
                        [_("Date"),         "ColumnDate"],
                        [_("Mime Type"),    "ColumnMime"] ]
                )
  
                # begin table body
                tbody = Html("tbody")
                table += tbody

                index = 1
                sort = Sort.Sort(self.dbase_)
                mlist = sorted(self.report.photo_list, key=sort.by_media_title_key)
        
                for handle in mlist:
                    media = self.dbase_.get_object_from_handle(handle)
                    if media:
                        title = media.get_description() or "[untitled]"

                        trow = Html("tr")
                        tbody += trow

                        media_data_row = [
                            [index,                                 "ColumnRowLabel"],
                            [self.media_ref_link(handle, title),    "ColumnName"],
                            [_dd.display(media.get_date_object() ), "ColumnDate"],
                            [media.get_mime_type(),                 "ColumnMime"] ]

                        trow.extend(
                            Html("td", data, class_ = colclass)
                                for data, colclass in media_data_row
                        )  
                        index += 1

        # add footer section
        # add clearline for proper styling
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(media_listpage, of)

    def media_ref_link(self, handle, name, up = False):

        # get media url
        url = self.report.build_url_fname_html(handle, "img", up)

        # get name
        name = html_escape(name)

        # begin hyper link
        hyper = Html("a", name, href = url, title = name)

        # return hyperlink to its callers
        return hyper

class ThumbnailPreviewPage(BasePage):
    def __init__(self, report, title, cb_progress):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)
        self.create_thumbs_only = report.options['create_thumbs_only']

        sort = Sort.Sort(self.dbase_)
        self.photo_keys = sorted(self.report.photo_list, key =sort.by_media_title_key)
        if not self.photo_keys:
            return

        media_list = []
        for phandle in self.photo_keys:
            photo = self.dbase_.get_object_from_handle(phandle)
            if photo:
                if photo.get_mime_type().startswith("image"):
                    media_list.append((photo.get_description(), phandle, photo))

                    if self.create_thumbs_only:
                        copy_thumbnail(self.report, phandle, photo)

        if not media_list:
            return
        media_list.sort()

        # reate thumbnail preview page...
        of = self.report.create_file("thumbnails")
        thumbnailpage, head, body = self.write_header(_("Thumbnails"))

        with Html("div", class_ ="content", id ="Preview") as previewpage:
            body += previewpage

            msg = _("This page displays a indexed list of all the media objects "
                "in this database.  It is sorted by media title.  There is an index "
                "of all the media objects in this database.  Clicking on a thumbnail "
                "will take you to that image&#8217;s page.")
            previewpage += Html("p", msg, id ="description")

            with Html("table", class_ ="calendar") as table:
                previewpage += table

                thead = Html("thead")
                table += thead

                # page title...
                trow = Html("tr")
                thead += trow

                trow += Html("th", _("Thumbnail Preview"), class_ ="monthName", colspan=7, inline =True)
 
                # table header cells...
                trow = Html("tr")
                thead += trow

                ltrs = ["G", "r", "a", "m", "p", "s", "3.4.0"]
                for ltr in ltrs:
                    trow += Html("th", ltr, class_ ="weekend", inline =True) 

                tbody = Html("tbody")
                table += tbody

                index, indexpos = 1, 0
                num_of_images = len(media_list)
                num_of_rows = ((num_of_images // 7) +  1)
                num_of_cols = 7
                grid_row = 0
                while grid_row < num_of_rows:
                    trow = Html("tr", id ="RowNumber: %08d" % grid_row)
                    tbody += trow

                    cols = 0
                    while (cols < num_of_cols and indexpos < num_of_images):
                        ptitle = media_list[indexpos][0]
                        phandle = media_list[indexpos][1]
                        photo = media_list[indexpos][2]

                        # begin table cell and attach to table row(trow)...
                        tcell = Html("td", class_ ="highlight weekend")
                        trow += tcell
  
                        # attach index number...
                        numberdiv = Html("div", class_ ="date")
                        tcell += numberdiv

                        # attach anchor name to date cell in upper right corner of grid...
                        numberdiv += Html("a", index, name =index, title =index, inline =True)

                        # begin unordered list and attach to table cell(tcell)...
                        unordered = Html("ul")
                        tcell += unordered  

                        # create thumbnail 
                        real_path, newpath = self.report.prepare_copy_media(photo)
                        newpath = self.report.build_url_fname(newpath)

                        list = Html("li")
                        unordered += list

                        # attach thumbnail to list...
                        list += self.thumb_hyper_image(newpath, "img", phandle, ptitle)

                        index += 1
                        indexpos += 1
                        cols += 1
                    grid_row += 1

        # if last row is incomplete, finish it off?
        if (grid_row == num_of_rows and cols < num_of_cols):
            for emptyCols in range(cols, num_of_cols):
                trow += Html("td", class_ ="emptyDays", inline =True)
 
        # begin Thumbnail Reference section...
        with Html("div", class_ ="subsection", id ="references") as section:
            body += section
            section += Html("h4", _("References"), inline =True)

            with Html("table", class_ ="infolist") as table:
                section += table

                tbody = Html("tbody")
                table += tbody 

                index = 1
                for ptitle, phandle, photo in media_list:
                    trow = Html("tr")
                    tbody += trow

                    tcell1 = Html("td", self.thumbnail_link(ptitle, index), class_ ="ColumnRowLabel")
                    tcell2 = Html("td", ptitle, class_ ="ColumnName")
                    trow += (tcell1, tcell2)

                    # increase index for row number...                    
                    index += 1

                    # increase progress meter...
                    cb_progress()

        # add body id element
        body.attr = 'id ="ThumbnailPreview"'

        # add footer section
        # add clearline for proper styling
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(thumbnailpage, of)

    def thumbnail_link(self, name, index):
        """
        creates a hyperlink for Thumbnail Preview Reference...
        """
        return Html("a", index, title =html_escape(name), href ="#%d" % index)

    def thumb_hyper_image(self, thumbnailUrl, subdir, fname, name):
        """
        eplaces media_link() because it doesn't work for this instance
        """
        name = html_escape(name)
        url = "/".join(self.report.build_subdirs(subdir, fname) + [fname]) + self.ext

        with Html("div", class_ ="content", id ="ThumbnailPreview") as section:
            with Html("div", class_="snapshot") as snapshot:
                section += snapshot

                with Html("div", class_ ="thumbnail") as thumbnail:
                    snapshot += thumbnail

                    if not self.create_thumbs_only:
                        thumbnail_link = Html("a", href =url, title =name) + (
                            Html("img", src =thumbnailUrl, alt =name)
                        )
                    else:
                        thumbnail_link = Html("img", src =thumbnailUrl, alt =name)
                    thumbnail += thumbnail_link
        return section

class DownloadPage(BasePage):
    def __init__(self, report, title):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        # do NOT include a Download Page
        if not self.report.inc_download:
            return

        # menu options for class
        # download and description #1

        dlfname1 = self.report.dl_fname1
        dldescr1 = self.report.dl_descr1

        # download and description #2
        dlfname2 = self.report.dl_fname2
        dldescr2 = self.report.dl_descr2

        # if no filenames at all, return???
        if dlfname1 or dlfname2:

            of = self.report.create_file("download")
            downloadpage, head, body = self.write_header(_('Download'))

            # begin download page and table
            with Html("div", class_ = "content", id = "Download") as download:
                body += download

                msg = _("This page is for the user/ creator of this Family Tree/ "
                    "Narrative website to share a couple of files with you "
                    "regarding their family.  If there are any files listed "
                    "below, clicking on them will allow you to download them. The "
                    "download page and files have the same copyright as the remainder "
                    "of these web pages.")
                download += Html("p", msg, id = "description")

                # begin download table and table head
                with Html("table", class_ = "infolist download") as table:
                    download += table

                    thead = Html("thead")
                    table += thead

                    trow = Html("tr")
                    thead += trow

                    trow.extend(
                        Html("th", label, class_ = "Column" + colclass, inline = True)
                        for (label, colclass) in [
                            (_("File Name"),     "Filename"),
                            (DESCRHEAD,          "Description"),
                            (_("Last Modified"), "Modified") ]
                            ) 
                    # table body
                    tbody = Html("tbody")
                    table += tbody

                    # if dlfname1 is not None, show it???
                    if dlfname1:

                        trow = Html("tr", id = 'Row01')
                        tbody += trow

                        fname = os.path.basename(dlfname1)
                        # TODO dlfname1 is filename, convert disk path to URL 
                        tcell = Html("td", class_ = "ColumnFilename") + (
                            Html("a", fname, href = dlfname1, title = html_escape(dldescr1))
                        )
                        trow += tcell

                        dldescr1 = dldescr1 or "&nbsp;"
                        trow += Html("td", dldescr1, class_ = "ColumnDescription", inline = True)

                        tcell = Html("td", class_ = "ColumnModified", inline = True)
                        trow += tcell 
                        if os.path.exists(dlfname1):
                            modified = os.stat(dlfname1).st_mtime
                            last_mod = datetime.datetime.fromtimestamp(modified)
                            tcell += last_mod
                        else:
                            tcell += "&nbsp;"

                    # if download filename #2, show it???
                    if dlfname2:

                        # begin row #2
                        trow = Html("tr", id = 'Row02')
                        tbody += trow

                        fname = os.path.basename(dlfname2)
                        tcell = Html("td", class_ = "ColumnFilename") + (
                            Html("a", fname, href = dlfname2, title = html_escape(dldescr2))
                        )  
                        trow += tcell

                        dldescr2 = dldescr2 or "&nbsp;"
                        trow += Html("td", dldescr2, class_ = "ColumnDescription", inline = True)

                        tcell = Html("td", id = 'Col04', class_ = "ColumnModified",  inline = True)
                        trow += tcell
                        if os.path.exists(dlfname2):
                            modified = os.stat(dlfname2).st_mtime
                            last_mod = datetime.datetime.fromtimestamp(modified)
                            tcell += last_mod
                        else:
                            tcell += "&nbsp;"

        # clear line for proper styling
        # create footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(downloadpage, of)

class ContactPage(BasePage):
    def __init__(self, report, title):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        of = self.report.create_file("contact")
        contactpage, head, body = self.write_header(_('Contact'))

        # begin contact division
        with Html("div", class_ = "content", id = "Contact") as section:
            body += section 

            # begin summaryarea division
            with Html("div", id = 'summaryarea') as summaryarea:
                section  += summaryarea

                contactimg = self.add_image('contactimg', 200)
                if contactimg is not None:
                    summaryarea += contactimg

                # get researcher information
                r = Utils.get_researcher()

                with Html("div", id = 'researcher') as researcher:
                    summaryarea += researcher

                    if r.name:
                        r.name = r.name.replace(',,,', '')
                        researcher += Html("h3", r.name, inline = True)
                    if r.addr:
                        researcher += Html("span", r.addr, id = 'streetaddress', inline = True)
                    if r.locality:
                        researcher += Html("span", r.locality, id = "locality", inline = True)
                    text = "".join([r.city, r.state, r.postal])
                    if text:
                        city = Html("span", r.city, id = 'city', inline = True)
                        state = Html("span", r.state, id = 'state', inline = True)
                        postal = Html("span", r.postal, id = 'postalcode', inline = True)
                        researcher += (city, state, postal)
                    if r.country:
                        researcher += Html("span", r.country, id = 'country', inline = True)
                    if r.email:
                        researcher += Html("span", id = 'email') + (
                            Html("a", r.email, href = 'mailto:%s' % r.email, inline = True)
                        )

                    # add clear line for proper styling
                    summaryarea += fullclear

                    note_id = report.options['contactnote']
                    if note_id:
                        note = self.dbase_.get_note_from_gramps_id(note_id)
                        note_text = self.get_note_format(note, False)
 
                        # attach note
                        summaryarea += note_text

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for porcessing
        # and close the file
        self.XHTMLWriter(contactpage, of)

#################################################
#
#    creates the Individual Pages from the IndividualListPage
#
#################################################
class IndividualPage(BasePage):
    gender_map = {
        gen.lib.Person.MALE    : _('male'),
        gen.lib.Person.FEMALE  : _('female'),
        gen.lib.Person.UNKNOWN : _('unknown'),
        }

    def __init__(self, report, title, person, ind_list, place_list, src_list, place_lat_long):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title, person.get_gramps_id())

        self.person = person
        self.ind_list = ind_list
        self.src_list = src_list        # Used by get_citation_links()
        self.bibli = Bibliography()
        self.place_list = place_list
        self.sort_name = self.get_name(person)
        self.name = self.get_name(person)

        self.familymappages = self.report.options['familymappages']
        self.placemappages = self.report.options['placemappages']
        self.mapservice = self.report.options['mapservice']
        self.googleopts = self.report.options['googleopts']

        of = self.report.create_file(person.get_handle(), "ppl")
        self.up = True
        indivdetpage, head, body = self.write_header(self.sort_name)

        # attach the ancestortree style sheet if ancestor graph is being created?
        if self.report.options["ancestortree"]:
            fname = "/".join(["styles", "ancestortree.css"])
            url = self.report.build_url_fname(fname, None, self.up)
            head += Html("link", href = url, type = "text/css", media = "screen", rel = "stylesheet")

        # begin individualdetail division
        with Html("div", class_ = "content", id = 'IndividualDetail') as individualdetail:
            body += individualdetail

            # display a person's general data
            thumbnail, name, summary = self.display_ind_general()
            if thumbnail is not None:
                individualdetail += thumbnail
            individualdetail += (name, summary)

            # display a person's events
            sect2 = self.display_ind_events(place_lat_long)
            if sect2 is not None:
                individualdetail += sect2

            # display parents
            sect3 = self.display_ind_parents(ind_list)
            if sect3 is not None:
                individualdetail += sect3

            # display relationships
            relationships = self.display_relationships(self.person, ind_list, place_lat_long)
            if relationships is not None:
                individualdetail += relationships

            # display LDS ordinance
            sect5 = self.display_lds_ordinance(self.person)
            if sect5 is not None:
                individualdetail += sect5

            # display address(es) and show sources
            sect6 = self.display_addr_list(self.person.get_address_list(), True)
            if sect6 is not None:
                individualdetail += sect6

            photo_list = self.person.get_media_list()
            media_list = photo_list[:]

            # if Family Pages are not being created, then include the Family Media objects?
            # there is no reason to add these objects to the Individual Pages...
            if not self.inc_families:
                for handle in self.person.get_family_handle_list():
                    family = self.dbase_.get_family_from_handle(handle)
                    if family:
                        media_list += family.get_media_list()
                        for evt_ref in family.get_event_ref_list():
                            event = self.dbase_.get_event_from_handle(evt_ref.ref)
                            media_list += event.get_media_list()

            # if the Event Pages are not being createsd, then include the Event Media objects?
            # there is no reason to add these objects to the Individual Pages...
            if not self.inc_events:
                for evt_ref in self.person.get_primary_event_ref_list():
                    event = self.dbase_.get_event_from_handle(evt_ref.ref)
                    if event:
                        media_list += event.get_media_list()

            # display additional images as gallery
            sect7 = self.display_additional_images_as_gallery(media_list, person)
            if sect7 is not None:
                individualdetail += sect7

            # display Narrative Notes
            notelist = person.get_note_list()
            sect8 = self.display_note_list(notelist)
            if sect8 is not None:
                individualdetail += sect8

            # display attributes
            attrlist = person.get_attribute_list()
            if attrlist: 
                attrsection, attrtable = self.display_attribute_header()
                self.display_attr_list(attrlist, attrtable)
                individualdetail += attrsection

            # display web links
            sect10 = self.display_url_list(self.person.get_url_list())
            if sect10 is not None:
                individualdetail += sect10

            # display associations
            assocs = person.get_person_ref_list()
            if assocs:
                individualdetail += self.display_ind_associations(assocs)

            # for use in family map pages...
            if len(place_lat_long):
                if self.report.options["familymappages"]:
                    individualdetail += self.__display_family_map(person, place_lat_long)

            # display pedigree
            sect13 = self.display_ind_pedigree()
            if sect13 is not None:
                individualdetail += sect13

            # display ancestor tree  
            if report.options['ancestortree']:
                sect14 = self.display_tree()
                if sect14 is not None:
                    individualdetail += sect14

            # display source references
            sect14 = self.display_ind_sources(person)
            if sect14 is not None:
                individualdetail += sect14

        # add clearline for proper styling
        # create footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(indivdetpage, of)

    def __create_family_map(self, person, place_lat_long):
        """
        creates individual family map page

        @param: person -- person from database
        @param: place_lat_long -- for use in Family Map Pages
        """
        if not place_lat_long:
            return

        of = self.report.create_file(person.get_handle(), "maps")
        self.up = True
        familymappage, head, body = self.write_header(_("Family Map"))

        minx, maxx = Decimal("0.00000001"), Decimal("0.00000001")
        miny, maxy = Decimal("0.00000001"), Decimal("0.00000001")
        xwidth, yheight = [], []
        midX_, midY_, spanx, spany = [None]*4

        number_markers = len(place_lat_long)
        if number_markers > 1:
            for (latitude, longitude, placetitle, handle, date, etype) in place_lat_long:
                xwidth.append(latitude)
                yheight.append(longitude)
            xwidth.sort()
            yheight.sort()

            minx = xwidth[0] if xwidth[0] else minx
            maxx = xwidth[-1] if xwidth[-1] else maxx
            minx, maxx = Decimal(minx), Decimal(maxx)
            midX_ = str( Decimal( (minx + maxx) /2) )

            miny =  yheight[0] if yheight[0] else miny
            maxy = yheight[-1] if yheight[-1] else maxy
            miny, maxy = Decimal(miny), Decimal(maxy)
            midY_ = str( Decimal( (miny + maxy) /2) )

            midX_, midY_ = conv_lat_lon(midX_, midY_, "D.D8")

            # get the integer span of latitude and longitude
            spanx = int(maxx - minx)
            spany = int(maxy - miny)

        # set zoom level based on span of Longitude?
        tinyset = [value for value in (-3, -2, -1, 0, 1, 2, 3)]
        smallset = [value for value in (-4, -5, -6, -7, 4, 5, 6, 7)]
        middleset = [value for value in (-8, -9, -10, -11, 8, 9, 10, 11)]
        largeset = [value for value in (-11, -12, -13, -14, -15, -16, -17, 11, 12, 13, 14, 15, 16, 17)]

        if (spany in tinyset or spany in smallset):
            zoomlevel = 6
        elif spany in middleset:
            zoomlevel = 5
        elif spany in largeset:
            zoomlevel = 4
        else:
            zoomlevel = 3 

        # 0 = latitude, 1 = longitude, 2 = place title, 3 = handle, and 4 = date, 5 = event type...
        # being sorted by date, latitude, and longitude...
        place_lat_long = sorted(place_lat_long, key =operator.itemgetter(4, 0, 1))

        # for all plugins
        # if family_detail_page
        # if active
        # call_(report, up, head)

        # add narrative-maps style sheet
        fname = "/".join(["styles", "narrative-maps.css"])
        url = self.report.build_url_fname(fname, None, self.up)
        head += Html("link", href =url, type ="text/css", media ="screen", rel ="stylesheet")

        # add MapService specific javascript code
        if self.mapservice == "Google":
            head += Html("script", type ="text/javascript",
                src ="http://maps.googleapis.com/maps/api/js?sensor=false", inline =True)
        else:
            head += Html("script", type ="text/javascript",
                src ="http://www.openlayers.org/api/OpenLayers.js", inline =True)

        if number_markers > 1:
            tracelife = "["
            seq_ = 1

            for index in xrange(0, (number_markers - 1)):
                latitude, longitude, placetitle, handle, date, etype = place_lat_long[index]

                # are we using Google?
                if self.mapservice == "Google":

                    # are we creating Family Links?
                    if self.googleopts == "FamilyLinks":
                        tracelife += """
    new google.maps.LatLng(%s, %s),""" % (latitude, longitude)

                    # are we creating Drop Markers or Markers?
                    elif self.googleopts in ["Drop", "Markers"]:
                        tracelife += """
    ['%s', %s, %s, %d],""" % (placetitle, latitude, longitude, seq_)

                # are we using OpenStreetMap?
                else:
                    tracelife += """
    [%s, %s],""" % (longitude, latitude)
                seq_ += 1
            latitude, longitude, placetitle, handle ,date, etype = place_lat_long[-1]

            # are we using Google?
            if self.mapservice == "Google":

                # are we creating Family Links?
                if self.googleopts == "FamilyLinks":
                    tracelife += """
    new google.maps.LatLng(%s, %s)
  ];""" % (latitude, longitude)

                # are we creating Drop Markers or Markers?
                elif self.googleopts in ["Drop", "Markers"]:
                    tracelife += """
    ['%s', %s, %s, %d]
  ];""" % (placetitle, latitude, longitude, seq_)

            # are we using OpenStreetMap?
            elif self.mapservice == "OpenStreetMap":
                tracelife += """
    [%s, %s]
  ];""" % (longitude, latitude)

        # begin MapDetail division...
        with Html("div", class_ ="content", id ="FamilyMapDetail") as mapdetail:
            body += mapdetail

            # add page title
            mapdetail += Html("h3", html_escape("Tracking %s" %
                                  self.get_name(person)), inline=True)

            # page description
            msg = _("This map page represents the person and their descendants with "
                    "all of their event/ places.  If you place your mouse over "
                    "the marker it will display the place name.  The markers and the Reference "
                    "list are sorted in date order (if any?).  Clicking on a place&#8217;s "
                    "name in the Reference section will take you to that place&#8217;s page.") 
            mapdetail += Html("p", msg, id = "description")

            # this is the style element where the Map is held in the CSS...
            with Html("div", id ="map_canvas") as canvas:
                mapdetail += canvas

                # begin javascript inline code...
                with Html("script", deter ="deter", style = 'width =100%; height =100%;',
                                                    type ="text/javascript", indent =False) as jsc:
                    head += jsc

                    # if there is only one marker?
                    if number_markers == 1:
                        latitude, longitude, placetitle, handle, date, etype = place_lat_long[0]

                        # are we using Google?
                        if self.mapservice == "Google":
                            jsc += google_jsc % (latitude, longitude, placetitle)

                        # we are using OpenStreetMap?
                        else:
                            jsc += openstreetmap_jsc % (Utils.xml_lang()[3:5].lower(), longitude, latitude)

                    # there is more than one marker...
                    else:

                        # are we using Google?
                        if self.mapservice == "Google":

                            # are we creating Family Links?
                            if self.googleopts == "FamilyLinks":
                                jsc += familylinks % (tracelife, midX_, midY_, zoomlevel)

                            # are we creating Drop Markers?
                            elif self.googleopts == "Drop":
                                jsc += dropmarkers  % (tracelife, zoomlevel)

                            # we are creating Markers only...
                            else:
                                jsc += markers % (tracelife, zoomlevel)

                        # we are using OpenStreetMap...
                        else:
                            jsc += osm_markers % (Utils.xml_lang()[3:5].lower(), tracelife, midY_, midX_, zoomlevel)

            # if Google and Drop Markers are selected, then add "Drop Markers" button?
            if (self.mapservice == "Google" and self.googleopts == "Drop"):
                mapdetail += Html("button", _("Drop Markers"), id ="drop", onclick ="drop()", inline =True)

            # begin place reference section and its table...
            with Html("div", class_ ="subsection", id ="references") as section:
                mapdetail += section
                section += Html("h4", _("References"), inline =True)

                with Html("table", class_ ="infolist") as table:
                    section += table

                    thead = Html("thead")
                    table += thead

                    trow = Html("tr")
                    thead += trow

                    trow.extend(
                        Html("th", label, class_ =colclass, inline =True)
                            for (label, colclass) in [
                                (_("Date"),        "ColumnDate"),
                                (_("Place Title"), "ColumnPlace"),
                                (_("Event Type"),  "ColumnType")
                            ]
                    )

                    tbody = Html("tbody")
                    table += tbody
    
                    for (latitude, longitude, placetitle, handle, date, etype) in place_lat_long:
                        trow = Html("tr")
                        tbody += trow

                        trow.extend(
                            Html("td", data, class_ =colclass, inline =True)
                                for data, colclass in [
                                    (date,                                          "ColumnDate"),
                                    (self.place_link(handle, placetitle, up =True), "ColumnPlace"),
                                    (str(etype),                                    "ColumnType")
                                ]
                        )
                        
        # add body id for this page...
        body.attr = 'id ="FamilyMap" onload ="initialize()"'

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(familymappage, of)

    def __display_family_map(self, person, place_lat_long):
        """
        create the family map link
        """
        # create family map page
        self.__create_family_map(person, place_lat_long)

        # begin family map division plus section title
        with Html("div", class_ = "subsection", id = "familymap") as familymap:
            familymap += Html("h4", _("Family Map"), inline = True)

            # add family map link
            person_handle = person.get_handle()
            url = self.report.build_url_fname_html(person_handle, "maps", True)
            familymap += self.family_map_link(person_handle, url)

        # return family map link to its caller
        return familymap

    def draw_box(self, center, col, person):
        """
        draw the box around the AncestorTree Individual name box...
        """
        top = center - _HEIGHT/2
        xoff = _XOFFSET+col*(_WIDTH+_HGAP)
        sex = person.gender
        if sex == gen.lib.Person.MALE:
            divclass = "male"
        elif sex == gen.lib.Person.FEMALE:
            divclass = "female"
        else:
            divclass = "unknown"
            
        boxbg = Html("div", class_ = "boxbg %s AncCol%s" % (divclass, col),
                    style="top: %dpx; left: %dpx;" % (top, xoff+1)
                   )
                      
        person_name = self.get_name(person)
        use_link = check_person_database(person.get_handle(), self.ind_list)
        if use_link:
            thumbnailUrl = None
            if self.create_media and col < 5:
                photolist = person.get_media_list()
                if photolist:
                    photo_handle = photolist[0].get_reference_handle()
                    photo = self.dbase_.get_object_from_handle(photo_handle)
                    mime_type = photo.get_mime_type()
                    if mime_type:
                        region = self.media_ref_region_to_object(photo_handle, person)
                        if region:
                            # make a thumbnail of this region
                            newpath = copy_thumbnail(self.report, photo_handle, photo, region)
                            # TODO. Check if build_url_fname can be used.
                            newpath = "/".join(['..']*3 + [newpath])
                            if constfunc.win():
                                newpath = newpath.replace('\\',"/")
                            thumbnailUrl = newpath
                            #snapshot += self.media_link(photo_handle, newpath, '', up = True)

                        else:
                            (photoUrl, thumbnailUrl) = self.report.prepare_copy_media(photo)
                            thumbnailUrl = "/".join(['..']*3 + [thumbnailUrl])
                            if constfunc.win():
                                thumbnailUrl = thumbnailUrl.replace('\\',"/")
            url = self.report.build_url_fname_html(person.handle, "ppl", True)
            boxbg += self.person_link(url, person, name_style = True, thumbnailUrl = thumbnailUrl)
        else:
            boxbg += Html("span", person_name, class_ = "unlinked", inline = True)
        shadow = Html("div", class_ = "shadow", inline = True, style="top: %dpx; left: %dpx;"
            % (top + _SHADOW, xoff + _SHADOW))

        return [boxbg, shadow]

    def extend_line(self, y0, x0):
        style = "top: %dpx; left: %dpx; width: %dpx"
        bv = Html("div", class_ = "bvline", inline = True,
                      style = style % (y0, x0, _HGAP/2)
                    )
        gv = Html("div", class_ = "gvline", inline = True,
                      style = style % (y0+_SHADOW, x0, _HGAP/2+_SHADOW)
                    )  
        return [bv, gv]

    def connect_line(self, y0, y1, col):
        y = min(y0, y1)
        stylew = "top: %dpx; left: %dpx; width: %dpx;"
        styleh = "top: %dpx; left: %dpx; height: %dpx;"
        x0 = _XOFFSET + col * _WIDTH + (col-1)*_HGAP + _HGAP/2
        bv = Html("div", class_ = "bvline", inline = True, style=stylew % (y1, x0, _HGAP/2))
        gv = Html("div", class_ = "gvline", inline = True, style=stylew % 
            (y1+_SHADOW, x0+_SHADOW, _HGAP/2+_SHADOW))
        bh = Html("div", class_ = "bhline", inline = True, style=styleh % (y, x0, abs(y0-y1)))
        gh = Html("div", class_ = "gvline", inline = True, style=styleh %
                 (y+_SHADOW, x0+_SHADOW, abs(y0-y1)))
        return [bv, gv, bh, gh]

    def draw_connected_box(self, center1, center2, col, handle):
        """
        draws the connected box for Ancestor Tree on the Individual Page
        """
        box = []
        if not handle:
            return box
        person = self.dbase_.get_person_from_handle(handle)
        box = self.draw_box(center2, col, person)
        box += self.connect_line(center1, center2, col)
        return box

    def display_tree(self):
        tree = []
        if not self.person.get_main_parents_family_handle():
            return None

        generations = self.report.options['graphgens']
        max_in_col = 1 << (generations-1)
        max_size = _HEIGHT*max_in_col + _VGAP*(max_in_col+1)
        center = int(max_size/2)

        with Html("div", id = "tree", class_ = "subsection") as tree:
            tree += Html("h4", _('Ancestors'), inline = True)
            with Html("div", id = "treeContainer",
                    style="width:%dpx; height:%dpx;" %
                        (_XOFFSET+(generations)*_WIDTH+(generations-1)*_HGAP, 
                        max_size)
                     ) as container:
                tree += container
                container += self.draw_tree(1, generations, max_size, 
                                            0, center, self.person.handle)
        return tree

    def draw_tree(self, gen_nr, maxgen, max_size, old_center, new_center, phandle):
        """
        draws the Abcestor Tree
        """
        tree = []
        if gen_nr > maxgen:
            return tree
        gen_offset = int(max_size / pow(2, gen_nr+1))
        person = self.dbase_.get_person_from_handle(phandle)
        if not person:
            return tree

        if gen_nr == 1:
            tree = self.draw_box(new_center, 0, person)
        else:
            tree = self.draw_connected_box(old_center, new_center, gen_nr-1, phandle)

        if gen_nr == maxgen:
            return tree

        family_handle = person.get_main_parents_family_handle()
        if family_handle:
            line_offset = _XOFFSET + gen_nr*_WIDTH + (gen_nr-1)*_HGAP
            tree += self.extend_line(new_center, line_offset)

            family = self.dbase_.get_family_from_handle(family_handle)

            f_center = new_center-gen_offset
            f_handle = family.get_father_handle()
            tree += self.draw_tree(gen_nr+1, maxgen, max_size, 
                                   new_center, f_center, f_handle)

            m_center = new_center+gen_offset
            m_handle = family.get_mother_handle()
            tree += self.draw_tree(gen_nr+1, maxgen, max_size, 
                                   new_center, m_center, m_handle)
        return tree

    def display_ind_associations(self, assoclist):
        """
        display an individual's associations
        """

        # begin Associations division  
        with Html("div", class_ = "subsection", id = "Associations") as section:
            section += Html("h4", _('Associations'), inline = True)

            with Html("table", class_ = "infolist assoclist") as table:
                section += table

                thead = Html("thead")
                table += thead

                trow = Html("tr")
                thead += trow

                assoc_row = [
                    (_("Person"),       'Person'),
                    (_('Relationship'), 'Relationship'),
                    (NHEAD,             'Notes'),
                    (SHEAD,             'Sources'),
                    ]

                trow.extend(
                    Html("th", label, class_="Column" + colclass, inline=True)
                    for (label, colclass) in assoc_row)

                tbody = Html("tbody")
                table += tbody

                for person_ref in assoclist:
                    if person_ref.ref not in self.report.person_handles:
                        continue # TODO why skip persons?
                    trow = Html("tr")
                    tbody += trow

                    person = self.report.database.get_person_from_handle(person_ref.ref)
                    url = self.report.build_url_fname_html(person.handle, "ppl", True)
                    person_link = self.person_link(url, person,
                            _NAME_STYLE_DEFAULT, gid=person.get_gramps_id())

                    index = 0
                    for data in [
                        person_link,
                        person_ref.get_relation(),
                        self.dump_notes(person_ref.get_note_list()),
                        self.get_citation_links(person_ref.get_citation_list()),
                        ]: 

                        # get colclass from assoc_row
                        colclass = assoc_row[index][1]

                        trow += Html("td", data, class_ = "Column" + colclass, 
                            inline = True)  
                        index += 1

        # return section to its callers
        return section

    def display_ind_pedigree(self):
        """
        Display an individual's pedigree
        """
        birthorder = self.report.options["birthorder"]

        # Define helper functions
        def children_ped(ol):
            if family:
                childlist = family.get_child_ref_list()

                childlist = [child_ref.ref for child_ref in childlist]
                children = add_birthdate(self.dbase_, childlist)

                if birthorder:
                    children = sorted(children)
                
                for birthdate, handle in children:
                    if handle == self.person.get_handle():
                        child_ped(ol)
                    else:
                        child = self.dbase_.get_person_from_handle(handle)
                        ol += Html("li") + self.pedigree_person(child)
            else:
                child_ped(ol)
            return ol
                
        def child_ped(ol):
            with Html("li", self.name, class_="thisperson") as pedfam:
                family = self.pedigree_family()
                if family:
                    pedfam += Html("ol", class_ = "spouselist") + family
            return ol + pedfam
        # End of helper functions

        parent_handle_list = self.person.get_parent_family_handle_list()
        if parent_handle_list:
            parent_handle = parent_handle_list[0]
            family = self.dbase_.get_family_from_handle(parent_handle)
            father_handle = family.get_father_handle()
            mother_handle = family.get_mother_handle()
            mother = self.dbase_.get_person_from_handle(mother_handle)
            father = self.dbase_.get_person_from_handle(father_handle)
        else:
            family = None
            father = None
            mother = None

        with Html("div", id = "pedigree", class_ = "subsection") as ped:
            ped += Html("h4", _('Pedigree'), inline = True)
            with Html("ol", class_ = "pedigreegen") as pedol:
                ped += pedol
                if father and mother:
                    pedfa = Html("li") + self.pedigree_person(father)
                    pedol += pedfa
                    with Html("ol") as pedma:
                        pedfa += pedma
                        pedma += (Html("li", class_ = "spouse") +
                                      self.pedigree_person(mother) +
                                      children_ped(Html("ol"))
                                 )
                elif father:
                    pedol += (Html("li") + self.pedigree_person(father) +
                                  children_ped(Html("ol"))
                             )
                elif mother:
                    pedol += (Html("li") + self.pedigree_person(mother) +
                                  children_ped(Html("ol"))
                             )
                else:
                    pedol += (Html("li") + children_ped(Html("ol")))
        return ped
        
    def display_ind_general(self):
        """
        display an individual's general information...
        """
        self.page_title = self.sort_name
        thumbnail = self.display_first_image_as_thumbnail(self.person.get_media_list(), self.person)
        section_title = Html("h3", self.page_title, inline =True)

        # begin summaryarea division
        with Html("div", id = 'summaryarea') as summaryarea:

            # begin general details table
            with Html("table", class_ = "infolist") as table:
                summaryarea += table

                primary_name = self.person.get_primary_name()
                all_names = [primary_name] + self.person.get_alternate_names()

                # Names [and their sources]
                for name in all_names:
                    pname =  _nd.display_name(name)
                    if name == primary_name:
                        pname += self.get_citation_links(self.person.get_citation_list() ) 
                    pname += self.get_citation_links( name.get_citation_list() )

                    # if we have just a firstname, then the name is preceeded by ", "
                    # which doesn't exactly look very nice printed on the web page
                    if pname[:2] == ', ':
                        pname = pname[2:]
                    if name != primary_name:
                        datetext = _dd.display(name.date)
                        if datetext:
                            pname = datetext + ': ' + pname

                    type_ = str( name.get_type() )
                    trow = Html("tr") + (
                        Html("td", type_, class_ = "ColumnAttribute", inline = True)
                        )
                    table += trow
                    tcell = Html("td", pname, class_ = "ColumnValue")
                    trow += tcell

                    # display any notes associated with this name
                    notelist = name.get_note_list()
                    if len(notelist):
                        unordered = Html("ul")
                        tcell += unordered

                        for notehandle in notelist:
                            note = self.dbase_.get_note_from_handle(notehandle)
                            if note:
                                note_text = self.get_note_format(note, True)
 
                                # attach note
                                unordered += note_text

                # display call name
                first_name = primary_name.get_first_name()
                for name in all_names:
                    call_name = name.get_call_name()
                    if call_name and call_name != first_name:
                        call_name += self.get_citation_links(name.get_citation_list() )
                        trow = Html("tr") + (
                            Html("td", _("Call Name"), class_ = "ColumnAttribute", inline = True),
                            Html("td", call_name, class_ = "ColumnValue", inline = True)
                            )
                        table += trow
  
                # display the nickname attribute
                nick_name = self.person.get_nick_name()
                if nick_name and nick_name != first_name:
                    nick_name += self.get_citation_links(self.person.get_citation_list() )
                    trow = Html("tr") + (
                        Html("td", _("Nick Name"), class_ = "ColumnAttribute", inline = True),
                        Html("td", nick_name, class_ = "ColumnValue", inline = True)
                        )
                    table += trow 

                # GRAMPS ID
                person_gid = self.person.get_gramps_id()
                if not self.noid and person_gid:
                    trow = Html("tr") + (
                        Html("td", GRAMPSID, class_ = "ColumnAttribute", inline = True),
                        Html("td", person_gid, class_ = "ColumnValue", inline = True)
                        )
                    table += trow

                # Gender
                gender = self.gender_map[self.person.gender]
                trow = Html("tr") + (
                    Html("td", _("Gender"), class_ = "ColumnAttribute", inline = True),
                    Html("td", gender, class_ = "ColumnValue", inline = True)
                    )
                table += trow

                # Age At Death???
                birth_date = gen.lib.Date.EMPTY
                birth_ref = self.person.get_birth_ref()
                if birth_ref:
                    birth = self.dbase_.get_event_from_handle(birth_ref.ref)
                    if birth: 
                        birth_date = birth.get_date_object()

                if birth_date and birth_date is not gen.lib.Date.EMPTY:
                    alive = Utils.probably_alive(self.person, self.dbase_, date.Today() )

                    death_date = _find_death_date(self.dbase_, self.person)
                    if not alive and death_date is not None:
                        nyears = death_date - birth_date
                        nyears.format(precision = 3)
                        trow = Html("tr") + (
                            Html("td", _("Age at Death"), class_ = "ColumnAttribute", inline = True),
                            Html("td", nyears, class_ = "ColumnValue", inline = True)
                            )
                        table += trow

        # return all three pieces to its caller
        # do NOT combine before returning 
        return thumbnail, section_title, summaryarea

    def display_ind_events(self, place_lat_long):
        """
        will create the events table

        @param: place_lat_long -- for use in Family Map Pages
        """
        event_ref_list = self.person.get_event_ref_list()
        if not event_ref_list:
            return None
            
        # begin events division and section title
        with Html("div", id = "events", class_ = "subsection") as section:
            section += Html("h4", _("Events"), inline = True)

            # begin events table
            with Html("table", class_ = "infolist eventlist") as table:
                section += table

                thead = Html("thead")
                table += thead

                # attach event header row
                thead += self.event_header_row()

                tbody = Html("tbody")
                table += tbody

                for evt_ref in event_ref_list:
                    event = self.dbase_.get_event_from_handle(evt_ref.ref)
                    if event:

                        # display event row
                        tbody += self.display_event_row(
                                                        event, evt_ref, place_lat_long,
                                                        True, True, EventRoleType.PRIMARY)
        return section

    def display_parent(self, handle, title, rel):
        """
        This will display a parent ...
        """
        person = self.dbase_.get_person_from_handle(handle)
        tcell1 = Html("td", title, class_ = "ColumnAttribute", inline = True)
        tcell2 = Html("td", class_ = "ColumnValue")

        use_link = check_person_database(handle, self.ind_list)
        if use_link:
            url = self.report.build_url_fname_html(handle, "ppl", True)
            tcell2 += self.person_link(url, person, _NAME_STYLE_DEFAULT, gid =person.get_gramps_id())
        else:
            tcell2 += self.get_name(person)

        if rel and rel != gen.lib.ChildRefType(gen.lib.ChildRefType.BIRTH):
            tcell2 +=  ''.join(['&mnsp;'] *3 + ['(%s)']) % str(rel)

        # return table columns to its caller
        return tcell1, tcell2

    def display_ind_parents(self, ppl_handle_list):
        """
        Display a person's parents
        """

        parent_list = self.person.get_parent_family_handle_list()
        if not parent_list:
            return None

        birthorder = self.report.options['birthorder']

        # begin parents division
        with Html("div", class_ = "subsection", id = "parents") as section:
            section += Html("h4", _("Parents"), inline = True)

            # begin parents table
            with Html("table", class_ = "infolist") as table:
                section += table

                first = True
                if parent_list:
                    for family_handle in parent_list:
                        family = self.dbase_.get_family_from_handle(family_handle)

                        # Get the mother and father relationships
                        frel = None
                        mrel = None
                        sibling = []
  
                        child_handle = self.person.get_handle()
                        child_ref_list = family.get_child_ref_list()
                        for child_ref in child_ref_list:
                            if child_ref.ref == child_handle:
                                frel = child_ref.get_father_relation()
                                mrel = child_ref.get_mother_relation()
                                break

                        if not first:
                            trow = Html("tr") + (
                                Html("td", "&nbsp;", colspan =2, inline = True)
                            )
                            table += trow
                        else:
                            first = False

                        # get the father
                        father_handle = family.get_father_handle()
                        if father_handle:
                            father = self.dbase_.get_person_from_handle(father_handle)
                            if father:
                                trow = Html("tr") + \
                                    (self.display_parent(father_handle, _("Father"), frel)
                                )
                                table += trow 

                        # get the mother
                        mother_handle = family.get_mother_handle()
                        if mother_handle:
                            mother = self.dbase_.get_person_from_handle(mother_handle)
                            if mother:
                                trow = Html("tr") + \
                                    (self.display_parent(mother_handle, _("Mother"), mrel)
                                )
                                table += trow

                        first = False
                        if len(child_ref_list) > 1:

                            # remove sibling if it is yourself?
                            childlist = [child_ref.ref for child_ref in child_ref_list
                                if child_ref.ref != self.person.handle]
                            sibling.extend(childlist)

                    # now that we have all siblings in families of the person,
                    # display them...    
                    if sibling:
                        trow = Html("tr") + (
                            Html("td", _("Siblings"), class_ = "ColumnAttribute", inline = True)
                            )
                        table += trow

                        tcell = Html("td", class_ = "ColumnValue")
                        trow += tcell

                        ordered = Html("ol")
                        tcell += ordered 

                        sibling = add_birthdate(self.dbase_, sibling)
                        if birthorder:
                            sibling = sorted(sibling)
 
                        ordered.extend(
                            self.display_child_link(chandle, ppl_handle_list)
                                for birth_date, chandle in sibling
                        )

                    # Also try to identify half-siblings
                    half_siblings = []

                    ## FOLLOWING CODE IS WRONG, AS showallsiblings = False
                    ## THIS CODE WILL NOT RUN
                    ## TO FIX: the code only works if the user has his
                    ## half/step siblings in a specific way in the database,
                    ## however this way is not the official way
                    ## The official way is:
                    ##    1. step or half siblings _must_ be present 
                    ##       somewhere in the same family. So the search
                    ##       here over other families is wrong
                    ##    2. to determine the relationship, only the child
                    ##       relationship must be looked at, nothing else! 
                    showallsiblings = False #self.report.options['showhalfsiblings']
##                    # if we have a known father...
##                    if father_handle and showallsiblings:
##                        # 1) get all of the families in which this father is involved
##                        # 2) get all of the children from those families
##                        # 3) if the children are not already listed as siblings...
##                        # 4) then remember those children since we're going to list them
##                        father = self.dbase_.get_person_from_handle(father_handle)
##                        for family_handle in father.get_family_handle_list():
##                            family = self.dbase_.get_family_from_handle(family_handle)
##                            for half_child_ref in family.get_child_ref_list():
##                                half_child_handle = half_child_ref.ref
##                                if half_child_handle not in sibling:
##                                    if half_child_handle != self.person.handle:
##                                        # we have a new step/half sibling
##                                        half_siblings.append(half_child_handle)
##
##                    # do the same thing with the mother (see "father" just above):
##                    if mother_handle and showallsiblings:
##                        mother = self.dbase_.get_person_from_handle(mother_handle)
##                        for family_handle in mother.get_family_handle_list():
##                            family = self.dbase_.get_family_from_handle(family_handle)
##                            for half_child_ref in family.get_child_ref_list():
##                                half_child_handle = half_child_ref.ref
##                                if half_child_handle not in sibling:
##                                    if half_child_handle != self.person.handle:
##                                        # we have a new half sibling
##                                        half_siblings.append(half_child_handle)
##
##                    # now that we have all half- siblings, display them...    
##                    if half_siblings:
##                        trow = Html("tr") + (
##                            Html("td", _("Half Siblings"), class_ = "ColumnAttribute", inline = True)
##                            )
##                        table += trow
##
##                        tcell = Html("td", class_ = "ColumnValue")
##                        trow += tcell
##
##                        ordered = Html("ol")
##                        tcell += ordered
##
##                          half_siblings = add_birthdate(self.dbase_, half_siblings)
##                          if birthorder:
##                              half_siblings = sorted(half_siblings)
##
##                          ordered.extend(
##                              self.display_child_link(chandle, ind_list)
##                                  for birth_date, chandle in half_siblings
##                            ) 
##
##                    # get step-siblings
##                    if showallsiblings:
##                        step_siblings = []
##
##                        # to find the step-siblings, we need to identify
##                        # all of the families that can be linked back to
##                        # the current person, and then extract the children
##                        # from those families
##                        all_family_handles = set()
##                        all_parent_handles = set()
##                        tmp_parent_handles = set()
##
##                        # first we queue up the parents we know about
##                        if mother_handle:
##                            tmp_parent_handles.add(mother_handle)
##                        if father_handle:
##                            tmp_parent_handles.add(father_handle)
##
##                        while len(tmp_parent_handles):
##                            # pop the next parent from the set
##                            parent_handle = tmp_parent_handles.pop()
##
##                            # add this parent to our official list
##                            all_parent_handles.add(parent_handle)
##
##                            # get all families with this parent
##                            parent = self.dbase_.get_person_from_handle(parent_handle)
##                            for family_handle in parent.get_family_handle_list():
##
##                                all_family_handles.add(family_handle)
##
##                                # we already have 1 parent from this family
##                                # (see "parent" above) so now see if we need
##                                # to queue up the other parent
##                                family = self.dbase_.get_family_from_handle(family_handle)
##                                tmp_mother_handle = family.get_mother_handle()
##                                if  tmp_mother_handle and \
##                                    tmp_mother_handle != parent and \
##                                    tmp_mother_handle not in tmp_parent_handles and \
##                                    tmp_mother_handle not in all_parent_handles:
##                                    tmp_parent_handles.add(tmp_mother_handle)
##                                tmp_father_handle = family.get_father_handle()
##                                if  tmp_father_handle and \
##                                    tmp_father_handle != parent and \
##                                    tmp_father_handle not in tmp_parent_handles and \
##                                    tmp_father_handle not in all_parent_handles:
##                                    tmp_parent_handles.add(tmp_father_handle)
##
##                        # once we get here, we have all of the families
##                        # that could result in step-siblings; note that
##                        # we can only have step-siblings if the number
##                        # of families involved is > 1
##
##                        if len(all_family_handles) > 1:
##                            while len(all_family_handles):
##                                # pop the next family from the set
##                                family_handle = all_family_handles.pop()
##                                # look in this family for children we haven't yet seen
##                                family = self.dbase_.get_family_from_handle(family_handle)
##                                for step_child_ref in family.get_child_ref_list():
##                                    step_child_handle = step_child_ref.ref
##                                    if step_child_handle not in sibling and \
##                                           step_child_handle not in half_siblings and \
##                                           step_child_handle != self.person.handle:
##                                        # we have a new step sibling
##                                        step_siblings.append(step_child_handle)
##
##                        # now that we have all step- siblings, display them...    
##                        if len(step_siblings):
##                            trow = Html("tr") + (
##                                Html("td", _("Step Siblings"), class_ = "ColumnAttribute", inline = True)
##                                )
##                            table += trow
##
##                            tcell = Html("td", class_ = "ColumnValue")
##                            trow += tcell
##
##                            ordered = Html("ol")
##                            tcell += ordered
##
##                              step_siblings = add_birthdate(self.dbase_, step_siblings)
##                              if birthorder:
##                                  step_siblings = sorted(step_siblings)
##
##                              ordered.extend(
##                                  self.display_child_link(chandle, ind_list)
##                                      for birth_date, chandle in step_siblings
##                                )

        # return parents division to its caller
        return section

    def pedigree_person(self, person):
        """
        will produce a hyperlink for a pedigree person ...
        """

        use_link = check_person_database(person.get_handle(), self.ind_list)
        if use_link:
            url = self.report.build_url_fname_html(person.handle, "ppl", True)
            hyper = self.person_link(url, person, _NAME_STYLE_DEFAULT)
        else:
            hyper = self.get_name(person)
        return hyper

    def pedigree_family(self):
        """
        Returns a family pedigree
        """
        ped = []
        for family_handle in self.person.get_family_handle_list():
            rel_family = self.dbase_.get_family_from_handle(family_handle)
            spouse_handle = ReportUtils.find_spouse(self.person, rel_family)
            if spouse_handle:
                spouse = self.dbase_.get_person_from_handle(spouse_handle)
                pedsp = (Html("li", class_ = "spouse") +
                         self.pedigree_person(spouse)
                        )
            else:
                pedsp = (Html("li", class_ = "spouse"))
            ped += [pedsp]
            childlist = rel_family.get_child_ref_list()
            if childlist:
                with Html("ol") as childol:
                    pedsp += [childol]
                    for child_ref in childlist:
                        child = self.dbase_.get_person_from_handle(child_ref.ref)
                        childol += (Html("li") +
                                    self.pedigree_person(child)
                                   )
        return ped

    def display_event_header(self):
        """
        will print the event header row for display_event_row() and
            format_family_events()
        """ 
        trow = Html("tr")

        trow.extend(
                Html("th", label, class_ = "Column" + colclass, inline = True)
                for (label, colclass) in  [
                    (_EVENT,          "Event"),
                    (DHEAD,           "Date"),
                    (PHEAD,          "Place"),
                    (DESCRHEAD, "Description"),
                    (NHEAD,         "Notes"),
                    (SHEAD,         "Sources") ]
                )
        return trow

class RepositoryListPage(BasePage):
    def __init__(self, report, title, repos_dict, keys):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)
        inc_repos = self.report.options["inc_repository"]

        of = self.report.create_file("repositories")
        repolistpage, head, body = self.write_header(_("Repositories"))

        # begin RepositoryList division
        with Html("div", class_ = "content", id = "RepositoryList") as repositorylist:
            body += repositorylist

            msg = _("This page contains an index of all the repositories in the "
                          "database, sorted by their title. Clicking on a repositories&#8217;s "
                          "title will take you to that repositories&#8217;s page.")
            repositorylist += Html("p", msg, id = "description")

            # begin repositories table and table head
            with Html("table", class_ = "infolist primobjlist repolist") as table:
                repositorylist += table 

                thead = Html("thead")
                table += thead

                trow = Html("tr") + (
                    Html("th", "&nbsp;", class_ = "ColumnRowLabel", inline = True),
                    Html("th", THEAD, class_ = "ColumnType", inline = True),
                    Html("th", _("Repository |Name"), class_ = "ColumnName", inline = True)
                    )
                thead += trow

                # begin table body
                tbody = Html("tbody")
                table += tbody 

                for index, key in enumerate(keys):
                    (repo, handle) = repos_dict[key]

                    trow = Html("tr")
                    tbody += trow

                    # index number
                    trow += Html("td", index + 1, class_ = "ColumnRowLabel", inline = True)

                    # repository type
                    rtype = str(repo.type)
                    trow += Html("td", rtype, class_ = "ColumnType", inline = True)

                    # repository name and hyperlink
                    if repo.name:
                        trow += Html("td", self.repository_link(handle, repo.get_name(),
                                                                repo.get_gramps_id()), 
                                     class_ = "ColumnName")
                    else:
                        trow += Html("td", "[ untitled ]", class_ = "ColumnName")

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(repolistpage, of)

#-----------------------------------------------------
#
# Repository Pages
#
#-----------------------------------------------------
class RepositoryPage(BasePage):
    def __init__(self, report, title, repo, handle, source_list):
        gid = repo.get_gramps_id()
        BasePage.__init__(self, report, title, gid)
        self.dbase_ = report.database

        of = self.report.create_file(handle, 'repo')
        self.up = True
        repositorypage, head, body = self.write_header(_('Repositories'))

        # begin RepositoryDetail division and page title
        with Html("div", class_ = "content", id = "RepositoryDetail") as repositorydetail:
            body += repositorydetail

            # repository name
            repositorydetail += Html("h3", html_escape(repo.name), inline = True)

            # begin repository table
            with Html("table", class_ = "infolist repolist") as table:
                repositorydetail += table

                tbody = Html("tbody")
                table += tbody

                if not self.noid and gid:
                    trow = Html("tr") + (
                        Html("td", _("Gramps ID"), class_ ="ColumnAttribute", inline =True),
                        Html("td", gid, class_="ColumnValue", inline =True)
                    )
                    tbody += trow

                trow = Html("tr") + (
                    Html("td", _("Type"), class_ ="ColumnAttribute", inline =True),
                    Html("td", str(repo.get_type()), class_ ="ColumnValue", inline =True)
                )
                tbody += trow

            # repository: address(es)... repository addresses do NOT have Sources
            repo_address = self.display_addr_list(repo.get_address_list(), False)
            if repo_address is not None:
                repositorydetail += repo_address

            # repository: urllist
            urllist = self.display_url_list(repo.get_url_list())
            if urllist is not None:
                repositorydetail += urllist

            # reposity: notelist
            notelist = self.display_note_list(repo.get_note_list()) 
            if notelist is not None:
                repositorydetail += notelist

            # display Repository Referenced Sources...
            repositorydetail += self.__write_referenced_sources(handle, source_list)

        # add clearline for proper styling
        # add footer section
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(repositorypage, of)

    def __write_referenced_sources(self, handle, source_list):
        """
        This procedure writes out each of the sources related to the repository.
        """
        repository = self.dbase_.get_repository_from_handle(handle)
        if not repository:
            return None

        repository_source_handles = [handle for (object_type, handle) in
                         self.dbase_.find_backlink_handles(handle, include_classes = ['Source'])]

        # begin Repository Referenced Sources...
        with Html("div", class_ ="Subsection", id ="referenced_sources") as section:
            section += Html("h4", _("Referenced Sources"), inline =True)

            source_nbr = 0
            for source_handle in repository_source_handles:
                source = self.dbase_.get_source_from_handle(source_handle)
                if source:

                    # Get the list of references from this source to our repo
                    # (can be more than one, technically)
                    for reporef in source.get_reporef_list():
                        if reporef.ref == repository.get_handle():
                            source_nbr += 1

                            if source_handle in source_list:
                                source_name = self.source_link(source, up =True)
                            else:
                                source_name = source.get_title()

                            title = (('%(nbr)d. %(name)s (%(type)s) : %(call)s') % 
                                            {'nbr'  : source_nbr,
                                             'name' : source_name,
                                             'type' : str(reporef.get_media_type()),
                                             'call' : reporef.get_call_number()})
                            ordered = Html("ol", title)
                            section += ordered
        return section

class AddressBookListPage(BasePage):
    def __init__(self, report, title, has_url_addr_res):
        self.dbase_ = report.database
        BasePage.__init__(self, report, title)

        # Name the file, and create it
        of = self.report.create_file("addressbook")

        # Add xml, doctype, meta and stylesheets
        addressbooklistpage, head, body = self.write_header(_("Address Book"))

        # begin AddressBookList division
        with Html("div", class_ = "content", id = "AddressBookList") as addressbooklist:
            body += addressbooklist

            # Address Book Page message
            msg = _("This page contains an index of all the individuals in the "
                "database, sorted by their surname, with one of the "
                "following: Address, Residence, or Web Links. Selecting the "
                "person&#8217;s name will take you to their individual Address "
                "Book page.")
            addressbooklist += Html("p", msg, id = "description")

            # begin Address Book table
            with Html("table", class_ = "infolist primobjlist addressbook") as table:
                addressbooklist += table

                thead = Html("thead")
                table += thead

                trow = Html("tr")
                thead += trow

                trow.extend(
                    Html("th", label, class_= colclass, inline = True)
                    for (label, colclass) in [
                        ["&nbsp;",       "ColumnRowLabel"],
                        [_("Full Name"), "ColumnName"],
                        [_("Address"),   "ColumnAddress"],
                        [_("Residence"), "ColumnResidence"],
                        [_("Web Links"), "ColumnWebLinks"] ]
                        )

                tbody = Html("tbody")
                table += tbody

                index = 1
                for (sort_name, person_handle, has_add, has_res, has_url) in has_url_addr_res:

                    address = None
                    residence = None
                    weblinks = None

                    # has address but no residence event
                    if has_add and not has_res:
                        address = "X"

                    # has residence, but no addresses
                    elif has_res and not has_add:
                        residence = "X" 

                    # has residence and addresses too
                    elif has_add and has_res:
                        address = "X"
                        residence = "X" 

                    # has Web Links
                    if has_url:
                        weblinks = "X"

                    trow = Html("tr")
                    tbody += trow

                    trow.extend(
                        Html("td", data or "&nbsp;", class_= colclass, inline = True)
                        for (colclass, data) in [
                            ["ColumnRowLabel",  index],
                            ["ColumnName",      self.addressbook_link(person_handle)],
                            ["ColumnAddress",   address],
                            ["ColumnResidence", residence],
                            ["ColumnWebLinks",  weblinks] ]
                            )
                    index += 1

        # Add footer and clearline
        footer = self.write_footer()
        body += (fullclear, footer)

        # send the page out for processing
        # and close the file
        self.XHTMLWriter(addressbooklistpage, of)

class AddressBookPage(BasePage):
    def __init__(self, report, title, person_handle, has_add, has_res, has_url):
        self.dbase_ = report.database
        self.bibli = Bibliography()

        person = self.dbase_.get_person_from_handle(person_handle)
        BasePage.__init__(self, report, title, person.gramps_id)
        self.up = True

        # set the file name and open file
        of = self.report.create_file(person_handle, "addr")
        addressbookpage, head, body = self.write_header(_("Address Book"))

        # begin address book page division and section title
        with Html("div", class_ = "content", id = "AddressBookDetail") as addressbookdetail:
            body += addressbookdetail

            url = self.report.build_url_fname_html(person.handle, "ppl", True)
            addressbookdetail += Html("h3", self.person_link(url, person, _NAME_STYLE_DEFAULT))

            # individual has an address
            if has_add:
                addressbookdetail += self.display_addr_list(has_add, None)

            # individual has a residence
            if has_res:
                addressbookdetail.extend(
                    self.dump_residence(res)
                    for res in has_res
                )

            # individual has a url
            if has_url:
                addressbookdetail += self.display_url_list(has_url)

        # add fullclear for proper styling
        # and footer section to page
        footer = self.write_footer()
        body += (fullclear, footer)

        # send page out for processing
        # and close the file
        self.XHTMLWriter(addressbookpage, of)

class NavWebReport(Report):
    
    def __init__(self, database, options, user):
        """
        Create WebReport object that produces the report.

        The arguments are:

        database        - the GRAMPS database instance
        options         - instance of the Options class for this report
        user            - instance of a gen.user.User()
        """
        Report.__init__(self, database, options, user)
        self.user = user
        menu = options.menu
        self.link_prefix_up = True
        self.options = {}

        for optname in menu.get_all_option_names():
            menuopt = menu.get_option_by_name(optname)
            self.options[optname] = menuopt.get_value()

        if not self.options['incpriv']:
            self.database = PrivateProxyDb(database)
        else:
            self.database = database

        livinginfo = self.options['living']
        yearsafterdeath = self.options['yearsafterdeath']

        if livinginfo != _INCLUDE_LIVING_VALUE:
            self.database = LivingProxyDb(self.database,
                                          livinginfo,
                                          None,
                                          yearsafterdeath)

        filters_option = menu.get_option_by_name('filter')
        self.filter = filters_option.get_filter()

        self.copyright = self.options['cright']
        self.target_path = self.options['target']
        self.ext = self.options['ext']
        self.css = self.options['css']
        self.navigation = self.options["navigation"]

        self.title = self.options['title']

        self.inc_gallery = self.options['gallery']
        self.create_thumbs_only = self.options['create_thumbs_only']

        self.inc_contact = self.options['contactnote'] or \
                           self.options['contactimg']

        # name format options
        self.name_format = self.options['name_format']

        # include families or not?
        self.inc_families = self.options['inc_families']

        # create an event pages or not?
        self.inc_events = self.options['inc_events']

        # include repository page or not?
        self.inc_repository = self.options['inc_repository']

        # include GENDEX page or not?
        self.inc_gendex = self.options['inc_gendex']

        # Download Options Tab
        self.inc_download = self.options['incdownload']
        self.dl_fname1 = self.options['down_fname1']
        self.dl_descr1 = self.options['dl_descr1']
        self.dl_fname2 = self.options['down_fname2']
        self.dl_descr2 = self.options['dl_descr2']

        self.encoding = self.options['encoding']

        self.use_archive = self.options['archive']
        self.use_intro = self.options['intronote'] or \
                         self.options['introimg']
        self.use_home = self.options['homenote'] or \
                        self.options['homeimg']
        self.use_contact = self.options['contactnote'] or \
                           self.options['contactimg']

        # either include the gender graphics or not?
        self.ancestortree = self.options['ancestortree']

        # whether to display children in birthorder or entry order?
        self.birthorder = self.options['birthorder']

        # get option for Internet Address Book
        self.inc_addressbook = self.options["inc_addressbook"]

        # Place Map tab options
        self.placemappages = self.options['placemappages']
        self.familymappages = self.options['familymappages']
        self.mapservice = self.options['mapservice']
        self.googleopts = self.options['googleopts']

        if self.use_home:
            self.index_fname = "index"
            self.surname_fname = "surnames"
            self.intro_fname = "introduction"
        elif self.use_intro:
            self.index_fname = None
            self.surname_fname = "surnames"
            self.intro_fname = "index"
        else:
            self.index_fname = None
            self.surname_fname = "index"
            self.intro_fname = None

        self.archive = None
        self.cur_fname = None            # Internal use. The name of the output file, 
                                         # to be used for the tar archive.
        self.string_io = None
        if self.use_archive:
            self.html_dir = None
        else:
            self.html_dir = self.target_path
        self.warn_dir = True        # Only give warning once.
        self.photo_list = {}

    def write_report(self):

        _WRONGMEDIAPATH = []
        if not self.use_archive:
            dir_name = self.target_path
            if dir_name is None:
                dir_name = os.getcwd()
            elif not os.path.isdir(dir_name):
                parent_dir = os.path.dirname(dir_name)
                if not os.path.isdir(parent_dir):
                    msg = _("Neither %s nor %s are directories") % \
                          (dir_name, parent_dir)
                    self.user.notify_error(msg)
                    return
                else:
                    try:
                        os.mkdir(dir_name)
                    except IOError, value:
                        msg = _("Could not create the directory: %s") % \
                              dir_name + "\n" + value[1]
                        self.user.notify_error(msg)
                        return
                    except:
                        msg = _("Could not create the directory: %s") % dir_name
                        self.user.notify_error(msg)
                        return

            try:
                image_dir_name = os.path.join(dir_name, 'images')
                if not os.path.isdir(image_dir_name):
                    os.mkdir(image_dir_name)

                image_dir_name = os.path.join(dir_name, 'thumb')
                if not os.path.isdir(image_dir_name):
                    os.mkdir(image_dir_name)
            except IOError, value:
                msg = _("Could not create the directory: %s") % \
                      image_dir_name + "\n" + value[1]
                self.user.notify_error(msg)
                return
            except:
                msg = _("Could not create the directory: %s") % \
                      image_dir_name + "\n" + value[1]
                self.user.notify_error(msg)
                return
        else:
            if os.path.isdir(self.target_path):
                self.user.notify_error(_('Invalid file name'),
                        _('The archive file must be a file, not a directory'))
                return
            try:
                self.archive = tarfile.open(self.target_path, "w:gz")
            except (OSError, IOError), value:
                self.user.notify_error(_("Could not create %s") % self.target_path,
                            str(value))
                return

        # Build the person list
        ind_list = self.build_person_list()

        # initialize place_lat_long variable for use in Family Map Pages
        place_lat_long = []

        # copy all of the neccessary files
        self.copy_narrated_files()

        place_list = {}
        source_list = {}

        self.base_pages()

        # build classes IndividualListPage and IndividualPage
        self.person_pages(ind_list, place_list, source_list, place_lat_long)

        # build classes SurnameListPage and SurnamePage
        self.surname_pages(ind_list)

        # build classes PlaceListPage and PlacePage
        self.place_pages(place_list, source_list)

        # build classes EventListPage and EventPage
        if self.inc_events:
            self.event_pages(ind_list)

        # build classes FamilyListPage and FamilyPage
        if self.inc_families:
            self.family_pages(ind_list, place_list, place_lat_long)

        # build classes SourceListPage and SourcePage
        self.source_pages(source_list, ind_list)

        # build classes MediaListPage and MediaPage
        if self.inc_gallery:
            if not self.create_thumbs_only:
                self.media_pages(source_list)

            # build Thumbnail Preview Page...
            self.thumbnail_preview_page()

        # Build classes source pages a second time to pick up sources referenced
        # by galleries
        self.source_pages(source_list, ind_list)

        # build classes ddressBookList and AddressBookPage
        if self.inc_addressbook:
            self.addressbook_pages(ind_list)

        # build classes RepositoryListPage and RepositoryPage
        if self.inc_repository:
            repolist = self.database.get_repository_handles()
            if len(repolist):
                self.repository_pages(repolist, source_list)

        # if an archive is being used, close it?
        if self.archive:
            self.archive.close()
        
        if len(_WRONGMEDIAPATH) > 0:
            error = '\n'.join([_('ID=%(grampsid)s, path=%(dir)s') % {
                            'grampsid': x[0],
                            'dir': x[1]} for x in _WRONGMEDIAPATH[:10]])
            if len(_WRONGMEDIAPATH) > 10:
                error += '\n ...'
            self.user.warn(_("Missing media objects:"), error)

    def build_person_list(self):
        """
        Builds the person list. Gets all the handles from the database
        and then applies the chosen filter:
        """
        # gets the person list and applies the requested filter
        self.person_handles = {}
        ind_list = self.database.iter_person_handles()
        
        self.user.begin_progress(_("Narrated Web Site Report"),
                                  _('Applying Filter...'), 
                                  self.database.get_number_of_people())
        ind_list = self.filter.apply(self.database, ind_list, 
                                     self.user.step_progress)
        self.user.end_progress()
        for handle in ind_list:
            self.person_handles[handle] = True
        return ind_list

    def copy_narrated_files(self):
        """
        Copy all of the CSS, image, and javascript files for Narrated Web
        """
        imgs = []

        # copy screen style sheet
        if CSS[self.css]["filename"]:
            fname = CSS[self.css]["filename"]
            self.copy_file(fname, _NARRATIVESCREEN, "styles")

        # copy printer style sheet
        fname = CSS["Print-Default"]["filename"] 
        self.copy_file(fname, _NARRATIVEPRINT, "styles")

        # copy ancestor tree style sheet if tree is being created?
        if self.ancestortree:
            fname = CSS["ancestortree"]["filename"]
            self.copy_file(fname, "ancestortree.css", "styles")

        # copy behaviour style sheet
        fname = CSS["behaviour"]["filename"] 
        self.copy_file(fname, "behaviour.css", "styles")

        # copy Menu Layout stylesheet if Blue or Visually is being used?
        if CSS[self.css]["navigation"]: 
            if self.navigation == "Horizontal":
                fname = CSS["Horizontal-Menus"]["filename"] 
            else:
                fname = CSS["Vertical-Menus"]["filename"] 
            self.copy_file(fname, "narrative-menus.css", "styles")

        # copy narrative-maps if Place or Family Map pages?
        if (self.placemappages or self.familymappages):
            fname = CSS["NarrativeMaps"]["filename"] 
            self.copy_file(fname, "narrative-maps.css", "styles")

        # Copy the Creative Commons icon if the Creative Commons
        # license is requested
        if 0 < self.copyright <= len(_CC):
            imgs += [CSS["Copyright"]["filename"]]

        # copy Gramps favorite icon #2
        imgs += [CSS["favicon2"]["filename"]]

        # we need the blank image gif needed by behaviour.css
        # add the document.png file for media other than photos
        imgs += CSS["All Images"]["images"]

        # copy Ancestor Tree graphics if needed???
        if self.ancestortree:
            imgs += CSS["ancestortree"]["images"]

        # Anything css-specific:
        imgs += CSS[self.css]["images"]

        # copy all to images subdir:
        for from_path in imgs:
            fdir, fname = os.path.split(from_path)
            self.copy_file(from_path, fname, "images")

    def person_pages(self, ind_list, place_list, source_list, place_lat_long):
        """
        creates IndividualListPage, IndividualPage, and gendex page
        """
        self.user.begin_progress(_("Narrated Web Site Report"),
                                  _('Creating individual pages'), 
                                  len(ind_list) + 1)
        IndividualListPage(self, self.title, ind_list)
        for person_handle in ind_list:

            # clear other's places
            place_lat_long = []

            self.user.step_progress()
            person = self.database.get_person_from_handle(person_handle)

            IndividualPage(self, self.title, person, ind_list, place_list, source_list, place_lat_long)
        self.user.end_progress()

        if self.inc_gendex:
            self.user.begin_progress(_("Narrated Web Site Report"),
                                      _('Creating GENDEX file'), len(ind_list))
            fp_gendex = self.create_file("gendex", ext=".txt")
            for person_handle in ind_list:
                self.user.step_progress()
                person = self.database.get_person_from_handle(person_handle)
                self.write_gendex(fp_gendex, person)
            self.close_file(fp_gendex)
            self.user.end_progress()

    def write_gendex(self, fp, person):
        """
        Reference|SURNAME|given name /SURNAME/|date of birth|place of birth|date of death|
            place of death|
        * field 1: file name of web page referring to the individual
        * field 2: surname of the individual
        * field 3: full name of the individual
        * field 4: date of birth or christening (optional)
        * field 5: place of birth or christening (optional)
        * field 6: date of death or burial (optional)
        * field 7: place of death or burial (optional) 
        """
        url = self.build_url_fname_html(person.handle, "ppl")
        surname = person.get_primary_name().get_surname()
        fullname = person.get_primary_name().get_gedcom_name()

        # get birth info:
        dob, pob = get_gendex_data(self.database, person.get_birth_ref())

        # get death info:
        dod, pod = get_gendex_data(self.database, person.get_death_ref())
        fp.write(
            '|'.join((url, surname, fullname, dob, pob, dod, pod)) + '|\n')

    def surname_pages(self, ind_list):
        """
        Generates the surname related pages from list of individual
        people.
        """
        local_list = sort_people(self.database, ind_list)

        self.user.begin_progress(_("Narrated Web Site Report"),
                                  _("Creating surname pages"), len(local_list))

        SurnameListPage(self, self.title, ind_list, SurnameListPage.ORDER_BY_NAME,
            self.surname_fname)

        SurnameListPage(self, self.title, ind_list, SurnameListPage.ORDER_BY_COUNT,
            "surnames_count")

        for (surname, handle_list) in local_list:
            SurnamePage(self, self.title, surname, handle_list)
            self.user.step_progress()
        self.user.end_progress()

    def family_pages(self, ppl_handle_list, place_list, place_lat_long):
        """
        creates the FamiliesListPage and FamilyPages
        """
        displayed = set()
        FamilyListPage(self, self.title, ppl_handle_list, displayed)

        self.user.begin_progress(_("Narrated Web Site Report"),
                                  _("Creating family pages..."), 
                                  len(displayed))

        for phandle in ppl_handle_list:
            person = self.database.get_person_from_handle(phandle)
            if person:
                family_handle_list = person.get_family_handle_list()
                if family_handle_list:
                    for fhandle in family_handle_list:
                        family = self.database.get_family_from_handle(fhandle)
                        if family:
                            FamilyPage(self, self.title, person, family, place_list, ppl_handle_list, place_lat_long)

                            self.user.step_progress()
        self.user.end_progress()

    def place_pages(self, place_list, source_list):
        """
        creates PlaceListPage and PlacePage
        """
        self.user.begin_progress(_("Narrated Web Site Report"),
                                  _("Creating place pages"), len(place_list))

        PlaceListPage(self, self.title, place_list)

        for place in place_list:
            PlacePage(self, self.title, place, source_list, place_list)
            self.user.step_progress()
        self.user.end_progress()

    def event_pages(self, ind_list):
        """
        a dump of all the events sorted by event type, date, and surname
        for classes EventListPage and EventPage
        """
        # get event types and the handles that go with that type by individuals
        event_handle_list, event_types = build_event_data_by_individuals(self.database, ind_list)

        self.user.begin_progress(_("Narrated Web Site Report"),
                                  _("Creating event pages"), 
                                  len(event_handle_list)
        )

        EventListPage(self, self.title, event_types, event_handle_list, ind_list)

        for event_handle in event_handle_list:
            EventPage(self, self.title, event_handle, ind_list)

            self.user.step_progress()
        self.user.end_progress()

    def source_pages(self, source_list, ppl_handle_list):
        """
        creates SourceListPage and SourcePage
        """
        self.user.begin_progress(_("Narrated Web Site Report"),
                                 _("Creating source pages"),
                                 len(source_list))

        SourceListPage(self, self.title, source_list.keys())

        for source_handle in source_list:
            SourcePage(self, self.title, source_handle, source_list, ppl_handle_list)

            self.user.step_progress()
        self.user.end_progress()

    def media_pages(self, source_list):
        """
        creates MediaListPage and MediaPage
        """
        self.user.begin_progress(_("Narrated Web Site Report"),
                                  _("Creating media pages"), 
                                  len(self.photo_list))

        MediaListPage(self, self.title)

        prev = None
        total = len(self.photo_list)
        sort = Sort.Sort(self.database)
        photo_keys = sorted(self.photo_list, key =sort.by_media_title_key)

        index = 1
        for photo_handle in photo_keys:
            gc.collect() # Reduce memory usage when there are many images.
            next = None if index == total else photo_keys[index]
            # Notice. Here self.photo_list[photo_handle] is used not self.photo_list
            MediaPage(self, self.title, photo_handle, source_list, self.photo_list[photo_handle],
                      (prev, next, index, total))
            self.user.step_progress()
            prev = photo_handle
            index += 1
        self.user.end_progress()

    def thumbnail_preview_page(self):
        """
        creates the thumbnail preview page
        """
        self.user.begin_progress(_("Narrated Web Site Report"),
                                  _("Creating thumbnail preview page..."), 
                                  len(self.photo_list))
        ThumbnailPreviewPage(self, self.title, self.user.step_progress)
        self.user.end_progress()

    def base_pages(self):
        """
        creates HomePage, ContactPage, DownloadPage, and IntroductionPage
        if requested by options in plugin
        """

        if self.use_home:
            HomePage(self, self.title)

        if self.inc_contact:
            ContactPage(self, self.title)

        if self.inc_download:
            DownloadPage(self, self.title)

        if self.use_intro:
            IntroductionPage(self, self.title)

    def repository_pages(self, repolist, source_list):
        """
        will create RepositoryPage() and RepositoryListPage()
        """
        repos_dict = {}

        # Sort the repositories
        for handle in repolist:
            repository = self.database.get_repository_from_handle(handle)
            key = repository.get_name() + str(repository.get_gramps_id())
            repos_dict[key] = (repository, handle)
            
        keys = sorted(repos_dict, key =locale.strxfrm)

        # set progress bar pass for Repositories
        repository_size = len(repos_dict)
        
        self.user.begin_progress(_("Narrated Web Site Report"),
                                  _('Creating repository pages'), 
                                  repository_size)
        # RepositoryListPage Class
        RepositoryListPage(self, self.title, repos_dict, keys)

        for index, key in enumerate(keys):
            (repo, handle) = repos_dict[key]

            RepositoryPage(self, self.title, repository, handle, source_list)
            self.user.step_progress()
        self.user.end_progress()

    def addressbook_pages(self, ind_list):
        """
        Create a webpage with a list of address availability for each person
        and the associated individual address pages.
        """

        url_addr_res = []

        for person_handle in ind_list:

            person = self.database.get_person_from_handle(person_handle)
            addrlist = person.get_address_list()
            evt_ref_list = person.get_event_ref_list()
            urllist = person.get_url_list()

            add = addrlist or None
            url = urllist or None
            res = []

            for event_ref in evt_ref_list:
                event = self.database.get_event_from_handle(event_ref.ref)
                if event.get_type() == gen.lib.EventType.RESIDENCE:
                    res.append(event)

            if add or res or url:
                primary_name = person.get_primary_name()
                sort_name = ''.join([primary_name.get_surname(), ", ", 
                                    primary_name.get_first_name()])
                url_addr_res.append( (sort_name, person_handle, add, res, url) )

        url_addr_res.sort()
        AddressBookListPage(self, self.title, url_addr_res)

        # begin Address Book pages 
        addr_size = len(url_addr_res)
        
        self.user.begin_progress(_("Narrated Web Site Report"),
                                  _("Creating address book pages ..."), 
                                  addr_size)
        for (sort_name, person_handle, add, res, url) in url_addr_res:
            AddressBookPage(self, self.title, person_handle, add, res, url)
            self.user.step_progress()
        self.user.end_progress()

    def build_subdirs(self, subdir, fname, up = False):
        """
        If subdir is given, then two extra levels of subdirectory are inserted
        between 'subdir' and the filename. The reason is to prevent directories
        with too many entries.

        For example, this may return "8/1/aec934857df74d36618"

        *** up = None = [./] for use in EventListPage
        """
        subdirs = []
        if subdir:
            subdirs.append(subdir)
            subdirs.append(fname[-1].lower())
            subdirs.append(fname[-2].lower())

        if up == True:
            subdirs = ['..']*3 + subdirs

        # added for use in EventListPage
        elif up is None:
            subdirs = ['.'] + subdirs
        return subdirs

    def build_path(self, subdir, fname, up = False):
        """
        Return the name of the subdirectory.

        Notice that we DO use os.path.join() here.
        """
        return os.path.join(*self.build_subdirs(subdir, fname, up))

    def build_url_image(self, fname, subdir = None, up = False):
        """
        builds a url from an image
        """

        subdirs = []
        if subdir:
            subdirs.append(subdir)
        if up:
            subdirs = ['..']*3 + subdirs
        nname = "/".join(subdirs + [fname])
        if constfunc.win():
            nname = nname.replace('\\',"/")
        return nname

    def build_url_fname_html(self, fname, subdir = None, up = False):
        """
        builds a url filename from html
        """

        return self.build_url_fname(fname, subdir, up) + self.ext

    def build_link(self, prop, handle, obj_class):
        """
        Build a link to an item.
        """
        if prop == "gramps_id":
            if obj_class in self.database.get_table_names():
                obj = self.database.get_table_metadata(obj_class)["gramps_id_func"](handle)
                if obj:
                    handle = obj.handle
                else:
                    raise AttributeError("gramps_id '%s' not found in '%s'" % 
                                         handle, obj_class)
            else:
                raise AttributeError("invalid gramps_id lookup " 
                                     "in table name '%s'" % obj_class)
        up = self.link_prefix_up 
        # handle, ppl
        if obj_class == "Person":
            if handle in self.person_handles:
                return self.build_url_fname(handle, "ppl", up) + self.ext
            else:
                return None
        elif obj_class == "Source":
            subdir = "src"
        elif obj_class == "Place":
            subdir = "plc"
        elif obj_class == "Event":
            subdir = "evt"
        elif obj_class == "Media":
            subdir = "img"
        elif obj_class == "Repository":
            subdir = "repo"
        elif obj_class == "Family": 
            # FIXME: no family page in NarWeb
            return None
        else:
            raise AttributeError("unknown object type '%s'" % obj_class)
        return self.build_url_fname(handle, subdir, up) + self.ext

    def build_url_fname(self, fname, subdir = None, up = False):
        """
        Create part of the URL given the filename and optionally the subdirectory.
        If the subdirectory is given, then two extra levels of subdirectory are inserted
        between 'subdir' and the filename. The reason is to prevent directories with
        too many entries.
        If 'up' is True, then "../../../" is inserted in front of the result. 

        The extension is added to the filename as well.

        Notice that we do NOT use os.path.join() because we're creating a URL.
        Imagine we run gramps on Windows (heaven forbits), we don't want to
        see backslashes in the URL.
        """
        if not fname:
            return ""

        if constfunc.win():
            fname = fname.replace('\\',"/")
        subdirs = self.build_subdirs(subdir, fname, up)
        return "/".join(subdirs + [fname])

    def create_file(self, fname, subdir = None, ext = None):
        """
        will create filename given

        @param: fname -- file name to be created
        @param: subdir -- a subdir to be added to filename
        @param: ext -- an extension to be added to filename
        """

        if ext is None:
            ext = self.ext
        if subdir:
            subdir = self.build_path(subdir, fname)
            self.cur_fname = os.path.join(subdir, fname) + ext
        else:
            self.cur_fname = fname + ext
        if self.archive:
            self.string_io = StringIO()
            of = codecs.EncodedFile(self.string_io, 'utf-8',
                                    self.encoding, 'xmlcharrefreplace')
        else:
            if subdir:
                subdir = os.path.join(self.html_dir, subdir)
                if not os.path.isdir(subdir):
                    os.makedirs(subdir)
            fname = os.path.join(self.html_dir, self.cur_fname)
            of = codecs.EncodedFile(open(fname, "w"), 'utf-8',
                                    self.encoding, 'xmlcharrefreplace')
        return of

    def close_file(self, of):
        """
        will close any file passed to it
        """

        if self.archive:
            tarinfo = tarfile.TarInfo(self.cur_fname)
            tarinfo.size = len(self.string_io.getvalue())
            tarinfo.mtime = time.time()
            if not constfunc.win():
                tarinfo.uid = os.getuid()
                tarinfo.gid = os.getgid()
            self.string_io.seek(0)
            self.archive.addfile(tarinfo, self.string_io)
            self.string_io = None
            of.close()
        else:
            of.close()
        self.cur_fname = None

    def add_lnkref_to_photo(self, photo, lnkref):
        """
        adds link reference to media object
        """

        handle = photo.get_handle()
        # FIXME. Is it OK to add to the photo_list of report?
        photo_list = self.photo_list
        if handle in photo_list:
            if lnkref not in photo_list[handle]:
                photo_list[handle].append(lnkref)
        else:
            photo_list[handle] = [lnkref]

    def prepare_copy_media(self, photo):
        """
        prepares a media object to copy
        """

        handle = photo.get_handle()
        ext = os.path.splitext(photo.get_path())[1]
        real_path = os.path.join(self.build_path('images', handle), handle + ext)
        thumb_path = os.path.join(self.build_path('thumb', handle), handle + '.png')
        return real_path, thumb_path

    def copy_file(self, from_fname, to_fname, to_dir=''):
        """
        Copy a file from a source to a (report) destination.
        If to_dir is not present and if the target is not an archive,
        then the destination directory will be created.

        Normally 'to_fname' will be just a filename, without directory path.

        'to_dir' is the relative path name in the destination root. It will
        be prepended before 'to_fname'.
        """
        log.debug("copying '%s' to '%s/%s'" % (from_fname, to_dir, to_fname))
        if self.archive:
            dest = os.path.join(to_dir, to_fname)
            self.archive.add(from_fname, dest)
        else:
            dest = os.path.join(self.html_dir, to_dir, to_fname)

            destdir = os.path.dirname(dest)
            if not os.path.isdir(destdir):
                os.makedirs(destdir)

            if from_fname != dest:
                try:
                    shutil.copyfile(from_fname, dest)
                except:
                    print("Copying error: %s" % sys.exc_info()[1])
                    print("Continuing...")
            elif self.warn_dir:
                self.user.warn(
                    _("Possible destination error") + "\n" +
                    _("You appear to have set your target directory "
                      "to a directory used for data storage. This "
                      "could create problems with file management. "
                      "It is recommended that you consider using "
                      "a different directory to store your generated "
                      "web pages."))
                self.warn_dir = False

#################################################
#
#    Creates the NarrativeWeb Report Menu Options
#        Defines options and provides handling interface.
#
#################################################
class NavWebOptions(MenuReportOptions):
    def __init__(self, name, dbase):
        self.__db = dbase
        self.__archive = None
        self.__target = None
        self.__pid = None
        self.__filter = None
        self.__graph = None
        self.__graphgens = None
        self.__living = None
        self.__yearsafterdeath = None
        MenuReportOptions.__init__(self, name, dbase)

    def add_menu_options(self, menu):
        """
        Add options to the menu for the web site.
        """
        self.__add_report_options(menu)
        self.__add_page_generation_options(menu)
        self.__add_privacy_options(menu)
        self.__add_download_options(menu) 
        self.__add_advanced_options(menu)
        self.__add_place_map_options(menu)


    def __add_report_options(self, menu):
        """
        Options on the "Report Options" tab.
        """
        category_name = _("Report Options")
        addopt = partial( menu.add_option, category_name )

        self.__archive = BooleanOption(_('Store web pages in .tar.gz archive'),
                                       False)
        self.__archive.set_help(_('Whether to store the web pages in an '
                                  'archive file'))
        addopt( "archive", self.__archive )
        self.__archive.connect('value-changed', self.__archive_changed)

        self.__target = DestinationOption(_("Destination"),
                                    os.path.join(const.USER_HOME, "NAVWEB"))
        self.__target.set_help( _("The destination directory for the web "
                                  "files"))
        addopt( "target", self.__target )

        self.__archive_changed()

        title = StringOption(_("Web site title"), _('My Family Tree'))
        title.set_help(_("The title of the web site"))
        addopt( "title", title )

        self.__filter = FilterOption(_("Filter"), 0)
        self.__filter.set_help(
               _("Select filter to restrict people that appear on web site"))
        addopt( "filter", self.__filter )
        self.__filter.connect('value-changed', self.__filter_changed)

        self.__pid = PersonOption(_("Filter Person"))
        self.__pid.set_help(_("The center person for the filter"))
        addopt( "pid", self.__pid )
        self.__pid.connect('value-changed', self.__update_filters)

        self.__update_filters()

        # We must figure out the value of the first option before we can
        # create the EnumeratedListOption
        fmt_list = _nd.get_name_format()
        defaultnum = _nd.get_default_format()
        default = 0
        for ind, val in enumerate(fmt_list):
            if val[0] == defaultnum:
                default =  ind
                break
        name_format = EnumeratedListOption(_("Name format"), 
                            fmt_list[default][0])
        for num, name, fmt_str, act in fmt_list:
            name_format.add_item(num, name)
        name_format.set_help(_("Select the format to display names"))
        addopt( "name_format", name_format )

        ext = EnumeratedListOption(_("File extension"), ".html" )
        for etype in _WEB_EXT:
            ext.add_item(etype, etype)
        ext.set_help( _("The extension to be used for the web files"))
        addopt( "ext", ext )

        cright = EnumeratedListOption(_('Copyright'), 0 )
        for index, copt in enumerate(_COPY_OPTIONS):
            cright.add_item(index, copt)
        cright.set_help( _("The copyright to be used for the web files"))
        addopt( "cright", cright )

        self.__css = EnumeratedListOption(_('StyleSheet'), CSS["default"]["id"])
        for (fname, id) in sorted([(CSS[key]["translation"], CSS[key]["id"]) 
                                  for key in CSS.keys()]):
            if CSS[id]["user"]:
                self.__css.add_item(CSS[id]["id"], CSS[id]["translation"])
        self.__css.set_help( _('The stylesheet to be used for the web pages'))
        addopt( "css", self.__css )
        self.__css.connect("value-changed", self.__stylesheet_changed)

        _nav_opts = [
            [_("Horizontal -- No Change"), "Horizontal"],
            [_("Vertical"),                "Vertical"]
            ]
        self.__navigation = EnumeratedListOption(_("Navigation Menu Layout"), _nav_opts[0][1])
        for layout in _nav_opts:
            self.__navigation.add_item(layout[1], layout[0])
        self.__navigation.set_help(_("Choose which layout for the Navigation Menus."))
        addopt( "navigation", self.__navigation )

        self.__stylesheet_changed()

        self.__ancestortree = BooleanOption(_("Include ancestor's tree"), True)
        self.__ancestortree.set_help(_('Whether to include an ancestor graph '
                                       'on each individual page'))
        addopt( "ancestortree", self.__ancestortree )
        self.__ancestortree.connect('value-changed', self.__graph_changed)

        self.__graphgens = NumberOption(_("Graph generations"), 4, 2, 5)
        self.__graphgens.set_help( _("The number of generations to include in "
                                     "the ancestor graph"))
        addopt( "graphgens", self.__graphgens )

        self.__graph_changed()

    def __add_page_generation_options(self, menu):
        """
        Options on the "Page Generation" tab.
        """
        category_name = _("Page Generation")
        addopt = partial(menu.add_option, category_name)

        homenote = NoteOption(_('Home page note'))
        homenote.set_help( _("A note to be used on the home page"))
        addopt( "homenote", homenote )

        homeimg = MediaOption(_('Home page image'))
        homeimg.set_help( _("An image to be used on the home page"))
        addopt( "homeimg", homeimg )

        intronote = NoteOption(_('Introduction note'))
        intronote.set_help( _("A note to be used as the introduction"))
        addopt( "intronote", intronote )

        introimg = MediaOption(_('Introduction image'))
        introimg.set_help( _("An image to be used as the introduction"))
        addopt( "introimg", introimg )

        contactnote = NoteOption(_("Publisher contact note"))
        contactnote.set_help( _("A note to be used as the publisher contact."
                                "\nIf no publisher information is given,"
                                "\nno contact page will be created")
                              )
        addopt( "contactnote", contactnote )

        contactimg = MediaOption(_("Publisher contact image"))
        contactimg.set_help( _("An image to be used as the publisher contact."
                               "\nIf no publisher information is given,"
                               "\nno contact page will be created")
                             )
        addopt("contactimg", contactimg)

        headernote = NoteOption(_('HTML user header'))
        headernote.set_help( _("A note to be used as the page header"))
        addopt( "headernote", headernote )

        footernote = NoteOption(_('HTML user footer'))
        footernote.set_help( _("A note to be used as the page footer"))
        addopt( "footernote", footernote )

        self.__gallery = BooleanOption(_("Include images and media objects"), True)
        self.__gallery.set_help(_('Whether to include a gallery of media objects'))
        addopt( "gallery", self.__gallery )
        self.__gallery.connect('value-changed', self.__gallery_changed)

        self.__create_thumbs_only = BooleanOption(_("Create and only use thumbnail- sized images"), False)
        self.__create_thumbs_only.set_help(_("This options allows you the choice to not create any full- sized "
            "images as in the Media Page, and only a thumb- sized images.  This will allow you to have a much "
            "smaller total upload size to your web hosting site."))
        addopt("create_thumbs_only", self.__create_thumbs_only)
        self.__create_thumbs_only.connect("value-changed", self.__gallery_changed)

        self.__maxinitialimagewidth = NumberOption(_("Max width of initial image"), 
            _DEFAULT_MAX_IMG_WIDTH, 0, 2000)
        self.__maxinitialimagewidth.set_help(_("This allows you to set the maximum width "
                              "of the image shown on the media page. Set to 0 for no limit."))
        addopt( "maxinitialimagewidth", self.__maxinitialimagewidth )

        self.__maxinitialimageheight = NumberOption(_("Max height of initial image"), 
            _DEFAULT_MAX_IMG_HEIGHT, 0, 2000)
        self.__maxinitialimageheight.set_help(_("This allows you to set the maximum height "
                              "of the image shown on the media page. Set to 0 for no limit."))
        addopt( "maxinitialimageheight", self.__maxinitialimageheight)

        self.__gallery_changed()

        nogid = BooleanOption(_('Suppress Gramps ID'), False)
        nogid.set_help(_('Whether to include the Gramps ID of objects'))
        addopt( "nogid", nogid )

    def __add_privacy_options(self, menu):
        """
        Options on the "Privacy" tab.
        """
        category_name = _("Privacy")
        addopt = partial(menu.add_option, category_name)

        incpriv = BooleanOption(_("Include records marked private"), False)
        incpriv.set_help(_('Whether to include private objects'))
        addopt( "incpriv", incpriv )

        self.__living = EnumeratedListOption(_("Living People"),
                                             LivingProxyDb.MODE_EXCLUDE_ALL)
        self.__living.add_item(LivingProxyDb.MODE_EXCLUDE_ALL, 
                               _("Exclude"))
        self.__living.add_item(LivingProxyDb.MODE_INCLUDE_LAST_NAME_ONLY, 
                               _("Include Last Name Only"))
        self.__living.add_item(LivingProxyDb.MODE_INCLUDE_FULL_NAME_ONLY, 
                               _("Include Full Name Only"))
        self.__living.add_item(_INCLUDE_LIVING_VALUE, 
                               _("Include"))
        self.__living.set_help(_("How to handle living people"))
        addopt( "living", self.__living )
        self.__living.connect('value-changed', self.__living_changed)

        self.__yearsafterdeath = NumberOption(_("Years from death to consider "
                                                 "living"), 30, 0, 100)
        self.__yearsafterdeath.set_help(_("This allows you to restrict "
                                          "information on people who have not "
                                          "been dead for very long"))
        addopt( "yearsafterdeath", self.__yearsafterdeath )

        self.__living_changed()

    def __add_download_options(self, menu):
        """
        Options for the download tab ...
        """

        category_name = _("Download")
        addopt = partial(menu.add_option, category_name)

        self.__incdownload = BooleanOption(_("Include download page"), False)
        self.__incdownload.set_help(_('Whether to include a database download option'))
        addopt( "incdownload", self.__incdownload )
        self.__incdownload.connect('value-changed', self.__download_changed)

        self.__down_fname1 = DestinationOption(_("Download Filename"),
            os.path.join(const.USER_HOME, ""))
        self.__down_fname1.set_help(_("File to be used for downloading of database"))
        addopt( "down_fname1", self.__down_fname1 )

        self.__dl_descr1 = StringOption(_("Description for download"), _('Smith Family Tree'))
        self.__dl_descr1.set_help(_('Give a description for this file.'))
        addopt( "dl_descr1", self.__dl_descr1 )

        self.__down_fname2 = DestinationOption(_("Download Filename"),
            os.path.join(const.USER_HOME, ""))
        self.__down_fname2.set_help(_("File to be used for downloading of database"))
        addopt( "down_fname2", self.__down_fname2 )

        self.__dl_descr2 = StringOption(_("Description for download"), _('Johnson Family Tree'))
        self.__dl_descr2.set_help(_('Give a description for this file.'))
        addopt( "dl_descr2", self.__dl_descr2 )

        self.__download_changed()

    def __add_advanced_options(self, menu):
        """
        Options on the "Advanced" tab.
        """
        category_name = _("Advanced Options")
        addopt = partial(menu.add_option, category_name)

        encoding = EnumeratedListOption(_('Character set encoding'), _CHARACTER_SETS[0][1] )
        for eopt in _CHARACTER_SETS:
            encoding.add_item(eopt[1], eopt[0])
        encoding.set_help( _("The encoding to be used for the web files"))
        addopt("encoding", encoding)

        linkhome = BooleanOption(_('Include link to active person on every page'), False)
        linkhome.set_help(_('Include a link to the active person (if they have a webpage)'))
        addopt("linkhome", linkhome)

        showbirth = BooleanOption(_("Include a column for birth dates on the index pages"), True)
        showbirth.set_help(_('Whether to include a birth column'))
        addopt( "showbirth", showbirth )

        showdeath = BooleanOption(_("Include a column for death dates on the index pages"), False)
        showdeath.set_help(_('Whether to include a death column'))
        addopt( "showdeath", showdeath )

        showpartner = BooleanOption(_("Include a column for partners on the "
                                    "index pages"), False)
        showpartner.set_help(_('Whether to include a partners column'))
        menu.add_option(category_name, 'showpartner', showpartner)

        showparents = BooleanOption(_("Include a column for parents on the "
                                      "index pages"), False)
        showparents.set_help(_('Whether to include a parents column'))
        addopt( "showparents", showparents )

        # This is programmed wrong, remove
        #showallsiblings = BooleanOption(_("Include half and/ or "
        #                                   "step-siblings on the individual pages"), False)
        #showallsiblings.set_help(_( "Whether to include half and/ or "
        #                            "step-siblings with the parents and siblings"))
        #menu.add_option(category_name, 'showhalfsiblings', showallsiblings)

        birthorder = BooleanOption(_('Sort all children in birth order'), False)
        birthorder.set_help(_('Whether to display children in birth order or in entry order?'))
        addopt( "birthorder", birthorder )

        inc_families = BooleanOption(_("Include family pages"), False)
        inc_families.set_help(_("Whether or not to include family pages."))
        addopt("inc_families", inc_families)

        inc_events = BooleanOption(_('Include event pages'), False)
        inc_events.set_help(_('Add a complete events list and relevant pages or not'))
        addopt( "inc_events", inc_events )

        inc_repository = BooleanOption(_('Include repository pages'), False)
        inc_repository.set_help(_('Whether or not to include the Repository Pages.'))
        addopt( "inc_repository", inc_repository )

        inc_gendex = BooleanOption(_('Include GENDEX file (/gendex.txt)'), False)
        inc_gendex.set_help(_('Whether to include a GENDEX file or not'))
        addopt( "inc_gendex", inc_gendex )

        inc_addressbook = BooleanOption(_("Include address book pages"), False)
        inc_addressbook.set_help(_("Whether or not to add Address Book pages,"
                                   "which can include e-mail and website "
                                   "addresses and personal address/ residence "
                                   "events."))
        addopt( "inc_addressbook", inc_addressbook )

    def __add_place_map_options(self, menu):
        """
        options for the Place Map tab.
        """
        category_name = _("Place Map Options")
        addopt = partial(menu.add_option, category_name)

        mapopts = [
            [_("Google"),        "Google"],
            [_("OpenStreetMap"), "OpenStreetMap"] ]
        self.__mapservice = EnumeratedListOption(_("Map Service"), mapopts[0][1])
        for trans, opt in mapopts:
            self.__mapservice.add_item(opt, trans)
        self.__mapservice.set_help(_("Choose your choice of map service for "
            "creating the Place Map Pages."))
        self.__mapservice.connect("value-changed", self.__placemap_options)
        addopt("mapservice", self.__mapservice)

        self.__placemappages = BooleanOption(_("Include Place map on Place Pages"), False)
        self.__placemappages.set_help(_("Whether to include a place map on the Place Pages, "
                                  "where Latitude/ Longitude are available."))
        self.__placemappages.connect("value-changed", self.__placemap_options)
        addopt("placemappages", self.__placemappages)

        self.__familymappages = BooleanOption(_("Include Family Map Pages with "
                                          "all places shown on the map"), False)
        self.__familymappages.set_help(_("Whether or not to add an individual page map "
                                     "showing all the places on this page. "
                                     "This will allow you to see how your family "
                                     "traveled around the country."))
        self.__familymappages.connect("value-changed", self.__placemap_options)
        addopt("familymappages", self.__familymappages)

        googleopts = [
            (_("Family Links"), "FamilyLinks"),
            (_("Drop"),         "Drop"),
            (_("Markers"),      "Markers") ]
        self.__googleopts = EnumeratedListOption(_("Google/ FamilyMap Option"), googleopts[0][1])
        for trans, opt in googleopts:
            self.__googleopts.add_item(opt, trans)
        self.__googleopts.set_help(_("Select which option that you would like "
            "to have for the Google Maps Family Map pages..."))
        addopt("googleopts", self.__googleopts)

        self.__placemap_options()

    def __archive_changed(self):
        """
        Update the change of storage: archive or directory
        """
        if self.__archive.get_value() == True:
            self.__target.set_extension(".tar.gz")
            self.__target.set_directory_entry(False)
        else:
            self.__target.set_directory_entry(True)

    def __update_filters(self):
        """
        Update the filter list based on the selected person
        """
        gid = self.__pid.get_value()
        person = self.__db.get_person_from_gramps_id(gid)
        filter_list = ReportUtils.get_person_filters(person, False)
        self.__filter.set_filters(filter_list)

    def __filter_changed(self):
        """
        Handle filter change. If the filter is not specific to a person,
        disable the person option
        """
        filter_value = self.__filter.get_value()
        if filter_value in [1, 2, 3, 4]:
            # Filters 1, 2, 3 and 4 rely on the center person
            self.__pid.set_available(True)
        else:
            # The rest don't
            self.__pid.set_available(False)

    def __stylesheet_changed(self):
        """
        Handles the changing nature of the stylesheet
        """

        css_opts = self.__css.get_value()
        if CSS[css_opts]["navigation"]: 
            self.__navigation.set_available(True)
        else:
            self.__navigation.set_available(False)

    def __graph_changed(self):
        """
        Handle enabling or disabling the ancestor graph
        """
        self.__graphgens.set_available(self.__ancestortree.get_value())

    def __gallery_changed(self):
        """
        Handles the changing nature of gallery
        """
        _gallery_option = self.__gallery.get_value()
        _create_thumbs_only_option = self.__create_thumbs_only.get_value()

        # images and media objects to be used, make all opti8ons available...
        if _gallery_option:
            self.__create_thumbs_only.set_available(True)
            self.__maxinitialimagewidth.set_available(True)
            self.__maxinitialimageheight.set_available(True)

            # thumbnail-sized images only...
            if _create_thumbs_only_option:
                self.__maxinitialimagewidth.set_available(False)
                self.__maxinitialimageheight.set_available(False)

            # full- sized images and Media Pages will be created... 
            else:
                self.__maxinitialimagewidth.set_available(True)
                self.__maxinitialimageheight.set_available(True)

        # no images or media objects are to be used...
        else:
            self.__create_thumbs_only.set_available(False)
            self.__maxinitialimagewidth.set_available(False)
            self.__maxinitialimageheight.set_available(False)

    def __living_changed(self):
        """
        Handle a change in the living option
        """
        if self.__living.get_value() == _INCLUDE_LIVING_VALUE:
            self.__yearsafterdeath.set_available(False)
        else:
            self.__yearsafterdeath.set_available(True)

    def __download_changed(self):
        """
        Handles the changing nature of include download page
        """

        if self.__incdownload.get_value():
            self.__down_fname1.set_available(True)
            self.__dl_descr1.set_available(True)
            self.__down_fname2.set_available(True)
            self.__dl_descr2.set_available(True)
        else:
            self.__down_fname1.set_available(False)
            self.__dl_descr1.set_available(False)
            self.__down_fname2.set_available(False)
            self.__dl_descr2.set_available(False)

    def __placemap_options(self):
        """
        Handles the changing nature of the place map Options
        """
        # get values for all Place Map Options tab...
        place_active = self.__placemappages.get_value()
        family_active = self.__familymappages.get_value()
        mapservice_opts = self.__mapservice.get_value()
        google_opts = self.__googleopts.get_value()

        if (place_active or family_active):
            self.__mapservice.set_available(True)
        else:
            self.__mapservice.set_available(False)

        if (family_active and mapservice_opts == "Google"):
            self.__googleopts.set_available(True)
        else:
            self.__googleopts.set_available(False)

# FIXME. Why do we need our own sorting? Why not use Sort.Sort?
def sort_people(dbase, handle_list):
    """
    will sort the database people by surname
    """
    sname_sub = defaultdict(list)
    sortnames = {}

    for person_handle in handle_list:
        person = dbase.get_person_from_handle(person_handle)
        primary_name = person.get_primary_name()

        if primary_name.group_as:
            surname = primary_name.group_as
        else:
            surname = dbase.get_name_group_mapping(
                            _nd.primary_surname(primary_name))

        sortnames[person_handle] = _nd.sort_string(primary_name)
        sname_sub[surname].append(person_handle)

    sorted_lists = []
    temp_list = sorted(sname_sub, key=locale.strxfrm)
    
    for name in temp_list:
        slist = sorted(((sortnames[x], x) for x in sname_sub[name]), 
                    key=lambda x:locale.strxfrm(x[0]))
        entries = [x[1] for x in slist]
        sorted_lists.append((name, entries))

    return sorted_lists

def sort_event_types(dbase, event_types, event_handle_list):
    """
    sort a list of event types and their associated event handles

    @param: dbase -- report database
    @param: event_types -- a dict of event types
    @param: event_handle_list -- all event handles in this database
    """

    event_dict = dict( (evt_type, []) for evt_type in event_types)

    for handle in event_handle_list:

        event = dbase.get_event_from_handle(handle)
        etype = str(event.type)

        # add (gramps_id, date, handle) from this event
        if etype in event_dict:
            event_dict[etype].append( handle )

    for tup_list in event_dict.values():
        tup_list.sort()

    # return a list of sorted tuples, one per event
    retval = [(event_type, event_list) for (event_type, event_list) in event_dict.iteritems()]
    retval.sort(key=lambda item: str(item[0]))
    return retval

# Modified _get_regular_surname from WebCal.py to get prefix, first name, and suffix
def _get_short_name(gender, name):
    """ Will get suffix for all people passed through it """
    short_name = name.get_first_name()
    suffix = name.get_suffix()
    if suffix:
        short_name = short_name + ", " + suffix
    return short_name

def __get_person_keyname(dbase, handle):
    """ .... """
    person = dbase.get_person_from_handle(handle)
    return _nd.sort_string(person.get_primary_name())

def __get_place_keyname(dbase, handle):
    """ ... """

    return ReportUtils.place_name(dbase, handle)  

def first_letter(string):
    """
    recieves a string and returns the first letter
    """
    if string:
        letter = normalize('NFKC', unicode(string))[0].upper()
    else:
        letter = u' '
    # See : http://www.gramps-project.org/bugs/view.php?id = 2933
    (lang_country, modifier ) = locale.getlocale()
    if lang_country == "sv_SE" and (letter == u'W' or letter == u'V'):
        letter = u'V,W'
    # See : http://www.gramps-project.org/bugs/view.php?id = 4423
    elif (lang_country == "cs_CZ" or lang_country == "sk_SK") and letter == u'C' and len(string) > 1:
        second_letter = normalize('NFKC', unicode(string))[1].upper()
        if second_letter == u'H':
            letter += u'h'
    elif lang_country == "sk_SK" and letter == u'D' and len(string) > 1:
        second_letter = normalize('NFKC', unicode(string))[1].upper()
        if second_letter == u'Z':
            letter += u'z'
        elif second_letter == u'Ž':
            letter += u'ž'
    return letter

def get_first_letters(dbase, menu_set, key):
    """
    get the first letters of the menu_set

    @param: menu_set = one of a handle list for either person or place handles 
        or an evt types list
    @param: key = either a person, place, or event type
    """
 
    first_letters = []

    for menu_item in menu_set:
        if key == _KEYPERSON:
            keyname = __get_person_keyname(dbase, menu_item)

        elif key == _KEYPLACE:
            keyname = __get_place_keyname(dbase, menu_item)

        else:
            keyname = menu_item
        ltr = first_letter(keyname)

        first_letters.append(ltr)

    # return menu set letters for alphabet_navigation
    return first_letters

def alphabet_navigation(menu_set):
    """
    Will create the alphabet navigation bar for classes IndividualListPage,
    SurnameListPage, PlaceListPage, and EventList

    @param: menu_set -- a dictionary of either letters or words
    """
    sorted_set = defaultdict(int)
    # The comment below from the glibc locale sv_SE in
    # localedata/locales/sv_SE :
    #
    # % The letter w is normally not present in the Swedish alphabet. It
    # % exists in some names in Swedish and foreign words, but is accounted
    # % for as a variant of 'v'.  Words and names with 'w' are in Swedish
    # % ordered alphabetically among the words and names with 'v'. If two
    # % words or names are only to be distinguished by 'v' or % 'w', 'v' is
    # % placed before 'w'.
    #
    # See : http://www.gramps-project.org/bugs/view.php?id = 2933
    #
    (lang_country, modifier) = locale.getlocale()

    for menu_item in menu_set:
        sorted_set[menu_item] += 1

    # remove the number of each occurance of each letter
    sorted_alpha_index = sorted(sorted_set, key = locale.strxfrm)

    # if no letters, return None to its callers
    if not sorted_alpha_index:
        return None, []

    num_ltrs = len(sorted_alpha_index)
    num_of_cols = 32
    num_of_rows = ((num_ltrs // num_of_cols) + 1)

    # begin alphabet navigation division
    with Html("div", id = "alphanav") as alphabetnavigation:

        index = 0
        for row in xrange(num_of_rows):
            unordered = Html("ul") 
            alphabetnavigation += unordered

            cols = 0
            while (cols <= num_of_cols and index < num_ltrs):
                menu_item = sorted_alpha_index[index]

                if lang_country == "sv_SE" and menu_item == u'V':
                    hyper = Html("a", "V,W", href = "#V,W", title = "V,W")
                else:
                    # adding title to hyperlink menu for screen readers and braille writers
                    title_str = _("Alphabet Menu: %s") % menu_item
                    hyper = Html("a", menu_item, title = title_str, href = "#%s" % menu_item)
                unordered.extend(
                    Html("li", hyper, inline = True)
                )

                # increase letter/ word in sorted_alpha_index
                index += 1
                cols += 1
            num_of_rows -= 1

    # return alphabet navigation, and menu_set to its callers
    # EventListPage will reuse sorted_alpha_index
    return alphabetnavigation, sorted_alpha_index

def _has_webpage_extension(url):
    """
    determine if a filename has an extension or not...

    url = filename to be checked
    """
    return any(url.endswith(ext) for ext in _WEB_EXT) 

def add_birthdate(dbase, ppl_handle_list):
    """
    This will sort a list of child handles in birth order
    """
    sortable_individuals = []
    birth_date = False
    for phandle in ppl_handle_list:
        person = dbase.get_person_from_handle(phandle)
        if person:

            # get birth date: if birth_date equals nothing, then generate a fake one?
            birth_ref = person.get_birth_ref()
            birth_date = gen.lib.Date.EMPTY
            if birth_ref:
                birth = dbase.get_event_from_handle(birth_ref.ref)
                if birth:
                    birth_date = birth.get_date_object().get_sort_value()
        sortable_individuals.append((birth_date, phandle))

    # return a list of handles with the individual's birthdate attached
    return sortable_individuals

def _find_birth_date(dbase, individual):
    """
    will look for a birth date within the person's events
    """
    date_out = None
    birth_ref = individual.get_birth_ref()
    if birth_ref:
        birth = dbase.get_event_from_handle(birth_ref.ref)
        if birth:
            date_out = birth.get_date_object()
            date_out.fallback = False
    else:
        person_evt_ref_list = individual.get_primary_event_ref_list()
        if person_evt_ref_list:
            for evt_ref in person_evt_ref_list:
                event = dbase.get_event_from_handle(evt_ref.ref)
                if event:
                    if event.get_type().is_birth_fallback():
                        date_out = event.get_date_object()
                        date_out.fallback = True
                        log.debug("setting fallback to true for '%s'" % (event))
                        break
    return date_out

def _find_death_date(dbase, individual):
    """
    will look for a death date within a person's events
    """
    date_out = None
    death_ref = individual.get_death_ref()
    if death_ref:
        death = dbase.get_event_from_handle(death_ref.ref)
        if death:
            date_out = death.get_date_object()
            date_out.fallback = False
    else:
        person_evt_ref_list = individual.get_primary_event_ref_list()
        if person_evt_ref_list: 
            for evt_ref in person_evt_ref_list:
                event = dbase.get_event_from_handle(evt_ref.ref)
                if event:
                    if event.get_type().is_death_fallback():
                        date_out = event.get_date_object()
                        date_out.fallback = True
                        log.debug("setting fallback to true for '%s'" % (event))
                        break
    return date_out

def build_event_data_by_individuals(dbase, ppl_handle_list):
    """
    creates a list of event handles and event types for this database
    """
    event_handle_list = []
    event_types = []

    for phandle in ppl_handle_list:
        person = dbase.get_person_from_handle(phandle)
        if person:

            evt_ref_list = person.get_event_ref_list()
            if evt_ref_list:
                for evt_ref in evt_ref_list:
                    event = dbase.get_event_from_handle(evt_ref.ref)
                    if event:

                        event_types.append(str(event.get_type()))
                        event_handle_list.append(evt_ref.ref)

            person_family_handle_list = person.get_family_handle_list()
            if person_family_handle_list:
                for fhandle in person_family_handle_list:
                    family = dbase.get_family_from_handle(fhandle)
                    if family:

                        family_evt_ref_list = family.get_event_ref_list()
                        if family_evt_ref_list:
                            for evt_ref in family_evt_ref_list:
                                event = dbase.get_event_from_handle(evt_ref.ref)
                                if event:  
                                    event_types.append(str(event.type))
                                    event_handle_list.append(evt_ref.ref)
            
    # return event_handle_list and event types to its caller
    return event_handle_list, event_types

def build_event_data_by_events(dbase_, event_handles):
    """
    creates a list of event handles and event types for these event handles
    """
    event_handle_list = []
    event_types = []

    for event_handle in event_handles:
        event = dbase_.get_event_from_handle(event_handle)
        if event:
            event_types.append(str(event.get_type()))
            event_handle_list.append(event_handle)

    return event_handle_list, event_types

def check_person_database(phandle, ppl_handle_list):
    """
    check to see if a person is in the report database

    @param: person -- person object from the database presumably
    """
    return any(person_handle == phandle for person_handle in ppl_handle_list)
