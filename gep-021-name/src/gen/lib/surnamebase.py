#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2010  Benny Malengier
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
SurnameBase class for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib.surname import Surname
from gen.lib.const import IDENTICAL, EQUAL

#-------------------------------------------------------------------------
#
# SurnameBase classes
#
#-------------------------------------------------------------------------
class SurnameBase(object):
    """
    Base class for surname-aware objects.
    """

    def __init__(self, source=None):
        """
        Initialize a SurnameBase. 
        
        If the source is not None, then object is initialized from values of 
        the source object.

        :param source: Object used to initialize the new object
        :type source: SurnameBase
        """
        self.surname_list = map(Surname, source.surname_list) if source else []

    def serialize(self):
        """
        Convert the object to a serialized tuple of data.
        """
        return [surname.serialize() for surname in self.surname_list]

    def unserialize(self, data):
        """
        Convert a serialized tuple of data to an object.
        """
        self.surname_list = [Surname().unserialize(item) for item in data]

    def add_surname(self, surname):
        """
        Add the :class:`~gen.lib.surname.Surname` instance to the object's 
        list of surnames.

        :param surname: :class:`~gen.lib.surname.Surname` instance to add to 
        the object's address list.
        :type address: list
        """
        self.surname_list.append(surname)

    def remove_surname(self, surname):
        """
        Remove the specified :class:`~gen.lib.surname.Surname` instance from 
        the surname list.
        
        If the instance does not exist in the list, the operation has
        no effect.

        :param surname: :class:`~gen.lib.surname.Surname` instance to remove 
            from the list
        :type surname: :class:`~gen.lib.surname.Surname`

        :returns: True if the surname was removed, False if it was not in the list.
        :rtype: bool
        """
        if surname in self.surname_list:
            self.surname_list.remove(surname)
            return True
        else:
            return False

    def get_surname_list(self):
        """
        Return the list of :class:`~gen.lib.surname.Surname` instances a
        ssociated with the object.

        :returns: Returns the list of :class:`~gen.lib.surname.Surname` instances
        :rtype: list
        """
        return self.surname_list

    def set_surname_list(self, surname_list):
        """
        Assign the passed list to the object's list of 
        :class:`~gen.lib.surname.Surname` instances.
        
        :param surname_list: List of :class:`~gen.lib.surname.surname` instances
            to be associated with the object
        :type surname_list: list
        """
        self.surname_list = surname_list

    def primary_surname(self):
        """
        Return the surname that is the primary surname
        
        :returns: Returns the surname instance that 
            is the primary surname. If primary not set, and there is a surname,
            the first surname is given, if no surnames, None is returned
        :rtype: :class:`~gen.lib.surname.Surname` or None
        """
        for surname in self.surname_list:
            if surname.primary:
                return surname
        if self.surname_list:
            return self.surname_list[0]
        return None

    def set_primary_surname(self, surnamenr=0):
        """
        Set the surname with surnamenr in the surname list as primary surname
        Counting starts at 0
        """
        if surnamenr >= len(self.surname_list):
            return
        for surname in self.surname_list:
            surname.set_primary(False)
        self.surname_list[surnamenr].set_primary(True)

    def _merge_surname_list(self, acquisition):
        """
        Merge the list of surname from acquisition with our own.

        :param acquisition: the surname list of this object will be merged with
            the current address list.
        :rtype acquisition: SurnameBase
        """
        surname_list = self.surname_list[:]
        for addendum in acquisition.get_surname_list():
            for surname in surname_list:
                equi = surname.is_equivalent(addendum)
                if equi == IDENTICAL:
                    break
                elif equi == EQUAL:
                    surname.merge(addendum)
                    break
            else:
                self.surname_list.append(addendum)
