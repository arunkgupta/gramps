#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2006  Donald N. Allingham
# Copyright (C) 2010  Michiel D. Nauta
# Copyright (C) 2011  Tim G L Lyons
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
SourceBase class for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib.srcref import SourceRef
from gen.lib.const import IDENTICAL, EQUAL, DIFFERENT

#-------------------------------------------------------------------------
#
# SourceBase classes
#
#-------------------------------------------------------------------------
class SourceBase(object):
    """
    Base class for storing source references.
    """
# FIXME: SourceBase is no longer used so this module needs to be removed    
    def __init__(self, source=None):
        """
        Create a new SourceBase, copying from source if not None.
        
        :param source: Object used to initialize the new object
        :type source: SourceBase
        """

        self.source_list = map(SourceRef, source.source_list) if source else []

    def serialize(self):
        """
        Convert the object to a serialized tuple of data.
        """
        return [sref.serialize() for sref in self.source_list]

    def unserialize(self, data):
        """
        Convert a serialized tuple of data to an object.
        """
        self.source_list = [SourceRef().unserialize(item) for item in data]

    def add_source_reference(self, src_ref) :
        """
        Add a source reference to this object.

        :param src_ref: The source reference to be added to the
            SourceNote's list of source references.
        :type src_ref: :class:`~gen.lib.srcref.SourceRef`
        """
        self.source_list.append(src_ref)

    def get_source_references(self) :
        """
        Return the list of source references associated with the object.

        :returns: Returns the list of :class:`~gen.lib.srcref.SourceRef` objects associated with
            the object.
        :rtype: list
        """
        return self.source_list

    def get_sourcref_child_list(self):
        """
        Return the list of child secondary objects that may refer sources.

        :returns: Returns the list of child secondary child objects that may 
                refer sources.
        :rtype: list
        """
        return []

    def has_source_reference(self, src_handle) :
        """
        Return True if the object or any of it's child objects has reference
        to this source handle.

        :param src_handle: The source handle to be checked.
        :type src_handle: str
        :returns: Returns whether the object or any of it's child objects has 
                reference to this source handle.
        :rtype: bool
        """
        for src_ref in self.source_list:
            # Using direct access here, not the getter method -- efficiency!
            if src_ref.ref == src_handle:
                return True

        for item in self.get_sourcref_child_list():
            if item.has_source_reference(src_handle):
                return True

        return False

    def remove_source_references(self, src_handle_list):
        """
        Remove references to all source handles in the list in this object 
        and all child objects.

        :param src_handle_list: The list of source handles to be removed.
        :type src_handle_list: list
        """
        new_source_list = [src_ref for src_ref in self.source_list
                                if src_ref.ref not in src_handle_list]
        self.source_list = new_source_list

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
        refs_list = [ src_ref.ref for src_ref in self.source_list ]
        new_ref = None
        if new_handle in refs_list:
            new_ref = self.source_list[refs_list.index(new_handle)]
        n_replace = refs_list.count(old_handle)
        for ix_replace in xrange(n_replace):
            idx = refs_list.index(old_handle)
            self.source_list[idx].ref = new_handle
            refs_list[idx] = new_handle
            if new_ref:
                src_ref = self.source_list[idx]
                equi = new_ref.is_equivalent(src_ref)
                if equi != DIFFERENT:
                    if equi == EQUAL:
                        new_ref.merge(src_ref)
                    self.source_list.pop(idx)
                    refs_list.pop(idx)

        for item in self.get_sourcref_child_list():
            item.replace_source_references(old_handle, new_handle)

    def set_source_reference_list(self, src_ref_list) :
        """
        Assign the passed list to the object's list of source references.

        :param src_ref_list: List of source references to ba associated
            with the object
        :type src_ref_list: list of :class:`~gen.lib.srcref.SourceRef` instances
        """
        self.source_list = src_ref_list

    def _merge_source_reference_list(self, acquisition):
        """
        Merge the list of source references from acquisition with our own.

        :param acquisition: the source references list of this object will be
            merged with the current source references list.
        :rtype acquisition: SourceRef
        """
        srcref_list = self.source_list[:]
        for addendum in acquisition.get_source_references():
            for srcref in srcref_list:
                equi = srcref.is_equivalent(addendum)
                if equi == IDENTICAL:
                    break
                elif equi == EQUAL:
                    srcref.merge(addendum)
                    break
            else:
                self.source_list.append(addendum)
