#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2008  Donald N. Allingham
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
Provide the Berkeley DB (DBDir) database backend for GRAMPS.
This is used since GRAMPS version 3.0
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import cPickle as pickle
import os
import sys
import time
from types import InstanceType

from gettext import gettext as _
from bsddb import dbshelve, db
import logging

_LOG = logging.getLogger(".GrampsDb")

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from gen.lib import (GenderStats, Person, Family, Event, Place, Source, 
                     MediaObject, Repository, Note)
from gen.db import (GrampsDbBase, KEY_TO_CLASS_MAP, CLASS_TO_KEY_MAP, 
                    REFERENCE_KEY, Transaction)
from BasicUtils import UpdateCallback
from gen.db.cursor import GrampsCursor
from gen.db.exceptions import FileVersionError, FileVersionDeclineToUpgrade
import Errors
from QuestionDialog import QuestionDialog2

_MINVERSION = 9
_DBVERSION = 14

IDTRANS     = "person_id"
FIDTRANS    = "family_id"
PIDTRANS    = "place_id"
OIDTRANS    = "media_id"
EIDTRANS    = "event_id"
RIDTRANS    = "repo_id"
NIDTRANS    = "note_id"
SIDTRANS    = "source_id"
SURNAMES    = "surnames"
NAME_GROUP  = "name_group"
META        = "meta_data"

FAMILY_TBL  = "family"
PLACES_TBL  = "place"
SOURCES_TBL = "source"
MEDIA_TBL   = "media"
EVENTS_TBL  = "event"
PERSON_TBL  = "person"
REPO_TBL    = "repo"
NOTE_TBL    = "note"

REF_MAP     = "reference_map"
REF_PRI     = "primary_map"
REF_REF     = "referenced_map"

DBERRS      = (db.DBRunRecoveryError, db.DBAccessError, 
               db.DBPageNotFoundError, db.DBInvalidArgError)


def find_surname(key, data):
    return str(data[3][5])

def find_idmap(key, data):
    return str(data[1])

# Secondary database key lookups for reference_map table
# reference_map data values are of the form:
#   ((primary_object_class_name, primary_object_handle),
#    (referenced_object_class_name, referenced_object_handle))

def find_primary_handle(key, data):
    return str((data)[0][1])

def find_referenced_handle(key, data):
    return str((data)[1][1])

#-------------------------------------------------------------------------
#
# GrampsDBDirCursor
#
#-------------------------------------------------------------------------
class GrampsDBDirCursor(GrampsCursor):

    def __init__(self, source, txn=None):
        self.cursor = source.db.cursor(txn)
        self.source = source
        
    def first(self):
        d = self.cursor.first()
        if d:
            return (d[0], pickle.loads(d[1]))
        return None

    def next(self):
        d = self.cursor.next()
        if d:
            return (d[0], pickle.loads(d[1]))
        return None

    def close(self):
        self.cursor.close()

    def delete(self):
        self.cursor.delete()
        
    def get_length(self):
        return self.source.stat()['ndata']

#-------------------------------------------------------------------------
#
# GrampsDBDirAssocCursor
#
#-------------------------------------------------------------------------
class GrampsDBDirAssocCursor(GrampsCursor):

    def __init__(self, source, txn=None):
        self.cursor = source.cursor(txn)
        self.source = source
        
    def first(self):
        d = self.cursor.first()
        if d:
            return (d[0], pickle.loads(d[1]))
        return None

    def next(self):
        d = self.cursor.next()
        if d:
            return (d[0], pickle.loads(d[1]))
        return None

    def close(self):
        self.cursor.close()

    def delete(self):
        self.cursor.delete()
        
    def get_length(self):
        return self.source.stat()['ndata']

#-------------------------------------------------------------------------
#
# GrampsDBDirDupCursor
#
#-------------------------------------------------------------------------
class GrampsDBDirDupCursor(GrampsDBDirAssocCursor):
    """Cursor that includes handling for duplicate keys."""

    def set(self, key):
        return self.cursor.set(str(key))

    def next_dup(self):
        return self.cursor.next_dup()

