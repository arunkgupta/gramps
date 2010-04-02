#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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

__author__ = "Donald N. Allingham"
__revision__ = "$Revision$"

#-------------------------------------------------------------------------
#
# libraries
#
#-------------------------------------------------------------------------
import cPickle
import time
import random
import locale
import os
from sys import maxint
from bsddb import db
from gettext import gettext as _

import logging
log = logging.getLogger(".GrampsDb")

#-------------------------------------------------------------------------
#
# GRAMPS libraries
#
#-------------------------------------------------------------------------
from RelLib import *
import Config
from _GrampsDBCallback import GrampsDBCallback

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
REPOSITORY_KEY = 6
REFERENCE_KEY  = 7

PERSON_COL_KEY      = 'columns'
CHILD_COL_KEY       = 'child_columns'
PLACE_COL_KEY       = 'place_columns'
SOURCE_COL_KEY      = 'source_columns'
MEDIA_COL_KEY       = 'media_columns'
REPOSITORY_COL_KEY  = 'repository_columns'
EVENT_COL_KEY       = 'event_columns'
FAMILY_COL_KEY      = 'family_columns'


# The following two dictionaries provide fast translation
# between the primary class names and the keys used to reference
# these classes in the database tables. Beware that changing
# these maps or modifying the values of the keys will break
# existing databases.

CLASS_TO_KEY_MAP = {Person.__name__: PERSON_KEY, 
                    Family.__name__: FAMILY_KEY, 
                    Source.__name__: SOURCE_KEY, 
                    Event.__name__: EVENT_KEY, 
                    MediaObject.__name__: MEDIA_KEY, 
                    Place.__name__: PLACE_KEY, 
                    Repository.__name__:REPOSITORY_KEY}

KEY_TO_CLASS_MAP = {PERSON_KEY: Person.__name__, 
                    FAMILY_KEY: Family.__name__, 
                    SOURCE_KEY: Source.__name__, 
                    EVENT_KEY: Event.__name__, 
                    MEDIA_KEY: MediaObject.__name__, 
                    PLACE_KEY: Place.__name__, 
                    REPOSITORY_KEY: Repository.__name__}

_sigbase = ('person', 'family', 'source', 'event', 
            'media', 'place', 'repository')

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

class GrampsDbBookmarks:
    def __init__(self, default=[]):
        self.bookmarks = list(default) # want a copy (not an alias)

    def set(self, new_list):
        self.bookmarks = list(new_list)

    def get(self):
        return self.bookmarks

    def append(self, item):
        self.bookmarks.append(item)

    def append_list(self, blist):
        self.bookmarks += blist

    def remove(self, item):
        self.bookmarks.remove(item)

    def pop(self, item):
        self.bookmarks.pop(item)

    def insert(self, pos, item):
        self.bookmarks.insert(pos, item)

