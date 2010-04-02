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
Provides the common infrastructure for database formats that
must hold all of their data in memory.
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from RelLib import *
from GrampsDbBase import *
import sets

class GrampsInMemCursor(GrampsCursor):
    """
    Cursor class for in-memory database classes. Since the in-memory
    classes use python dictionaries, the python iter class is used
    to provide the cursor function.
    """
    def __init__(self,src_map):
        self.src_map = src_map
        self.current = iter(src_map)
        
    def first(self):
        self.current = iter(self.src_map)
        return self.next()

    def next(self):
        try:
            index = self.current.next()
            return (index,self.src_map[index])
        except StopIteration:
            return None

    def close(self):
        pass
        
#-------------------------------------------------------------------------
#
# GrampsInMemDB
#
#-------------------------------------------------------------------------
class GrampsInMemDB(GrampsDbBase):
    """GRAMPS database object. This object is a base class for other
    objects."""

    def __init__(self):
        """creates a new GrampsDB"""
        GrampsDbBase.__init__(self)
        self.person_map = {}
        self.name_group = {}
        self.family_map = {}
        self.place_map  = {}
        self.source_map = {}
        self.media_map  = {}
        self.event_map  = {}
        self.metadata   = {}
        self.filename   = ""
        self.id_trans   = {}
        self.pid_trans  = {}
        self.fid_trans  = {}
        self.sid_trans  = {}
        self.oid_trans  = {}
        self.undodb     = []

    def load(self,name,callback,mode="w"):
        pass

    def get_person_cursor(self):
        return GrampsInMemCursor(self.person_map)

    def get_family_cursor(self):
        return GrampsInMemCursor(self.family_map)

    def get_place_cursor(self):
        return GrampsInMemCursor(self.place_map)

    def get_source_cursor(self):
        return GrampsInMemCursor(self.source_map)

    def get_media_cursor(self):
        return GrampsInMemCursor(self.media_map)

    def get_event_cursor(self):
        return GrampsInMemCursor(self.event_map)

    def close(self):
        pass

    def abort_changes(self):
        pass
    
    def set_name_group_mapping(self,name,group):
        if group == None and self.name_group.has_key(name):
            del self.name_group[name]
        else:
            self.name_group[name] = group

    def get_surname_list(self):
        a = {}
        for person_id in iter(self.person_map):
            p = self.get_person_from_handle(person_id)
            a[p.get_primary_name().get_group_as()] = 1
        vals = a.keys()
        vals.sort()
        return vals

    def remove_person(self,handle,transaction):
        if self.readonly or not handle or str(handle) not in self.person_map:
            return
        person = self.get_person_from_handle(handle)
        self.genderStats.uncount_person (person)
        if transaction != None:
            old_data = self.person_map.get(handle)
            transaction.add(PERSON_KEY,handle,old_data)
        self.emit('person-delete',([handle],))
        del self.id_trans[person.get_gramps_id()]
        del self.person_map[handle]

    def remove_source(self,handle,transaction):
        if self.readonly or not handle or str(handle) not in self.source_map:
            return
        source = self.get_source_from_handle(handle)
        if transaction != None:
            old_data = self.source_map.get(str(handle))
            transaction.add(SOURCE_KEY,handle,old_data)
        self.emit('source-delete',([handle],))
        del self.sid_trans[source.get_gramps_id()]
        del self.source_map[str(handle)]

    def remove_place(self,handle,transaction):
        if self.readonly or not handle or str(handle) not in self.place_map:
            return
        place = self.get_place_from_handle(handle)
        if transaction != None:
            old_data = self.place_map.get(str(handle))
            transaction.add(PLACE_KEY,handle,old_data)
        self.emit('place-delete',([handle],))
        del self.pid_trans[place.get_gramps_id()]
        del self.place_map[str(handle)]

    def remove_object(self,handle,transaction):
        if self.readonly or not handle or str(handle) not in self.media_map:
            return
        obj = self.get_object_from_handle(handle)
        if transaction != None:
            old_data = self.media_map.get(str(handle))
            transaction.add(MEDIA_KEY,handle,old_data)
        self.emit('media-delete',([handle],))
        del self.oid_trans[obj.get_gramps_id()]
        del self.media_map[str(handle)]

    def remove_family(self,handle,transaction):
        if self.readonly or not handle or str(handle) not in self.family_map:
            return
        family = self.get_family_from_handle(handle)
        if transaction != None:
            old_data = self.family_map.get(str(handle))
            transaction.add(FAMILY_KEY,handle,old_data)
        self.emit('family-delete',([handle],))
        del self.fid_trans[family.get_gramps_id()]
        del self.family_map[str(handle)]

    def remove_event(self,handle,transaction):
        if self.readonly or not handle or str(handle) not in self.event_map:
            return
        if transaction != None:
            old_data = self.event_map.get(str(handle))
            transaction.add(EVENT_KEY,handle,old_data)
        del self.event_map[str(handle)]

    def commit_person(self,person,transaction,change_time=None):
        if self.readonly or not person or not person.get_handle():
            return
        gid = person.get_gramps_id()
        self.id_trans[gid] = person.get_handle()
        GrampsDbBase.commit_person(self,person,transaction,change_time)

    def commit_place(self,place,transaction,change_time=None):
        if self.readonly or not place or not place.get_handle():
            return
        gid = place.get_gramps_id()
        self.pid_trans[gid] = place.get_handle()
        GrampsDbBase.commit_place(self,place,transaction,change_time)

    def commit_family(self,family,transaction,change_time=None):
        if self.readonly or not family or not family.get_handle():
            return
        gid = family.get_gramps_id()
        self.fid_trans[gid] = family.get_handle()
        GrampsDbBase.commit_family(self,family,transaction,change_time)

    def commit_media_object(self,obj,transaction,change_time=None):
        if self.readonly or not obj or not obj.get_handle():
            return
        gid = obj.get_gramps_id()
        self.oid_trans[gid] = obj.get_handle()
        GrampsDbBase.commit_media_object(self,obj,transaction,change_time)

    def commit_source(self,source,transaction,change_time=None):
        if self.readonly or not source or not source.get_handle():
            return
        gid = source.get_gramps_id()
        self.sid_trans[gid] = source.get_handle()
        GrampsDbBase.commit_source(self,source,transaction,change_time)

    def get_person_from_gramps_id(self,val):
        handle = self.id_trans.get(str(val))
        if handle:
            data = self.person_map[handle]
            if data:
                person = Person()
                person.unserialize(data)
                return person
        return None

    def get_family_from_gramps_id(self,val):
        handle = self.fid_trans.get(str(val))
        if handle:
            data = self.family_map[handle]
            if data:
                family = Family()
                family.unserialize(data)
                return family
        return None

    def get_place_from_gramps_id(self,val):
        handle = self.pid_trans.get(str(val))
        if handle:
            data = self.place_map[handle]
            if data:
                place = Place()
                place.unserialize(data)
                return place
        return None

    def get_source_from_gramps_id(self,val):
        handle = self.sid_trans.get(str(val))
        if handle:
            data = self.source_map[handle]
            if data:
                source = Source()
                source.unserialize(data)
                return source
        return None

    def get_object_from_gramps_id(self,val):
        handle = self.oid_trans.get(str(val))
        if handle:
            data = self.media_map[handle]
            if data:
                obj = MediaObject()
                obj.unserialize(data)
                return obj
        return None
