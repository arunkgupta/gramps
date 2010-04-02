#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2005  Donald N. Allingham
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
Base class for the GRAMPS databases. All database interfaces should inherit
from this class.
"""

#-------------------------------------------------------------------------
#
# libraries
#
#-------------------------------------------------------------------------
import cPickle
import time
import random
import locale
import re
import sets
import sys
from gettext import gettext as _

log = sys.stderr.write

#-------------------------------------------------------------------------
#
# GRAMPS libraries
#
#-------------------------------------------------------------------------
from RelLib import *
import GrampsKeys
import GrampsDBCallback

#-------------------------------------------------------------------------
#
# constants
#
#-------------------------------------------------------------------------
_UNDO_SIZE = 1000

PERSON_KEY     = 0
FAMILY_KEY     = 1
SOURCE_KEY     = 2
EVENT_KEY      = 3
MEDIA_KEY      = 4
PLACE_KEY      = 5

class GrampsCursor:
    """
    Provides a basic iterator that allows the user to cycle through
    the elements in a particular map. A cursor should never be
    directly instantiated. Instead, in should be created by the
    database class.

    A cursor should only be used for a single pass through the
    database. If multiple passes are needed, multiple cursors
    should be used.
    """

    def first(self):
        """
        Returns the first (index, data) pair in the database. This
        should be called before the first call to next(). Note that
        the data return is in the format of the serialized format
        stored in the database, not in the more usable class object.
        The data should be converted to a class using the class's
        unserialize method.

        If no data is available, None is returned.
        """
        return None

    def next(self):
        """
        Returns the next (index, data) pair in the database. Like
        the first() method, the data return is in the format of the
        serialized format stored in the database, not in the more
        usable class object. The data should be converted to a class
        using the class's unserialize method.

        None is returned when no more data is available.
        """
        return None

    def close(self):
        """
        Closes the cursor. This should be called when the user is
        finished using the cursor, freeing up the cursor's resources.
        """
        pass

class GrampsDbBase(GrampsDBCallback.GrampsDBCallback):
    """
    GRAMPS database object. This object is a base class for all
    database interfaces.
    """

    __signals__ = {
        'person-add'     : (list,),
        'person-update'  : (list,),
        'person-delete'  : (list,),
        'person-rebuild' : None,
        'family-add'     : (list,),
        'family-update'  : (list,),
        'family-delete'  : (list,),
        'family-rebuild' : None,
        'source-add'     : (list,),
        'source-update'  : (list,),
        'source-delete'  : (list,),
        'source-rebuild' : None,
        'place-add'      : (list,),
        'place-update'   : (list,),
        'place-delete'   : (list,),
        'place-rebuild'  : None,
        'media-add'      : (list,),
        'media-update'   : (list,),
        'media-delete'   : (list,),
        'media-rebuild'  : None,
        }
    

    # If this is True logging will be turned on.
    try:
        __LOG_ALL = int(os.environ.get('GRAMPS_SIGNAL',"0")) == 1
    except:
        __LOG_ALL = False


    def __init__(self):
        """
        Creates a new GrampsDbBase instance. A new GrampDbBase class should
        never be directly created. Only classes derived from this class should
        be created.
        """

        GrampsDBCallback.GrampsDBCallback.__init__(self)
        
        self.readonly = False
        self.rand = random.Random(time.time())
        self.smap_index = 0
        self.emap_index = 0
        self.pmap_index = 0
        self.fmap_index = 0
        self.lmap_index = 0
        self.omap_index = 0

        self.family_event_names = sets.Set()
        self.individual_event_names = sets.Set()
        self.individual_attributes = sets.Set()
        self.family_attributes = sets.Set()

        self.set_person_id_prefix(GrampsKeys.get_person_id_prefix())
        self.set_object_id_prefix(GrampsKeys.get_object_id_prefix())
        self.set_family_id_prefix(GrampsKeys.get_family_id_prefix())
        self.set_source_id_prefix(GrampsKeys.get_source_id_prefix())
        self.set_place_id_prefix(GrampsKeys.get_place_id_prefix())
        self.set_event_id_prefix(GrampsKeys.get_event_id_prefix())

        self.open = 0
        self.genderStats = GenderStats()

        self.undodb    = None
        self.id_trans  = None
        self.fid_trans = None
        self.pid_trans = None
        self.sid_trans = None
        self.oid_trans = None
        self.env = None
        self.person_map = None
        self.family_map = None
        self.place_map  = None
        self.source_map = None
        self.media_map  = None
        self.event_map  = None
        self.metadata   = None
        self.name_group = None
        self.undo_callback = None
        self.redo_callback = None
        self.modified   = 0

        self.undoindex  = -1
        self.translist  = [None] * _UNDO_SIZE
        self.default = None
        self.owner = Researcher()
        self.bookmarks = []
        self.path = ""
        self.place2title = {}
        self.name_group = {}

    def rebuild_secondary(self,callback=None):
        pass

    def version_supported(self):
        """ Returns True when the file has a supported version"""
        return True

    def need_upgrade(self):
        return False

    def upgrade(self):
        pass

    def create_id(self):
        s = ""
        for val in [ int(time.time()*10000) & 0x7fffffff,
                     self.rand.randint(0,0x7fffffff),
                     self.rand.randint(0,0x7fffffff)]:
            while val != 0:
                rem = val % 36
                if rem <= 9:
                    s += chr(48+rem)
                else:
                    s += chr(rem+55)
                val = int(val/36)
        return s

    def get_person_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def get_family_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def get_place_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def get_source_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def get_media_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def get_event_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def load(self,name,callback,mode="w"):
        """
        Opens the specified database. The method needs to be overridden
        in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def close(self):
        """
        Closes the specified database. The method needs to be overridden
        in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"
        
    def abort_changes(self):
        pass
    
    def is_open(self):
        """
        Returns 1 if the database has been opened.
        """
        return self.person_map != None

    def request_rebuild(self):
        """
        Notifies clients that the data has change significantly, and that all
        internal data dependent on the database should be rebuilt.
        """
        self.emit('person-rebuild')
        self.emit('family-rebuild')
        self.emit('place-rebuild')
        self.emit('source-rebuild')
        self.emit('media-rebuild')
    
    def commit_person(self,person,transaction,change_time=None):
        """
        Commits the specified Person to the database, storing the changes
        as part of the transaction.
        """
        if self.readonly or not person or not person.get_handle():
            return
        if change_time:
            person.change = int(change_time)
        else:
            person.change = int(time.time())
        handle = str(person.get_handle())
        old_data = self.person_map.get(handle)
        if transaction != None:
            transaction.add(PERSON_KEY,handle,old_data)

        if old_data:
            old_person = Person(old_data)
            if (old_data[2] != person.gender or
                old_data[3].first_name != person.primary_name.first_name):
                self.genderStats.uncount_person(old_person)
                self.genderStats.count_person(person,self)
        else:
            self.genderStats.count_person(person,self)

        for attr in person.attribute_list:
            self.individual_attributes.add(attr.type)
            
        self.person_map[handle] = person.serialize()
        if old_data:
            self.emit('person-update',([handle],))
        else:
            self.emit('person-add',([handle],))
          
    def commit_media_object(self,obj,transaction,change_time=None):
        """
        Commits the specified MediaObject to the database, storing the changes
        as part of the transaction.
        """
        if self.readonly or not obj or not obj.get_handle():
            return 
        if change_time:
            obj.change = int(change_time)
        else:
            obj.change = int(time.time())
        handle = str(obj.get_handle())
        old_data = self.media_map.get(handle)
        if transaction != None:
            transaction.add(MEDIA_KEY,handle,old_data)
        self.media_map[handle] = obj.serialize()
        if old_data:
            self.emit('media-update',([handle],))
        else:
            self.emit('media-add',([handle],))
            
    def commit_source(self,source,transaction,change_time=None):
        """
        Commits the specified Source to the database, storing the changes
        as part of the transaction.
        """
        if self.readonly or not source or not source.get_handle():
            return 
        if change_time:
            source.change = int(change_time)
        else:
            source.change = int(time.time())
        handle = str(source.get_handle())
        old_data = self.source_map.get(handle)
        if transaction != None:
            transaction.add(SOURCE_KEY,handle,old_data)
        self.source_map[handle] =  source.serialize()
        if old_data:
            self.emit('source-update',([handle],))
        else:
            self.emit('source-add',([handle],))

    def commit_place(self,place,transaction,change_time=None):
        """
        Commits the specified Place to the database, storing the changes
        as part of the transaction.
        """
        if self.readonly or not place or not place.get_handle():
            return 
        if change_time:
            place.change = int(change_time)
        else:
            place.change = int(time.time())
        handle = str(place.get_handle())
        old_data = self.place_map.get(handle)
        if transaction != None:
            transaction.add(PLACE_KEY,handle,old_data)
        self.place_map[handle] = place.serialize()
        if old_data:
            self.emit('place-update',([handle],))
        else:
            self.emit('place-add',([handle],))
            
    def commit_personal_event(self,event,transaction,change_time=None):
        self.individual_event_names.add(event.name)
        self.commit_event(event,transaction,change_time)

    def commit_family_event(self,event,transaction,change_time=None):
        self.family_event_names.add(event.name)
        self.commit_event(event,transaction,change_time)

    def commit_event(self,event,transaction,change_time=None):
        """
        Commits the specified Event to the database, storing the changes
        as part of the transaction.
        """
        if self.readonly or not event or not event.get_handle():
            return 
        if change_time:
            event.change = int(change_time)
        else:
            event.change = int(time.time())
        handle = str(event.get_handle())
        old_data = self.event_map.get(handle)
        if transaction != None:
            transaction.add(EVENT_KEY,handle,old_data)
        self.event_map[handle] = event.serialize()

    def commit_family(self,family,transaction,change_time=None):
        """
        Commits the specified Family to the database, storing the changes
        as part of the transaction.
        """
        if self.readonly or not family or not family.handle:
            return
        if change_time:
            family.change = int(change_time)
        else:
            family.change = int(time.time())
        handle = str(family.get_handle())
        old_data = self.family_map.get(handle)
        if transaction != None:
            transaction.add(FAMILY_KEY,handle,old_data)
        self.family_map[handle] = family.serialize()

        for attr in family.attribute_list:
            self.family_attributes.add(attr.type)

        if old_data:
            self.emit('family-update',([handle],))
        else:
            self.emit('family-add',([handle],))

    def find_next_person_gramps_id(self):
        """
        Returns the next available GRAMPS' ID for a Person object based
        off the person ID prefix.
        """
        index = self.iprefix % self.pmap_index
        while self.id_trans.get(str(index)):
            self.pmap_index += 1
            index = self.iprefix % self.pmap_index
        self.pmap_index += 1
        return index

    def find_next_place_gramps_id(self):
        """
        Returns the next available GRAMPS' ID for a Place object based
        off the person ID prefix.
        """
        index = self.pprefix % self.lmap_index
        while self.pid_trans.get(str(index)):
            self.lmap_index += 1
            index = self.pprefix % self.lmap_index
        self.lmap_index += 1
        return index

    def find_next_event_gramps_id(self):
        """
        Returns the next available GRAMPS' ID for a Event object based
        off the person ID prefix.
        """
        index = self.eprefix % self.emap_index
        self.emap_index += 1
        return index

    def find_next_object_gramps_id(self):
        """
        Returns the next available GRAMPS' ID for a MediaObject object based
        off the person ID prefix.
        """
        index = self.oprefix % self.omap_index
        while self.oid_trans.get(str(index)):
            self.omap_index += 1
            index = self.oprefix % self.omap_index
        self.omap_index += 1
        return index

    def find_next_source_gramps_id(self):
        """
        Returns the next available GRAMPS' ID for a Source object based
        off the person ID prefix.
        """
        index = self.sprefix % self.smap_index
        while self.sid_trans.get(str(index)):
            self.smap_index += 1
            index = self.sprefix % self.smap_index
        self.smap_index += 1
        return index

    def find_next_family_gramps_id(self):
        """
        Returns the next available GRAMPS' ID for a Family object based
        off the person ID prefix.
        """
        index = self.fprefix % self.fmap_index
        while self.fid_trans.get(str(index)):
            self.fmap_index += 1
            index = self.fprefix % self.fmap_index
        self.fmap_index += 1
        return index

    def get_person_from_handle(self,val):
        """finds a Person in the database from the passed gramps' ID.
        If no such Person exists, None is returned."""

        data = self.person_map.get(str(val))
        if data:
            person = Person(data)
            return person
        return None

    def get_source_from_handle(self,val):
        """finds a Source in the database from the passed gramps' ID.
        If no such Source exists, None is returned."""

        data = self.source_map.get(str(val))
        if data:
            source = Source()
            source.unserialize(data)
            return source
        return None

    def get_object_from_handle(self,handle):
        """finds an Object in the database from the passed gramps' ID.
        If no such Object exists, None is returned."""
        data = self.media_map.get(str(handle))
        if data:
            mobject = MediaObject()
            mobject.unserialize(data)
            return mobject
        return None

    def get_place_from_handle(self,handle):
        """finds a Place in the database from the passed gramps' ID.
        If no such Place exists, None is returned."""
        data = self.place_map.get(str(handle))
        if data:
            place = Place()
            place.unserialize(data)
            return place
        return None

    def get_event_from_handle(self,handle):
        """finds a Event in the database from the passed gramps' ID.
        If no such Event exists, None is returned."""

        data = self.event_map.get(str(handle))
        if data:
            event = Event()
            event.unserialize(data)
            return event
        return None

    def get_family_from_handle(self,handle):
        """finds a Family in the database from the passed gramps' ID.
        If no such Family exists, None is returned."""

        data = self.family_map.get(str(handle))
        if data:
            family = Family()
            family.unserialize(data)
            return family
        return None

    def find_person_from_handle(self,val,transaction):
        """
        Finds a Person in the database from the passed GRAMPS ID.
        If no such Person exists, a new Person is added to the database.
        """
        person = Person()
        data = self.person_map.get(str(val))
        if data:
            person.unserialize(data)
        else:
            person.set_handle(val)
            if not self.readonly:
                if transaction != None:
                    transaction.add(PERSON_KEY, val, None)
                self.person_map[str(val)] = person.serialize()
                self.emit('person-add', ([str(val)],))
        return person

    def find_source_from_handle(self,val,transaction):
        """
        Finds a Source in the database from the passed GRAMPS ID.
        If no such Source exists, a new Source is added to the database.
        """
        source = Source()
        if self.source_map.get(str(val)):
            source.unserialize(self.source_map.get(str(val)))
        else:
            source.set_handle(val)
            self.add_source(source,transaction)
        return source

    def find_event_from_handle(self,val,transaction):
        """
        Finds a Event in the database from the passed GRAMPS ID.
        If no such Event exists, a new Event is added to the database.
        """
        event = Event()
        data = self.event_map.get(str(val))
        if data:
            event.unserialize(data)
        else:
            event.set_handle(val)
            self.add_event(event,transaction)
        return event

    def find_object_from_handle(self,handle,transaction):
        """
        Finds an MediaObject in the database from the passed GRAMPS ID.
        If no such MediaObject exists, a new Object is added to the database."""

        obj = MediaObject()
        if self.media_map.get(str(handle)):
            obj.unserialize(self.media_map.get(str(handle)))
        else:
            obj.set_handle(handle)
            self.add_object(obj,transaction)
        return obj

    def find_place_from_handle(self,handle,transaction):
        """
        Finds a Place in the database from the passed GRAMPS ID.
        If no such Place exists, a new Place is added to the database.
        """
        place = Place()
        if self.place_map.get(str(handle)):
            place.unserialize(self.place_map.get(str(handle)))
        else:
            place.set_handle(handle)
            self.add_place(place,transaction)
        return place

    def find_family_from_handle(self,val,transaction):
        """finds a Family in the database from the passed gramps' ID.
        If no such Family exists, a new Family is added to the database."""

        family = Family()
        if self.family_map.get(str(val)):
            family.unserialize(self.family_map.get(str(val)))
        else:
            family.set_handle(val)
            self.add_family(family,transaction)
        return family

    def get_person_from_gramps_id(self,val):
        """
        Finds a Person in the database from the passed GRAMPS ID.
        If no such Person exists, None is returned.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_family_from_gramps_id(self,val):
        """
        Finds a Family in the database from the passed GRAMPS ID.
        If no such Family exists, None is returned.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_place_from_gramps_id(self,val):
        """finds a Place in the database from the passed gramps' ID.
        If no such Place exists, a new Person is added to the database.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_source_from_gramps_id(self,val):
        """finds a Source in the database from the passed gramps' ID.
        If no such Source exists, a new Person is added to the database.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class" 

    def get_object_from_gramps_id(self,val):
        """finds a MediaObject in the database from the passed gramps' ID.
        If no such MediaObject exists, a new Person is added to the database.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def add_person(self,person,transaction):
        """
        Adds a Person to the database, assigning internal IDs if they have
        not already been defined.
        """
        if not person:
            return None
        if not person.get_gramps_id():
            person.set_gramps_id(self.find_next_person_gramps_id())
        if not person.get_handle():
            person.set_handle(self.create_id())
        self.commit_person(person,transaction)
        return person.get_handle()

    def add_family(self,family,transaction):
        """
        Adds a Family to the database, assigning internal IDs if they have
        not already been defined.
        """
        if not family:
            return None
        if family.get_gramps_id() == None:
            family.set_gramps_id(self.find_next_family_gramps_id())
        if family.get_handle() == None:
            family.set_handle(self.create_id())
        self.commit_family(family,transaction)
        return family.get_handle()

    def add_source(self,source,transaction):
        """
        Adds a Source to the database, assigning internal IDs if they have
        not already been defined.
        """
        if not source:
            return None
        if source.get_handle() == None:
            source.set_handle(self.create_id())
        if source.get_gramps_id() == None:
            source.set_gramps_id(self.find_next_source_gramps_id())
        self.commit_source(source,transaction)
        return source.get_handle()

    def add_event(self,event,transaction):
        """
        Adds an Event to the database, assigning internal IDs if they have
        not already been defined.
        """
        if not event:
            return None
        if event.get_handle() == None:
            event.set_handle(self.create_id())
        if event.get_gramps_id() == None:
            event.set_gramps_id(self.find_next_event_gramps_id())
        self.commit_event(event,transaction)
        return event.get_handle()

    def add_place(self,place,transaction):
        """
        Adds a Place to the database, assigning internal IDs if they have
        not already been defined.
        """
        if not place:
            return None
        if place.get_handle() == None:
            index = self.create_id()
            place.set_handle(index)
        if place.get_gramps_id() == None:
            place.set_gramps_id(self.find_next_place_gramps_id())
        self.commit_place(place,transaction)
        return place.get_handle()

    def add_object(self,obj,transaction):
        """
        Adds a MediaObject to the database, assigning internal IDs if they have
        not already been defined.
        """
        if not obj:
            return None
        index = obj.get_handle()
        if index == None:
            index = self.create_id()
            obj.set_handle(index)
        if obj.get_gramps_id() == None:
            obj.set_gramps_id(self.find_next_object_gramps_id())
        self.commit_media_object(obj,transaction)
        return index

    def get_name_group_mapping(self,name):
        """
        Returns the default grouping name for a surname
        """
        return self.name_group.get(str(name),name)

    def get_name_group_keys(self):
        """
        Returns the defined names that have been assigned to a default grouping
        """
        return [unicode(k) for k in self.name_group.keys()]

    def set_name_group_mapping(self,name,group):
        """
        Sets the default grouping name for a surname. Needs to be overridden in the
        derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_number_of_people(self):
        """
        Returns the number of people currently in the databse.
        """
        return len(self.person_map)

    def get_number_of_families(self):
        """
        Returns the number of families currently in the databse.
        """
        return len(self.family_map)

    def get_number_of_events(self):
        """
        Returns the number of events currently in the databse.
        """
        return len(self.event_map)

    def get_number_of_places(self):
        """
        Returns the number of places currently in the databse.
        """
        return len(self.place_map)

    def get_number_of_sources(self):
        """
        Returns the number of sources currently in the databse.
        """
        return len(self.source_map)

    def get_number_of_media_objects(self):
        """
        Returns the number of media objects currently in the databse.
        """
        return len(self.media_map)

    def get_person_handles(self,sort_handles=True):
        """
        Returns a list of database handles, one handle for each Person in
        the database. If sort_handles is True, the list is sorted by surnames
        """
        if self.person_map:
            if sort_handles:
                slist = []
                cursor = self.get_person_cursor()
                data = cursor.first()
                while data:
                    slist.append((data[1][3].sname,data[0]))
                    data = cursor.next()
                cursor.close()
                slist.sort()
                return map(lambda x: x[1], slist)
            else:
                return self.person_map.keys()
        return []

    def get_place_handles(self,sort_handles=True):
        """
        Returns a list of database handles, one handle for each Place in
        the database. If sort_handles is True, the list is sorted by
        Place title.
        """
        if self.place_map:
            if sort_handles:
                slist = []
                cursor = self.get_place_cursor()
                data = cursor.first()
                while data:
                    slist.append((data[1][2],data[0]))
                    data = cursor.next()
                cursor.close()
                slist.sort()
                val = map(lambda x: x[1], slist)
                return val
            else:
                return self.place_map.keys()
        return []

    def get_source_handles(self,sort_handles=True):
        """
        Returns a list of database handles, one handle for each Source in
        the database. If sort_handles is True, the list is sorted by
        Source title.
        """
        if self.source_map:
            handle_list = self.source_map.keys()
            if sort_handles:
                handle_list.sort(self._sortbysource)
            return handle_list
        return []

    def get_media_object_handles(self,sort_handles=True):
        """
        Returns a list of database handles, one handle for each MediaObject in
        the database. If sort_handles is True, the list is sorted by title.
        """
        if self.media_map:
            handle_list = self.media_map.keys()
            if sort_handles:
                handle_list.sort(self._sortbymedia)
            return handle_list
        return []

    def get_event_handles(self):
        """
        Returns a list of database handles, one handle for each Event in
        the database. 
        """
        if self.event_map:
            return self.event_map.keys()
        return []

    def get_family_handles(self):
        """
        Returns a list of database handles, one handle for each Family in
        the database.
        """
        if self.family_map:
            return self.family_map.keys()
        return []

    def _validated_id_prefix(self, val, default):
        if val:
            try:
                junk = val % 1
                prefix_var = val    # use the prefix as is because it works fine
            except:
                try:
                    val = val + "%d"
                    junk = val % 1
                    prefix_var = val    # format string was missing
                except:
                    prefix_var = default+"%04d" # use default
        else:
            prefix_var = default+"%04d"
        return prefix_var
    
    def set_person_id_prefix(self,val):
        """
        Sets the naming template for GRAMPS Person ID values. The string is expected
        to be in the form of a simple text string, or in a format that contains
        a C/Python style format string using %d, such as I%d or I%04d.
        """
        self.iprefix = self._validated_id_prefix(val,"I")
            
    def set_source_id_prefix(self,val):
        """
        Sets the naming template for GRAMPS Source ID values. The string is expected
        to be in the form of a simple text string, or in a format that contains
        a C/Python style format string using %d, such as S%d or S%04d.
        """
        self.sprefix = self._validated_id_prefix(val,"S")
            
    def set_object_id_prefix(self,val):
        """
        Sets the naming template for GRAMPS MediaObject ID values. The string is expected
        to be in the form of a simple text string, or in a format that contains
        a C/Python style format string using %d, such as O%d or O%04d.
        """
        self.oprefix = self._validated_id_prefix(val,"O")

    def set_place_id_prefix(self,val):
        """
        Sets the naming template for GRAMPS Place ID values. The string is expected
        to be in the form of a simple text string, or in a format that contains
        a C/Python style format string using %d, such as P%d or P%04d.
        """
        self.pprefix = self._validated_id_prefix(val,"P")

    def set_family_id_prefix(self,val):
        """
        Sets the naming template for GRAMPS Family ID values. The string is expected
        to be in the form of a simple text string, or in a format that contains
        a C/Python style format string using %d, such as F%d or F%04d.
        """
        self.fprefix = self._validated_id_prefix(val,"F")

    def set_event_id_prefix(self,val):
        """
        Sets the naming template for GRAMPS Event ID values. The string is expected
        to be in the form of a simple text string, or in a format that contains
        a C/Python style format string using %d, such as E%d or E%04d.
        """
        self.eprefix = self._validated_id_prefix(val,"E")
            
    def transaction_begin(self,msg=""):
        """
        Creates a new Transaction tied to the current UNDO database. The transaction
        has no effect until it is committed using the transaction_commit function of
        the this database object.
        """
        if self.__LOG_ALL:
            log("%s: Transaction begin '%s'\n" % (self.__class__.__name__, str(msg)))
        return Transaction(msg,self.undodb)

    def transaction_commit(self,transaction,msg):
        """
        Commits the transaction to the assocated UNDO database.
        """
        if self.__LOG_ALL:
            log("%s: Transaction commit '%s'\n" % (self.__class__.__name__, str(msg)))
        if not len(transaction) or self.readonly:
            return
        transaction.set_description(msg)
        self.undoindex += 1
        if self.undoindex == _UNDO_SIZE:
            self.translist = self.translist[0:-1] + [ transaction ]
        else:
            self.translist[self.undoindex] = transaction
            
        if self.undo_callback:
            self.undo_callback(_("_Undo %s") % transaction.get_description())

    def undo(self):
        """
        Accesses the last committed transaction, and reverts the data to
        the state before the transaction was committed.
        """
        if self.undoindex == -1 or self.readonly:
            return False
        transaction = self.translist[self.undoindex]

        self.undoindex -= 1
        subitems = transaction.get_recnos()
        subitems.reverse()
        for record_id in subitems:
            (key, handle, data) = transaction.get_record(record_id)
            handle = str(handle)
            if key == PERSON_KEY:
                self.undo_data(data,handle,self.person_map,'person')
            elif key == FAMILY_KEY:
                self.undo_data(data,handle,self.family_map,'family')
            elif key == SOURCE_KEY:
                self.undo_data(data,handle,self.source_map,'source')
            elif key == EVENT_KEY:
                if data == None:
                    del self.event_map[handle]
                else:
                    self.event_map[handle] = data
            elif key == PLACE_KEY:
                self.undo_data(data,handle,self.place_map,'place')
            elif key == MEDIA_KEY:
                self.undo_data(data,handle,self.media_map,'media')

        if self.undo_callback:
            if self.undoindex == -1:
                self.undo_callback(None)
            else:
                transaction = self.translist[self.undoindex]
                self.undo_callback(_("_Undo %s") % transaction.get_description())
        return True

    def undo_data(self,data,handle,db_map,signal_root):
        if data == None:
            self.emit(signal_root + '-delete',([handle],))
            del db_map[handle]
        else:
            if db_map.has_key(handle):
                signal = signal_root + '-update'
            else:
                signal = signal_root + '-add'
            db_map[handle] = data
            self.emit(signal,([handle],))
    
    def set_undo_callback(self,callback):
        """
        Defines the callback function that is called whenever an undo operation
        is executed. The callback function recieves a single argument that is a
        text string that defines the operation.
        """
        self.undo_callback = callback

    def set_redo_callback(self,callback):
        """
        Defines the callback function that is called whenever an redo operation
        is executed. The callback function recieves a single argument that is a
        text string that defines the operation.
        """
        self.redo_callback = callback

    def get_surname_list(self):
        """
        Returns the list of surnames contained within the database.
        The function must be overridden in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_person_event_type_list(self):
        """
        Returns the list of personal event types contained within the
        database. The function must be overridden in the derived class.
        """
        return list(self.individual_event_names)

    def get_bookmarks(self):
        """returns the list of Person handles in the bookmarks"""
        return self.bookmarks

    def set_researcher(self,owner):
        """sets the information about the owner of the database"""
        self.owner.set(owner.get_name(),owner.get_address(),owner.get_city(),
                       owner.get_state(),owner.get_country(),
                       owner.get_postal_code(),owner.get_phone(),owner.get_email())

    def get_researcher(self):
        """returns the Researcher instance, providing information about
        the owner of the database"""
        return self.owner

    def set_default_person_handle(self,handle):
        """sets the default Person to the passed instance"""
        if not self.readonly:
            self.metadata['default'] = handle

    def get_default_person(self):
        """returns the default Person of the database"""
        if self.metadata and self.metadata.has_key('default') and not self.readonly:
            person = Person()
            handle = self.metadata['default']
            data = self.person_map.get(str(handle),None)
            if data:
                person.unserialize(data)
                return person
            else:
                self.metadata['default'] = None
                return None
        return None

    def get_save_path(self):
        """returns the save path of the file, or "" if one does not exist"""
        return self.path

    def set_save_path(self,path):
        """sets the save path for the database"""
        self.path = path

    def get_person_event_types(self):
        """returns a list of all Event types assocated with Person
        instances in the database"""
        return list(self.individual_event_names)

    def get_person_attribute_types(self):
        """returns a list of all Attribute types assocated with Person
        instances in the database"""
        return list(self.individual_attributes)

    def get_family_attribute_types(self):
        """returns a list of all Attribute types assocated with Family
        instances in the database"""
        return list(self.family_attributes)

    def get_family_event_types(self):
        """returns a list of all Event types assocated with Family
        instances in the database"""
        return list(self.family_event_names)


    def get_media_attribute_types(self):
        """returns a list of all Attribute types assocated with Media
        instances in the database"""
        return []

    def get_family_relation_types(self):
        """returns a list of all relationship types assocated with Family
        instances in the database"""
        return []

    def remove_person(self,handle,transaction):
        """
        Removes the Person specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def remove_source(self,handle,transaction):
        """
        Removes the Source specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def remove_event(self,handle,transaction):
        """
        Removes the Event specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def remove_object(self,handle,transaction):
        """
        Removes the MediaObjectPerson specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def remove_place(self,handle,transaction):
        """
        Removes the Place specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def remove_family(self,handle,transaction):
        """
        Removes the Family specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def has_person_handle(self,handle):
        """
        returns True if the handle exists in the current Person database.
        """
        return self.person_map.has_key(str(handle))

    def has_family_handle(self,handle):            
        """
        returns True if the handle exists in the current Family database.
        """
        return self.family_map.has_key(str(handle))

    def has_object_handle(self,handle):
        """
        returns True if the handle exists in the current MediaObjectdatabase.
        """
        return self.media_map.has_key(str(handle)) != None

    def _sortbyname(self,f,s):
        n1 = self.person_map.get(str(f))[3].sname
        n2 = self.person_map.get(str(s))[3].sname
        return locale.strcoll(n1,n2)

    def _sortbyplace(self,f,s):
        return locale.strcoll(self.place_map.get(str(f))[2],
                              self.place_map.get(str(s))[2])

    def _sortbysource(self,f,s):
        fp = unicode(self.source_map[str(f)][2])
        sp = unicode(self.source_map[str(s)][2])
        return locale.strcoll(fp,sp)

    def _sortbymedia(self,f,s):
        fp = self.media_map[str(f)][4]
        sp = self.media_map[str(s)][4]
        return locale.strcoll(fp,sp)

    def set_person_column_order(self,list):
        """
        Stores the Person display common information in the
        database's metadata.
        """
        if self.metadata != None and not self.readonly: 
            self.metadata['columns'] = list

    def set_child_column_order(self,list):
        """
        Stores the Person display common information in the
        database's metadata.
        """
        if self.metadata != None and not self.readonly:
            self.metadata['child_columns'] = list

    def set_place_column_order(self,list):
        """
        Stores the Place display common information in the
        database's metadata.
        """
        if self.metadata != None and not self.readonly:
            self.metadata['place_columns'] = list

    def set_source_column_order(self,list):
        """
        Stores the Source display common information in the
        database's metadata.
        """
        if self.metadata != None and not self.readonly:
            self.metadata['source_columns'] = list

    def set_media_column_order(self,list):
        """
        Stores the Media display common information in the
        database's metadata.
        """
        if self.metadata != None and not self.readonly:
            self.metadata['media_columns'] = list

    def get_person_column_order(self):
        """
        Returns the Person display common information stored in the
        database's metadata.
        """
        default = [(1,1),(1,2),(1,3),(0,4),(1,5),(0,6),(0,7),(0,8),(0,9,)]
        if self.metadata == None:
            return default
        else:
            cols = self.metadata.get('columns',default)
            if len(cols) != len(default):
                return cols + default[len(cols):]
            else:
                return cols

    def get_child_column_order(self):
        """
        Returns the Person display common information stored in the
        database's metadata.
        """
        default = [(1,0),(1,1),(1,2),(1,3),(1,4),(1,5),(0,6),(0,7)]
        if self.metadata == None:
            return default
        else:
            cols = self.metadata.get('child_columns',default)
            if len(cols) != len(default):
                return cols + default[len(cols):]
            else:
                return cols

    def get_place_column_order(self):
        """
        Returns the Place display common information stored in the
        database's metadata.
        """
        default = [(1,1),(1,2),(0,3),(0,4),(1,5),(0,6),(1,7),(0,8),(0,9),(0,10)]
        if self.metadata == None:
            return default
        else:
            cols = self.metadata.get('place_columns',default)
            if len(cols) != len(default):
                return cols + default[len(cols):]
            else:
                return cols

    def get_source_column_order(self):
        """
        Returns the Source display common information stored in the
        database's metadata.
        """
        default = [(1,1),(1,2),(0,3),(1,4),(0,5)]
        if self.metadata == None:
            return default
        else:
            cols = self.metadata.get('source_columns',default)
            if len(cols) != len(default):
                return cols + default[len(cols):]
            else:
                return cols

    def get_media_column_order(self):
        """
        Returns the MediaObject display common information stored in the
        database's metadata.
        """
        default = [(1,1),(0,5),(0,4),(1,2),(1,3)]
        if self.metadata == None:
            return default
        else:
            cols = self.metadata.get('media_columns',default)
            if len(cols) != len(default):
                return cols + default[len(cols):]
            else:
                return cols