class GrampsDbBase(GrampsDBCallback):
    """
    GRAMPS database object. This object is a base class for all
    database interfaces.
    """

    __signals__ = {
        'person-add'     : (list, ), 
        'person-update'  : (list, ), 
        'person-delete'  : (list, ), 
        'person-rebuild' : None, 
        'family-add'     : (list, ), 
        'family-update'  : (list, ), 
        'family-delete'  : (list, ), 
        'family-rebuild' : None, 
        'source-add'     : (list, ), 
        'source-update'  : (list, ), 
        'source-delete'  : (list, ), 
        'source-rebuild' : None, 
        'place-add'      : (list, ), 
        'place-update'   : (list, ), 
        'place-delete'   : (list, ), 
        'place-rebuild'  : None, 
        'media-add'      : (list, ), 
        'media-update'   : (list, ), 
        'media-delete'   : (list, ), 
        'media-rebuild'  : None, 
        'event-add'      : (list, ), 
        'event-update'   : (list, ), 
        'event-delete'   : (list, ), 
        'event-rebuild'  : None, 
        'repository-add'      : (list, ), 
        'repository-update'   : (list, ), 
        'repository-delete'   : (list, ), 
        'repository-rebuild'  : None, 
        }
    

    # If this is True logging will be turned on.
    try:
        __LOG_ALL = int(os.environ.get('GRAMPS_SIGNAL', "0")) == 1
    except:
        __LOG_ALL = False


    def __init__(self):
        """
        Creates a new GrampsDbBase instance. A new GrampDbBase class should
        never be directly created. Only classes derived from this class should
        be created.
        """

        GrampsDBCallback.__init__(self)
        self.readonly = False
        self.rand = random.Random(time.time())
        self.smap_index = 0
        self.emap_index = 0
        self.pmap_index = 0
        self.fmap_index = 0
        self.lmap_index = 0
        self.omap_index = 0
        self.rmap_index = 0
        self.db_is_open = False

        self.family_event_names = set()
        self.individual_event_names = set()
        self.individual_attributes = set()
        self.family_attributes = set()
        self.marker_names = set()
        self.child_ref_types = set()
        self.family_rel_types = set()
        self.event_role_names = set()
        self.name_types = set()
        self.repository_types = set()
        self.source_media_types = set()
        self.url_types = set()
        self.media_attributes = set()

        self.set_person_id_prefix(Config.get(Config.IPREFIX))
        self.set_object_id_prefix(Config.get(Config.OPREFIX))
        self.set_family_id_prefix(Config.get(Config.FPREFIX))
        self.set_source_id_prefix(Config.get(Config.SPREFIX))
        self.set_place_id_prefix(Config.get(Config.PPREFIX))
        self.set_event_id_prefix(Config.get(Config.EPREFIX))
        self.set_repository_id_prefix(Config.get(Config.RPREFIX))

        self.open = 0
        self.genderStats = GenderStats()

        self.undodb    = None
        self.id_trans  = None
        self.fid_trans = None
        self.pid_trans = None
        self.sid_trans = None
        self.oid_trans = None
        self.rid_trans = None
        self.eid_trans = None
        self.env = None
        self.person_map = None
        self.family_map = None
        self.place_map  = None
        self.source_map = None
        self.repository_map  = None
        self.media_map  = None
        self.event_map  = None
        self.metadata   = None
        self.name_group = None
        self.undo_callback = None
        self.redo_callback = None
        self.undo_history_callback = None
        self.modified   = 0

        self.undoindex  = -1
        self.translist  = [None] * _UNDO_SIZE
        self.abort_possible = True
        self.undo_history_timestamp = 0
        self.default = None
        self.owner = Researcher()
        self.name_formats = []
        self.bookmarks = GrampsDbBookmarks()
        self.family_bookmarks = GrampsDbBookmarks()
        self.event_bookmarks = GrampsDbBookmarks()
        self.place_bookmarks = GrampsDbBookmarks()
        self.source_bookmarks = GrampsDbBookmarks()
        self.repo_bookmarks = GrampsDbBookmarks()
        self.media_bookmarks = GrampsDbBookmarks()
        self.path = ""
        self.name_group = {}
        self.surname_list = []
        self._bm_changes = 0

    def rebuild_secondary(self, callback):
        pass

    def version_supported(self):
        """ Returns True when the file has a supported version"""
        return True

    def need_upgrade(self):
        return False

    def gramps_upgrade(self):
        pass

    def _del_person(self, handle):
        pass

    def _del_source(self, handle):
        pass

    def _del_repository(self, handle):
        pass

    def _del_place(self, handle):
        pass

    def _del_media(self, handle):
        pass

    def _del_family(self, handle):
        pass

    def _del_event(self, handle):
        pass

    def create_id(self):
        return "%08x%08x" % ( int(time.time()*10000), 
                              self.rand.randint(0, maxint))

    def get_person_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def get_family_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def get_event_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def get_place_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def get_source_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def get_media_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def get_repository_cursor(self):
        assert False, "Needs to be overridden in the derived class"

    def open_undodb(self):
        if not self.readonly:
            self.undolog = "%s.undo" % self.full_name
            self.undodb = db.DB()
            self.undodb.open(self.undolog, db.DB_RECNO, db.DB_CREATE)

    def close_undodb(self):
        if not self.readonly:
            try:
                self.undodb.close()
            except db.DBNoSuchFileError, msg:
                pass
            try:
                os.remove(self.undolog)
            except:
                pass

    def load(self, name, callback, mode="w"):
        """
        Opens the specified database. The method needs to be overridden
        in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def load_from(self, other_database, filename, callback):
        """
        Loads data from the other database into itself.
        The filename is the name of the file for the newly created database.
        The method needs to be overridden in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def close(self):
        """
        Closes the specified database. The method needs to be overridden
        in the derived class.
        """
        pass
        
    def is_open(self):
        """
        Returns 1 if the database has been opened.
        """
        return self.db_is_open

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
        self.emit('event-rebuild')
        self.emit('repository-rebuild')
            
    def _commit_base(self, obj, data_map, key, update_list, add_list, 
                     transaction, change_time):
        """
        Commits the specified Person to the database, storing the changes
        as part of the transaction.
        """
        if self.readonly or not obj or not obj.handle:
            return 

        if change_time:
            obj.change = int(change_time)
        else:
            obj.change = int(time.time())
        handle = str(obj.handle)
        
        self._update_reference_map(obj, transaction)

        try:
            if transaction.batch:
                data_map[handle] = obj.serialize()
                old_data = None
            else:
                old_data = data_map.get(handle)
                new_data = obj.serialize()
                transaction.add(key, handle, old_data, new_data)
                if old_data:
                    update_list.append((handle, new_data))
                else:
                    add_list.append((handle, new_data))
        except db.DBNoSpaceError, msg:
            from QuestionDialog import ErrorDialog

            ErrorDialog(_("Out of disk space"),
                        _("Your data cannot be saved because you are out "
                          "of disk space. Please free up some disk space "
                          "and try again.\n\n%s") % msg[1])
        return old_data

    def commit_person(self, person, transaction, change_time=None):
        """
        Commits the specified Person to the database, storing the changes
        as part of the transaction.
        """

        old_data = self._commit_base(
            person, self.person_map, PERSON_KEY, transaction.person_update, 
            transaction.person_add, transaction, change_time)
        if old_data:
            old_person = Person(old_data)
            if (old_data[2] != person.gender or
                old_data[3][4]!= person.primary_name.first_name):
                self.genderStats.uncount_person(old_person)
                self.genderStats.count_person(person)
            if (old_data[3][5]!=person.primary_name.surname):
                self.remove_from_surname_list(old_person)
                self.add_to_surname_list(person,transaction.batch)
        else:
            self.genderStats.count_person(person)
            self.add_to_surname_list(person,transaction.batch)

        self.individual_attributes.update(
            [str(attr.type) for attr in person.attribute_list
             if attr.type.is_custom() and str(attr.type)])

        if person.marker.is_custom():
            self.marker_names.add(str(person.marker))

        self.event_role_names.update([str(eref.role)
                                      for eref in person.event_ref_list
                                      if eref.role.is_custom()])

        self.name_types.update([str(name.type)
                                for name in ([person.primary_name]
                                             + person.alternate_names)
                                if name.type.is_custom()])
        
        self.url_types.update([str(url.type) for url in person.urls
                               if url.type.is_custom()])

        attr_list = []
        for mref in person.media_list:
            attr_list += [str(attr.type) for attr in mref.attribute_list
                          if attr.type.is_custom() and str(attr.type)]
        self.media_attributes.update(attr_list)

    def commit_media_object(self, obj, transaction, change_time=None):
        """
        Commits the specified MediaObject to the database, storing the changes
        as part of the transaction.
        """
        
        self._commit_base(obj, self.media_map, MEDIA_KEY, 
                          transaction.media_update, transaction.media_add, 
                          transaction, change_time)
        self.media_attributes.update(
            [str(attr.type) for attr in obj.attribute_list
             if attr.type.is_custom() and str(attr.type)])
            
    def commit_source(self, source, transaction, change_time=None):
        """
        Commits the specified Source to the database, storing the changes
        as part of the transaction.
        """

        self._commit_base(source, self.source_map, SOURCE_KEY, 
                          transaction.source_update, transaction.source_add, 
                          transaction, change_time)

        self.source_media_types.update(
            [str(ref.media_type) for ref in source.reporef_list
             if ref.media_type.is_custom()])       

        attr_list = []
        for mref in source.media_list:
            attr_list += [str(attr.type) for attr in mref.attribute_list
                          if attr.type.is_custom() and str(attr.type)]
        self.media_attributes.update(attr_list)

    def commit_place(self, place, transaction, change_time=None):
        """
        Commits the specified Place to the database, storing the changes
        as part of the transaction.
        """

        self._commit_base(place, self.place_map, PLACE_KEY, 
                          transaction.place_update, transaction.place_add, 
                          transaction, change_time)

        self.url_types.update([str(url.type) for url in place.urls
                               if url.type.is_custom()])

        attr_list = []
        for mref in place.media_list:
            attr_list += [str(attr.type) for attr in mref.attribute_list
                          if attr.type.is_custom() and str(attr.type)]
        self.media_attributes.update(attr_list)

    def commit_personal_event(self, event, transaction, change_time=None):
        if event.type.is_custom():
            self.individual_event_names.add(str(event.type))
        self.commit_event(event, transaction, change_time)

    def commit_family_event(self, event, transaction, change_time=None):
        if event.type.is_custom():
            self.family_event_names.add(str(event.type))
        self.commit_event(event, transaction, change_time)

    def commit_event(self, event, transaction, change_time=None):
        """
        Commits the specified Event to the database, storing the changes
        as part of the transaction.
        """
        self._commit_base(event, self.event_map, EVENT_KEY, 
                          transaction.event_update, transaction.event_add, 
                          transaction, change_time)

        attr_list = []
        for mref in event.media_list:
            attr_list += [str(attr.type) for attr in mref.attribute_list
                          if attr.type.is_custom() and str(attr.type)]
        self.media_attributes.update(attr_list)

    def commit_family(self, family, transaction, change_time=None):
        """
        Commits the specified Family to the database, storing the changes
        as part of the transaction.
        """

        self._commit_base(family, self.family_map, FAMILY_KEY, 
                          transaction.family_update, transaction.family_add, 
                          transaction, change_time)

        self.family_attributes.update(
            [str(attr.type) for attr in family.attribute_list
             if attr.type.is_custom() and str(attr.type)])

        rel_list = []
        for ref in family.child_ref_list:
            if ref.frel.is_custom():
                rel_list.append(str(ref.frel))
            if ref.mrel.is_custom():
                rel_list.append(str(ref.mrel))
        self.child_ref_types.update(rel_list)

        self.event_role_names.update(
            [str(eref.role) for eref in family.event_ref_list
             if eref.role.is_custom()])

        if family.type.is_custom():
            self.family_rel_types.add(str(family.type))

        attr_list = []
        for mref in family.media_list:
            attr_list += [str(attr.type) for attr in mref.attribute_list
                          if attr.type.is_custom() and str(attr.type)]
        self.media_attributes.update(attr_list)

    def commit_repository(self, repository, transaction, change_time=None):
        """
        Commits the specified Repository to the database, storing the changes
        as part of the transaction.
        """

        self._commit_base(repository, self.repository_map, REPOSITORY_KEY, 
                          transaction.repository_update,
                          transaction.repository_add, 
                          transaction, change_time)

        if repository.type.is_custom():
            self.repository_types.add(str(repository.type))

        self.url_types.update([str(url.type) for url in repository.urls
                               if url.type.is_custom()])

    def find_next_person_gramps_id(self):
        """
        Returns the next available GRAMPS' ID for a Person object based
        off the person ID prefix.
        """
        index = self.iprefix % self.pmap_index
        while self.id_trans.has_key(str(index)):
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
        while self.pid_trans.has_key(str(index)):
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
        while self.eid_trans.has_key(str(index)):
            self.emap_index += 1
            index = self.eprefix % self.emap_index
        self.emap_index += 1
        return index

    def find_next_object_gramps_id(self):
        """
        Returns the next available GRAMPS' ID for a MediaObject object based
        off the person ID prefix.
        """
        index = self.oprefix % self.omap_index
        while self.oid_trans.has_key(str(index)):
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
        while self.sid_trans.has_key(str(index)):
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
        while self.fid_trans.has_key(str(index)):
            self.fmap_index += 1
            index = self.fprefix % self.fmap_index
        self.fmap_index += 1
        return index

    def find_next_repository_gramps_id(self):
        """
        Returns the next available GRAMPS' ID for a Respository object based
        off the repository ID prefix.
        """
        index = self.rprefix % self.rmap_index
        while self.rid_trans.has_key(str(index)):
            self.rmap_index += 1
            index = self.rprefix % self.rmap_index
        self.rmap_index += 1
        return index

    def _get_from_handle(self, handle, class_type, data_map):
        if not data_map:
            return
        data = data_map.get(str(handle))
        if data:
            newobj = class_type()
            newobj.unserialize(data)
            return newobj
        return None

    def get_person_from_handle(self, handle):
        """
        Finds a Person in the database from the passed gramps' ID.
        If no such Person exists, None is returned.
        """
        return self._get_from_handle(handle, Person, self.person_map)

    def get_source_from_handle(self, handle):
        """
        Finds a Source in the database from the passed gramps' ID.
        If no such Source exists, None is returned.
        """
        return self._get_from_handle(handle, Source, self.source_map)

    def get_object_from_handle(self, handle):
        """
        Finds an Object in the database from the passed gramps' ID.
        If no such Object exists, None is returned.
        """
        return self._get_from_handle(handle, MediaObject, self.media_map)

    def get_place_from_handle(self, handle):
        """
        Finds a Place in the database from the passed gramps' ID.
        If no such Place exists, None is returned.
        """
        return self._get_from_handle(handle, Place, self.place_map)

    def get_event_from_handle(self, handle):
        """
        Finds a Event in the database from the passed gramps' ID.
        If no such Event exists, None is returned.
        """
        return self._get_from_handle(handle, Event, self.event_map)

    def get_family_from_handle(self, handle):
        """
        Finds a Family in the database from the passed gramps' ID.
        If no such Family exists, None is returned.
        """
        return self._get_from_handle(handle, Family, self.family_map)

    def get_repository_from_handle(self, handle):
        """
        Finds a Repository in the database from the passed gramps' ID.
        If no such Repository exists, None is returned.
        """
        return self._get_from_handle(handle, Repository, self.repository_map)

    def _find_from_handle(self, handle, transaction, class_type, dmap,
                          add_func):
        obj = class_type()
        handle = str(handle)
        if dmap.has_key(handle):
            obj.unserialize(dmap.get(handle))
        else:
            obj.set_handle(handle)
            add_func(obj, transaction)
        return obj

    def _check_from_handle(self, handle, transaction, class_type, dmap,
                           add_func, set_gid=True):
        handle = str(handle)
        if not dmap.has_key(handle):
            obj = class_type()
            obj.set_handle(handle)
            add_func(obj, transaction, set_gid=set_gid)

    def find_person_from_handle(self, handle, transaction):
        """
        Finds a Person in the database from the passed GRAMPS ID.
        If no such Person exists, a new Person is added to the database.
        """
        return self._find_from_handle(handle, transaction, Person, 
                                      self.person_map, self.add_person)

    def find_source_from_handle(self, handle, transaction):
        """
        Finds a Source in the database from the passed handle.
        If no such Source exists, a new Source is added to the database.
        """
        return self._find_from_handle(handle, transaction, Source, 
                                      self.source_map, self.add_source)

    def find_event_from_handle(self, handle, transaction):
        """
        Finds a Event in the database from the passed handle.
        If no such Event exists, a new Event is added to the database.
        """
        return self._find_from_handle(handle, transaction, Event, 
                                      self.event_map, self.add_event)

    def find_object_from_handle(self, handle, transaction):
        """
        Finds an MediaObject in the database from the passed handle.
        If no such MediaObject exists, a new Object is added to the database.
        """
        return self._find_from_handle(handle, transaction, MediaObject, 
                                      self.media_map, self.add_object)

    def find_place_from_handle(self, handle, transaction):
        """
        Finds a Place in the database from the passed handle.
        If no such Place exists, a new Place is added to the database.
        """
        return self._find_from_handle(handle, transaction, Place, 
                                      self.place_map, self.add_place)

    def find_family_from_handle(self, handle, transaction):
        """
        Finds a Family in the database from the passed handle.
        If no such Family exists, a new Family is added to the database.
        """
        return self._find_from_handle(handle, transaction, Family, 
                                      self.family_map, self.add_family)

    def find_repository_from_handle(self, handle, transaction):
        """
        Finds a Repository in the database from the passed handle.
        If no such Repository exists, a new Repository is added to the database.
        """
        return self._find_from_handle(handle, transaction, Repository, 
                                      self.repository_map, self.add_repository)

    def check_person_from_handle(self, handle, transaction, set_gid=True):
        """
        Checks whether a Person with the passed handle exists in the database.
        If no such Person exists, a new Person is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self._check_from_handle(handle, transaction, Person, 
                                self.person_map, self.add_person, 
                                set_gid=set_gid)

    def check_source_from_handle(self, handle, transaction, set_gid=True):
        """
        Checks whether a Source with the passed handle exists in the database.
        If no such Source exists, a new Source is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self._check_from_handle(handle, transaction, Source, 
                                self.source_map, self.add_source, 
                                set_gid=set_gid)

    def check_event_from_handle(self, handle, transaction, set_gid=True):
        """
        Checks whether an Event with the passed handle exists in the database.
        If no such Event exists, a new Event is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self._check_from_handle(handle, transaction, Event, 
                                self.event_map, self.add_event, 
                                set_gid=set_gid)

    def check_object_from_handle(self, handle, transaction, set_gid=True):
        """
        Checks whether a MediaObject with the passed handle exists in
        the database. If no such MediaObject exists, a new Object is
        added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """

        self._check_from_handle(handle, transaction, MediaObject, 
                                self.media_map, self.add_object, 
                                set_gid=set_gid)

    def check_place_from_handle(self, handle, transaction, set_gid=True):
        """
        Checks whether a Place with the passed handle exists in the database.
        If no such Place exists, a new Place is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self._check_from_handle(handle, transaction, Place, 
                                self.place_map, self.add_place, 
                                set_gid=set_gid)

    def check_family_from_handle(self, handle, transaction, set_gid=True):
        """
        Checks whether a Family with the passed handle exists in the database.
        If no such Family exists, a new Family is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self._check_from_handle(handle, transaction, Family, 
                                self.family_map, self.add_family, 
                                set_gid=set_gid)

    def check_repository_from_handle(self, handle, transaction, set_gid=True):
        """
        Checks whether a Repository with the passed handle exists in the
        database. If no such Repository exists, a new Repository is added
        to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self._check_from_handle(handle, transaction, Repository, 
                                self.repository_map, self.add_repository, 
                                set_gid=set_gid)

    def get_person_from_gramps_id(self, val):
        """
        Finds a Person in the database from the passed GRAMPS ID.
        If no such Person exists, None is returned.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_family_from_gramps_id(self, val):
        """
        Finds a Family in the database from the passed GRAMPS ID.
        If no such Family exists, None is returned.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_event_from_gramps_id(self, val):
        """
        Finds an Event in the database from the passed GRAMPS ID.
        If no such Event exists, None is returned.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_place_from_gramps_id(self, val):
        """
        Finds a Place in the database from the passed gramps' ID.
        If no such Place exists, None is returned.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_source_from_gramps_id(self, val):
        """
        Finds a Source in the database from the passed gramps' ID.
        If no such Source exists, None is returned.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class" 

    def get_object_from_gramps_id(self, val):
        """
        Finds a MediaObject in the database from the passed gramps' ID.
        If no such MediaObject exists, None is returned.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_repository_from_gramps_id(self, val):
        """
        Finds a Repository in the database from the passed gramps' ID.
        If no such MediaObject exists, None is returned.

        Needs to be overridden by the derrived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def _add_object(self, obj, transaction, find_next_func, commit_func):
        if find_next_func and not obj.gramps_id:
            obj.gramps_id = find_next_func()
        if not obj.handle:
            obj.handle = self.create_id()
        commit_func(obj, transaction)
        if obj.__class__.__name__ == 'Person':
            self.genderStats.count_person (obj)
        return obj.handle

    def add_person(self, person, transaction, set_gid=True):
        """
        Adds a Person to the database, assigning internal IDs if they have
        not already been defined.
        If not set_gid, then gramps_id is not set
        """
        if set_gid:
            return self._add_object(person, transaction, 
                                    self.find_next_person_gramps_id, 
                                    self.commit_person)
        else:
            return self._add_object(person, transaction, 
                                    None, 
                                    self.commit_person)

    def add_family(self, family, transaction, set_gid=True):
        """
        Adds a Family to the database, assigning internal IDs if they have
        not already been defined.
        If not set_gid, then gramps_id is not set
        """
        if set_gid:
            return self._add_object(family, transaction, 
                                    self.find_next_family_gramps_id, 
                                    self.commit_family)
        else:
            return self._add_object(family, transaction, 
                                    None, 
                                    self.commit_family)

    def add_source(self, source, transaction, set_gid=True):
        """
        Adds a Source to the database, assigning internal IDs if they have
        not already been defined.
        If not set_gid, then gramps_id is not set
        """
        if set_gid:
            return self._add_object(source, transaction, 
                                    self.find_next_source_gramps_id, 
                                    self.commit_source)
        else :
            return self._add_object(source, transaction, 
                                None, 
                                self.commit_source)

    def add_event(self, event, transaction, set_gid=True):
        """
        Adds an Event to the database, assigning internal IDs if they have
        not already been defined.
        If not set_gid, then gramps_id is not set
        """
        if set_gid:
            return self._add_object(event, transaction, 
                                    self.find_next_event_gramps_id, 
                                    self.commit_event)
        else:
            return self._add_object(event, transaction, 
                                    None, 
                                    self.commit_event)

    def add_person_event(self, event, transaction):
        """
        Adds an Event to the database, assigning internal IDs if they have
        not already been defined.
        """
        if event.type.is_custom():
            self.individual_event_names.add(str(event.type))
        return self.add_event(event, transaction)

    def add_family_event(self, event, transaction):
        """
        Adds an Event to the database, assigning internal IDs if they have
        not already been defined.
        """
        if event.type.is_custom():
            self.family_event_names.add(str(event.type))
        return self.add_event(event, transaction)

    def add_place(self, place, transaction, set_gid=True):
        """
        Adds a Place to the database, assigning internal IDs if they have
        not already been defined.
        If not set_gid, then gramps_id is not set
        """
        if set_gid:
            return self._add_object(place, transaction, 
                                    self.find_next_place_gramps_id, 
                                    self.commit_place)
        else:
            return self._add_object(place, transaction, 
                                    None,
                                    self.commit_place)

    def add_object(self, obj, transaction, set_gid=True):
        """
        Adds a MediaObject to the database, assigning internal IDs if they have
        not already been defined.
        If not set_gid, then gramps_id is not set
        """
        if set_gid:
            return self._add_object(obj, transaction, 
                                    self.find_next_object_gramps_id, 
                                    self.commit_media_object)
        else:
            return self._add_object(obj, transaction, 
                                    None, 
                                    self.commit_media_object)

    def add_repository(self, obj, transaction, set_gid=True):
        """
        Adds a Repository to the database, assigning internal IDs if they have
        not already been defined.
        If not set_gid, then gramps_id is not set
        """
        if set_gid:
            return self._add_object(obj, transaction, 
                                    self.find_next_repository_gramps_id, 
                                    self.commit_repository)
        else:
            return self._add_object(obj, transaction, 
                                    None,
                                    self.commit_repository)

    def get_name_group_mapping(self, name):
        """
        Returns the default grouping name for a surname
        """
        return unicode(self.name_group.get(str(name), name))

    def get_name_group_keys(self):
        """
        Returns the defined names that have been assigned to a default grouping
        """
        return [unicode(k) for k in self.name_group.keys()]

    def has_name_group_key(self, name):
        """
        Return if a key exists in the name_group table
        """
        return self.name_group.has_key(str(name))

    def set_name_group_mapping(self, name, group):
        """
        Sets the default grouping name for a surname. Needs to be overridden
        in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_number_of_people(self):
        """
        Returns the number of people currently in the databse.
        """
        if self.db_is_open:
            return len(self.person_map)
        else:
            return 0

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

    def get_number_of_repositories(self):
        """
        Returns the number of source repositories currently in the databse.
        """
        return len(self.repository_map)

    def _all_handles(self, table):
        return table.keys()

    def get_person_handles(self, sort_handles=True):
        """
        Returns a list of database handles, one handle for each Person in
        the database. If sort_handles is True, the list is sorted by surnames
        """
        if self.db_is_open:
            if sort_handles:
                slist = []
                cursor = self.get_person_cursor()
                data = cursor.first()
                while data:
                    slist.append((data[1][3][3], data[0]))
                    data = cursor.next()
                cursor.close()
                slist.sort()
                return map(lambda x: x[1], slist)
            else:
                return self._all_handles(self.person_map)
        return []

    def get_place_handles(self, sort_handles=True):
        """
        Returns a list of database handles, one handle for each Place in
        the database. If sort_handles is True, the list is sorted by
        Place title.
        """
        if self.db_is_open:
            if sort_handles:
                slist = []
                cursor = self.get_place_cursor()
                data = cursor.first()
                while data:
                    slist.append((data[1][2], data[0]))
                    data = cursor.next()
                cursor.close()
                slist.sort()
                val = map(lambda x: x[1], slist)
                return val
            else:
                return self._all_handles(self.place_map)
        return []

    def get_source_handles(self, sort_handles=True):
        """
        Returns a list of database handles, one handle for each Source in
        the database. If sort_handles is True, the list is sorted by
        Source title.
        """
        if self.db_is_open:
            handle_list = self._all_handles(self.source_map)
            if sort_handles:
                handle_list.sort(self._sortbysource)
            return handle_list
        return []

    def get_media_object_handles(self, sort_handles=True):
        """
        Returns a list of database handles, one handle for each MediaObject in
        the database. If sort_handles is True, the list is sorted by title.
        """
        if self.db_is_open:
            handle_list = self._all_handles(self.media_map)
            if sort_handles:
                handle_list.sort(self._sortbymedia)
            return handle_list
        return []

    def get_event_handles(self):
        """
        Returns a list of database handles, one handle for each Event in
        the database. 
        """
        if self.db_is_open:
            return self._all_handles(self.event_map)
        return []

    def get_family_handles(self):
        """
        Returns a list of database handles, one handle for each Family in
        the database.
        """
        if self.db_is_open:
            return self._all_handles(self.family_map)
        return []

    def get_repository_handles(self):
        """
        Returns a list of database handles, one handle for each Repository in
        the database.
        """
        if self.db_is_open:
            return self._all_handles(self.repository_map)
        return []

    def get_gramps_ids(self, obj_key):
        key2table = {
            PERSON_KEY: self.id_trans, 
            FAMILY_KEY: self.fid_trans, 
            SOURCE_KEY: self.sid_trans, 
            EVENT_KEY:  self.eid_trans, 
            MEDIA_KEY:  self.oid_trans, 
            PLACE_KEY:  self.pid_trans, 
            REPOSITORY_KEY: self.rid_trans, 
            }

        table = key2table[obj_key]
        return table.keys()

    def has_gramps_id(self, obj_key, gramps_id):
        key2table = {
            PERSON_KEY: self.id_trans, 
            FAMILY_KEY: self.fid_trans, 
            SOURCE_KEY: self.sid_trans, 
            EVENT_KEY:  self.eid_trans, 
            MEDIA_KEY:  self.oid_trans, 
            PLACE_KEY:  self.pid_trans, 
            REPOSITORY_KEY: self.rid_trans, 
            }

        table = key2table[obj_key]
        return table.has_key(str(gramps_id))

    def find_initial_person(self):
        person = self.get_default_person()
        if not person:
            the_ids = self.get_gramps_ids(PERSON_KEY)
            if the_ids:
                person = self.get_person_from_gramps_id(min(the_ids))
        return person

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
    
    def set_person_id_prefix(self, val):
        """
        Sets the naming template for GRAMPS Person ID values. The string is
        expected to be in the form of a simple text string, or in a format
        that contains a C/Python style format string using %d, such as I%d
        or I%04d.
        """
        self.iprefix = self._validated_id_prefix(val, "I")
            
    def set_source_id_prefix(self, val):
        """
        Sets the naming template for GRAMPS Source ID values. The string is
        expected to be in the form of a simple text string, or in a format
        that contains a C/Python style format string using %d, such as S%d
        or S%04d.
        """
        self.sprefix = self._validated_id_prefix(val, "S")
            
    def set_object_id_prefix(self, val):
        """
        Sets the naming template for GRAMPS MediaObject ID values. The string
        is expected to be in the form of a simple text string, or in a format
        that contains a C/Python style format string using %d, such as O%d
        or O%04d.
        """
        self.oprefix = self._validated_id_prefix(val, "O")

    def set_place_id_prefix(self, val):
        """
        Sets the naming template for GRAMPS Place ID values. The string is
        expected to be in the form of a simple text string, or in a format
        that contains a C/Python style format string using %d, such as P%d
        or P%04d.
        """
        self.pprefix = self._validated_id_prefix(val, "P")

    def set_family_id_prefix(self, val):
        """
        Sets the naming template for GRAMPS Family ID values. The string is
        expected to be in the form of a simple text string, or in a format
        that contains a C/Python style format string using %d, such as F%d
        or F%04d.
        """
        self.fprefix = self._validated_id_prefix(val, "F")

    def set_event_id_prefix(self, val):
        """
        Sets the naming template for GRAMPS Event ID values. The string is
        expected to be in the form of a simple text string, or in a format
        that contains a C/Python style format string using %d, such as E%d
        or E%04d.
        """
        self.eprefix = self._validated_id_prefix(val, "E")

    def set_repository_id_prefix(self, val):
        """
        Sets the naming template for GRAMPS Repository ID values. The string is
        expected to be in the form of a simple text string, or in a format
        that contains a C/Python style format string using %d, such as R%d
        or R%04d.
        """
        self.rprefix = self._validated_id_prefix(val, "R")

    def transaction_begin(self, msg="",batch=False,no_magic=False):
        """
        Creates a new Transaction tied to the current UNDO database. The
        transaction has no effect until it is committed using the
        transaction_commit function of the this database object.
        """
        if self.__LOG_ALL:
            log.debug("%s: Transaction begin '%s'\n"
                      % (self.__class__.__name__, str(msg)))
        if batch:
            # A batch transaction does not store the commits
            # Aborting the session completely will become impossible.
            self.abort_possible = False
            self.undo_history_timestamp = time.time()
            # Undo is also impossible after batch transaction
            self.undoindex = -1
            self.translist  = [None] * _UNDO_SIZE
        return Transaction(msg, self.undodb, batch)

    def transaction_commit(self, transaction, msg):
        """
        Commits the transaction to the assocated UNDO database.
        """
        if self.__LOG_ALL:
            log.debug("%s: Transaction commit '%s'\n"
                      % (self.__class__.__name__, str(msg)))

        if not len(transaction) or self.readonly:
            return

        transaction.set_description(msg)
        transaction.timestamp = time.time()
        self.undoindex += 1                    
        if self.undoindex >= _UNDO_SIZE:
            # We overran the undo size.
            # Aborting the session completely will become impossible.
            self.abort_possible = False
            self.undo_history_timestamp = time.time()            
            self.translist = self.translist[0:-1] + [ transaction ]
        else:
            self.translist[self.undoindex] = transaction
            # Real commit erases all subsequent transactions
            # to there's no Redo anymore.
            for index in range(self.undoindex+1, _UNDO_SIZE):
                self.translist[index] = None

        person_add    = self._do_commit(transaction.person_add,self.person_map)
        family_add    = self._do_commit(transaction.family_add,self.family_map)
        source_add    = self._do_commit(transaction.source_add,self.source_map)
        place_add     = self._do_commit(transaction.place_add, self.place_map)
        media_add     = self._do_commit(transaction.media_add, self.media_map)
        event_add     = self._do_commit(transaction.event_add, self.event_map)
        repository_add= self._do_commit(transaction.repository_add, 
                                          self.repository_map)

        person_upd    = self._do_commit(transaction.person_update, 
                                        self.person_map)
        family_upd    = self._do_commit(transaction.family_update, 
                                        self.family_map)
        source_upd    = self._do_commit(transaction.source_update, 
                                        self.source_map)
        place_upd     = self._do_commit(transaction.place_update, 
                                          self.place_map)
        media_upd     = self._do_commit(transaction.media_update, 
                                        self.media_map)
        event_upd     = self._do_commit(transaction.event_update, 
                                        self.event_map)
        repository_upd= self._do_commit(transaction.repository_update, 
                                        self.repository_map)

        self._do_emit('person', person_add, person_upd, transaction.person_del)
        self._do_emit('family', family_add, family_upd, transaction.family_del)
        self._do_emit('event',  event_add,  event_upd,  transaction.event_del)
        self._do_emit('source', source_add, source_upd, transaction.source_del)
        self._do_emit('place',  place_add,  place_upd,  transaction.place_del)
        self._do_emit('media',  media_add,  media_upd,  transaction.media_del)
        self._do_emit('repository', repository_add, repository_upd, 
                      transaction.repository_del)

        self._do_del(transaction.person_del,     self._del_person)
        self._do_del(transaction.family_del,     self._del_family)
        self._do_del(transaction.place_del,      self._del_place)
        self._do_del(transaction.source_del,     self._del_source)
        self._do_del(transaction.event_del,      self._del_event)
        self._do_del(transaction.media_del,      self._del_media)
        self._do_del(transaction.repository_del, self._del_repository)

        if self.undo_callback:
            self.undo_callback(_("_Undo %s") % transaction.get_description())
        if self.redo_callback:
            self.redo_callback(None)
        if self.undo_history_callback:
            self.undo_history_callback()

    def _do_emit(self, objtype, add_list, upd_list, del_list):
        if add_list:
            self.emit(objtype + '-add', (add_list, ))
        if upd_list:
            self.emit(objtype + '-update', (upd_list, ))
        if del_list:
            self.emit(objtype + '-delete', (del_list, ))

    def _do_del(self, del_list, func):
        for handle in del_list:
            func(handle)
        return del_list

    def _do_commit(self, add_list, db_map):
        retlist = []
        for (handle, data) in add_list:
            db_map[handle] = data
            retlist.append(str(handle))
        return retlist

    def undo_available(self):
        # returns boolean of whether or not there's a possibility of undo
        if self.undoindex == -1 or self.readonly:
            return False

        return True
        
    def redo_available(self):
        # returns boolean of whether or not there's a possibility of redo
        if self.undoindex >= _UNDO_SIZE or self.readonly:
            return False

        if self.translist[self.undoindex+1] == None:
            return False

        return True
        
    def undo(self,update_history=True):
        """
        Accesses the last committed transaction, and reverts the data to
        the state before the transaction was committed.
        """
        if not self.undo_available():
            return False

        transaction = self.translist[self.undoindex]

        mapbase = (self.person_map, self.family_map, self.source_map, 
                   self.event_map, self.media_map, self.place_map,
                   self.repository_map)

        self.undoindex -= 1
        subitems = transaction.get_recnos()
        subitems.reverse()
        for record_id in subitems:
            (key,handle,old_data,new_data) = transaction.get_record(record_id)
            if key == REFERENCE_KEY:
                self.undo_reference(old_data, handle)
            else:
                self.undo_data(old_data, handle, mapbase[key], _sigbase[key])

        if self.undo_callback:
            if self.undo_available():
                new_transaction = self.translist[self.undoindex]
                self.undo_callback(_("_Undo %s")
                                   % new_transaction.get_description())
            else:
                self.undo_callback(None)

        if self.redo_callback:
            if self. redo_available():
                self.redo_callback(_("_Redo %s")
                                   % transaction.get_description())
            else:
                self.redo_callback(None)

        if update_history and self.undo_history_callback:
            self.undo_history_callback()
        return True

    def redo(self,update_history=True):
        """
        Accesses the last undone transaction, and reverts the data to
        the state before the transaction was undone.
        """

        if not self.redo_available():
            return False

        self.undoindex += 1
        transaction = self.translist[self.undoindex]
        mapbase = (self.person_map, self.family_map, self.source_map, 
                   self.event_map, self.media_map, self.place_map,
                   self.repository_map)

        subitems = transaction.get_recnos()
        for record_id in subitems:
            (key,handle,old_data,new_data) = transaction.get_record(record_id)
            if key == REFERENCE_KEY:
                self.undo_reference(new_data, handle)
            else:
                self.undo_data(new_data, handle, mapbase[key], _sigbase[key])

        if self.undo_callback:
            if self.undo_available():
                self.undo_callback(_("_Undo %s")
                                   % transaction.get_description())
            else:
                self.undo_callback(None)

        if self.redo_callback:
            if self.redo_available():
                new_transaction = self.translist[self.undoindex+1]
                self.redo_callback(_("_Redo %s")
                                   % new_transaction.get_description())
            else:
                self.redo_callback(None)

        if update_history and self.undo_history_callback:
            self.undo_history_callback()
        return True

    def undo_reference(self, data, handle):
        pass

    def undo_data(self, data, handle, db_map, signal_root):
        if data == None:
            self.emit(signal_root + '-delete', ([handle], ))
            del db_map[handle]
        else:
            if db_map.has_key(handle):
                signal = signal_root + '-update'
            else:
                signal = signal_root + '-add'
            db_map[handle] = data
            self.emit(signal, ([handle], ))
    
    def set_undo_callback(self, callback):
        """
        Defines the callback function that is called whenever an undo operation
        is executed. The callback function recieves a single argument that is a
        text string that defines the operation.
        """
        self.undo_callback = callback

    def set_redo_callback(self, callback):
        """
        Defines the callback function that is called whenever an redo operation
        is executed. The callback function recieves a single argument that is a
        text string that defines the operation.
        """
        self.redo_callback = callback

    def get_surname_list(self):
        """
        Returns the list of locale-sorted surnames contained in the database.
        """
        return self.surname_list

    def build_surname_list(self):
        """
        Builds the list of locale-sorted surnames contained in the database.
        The function must be overridden in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def sort_surname_list(self):
        vals = [(locale.strxfrm(item),item) for item in self.surname_list]
        vals.sort()
        self.surname_list = [item[1] for item in vals]

    def add_to_surname_list(self,person,batch_transaction):
        if batch_transaction:
            return
        name = unicode(person.get_primary_name().get_surname())
        if name not in self.surname_list:
            self.surname_list.append(name)
            self.sort_surname_list()

    def remove_from_surname_list(self,person):
        """
        Check whether there are persons with the same surname left in
        the database. If not then we need to remove the name from the list.
        The function must be overridden in the derived class.
        """
        assert False, "Needs to be overridden in the derived class"

    def get_bookmarks(self):
        """returns the list of Person handles in the bookmarks"""
        return self.bookmarks

    def get_family_bookmarks(self):
        """returns the list of Person handles in the bookmarks"""
        return self.family_bookmarks

    def get_event_bookmarks(self):
        """returns the list of Person handles in the bookmarks"""
        return self.event_bookmarks

    def get_place_bookmarks(self):
        """returns the list of Person handles in the bookmarks"""
        return self.place_bookmarks

    def get_source_bookmarks(self):
        """returns the list of Person handles in the bookmarks"""
        return self.source_bookmarks

    def get_media_bookmarks(self):
        """returns the list of Person handles in the bookmarks"""
        return self.media_bookmarks

    def get_repo_bookmarks(self):
        """returns the list of Person handles in the bookmarks"""
        return self.repo_bookmarks

    def set_researcher(self, owner):
        """sets the information about the owner of the database"""
        self.owner.set(owner.get_name(), owner.get_address(), 
                       owner.get_city(), owner.get_state(), 
                       owner.get_country(), owner.get_postal_code(), 
                       owner.get_phone(), owner.get_email())

    def get_researcher(self):
        """returns the Researcher instance, providing information about
        the owner of the database"""
        return self.owner

    def set_default_person_handle(self, handle):
        """sets the default Person to the passed instance"""
        if (self.metadata != None) and (not self.readonly):
            self.metadata['default'] = str(handle)

    def get_default_person(self):
        """returns the default Person of the database"""
        person = self.get_person_from_handle(self.get_default_handle())
        if person:
            return person
        elif (self.metadata != None) and (not self.readonly):
            self.metadata['default'] = None
        return None

    def get_default_handle(self):
        """returns the default Person of the database"""
        if self.metadata != None:
            return self.metadata.get('default')
        return None

    def get_save_path(self):
        """returns the save path of the file, or "" if one does not exist"""
        return self.path

    def set_save_path(self, path):
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

    def get_marker_types(self):
        """return a list of all marker types available in the database"""
        return list(self.marker_names)
        
    def get_media_attribute_types(self):
        """returns a list of all Attribute types assocated with Media
        and MediaRef instances in the database"""
        return list(self.media_attributes)

    def get_family_relation_types(self):
        """returns a list of all relationship types assocated with Family
        instances in the database"""
        return list(self.family_rel_types)

    def get_child_reference_types(self):
        """returns a list of all child reference types assocated with Family
        instances in the database"""
        return list(self.child_ref_types)

    def get_event_roles(self):
        """returns a list of all custom event role names assocated with Event
        instances in the database"""
        return list(self.event_role_names)

    def get_name_types(self):
        """returns a list of all custom names types assocated with Person
        instances in the database"""
        return list(self.name_types)

    def get_repository_types(self):
        """returns a list of all custom repository types assocated with
        Repository instances in the database"""
        return list(self.repository_types)

    def get_source_media_types(self):
        """returns a list of all custom source media types assocated with
        Source instances in the database"""
        return list(self.source_media_types)

    def get_url_types(self):
        """returns a list of all custom names types assocated with Url
        instances in the database"""
        return list(self.url_types)

    def remove_person(self, handle, transaction):
        """
        Removes the Person specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """

        if self.readonly or not handle:
            return
        self._delete_primary_from_reference_map(handle, transaction)
        person = self.get_person_from_handle(handle)
        self.genderStats.uncount_person (person)
        self.remove_from_surname_list(person)
        if transaction.batch:
            self._del_person(handle)
        else:
            transaction.add(PERSON_KEY, handle, person.serialize(), None)
            transaction.person_del.append(str(handle))

    def get_del_func(self,key):
        key2del = {
            PERSON_KEY: self._del_person,
            FAMILY_KEY: self._del_family,
            SOURCE_KEY: self._del_source,
            EVENT_KEY:  self._del_event,
            MEDIA_KEY:  self._del_media,
            PLACE_KEY:  self._del_place,
            REPOSITORY_KEY: self._del_repository,
            }
        return key2del[key]

    def _do_remove_object(self, handle, trans, dmap, key, del_list):
        if self.readonly or not handle:
            return

        handle = str(handle)
        self._delete_primary_from_reference_map(handle, trans)
        if trans.batch:
            del_func = self.get_del_func(key)
            del_func(handle)
        else:
            old_data = dmap.get(handle)
            trans.add(key, handle, old_data, None)
            del_list.append(handle)

    def remove_source(self, handle, transaction):
        """
        Removes the Source specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        self._do_remove_object(handle, transaction, self.source_map, 
                               SOURCE_KEY, transaction.source_del)

    def remove_event(self, handle, transaction):
        """
        Removes the Event specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        self._do_remove_object(handle, transaction, self.event_map, 
                               EVENT_KEY, transaction.event_del)

    def remove_object(self, handle, transaction):
        """
        Removes the MediaObjectPerson specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        self._do_remove_object(handle, transaction, self.media_map, 
                               MEDIA_KEY, transaction.media_del)

    def remove_place(self, handle, transaction):
        """
        Removes the Place specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        self._do_remove_object(handle, transaction, self.place_map, 
                               PLACE_KEY, transaction.place_del)

    def remove_family(self, handle, transaction):
        """
        Removes the Family specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        self._do_remove_object(handle, transaction, self.family_map, 
                               FAMILY_KEY, transaction.family_del)

    def remove_repository(self, handle, transaction):
        """
        Removes the Repository specified by the database handle from the
        database, preserving the change in the passed transaction. This
        method must be overridden in the derived class.
        """
        self._do_remove_object(handle, transaction, self.repository_map, 
                               REPOSITORY_KEY, transaction.repository_del)

    def get_raw_person_data(self, handle):
        return self.person_map.get(str(handle))

    def get_raw_family_data(self, handle):
        return self.family_map.get(str(handle))

    def get_raw_object_data(self, handle):
        return self.media_map.get(str(handle))

    def get_raw_place_data(self, handle):
        return self.place_map.get(str(handle))

    def get_raw_event_data(self, handle):
        return self.event_map.get(str(handle))

    def get_raw_source_data(self, handle):
        return self.source_map.get(str(handle))

    def get_raw_repository_data(self, handle):
        return self.repository_map.get(str(handle))

    def has_person_handle(self, handle):
        """
        returns True if the handle exists in the current Person database.
        """
        return self.person_map.has_key(str(handle))

    def has_event_handle(self, handle):
        """
        returns True if the handle exists in the current Event database.
        """
        return self.event_map.has_key(str(handle))

    def has_source_handle(self, handle):
        """
        returns True if the handle exists in the current Source database.
        """
        return self.source_map.has_key(str(handle))

    def has_place_handle(self, handle):
        """
        returns True if the handle exists in the current Place database.
        """
        return self.place_map.has_key(str(handle))

    def has_family_handle(self, handle):            
        """
        returns True if the handle exists in the current Family database.
        """
        return self.family_map.has_key(str(handle))

    def has_object_handle(self, handle):
        """
        returns True if the handle exists in the current MediaObjectdatabase.
        """
        return self.media_map.has_key(str(handle))

    def has_repository_handle(self, handle):
        """
        returns True if the handle exists in the current Repository database.
        """
        return self.repository_map.has_key(str(handle))

    def _sortbyplace(self, first, second):
        return locale.strcoll(self.place_map.get(str(first))[2], 
                              self.place_map.get(str(second))[2])

    def _sortbysource(self, first, second):
        source1 = unicode(self.source_map[str(first)][2])
        source2 = unicode(self.source_map[str(second)][2])
        return locale.strcoll(source1, source2)

    def _sortbymedia(self, first, second):
        media1 = self.media_map[str(first)][4]
        media2 = self.media_map[str(second)][4]
        return locale.strcoll(media1, media2)

    def _set_column_order(self, col_list, name):
        if (self.metadata != None) and (not self.readonly):
            self.metadata[name] = col_list

    def set_person_column_order(self, col_list):
        """
        Stores the Person display common information in the
        database's metadata.
        """
        self._set_column_order(col_list, PERSON_COL_KEY)

    def set_family_list_column_order(self, col_list):
        """
        Stores the Person display common information in the
        database's metadata.
        """
        self._set_column_order(col_list, FAMILY_COL_KEY)

    def set_child_column_order(self, col_list):
        """
        Stores the Person display common information in the
        database's metadata.
        """
        self._set_column_order(col_list, CHILD_COL_KEY)

    def set_place_column_order(self, col_list):
        """
        Stores the Place display common information in the
        database's metadata.
        """
        self._set_column_order(col_list, PLACE_COL_KEY)

    def set_source_column_order(self, col_list):
        """
        Stores the Source display common information in the
        database's metadata.
        """
        self._set_column_order(col_list, SOURCE_COL_KEY)

    def set_media_column_order(self, col_list):
        """
        Stores the Media display common information in the
        database's metadata.
        """
        self._set_column_order(col_list, MEDIA_COL_KEY)

    def set_event_column_order(self, col_list):
        """
        Stores the Event display common information in the
        database's metadata.
        """
        self._set_column_order(col_list, EVENT_COL_KEY)

    def set_repository_column_order(self, col_list):
        """
        Stores the Repository display common information in the
        database's metadata.
        """
        self._set_column_order(col_list, REPOSITORY_COL_KEY)

    def _get_column_order(self, name, default):
        if self.metadata == None:
            return default
        else:
            cols = self.metadata.get(name, default)
            if len(cols) != len(default):
                return cols + default[len(cols):]
            else:
                return cols

    def get_person_column_order(self):
        """
        Returns the Person display common information stored in the
        database's metadata.
        """
        default = [(1, 1, 100), (1, 2, 100), (1, 3, 150), (0, 4, 150),
                   (1, 5, 150), (0, 6, 150), (0, 7, 100), (0, 8, 100),
                   ]
        return self._get_column_order(PERSON_COL_KEY, default)

    def _get_columns(self, key, default):
        values = self._get_column_order(key, default)
        new = []
        for val in values:
            if len(val) == 2:
                for x in default:
                    if val[1] == x[1]:
                        new.append((val[0], val[1], x[2]))
                        break
            else:
                new.append(val)
        return new
        
    def get_family_list_column_order(self):
        """
        Returns the Person display common information stored in the
        database's metadata.
        """
        default = [(1, 0, 75), (1, 1, 200), (1, 2, 200), (1, 3, 100),
                   (0, 4, 100)]
        return self._get_columns(FAMILY_COL_KEY, default)

    def get_child_column_order(self):
        """
        Returns the Person display common information stored in the
        database's metadata.
        """
        default = [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
                   (0, 6), (0, 7)]
        return self._get_column_order(CHILD_COL_KEY, default)

    def get_place_column_order(self):
        """
        Returns the Place display common information stored in the
        database's metadata.
        """
        default = [(1, 0, 250), (1, 1, 75), (1, 11, 100), (0, 3, 100),
                   (1, 4, 100, ), (0, 5, 150), (1, 6, 150), (0, 7, 150),
                   (0, 8, 150), (0, 9, 150), (0, 10, 150),(0,2,100)]
        return self._get_columns(PLACE_COL_KEY, default)

    def get_source_column_order(self):
        """
        Returns the Source display common information stored in the
        database's metadata.
        """
        default = [(1, 0, 200), (1, 1, 75), (1, 2, 150), (0, 3, 100),
                   (1, 4, 150), (0, 5, 100)]
        return self._get_columns(SOURCE_COL_KEY, default)

    def get_media_column_order(self):
        """
        Returns the MediaObject display common information stored in the
        database's metadata.
        """
        default = [(1, 0, 200, ), (1, 1, 75), (1, 2, 100), (1, 3, 200),
                   (1, 5, 150), (0, 4, 150)]
        return self._get_columns(MEDIA_COL_KEY, default)

    def get_event_column_order(self):
        """
        Returns the Event display common information stored in the
        database's metadata.
        """
        default = [(1, 0, 200), (1, 1, 75), (1, 2, 100), (1, 3, 150),
                   (1, 4, 200), (0, 5, 100)]
        return self._get_columns(EVENT_COL_KEY, default)

    def get_repository_column_order(self):
        """
        Returns the Repository display common information stored in the
        database's metadata.
        """
        default = [(1, 0, 200), (1, 1, 75), (0, 5, 100), (0, 6, 100),
                   (1, 2, 100), (1, 3, 250), (1, 4, 100), (0, 7, 100),
                   (0, 8, 100), (0, 9, 100), (0, 10, 100)]
        return self._get_columns(REPOSITORY_COL_KEY, default)

    def _delete_primary_from_reference_map(self, handle, transaction):
        """Called each time an object is removed from the database. This can
        be used by subclasses to update any additional index tables that might
        need to be changed."""
        pass

    def _update_reference_map(self, obj, transaction):
        """Called each time an object is writen to the database. This can
        be used by subclasses to update any additional index tables that might
        need to be changed."""
        pass

    def reindex_reference_map(self,callback):
        """
        Reindex all primary records in the database.

        """
        pass

    def find_backlink_handles(self, handle, include_classes=None):
        """
        Find all objects that hold a reference to the object handle.
        Returns an interator over alist of (class_name, handle) tuples.

        @param handle: handle of the object to search for.
        @type handle: database handle
        @param include_classes: list of class names to include in the results.
                                Default: None means include all classes.
        @type include_classes: list of class names
        
        This default implementation does a sequencial scan through all
        the primary object databases and is very slow. Backends can
        override this method to provide much faster implementations that
        make use of additional capabilities of the backend.

        Note that this is a generator function, it returns a iterator for
        use in loops. If you want a list of the results use:

        >    result_list = [i for i in find_backlink_handles(handle)]
        """

        # Make a dictionary of the functions and classes that we need for
        # each of the primary object tables.
        primary_tables = {
            'Person': {'cursor_func': self.get_person_cursor, 
                       'class_func': Person}, 
            'Family': {'cursor_func': self.get_family_cursor, 
                       'class_func': Family}, 
            'Event': {'cursor_func': self.get_event_cursor, 
                      'class_func': Event}, 
            'Place': {'cursor_func': self.get_place_cursor, 
                      'class_func': Place}, 
            'Source': {'cursor_func': self.get_source_cursor, 
                       'class_func': Source}, 
            'MediaObject': {'cursor_func': self.get_media_cursor, 
                            'class_func': MediaObject}, 
            'Repository': {'cursor_func': self.get_repository_cursor, 
                           'class_func': Repository}, 
            }


        # Find which tables to iterate over
        if (include_classes == None):
            the_tables = primary_tables.keys()
        else:
            the_tables = include_classes
        
        # Now we use the functions and classes defined above to loop through
        # each of the existing primary object tables
        for primary_table_name in the_tables:
            cursor = primary_tables[primary_table_name]['cursor_func']()
            data = cursor.first()

            # Grab the real object class here so that the lookup does
            # not happen inside the main loop.
            class_func = primary_tables[primary_table_name]['class_func']

            while data:
                found_handle, val = data
                obj = class_func()
                obj.unserialize(val)

                # Now we need to loop over all object types
                # that have been requests in the include_classes list
                for classname in primary_tables.keys():               
                    if obj.has_handle_reference(classname,handle):
                        yield (primary_table_name, found_handle)
                        
                data = cursor.next()
                    
            cursor.close()

        return

    def report_bm_change(self):
        self._bm_changes += 1;

    def db_has_bm_changes(self):
        return self._bm_changes > 0

        
