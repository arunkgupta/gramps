# encoding:utf-8
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011 Serge Noiraud
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

# $Id: htmlrenderer.gpr.py 14843 2011-03-15 22:15:29Z snoiraud $

#------------------------------------------------------------------------
#
# Geography view
#
#------------------------------------------------------------------------

register(VIEW, 
         id    = 'personmap',
         name  = _("person"),
         description =  _("A view allowing to see the places visited by "
                          "one person during his life."),
         version = '1.0',
         gramps_target_version = '3.4',
         status = STABLE,
         fname = 'geoperson.py',
         authors = [u"Serge Noiraud"],
         authors_email = [""],
         category = ("Geography", _("Geography")),
         viewclass = 'GeoPerson',
         order = START,
         stock_icon = 'geo-show-person',
  )

register(VIEW, 
         id    = 'placesmap',
         name  = _("place"),
         description =  _("A view allowing to see all places of the database."),
         version = '1.0',
         gramps_target_version = '3.4',
         status = STABLE,
         fname = 'geoplaces.py',
         authors = [u"Serge Noiraud"],
         authors_email = [""],
         category = ("Geography", _("Geography")),
         viewclass = 'GeoPlaces',
         stock_icon = 'geo-show-place',
  )

register(VIEW, 
         id    = 'eventsmap',
         name  = _("event"),
         description =  _("A view allowing to see all events "
                          "places of the database."),
         version = '1.0',
         gramps_target_version = '3.4',
         status = STABLE,
         fname = 'geoevents.py',
         authors = [u"Serge Noiraud"],
         authors_email = [""],
         category = ("Geography", _("Geography")),
         viewclass = 'GeoEvents',
         stock_icon = 'geo-show-event',
  )

register(VIEW, 
         id    = 'familymap',
         name  = _("family"),
         description =  _("A view allowing to see the places visited by "
                          "one family during all their life."),
         version = '1.0',
         gramps_target_version = '3.4',
         status = STABLE,
         fname = 'geofamily.py',
         authors = [u"Serge Noiraud"],
         authors_email = [""],
         category = ("Geography", _("Geography")),
         viewclass = 'GeoFamily',
         stock_icon = 'geo-show-family',
  )

