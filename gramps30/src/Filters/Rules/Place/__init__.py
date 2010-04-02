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

from _AllPlaces import AllPlaces
from _HasIdOf import HasIdOf
from _RegExpIdOf import RegExpIdOf
from _HasNoteRegexp import HasNoteRegexp
from _HasNoteMatchingSubstringOf import HasNoteMatchingSubstringOf
from _HasReferenceCountOf import HasReferenceCountOf
from _PlacePrivate import PlacePrivate
from _MatchesFilter import MatchesFilter
from _HasPlace import HasPlace
from _HasNoLatOrLon import HasNoLatOrLon
from _InLatLonNeighborhood import InLatLonNeighborhood
from _MatchesEventFilter import MatchesEventFilter

editor_rule_list = [
    AllPlaces,
    HasIdOf,
    RegExpIdOf,
    HasNoteRegexp,
    HasNoteMatchingSubstringOf,
    HasReferenceCountOf,
    PlacePrivate,
    MatchesFilter,
    HasPlace,
    HasNoLatOrLon,
    InLatLonNeighborhood,
    MatchesEventFilter,
]