class Transaction:
    """
    Defines a group of database commits that define a single logical
    operation.
    """
    def __init__(self, msg, db, batch=False, no_magic=False):
        """
        Creates a new transaction. A Transaction instance should not be
        created directly, but by the GrampsDbBase class or classes derived
        from GrampsDbBase. The db parameter is a list-like interface that
        stores the commit data. This could be a simple list, or a RECNO-style
        database object.

        The batch parameter is set to True for large transactions. For such
        transactions, the list of changes is not maintained, and no undo
        is possible.

        The no_magic parameter is ignored for non-batch transactions, and
        is also of no importance for DB backends other than BSD DB. For
        the BSDDB, when this paramter is set to True, some secondary
        indices will be removed at the beginning and then rebuilt at
        the end of such transaction (only if it is batch).
        """
        self.db = db
        self.first = None
        self.last = None
        self.batch = batch
        self.no_magic = no_magic
        self.length = 0
        self.timestamp = 0

        self.person_add = []
        self.person_del = []
        self.person_update = []

        self.family_add = []
        self.family_del = []
        self.family_update = []

        self.source_add = []
        self.source_del = []
        self.source_update = []

        self.event_add = []
        self.event_del = []
        self.event_update = []

        self.media_add = []
        self.media_del = []
        self.media_update = []

        self.place_add = []
        self.place_del = []
        self.place_update = []

        self.repository_add = []
        self.repository_del = []
        self.repository_update = []