#-------------------------------------------------------------------------
#
# GrampsDBDir
#
#-------------------------------------------------------------------------
class GrampsDBDir(GrampsDbBase, UpdateCallback):
    """
    GRAMPS database object. 
    
    This object is a base class for other objects.
    """

    def __init__(self):
        """Create a new GrampsDB."""
        
        GrampsDbBase.__init__(self)
        self.txn = None
        self.secondary_connected = False

    def __open_flags(self):
        return db.DB_CREATE | db.DB_AUTO_COMMIT

    def __open_table(self, file_name, table_name, dbtype=db.DB_HASH):
        dbmap = dbshelve.DBShelf(self.env)
        dbmap.db.set_pagesize(16384)

        fname = os.path.join(file_name, table_name + ".db")

        if self.readonly:
            dbmap.open(fname, table_name, dbtype, db.DB_RDONLY)
        else:
            dbmap.open(fname, table_name, dbtype, self.__open_flags(), 0666)
        return dbmap

    def all_handles(self, table):
        return table.keys(self.txn)
    
    def __log_error(self):
        mypath = os.path.join(self.get_save_path(),"need_recover")
        ofile = open(mypath, "w")
        ofile.close()
        try:
            clear_lock_file(self.get_save_path())
        except:
            pass

    def __get_cursor(self, table):
        try:
            return GrampsDBDirCursor(table, self.txn)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def get_person_cursor(self):
        return self.__get_cursor(self.person_map)

    def get_family_cursor(self):
        return self.__get_cursor(self.family_map)

    def get_event_cursor(self):
        return self.__get_cursor(self.event_map)

    def get_place_cursor(self):
        return self.__get_cursor(self.place_map)

    def get_source_cursor(self):
        return self.__get_cursor(self.source_map)

    def get_media_cursor(self):
        return self.__get_cursor(self.media_map)

    def get_repository_cursor(self):
        return self.__get_cursor(self.repository_map)

    def get_note_cursor(self):
        return self.__get_cursor(self.note_map)

    def __has_handle(self, table, handle):
        try:
            return table.get(str(handle), txn=self.txn) is not None
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)
        
    def has_person_handle(self, handle):
        """
        Return True if the handle exists in the current Person database.
        """
        return self.__has_handle(self.person_map, handle)

    def has_family_handle(self, handle):            
        """
        Return True if the handle exists in the current Family database.
        """
        return self.__has_handle(self.family_map, handle)

    def has_object_handle(self, handle):
        """
        Return True if the handle exists in the current MediaObjectdatabase.
        """
        return self.__has_handle(self.media_map, handle)

    def has_repository_handle(self, handle):
        """
        Return True if the handle exists in the current Repository database.
        """
        return self.__has_handle(self.repository_map, handle)

    def has_note_handle(self, handle):
        """
        Return True if the handle exists in the current Note database.
        """
        return self.__has_handle(self.note_map, handle)

    def has_event_handle(self, handle):
        """
        Return True if the handle exists in the current Event database.
        """
        return self.__has_handle(self.event_map, handle)

    def has_place_handle(self, handle):
        """
        Return True if the handle exists in the current Place database.
        """
        return self.__has_handle(self.place_map, handle)

    def has_source_handle(self, handle):
        """
        Return True if the handle exists in the current Source database.
        """
        return self.__has_handle(self.source_map, handle)

    def __get_raw_data(self, table, handle):
        try:
            return table.get(str(handle), txn=self.txn)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)
    
    def get_raw_person_data(self, handle):
        return self.__get_raw_data(self.person_map, handle)

    def get_raw_family_data(self, handle):
        return self.__get_raw_data(self.family_map, handle)

    def get_raw_object_data(self, handle):
        return self.__get_raw_data(self.media_map, handle)

    def get_raw_place_data(self, handle):
        return self.__get_raw_data(self.place_map, handle)

    def get_raw_event_data(self, handle):
        return self.__get_raw_data(self.event_map, handle)

    def get_raw_source_data(self, handle):
        return self.__get_raw_data(self.source_map, handle)

    def get_raw_repository_data(self, handle):
        return self.__get_raw_data(self.repository_map, handle)

    def get_raw_note_data(self, handle):
        return self.__get_raw_data(self.note_map, handle)

    # cursors for lookups in the reference_map for back reference
    # lookups. The reference_map has three indexes:
    # the main index: a tuple of (primary_handle, referenced_handle)
    # the primary_handle index: the primary_handle
    # the referenced_handle index: the referenced_handle
    # the main index is unique, the others allow duplicate entries.

    def get_reference_map_cursor(self):
        try:
            return GrampsDBDirAssocCursor(self.reference_map, self.txn)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def get_reference_map_primary_cursor(self):
        try:
            return GrampsDBDirDupCursor(self.reference_map_primary_map, 
                                        self.txn)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def get_reference_map_referenced_cursor(self):
        try:
            return GrampsDBDirDupCursor(self.reference_map_referenced_map, 
                                        self.txn)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    # These are overriding the GrampsDbBase's methods of saving metadata
    # because we now have txn-capable metadata table
    def set_default_person_handle(self, handle):
        try:
            return self.__set_default_person_handle(handle)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def __set_default_person_handle(self, handle):
        """Set the default Person to the passed instance."""
        if not self.readonly:
            # Start transaction
            the_txn = self.env.txn_begin()
            self.metadata.put('default', str(handle), txn=the_txn)
            the_txn.commit()
            self.emit('home-person-changed')

    def get_default_person(self):
        try:
            return self.__get_default_person()
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def __get_default_person(self):
        """Return the default Person of the database."""
        person = self.get_person_from_handle(self.get_default_handle())
        if person:
            return person
        elif (self.metadata) and (not self.readonly):
            # Start transaction
            the_txn = self.env.txn_begin()
            self.metadata.put('default', None, txn=the_txn)
            the_txn.commit()
        return None

    def set_mediapath(self, path):
        """Set the default media path for database, path should be utf-8."""
        if self.metadata and not self.readonly:
            # Start transaction
            the_txn = self.env.txn_begin()
            self.metadata.put('mediapath', path, txn=the_txn)
            the_txn.commit()

    def set_column_order(self, col_list, name):
        if self.metadata and not self.readonly: 
            # Start transaction
            the_txn = self.env.txn_begin()
            self.metadata.put(name, col_list, txn=the_txn)
            the_txn.commit()

    def version_supported(self):
        try:
            dbversion = self.metadata.get('version', default=0)
            return ((dbversion <= _DBVERSION) and (dbversion >= _MINVERSION))
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)
    
    def need_upgrade(self):
        try:
            dbversion = self.metadata.get('version', default=0)
            return not self.readonly and dbversion < _DBVERSION
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def load(self, name, callback, mode="w"):
        try:
            if self.__check_readonly(name):
                mode = "r"
            write_lock_file(name)
            return self.__load(name, callback, mode)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def __check_readonly(self, name):
        for base in [FAMILY_TBL, PLACES_TBL, SOURCES_TBL, MEDIA_TBL, 
                     EVENTS_TBL, PERSON_TBL, REPO_TBL, NOTE_TBL, REF_MAP, META]:
            path = os.path.join(name, base + ".db")
            if os.path.isfile(path) and not os.access(path, os.W_OK):
                return True
        return False

    def __load(self, name, callback, mode="w"):

        if self.db_is_open:
            self.close()

        self.readonly = mode == "r"

        if callback:
            callback(12)

        self.full_name = os.path.abspath(name)
        self.path = self.full_name
        self.brief_name = os.path.basename(name)

        self.env = db.DBEnv()
        self.env.set_cachesize(0, 0x4000000)         # 32MB

        # These env settings are only needed for Txn environment
        self.env.set_lk_max_locks(25000)
        self.env.set_lk_max_objects(25000)
        
        self.set_auto_remove()

        # The DB_PRIVATE flag must go if we ever move to multi-user setup
        env_flags = db.DB_CREATE | db.DB_PRIVATE |\
                    db.DB_INIT_MPOOL | db.DB_INIT_LOCK |\
                    db.DB_INIT_LOG | db.DB_INIT_TXN | db.DB_THREAD

        # As opposed to before, we always try recovery on databases
        env_flags = env_flags | db.DB_RECOVER

        # Environment name is now based on the filename
        env_name = name

        self.env.open(env_name, env_flags)
        self.env.txn_checkpoint()

        if callback:
            callback(25)
        self.metadata = self.__open_table(self.full_name, META)

        # If we cannot work with this DB version,
        # it makes no sense to go further
        if not self.version_supported():
            self.__close_early()

        self.family_map     = self.__open_table(self.full_name, FAMILY_TBL)
        self.place_map      = self.__open_table(self.full_name, PLACES_TBL)
        self.source_map     = self.__open_table(self.full_name, SOURCES_TBL)
        self.media_map      = self.__open_table(self.full_name, MEDIA_TBL)
        self.event_map      = self.__open_table(self.full_name, EVENTS_TBL)
        self.person_map     = self.__open_table(self.full_name, PERSON_TBL)
        self.repository_map = self.__open_table(self.full_name, REPO_TBL)
        self.note_map       = self.__open_table(self.full_name, NOTE_TBL)
        self.reference_map  = self.__open_table(self.full_name, REF_MAP,
                                                dbtype=db.DB_BTREE)
        if callback:
            callback(37)
  
        self.name_group = db.DB(self.env)
        self.name_group.set_flags(db.DB_DUP)
        if self.readonly:
            self.name_group.open(_mkname(self.full_name, NAME_GROUP), 
                                 NAME_GROUP, db.DB_HASH, flags=db.DB_RDONLY)
        else:
            self.name_group.open(_mkname(self.full_name, NAME_GROUP), 
                                 NAME_GROUP, db.DB_HASH, 
                                 flags=self.__open_flags())
        self.__load_metadata()

        gstats = self.metadata.get('gender_stats', default=None)

        if not self.readonly:
            # Start transaction
            the_txn = self.env.txn_begin()

            if gstats is None:
                # New database. Set up the current version.
                self.metadata.put('version', _DBVERSION, txn=the_txn)
            elif 'version' not in self.metadata:
                # Not new database, but the version is missing.
                # Use 0, but it is likely to fail anyway.
                self.metadata.put('version', 0, txn=the_txn)

            the_txn.commit()
            
        self.genderStats = GenderStats(gstats)

        # Here we take care of any changes in the tables related to new code.
        # If secondary indices change, then they should removed
        # or rebuilt by upgrade as well. In any case, the
        # self.secondary_connected flag should be set accordingly.
        
        if self.need_upgrade():
            if QuestionDialog2(_("Need to upgrade database!"), 
                               _("You cannot open this database "
                                 "without upgrading it.\n"
                                 "If you upgrade then you won't be able "
                                 "to use previous versions of GRAMPS.\n" 
                                 "You might want to make a backup copy "
                                 "first."), 
                               _("Upgrade now"), 
                               _("Cancel")).run():
                self.gramps_upgrade(callback)
            else:
                raise FileVersionDeclineToUpgrade()

        if callback:
            callback(50)

        if not self.secondary_connected:
            self.__connect_secondary()

        if callback:
            callback(75)

        self.open_undodb()
        self.db_is_open = True

        if callback:
            callback(87)
        
        # Re-set the undo history to a fresh session start
        self.undoindex = -1
        self.translist = [None] * len(self.translist)
        self.abort_possible = True
        self.undo_history_timestamp = time.time()

        return 1

    def open_undodb(self):
        """
        Override method from GrampsDbBase because in DIR setup we want the 
        undo database to be inside the dir.
        """
        if not self.readonly:
            self.undolog = os.path.join(self.full_name, "undo.db")
            self.undodb = db.DB()
            self.undodb.open(self.undolog, db.DB_RECNO, db.DB_CREATE)

    def load_from(self, other_database, filename, callback):
        try:
            self.load(filename, callback)
            from gen.utils import db_copy
            db_copy(other_database, self, callback)
            return 1
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def __load_metadata(self):
        # name display formats
        self.name_formats = self.metadata.get('name_formats', default=[])
        # upgrade formats if they were saved in the old way
        for format_ix in range(len(self.name_formats)):
            format = self.name_formats[format_ix]
            if len(format) == 3:
                format = format + (True,)
                self.name_formats[format_ix] = format
        
        # database owner
        try:
            owner_data = self.metadata.get('researcher')
            if owner_data:
                self.owner.unserialize(owner_data)
        except ImportError: #handle problems with pre-alpha 3.0
            pass
        
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

    def __connect_secondary(self):
        """
        Connect or creates secondary index tables.
        
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
        self.surnames.set_flags(db.DB_DUP | db.DB_DUPSORT)
        self.surnames.open(_mkname(self.full_name, SURNAMES), SURNAMES, 
                           db.DB_BTREE, flags=table_flags)

        self.id_trans = db.DB(self.env)
        self.id_trans.set_flags(db.DB_DUP)
        self.id_trans.open(_mkname(self.full_name, IDTRANS), IDTRANS,
                           db.DB_HASH, flags=table_flags)

        self.fid_trans = db.DB(self.env)
        self.fid_trans.set_flags(db.DB_DUP)
        self.fid_trans.open(_mkname(self.full_name, FIDTRANS), FIDTRANS,
                            db.DB_HASH, flags=table_flags)

        self.eid_trans = db.DB(self.env)
        self.eid_trans.set_flags(db.DB_DUP)
        self.eid_trans.open(_mkname(self.full_name, EIDTRANS), EIDTRANS,
                            db.DB_HASH, flags=table_flags)

        self.pid_trans = db.DB(self.env)
        self.pid_trans.set_flags(db.DB_DUP)
        self.pid_trans.open(_mkname(self.full_name, PIDTRANS), PIDTRANS,
                            db.DB_HASH, flags=table_flags)

        self.sid_trans = db.DB(self.env)
        self.sid_trans.set_flags(db.DB_DUP)
        self.sid_trans.open(_mkname(self.full_name, SIDTRANS), SIDTRANS,
                            db.DB_HASH, flags=table_flags)

        self.oid_trans = db.DB(self.env)
        self.oid_trans.set_flags(db.DB_DUP)
        self.oid_trans.open(_mkname(self.full_name, OIDTRANS), OIDTRANS,
                            db.DB_HASH, flags=table_flags)

        self.rid_trans = db.DB(self.env)
        self.rid_trans.set_flags(db.DB_DUP)
        self.rid_trans.open(_mkname(self.full_name, RIDTRANS), RIDTRANS,
                            db.DB_HASH, flags=table_flags)

        self.nid_trans = db.DB(self.env)
        self.nid_trans.set_flags(db.DB_DUP)
        self.nid_trans.open(_mkname(self.full_name, NIDTRANS), NIDTRANS,
                            db.DB_HASH, flags=table_flags)

        self.reference_map_primary_map = db.DB(self.env)
        self.reference_map_primary_map.set_flags(db.DB_DUP)
        self.reference_map_primary_map.open(
            _mkname(self.full_name, REF_PRI),
            REF_PRI, db.DB_BTREE, flags=table_flags)

        self.reference_map_referenced_map = db.DB(self.env)
        self.reference_map_referenced_map.set_flags(db.DB_DUP|db.DB_DUPSORT)
        self.reference_map_referenced_map.open(
            _mkname(self.full_name, REF_REF),
            REF_REF, db.DB_BTREE, flags=table_flags)

        if not self.readonly:
            self.person_map.associate(self.surnames, find_surname, table_flags)
            self.person_map.associate(self.id_trans, find_idmap, table_flags)
            self.family_map.associate(self.fid_trans, find_idmap, table_flags)
            self.event_map.associate(self.eid_trans, find_idmap,  table_flags)
            self.repository_map.associate(self.rid_trans, find_idmap,
                                          table_flags)
            self.note_map.associate(self.nid_trans, find_idmap, table_flags)
            self.place_map.associate(self.pid_trans,  find_idmap, table_flags)
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

    def rebuild_secondary(self, callback=None):
        try:
            self.__rebuild_secondary(callback)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def __rebuild_secondary(self, callback=None):
        if self.readonly:
            return

        table_flags = self.__open_flags()

        # remove existing secondary indices
        
        index = 1

        items = [
            ( self.id_trans,  IDTRANS ),
            ( self.surnames,  SURNAMES ),
            ( self.fid_trans, FIDTRANS ),
            ( self.pid_trans, PIDTRANS ),
            ( self.oid_trans, OIDTRANS ),
            ( self.eid_trans, EIDTRANS ),
            ( self.rid_trans, RIDTRANS ),
            ( self.nid_trans, NIDTRANS ),
            ( self.reference_map_primary_map, REF_PRI),
            ( self.reference_map_referenced_map, REF_REF),
            ]

        for (database, name) in items:
            database.close()
            env = db.DB(self.env)
            env.remove(_mkname(self.full_name, name), name)
            if callback:
                callback(index)
            index += 1

        if callback:
            callback(11)

        # Set flag saying that we have removed secondary indices
        # and then call the creating routine
        self.secondary_connected = False
        self.__connect_secondary()
        if callback:
            callback(12)

    def find_backlink_handles(self, handle, include_classes=None):
        try:
            return self.__find_backlink_handles(handle, include_classes)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def __find_backlink_handles(self, handle, include_classes=None):
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

        >       result_list = [i for i in find_backlink_handles(handle)]
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

    def delete_primary_from_reference_map(self, handle, transaction, txn=None):
        """
        Remove all references to the primary object from the reference_map.
        """

        primary_cur = self.get_reference_map_primary_cursor()

        try:
            ret = primary_cur.set(handle)
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

            main_key = (handle, pickle.loads(data)[1][1])
            
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
        # from the primary object 'obj' or any of its secondary objects.

        handle = obj.handle
        update = self.reference_map_primary_map.has_key(str(handle))

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
                    (CLASS_TO_KEY_MAP[ref_class_name], ref_handle),)
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
        Remove the reference specified by the key, preserving the change in 
        the passed transaction.
        """
        if not self.readonly:
            if transaction.batch:
                self.reference_map.delete(str(key), txn=txn)
            else:
                old_data = self.reference_map.get(str(key), txn=self.txn)
                transaction.add(REFERENCE_KEY, str(key), old_data, None)
                transaction.reference_del.append(str(key))

    def __add_reference(self, key, data, transaction, txn=None):
        """
        Add the reference specified by the key and the data, preserving the 
        change in the passed transaction.
        """

        if self.readonly or not key:
            return
        
        if transaction.batch:
            self.reference_map.put(str(key), data, txn=txn)
        else:
            transaction.add(REFERENCE_KEY, str(key), None, data)
            transaction.reference_add.append((str(key), data))

    def reindex_reference_map(self, callback):
        try:
            self.__reindex_reference_map(callback)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def __reindex_reference_map(self, callback):
        """
        Reindex all primary records in the database.
        
        This will be a slow process for large databases.
        """

        # First, remove the reference map and related tables
        self.reference_map_referenced_map.close()
        junk = db.DB(self.env)
        junk.remove(_mkname(self.full_name, REF_REF), REF_REF)
        callback(1)

        self.reference_map_primary_map.close()
        junk = db.DB(self.env)
        junk.remove(_mkname(self.full_name, REF_PRI), REF_PRI)
        callback(2)

        self.reference_map.close()
        junk = db.DB(self.env)
        junk.remove(_mkname(self.full_name, REF_MAP), REF_MAP)
        callback(3)

        # Open reference_map and primapry map
        self.reference_map  = self.__open_table(self.full_name, REF_MAP, 
                                                dbtype=db.DB_BTREE)
        
        open_flags = self.__open_flags()
        self.reference_map_primary_map = db.DB(self.env)
        self.reference_map_primary_map.set_flags(db.DB_DUP)
        self.reference_map_primary_map.open(
            _mkname(self.full_name, REF_PRI), REF_PRI,  db.DB_BTREE, 
            flags=open_flags)

        self.reference_map.associate(self.reference_map_primary_map,
                                     find_primary_handle, open_flags)

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
        callback(4)

        # Now we use the functions and classes defined above
        # to loop through each of the primary object tables.
        for primary_table_name in primary_tables.keys():
            
            cursor = primary_tables[primary_table_name]['cursor_func']()
            data = cursor.first()

            # Grab the real object class here so that the lookup does
            # not happen inside the cursor loop.
            class_func = primary_tables[primary_table_name]['class_func']
            while data:
                found_handle, val = data
                obj = class_func()
                obj.unserialize(val)

                the_txn = self.env.txn_begin()
                self.update_reference_map(obj, transaction, the_txn)
                if the_txn:
                    the_txn.commit()
                
                data = cursor.next()

            cursor.close()
        callback(5)
        self.transaction_commit(transaction, _("Rebuild reference map"))

        self.reference_map_referenced_map = db.DB(self.env)
        self.reference_map_referenced_map.set_flags(db.DB_DUP|db.DB_DUPSORT)
        self.reference_map_referenced_map.open(
            _mkname(self.full_name, REF_REF),
            REF_REF, db.DB_BTREE,flags=open_flags)
        self.reference_map.associate(self.reference_map_referenced_map,
                                     find_referenced_handle, open_flags)
        callback(6)

    def __close_metadata(self):
        if not self.readonly:
            # Start transaction
            the_txn = self.env.txn_begin()

            # name display formats
            self.metadata.put('name_formats', self.name_formats, txn=the_txn)
            
            # database owner
            owner_data = self.owner.serialize()
            self.metadata.put('researcher', owner_data, txn=the_txn)

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

            the_txn.commit()

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
        raise FileVersionError(
            _("The database version is not supported by this "
              "version of GRAMPS.\nPlease upgrade to the "
              "corresponding version or use XML for porting "
              "data between different database versions."))

    def close(self):
        try:
            self.__close()
            clear_lock_file(self.get_save_path())
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)
        except IOError:
            pass

    def __close(self):
        if not self.db_is_open:
            return

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
            the_txn = self.env.txn_begin()
            self.delete_primary_from_reference_map(handle, transaction,
                                                    txn=the_txn)
            data_map.delete(handle, txn=the_txn)
            if the_txn:
                the_txn.commit()
        else:
            self.delete_primary_from_reference_map(handle, transaction)
            old_data = data_map.get(handle, txn=self.txn)
            transaction.add(key, handle, old_data, None)
            del_list.append(handle)

    def del_person(self, handle):
        self.person_map.delete(str(handle), txn=self.txn)

    def del_source(self, handle):
        self.source_map.delete(str(handle), txn=self.txn)

    def del_repository(self, handle):
        self.repository_map.delete(str(handle), txn=self.txn)

    def del_note(self, handle):
        self.note_map.delete(str(handle), txn=self.txn)

    def del_place(self, handle):
        self.place_map.delete(str(handle), txn=self.txn)

    def del_media(self, handle):
        self.media_map.delete(str(handle), txn=self.txn)

    def del_family(self, handle):
        self.family_map.delete(str(handle), txn=self.txn)

    def del_event(self, handle):
        self.event_map.delete(str(handle), txn=self.txn)

    def set_name_group_mapping(self, name, group):
        """
        Make name group under the value of group.
        
        If group =None, the old grouping is deleted. 
        """
        try:
            self.__set_name_group_mapping(name, group)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)
            
    def __set_name_group_mapping(self, name, group):
        if not self.readonly:
            # Start transaction
            the_txn = self.env.txn_begin()

            name = str(name)
            data = self.name_group.get(name, txn=the_txn)
            if data is not None:
                self.name_group.delete(name, txn=the_txn)
            if group is not None:
                self.name_group.put(name, group, txn=the_txn)
            the_txn.commit()
            self.emit('person-rebuild')

    def build_surname_list(self):
        try:
            self.surname_list = list(set(self.surnames.keys()))
            self.sort_surname_list()
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def remove_from_surname_list(self, person):
        """
        Check whether there are persons with the same surname left in
        the database. 
        
        If not then we need to remove the name from the list.
        The function must be overridden in the derived class.
        """
        name = str(person.get_primary_name().get_surname())
        try:
            if self.surnames.keys().count(name) == 1:
                self.surname_list.remove(unicode(name))
        except ValueError:
            pass
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def __get_obj_from_gramps_id(self, val, tbl, class_init, prim_tbl):
        try:
            if tbl.has_key(str(val)):
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
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def get_person_from_gramps_id(self, val):
        """
        Find a Person in the database from the passed gramps' ID.
        
        If no such Person exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.id_trans, Person,
                                             self.person_map)

    def get_family_from_gramps_id(self, val):
        """
        Find a Family in the database from the passed gramps' ID.
        
        If no such Family exists, None is return.
        """
        return self.__get_obj_from_gramps_id(val, self.fid_trans, Family,
                                             self.family_map)
    
    def get_event_from_gramps_id(self, val):
        """
        Find an Event in the database from the passed gramps' ID.
        
        If no such Family exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.eid_trans, Event,
                                             self.event_map)

    def get_place_from_gramps_id(self, val):
        """
        Find a Place in the database from the passed gramps' ID.
        
        If no such Place exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.pid_trans, Place,
                                             self.place_map)

    def get_source_from_gramps_id(self, val):
        """
        Find a Source in the database from the passed gramps' ID.
        
        If no such Source exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.sid_trans, Source,
                                              self.source_map)

    def get_object_from_gramps_id(self, val):
        """
        Find a MediaObject in the database from the passed gramps' ID.
        
        If no such MediaObject exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.oid_trans, MediaObject,
                                              self.media_map)

    def get_repository_from_gramps_id(self, val):
        """
        Find a Repository in the database from the passed gramps' ID.
        
        If no such Repository exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.rid_trans, Repository,
                                              self.repository_map)

    def get_note_from_gramps_id(self, val):
        """
        Find a Note in the database from the passed gramps' ID.
        
        If no such Note exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.nid_trans, Note,
                                              self.note_map)

    def commit_base(self, obj, data_map, key, update_list, add_list,
                      transaction, change_time):
        """
        Commit the specified object to the database, storing the changes as 
        part of the transaction.
        """
        if self.readonly or not obj or not obj.handle:
            return 

        if change_time:
            obj.change = int(change_time)
        else:
            obj.change = int(time.time())
        handle = str(obj.handle)
        
        if transaction.batch:
            the_txn = self.env.txn_begin()
            self.update_reference_map(obj, transaction, txn=the_txn)
            data_map.put(handle, obj.serialize(), txn=the_txn)
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
                _LOG.error("Failed to get from handle", exc_info=True)
        if data:
            newobj = class_type()
            newobj.unserialize(data)
            return newobj
        return None

    def find_from_handle(self, handle, transaction, class_type, dmap, add_func):
        """
        Find a object of class_type in the database from the passed handle.
        
        If no object exists, a new object is added to the database.
        
        @return: Returns a tuple, first the object, second a bool which is True
                 if the object is new
        @rtype: tuple
        """
        obj = class_type()
        handle = str(handle)
        new = True
        if handle in dmap:
            data = dmap.get(handle, txn=self.txn)
            obj.unserialize(data)
            #references create object with id None before object is really made
            if obj.gramps_id is not None:
                new = False
        else:
            obj.set_handle(handle)
            add_func(obj, transaction)
        return obj, new

    def transaction_begin(self, msg="", batch=False, no_magic=False):
        try:
            return self.__transaction_begin(msg, batch, no_magic)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def __transaction_begin(self, msg="", batch=False, no_magic=False):
        """
        Create a new Transaction tied to the current UNDO database. 
        
        The transaction has no effect until it is committed using the 
        transaction_commit function of the this database object.
        """

        if batch:
            # A batch transaction does not store the commits
            # Aborting the session completely will become impossible.
            self.abort_possible = False
            # Undo is also impossible after batch transaction
            self.undoindex = -1
            self.translist = [None] * len(self.translist)
        transaction = BdbTransaction(msg, self.undodb, batch, no_magic)
        if transaction.batch:
            self.env.txn_checkpoint()
            if db.version() < (4, 7):
                self.env.set_flags(db.DB_TXN_NOSYNC, 1)      # async txn

            if self.secondary_connected and not transaction.no_magic:
                # Disconnect unneeded secondary indices
                self.surnames.close()
                junk = db.DB(self.env)
                junk.remove(_mkname(self.full_name, SURNAMES), SURNAMES)

                self.reference_map_referenced_map.close()
                junk = db.DB(self.env)
                junk.remove(_mkname(self.full_name, REF_REF), REF_REF)
            
        return transaction

    def transaction_commit(self, transaction, msg):
        try:
            self.__transaction_commit(transaction, msg)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def __transaction_commit(self, transaction, msg):

        # Start BSD DB transaction -- DBTxn
        self.txn = self.env.txn_begin()

        GrampsDbBase.transaction_commit(self, transaction, msg)

        for (key, data) in transaction.reference_add:
            self.reference_map.put(str(key), data, txn=self.txn)

        for key in transaction.reference_del:
            self.reference_map.delete(str(key), txn=self.txn)

        # Commit BSD DB transaction -- DBTxn
        self.txn.commit()
        if transaction.batch:
            self.env.txn_checkpoint()
            if db.version() < (4, 7):
                self.env.set_flags(db.DB_TXN_NOSYNC, 0)      # sync txn

            if not transaction.no_magic:
                # create new secondary indices to replace the ones removed
                open_flags = self.__open_flags()
                dupe_flags = db.DB_DUP|db.DB_DUPSORT

                self.surnames = db.DB(self.env)
                self.surnames.set_flags(dupe_flags)
                self.surnames.open(
                    _mkname(self.full_name, "surnames"),
                    'surnames', db.DB_BTREE,flags=open_flags)
                self.person_map.associate(self.surnames, find_surname,
                                          open_flags)
            
                self.reference_map_referenced_map = db.DB(self.env)
                self.reference_map_referenced_map.set_flags(dupe_flags)
                self.reference_map_referenced_map.open(
                    _mkname(self.full_name, REF_REF),
                    REF_REF, db.DB_BTREE,flags=open_flags)
                self.reference_map.associate(self.reference_map_referenced_map,
                                             find_referenced_handle, open_flags)

            # Only build surname list after surname index is surely back
            self.build_surname_list()

        self.txn = None

    def undo(self, update_history=True):
        try:
            self.txn = self.env.txn_begin()
            status = GrampsDbBase.undo(self, update_history)
            if status:
                self.txn.commit()
            else:
                self.txn.abort()
            self.txn = None
            return status
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def redo(self, update_history=True):
        try:
            self.txn = self.env.txn_begin()
            status = GrampsDbBase.redo(self, update_history)
            if status:
                self.txn.commit()
            else:
                self.txn.abort()
            self.txn = None
            return status
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def undo_reference(self, data, handle):
        try:
            if data is None:
                self.reference_map.delete(handle, txn=self.txn)
            else:
                self.reference_map.put(handle, data, txn=self.txn)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def undo_data(self, data, handle, db_map, signal_root):
        try:
            if data is None:
                self.emit(signal_root + '-delete', ([handle],))
                db_map.delete(handle, txn=self.txn)
            else:
                ex_data = db_map.get(handle, txn=self.txn)
                if ex_data:
                    signal = signal_root + '-update'
                else:
                    signal = signal_root + '-add'
                db_map.put(handle, data, txn=self.txn)
                self.emit(signal, ([handle],))
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def gramps_upgrade(self, callback=None):
        UpdateCallback.__init__(self, callback)
        
        version = self.metadata.get('version', default=_MINVERSION)

        t = time.time()

        if version < 14:
            self.gramps_upgrade_14()

        print "Upgrade time:", int(time.time()-t), "seconds"

    def gramps_upgrade_14(self):
        """Upgrade database from version 13 to 14."""
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
            new_person_ref_list = self.new_person_ref_list_14(person_ref_list)

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
                          new_person_ref_list,    # 20
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
            new_child_ref_list = self.new_child_ref_list_14(child_ref_list)
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
                          new_child_ref_list, the_type, event_ref_list, new_media_list,
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

    def new_person_ref_list_14(self, person_ref_list):
        new_person_ref_list = []
        for person_ref in person_ref_list:
            (private, source_list, note_list, ref, rel) = person_ref
            new_source_list = self.new_source_list_14(source_list)
            new_person_ref_list.append((private, new_source_list, note_list, ref, rel))
        return new_person_ref_list

    def new_child_ref_list_14(self, child_ref_list):
        new_child_ref_list = []
        for data in child_ref_list:
            (private, source_list, note_list, ref, frel, mrel) = data
            new_source_list = self.new_source_list_14(source_list)
            new_child_ref_list.append((private, new_source_list, note_list, ref, frel, mrel))
        return new_child_ref_list

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

    def write_version(self, name):
        """Write version number for a newly created DB."""
        full_name = os.path.abspath(name)

        self.env = db.DBEnv()
        self.env.set_cachesize(0, 0x4000000)         # 32MB

        # These env settings are only needed for Txn environment
        self.env.set_lk_max_locks(25000)
        self.env.set_lk_max_objects(25000)

        # clean up unused logs
        self.set_auto_remove()

        # The DB_PRIVATE flag must go if we ever move to multi-user setup
        env_flags = db.DB_CREATE | db.DB_PRIVATE |\
                    db.DB_INIT_MPOOL | db.DB_INIT_LOCK |\
                    db.DB_INIT_LOG | db.DB_INIT_TXN | db.DB_THREAD

        # As opposed to before, we always try recovery on databases
        env_flags = env_flags | db.DB_RECOVER

        # Environment name is now based on the filename
        env_name = name

        self.env.open(env_name, env_flags)
        self.env.txn_checkpoint()

        self.metadata  = self.__open_table(full_name, META)
        
        the_txn = self.env.txn_begin()
        self.metadata.put('version', _DBVERSION, txn=the_txn)
        the_txn.commit()
        
        self.metadata.close()
        self.env.close()
        
#-------------------------------------------------------------------------
#
# BdbTransaction
#
#-------------------------------------------------------------------------
class BdbTransaction(Transaction):
    def __init__(self, msg, db, batch=False, no_magic=False):
        Transaction.__init__(self, msg, db, batch, no_magic)
        self.reference_del = []
        self.reference_add = []

def _mkname(path, name):
    return os.path.join(path, name + ".db")

def clear_lock_file(name):
    try:
        os.unlink(os.path.join(name, "lock"))
    except OSError:
        return

def write_lock_file(name):
    if not os.path.isdir(name):
        os.mkdir(name)
    f = open(os.path.join(name, "lock"), "w")
    if os.name == 'nt':
        text = os.environ['USERNAME']
    else:
        host = os.uname()[1]
        # An ugly workaround for os.getlogin() issue with Konsole
        try:
            user = os.getlogin()
        except:
            user = os.environ.get('USER')
        text = "%s@%s" % (user, host)
    # Save only the username and host, so the massage can be
    # printed with correct locale in DbManager.py when a lock is found
    f.write(text)
    f.close()

if __name__ == "__main__":

    import sys
    
    d = GrampsDBDir()
    d.load(sys.argv[1], lambda x: x)

    c = d.get_person_cursor()
    data = c.first()
    while data:
        person = Person(data[1])
        print data[0], person.get_primary_name().get_name(),
        data = c.next()
    c.close()

    print d.surnames.keys()
