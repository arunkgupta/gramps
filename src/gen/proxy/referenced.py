#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2008       Gary Burton
# Copyright (C) 2011       Tim G L Lyons
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
Proxy class for the GRAMPS databases. Returns objects which are referenced
by at least one other object.
"""

#-------------------------------------------------------------------------
#
# GRAMPS libraries
#
#-------------------------------------------------------------------------
from proxybase import ProxyDbBase

class ReferencedProxyDb(ProxyDbBase):
    """
    A proxy to a Gramps database. This proxy will act like a Gramps database,
    but returning all objects which are referenced by at least one other object.
    """

    def __init__(self, dbase):
        """
        Create a new ReferencedProxyDb instance. 
        """
        ProxyDbBase.__init__(self, dbase)
        self.unreferenced_events = set()
        self.unreferenced_places = set()
        self.unreferenced_citations = set()
        self.unreferenced_sources = set()
        self.unreferenced_repositories = set()
        self.unreferenced_media_objects = set()
        self.unreferenced_notes = set()
        self.unreferenced_tags = set()

        # Build lists of unreferenced objects
        self.__find_unreferenced_objects()

    def include_place(self, handle):
        """
        Filter for places
        """
        return handle not in self.unreferenced_places
        
    def include_media_object(self, handle):
        """
        Filter for media objects
        """
        return handle not in self.unreferenced_media_objects
        
    def include_event(self, handle):
        """
        Filter for events
        """
        return handle not in self.unreferenced_events

    def include_citation(self, handle):
        """
        Filter for citations
        """
        return handle not in self.unreferenced_citations
    
    def include_source(self, handle):
        """
        Filter for sources
        """
        return handle not in self.unreferenced_sources
    
    def include_repository(self, handle):
        """
        Filter for repositories
        """
        return handle not in self.unreferenced_repositories
        
    def include_note(self, handle):
        """
        Filter for notes
        """
        return handle not in self.unreferenced_notes
    
    def include_tag(self, handle):
        """
        Filter for tags
        """
        return handle not in self.unreferenced_tags
    
    def find_backlink_handles(self, handle, include_classes=None):
        """
        Find all objects that hold a reference to the object handle.
        Returns an iterator over a list of (class_name, handle) tuples.

        @param handle: handle of the object to search for.
        @type handle: database handle
        @param include_classes: list of class names to include in the results.
                                Default: None means include all classes.
        @type include_classes: list of class names
        
        This default implementation does a sequential scan through all
        the primary object databases and is very slow. Backends can
        override this method to provide much faster implementations that
        make use of additional capabilities of the backend.

        Note that this is a generator function, it returns a iterator for
        use in loops. If you want a list of the results use:

        >    result_list = list(find_backlink_handles(handle))
        """

        perfam = {
                    "Person" : self.get_person_from_handle,
                    "Family" : self.get_family_from_handle,
                 }

        unref = {
                    "Event"         : self.unreferenced_events,
                    "Place"         : self.unreferenced_places,
                    "Citation"      : self.unreferenced_citations,
                    "Source"        : self.unreferenced_sources,
                    "Repository"    : self.unreferenced_repositories,
                    "MediaObject"   : self.unreferenced_media_objects,
                    "Note"          : self.unreferenced_notes,
                }
                
        handle_itr = self.db.find_backlink_handles(handle, include_classes)
        for (class_name, handle) in handle_itr:
            if (class_name in perfam                # Person or Family exist?
                    and perfam[class_name](handle)
                or class_name in unref               # not yet in unref?
                    and handle not in unref[class_name]):

                        yield (class_name, handle)
        return

    def __find_unreferenced_objects(self):
        """
        Builds lists of all objects that are not referenced by another object.
        These may be objects that are really unreferenced or because they
        are referenced by something or someone that has already been filtered
        by one of the other proxy decorators.
        By adding an object to a list, other referenced objects could
        effectively become unreferenced, so the action is performed in a loop
        until there are no more objects to unreference.
        """

        unrefs = (
                (self.unreferenced_events,      self.get_event_handles),
                (self.unreferenced_places,      self.get_place_handles),
                (self.unreferenced_citations,   self.get_citation_handles),
                (self.unreferenced_sources,     self.get_source_handles),
                (self.unreferenced_repositories,
                                                self.get_repository_handles),
                (self.unreferenced_media_objects,
                                                self.get_media_object_handles),
                (self.unreferenced_notes,       self.get_note_handles),
                (self.unreferenced_tags,        self.get_tag_handles),
                )

        last_count = 0
        while True:
            current_count = 0
            for (unref_list, handle_list) in unrefs:
                unref_list.update(
                    handle for handle in handle_list()
                        if not any(self.find_backlink_handles(handle)))
                current_count += len(unref_list)

            if current_count == last_count:
                break
            last_count = current_count
