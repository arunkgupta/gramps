#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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

# plugins/view/placetreeview.gpr.py
# $Id$

register(VIEW, 
         id = 'placetreeview',
         name = _("Place Tree View"),
         description =  _("A view displaying places in a tree format."),
         version = '1.0',
         gramps_target_version = '3.5',
         status = STABLE,
         fname = 'placetreeview.py',
         authors = [u"Donald N. Allingham", u"Gary Burton", u"Nick Hall"],
         authors_email = [""],
         category = ("Places", _("Places")),
         viewclass = 'PlaceTreeView',
         stock_icon = 'gramps-tree-group',
  )
