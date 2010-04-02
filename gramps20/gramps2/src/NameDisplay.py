#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2005  Donald N. Allingham
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
Class handling language-specific displaying of names.
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import RelLib

#-------------------------------------------------------------------------
#
# NameDisplay class
#
#-------------------------------------------------------------------------
class NameDisplay:
    """
    Base class for displaying of Name instances.
    """
    def __init__(self,use_upper=False):
        """
        Creates a new NameDisplay class.

        @param use_upper: True indicates that the surname should be
        displayed in upper case.
        @type use_upper: bool
        """
        self.force_upper = use_upper

    def use_upper(self,upper):
        """
        Changes the NameDisplay class to enable or display the displaying
        of surnames in upper case.
        
        @param upper: True indicates that the surname should be
        displayed in upper case.
        @type upper: bool
        """
        self.force_upper = upper

    def sorted(self,person):
        """
        Returns a text string representing the L{RelLib.Person} instance's
        L{RelLib.Name} in a manner that should be used for displaying a sorted
        name.

        @param person: L{RelLib.Person} instance that contains the
        L{RelLib.Name} that is to be displayed. The primary name is used for
        the display.
        @type person: L{RelLib.Person}
        @returns: Returns the L{RelLib.Person} instance's name
        @rtype: str
        """
        name = person.get_primary_name()
        if name.sort_as == RelLib.Name.FNLN:
            return self._fnln(name)
        elif name.sort_as == RelLib.Name.PTFN:
            return self._ptfn(name)
        elif name.sort_as == RelLib.Name.FN:
            return name.first_name
        else:
            return self._lnfn(name)

    def sorted_name(self,name):
        """
        Returns a text string representing the L{RelLib.Name} instance
        in a manner that should be used for displaying a sorted
        name.

        @param name: L{RelLib.Name} instance that is to be displayed.
        @type name: L{RelLib.Name}
        @returns: Returns the L{RelLib.Name} string representation
        @rtype: str
        """
        if name.sort_as == RelLib.Name.FNLN:
            return self._fnln(name)
        elif name.sort_as == RelLib.Name.PTFN:
            return self._ptfn(name)
        elif name.sort_as == RelLib.Name.FN:
            return name.first_name
        else:
            return self._lnfn(name)

    def display_given(self,person):
        name = person.get_primary_name()
        if name.patronymic:
            return "%s %s" % (name.first_name, name.patronymic)
        else:
            return name.first_name

    def display(self,person):
        """
        Returns a text string representing the L{RelLib.Person} instance's
        L{RelLib.Name} in a manner that should be used for normal displaying.

        @param person: L{RelLib.Person} instance that contains the
        L{RelLib.Name} that is to be displayed. The primary name is used for
        the display.
        @type person: L{RelLib.Person}
        @returns: Returns the L{RelLib.Person} instance's name
        @rtype: str
        """
        name = person.get_primary_name()
        if name.display_as == RelLib.Name.LNFN:
            return self._lnfn(name,"")
        else:
            return self._fnln(name,"")

    def display_formal(self,person):
        """
        Returns a text string representing the L{RelLib.Person} instance's
        L{RelLib.Name} in a manner that should be used for normal displaying.

        @param person: L{RelLib.Person} instance that contains the
        L{RelLib.Name} that is to be displayed. The primary name is used for
        the display.
        @type person: L{RelLib.Person}
        @returns: Returns the L{RelLib.Person} instance's name
        @rtype: str
        """
        name = person.get_primary_name()
        if name.display_as == RelLib.Name.LNFN:
            return self._lnfn(name,'')
        else:
            return self._fnln(name,'')

    def display_with_nick(self,person):
        """
        Returns a text string representing the L{RelLib.Person} instance's
        L{RelLib.Name} in a manner that should be used for normal displaying.

        @param person: L{RelLib.Person} instance that contains the
        L{RelLib.Name} that is to be displayed. The primary name is used for
        the display.
        @type person: L{RelLib.Person}
        @returns: Returns the L{RelLib.Person} instance's name
        @rtype: str
        """
        name = person.get_primary_name()
        if name.display_as == RelLib.Name.LNFN:
            return self._lnfn(name,person.get_nick_name())
        else:
            return self._fnln(name,person.get_nick_name())

    def display_name(self,name):
        """
        Returns a text string representing the L{RelLib.Name} instance
        in a manner that should be used for normal displaying.

        @param name: L{RelLib.Name} instance that is to be displayed.
        @type name: L{RelLib.Name}
        @returns: Returns the L{RelLib.Name} string representation
        @rtype: str
        """
        if name == None:
            return ""
        elif name.display_as == RelLib.Name.LNFN:
            return self._lnfn(name)
        elif name.display_as == RelLib.Name.PTFN:
            return self._ptfn(name)
        else:
            return self._fnln(name)

    def _ptfn(self,name):
        """
        Prints the Western style first name, last name style.
        Typically this is::

           SurnamePrefix Patronymic SurnameSuffix, FirstName
        """

        first = name.first_name

        if self.force_upper:
            last = name.patronymic.upper()
        else:
            last = name.patronymic
            
        if name.suffix == "":
            if name.prefix:
                return "%s %s, %s" % (name.prefix, last, first)
            else:
                return "%s, %s" % (last, first)
        else:
            if name.prefix:
                return "%s %s %s, %s" % (name.prefix, last, name.suffix, first)
            else:
                return "%s %s, %s" % (last, name.suffix, first)
        
    def _fnln(self,name,nickname=""):
        """
        Prints the Western style first name, last name style.
        Typically this is::

           FirstName Patronymic SurnamePrefix Surname SurnameSuffix
        """

        first = name.first_name

        if nickname:
            first = '%s "%s"' % (first,nickname)
            
        if name.patronymic:
            first = "%s %s" % (first, name.patronymic)

        if self.force_upper:
            last = name.surname.upper()
        else:
            last = name.surname
            
        if name.suffix == "":
            if name.prefix:
                return "%s %s %s" % (first, name.prefix, last)
            else:
                return "%s %s" % (first, last)
        else:
            if name.prefix:
                return "%s %s %s, %s" % (first, name.prefix, last, name.suffix)
            else:
                return "%s %s, %s" % (first, last, name.suffix)

    def name_grouping(self,db,person):
        return self.name_grouping_name(db,person.primary_name)

    def name_grouping_name(self,db,pn):
        sv = pn.sort_as
        if pn.group_as:
            return pn.group_as
        if sv <= RelLib.Name.LNFN:
            val = pn.surname
        elif sv == RelLib.Name.PTFN:
            val = pn.patronymic
        else:
            val = pn.first_name
        return db.get_name_group_mapping(val)
        
    def _lnfn(self,name,nickname=u""):
        """
        Prints the Western style last name, first name style.
        Typically this is::

            SurnamePrefix Surname, FirstName Patronymic SurnameSuffix
        """

        first = name.first_name

        if nickname:
            first = '%s "%s"' % (first,nickname)
            
        if name.patronymic:
            first = "%s %s" % (first, name.patronymic)

        if self.force_upper:
            last = name.surname.upper()
        else:
            last = name.surname

        if last:
            last += ","

        if name.suffix:
            if name.prefix:
                return "%s %s %s %s" % (name.prefix, last, first, name.suffix)
            else:
                return "%s %s %s" % (last, first, name.suffix)
        else:
            if name.prefix:
                return "%s %s %s" % (name.prefix, last, first)
            else:
                return "%s %s" % (last, first)

    
displayer = NameDisplay()
