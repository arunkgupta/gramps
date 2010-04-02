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
Source object for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from types import InstanceType

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib.primaryobj import PrimaryObject
from gen.lib.mediabase import MediaBase
from gen.lib.notebase import NoteBase
from gen.lib.reporef import RepoRef
from gen.lib.markertype import MarkerType

#-------------------------------------------------------------------------
#
# Source class
#
#-------------------------------------------------------------------------
class Source(MediaBase, NoteBase, PrimaryObject):
    """A record of a source of information."""
    
    def __init__(self):
        """Create a new Source instance."""
        PrimaryObject.__init__(self)
        MediaBase.__init__(self)
        NoteBase.__init__(self)
        self.marker = MarkerType()
        self.title = ""
        self.author = ""
        self.pubinfo = ""
        self.datamap = {}
        self.abbrev = ""
        self.reporef_list = []
        
    def serialize(self):
        """
        Convert the object to a serialized tuple of data.
        """
        return (self.handle, self.gramps_id, unicode(self.title),
                unicode(self.author), unicode(self.pubinfo),
                NoteBase.serialize(self),
                MediaBase.serialize(self), unicode(self.abbrev),
                self.change, self.datamap,
                [rr.serialize() for rr in self.reporef_list],
                self.marker.serialize(), self.private)

    def unserialize(self, data):
        """
        Convert the data held in a tuple created by the serialize method
        back into the data in an Event structure.
        """
        (self.handle, self.gramps_id, self.title, self.author,
         self.pubinfo, note_list, media_list,
         self.abbrev, self.change, self.datamap, reporef_list,
         marker, self.private) = data

        self.marker = InstanceType(MarkerType)
        self.marker.unserialize(marker)
        NoteBase.unserialize(self, note_list)
        MediaBase.unserialize(self, media_list)
        self.reporef_list = [InstanceType(RepoRef).unserialize(rr) 
                             for rr in reporef_list]
        
    def _has_handle_reference(self, classname, handle):
        """
        Return True if the object has reference to a given handle of given 
        primary object type.
        
        @param classname: The name of the primary object class.
        @type classname: str
        @param handle: The handle to be checked.
        @type handle: str
        @return: Returns whether the object has reference to this handle of 
                this object type.
        @rtype: bool
        """
        if classname == 'Repository':
            return handle in [ref.ref for ref in self.reporef_list]
        return False

    def _remove_handle_references(self, classname, handle_list):
        """
        Remove all references in this object to object handles in the list.

        @param classname: The name of the primary object class.
        @type classname: str
        @param handle_list: The list of handles to be removed.
        @type handle_list: str
        """
        if classname == 'Repository':
            new_list = [ ref for ref in self.reporef_list \
                         if ref.ref not in handle_list ]
            self.reporef_list = new_list

    def _replace_handle_reference(self, classname, old_handle, new_handle):
        """
        Replace all references to old handle with those to the new handle.

        @param classname: The name of the primary object class.
        @type classname: str
        @param old_handle: The handle to be replaced.
        @type old_handle: str
        @param new_handle: The handle to replace the old one with.
        @type new_handle: str
        """
        if classname == 'Repository':
            handle_list = [ref.ref for ref in self.reporef_list]
            while old_handle in handle_list:
                ix = handle_list.index(old_handle)
                self.reporef_list[ix].ref = new_handle
                handle_list[ix] = ''

    def get_text_data_list(self):
        """
        Return the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.title, self.author, self.pubinfo, self.abbrev,
                self.gramps_id] + self.datamap.keys() + self.datamap.values()
    
    def get_text_data_child_list(self):
        """
        Return the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        return self.media_list + self.reporef_list

    def get_sourcref_child_list(self):
        """
        Return the list of child secondary objects that may refer sources.

        @return: Returns the list of child secondary child objects that may 
                refer sources.
        @rtype: list
        """
        return self.media_list

    def get_note_child_list(self):
        """
        Return the list of child secondary objects that may refer notes.

        @return: Returns the list of child secondary child objects that may 
                refer notes.
        @rtype: list
        """
        return self.media_list + self.reporef_list

    def get_handle_referents(self):
        """
        Return the list of child objects which may, directly or through
        their children, reference primary objects.
        
        @return: Returns the list of objects refereincing primary objects.
        @rtype: list
        """
        return self.media_list + self.reporef_list

    def get_referenced_handles(self):
        """
        Return the list of (classname, handle) tuples for all directly
        referenced primary objects.
        
        @return: List of (classname, handle) tuples for referenced objects.
        @rtype: list
        """
        return self.get_referenced_note_handles()

    def has_source_reference(self, src_handle) :
        """
        Return True if any of the child objects has reference to this source 
        handle.

        @param src_handle: The source handle to be checked.
        @type src_handle: str
        @return: Returns whether any of it's child objects has reference to 
                this source handle.
        @rtype: bool
        """
        for item in self.get_sourcref_child_list():
            if item.has_source_reference(src_handle):
                return True

        return False

    def remove_source_references(self, src_handle_list):
        """
        Remove references to all source handles in the list in all child 
        objects.

        @param src_handle_list: The list of source handles to be removed.
        @type src_handle_list: list
        """
        for item in self.get_sourcref_child_list():
            item.remove_source_references(src_handle_list)

    def replace_source_references(self, old_handle, new_handle):
        """
        Replace references to source handles in the list in this object and 
        all child objects.

        @param old_handle: The source handle to be replaced.
        @type old_handle: str
        @param new_handle: The source handle to replace the old one with.
        @type new_handle: str
        """
        for item in self.get_sourcref_child_list():
            item.replace_source_references(old_handle, new_handle)

    def get_data_map(self):
        """Return the data map of attributes for the source."""
        return self.datamap

    def set_data_map(self, datamap):
        """Set the data map of attributes for the source."""
        self.datamap = datamap

    def set_data_item(self, key, value):
        """Set the particular data item in the attribute data map."""
        self.datamap[key] = value

    def set_title(self, title):
        """
        Set the descriptive title of the Source object.

        @param title: descriptive title to assign to the Source
        @type title: str
        """
        self.title = title

    def get_title(self):
        """
        Return the descriptive title of the Place object.

        @returns: Returns the descriptive title of the Place
        @rtype: str
        """
        return self.title

    def set_author(self, author):
        """Set the author of the Source."""
        self.author = author

    def get_author(self):
        """Return the author of the Source."""
        return self.author

    def set_publication_info(self, text):
        """Set the publication information of the Source."""
        self.pubinfo = text

    def get_publication_info(self):
        """Return the publication information of the Source."""
        return self.pubinfo

    def set_abbreviation(self, abbrev):
        """Set the title abbreviation of the Source."""
        self.abbrev = abbrev

    def get_abbreviation(self):
        """Return the title abbreviation of the Source."""
        return self.abbrev

    def add_repo_reference(self, repo_ref):
        """
        Add a L{RepoRef} instance to the Source's reporef list.

        @param repo_ref: L{RepoRef} instance to be added to the object's 
                reporef list.
        @type repo_ref: L{RepoRef}
        """
        self.reporef_list.append(repo_ref)

    def get_reporef_list(self):
        """
        Return the list of L{RepoRef} instances associated with the Source.

        @Return: list of L{RepoRef} instances associated with the Source
        @rtype: list
        """
        return self.reporef_list

    def set_reporef_list(self, reporef_list):
        """
        Set the list of L{RepoRef} instances associated with the Source.
        It replaces the previous list.

        @param reporef_list: list of L{RepoRef} instances to be assigned to 
                the Source.
        @type reporef_list: list
        """
        self.reporef_list = reporef_list

    def has_repo_reference(self, repo_handle):
        """
        Return True if the Source has reference to this Repository handle.

        @param repo_handle: The Repository handle to be checked.
        @type repo_handle: str
        @return: Returns whether the Source has reference to this Repository 
                handle.
        @rtype: bool
        """
        return repo_handle in [repo_ref.ref for repo_ref in self.reporef_list]

    def remove_repo_references(self, repo_handle_list):
        """
        Remove references to all Repository handles in the list.

        @param repo_handle_list: The list of Repository handles to be removed.
        @type repo_handle_list: list
        """
        new_reporef_list = [ repo_ref for repo_ref in self.reporef_list \
                                    if repo_ref.ref not in repo_handle_list ]
        self.reporef_list = new_reporef_list

    def replace_repo_references(self, old_handle, new_handle):
        """
        Replace all references to old Repository handle with the new handle.

        @param old_handle: The Repository handle to be replaced.
        @type old_handle: str
        @param new_handle: The Repository handle to replace the old one with.
        @type new_handle: str
        """
        refs_list = [ repo_ref.ref for repo_ref in self.reporef_list ]
        n_replace = refs_list.count(old_handle)
        for ix_replace in xrange(n_replace):
            ix = refs_list.index(old_handle)
            self.reporef_list[ix].ref = new_handle
            refs_list.pop(ix)

