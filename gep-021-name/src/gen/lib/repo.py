#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2010       Michiel D. Nauta
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
Repository object for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib.primaryobj import PrimaryObject
from gen.lib.notebase import NoteBase
from gen.lib.addressbase import AddressBase
from gen.lib.urlbase import UrlBase
from gen.lib.repotype import RepositoryType
from gen.lib.markertype import MarkerType

#-------------------------------------------------------------------------
#
# Repository class
#
#-------------------------------------------------------------------------
class Repository(NoteBase, AddressBase, UrlBase, PrimaryObject):
    """A location where collections of Sources are found."""
    
    def __init__(self):
        """
        Create a new Repository instance.
        """
        PrimaryObject.__init__(self)
        NoteBase.__init__(self)
        AddressBase.__init__(self)
        UrlBase.__init__(self)
        self.type = RepositoryType()
        self.name = ""

    def serialize(self):
        """
        Convert the object to a serialized tuple of data.
        """
        return (self.handle, self.gramps_id, self.type.serialize(),
                unicode(self.name),
                NoteBase.serialize(self),
                AddressBase.serialize(self),
                UrlBase.serialize(self),
                self.change, self.marker.serialize(), self.private)

    def unserialize(self, data):
        """
        Convert the data held in a tuple created by the serialize method
        back into the data in a Repository structure.
        """
        (self.handle, self.gramps_id, the_type, self.name, note_list,
         address_list, urls, self.change, marker, self.private) = data

        self.marker = MarkerType()
        self.marker.unserialize(marker)
        self.type = RepositoryType()
        self.type.unserialize(the_type)
        NoteBase.unserialize(self, note_list)
        AddressBase.unserialize(self, address_list)
        UrlBase.unserialize(self, urls)
        
    def get_text_data_list(self):
        """
        Return the list of all textual attributes of the object.

        :returns: Returns the list of all textual attributes of the object.
        :rtype: list
        """
        return [self.name, str(self.type)]

    def get_text_data_child_list(self):
        """
        Return the list of child objects that may carry textual data.

        :returns: Returns the list of child objects that may carry textual data.
        :rtype: list
        """
        return self.address_list + self.urls

    def get_sourcref_child_list(self):
        """
        Return the list of child secondary objects that may refer sources.

        :returns: Returns the list of child secondary child objects that may 
                refer sources.
        :rtype: list
        """
        return self.address_list

    def get_note_child_list(self):
        """
        Return the list of child secondary objects that may refer notes.

        :returns: Returns the list of child secondary child objects that may 
                refer notes.
        :rtype: list
        """
        return self.address_list

    def get_handle_referents(self):
        """
        Return the list of child objects which may, directly or through
        their children, reference primary objects.
        
        :returns: Returns the list of objects referencing primary objects.
        :rtype: list
        """
        return self.address_list

    def get_referenced_handles(self):
        """
        Return the list of (classname, handle) tuples for all directly
        referenced primary objects.
        
        :returns: List of (classname, handle) tuples for referenced objects.
        :rtype: list
        """
        return self.get_referenced_note_handles()

    def has_source_reference(self, src_handle) :
        """
        Return True if any of the child objects has reference to this source 
        handle.

        :param src_handle: The source handle to be checked.
        :type src_handle: str
        :returns: Returns whether any of it's child objects has reference to 
                this source handle.
        :rtype: bool
        """
        for item in self.get_sourcref_child_list():
            if item.has_source_reference(src_handle):
                return True

        return False

    def remove_source_references(self, src_handle_list):
        """
        Remove references to all source handles in the list in all child 
        objects.

        :param src_handle_list: The list of source handles to be removed.
        :type src_handle_list: list
        """
        for item in self.get_sourcref_child_list():
            item.remove_source_references(src_handle_list)

    def replace_source_references(self, old_handle, new_handle):
        """
        Replace references to source handles in the list in this object and 
        all child objects and merge equivalent entries.

        :param old_handle: The source handle to be replaced.
        :type old_handle: str
        :param new_handle: The source handle to replace the old one with.
        :type new_handle: str
        """
        for item in self.get_sourcref_child_list():
            item.replace_source_references(old_handle, new_handle)

    def merge(self, acquisition):
        """
        Merge the content of acquisition into this repository.

        :param acquisition: The repository to merge with the present repository.
        :rtype acquisition: Repository
        """
        self._merge_privacy(acquisition)
        self._merge_address_list(acquisition)
        self._merge_url_list(acquisition)
        self._merge_note_list(acquisition)

    def set_type(self, the_type):
        """
        :param the_type: descriptive type of the Repository
        :type the_type: str
        """
        self.type.set(the_type)

    def get_type(self):
        """
        :returns: the descriptive type of the Repository
        :rtype: str
        """
        return self.type

    def set_name(self, name):
        """
        :param name: descriptive name of the Repository
        :type name: str
        """
        self.name = name

    def get_name(self):
        """
        :returns: the descriptive name of the Repository
        :rtype: str
        """
        return self.name