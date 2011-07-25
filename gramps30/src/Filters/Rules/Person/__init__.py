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

# $Id:__init__.py 9912 2008-01-22 09:17:46Z acraphae $

"""
Package providing filter rules for GRAMPS.
"""

from _Disconnected import Disconnected
from _Everyone import Everyone
from _FamilyWithIncompleteEvent import FamilyWithIncompleteEvent
from _HasAttribute import HasAttribute
from _HasBirth import HasBirth
from _HasCommonAncestorWith import HasCommonAncestorWith
from _HasCommonAncestorWithFilterMatch import HasCommonAncestorWithFilterMatch
from _HasCompleteRecord import HasCompleteRecord
from _HasDeath import HasDeath
from _HasEvent import HasEvent
from _HasFamilyAttribute import HasFamilyAttribute
from _HasFamilyEvent import HasFamilyEvent
from _HasIdOf import HasIdOf
from _HasNameOf import HasNameOf
from _HasNote import HasNote
from _HasNoteMatchingSubstringOf import HasNoteMatchingSubstringOf
from _HasNoteRegexp import HasNoteRegexp
from _HasRelationship import HasRelationship
from _HasSourceOf import HasSourceOf
from _HasTextMatchingRegexpOf import HasTextMatchingRegexpOf
from _HasTextMatchingSubstringOf import HasTextMatchingSubstringOf
from _HasUnknownGender import HasUnknownGender
from _HasMarkerOf import HasMarkerOf
from _HaveAltFamilies import HaveAltFamilies
from _HaveChildren import HaveChildren
from _HavePhotos import HavePhotos
from _IncompleteNames import IncompleteNames
from _IsAncestorOf import IsAncestorOf
from _IsAncestorOfFilterMatch import IsAncestorOfFilterMatch
from _IsBookmarked import IsBookmarked
from _IsChildOfFilterMatch import IsChildOfFilterMatch
from _IsDefaultPerson import IsDefaultPerson
from _IsDescendantFamilyOf import IsDescendantFamilyOf
from _IsDescendantOf import IsDescendantOf
from _IsDescendantOfFilterMatch import IsDescendantOfFilterMatch
from _IsFemale import IsFemale
from _IsLessThanNthGenerationAncestorOf import \
     IsLessThanNthGenerationAncestorOf
from _IsLessThanNthGenerationAncestorOfBookmarked import \
     IsLessThanNthGenerationAncestorOfBookmarked
from _IsLessThanNthGenerationAncestorOfDefaultPerson import \
     IsLessThanNthGenerationAncestorOfDefaultPerson
from _IsLessThanNthGenerationDescendantOf import \
     IsLessThanNthGenerationDescendantOf
from _IsMale import IsMale
from _IsMoreThanNthGenerationAncestorOf import \
     IsMoreThanNthGenerationAncestorOf
from _IsMoreThanNthGenerationDescendantOf import \
     IsMoreThanNthGenerationDescendantOf
from _IsParentOfFilterMatch import IsParentOfFilterMatch
from _IsSiblingOfFilterMatch import IsSiblingOfFilterMatch
from _IsSpouseOfFilterMatch import IsSpouseOfFilterMatch
from _IsWitness import IsWitness
from _MatchesFilter import MatchesFilter
from _MatchesEventFilter import MatchesEventFilter
from _MissingParent import MissingParent
from _MultipleMarriages import MultipleMarriages
from _NeverMarried import NeverMarried
from _NoBirthdate import NoBirthdate
from _PeoplePrivate import PeoplePrivate
from _PersonWithIncompleteEvent import PersonWithIncompleteEvent
from _ProbablyAlive import ProbablyAlive
from _RelationshipPathBetween import RelationshipPathBetween
from _RelationshipPathBetweenBookmarks import RelationshipPathBetweenBookmarks
from Filters.Rules._Rule import Rule
from _SearchName import SearchName
from _RegExpName import RegExpName
from _MatchIdOf import MatchIdOf
from _RegExpIdOf import RegExpIdOf


#-------------------------------------------------------------------------
#
# This is used by Custom Filter Editor tool
#
#-------------------------------------------------------------------------
editor_rule_list = [
    Everyone,
    IsFemale,
    HasUnknownGender,
    IsMale,
    IsDefaultPerson,
    IsBookmarked,
    HasIdOf,
    HasNameOf,
    HasRelationship,
    HasDeath,
    HasBirth,
    HasCompleteRecord,
    HasEvent,
    HasFamilyEvent,
    HasAttribute,
    HasFamilyAttribute,
    HasSourceOf,
    HasMarkerOf,
    HaveAltFamilies,
    HavePhotos,
    HaveChildren,
    IncompleteNames,
    NeverMarried,
    MultipleMarriages,
    NoBirthdate,
    PersonWithIncompleteEvent,
    FamilyWithIncompleteEvent,
    ProbablyAlive,
    PeoplePrivate,
    IsWitness,
    IsDescendantOf,
    IsDescendantFamilyOf,
    IsLessThanNthGenerationAncestorOfDefaultPerson,
    IsDescendantOfFilterMatch,
    IsLessThanNthGenerationDescendantOf,
    IsMoreThanNthGenerationDescendantOf,
    IsAncestorOf,
    IsAncestorOfFilterMatch,
    IsLessThanNthGenerationAncestorOf,
    IsLessThanNthGenerationAncestorOfBookmarked,
    IsMoreThanNthGenerationAncestorOf,
    HasCommonAncestorWith,
    HasCommonAncestorWithFilterMatch,
    MatchesFilter,
    MatchesEventFilter,
    MissingParent,
    IsChildOfFilterMatch,
    IsParentOfFilterMatch,
    IsSpouseOfFilterMatch,
    IsSiblingOfFilterMatch,
    RelationshipPathBetween,
    RelationshipPathBetweenBookmarks,
    HasTextMatchingSubstringOf,
    HasNote,
    HasNoteRegexp,
    HasNoteMatchingSubstringOf,
    RegExpIdOf,
    Disconnected,
]
