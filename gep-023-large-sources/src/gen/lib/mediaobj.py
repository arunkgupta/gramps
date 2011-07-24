#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2010       Michiel D. Nauta
# Copyright (C) 2010       Nick Hall
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
Media object for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
import os
import logging
LOG = logging.getLogger(".citation")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib.primaryobj import PrimaryObject
from gen.lib.srcbase import SourceBase
from gen.lib.citationbase import CitationBase
from gen.lib.notebase import NoteBase
from gen.lib.datebase import DateBase
from gen.lib.attrbase import AttributeBase
from gen.lib.tagbase import TagBase

#-------------------------------------------------------------------------
#
# MediaObject class
#
#-------------------------------------------------------------------------
class MediaObject(SourceBase, CitationBase, NoteBase, DateBase, AttributeBase,
                  TagBase, PrimaryObject):
    """
    Container for information about an image file, including location,
    description and privacy.
    """
    
    def __init__(self, source=None):
        """
        Initialize a MediaObject. 
        
        If source is not None, then object is initialized from values of the 
        source object.

        :param source: Object used to initialize the new object
        :type source: MediaObject
        """
        PrimaryObject.__init__(self, source)
        SourceBase.__init__(self, source)
        NoteBase.__init__(self, source)
        DateBase.__init__(self, source)
        AttributeBase.__init__(self, source)
        TagBase.__init__(self)
        CitationBase.__init__(self)

        if source:
            self.path = source.path
            self.mime = source.mime
            self.desc = source.desc
            self.thumb = source.thumb
        else:
            self.path = ""
            self.mime = ""
            self.desc = ""
            self.thumb = None

    def serialize(self, no_text_date = False):
        """
        Convert the data held in the event to a Python tuple that
        represents all the data elements. 
        
        This method is used to convert the object into a form that can easily 
        be saved to a database.

        These elements may be primitive Python types (string, integers),
        complex Python types (lists or tuples, or Python objects. If the
        target database cannot handle complex types (such as objects or
        lists), the database is responsible for converting the data into
        a form that it can use.

        :returns: Returns a python tuple containing the data that should
            be considered persistent.
        :rtype: tuple
        """
        return (self.handle, self.gramps_id, self.path, self.mime, self.desc,
                AttributeBase.serialize(self),
                SourceBase.serialize(self),
                NoteBase.serialize(self),
                self.change,
                DateBase.serialize(self, no_text_date),
                TagBase.serialize(self),
                CitationBase.serialize(self),
                self.private)

    def unserialize(self, data):
        """
        Convert the data held in a tuple created by the serialize method
        back into the data in an Event structure.

        :param data: tuple containing the persistent data associated the object
        :type data: tuple
        """
        (self.handle, self.gramps_id, self.path, self.mime, self.desc,
         attribute_list, source_list, note_list, self.change,
         date, tag_list,
         citation_list,
         self.private) = data

        AttributeBase.unserialize(self, attribute_list)
        SourceBase.unserialize(self, source_list)
        NoteBase.unserialize(self, note_list)
        DateBase.unserialize(self, date)
        TagBase.unserialize(self, tag_list)
        CitationBase.unserialize(self, citation_list)

    def get_text_data_list(self):
        """
        Return the list of all textual attributes of the object.

        :returns: Returns the list of all textual attributes of the object.
        :rtype: list
        """
        return [self.path, self.mime, self.desc, self.gramps_id]

    def get_text_data_child_list(self):
        """
        Return the list of child objects that may carry textual data.

        :returns: Returns the list of child objects that may carry textual data.
        :rtype: list
        """
        return self.attribute_list + self.source_list

    def get_sourcref_child_list(self):
        """
        Return the list of child secondary objects that may refer sources.

        :returns: Returns the list of child secondary child objects that may 
                refer sources.
        :rtype: list
        """
        return self.attribute_list

    def get_citation_child_list(self):
        """
        Return the list of child secondary objects that may refer sources.

        :returns: Returns the list of child secondary child objects that may 
                refer sources.
        :rtype: list
        """
        # N.B. the citation_list of the media object is not a child object
        # it is a direct reference from Media to a citation.
        return []

    def get_note_child_list(self):
        """
        Return the list of child secondary objects that may refer notes.

        :returns: Returns the list of child secondary child objects that may 
                refer notes.
        :rtype: list
        """
        return self.attribute_list + self.source_list + self.citation_list

    def get_referenced_handles(self):
        """
        Return the list of (classname, handle) tuples for all directly
        referenced primary objects.
        
        :returns: List of (classname, handle) tuples for referenced objects.
        :rtype: list
        """
        LOG.debug ("Media: %s get_referenced_handles: %s" % 
                   (self.desc,
                   self.get_referenced_note_handles() + 
                   self.get_referenced_tag_handles() +
                   self.get_referenced_citation_handles()))
        return self.get_referenced_note_handles() + \
               self.get_referenced_tag_handles()  + \
               self.get_referenced_citation_handles()

    def get_handle_referents(self):
        """
        Return the list of child objects which may, directly or through
        their children, reference primary objects.
        
        :returns: Returns the list of objects referencing primary objects.
        :rtype: list
        """
        LOG.debug ("Media: %s get_handle_referents: %s" %
                   (self.desc,
                   self.attribute_list + self.source_list))
# FIXME: This is wrong, because it returns the handle, when it should return the
# citation object. This is probably because the citation unpack has not been done.
        return self.attribute_list + self.source_list

    def merge(self, acquisition):
        """
        Merge the content of acquisition into this media object.

        Lost: handle, id, file, date of acquisition.

        :param acquisition: The media object to merge with the present object.
        :rtype acquisition: MediaObject
        """
        self._merge_privacy(acquisition)
        self._merge_attribute_list(acquisition)
        self._merge_note_list(acquisition)
        self._merge_source_reference_list(acquisition)
        self._merge_tag_list(acquisition)
        self.merge_citation_list(acquisition)

    def set_mime_type(self, mime_type):
        """
        Set the MIME type associated with the MediaObject.

        :param mime_type: MIME type to be assigned to the object
        :type mime_type: str
        """
        self.mime = mime_type

    def get_mime_type(self):
        """
        Return the MIME type associated with the MediaObject.

        :returns: Returns the associated MIME type
        :rtype: str
        """
        return self.mime
    
    def set_path(self, path):
        """Set the file path to the passed path."""
        self.path = os.path.normpath(path)

    def get_path(self):
        """Return the file path."""
        return self.path

    def set_description(self, text):
        """Set the description of the image."""
        self.desc = text

    def get_description(self):
        """Return the description of the image."""
        return self.desc