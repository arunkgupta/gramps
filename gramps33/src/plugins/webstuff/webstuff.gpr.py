# encoding:utf-8
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2010 Doug Blank <doug.blank@gmail.com>
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

# $Id $

#------------------------------------------------------------------------
#
# Stylesheets
#
#------------------------------------------------------------------------
register(GENERAL, 
id    = 'system webstuff',
category = "WEBSTUFF",
name  = _("Webstuff"),
description =  _("Provides a collection of resources for the web"),
version = '1.0',
gramps_target_version = '3.3',
fname = "webstuff.py",
load_on_reg = True,
process = "process_list",
status = STABLE
  )