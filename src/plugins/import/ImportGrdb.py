#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2005-2007  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
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

# Written by Alex Roitman, 
# largely based on ReadXML by Don Allingham

#-------------------------------------------------------------------------
#
# Standard Python Modules
#
#-------------------------------------------------------------------------
from __future__ import with_statement
import os
import shutil
import tempfile
from gen.ggettext import gettext as _
import cPickle as pickle
import time
from bsddb import dbshelve, db
import logging
LOG = logging.getLogger(".Db")

#-------------------------------------------------------------------------
#
# Gramps Modules
#
#-------------------------------------------------------------------------
from gen.lib import (GenderStats, Source, Person, Family, Event, Place, 
                     MediaObject, Repository, Note, Attribute, AttributeType, 
                     NoteType)
from gen.db.write import (KEY_TO_CLASS_MAP, CLASS_TO_KEY_MAP)
from libgrdb import DbGrdb
from gen.db.txn import DbTxn as Transaction
from gen.db.cursor import BsddbBaseCursor
from gen.db.dbconst import *
from gen.db.exceptions import DbVersionError
import const
from QuestionDialog import ErrorDialog
from Errors import HandleError
from gen.updatecallback import UpdateCallback
from gen.display.name import displayer as name_displayer

#-------------------------------------------------------------------------
#
# Constants 
#
#-------------------------------------------------------------------------
_MINVERSION = 9
_DBVERSION = 14

#--------------------------------------------------------------------------
#
# Secondary index functions
#
#--------------------------------------------------------------------------
def find_surname(key, data):
    """
    Return the surname from the data stream. Used for building a secondary 
    index.
    """
    return str(data[3][5])

def find_idmap(key, data):
    """
    Return the ID from the data stream. Used for building a secondary 
    index.
    """
    return str(data[1])

def find_primary_handle(key, data):
    """
    Secondary database key lookups for reference_map table
    reference_map data values are of the form:
       ((primary_object_class_name, primary_object_handle),
       (referenced_object_class_name, referenced_object_handle))
    """
    return str((data)[0][1])

def find_referenced_handle(key, data):
    """
    Secondary database key lookups for reference_map table
    reference_map data values are of the form:
       ((primary_object_class_name, primary_object_handle),
       (referenced_object_class_name, referenced_object_handle))
    """
    return str((data)[1][1])

class GrampsBSDDBCursor(BsddbBaseCursor):
    """
    Cursor to loop through a BSDDB table
    """
    def __init__(self, source, txn=None):
        self.cursor = source.db.cursor(txn)
        self.source = source
        
class GrampsBSDDBAssocCursor(BsddbBaseCursor):

    def __init__(self, source, txn=None):
        self.cursor = source.cursor(txn)
        self.source = source
        
class GrampsBSDDBDupCursor(GrampsBSDDBAssocCursor):
    """Cursor that includes handling for duplicate keys"""

    def set(self, key):
        return self.cursor.set(str(key))

    def next_dup(self):
        return self.cursor.next_dup()

