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

from _allmedia import AllMedia
from _hasidof import HasIdOf
from _regexpidof import RegExpIdOf
from _hasnoteregexp import HasNoteRegexp
from _hasnotematchingsubstringof import HasNoteMatchingSubstringOf
from _hasreferencecountof import HasReferenceCountOf
from _mediaprivate import MediaPrivate
from _matchesfilter import MatchesFilter
from _hasmedia import HasMedia
from _hasattribute import HasAttribute
from _changedsince import ChangedSince
from _hastag import HasTag

editor_rule_list = [
    AllMedia,
    HasIdOf,
    RegExpIdOf,
    HasNoteRegexp,
    HasNoteMatchingSubstringOf,
    HasReferenceCountOf,
    MediaPrivate,
    MatchesFilter,
    HasAttribute,
    ChangedSince,
    HasTag,
]
