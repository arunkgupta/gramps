#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
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
Package providing filter rules for GRAMPS.
"""

__author__ = "Don Allingham"

# Need to expose this to be available for filter plugins:
# the plugins should say: from Filters.Rules import Rule
from _Rule import Rule

from _Everything import Everything
from _HasGrampsId import HasGrampsId
from _IsPrivate import IsPrivate
from _HasTextMatchingSubstringOf import HasTextMatchingSubstringOf
from _HasTextMatchingRegexpOf import HasTextMatchingRegexpOf

import Person
import Family
import Event
import Source
import Place
import MediaObject
import Repository