class Transaction:
    """
    Defines a group of database commits that define a single logical
    operation.
    """
    def __init__(self,msg,db):
        """
        Creates a new transaction. A Transaction instance should not be created
        directly, but by the GrampsDbBase class or classes derived from
        GrampsDbBase. The db parameter is a list-like interface that stores
        the commit data. This could be a simple list, or a RECNO-style database
        object.
        """
        self.db = db
        self.first = None
        self.last = None
        self.batch = False

    def set_batch(self,batch):
        self.batch = batch

    def get_batch(self):
        return self.batch
    
    def get_description(self):
        """
        Returns the text string that describes the logical operation
        performed by the Transaction.
        """
        return self.msg

    def set_description(self,msg):
        """
        Sets the text string that describes the logical operation
        performed by the Transaction.
        """
        self.msg = msg

    def add(self, type, handle, data):
        """
        Adds a commit operation to the Transaction. The type is a constant
        that indicates what type of PrimaryObject is being added. The handle
        is the object's database handle, and the data is the tuple returned
        by the object's serialize method.
        """
        self.last = self.db.append(cPickle.dumps((type,handle,data),1))
        if self.first == None:
            self.first = self.last

    def get_recnos(self):
        """
        Returns a list of record numbers associated with the transaction.
        While the list is an arbitrary index of integers, it can be used
        to indicate record numbers for a database.
        """
        return range (self.first, self.last+1)

    def get_record(self,recno):
        """
        Returns a tuple representing the PrimaryObject type, database handle
        for the PrimaryObject, and a tuple representing the data created by
        the object's serialize method.
        """
        return cPickle.loads(self.db[recno])

    def __len__(self):
        """
        Returns the number of commits associated with the Transaction.
        """
        if self.last and self.first:
            return self.last - self.first + 1
        return 0