##     def set_batch(self, batch):
##         self.batch = batch

    def get_batch(self):
        return self.batch
    
    def get_description(self):
        """
        Returns the text string that describes the logical operation
        performed by the Transaction.
        """
        return self.msg

    def set_description(self, msg):
        """
        Sets the text string that describes the logical operation
        performed by the Transaction.
        """
        self.msg = msg

    def add(self, obj_type, handle, old_data, new_data):
        """
        Adds a commit operation to the Transaction. The obj_type is a constant
        that indicates what type of PrimaryObject is being added. The handle
        is the object's database handle, and the data is the tuple returned
        by the object's serialize method.
        """
        self.last = self.db.append(cPickle.dumps((obj_type, 
                                                  handle, 
                                                  old_data, 
                                                  new_data), 
                                                 1)
                                   )
        if self.first == None:
            self.first = self.last

    def get_recnos(self):
        """
        Returns a list of record numbers associated with the transaction.
        While the list is an arbitrary index of integers, it can be used
        to indicate record numbers for a database.
        """
        return range (self.first, self.last+1)

    def get_record(self, recno):
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

class DbState(GrampsDBCallback):

    __signals__ = {
        'database-changed' : (GrampsDbBase, ), 
        'active-changed'   : (str, ), 
        'no-database'      :  None, 
        }

    def __init__(self):
        GrampsDBCallback.__init__(self)
        self.db     = GrampsDbBase()
        self.open   = False
        self.active = None

    def change_active_person(self, person):
        self.active = person
        if person:
            try:
                self.emit('active-changed', (person.handle, ))
            except:
                self.emit('active-changed', ("", ))

    def change_active_handle(self, handle):
        self.change_active_person(self.db.get_person_from_handle(handle))

    def get_active_person(self):
        if self.active: # Fetch a fresh version from DB to not return a stale one
            self.active = self.db.get_person_from_handle(self.active.handle)
        return self.active

    def change_database(self, database):
        self.db.close()
        self.change_database_noclose(database)

    def change_database_noclose(self, database):
        self.db = database
        self.active = None
        self.open = True

    def signal_change(self):
        self.emit('database-changed', (self.db, ))

    def no_database(self):
        self.db.close()
        self.db = GrampsDbBase()
        self.active = None
        self.open = False
        self.emit('no-database')
