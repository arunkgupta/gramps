#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2010       Doug Blank <doug.blank@gmail.com>
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

# $Id $

"""
Proxy class for the GRAMPS databases. Returns objects which are
referenced by a person, or through a chain of references starting with
a person.
"""

#-------------------------------------------------------------------------
#
# GRAMPS libraries
#
#-------------------------------------------------------------------------
from proxybase import ProxyDbBase

class ReferencedBySelectionProxyDb(ProxyDbBase):
    """
    A proxy to a Gramps database. This proxy will act like a Gramps
    database, but returning all objects which are referenced by a
    selection, or by an object that is referenced by an object which
    is eventually referenced by one of the selected objects.
    """

    def __init__(self, dbase, all_people=False):
        """
        Create a new ReferencedByPeopleProxyDb instance.  

        all_people - if True, get all people, and the items they link
        to;  if False, get all people that are connected to something,
        and all of items they link to.
        """
        ProxyDbBase.__init__(self, dbase)
        self.reset_references()
        # If restricted_to["Person"] is a set, restrict process to
        # them, and do not process others outside of them
        self.restricted_to = {"Person": None}
        # Build lists of referenced objects
        # iter through whatever object(s) you want to start
        # the trace.
        if all_people:
            # Do not add references to those note already included
            self.restricted_to["Person"] = [x for x in 
                                            self.db.iter_person_handles()]
            # Spread activation to all other items:
            for handle in self.restricted_to["Person"]:
                self.process_object("Person", handle)
        else:
            # get rid of orphaned people:
            # first, get all of the links from people:
            for person in self.db.iter_people():
                self.process_person(person, reference=False)
            # save those people:
            self.restricted_to["Person"] = self.referenced["Person"]
            # reset, and just follow those people
            self.reset_references()
            for handle in self.restricted_to["Person"]:
                self.process_object("Person", handle)

    def reset_references(self):
        self.referenced = {
            "Person": set(),
            "Family": set(),
            "Event": set(),
            "Place": set(),
            "Source": set(),
            "Repository": set(),
            "MediaObject": set(),
            "Note": set(),
            "Tag": set(),
            }

    def process_object(self, class_name, handle):
        if class_name == "Person":
            obj = self.db.get_person_from_handle(handle)
            if obj:
                self.process_person(obj)
        elif class_name == "Family":
            obj = self.db.get_family_from_handle(handle)
            if obj:
                self.process_family(obj)
        elif class_name == "Event":
            obj = self.db.get_event_from_handle(handle)
            if obj:
                self.process_event(obj)
        elif class_name == "Place":
            obj = self.db.get_place_from_handle(handle)
            if obj:
                self.process_place(obj)
        elif class_name == "Source":
            obj = self.db.get_source_from_handle(handle)
            if obj:
                self.process_source(obj)
        elif class_name == "Repository":
            obj = self.db.get_repository_from_handle(handle)
            if obj:
                self.process_repository(obj)
        elif class_name == "MediaObject":
            obj = self.db.get_object_from_handle(handle)
            if obj:
                self.process_media(obj)
        elif class_name == "Note":
            obj = self.db.get_note_from_handle(handle)
            if obj:
                self.process_note(obj)
        else:
            raise AttributeError("unknown class: '%s'" % class_name)

    def process_person(self, person, reference=True):
        """
        Follow the person object and find all of the primary objects
        that it references.
        """
        # A non-person:
        if person is None:
            return
        # A person we have seen before:
        if person.handle in self.referenced["Person"]:
            return
        # A person that we should not add:
        if (self.restricted_to["Person"] and 
            person.handle not in self.restricted_to["Person"]):
            return
        if reference:
            # forward reference:
            self.referenced["Person"].add(person.handle)
        # include backward references to this object:
        for (class_name, handle) in self.db.find_backlink_handles(
            person.handle, ["Person", "Family"]):
            self.process_object(class_name, handle)
                
        name = person.get_primary_name()
        if name:
            self.process_name(name)

        for handle in person.get_family_handle_list():
            family = self.db.get_family_from_handle(handle)
            if family:
                self.process_family(family)

        for handle in person.get_parent_family_handle_list():
            family = self.db.get_family_from_handle(handle)
            if family:
                self.process_family(family)

        for name in person.get_alternate_names():
            if name:
                self.process_name(name)

        for event_ref in person.get_event_ref_list():
            if event_ref:
                event = self.db.get_event_from_handle(event_ref.ref)
                if event:
                    self.process_event_ref(event_ref)

        self.process_addresses(person)
        self.process_attributes(person)
        self.process_source_ref_list(person)
        self.process_urls(person)
        self.process_media_ref_list(person)
        self.process_lds_ords(person)
        self.process_notes(person)
        self.process_associations(person)
        self.process_tags(person)

    def process_family(self, family):
        """
        Follow the family object and find all of the primary objects
        that it references.
        """
        if family is None or family.handle in self.referenced["Family"]:
            return
        self.referenced["Family"].add(family.handle)

        self.process_object("Person", family.mother_handle)
        self.process_object("Person", family.father_handle)
        for child_ref in family.get_child_ref_list():
            if not child_ref:
                continue
            self.process_object("Person", child_ref.ref)
            self.process_notes(child_ref)
            self.process_source_ref_list(child_ref)

        for event_ref in family.get_event_ref_list():
            if event_ref:
                event = self.db.get_event_from_handle(event_ref.ref)
                if event:
                    self.process_event_ref(event_ref)

        self.process_source_ref_list(family)
        self.process_notes(family)
        self.process_media_ref_list(family)
        self.process_attributes(family)
        self.process_lds_ords(family)

    def process_event(self, event):
        """
        Follow the event object and find all of the primary objects
        that it references.
        """
        if event is None or event.handle in self.referenced["Event"]:
            return
        self.referenced["Event"].add(event.handle)
        self.process_source_ref_list(event)
        self.process_notes(event)
        self.process_media_ref_list(event)
        self.process_attributes(event)

        place_handle = event.get_place_handle()
        place = self.db.get_place_from_handle(place_handle)
        if place:
            self.process_place(place)
    
    def process_place(self, place):
        """
        Follow the place object and find all of the primary objects
        that it references.
        """
        if place is None or place.handle in self.referenced["Place"]:
            return
        self.referenced["Place"].add(place.handle)
        self.process_source_ref_list(place)
        self.process_notes(place)
        self.process_media_ref_list(place)
        self.process_urls(place)

    def process_source(self, source):
        """
        Follow the source object and find all of the primary objects
        that it references.
        """
        if source is None or source.handle in self.referenced["Source"]:
            return
        self.referenced["Source"].add(source.handle)
        for repo_ref in source.get_reporef_list():
            if repo_ref:
                self.process_notes(repo_ref)
                handle = repo_ref.get_reference_handle()                
                repo = self.db.get_repository_from_handle(handle)
                if repo:
                    self.process_repository(repo)
        self.process_media_ref_list(source)
        self.process_notes(source)

    def process_repository(self, repository):
        """
        Follow the repository object and find all of the primary objects
        that it references.
        """
        if repository is None or repository.handle in self.referenced["Repository"]:
            return
        self.referenced["Repository"].add(repository.handle)
        self.process_notes(repository)
        self.process_addresses(repository)
        self.process_urls(repository)

    def process_media(self, media):
        """
        Follow the media object and find all of the primary objects
        that it references.
        """
        if media is None or media.handle in self.referenced["MediaObject"]:
            return
        self.referenced["MediaObject"].add(media.handle)
        self.process_source_ref_list(media)
        self.process_attributes(media)
        self.process_notes(media)

    def process_notes(self, original_obj):
        """
        Follow the note object and find all of the primary objects
        that it references.
        """
        for note_handle in original_obj.get_note_list():
            if note_handle and note_handle not in self.referenced["Note"]:
                note = self.db.get_note_from_handle(note_handle)
                if note:
                    self.referenced["Note"].add(note_handle)
                    for tag in note.text.get_tags():
                        if tag.name == 'Link':
                            if tag.value.startswith("gramps://"):
                                obj_class, prop, value = tag.value[9:].split("/")
                                if prop == "handle":
                                    self.process_object(obj_class, value)

    # --------------------------------------------

    def process_tags(self, original_obj):
        """
        Record the tags referenced by the primary object.
        """
        for tag_handle in original_obj.get_tag_list():
            self.referenced["Tag"].add(tag_handle)

    # --------------------------------------------

    def process_name(self, name):
        """ Find all of the primary objects referred to """
        self.process_source_ref_list(name)
        self.process_notes(name)
    
    def process_addresses(self, original_obj):
        """ Find all of the primary objects referred to """
        for address in original_obj.get_address_list():
            if address:
                self.process_address(address)

    def process_address(self, address):
        """ Find all of the primary objects referred to """
        self.process_source_ref_list(address)
        self.process_notes(address)

    def process_attributes(self, original_obj):
        """ Find all of the primary objects referred to """
        for attribute in original_obj.get_attribute_list():
            if attribute:
                self.process_notes(attribute)
                self.process_source_ref_list(attribute)

    def process_source_ref_list(self, original_obj):
        """ Find all of the primary objects referred to """
        for ref in original_obj.get_source_references():
            if ref:
                handle = ref.get_reference_handle()
                source = self.db.get_source_from_handle(handle)
                if source:
                    self.process_source_ref(ref)

    def process_source_ref(self, srcref):
        """ Find all of the primary objects referred to """
        source = self.db.get_source_from_handle(srcref.ref)
        if source:
            self.process_source(source)
        self.process_notes(srcref)

    def process_urls(self, original_obj):
        """ Find all of the primary objects referred to """
        pass

    def process_media_ref_list(self, original_obj):
        """ Find all of the primary objects referred to """
        for media_ref in original_obj.get_media_list():
            if media_ref:
                self.process_notes(media_ref)
                self.process_attributes(media_ref)
                self.process_source_ref_list(media_ref)
                handle = media_ref.get_reference_handle()
                media_object = self.db.get_object_from_handle(handle)
                if media_object:
                    self.process_media(media_object)

    def process_lds_ords(self, original_obj):
        """ Find all of the primary objects referred to """
        for lds_ord in original_obj.get_lds_ord_list():
            if lds_ord:
                self.process_lds_ord(lds_ord)

    def process_lds_ord(self, lds_ord):
        """ Find all of the primary objects referred to """
        fam_handle = lds_ord.get_family_handle()
        fam = self.db.get_family_from_handle(fam_handle)
        if fam:
            self.process_family(fam)

        place_handle = lds_ord.get_place_handle()
        place = self.db.get_place_from_handle(place_handle)
        if place:
            self.process_place(place)

        self.process_source_ref_list(lds_ord)
        self.process_notes(lds_ord)

    def process_associations(self, original_obj):
        """ Find all of the primary objects referred to """
        for person_ref in original_obj.get_person_ref_list():
            if person_ref:
                self.process_source_ref_list(person_ref)
                self.process_notes(person_ref)
                person = self.db.get_person_from_handle(person_ref.ref)
                if person:
                    self.process_person(person)

    def process_event_ref(self, event_ref):
        """ Find all of the primary objects referred to """
        self.process_notes(event_ref)
        self.process_attributes(event_ref)
        event = self.db.get_event_from_handle(event_ref.ref)
        if event:
            self.process_event(event)

    # ---------------------------------------------------

    def include_person(self, handle):
        """
        Filter for person
        """
        return handle in self.referenced["Person"]
        
    def include_place(self, handle):
        """
        Filter for places
        """
        return handle in self.referenced["Place"]
        
    def include_family(self, handle):
        """
        Filter for families
        """
        return handle in self.referenced["Family"]
        
    def include_media_object(self, handle):
        """
        Filter for media objects
        """
        return handle in self.referenced["MediaObject"]
        
    def include_event(self, handle):
        """
        Filter for events
        """
        return handle in self.referenced["Event"]

    def include_source(self, handle):
        """
        Filter for sources
        """
        return handle in self.referenced["Source"]
    
    def include_repository(self, handle):
        """
        Filter for repositories
        """
        return handle in self.referenced["Repository"]
        
    def include_note(self, handle):
        """
        Filter for notes
        """
        return handle in self.referenced["Note"]
    
    def include_tag(self, handle):
        """
        Filter for tags
        """
        return handle in self.referenced["Tag"]
    
    def find_backlink_handles(self, handle, include_classes=None):
        """
        Return appropriate backlink handles for this proxy.
        """
        for (objclass, handle) in self.db.find_backlink_handles(handle, 
                                                        include_classes):
            if handle in self.referenced[objclass]:
                yield (objclass, handle)
