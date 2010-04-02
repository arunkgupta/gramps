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

# $Id$

"""
Provide sorting routines for use in GRAMPS. Since these functions are
intended to provide fast sorting, they tend to bypass access methods, 
and directly use class members. For this reason, care needs to be taken
to make sure these remain in sync with the rest of the design.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import locale

#-------------------------------------------------------------------------
#
# GRAMPS Modules
#
#-------------------------------------------------------------------------
from gen.lib import Date
from BasicUtils import name_displayer as _nd
from ReportBase import ReportUtils

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------

class Sort:
    
    def __init__(self, database):
        self.database = database

    def by_last_name(self, first_id, second_id):
        """Sort routine for comparing two last names. If last names are equal, 
        uses the given name and suffix"""
        first = self.database.get_person_from_handle(first_id)
        second = self.database.get_person_from_handle(second_id)
        
        name1 = first.get_primary_name()
        name2 = second.get_primary_name()

        fsn = name1.get_surname()
        ssn = name2.get_surname()

        if fsn == ssn :
            ffn = name1.get_first_name()
            sfn = name2.get_first_name()
            if ffn == sfn:
                return locale.strcoll(name1.get_suffix(), name2.get_suffix())
            else:
                return locale.strcoll(ffn, sfn)
        else:
            return locale.strcoll(fsn, ssn)

    def by_sorted_name(self, first_id, second_id):
        """
        Sort routine for comparing two displayed names.
        """

        first = self.database.get_person_from_handle(first_id)
        second = self.database.get_person_from_handle(second_id)

        name1 = _nd.sorted(first)
        name2 = _nd.sorted(second)

        return locale.strcoll(name1, name2)

    def by_birthdate(self, first_id, second_id):
        """Sort routine for comparing two people by birth dates. If the birth dates
        are equal, sorts by name"""
        first = self.database.get_person_from_handle(first_id)
        second = self.database.get_person_from_handle(second_id)

        birth1 = ReportUtils.get_birth_or_fallback(self.database, first)
        if birth1:
            date1 = birth1.get_date_object()
        else:
            date1 = Date()

        birth2 = ReportUtils.get_birth_or_fallback(self.database, second)
        if birth2:
            date2 = birth2.get_date_object()
        else:
            date2 = Date()

        dsv1 = date1.get_sort_value()
        dsv2 = date2.get_sort_value()

        val = cmp(dsv1, dsv2)
        if val == 0:
            return self.by_last_name(first_id, second_id)
        return val

    def by_date(self, a_id, b_id):
        """Sort routine for comparing two events by their dates. """
        if not (a_id and b_id):
            return 0
        a_obj = self.database.get_event_from_handle(a_id)
        b_obj = self.database.get_event_from_handle(b_id)
        return cmp(a_obj.get_date_object(), b_obj.get_date_object())

    def by_place_title(self, a_id, b_id):
        """Sort routine for comparing two events by their dates. """
        if not (a_id and b_id):
            return 0
        a_obj = self.database.get_place_from_handle(a_id)
        b_obj = self.database.get_place_from_handle(b_id)
        return locale.strcoll(a_obj.title, b_obj.title)
    
    def by_media_title(self,a_id,b_id):
        """Sort routine for comparing two media objects by their title. """
        if not (a_id and b_id):
            return False
        a = self.database.get_object_from_handle(a_id)
        b = self.database.get_object_from_handle(b_id)
        return locale.strcoll(a.desc,b.desc)
    