#-------------------------------------------------------------------------
#
# GrampsBSDDB
#
#-------------------------------------------------------------------------
class GrampsBSDDB(DbGrdb, UpdateCallback):
    """ GRAMPS database object for Berkeley DB. 
        This is replaced for internal use by gen/db/dbdir.py
        However, this class is still used for import of the 2.2.x 
        GRDB format. In 3.0+ this format is no longer used.
    """

    def __init__(self, use_txn = True):
        """creates a new GrampsDB"""
        
        DbGrdb.__init__(self)
        #UpdateCallback.__init__(self)
        self.txn = None
        self.secondary_connected = False
        self.UseTXN = use_txn

    def __open_flags(self):
        if self.UseTXN:
            return db.DB_CREATE|db.DB_AUTO_COMMIT
        else:
            return db.DB_CREATE

    def __open_table(self, file_name, table_name, dbtype=db.DB_HASH):
        dbmap = dbshelve.DBShelf(self.env)
        dbmap.db.set_pagesize(16384)
        if self.readonly:
            dbmap.open(file_name, table_name, dbtype, db.DB_RDONLY)
        else:
            dbmap.open(file_name, table_name, dbtype, self.__open_flags(), 0666)
        return dbmap

    def all_handles(self, table):
        return table.keys(self.txn)
    
    def get_person_cursor(self):
        return GrampsBSDDBCursor(self.person_map, self.txn)

    def get_family_cursor(self):
        return GrampsBSDDBCursor(self.family_map, self.txn)

    def get_event_cursor(self):
        return GrampsBSDDBCursor(self.event_map, self.txn)

    def get_place_cursor(self):
        return GrampsBSDDBCursor(self.place_map, self.txn)

    def get_source_cursor(self):
        return GrampsBSDDBCursor(self.source_map, self.txn)

    def get_media_cursor(self):
        return GrampsBSDDBCursor(self.media_map, self.txn)

    def get_repository_cursor(self):
        return GrampsBSDDBCursor(self.repository_map, self.txn)

    def get_note_cursor(self):
        return GrampsBSDDBCursor(self.note_map, self.txn)

    def has_person_handle(self, handle):
        """
        returns True if the handle exists in the current Person database.
        """
        return self.person_map.get(str(handle), txn=self.txn) is not None

    def has_family_handle(self, handle):            
        """
        returns True if the handle exists in the current Family database.
        """
        return self.family_map.get(str(handle), txn=self.txn) is not None

    def has_object_handle(self, handle):
        """
        returns True if the handle exists in the current MediaObjectdatabase.
        """
        return self.media_map.get(str(handle), txn=self.txn) is not None

    def has_repository_handle(self, handle):
        """
        returns True if the handle exists in the current Repository database.
        """
        return self.repository_map.get(str(handle), txn=self.txn) is not None

    def has_note_handle(self, handle):
        """
        returns True if the handle exists in the current Note database.
        """
        return self.note_map.get(str(handle), txn=self.txn) is not None

    def has_event_handle(self, handle):
        """
        returns True if the handle exists in the current Repository database.
        """
        return self.event_map.get(str(handle), txn=self.txn) is not None

    def has_place_handle(self, handle):
        """
        returns True if the handle exists in the current Repository database.
        """
        return self.place_map.get(str(handle), txn=self.txn) is not None

    def has_source_handle(self, handle):
        """
        returns True if the handle exists in the current Repository database.
        """
        return self.source_map.get(str(handle), txn=self.txn) is not None

    def get_raw_person_data(self, handle):
        """
        returns the raw, unserialized data for a person
        """
        return self.person_map.get(str(handle), txn=self.txn)

    def get_raw_family_data(self, handle):
        """
        returns the raw, unserialized data for a family
        """
        return self.family_map.get(str(handle), txn=self.txn)

    def get_raw_object_data(self, handle):
        """
        returns the raw, unserialized data for a media object
        """
        return self.media_map.get(str(handle), txn=self.txn)

    def get_raw_place_data(self, handle):
        """
        returns the raw, unserialized data for a place
        """
        return self.place_map.get(str(handle), txn=self.txn)

    def get_raw_event_data(self, handle):
        """
        returns the raw, unserialized data for an event
        """
        return self.event_map.get(str(handle), txn=self.txn)

    def get_raw_source_data(self, handle):
        """
        returns the raw, unserialized data for a source
        """
        return self.source_map.get(str(handle), txn=self.txn)

    def get_raw_repository_data(self, handle):
        """
        returns the raw, unserialized data for a repository
        """
        return self.repository_map.get(str(handle), txn=self.txn)

    def get_raw_note_data(self, handle):
        """
        returns the raw, unserialized data for a note
        """
        return self.note_map.get(str(handle), txn=self.txn)

    # cursors for lookups in the reference_map for back reference
    # lookups. The reference_map has three indexes:
    # the main index: a tuple of (primary_handle, referenced_handle)
    # the primary_handle index: the primary_handle
    # the referenced_handle index: the referenced_handle
    # the main index is unique, the others allow duplicate entries.

    def get_reference_map_cursor(self):
        return GrampsBSDDBAssocCursor(self.reference_map, self.txn)

    def get_reference_map_primary_cursor(self):
        return GrampsBSDDBDupCursor(self.reference_map_primary_map, self.txn)

    def get_reference_map_referenced_cursor(self):
        return GrampsBSDDBDupCursor(self.reference_map_referenced_map, self.txn)

    # These are overriding the DbBase's methods of saving metadata
    # because we now have txn-capable metadata table
    def set_default_person_handle(self, handle):
        """sets the default Person to the passed instance"""
        if not self.readonly:
            if self.UseTXN:
                # Start transaction if needed
                the_txn = self.env.txn_begin()
            else:
                the_txn = None
            self.metadata.put('default', str(handle), txn=the_txn)
            if self.UseTXN:
                the_txn.commit()
            else:
                self.metadata.sync()

    def get_default_person(self):
        """returns the default Person of the database"""
        person = self.get_person_from_handle(self.get_default_handle())
        if person:
            return person
        elif (self.metadata) and (not self.readonly):
            if self.UseTXN:
                # Start transaction if needed
                the_txn = self.env.txn_begin()
            else:
                the_txn = None
            self.metadata.put('default', None, txn=the_txn)
            if self.UseTXN:
                the_txn.commit()
            else:
                self.metadata.sync()
        return None

    def version_supported(self):
        dbversion = self.metadata.get('version',default=_DBVERSION)
        return ((dbversion <= _DBVERSION) and (dbversion >= _MINVERSION))
    
    def need_upgrade(self):
        dbversion = self.metadata.get('version', default=0)
        return not self.readonly and dbversion < _DBVERSION

    def load(self, name, callback, mode="w"):
        if self.db_is_open:
            self.close()

        self.readonly = mode == "r"
        if self.readonly:
            self.UseTXN = False

        if callback:
            callback(12)

        self.full_name = os.path.abspath(name)
        self.brief_name = os.path.basename(name)

        self.env = db.DBEnv()
        self.env.set_cachesize(0, 0x4000000)         # 32MB

        if self.UseTXN:
            # These env settings are only needed for Txn environment
            self.env.set_lk_max_locks(25000)
            self.env.set_lk_max_objects(25000)
            
            self.set_auto_remove()

            # The DB_PRIVATE flag must go if we ever move to multi-user setup
            env_flags = db.DB_CREATE | db.DB_PRIVATE | \
                        db.DB_INIT_MPOOL | db.DB_INIT_LOCK | \
                        db.DB_INIT_LOG | db.DB_INIT_TXN | db.DB_THREAD
            # Only do recovery for existing databases
            if os.path.isfile(self.full_name):
                env_flags = env_flags | db.DB_RECOVER
        else:
            env_flags = db.DB_CREATE | db.DB_PRIVATE | db.DB_INIT_MPOOL

        env_name = self.make_env_name(self.full_name)
        self.env.open(env_name, env_flags)
        if self.UseTXN:
            self.env.txn_checkpoint()

        if callback:
            callback(25)
        self.metadata     = self.__open_table(self.full_name, "meta")

        # If we cannot work with this DB version,
        # it makes no sense to go further
        if not self.version_supported():
            self.__close_early()

        self.family_map     = self.__open_table(self.full_name, "family")
        self.place_map      = self.__open_table(self.full_name, "places")
        self.source_map     = self.__open_table(self.full_name, "sources")
        self.media_map      = self.__open_table(self.full_name, "media")
        self.event_map      = self.__open_table(self.full_name, "events")
        self.person_map     = self.__open_table(self.full_name, "person")
        self.repository_map = self.__open_table(self.full_name, "repository")
        self.note_map       = self.__open_table(self.full_name, "note")
        self.reference_map  = self.__open_table(self.full_name, "reference_map",
                                                dbtype=db.DB_BTREE)

        self.name_group = db.DB(self.env)
        self.name_group.set_flags(db.DB_DUP)
        if self.readonly:
            self.name_group.open(self.full_name, "name_group",
                             db.DB_HASH, flags=db.DB_RDONLY)
        else:
            self.name_group.open(self.full_name, "name_group",
                             db.DB_HASH, flags=self.__open_flags())

        self.__load_metadata()

        gstats = self.metadata.get('gender_stats', default=None)

        if not self.readonly:
            if self.UseTXN:
                # Start transaction if needed
                the_txn = self.env.txn_begin()
            else:
                the_txn = None

            if gstats is None:
                # New database. Set up the current version.
                self.metadata.put('version', _DBVERSION, txn=the_txn)
            elif 'version' not in self.metadata:
                # Not new database, but the version is missing.
                # Use 0, but it is likely to fail anyway.
                self.metadata.put('version', 0, txn=the_txn)

            if self.UseTXN:
                the_txn.commit()
            else:
                self.metadata.sync()
            
        self.genderStats = GenderStats(gstats)

        # Here we take care of any changes in the tables related to new code.
        # If secondary indices change, then they should removed
        # or rebuilt by upgrade as well. In any case, the
        # self.secondary_connected flag should be set accordingly.
        if self.need_upgrade():
            self.gramps_upgrade(callback)

        if not self.secondary_connected:
            self.connect_secondary()

        self.open_undodb()
        self.db_is_open = True

        # Re-set the undo history to a fresh session start
        #self.undoindex = -1
        #self.translist = [None] * len(self.translist)
        self.abort_possible = True
        #self.undo_history_timestamp = time.time()

        return 1

    def make_env_name(self, full_name):
        if self.UseTXN:
            # Environment name is now based on the filename
            drive, tmp_name = os.path.splitdrive(full_name)
            tmp_name = tmp_name.lstrip(os.sep)
            env_name = os.path.join(os.path.expanduser(const.ENV_DIR),tmp_name)
        else:
            env_name = os.path.expanduser('~')
        return env_name

    def __load_metadata(self):
        # name display formats
        self.name_formats = self.metadata.get('name_formats', default=[])
        # upgrade formats if they were saved in the old way
        for format_ix in range(len(self.name_formats)):
            format = self.name_formats[format_ix]
            if len(format) == 3:
                format = format + (True, )
                self.name_formats[format_ix] = format
        
        # database owner
        self.set_researcher(self.metadata.get('researcher', default=self.owner))
        
        # bookmarks
        self.bookmarks.set(self.metadata.get('bookmarks', default=[]))
        self.family_bookmarks.set(self.metadata.get('family_bookmarks',
                                                    default=[]))
        self.event_bookmarks.set(self.metadata.get('event_bookmarks',
                                                   default=[]))
        self.source_bookmarks.set(self.metadata.get('source_bookmarks',
                                                    default=[]))
        self.repo_bookmarks.set(self.metadata.get('repo_bookmarks',
                                                  default=[]))
        self.media_bookmarks.set(self.metadata.get('media_bookmarks',
                                                   default=[]))
        self.place_bookmarks.set(self.metadata.get('place_bookmarks',
                                                   default=[]))
        self.note_bookmarks.set(self.metadata.get('note_bookmarks',
                                                   default=[]))

        # Custom type values
        self.family_event_names = set(self.metadata.get('fevent_names',
                                                        default=[]))
        self.individual_event_names = set(self.metadata.get('pevent_names',
                                                            default=[]))
        self.family_attributes = set(self.metadata.get('fattr_names',
                                                       default=[]))
        self.individual_attributes = set(self.metadata.get('pattr_names',
                                                           default=[]))
        self.marker_names = set(self.metadata.get('marker_names', default=[]))
        self.child_ref_types = set(self.metadata.get('child_refs',
                                                     default=[]))
        self.family_rel_types = set(self.metadata.get('family_rels',
                                                      default=[]))
        self.event_role_names = set(self.metadata.get('event_roles',
                                                      default=[]))
        self.name_types = set(self.metadata.get('name_types', default=[]))
        self.repository_types = set(self.metadata.get('repo_types',
                                                      default=[]))
        self.note_types = set(self.metadata.get('note_types',
                                                default=[]))
        self.source_media_types = set(self.metadata.get('sm_types',
                                                        default=[]))
        self.url_types = set(self.metadata.get('url_types', default=[]))
        self.media_attributes = set(self.metadata.get('mattr_names',
                                                      default=[]))

        # surname list
        self.surname_list = self.metadata.get('surname_list', default=[])

    def connect_secondary(self):
        """
        This method connects or creates secondary index tables.
        It assumes that the tables either exist and are in the right
        format or do not exist (in which case they get created).

        It is the responsibility of upgrade code to either create
        or remove invalid secondary index tables.
        """
        
        # index tables used just for speeding up searches
        if self.readonly:
            table_flags = db.DB_RDONLY
        else:
            table_flags = self.__open_flags()

        self.surnames = db.DB(self.env)
        self.surnames.set_flags(db.DB_DUP|db.DB_DUPSORT)
        self.surnames.open(self.full_name, "surnames", db.DB_BTREE,
                           flags=table_flags)

        self.id_trans = db.DB(self.env)
        self.id_trans.set_flags(db.DB_DUP)
        self.id_trans.open(self.full_name, "idtrans",
                           db.DB_HASH, flags=table_flags)

        self.fid_trans = db.DB(self.env)
        self.fid_trans.set_flags(db.DB_DUP)
        self.fid_trans.open(self.full_name, "fidtrans",
                            db.DB_HASH, flags=table_flags)

        self.eid_trans = db.DB(self.env)
        self.eid_trans.set_flags(db.DB_DUP)
        self.eid_trans.open(self.full_name, "eidtrans",
                            db.DB_HASH, flags=table_flags)

        self.pid_trans = db.DB(self.env)
        self.pid_trans.set_flags(db.DB_DUP)
        self.pid_trans.open(self.full_name, "pidtrans",
                            db.DB_HASH, flags=table_flags)

        self.sid_trans = db.DB(self.env)
        self.sid_trans.set_flags(db.DB_DUP)
        self.sid_trans.open(self.full_name, "sidtrans",
                            db.DB_HASH, flags=table_flags)

        self.oid_trans = db.DB(self.env)
        self.oid_trans.set_flags(db.DB_DUP)
        self.oid_trans.open(self.full_name, "oidtrans",
                            db.DB_HASH, flags=table_flags)

        self.rid_trans = db.DB(self.env)
        self.rid_trans.set_flags(db.DB_DUP)
        self.rid_trans.open(self.full_name, "ridtrans",
                            db.DB_HASH, flags=table_flags)

        self.nid_trans = db.DB(self.env)
        self.nid_trans.set_flags(db.DB_DUP)
        self.nid_trans.open(self.full_name, "nidtrans",
                            db.DB_HASH, flags=table_flags)

        self.reference_map_primary_map = db.DB(self.env)
        self.reference_map_primary_map.set_flags(db.DB_DUP)
        self.reference_map_primary_map.open(self.full_name,
                                            "reference_map_primary_map",
                                            db.DB_BTREE, flags=table_flags)

        self.reference_map_referenced_map = db.DB(self.env)
        self.reference_map_referenced_map.set_flags(db.DB_DUP|db.DB_DUPSORT)
        self.reference_map_referenced_map.open(self.full_name,
                                               "reference_map_referenced_map",
                                               db.DB_BTREE, flags=table_flags)

        if not self.readonly:
            self.person_map.associate(self.surnames, find_surname, table_flags)
            self.person_map.associate(self.id_trans, find_idmap, table_flags)
            self.family_map.associate(self.fid_trans, find_idmap, table_flags)
            self.event_map.associate(self.eid_trans, find_idmap, table_flags)
            self.repository_map.associate(self.rid_trans, find_idmap,
                                          table_flags)
            self.note_map.associate(self.nid_trans, find_idmap, table_flags)
            self.place_map.associate(self.pid_trans, find_idmap, table_flags)
            self.media_map.associate(self.oid_trans, find_idmap, table_flags)
            self.source_map.associate(self.sid_trans, find_idmap, table_flags)
            self.reference_map.associate(self.reference_map_primary_map,
                                         find_primary_handle,
                                         table_flags)
            self.reference_map.associate(self.reference_map_referenced_map,
                                         find_referenced_handle,
                                         table_flags)
        self.secondary_connected = True

        self.smap_index = len(self.source_map)
        self.emap_index = len(self.event_map)
        self.pmap_index = len(self.person_map)
        self.fmap_index = len(self.family_map)
        self.lmap_index = len(self.place_map)
        self.omap_index = len(self.media_map)
        self.rmap_index = len(self.repository_map)
        self.nmap_index = len(self.note_map)

    def rebuild_secondary(self, callback):
        if self.readonly:
            return

        table_flags = self.__open_flags()

        # remove existing secondary indices
        self.id_trans.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "idtrans")
        if callback:
            callback(1)

        self.surnames.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "surnames")
        if callback:
            callback(2)

        # Repair secondary indices related to family_map
        self.fid_trans.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "fidtrans")
        if callback:
            callback(3)

        # Repair secondary indices related to place_map
        self.pid_trans.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "pidtrans")
        if callback:
            callback(4)

        # Repair secondary indices related to media_map
        self.oid_trans.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "oidtrans")
        if callback:
            callback(5)

        # Repair secondary indices related to source_map
        self.sid_trans.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "sidtrans")
        if callback:
            callback(6)

        # Repair secondary indices related to event_map
        self.eid_trans.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "eidtrans")
        if callback:
            callback(7)

        # Repair secondary indices related to repository_map
        self.rid_trans.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "ridtrans")
        if callback:
            callback(8)

        # Repair secondary indices related to note_map
        self.nid_trans.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "nidtrans")
        if callback:
            callback(9)

        # Repair secondary indices related to reference_map
        self.reference_map_primary_map.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "reference_map_primary_map")
        if callback:
            callback(10)

        self.reference_map_referenced_map.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "reference_map_referenced_map")
        if callback:
            callback(11)

        # Set flag saying that we have removed secondary indices
        # and then call the creating routine
        self.secondary_connected = False
        self.connect_secondary()
        if callback:
            callback(12)

    def find_backlink_handles(self, handle, include_classes=None):
        """
        Find all objects that hold a reference to the object handle.
        Returns an interator over a list of (class_name, handle) tuples.

        @param handle: handle of the object to search for.
        @type handle: database handle
        @param include_classes: list of class names to include in the results.
                                Default: None means include all classes.
        @type include_classes: list of class names

        Note that this is a generator function, it returns a iterator for
        use in loops. If you want a list of the results use:

        >       result_list = list(find_backlink_handles(handle))
        """

        # Use the secondary index to locate all the reference_map entries
        # that include a reference to the object we are looking for.
        referenced_cur = self.get_reference_map_referenced_cursor()

        try:
            ret = referenced_cur.set(handle)
        except:
            ret = None
            
        while (ret is not None):
            (key, data) = ret
            
            # data values are of the form:
            #   ((primary_object_class_name, primary_object_handle),
            #    (referenced_object_class_name, referenced_object_handle))
            # so we need the first tuple to give us the type to compare

            ### FIXME: this is a dirty hack that works without no
            ### sensible explanation. For some reason, for a readonly
            ### database, secondary index returns a primary table key
            ### corresponding to the data, not the data.
            if self.readonly:
                data = self.reference_map.get(data)
            else:
                data = pickle.loads(data)
            if include_classes is None or \
                   KEY_TO_CLASS_MAP[data[0][0]] in include_classes:
                yield (KEY_TO_CLASS_MAP[data[0][0]], data[0][1])
                
            ret = referenced_cur.next_dup()

        referenced_cur.close()

    def delete_primary_from_reference_map(self, hndl, transaction, txn=None):
        """
        Remove all references to the primary object from the reference_map.
        """

        primary_cur = self.get_reference_map_primary_cursor()

        try:
            ret = primary_cur.set(hndl)
        except:
            ret = None
        
        remove_list = set()
        while (ret is not None):
            (key, data) = ret
            
            # data values are of the form:
            #   ((primary_object_class_name, primary_object_handle),
            #    (referenced_object_class_name, referenced_object_handle))
            
            # so we need the second tuple give us a reference that we can
            # combine with the primary_handle to get the main key.

            main_key = (hndl, pickle.loads(data)[1][1])
            
            # The trick is not to remove while inside the cursor,
            # but collect them all and remove after the cursor is closed
            remove_list.add(main_key)

            ret = primary_cur.next_dup()

        primary_cur.close()

        # Now that the cursor is closed, we can remove things
        for main_key in remove_list:
            self.__remove_reference(main_key, transaction, txn)
        
    def update_reference_map(self, obj, transaction, txn=None):
        """
        If txn is given, then changes are written right away using txn.
        """
        
        # Add references to the reference_map for all primary object referenced
        # from the primary object 'obj, or any of its secondary objects.

        handle = obj.handle
        update = str(handle) in self.reference_map_primary_map

        if update:
            # First thing to do is get hold of all rows in the reference_map
            # table that hold a reference from this primary obj. This means
            # finding all the rows that have this handle somewhere in the
            # list of (class_name, handle) pairs.
            # The primary_map sec index allows us to look this up quickly.

            existing_references = set()

            primary_cur = self.get_reference_map_primary_cursor()

            try:
                ret = primary_cur.set(handle)
            except:
                ret = None

            while (ret is not None):
                (key, data) = ret

                # data values are of the form:
                #   ((primary_object_class_name, primary_object_handle),
                #    (referenced_object_class_name, referenced_object_handle))
                # so we need the second tuple give us a reference that we can
                # compare with what is returned from
                # get_referenced_handles_recursively

                # secondary DBs are not DBShelf's, so we need to do pickling
                # and unpicking ourselves here
                existing_reference = pickle.loads(data)[1]
                existing_references.add(
                    (KEY_TO_CLASS_MAP[existing_reference[0]],
                     existing_reference[1]))
                ret = primary_cur.next_dup()

            primary_cur.close()

            # Once we have the list of rows that already have a reference
            # we need to compare it with the list of objects that are
            # still references from the primary object.

            current_references = set(obj.get_referenced_handles_recursively())

            no_longer_required_references = existing_references.difference(
                current_references)

            new_references = current_references.difference(existing_references)

        else:
            # No existing refs are found:
            #    all we have is new, nothing to remove
            no_longer_required_references = set()
            new_references = set(obj.get_referenced_handles_recursively())
            
        # handle addition of new references
        for (ref_class_name, ref_handle) in new_references:
            data = ((CLASS_TO_KEY_MAP[obj.__class__.__name__], handle),
                    (CLASS_TO_KEY_MAP[ref_class_name], ref_handle), )
            self.__add_reference((handle, ref_handle), data, transaction, txn)

        # handle deletion of old references
        for (ref_class_name, ref_handle) in no_longer_required_references:
            try:
                self.__remove_reference((handle, ref_handle), transaction, txn)
            except:
                # ignore missing old reference
                pass

    def __remove_reference(self, key, transaction, txn=None):
        """
        Remove the reference specified by the key,
        preserving the change in the passed transaction.
        """
        if not self.readonly:
            if transaction.batch:
                self.reference_map.delete(str(key), txn=txn)
                if not self.UseTXN:
                    self.reference_map.sync()
            else:
                old_data = self.reference_map.get(str(key), txn=self.txn)
                transaction.add(REFERENCE_KEY, str(key), old_data, None)
                transaction.reference_del.append(str(key))

    def __add_reference(self, key, data, transaction, txn=None):
        """
        Add the reference specified by the key and the data,
        preserving the change in the passed transaction.
        """

        if self.readonly or not key:
            return
        
        if transaction.batch:
            self.reference_map.put(str(key), data, txn=txn)
            if not self.UseTXN:
                self.reference_map.sync()
        else:
            transaction.add(REFERENCE_KEY, str(key), None, data)
            transaction.reference_add.append((str(key), data))

    def reindex_reference_map(self, callback):
        """
        Reindex all primary records in the database.
        This will be a slow process for large databases.

        """

        # First, remove the reference map and related tables
        self.reference_map_referenced_map.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "reference_map_referenced_map")
        if callback:
            callback(1)

        self.reference_map_primary_map.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "reference_map_primary_map")
        if callback:
            callback(2)

        self.reference_map.close()
        junk = db.DB(self.env)
        junk.remove(self.full_name, "reference_map")
        if callback:
            callback(3)

        # Open reference_map and primapry map
        self.reference_map  = self.__open_table(self.full_name, "reference_map",
                                                dbtype=db.DB_BTREE)
        
        open_flags = self.__open_flags()
        self.reference_map_primary_map = db.DB(self.env)
        self.reference_map_primary_map.set_flags(db.DB_DUP)
        self.reference_map_primary_map.open(self.full_name,
                                            "reference_map_primary_map",
                                            db.DB_BTREE, flags=open_flags)
        self.reference_map.associate(self.reference_map_primary_map,
                                     find_primary_handle,
                                     open_flags)

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
            'Note': {'cursor_func': self.get_note_cursor,
                           'class_func': Note},
            }

        transaction = self.transaction_begin(batch=True, no_magic=True)
        if callback:
            callback(4)

        # Now we use the functions and classes defined above
        # to loop through each of the primary object tables.
        for primary_table_name, funcs in primary_tables.iteritems():
            with funcs['cursor_func']() as cursor:

            # Grab the real object class here so that the lookup does
            # not happen inside the cursor loop.
                class_func = funcs['class_func']
                for found_handle, val in cursor:
                    obj = class_func()
                    obj.unserialize(val)

                    if self.UseTXN:
                        the_txn = self.env.txn_begin()
                    else:
                        the_txn = None
                    self.update_reference_map(obj, transaction, the_txn)
                    if not self.UseTXN:
                        self.reference_map.sync()
                    if the_txn:
                        the_txn.commit()

        if callback:
            callback(5)
        self.transaction_commit(transaction, _("Rebuild reference map"))

        self.reference_map_referenced_map = db.DB(self.env)
        self.reference_map_referenced_map.set_flags(db.DB_DUP|db.DB_DUPSORT)
        self.reference_map_referenced_map.open(
            self.full_name, "reference_map_referenced_map",
            db.DB_BTREE, flags=open_flags)
        self.reference_map.associate(self.reference_map_referenced_map,
                                     find_referenced_handle, open_flags)
        if callback:
            callback(6)

        return
        
    def __close_metadata(self):
        if not self.readonly:
            if self.UseTXN:
                # Start transaction if needed
                the_txn = self.env.txn_begin()
            else:
                the_txn = None

            # name display formats
            self.metadata.put('name_formats', self.name_formats, txn=the_txn)
            
            # database owner
            self.metadata.put('researcher', self.owner, txn=the_txn)

            # bookmarks
            self.metadata.put('bookmarks', self.bookmarks.get(), txn=the_txn)
            self.metadata.put('family_bookmarks', self.family_bookmarks.get(), 
                              txn=the_txn)
            self.metadata.put('event_bookmarks', self.event_bookmarks.get(), 
                              txn=the_txn)
            self.metadata.put('source_bookmarks', self.source_bookmarks.get(), 
                              txn=the_txn)
            self.metadata.put('place_bookmarks', self.place_bookmarks.get(), 
                              txn=the_txn)
            self.metadata.put('repo_bookmarks', self.repo_bookmarks.get(), 
                              txn=the_txn)
            self.metadata.put('media_bookmarks', self.media_bookmarks.get(), 
                              txn=the_txn)
            self.metadata.put('note_bookmarks', self.note_bookmarks.get(), 
                              txn=the_txn)

            # gender stats
            self.metadata.put('gender_stats', self.genderStats.save_stats(), 
                              txn=the_txn)
            # Custom type values
            self.metadata.put('fevent_names', list(self.family_event_names), 
                              txn=the_txn)
            self.metadata.put('pevent_names', list(self.individual_event_names),
                              txn=the_txn)
            self.metadata.put('fattr_names', list(self.family_attributes), 
                              txn=the_txn)
            self.metadata.put('pattr_names', list(self.individual_attributes), 
                              txn=the_txn)
            self.metadata.put('marker_names', list(self.marker_names), 
                              txn=the_txn)
            self.metadata.put('child_refs', list(self.child_ref_types), 
                              txn=the_txn)
            self.metadata.put('family_rels', list(self.family_rel_types), 
                              txn=the_txn)
            self.metadata.put('event_roles', list(self.event_role_names), 
                              txn=the_txn)
            self.metadata.put('name_types', list(self.name_types), 
                              txn=the_txn)
            self.metadata.put('repo_types', list(self.repository_types), 
                              txn=the_txn)
            self.metadata.put('note_types', list(self.note_types), 
                              txn=the_txn)
            self.metadata.put('sm_types', list(self.source_media_types), 
                              txn=the_txn)
            self.metadata.put('url_types', list(self.url_types), 
                              txn=the_txn)
            self.metadata.put('mattr_names', list(self.media_attributes), 
                              txn=the_txn)
            # name display formats
            self.metadata.put('surname_list', self.surname_list, txn=the_txn)

            if self.UseTXN:
                the_txn.commit()
            else:
                self.metadata.sync()

        self.metadata.close()

    def __close_early(self):
        """
        Bail out if the incompatible version is discovered:
        * close cleanly to not damage data/env
        * raise exception
        """
        self.metadata.close()
        self.env.close()
        self.metadata   = None
        self.env        = None
        self.db_is_open = False
        raise DbVersionError()

    def close(self):
        if not self.db_is_open:
            return

        if self.UseTXN:
            self.env.txn_checkpoint()

        self.__close_metadata()
        self.name_group.close()
        self.surnames.close()
        self.id_trans.close()
        self.fid_trans.close()
        self.eid_trans.close()
        self.rid_trans.close()
        self.nid_trans.close()
        self.oid_trans.close()
        self.sid_trans.close()
        self.pid_trans.close()
        self.reference_map_primary_map.close()
        self.reference_map_referenced_map.close()
        self.reference_map.close()

        # primary databases must be closed after secondary indexes, or
        # we run into problems with any active cursors.
        self.person_map.close()
        self.family_map.close()
        self.repository_map.close()
        self.note_map.close()
        self.place_map.close()
        self.source_map.close()
        self.media_map.close()
        self.event_map.close()
        self.env.close()

        try:
            self.close_undodb()
        except db.DBNoSuchFileError:
            pass

        self.person_map     = None
        self.family_map     = None
        self.repository_map = None
        self.note_map       = None
        self.place_map      = None
        self.source_map     = None
        self.media_map      = None
        self.event_map      = None
        self.surnames       = None
        self.name_group     = None
        self.env            = None
        self.metadata       = None
        self.db_is_open     = False

    def do_remove_object(self, handle, transaction, data_map, key, del_list):
        if self.readonly or not handle:
            return

        handle = str(handle)
        if transaction.batch:
            if self.UseTXN:
                the_txn = self.env.txn_begin()
            else:
                the_txn = None
            self.delete_primary_from_reference_map(handle, transaction, 
                                                    txn=the_txn)
            data_map.delete(handle, txn=the_txn)
            if not self.UseTXN:
                data_map.sync()
            if the_txn:
                the_txn.commit()
        else:
            self.delete_primary_from_reference_map(handle, transaction)
            old_data = data_map.get(handle, txn=self.txn)
            transaction.add(key, handle, old_data, None)
            del_list.append(handle)

    def del_person(self, handle):
        self.person_map.delete(str(handle), txn=self.txn)
        if not self.UseTXN:
            self.person_map.sync()

    def del_source(self, handle):
        self.source_map.delete(str(handle), txn=self.txn)
        if not self.UseTXN:
            self.source_map.sync()

    def del_repository(self, handle):
        self.repository_map.delete(str(handle), txn=self.txn)
        if not self.UseTXN:
            self.repository_map.sync()

    def del_note(self, handle):
        self.note_map.delete(str(handle), txn=self.txn)
        if not self.UseTXN:
            self.note_map.sync()

    def del_place(self, handle):
        self.place_map.delete(str(handle), txn=self.txn)
        if not self.UseTXN:
            self.place_map.sync()

    def del_media(self, handle):
        self.media_map.delete(str(handle), txn=self.txn)
        if not self.UseTXN:
            self.media_map.sync()

    def del_family(self, handle):
        self.family_map.delete(str(handle), txn=self.txn)
        if not self.UseTXN:
            self.family_map.sync()

    def del_event(self, handle):
        self.event_map.delete(str(handle), txn=self.txn)
        if not self.UseTXN:
            self.event_map.sync()

    def set_name_group_mapping(self, name, group):
        """Make name group under the value of group.
           If group =None, the old grouping is deleted 
        """
        if not self.readonly:
            if self.UseTXN:
                # Start transaction if needed
                the_txn = self.env.txn_begin()
            else:
                the_txn = None
            name = str(name)
            data = self.name_group.get(name, txn=the_txn)
            if data is not None:
                self.name_group.delete(name, txn=the_txn)
            if group is not None:
                self.name_group.put(name,group,txn=the_txn)
            if self.UseTXN:
                the_txn.commit()
            else:
                self.name_group.sync()
            self.emit('person-rebuild')

    def build_surname_list(self):
        self.surname_list = list(set(self.surnames.keys()))
        self.sort_surname_list()

    def remove_from_surname_list(self, person):
        """
        Check whether there are persons with the same surname left in
        the database. If not then we need to remove the name from the list.
        The function must be overridden in the derived class.
        """
        name = str(person.get_primary_name().get_surname())
        try:
            if self.surnames.keys().count(name) == 1:
                self.surname_list.remove(unicode(name))
        except ValueError:
            pass

    def __get_obj_from_gramps_id(self, val, tbl, class_init, prim_tbl):
        if tbl.has_key(str(val)):
        #if str(val) in tbl:
            data = tbl.get(str(val), txn=self.txn)
            obj = class_init()
            ### FIXME: this is a dirty hack that works without no
            ### sensible explanation. For some reason, for a readonly
            ### database, secondary index returns a primary table key
            ### corresponding to the data, not the data.
            if self.readonly:
                tuple_data = prim_tbl.get(data, txn=self.txn)
            else:
                tuple_data = pickle.loads(data)
            obj.unserialize(tuple_data)
            return obj
        else:
            return None

    def get_person_from_gramps_id(self, val):
        """
        Finds a Person in the database from the passed gramps' ID.
        If no such Person exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.id_trans, Person, 
                                            self.person_map)

    def get_family_from_gramps_id(self, val):
        """
        Finds a Family in the database from the passed gramps' ID.
        If no such Family exists, None is return.
        """
        return self.__get_obj_from_gramps_id(val, self.fid_trans, Family, 
                                            self.family_map)

    def get_event_from_gramps_id(self, val):
        """
        Finds an Event in the database from the passed gramps' ID.
        If no such Family exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.eid_trans, Event, 
                                            self.event_map)

    def get_place_from_gramps_id(self, val):
        """
        Finds a Place in the database from the passed gramps' ID.
        If no such Place exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.pid_trans, Place, 
                                            self.place_map)

    def get_source_from_gramps_id(self, val):
        """
        Finds a Source in the database from the passed gramps' ID.
        If no such Source exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.sid_trans, Source, 
                                            self.source_map)

    def get_object_from_gramps_id(self, val):
        """
        Finds a MediaObject in the database from the passed gramps' ID.
        If no such MediaObject exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.oid_trans, MediaObject, 
                                            self.media_map)

    def get_repository_from_gramps_id(self, val):
        """
        Finds a Repository in the database from the passed gramps' ID.
        If no such Repository exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.rid_trans, Repository, 
                                            self.repository_map)

    def get_note_from_gramps_id(self, val):
        """
        Finds a Note in the database from the passed gramps' ID.
        If no such Note exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.nid_trans, Note, 
                                            self.note_map)

    def commit_base(self, obj, data_map, key, update_list, add_list, 
                     transaction, change_time):
        """
        Commits the specified object to the database, storing the changes
        as part of the transaction.
        """
        if self.readonly or not obj or not obj.handle:
            return 

        if change_time:
            obj.change = int(change_time)
        else:
            obj.change = int(time.time())
        handle = str(obj.handle)
        
        if transaction.batch:
            if self.UseTXN:
                the_txn = self.env.txn_begin()
            else:
                the_txn = None
            self.update_reference_map(obj, transaction, txn=the_txn)
            data_map.put(handle, obj.serialize(), txn=the_txn)
            if not self.UseTXN:
                data_map.sync()
            if the_txn:
                the_txn.commit()
            old_data = None
        else:
            self.update_reference_map(obj, transaction)
            old_data = data_map.get(handle, txn=self.txn)
            new_data = obj.serialize()
            transaction.add(key, handle, old_data, new_data)
            if old_data:
                update_list.append((handle, new_data))
            else:
                add_list.append((handle, new_data))
        return old_data

    def do_commit(self, add_list, db_map):
        retlist = []
        for (handle, data) in add_list:
            db_map.put(handle, data, self.txn)
            if not self.UseTXN:
                db_map.sync()
            retlist.append(str(handle))
        return retlist

    def get_from_handle(self, handle, class_type, data_map):
        try:
            data = data_map.get(str(handle), txn=self.txn)
        except:
            data = None
            # under certain circumstances during a database reload, 
            # data_map can be none. If so, then don't report an error
            if data_map:
                LOG.error("Failed to get from handle", exc_info=True)
        if data:
            newobj = class_type()
            newobj.unserialize(data)
            return newobj
        return None

    def find_from_handle(self, hndl, transaction, class_type, dmap, add_func):
        obj = class_type()
        hndl = str(hndl)
        new = True
        if hndl in dmap:
            data = dmap.get(hndl, txn=self.txn)
            obj.unserialize(data)
            #references create object with id None before object is really made
            if obj.gramps_id is not None:
                new = False
        else:
            obj.set_handle(hndl)
            add_func(obj, transaction)
        return obj, new

    def transaction_begin(self, msg="", batch=False, no_magic=False):
        """
        Create a new Transaction tied to the current UNDO database. The
        transaction has no effect until it is committed using the
        transaction_commit function of the this database object.
        """

        if batch:
            # A batch transaction does not store the commits
            # Aborting the session completely will become impossible.
            self.abort_possible = False
            # Undo is also impossible after batch transaction
            #self.undoindex = -1
            #self.translist = [None] * len(self.translist)
        transaction = BdbTransaction(msg, self.undodb, batch, no_magic)
        if transaction.batch:
            if self.UseTXN:
                self.env.txn_checkpoint()
                self.env.set_flags(db.DB_TXN_NOSYNC, 1)      # async txn

            if self.secondary_connected and not transaction.no_magic:
                # Disconnect unneeded secondary indices
                self.surnames.close()
                junk = db.DB(self.env)
                junk.remove(self.full_name, "surnames")

                self.reference_map_referenced_map.close()
                junk = db.DB(self.env)
                junk.remove(self.full_name, "reference_map_referenced_map")
            
        return transaction

    def transaction_commit(self, transaction, msg):

        # Start BSD DB transaction -- DBTxn
        if self.UseTXN:
            self.txn = self.env.txn_begin()
        else:
            self.txn = None

        DbBase.transaction_commit(self, transaction, msg)

        for (key, data) in transaction.reference_add:
            self.reference_map.put(str(key), data, txn=self.txn)

        for key in transaction.reference_del:
            self.reference_map.delete(str(key), txn=self.txn)

        if (len(transaction.reference_add)+len(transaction.reference_del)) > 0\
               and not self.UseTXN:
            self.reference_map.sync()

        # Commit BSD DB transaction -- DBTxn
        if self.UseTXN:
            self.txn.commit()
        if transaction.batch:
            if self.UseTXN:
                self.env.txn_checkpoint()
                self.env.set_flags(db.DB_TXN_NOSYNC, 0)      # sync txn

            if not transaction.no_magic:
                # create new secondary indices to replace the ones removed
                open_flags = self.__open_flags()
                dupe_flags = db.DB_DUP|db.DB_DUPSORT

                self.surnames = db.DB(self.env)
                self.surnames.set_flags(dupe_flags)
                self.surnames.open(self.full_name, "surnames", 
                                   db.DB_BTREE, flags=open_flags)
                self.person_map.associate(self.surnames, find_surname, 
                                          open_flags)
            
                self.reference_map_referenced_map = db.DB(self.env)
                self.reference_map_referenced_map.set_flags(dupe_flags)
                self.reference_map_referenced_map.open(
                    self.full_name, "reference_map_referenced_map", 
                    db.DB_BTREE, flags=open_flags)
                self.reference_map.associate(self.reference_map_referenced_map, 
                                             find_referenced_handle, open_flags)

            # Only build surname list after surname index is surely back
            self.build_surname_list()

        self.txn = None

    def undo(self, update_history=True):
        if self.UseTXN:
            self.txn = self.env.txn_begin()
        status = DbBase.undo(self, update_history)
        if self.UseTXN:
            if status:
                self.txn.commit()
            else:
                self.txn.abort()
        self.txn = None
        return status

    def redo(self, update_history=True):
        if self.UseTXN:
            self.txn = self.env.txn_begin()
        status = DbBase.redo(self, update_history)
        if self.UseTXN:
            if status:
                self.txn.commit()
            else:
                self.txn.abort()
        self.txn = None
        return status

    def undo_reference(self, data, handle):
        if data is None:
            self.reference_map.delete(handle, txn=self.txn)
        else:
            self.reference_map.put(handle, data, txn=self.txn)

    def undo_data(self, data, handle, db_map, signal_root):
        if data is None:
            self.emit(signal_root + '-delete', ([handle], ))
            db_map.delete(handle, txn=self.txn)
        else:
            ex_data = db_map.get(handle, txn=self.txn)
            if ex_data:
                signal = signal_root + '-update'
            else:
                signal = signal_root + '-add'
            db_map.put(handle, data, txn=self.txn)
            self.emit(signal, ([handle], ))

    def gramps_upgrade(self, callback=None):
        UpdateCallback.__init__(self, callback)
        
        version = self.metadata.get('version', default=_MINVERSION)

        t = time.time()
        if version < 10:
            self.gramps_upgrade_10()
        if version < 11:
            self.gramps_upgrade_11()
        if version < 12:
            self.gramps_upgrade_12()
        if version < 13:
            self.gramps_upgrade_13()
        if version < 14:
            self.gramps_upgrade_14()
        LOG.debug("Upgrade time: %s %s", int(time.time()-t), "seconds")

    def gramps_upgrade_10(self):
        LOG.debug("Upgrading to DB version 10...")

        # This upgrade adds attribute lists to Event and EventRef objects
        length = self.get_number_of_events() + len(self.person_map) \
                 + self.get_number_of_families()
        self.set_total(length)

        for handle in self.event_map.keys():
            info = self.event_map[handle]

            (junk_handle, gramps_id, the_type, date, description, 
             place, cause, source_list, note, media_list, 
             change, marker, private) = info

            # Cause is removed, so we're converting it into an attribute
            if cause.strip():
                attr = Attribute()
                attr.set_type(AttributeType.CAUSE)
                attr.set_value(cause)
                attr_list = [attr.serialize()]
            else:
                attr_list = []

            info = (handle, gramps_id, the_type, date, 
                    description, place, source_list, note, media_list, 
                    attr_list, change, marker, private)

            if self.UseTXN:
                the_txn = self.env.txn_begin()
            else:
                the_txn = None
            self.event_map.put(str(handle), info, txn=the_txn)
            if self.UseTXN:
                the_txn.commit()
            self.update()

        if not self.UseTXN:
            self.event_map.sync()

        # Personal event references
        for handle in self.person_map.keys():
            info = self.person_map[handle]

            (junk_handle, gramps_id, gender, 
             primary_name, alternate_names, death_ref_index, 
             birth_ref_index, event_ref_list, family_list, 
             parent_family_list, media_list, address_list, attribute_list, 
             urls, lds_ord_list, source_list, note, change, marker, 
             private, person_ref_list, ) = info

            # Names lost the "sname" attribute
            new_primary_name = convert_name_10(primary_name)
            new_alternate_names = [convert_name_10(name)
                                   for name in alternate_names]

            # Events gained attribute_list
            new_event_ref_list = [
                (privacy, note, [], ref, role)
                for (privacy, note, ref, role) in event_ref_list]

            info = (handle, gramps_id, gender, new_primary_name, 
                    new_alternate_names, 
                    death_ref_index, birth_ref_index, new_event_ref_list, 
                    family_list, parent_family_list, media_list, address_list, 
                    attribute_list, urls, lds_ord_list, source_list, note, 
                    change, marker, private, person_ref_list, )

            if self.UseTXN:
                the_txn = self.env.txn_begin()
            else:
                the_txn = None
            self.person_map.put(str(handle), info, txn=the_txn)
            if self.UseTXN:
                the_txn.commit()
            self.update()

        if not self.UseTXN:
            self.person_map.sync()

        # Family event references
        for handle in self.family_map.keys():
            info = self.family_map[handle]

            (junk_handle, gramps_id, father_handle, 
             mother_handle, child_ref_list, the_type, event_ref_list, 
             media_list, attribute_list, lds_seal_list, source_list, note, 
             change, marker, private) = info

            new_event_ref_list = [
                (privacy, note, [], ref, role)
                for (privacy, note, ref, role) in event_ref_list]

            info = (handle, gramps_id, father_handle, 
                        mother_handle, child_ref_list, the_type, 
                        new_event_ref_list, 
                        media_list, attribute_list, lds_seal_list, 
                        source_list, note, change, marker, private)

            if self.UseTXN:
                the_txn = self.env.txn_begin()
            else:
                the_txn = None
            self.family_map.put(str(handle), info, txn=the_txn)
            if self.UseTXN:
                the_txn.commit()
            self.update()
        if not self.UseTXN:
            self.family_map.sync()

        self.reset()

        if self.UseTXN:
            # Separate transaction to save metadata
            the_txn = self.env.txn_begin()
        else:
            the_txn = None
        self.metadata.put('version', 10, txn=the_txn)
        if self.UseTXN:
            the_txn.commit()
        else:
            self.metadata.sync()

        LOG.debug("Done upgrading to DB version 10")

    def gramps_upgrade_11(self):
        LOG.debug("Upgrading to DB version 11...")

        # This upgrade modifies addresses and locations
        length = len(self.person_map) + len(self.place_map) \
                 + len(self.repository_map)
        self.set_total(length)

        # Personal addresses
        for handle in self.person_map.keys():
            info = self.person_map[handle]

            (junk_handle, gramps_id, gender, 
             primary_name, alternate_names, death_ref_index, 
             birth_ref_index, event_ref_list, family_list, 
             parent_family_list, media_list, address_list, attribute_list, 
             urls, lds_ord_list, source_list, note, change, marker, 
             private, person_ref_list, ) = info

            new_address_list = [convert_address_11(addr)
                                for addr in address_list]

            info = (handle, gramps_id, gender, 
                    primary_name, alternate_names, death_ref_index, 
                    birth_ref_index, event_ref_list, family_list, 
                    parent_family_list, media_list, new_address_list, 
                    attribute_list, 
                    urls, lds_ord_list, source_list, note, change, marker, 
                    private, person_ref_list, )

            if self.UseTXN:
                the_txn = self.env.txn_begin()
            else:
                the_txn = None
            self.person_map.put(str(handle), info, txn=the_txn)
            if self.UseTXN:
                the_txn.commit()
            self.update()

        if not self.UseTXN:
            self.person_map.sync()
        
        # Repositories
        for handle in self.repository_map.keys():
            info = self.repository_map[handle]

            (junk_handle, gramps_id, the_type, name, note, 
             address_list, urls, marker, private) = info

            new_address_list = [convert_address_11(addr)
                                for addr in address_list]

            info = (handle, gramps_id, the_type, name, note, 
                    new_address_list, urls, marker, private)

            if self.UseTXN:
                the_txn = self.env.txn_begin()
            else:
                the_txn = None
            self.repository_map.put(str(handle), info, txn=the_txn)
            if self.UseTXN:
                the_txn.commit()
            self.update()

        if not self.UseTXN:
            self.repository_map.sync()

        # Places
        for handle in self.place_map.keys():
            info = self.place_map[handle]

            (junk_handle, gramps_id, title, long, lat, main_loc, alt_loc, urls, 
             media_list, source_list, note, change, marker, private) = info

            if main_loc:
                main_loc = convert_location_11(main_loc)

            new_alt_loc = [convert_location_11(loc) for loc in alt_loc]

            info = (handle, gramps_id, title, long, lat, main_loc, new_alt_loc, 
                    urls, media_list, source_list, note, change, marker, private)

            if self.UseTXN:
                the_txn = self.env.txn_begin()
            else:
                the_txn = None
            self.place_map.put(str(handle), info, txn=the_txn)
            if self.UseTXN:
                the_txn.commit()
            self.update()

        if not self.UseTXN:
            self.place_map.sync()

        self.reset()

        if self.UseTXN:
            # Separate transaction to save metadata
            the_txn = self.env.txn_begin()
        else:
            the_txn = None
        self.metadata.put('version', 11, txn=the_txn)
        if self.UseTXN:
            the_txn.commit()
        else:
            self.metadata.sync()

        LOG.debug("Done upgrading to DB version 11")

    def gramps_upgrade_12(self):
        LOG.debug("Upgrading to DB version 12...")
        # Hook up surnames 
        table_flags = self.__open_flags()
        self.surnames = db.DB(self.env)
        self.surnames.set_flags(db.DB_DUP|db.DB_DUPSORT)
        self.surnames.open(self.full_name, "surnames", db.DB_BTREE, 
                           flags=table_flags)
        self.person_map.associate(self.surnames, find_surname, table_flags)
        
        self.build_surname_list()

        # Close so that we can open it again later
        self.surnames.close()

        if self.UseTXN:
            # Separate transaction to save metadata
            the_txn = self.env.txn_begin()
        else:
            the_txn = None
        self.metadata.put('version', 12, txn=the_txn)
        if self.UseTXN:
            the_txn.commit()
        else:
            self.metadata.sync()

        LOG.debug("Done upgrading to DB version 12")

    def gramps_upgrade_13(self):
        """
        First upgrade in 2.3/3.0 branch.
        We assume that the data is at least from 2.2.x.
        """
        LOG.debug("Upgrading to DB version 13...")
        # Hook up note id index
        table_flags = self.__open_flags()
        self.nid_trans = db.DB(self.env)
        self.nid_trans.set_flags(db.DB_DUP)
        self.nid_trans.open(self.full_name, "nidtrans", 
                            db.DB_HASH, flags=table_flags)
        self.note_map.associate(self.nid_trans, find_idmap, table_flags)

        # This upgrade modifies repos (store change attribute)
        # And converts notes to the list of handles in all records
        length = len(self.person_map) + len(self.family_map) + \
                 len(self.event_map) + len(self.source_map) + \
                 len(self.place_map) + len(self.media_map) + \
                 + len(self.repository_map)
        self.set_total(length)

        self.change_13 = int(time.time())

        # Person upgrade
        for handle in self.person_map.keys():
            info = self.person_map[handle]
            (new_info, note_handles) = self.convert_notes_13('Person', info)
            self.commit_13(new_info, PERSON_KEY, self.person_map, note_handles)
            self.update()

        # Family upgrade
        for handle in self.family_map.keys():
            info = self.family_map[handle]
            (new_info, note_handles) = self.convert_notes_13('Family', info)
            self.commit_13(new_info, FAMILY_KEY, self.family_map, note_handles)
            self.update()

        # Event upgrade
        for handle in self.event_map.keys():
            info = self.event_map[handle]
            (new_info, note_handles) = self.convert_notes_13('Event', info)
            self.commit_13(new_info, EVENT_KEY, self.event_map, note_handles)
            self.update()

        # Source upgrade
        for handle in self.source_map.keys():
            info = self.source_map[handle]
            (new_info, note_handles) = self.convert_notes_13('Source', info)
            self.commit_13(new_info, SOURCE_KEY, self.source_map, note_handles)
            self.update()

        # Place upgrade
        for handle in self.place_map.keys():
            info = self.place_map[handle]
            (new_info, note_handles) = self.convert_notes_13('Place', info)
            self.commit_13(new_info, PLACE_KEY, self.place_map, note_handles)
            self.update()

        # Media upgrade
        for handle in self.media_map.keys():
            info = self.media_map[handle]
            (new_info, note_handles) = self.convert_notes_13('MediaObject', info)
            self.commit_13(new_info, MEDIA_KEY, self.media_map, note_handles)
            self.update()

        # Repo upgrade
        for handle in self.repository_map.keys():
            info = self.repository_map[handle]
            (new_info, note_handles) = self.convert_notes_13('Repository', info)
            self.commit_13(new_info, REPOSITORY_KEY, 
                           self.repository_map, note_handles)
            self.update()

        if not self.UseTXN:
            self.person_map.sync()
            self.family_map.sync()
            self.event_map.sync()
            self.source_map.sync()
            self.place_map.sync()
            self.media_map.sync()
            self.repository_map.sync()
            self.note_map.sync()
            self.reference_map.sync()

        # Clean up after the upgrade: metadata and such
        if self.UseTXN:
            # Separate transaction to save metadata
            the_txn = self.env.txn_begin()
        else:
            the_txn = None
        self.metadata.put('version', 13, txn=the_txn)
        if self.UseTXN:
            the_txn.commit()
        else:
            self.metadata.sync()

        # Close nid_trans that we can open it again later
        self.nid_trans.close()

        # Rebuild secondary indices related to reference_map
        junk = db.DB(self.env)
        junk.remove(self.full_name, "reference_map_primary_map")
        self.reference_map_primary_map = db.DB(self.env)
        self.reference_map_primary_map.set_flags(db.DB_DUP)
        self.reference_map_primary_map.open(self.full_name, 
                                            "reference_map_primary_map", 
                                            db.DB_BTREE, flags=table_flags)
        self.reference_map.associate(self.reference_map_primary_map, 
                                     find_primary_handle, 
                                     table_flags)
        self.reference_map_primary_map.close()

        junk = db.DB(self.env)
        junk.remove(self.full_name, "reference_map_referenced_map")
        self.reference_map_referenced_map = db.DB(self.env)
        self.reference_map_referenced_map.set_flags(db.DB_DUP|db.DB_DUPSORT)
        self.reference_map_referenced_map.open(self.full_name, 
                                               "reference_map_referenced_map", 
                                               db.DB_BTREE, flags=table_flags)
        self.reference_map.associate(self.reference_map_referenced_map, 
                                     find_referenced_handle, 
                                     table_flags)
        self.reference_map_referenced_map.close()

        LOG.debug("Done upgrading to DB version 13")

    def commit_13(self,data_tuple,data_key_name,data_map, note_handles=None):
        """
        Commits the specified object to the data_map table in the database, 
        add a reference to each note handle.
        """
        handle = str(data_tuple[0])
        
        if self.UseTXN:
            the_txn = self.env.txn_begin()
        else:
            the_txn = None

        # Add all references
        for note_handle in note_handles:
            ref_key = str((handle, note_handle))
            ref_data = ((data_key_name, handle), (NOTE_KEY, note_handle), )
            self.reference_map.put(ref_key, ref_data, txn=the_txn)
        # Commit data itself
        data_map.put(handle, data_tuple, txn=the_txn)

        # Clean up
        if the_txn:
            the_txn.commit()

    def convert_notes_13(self, name, obj, nttype=NoteType._DEFAULT,private=False):
        """
        This is the function for conversion all notes in all objects
        and their child objects to the top-level notes and handle references.
        It calls itself recursively to get to the bottom of everything.
        The obj is the data tuple that is not serialized.

        This functions returns the following tuple:
                (converted_object, note_handles)
        where note_handles is the list containing the note handles to which
        the object and its children refer. These handles will be used to add
        the references to the reference_map. Every clause has to collect
        these and return the unique list of all such handles.

        This function also adds privacy of 'False' to LdsOrd instances.
        """

        if name == 'Note':
            # Special case: we are way down at the very bottom.
            # Create note, commit it, return a list with one handle.
            if isinstance(obj, tuple) and (len(obj) > 0) and \
                   ('strip' in dir(obj[0])) and (obj[0].strip()):
                # Some notes may be None, from early databases.
                (text, format) = obj
                handle = str(self.create_id())
                gramps_id = self.find_next_note_gramps_id()
                note_tuple = (handle, gramps_id, text, format, (nttype, '', ), 
                              self.change_13, (-1, '', ), private)
                self.commit_13(note_tuple, NOTE_KEY, self.note_map, [])
                new_obj = [handle]
                note_handles = [handle]
            else:
                new_obj = []
                note_handles = []
        elif name == 'RepoRef':
            (note, ref, call_number, media_type) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.REPOREF)
            # Add the privacy field with 'False' content
            new_obj = (note_list, ref, call_number, media_type, False)
        elif name == 'SourceRef':
            (date, priv, note, conf, ref, page, text) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.SOURCEREF, 
                                        private=priv)
            # Also we lose the text field and make it a note
            if text.strip():
                handle = str(self.create_id())
                gramps_id = self.find_next_note_gramps_id()
                note_tuple = (handle, gramps_id, text, Note.FLOWED,
                              (NoteType.SOURCE_TEXT, '', ), self.change_13,
                              (-1, '', ), priv)
                self.commit_13(note_tuple, NOTE_KEY, self.note_map, [])
                note_list += [handle]
            new_obj = (date, priv, note_list, conf, ref, page)
        elif name == 'Attribute':
            (priv, source_list, note, the_type, value) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.ATTRIBUTE, 
                                        private=priv)
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (priv, new_source_list, note_list, the_type, value)
        elif name == 'Address':
            (priv, source_list, note, date, loc) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.ADDRESS, 
                                        private=priv)
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (priv, new_source_list, note_list, date, loc)
        elif name == 'EventRef':
            (priv, note, attr_list, ref, role) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.EVENTREF, 
                                        private=priv)
            tuples = [self.convert_notes_13('Attribute', item)
                      for item in attr_list]
            new_attr_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (priv, note_list, new_attr_list, ref, role)
        elif name == 'ChildRef':
            (pri, source_list, note, ref, frel, mrel) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.CHILDREF, 
                                        private=pri)
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (pri, new_source_list, note_list, ref, frel, mrel)
        elif name == 'PersonRef':
            (priv, source_list, note, ref, rel) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.ASSOCIATION, 
                                        private=priv)
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (priv, new_source_list, note_list, ref, rel)
        elif name == 'MediaRef':
            (priv, source_list, note, attr_list, ref, rect) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.MEDIAREF, 
                                        private=priv)
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('Attribute', item)
                      for item in attr_list]
            new_attr_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (priv, new_source_list, note_list, new_attr_list,
                       ref, rect)
        elif name == 'Name':
            (priv, source_list, note, date,
             f, s, su, t, ty, p, pa, g, so, di, call) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.PERSONNAME, 
                                        private=priv)
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (priv, new_source_list, note_list, 
                       date, f, s, su, t, ty, p, pa, g, so, di, call)
        elif name == 'LdsOrd':
            (source_list, note, date, t, place, famc, temple, st) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.LDS)
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            # Add privacy 'False' here
            new_obj = (new_source_list, note_list, date, t, place,
                       famc, temple, st, False) 
        elif name == 'Event':
            (handle, gramps_id, the_type, date, description, place, 
             source_list, note, media_list, attr_list, 
             change, marker, priv) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.EVENT, 
                                        private=priv)
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('MediaRef', item)
                      for item in media_list]
            new_media_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('Attribute', item)
                      for item in attr_list]
            new_attr_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (handle, gramps_id, the_type, date, description, place, 
                       new_source_list, note_list, new_media_list,
                       new_attr_list, change, marker, priv)
        elif name == 'Family':
            (handle, gramps_id, fh, mh, child_ref_list, the_type,
             event_ref_list, media_list, attr_list, lds_list, source_list,
             note, change, marker, priv) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.FAMILY, 
                                        private=priv)
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('MediaRef', item)
                      for item in media_list]
            new_media_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('Attribute', item)
                      for item in attr_list]
            new_attr_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('ChildRef', item)
                      for item in child_ref_list]
            new_child_ref_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('EventRef', item)
                      for item in event_ref_list]
            new_event_ref_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('LdsOrd', item)
                      for item in lds_list]
            new_lds_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (handle, gramps_id, fh, mh, new_child_ref_list,
                       the_type, new_event_ref_list, new_media_list,
                       new_attr_list, new_lds_list, new_source_list, note_list, 
                       change, marker, priv)
        elif name == 'MediaObject':
            (handle, gramps_id, path, mime, desc, attr_list, source_list,
             note, change,date, marker, priv) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.MEDIA, 
                                        private=priv)
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('Attribute', item)
                      for item in attr_list]
            new_attr_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (handle, gramps_id, path, mime, desc, new_attr_list, 
                       new_source_list, note_list, change, date, marker, priv)
        elif name == 'Place':
            (handle, gramps_id, title, long, lat, main_loc, alt_loc, urls, 
             media_list, source_list, note, change, marker, priv) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.PLACE, 
                                        private=priv)
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('MediaRef', item)
                      for item in media_list]
            new_media_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (handle, gramps_id, title, long, lat, main_loc, alt_loc,
                       urls, new_media_list, new_source_list, note_list, 
                       change, marker, priv)
        elif name == 'Source':
            (handle, gramps_id, title, author, pubinfo, note, media_list, 
             abbrev, change, datamap, reporef_list, marker, priv) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.SOURCE, 
                                        private=priv)
            tuples = [self.convert_notes_13('MediaRef', item)
                      for item in media_list]
            new_media_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('RepoRef', item)
                      for item in reporef_list]
            new_reporef_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (handle, gramps_id, title, author, pubinfo, note_list, 
                       new_media_list, abbrev, change, datamap,
                       new_reporef_list, marker, priv)
        elif name == 'Repository':
            (handle, gramps_id, t, n, note, addr_list, urls,
             marker, priv) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.REPO, 
                                        private=priv)
            tuples = [self.convert_notes_13('Address', item)
                      for item in addr_list]
            new_addr_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            new_obj = (handle, gramps_id, t, n, note_list, new_addr_list,
                       urls, self.change_13, marker, priv)
        elif name == 'Person':
            (handle, gramps_id, gender, primary_name, alternate_names, 
             dri, bri, event_ref_list, fl, pfl, media_list, addr_list,
             attr_list, urls, lds_list, source_list, note, change, marker,
             priv,person_ref_list) = obj
            (note_list, note_handles) = self.convert_notes_13('Note', note, 
                                        nttype=NoteType.PERSON, 
                                        private=priv)
            (new_primary_name, nh) = self.convert_notes_13('Name',primary_name)
            note_handles += nh
            tuples = [self.convert_notes_13('Name', item)
                      for item in alternate_names]
            new_alternate_names = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('EventRef', item)
                      for item in event_ref_list]
            new_event_ref_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('MediaRef', item)
                      for item in media_list]
            new_media_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('Address', item)
                      for item in addr_list]
            new_addr_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('Attribute', item)
                      for item in attr_list]
            new_attr_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('LdsOrd', item)
                      for item in lds_list]
            new_lds_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('SourceRef', item)
                      for item in source_list]
            new_source_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]
            tuples = [self.convert_notes_13('PersonRef', item)
                      for item in person_ref_list]
            new_person_ref_list = [item[0] for item in tuples]
            note_handles += [item[1] for item in tuples]

            new_obj = (handle, gramps_id, gender, new_primary_name, 
                       new_alternate_names, dri, bri, new_event_ref_list, 
                       fl, pfl, new_media_list, new_addr_list, new_attr_list, 
                       urls, new_lds_list, new_source_list, note_list, 
                       change, marker, priv, new_person_ref_list)
        else:
            LOG.warn("could not convert_notes_13 %s %s", name, obj)
        # Return the required tuple
        return (new_obj, note_handles)
    
    def gramps_upgrade_14(self):
        """Upgrade database from version 13 to 14."""
        LOG.debug("Upgrading to DB version 14...")
        # This upgrade modifies notes and dates
        length = (len(self.note_map) + len(self.person_map) +
                  len(self.event_map) + len(self.family_map) +
                  len(self.repository_map) + len(self.media_map) +
                  len(self.place_map) + len(self.source_map))
        self.set_total(length)

        # ---------------------------------
        # Modify Notes
        # ---------------------------------
        # replace clear text with StyledText in Notes
        for handle in self.note_map.keys():
            note = self.note_map[handle]
            (junk_handle, gramps_id, text, format, note_type,
             change, marker, private) = note
            styled_text = (text, [])
            new_note = (handle, gramps_id, styled_text, format, note_type,
                        change, marker, private)
            the_txn = self.env.txn_begin()
            self.note_map.put(str(handle), new_note, txn=the_txn)
            the_txn.commit()
            self.update()

        # ---------------------------------
        # Modify Event
        # ---------------------------------
        # update dates with newyear
        for handle in self.event_map.keys():
            event = self.event_map[handle]
            (junk_handle, gramps_id, the_type, date, description, place, 
             source_list, note_list, media_list, attribute_list,
             change, marker, private) = event
            new_date = self.convert_date_14(date)
            new_source_list = self.new_source_list_14(source_list)
            new_media_list = self.new_media_list_14(media_list)
            new_attribute_list = self.new_attribute_list_14(attribute_list)
            new_event = (junk_handle, gramps_id, the_type, new_date,
                         description, place, new_source_list, note_list, 
                         new_media_list, new_attribute_list, change,marker,private)
            the_txn = self.env.txn_begin()
            self.event_map.put(str(handle), new_event, txn=the_txn)
            the_txn.commit()
            self.update()

        # ---------------------------------
        # Modify Person
        # ---------------------------------
        # update dates with newyear
        for handle in self.person_map.keys():
            person = self.person_map[handle]
            (junk_handle,        #  0
             gramps_id,          #  1
             gender,             #  2
             primary_name,       #  3
             alternate_names,    #  4
             death_ref_index,    #  5
             birth_ref_index,    #  6
             event_ref_list,     #  7
             family_list,        #  8
             parent_family_list, #  9
             media_list,         # 10
             address_list,       # 11
             attribute_list,     # 12
             urls,               # 13
             lds_ord_list,       # 14
             psource_list,       # 15
             pnote_list,         # 16
             change,             # 17
             marker,             # 18
             pprivate,           # 19
             person_ref_list,    # 20
             ) = person

            new_address_list = []
            for address in address_list:
                (privacy, asource_list, anote_list, date, location) = address
                new_date = self.convert_date_14(date)
                new_asource_list = self.new_source_list_14(asource_list)
                new_address_list.append((privacy, new_asource_list, anote_list, 
                                         new_date, location))
            new_ord_list = []
            for ldsord in lds_ord_list:
                (lsource_list, lnote_list, date, type, place,
                 famc, temple, status, lprivate) = ldsord
                new_date = self.convert_date_14(date)
                new_lsource_list = self.new_source_list_14(lsource_list)
                new_ord_list.append( (new_lsource_list, lnote_list, new_date, type, 
                                      place, famc, temple, status, lprivate))

            new_primary_name = self.convert_name_14(primary_name)

            new_alternate_names = [self.convert_name_14(name) for name 
                                   in alternate_names]
            
            new_media_list = self.new_media_list_14(media_list)
            new_psource_list = self.new_source_list_14(psource_list)
            new_attribute_list = self.new_attribute_list_14(attribute_list)

            new_person = (junk_handle,        #  0
                          gramps_id,          #  1
                          gender,             #  2
                          new_primary_name,       #  3
                          new_alternate_names,    #  4
                          death_ref_index,    #  5
                          birth_ref_index,    #  6
                          event_ref_list,     #  7
                          family_list,        #  8
                          parent_family_list, #  9
                          new_media_list,         # 10
                          new_address_list,       # 11
                          new_attribute_list,     # 12
                          urls,               # 13
                          new_ord_list,          # 14
                          new_psource_list,       # 15
                          pnote_list,         # 16
                          change,             # 17
                          marker,             # 18
                          pprivate,           # 19
                          person_ref_list,    # 20
                          )

            the_txn = self.env.txn_begin()
            self.person_map.put(str(handle), new_person, txn=the_txn)
            the_txn.commit()
            self.update()

        # ---------------------------------
        # Modify Family
        # ---------------------------------
        # update dates with newyear
        for handle in self.family_map.keys():
            family = self.family_map[handle]
            (junk_handle, gramps_id, father_handle, mother_handle,
             child_ref_list, the_type, event_ref_list, media_list,
             attribute_list, lds_seal_list, source_list, note_list,
             change, marker, private) = family
            new_media_list = self.new_media_list_14(media_list)
            new_source_list = self.new_source_list_14(source_list)
            new_attribute_list = self.new_attribute_list_14(attribute_list)
            new_seal_list = []
            for ldsord in lds_seal_list:
                (lsource_list, lnote_list, date, type, place,
                 famc, temple, status, lprivate) = ldsord
                new_date = self.convert_date_14(date)
                new_lsource_list = self.new_source_list_14(lsource_list)
                new_seal_list.append( (new_lsource_list, lnote_list, new_date, type, 
                                       place, famc, temple, status, lprivate))

            new_family = (junk_handle, gramps_id, father_handle, mother_handle,
                          child_ref_list, the_type, event_ref_list, new_media_list,
                          new_attribute_list, new_seal_list, new_source_list, note_list,
                          change, marker, private)
            the_txn = self.env.txn_begin()
            self.family_map.put(str(handle), new_family, txn=the_txn)
            the_txn.commit()
            self.update()

        # ---------------------------------
        # Modify Repository
        # ---------------------------------
        # update dates with newyear
        for handle in self.repository_map.keys():
            repository = self.repository_map[handle]
            # address
            (junk_handle, gramps_id, the_type, name, note_list,
             address_list, urls, change, marker, private) = repository

            new_address_list = []
            for address in address_list:
                (privacy, asource_list, anote_list, date, location) = address
                new_date = self.convert_date_14(date)
                new_asource_list = self.new_source_list_14(asource_list)
                new_address_list.append((privacy, new_asource_list, anote_list, 
                                         new_date, location))

            new_repository = (junk_handle, gramps_id, the_type, name, note_list,
                              new_address_list, urls, change, marker, private)

            the_txn = self.env.txn_begin()
            self.repository_map.put(str(handle), new_repository, txn=the_txn)
            the_txn.commit()
            self.update()

        # ---------------------------------
        # Modify Media
        # ---------------------------------
        for media_handle in self.media_map.keys():
            media = self.media_map[media_handle]
            (handle, gramps_id, path, mime, desc,
             attribute_list, source_list, note_list, change,
             date, marker, private) = media
            new_source_list = self.new_source_list_14(source_list)
            new_date = self.convert_date_14(date)
            new_media = (handle, gramps_id, path, mime, desc,
                         attribute_list, new_source_list, note_list, change,
                         new_date, marker, private)

            the_txn = self.env.txn_begin()
            self.media_map.put(str(handle), new_media, txn=the_txn)
            the_txn.commit()
            self.update()

        # ---------------------------------
        # Modify Place
        # ---------------------------------
        for place_handle in self.place_map.keys():
            place = self.place_map[place_handle]
            (handle, gramps_id, title, long, lat,
             main_loc, alt_loc, urls, media_list, source_list, note_list,
             change, marker, private) = place
            new_media_list = self.new_media_list_14(media_list)
            new_source_list = self.new_source_list_14(source_list)
            new_place = (handle, gramps_id, title, long, lat,
                         main_loc, alt_loc, urls, new_media_list, 
                         new_source_list, note_list, change, marker, private) 

            the_txn = self.env.txn_begin()
            self.place_map.put(str(handle), new_place, txn=the_txn)
            the_txn.commit()
            self.update()

        # ---------------------------------
        # Modify Source
        # ---------------------------------
        for source_handle in self.source_map.keys():
            source = self.source_map[source_handle]
            (handle, gramps_id, title, author,
             pubinfo, note_list, media_list,
             abbrev, change, datamap, reporef_list,
             marker, private) = source
            new_media_list = self.new_media_list_14(media_list)
            new_source = (handle, gramps_id, title, author,
                          pubinfo, note_list, new_media_list,
                          abbrev, change, datamap, reporef_list,
                          marker, private)

            the_txn = self.env.txn_begin()
            self.source_map.put(str(handle), new_source, txn=the_txn)
            the_txn.commit()
            self.update()

        # Bump up database version. Separate transaction to save metadata.
        the_txn = self.env.txn_begin()
        self.metadata.put('version', 14, txn=the_txn)
        the_txn.commit()

    def new_source_list_14(self, source_list):
        new_source_list = []
        for source in source_list:
            (date, private, note_list, confidence, ref, page) = source
            new_date = self.convert_date_14(date)
            new_source_list.append((new_date, private, note_list, confidence, ref, page))
        return new_source_list

    def new_attribute_list_14(self, attribute_list):
        new_attribute_list = []
        for attribute in attribute_list:
            (private, asource_list, note_list, the_type, value) = attribute
            new_asource_list = self.new_source_list_14(asource_list)
            new_attribute_list.append((private, new_asource_list, note_list, the_type, value))
        return new_attribute_list

    def new_media_list_14(self, media_list):
        # ---------------------------------
        # Event Media list
        # ---------------------------------
        new_media_list = []
        for media in media_list:
            (private, source_list, note_list,attribute_list,ref,role) = media
            new_source_list = self.new_source_list_14(source_list)
            new_attribute_list = self.new_attribute_list_14(attribute_list)
            new_media_list.append((private, new_source_list, note_list, new_attribute_list, ref, role))
        return new_media_list

    def convert_date_14(self, date):
        if date:
            (calendar, modifier, quality, dateval, text, sortval) = date
            return (calendar, modifier, quality, dateval, text, sortval, 0)
        else:
            return None

    def convert_name_14(self, name):
        (privacy, source_list, note_list, date, 
         first_name, surname, suffix, title,
         name_type, prefix, patronymic,
         group_as, sort_as, display_as, call) = name
        new_date = self.convert_date_14(date)
        new_source_list = self.new_source_list_14(source_list)
        return (privacy, new_source_list, note_list, new_date, 
                first_name, surname, suffix, title,
                name_type, prefix, patronymic,
                group_as, sort_as, display_as, call)

    def set_auto_remove(self):
        """
        BSDDB change log settings using new method with renamed attributes
        """
        if db.version() < (4, 7):
            # by the book: old method with old attribute
            self.env.set_flags(db.DB_LOG_AUTOREMOVE, 1)
        else: # look at python interface
            # TODO test with new version of pybsddb
            try:
                # try numeric compare, just first 2 digits
                # this won't work with something like "4.10a", but
                # hopefully they won't do that
                old_version = map(int, db.__version__.split(".",2)[:2]) < (4, 7)
            except:
                # fallback, weak string compare
                old_version = db.__version__ < "4.7"
            if old_version:
                # undocumented: old method with new attribute
                self.env.set_flags(db.DB_LOG_AUTO_REMOVE, 1)
            else:
                # by the book: new method with new attribute
                self.env.log_set_config(db.DB_LOG_AUTO_REMOVE, 1)

class BdbTransaction(Transaction):
    def __init__(self, msg, db, batch=False, no_magic=False):
        Transaction.__init__(self, msg, db)
        self.batch = batch
        self.no_magic = no_magic

def convert_name_10(name):
    # Names lost the "sname" attribute
    (privacy, source_list, note, date, first_name, surname, suffix, title, name_type, 
     prefix, patronymic, sname, group_as, sort_as, display_as, call) = name
    return (privacy, source_list, note, date, first_name, surname, suffix, title, 
            name_type, prefix, patronymic, group_as, sort_as, display_as, call)

def convert_address_11(addr):
    # addresses got location instead of city, ...
    (privacy, source_list, note, date, 
     city, state, country, postal, phone, street) = addr
    county = u''
    location_base = (street, city, county, state, country, postal, phone)
    return (privacy, source_list, note, date, location_base)

def convert_location_11(loc):
    (location_base, parish, county) = loc
    (city, state, country, postal, phone) = location_base
    street = u''
    new_location_base = (street, city, county, state, country, postal, phone)
    return (new_location_base, parish)

#-------------------------------------------------------------------------
#
# Importing data into the currently open database. 
#
#-------------------------------------------------------------------------
def importData(database, filename, callback=None, cl=0):
    other_database = GrampsBSDDB()

    # Since we don't want to modify the file being imported, 
    # we create new temp file into which we will copy the imported file
    orig_filename = os.path.normpath(filename)
    new_file_id, new_filename = tempfile.mkstemp()
    os.close(new_file_id)
    new_env_name = tempfile.mkdtemp()

    # determine old env dir and make db work with new env dir
    orig_env_name = other_database.make_env_name(orig_filename)
    other_database.make_env_name = lambda x: new_env_name

    # Copy data
    shutil.copyfile(orig_filename, new_filename)
    # Copy env if we need and if it exists
    if other_database.UseTXN and os.path.isdir(orig_env_name):
        shutil.rmtree(new_env_name)
        shutil.copytree(orig_env_name, new_env_name)

    try:
        other_database.load(new_filename, callback)
    except:
        if cl:
            LOG.warn("%s could not be opened. Exiting." % new_filename)
        else:
            import traceback
            traceback.print_exc()
            ErrorDialog(_("%s could not be opened") % new_filename)
        return

    if not other_database.version_supported():
        if cl:
            LOG.warn("Error: %s could not be opened.\n%s  Exiting." \
                  % (filename, 
                     _("The database version is not supported "
                       "by this version of Gramps.\n"\
                       "Please upgrade to the corresponding version "
                       "or use XML for porting data between different "
                       "database versions.")))
        else:
            ErrorDialog(_("%s could not be opened") % filename, 
                        _("The Database version is not supported "
                          "by this version of Gramps."))
        return

    # If other_database contains its custom name formats, 
    # we need to do tricks to remap the format numbers
    if len(other_database.name_formats) > 0:
        formats_map = remap_name_formats(database, other_database)
        name_displayer.set_name_format(database.name_formats)
        get_person = make_peron_name_remapper(other_database, formats_map)
    else:
        # No remapping necessary, proceed as usual
        get_person = other_database.get_person_from_handle

    # Prepare table and method definitions
    tables = {
        'Person' : {'table' :  database.person_map, 
                    'id_table' : database.id_trans, 
                    'add_obj' : database.add_person, 
                    'find_next_gramps_id' :database.find_next_person_gramps_id, 
                    'other_get_from_handle':
                    get_person, 
                    'other_table': other_database.person_map,                  
                    }, 
        'Family' : {'table' :  database.family_map, 
                    'id_table' : database.fid_trans, 
                    'add_obj' : database.add_family, 
                    'find_next_gramps_id' :database.find_next_family_gramps_id, 
                    'other_get_from_handle':
                    other_database.get_family_from_handle, 
                    'other_table': other_database.family_map,                  
                    }, 

        'Event' : {'table' :  database.event_map, 
                   'id_table' : database.eid_trans, 
                   'add_obj' : database.add_event, 
                   'find_next_gramps_id' : database.find_next_event_gramps_id, 
                   'other_get_from_handle':
                   other_database.get_event_from_handle, 
                   'other_table': other_database.event_map,                  
                    }, 
        'Source' : {'table' :  database.source_map, 
                    'id_table' : database.sid_trans, 
                    'add_obj' : database.add_source, 
                    'find_next_gramps_id': database.find_next_source_gramps_id, 
                    'other_get_from_handle':
                    other_database.get_source_from_handle, 
                    'other_table': other_database.source_map,                  
                    }, 
        'Place' : {'table' :  database.place_map, 
                   'id_table' : database.pid_trans, 
                   'add_obj' : database.add_place, 
                   'find_next_gramps_id' :database.find_next_place_gramps_id, 
                   'other_get_from_handle':
                   other_database.get_place_from_handle, 
                   'other_table': other_database.place_map,                  
                   }, 
        'Media' : {'table' :  database.media_map, 
                   'id_table' : database.oid_trans, 
                   'add_obj' : database.add_object, 
                   'find_next_gramps_id' : database.find_next_object_gramps_id, 
                   'other_get_from_handle':
                   other_database.get_object_from_handle, 
                   'other_table': other_database.media_map,                  
                   }, 
        'Repository' : {'table' :  database.repository_map, 
                        'id_table' : database.rid_trans, 
                        'add_obj' : database.add_repository, 
                        'find_next_gramps_id' :
                        database.find_next_repository_gramps_id, 
                        'other_get_from_handle':
                        other_database.get_repository_from_handle, 
                        'other_table': other_database.repository_map, 
                        }, 
        'Note' : {'table':  database.note_map, 
                  'id_table': database.nid_trans, 
                  'add_obj': database.add_note, 
                  'find_next_gramps_id': database.find_next_note_gramps_id, 
                  'other_get_from_handle':
                      other_database.get_note_from_handle, 
                  'other_table': other_database.note_map,                  
                  }, 
        }

    uc = UpdateCallback(callback)
    uc.set_total(len(tables.keys()))

    the_len = 0

    # Check for duplicate handles.
    for key in tables:
        table_dict = tables[key]
        table = table_dict['table']
        other_table = table_dict['other_table']
        msg = '%s handles in two databases overlap.' % key
        the_len += check_common_handles(table, other_table, msg)
        uc.update()
        
    # Proceed with preparing for import
    trans = database.transaction_begin("", batch=True)

    database.disable_signals()

    # copy all data from new_database to database, 
    # rename gramps IDs of first-class objects when conflicts are found
    uc.set_total(the_len)

    for key in tables:
        table_dict = tables[key]
        id_table = table_dict['id_table']
        add_obj = table_dict['add_obj']
        find_next_gramps_id = table_dict['find_next_gramps_id']
        other_table = table_dict['other_table']
        other_get_from_handle = table_dict['other_get_from_handle']
        import_table(id_table, add_obj, find_next_gramps_id, 
                     other_table, other_get_from_handle, trans, uc)

    # Copy bookmarks over:
    # we already know that there's no overlap in handles anywhere
    database.bookmarks.append_list(other_database.bookmarks.get())
    database.family_bookmarks.append_list(other_database.family_bookmarks.get())
    database.event_bookmarks.append_list(other_database.event_bookmarks.get())
    database.source_bookmarks.append_list(other_database.source_bookmarks.get())
    database.place_bookmarks.append_list(other_database.place_bookmarks.get())
    database.media_bookmarks.append_list(other_database.media_bookmarks.get())
    database.repo_bookmarks.append_list(other_database.repo_bookmarks.get())
    database.note_bookmarks.append_list(other_database.note_bookmarks.get())

    # Copy grouping table
    group_map = other_database.get_name_group_keys()
    name_len = len(group_map)
    if name_len > 0:
        for key in group_map:
            value = other_database.get_name_group_mapping(key)
            if database.has_name_group_key(key) :
                present = database.get_name_group_mapping(key)
                if not value == present:
                    msg = _("Your family tree groups name %(key)s together"
                            " with %(present)s, did not change this grouping to %(value)s") % {
                                'key' : key, 'present' : present, 'value' : value }
                    LOG.warn(msg)
            else:
                database.set_name_group_mapping(key, value)

    # close the other database and clean things up
    other_database.close()

    # Remove temp file and env dir
    os.unlink(new_filename)
    shutil.rmtree(new_env_name)
    
    database.transaction_commit(trans, _("Import database"))
    database.enable_signals()
    database.request_rebuild()

def check_common_handles(table, other_table, msg):
    # Check for duplicate handles. At the moment we simply exit here, 
    # before modifying any data. In the future we will need to handle
    # this better. How?
    handles = set(table.keys())
    other_handles = set(other_table.keys())
    if handles.intersection(other_handles):
        raise HandleError(msg)
    return len(other_handles)
    
def import_table(id_table, add_obj, find_next_gramps_id, 
                other_table, other_get_from_handle, trans, uc):

    for handle in other_table.keys():
        obj = other_get_from_handle(handle)
        
        # Then we check gramps_id for conflicts and change it if needed
        gramps_id = str(obj.gramps_id)
        if id_table.has_key(gramps_id):
            gramps_id = find_next_gramps_id()
            obj.gramps_id = gramps_id
        add_obj(obj, trans)
        uc.update()

def remap_name_formats(database, other_database):
    formats_map = {}
    taken_numbers = [num for (num, name, fmt_str, active)
                     in database.name_formats]
    for (number, name, fmt_str, act) in other_database.name_formats:
        if number in taken_numbers:
            new_number = -1
            while new_number in taken_numbers:
                new_number -= 1
            taken_numbers.append(new_number)
            formats_map[number] = new_number
        else:
            new_number = number
        database.name_formats.append((new_number, name, fmt_str, act))
    return formats_map

def remap_name(person, formats_map):
    for name in [person.primary_name] + person.alternate_names:
        try:
            name.sort_as = formats_map[name.sort_as]
        except KeyError:
            pass
        try:
            name.display_as = formats_map[name.display_as]
        except KeyError:
            pass

def make_peron_name_remapper(other_database, formats_map):
    def new_get_person(handle):
        person = other_database.get_person_from_handle(handle)
        remap_name(person, formats_map)
        return person
    return new_get_person
