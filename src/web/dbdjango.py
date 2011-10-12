# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009         Douglas S. Blank <doug.blank@gmail.com>
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
#

""" Implements a Db interface """

#------------------------------------------------------------------------
#
# Gramps Modules
#
#------------------------------------------------------------------------
import cPickle
import base64
import web
import gen
from gen.db import DbReadBase, DbWriteBase
from gen.db import (PERSON_KEY,
                    FAMILY_KEY,
                    SOURCE_KEY,
                    EVENT_KEY,
                    MEDIA_KEY,
                    PLACE_KEY,
                    REPOSITORY_KEY,
                    NOTE_KEY)
from web.libdjango import DjangoInterface

# Example for running a report:
# ------------------------------
# from cli.plug import run_report
# from django.conf import settings
# import web.settings as default_settings
# try:
#     settings.configure(default_settings)
# except:
#     pass
# import dbdjango
# db = dbdjango.DbDjango()
# run_report(db, "ancestor_report", off="txt", of="ar.txt", pid="I0363")

# Imports for importing a file:
import DbState
from cli.grampscli import CLIManager
from gen.plug import BasePluginManager
import os

def import_file(db, filename, callback):
    """
    Import a file (such as a GEDCOM file) into the given db.

    >>> import_file(DbDjango(), "/home/user/Untitled_1.ged", lambda a: a)
    """
    dbstate = DbState.DbState()
    climanager = CLIManager(dbstate, False) # do not load db_loader
    climanager.do_reg_plugins()
    pmgr = BasePluginManager.get_instance()
    (name, ext) = os.path.splitext(os.path.basename(filename))
    format = ext[1:].lower()
    import_list = pmgr.get_reg_importers()
    for pdata in import_list:
        if format == pdata.extension:
            mod = pmgr.load_plugin(pdata)
            if not mod:
                for name, error_tuple in pmgr.get_fail_list():
                    etype, exception, traceback = error_tuple
                    print "ERROR:", name, exception
                return False
            import_function = getattr(mod, pdata.import_function)
            db.step = 0
            import_function(db, filename, callback)
            db.step = 1
            import_function(db, filename, callback)
            return True
    return False

class Cursor(object):
    def __init__(self, model, func):
        self.model = model
        self.func = func
    def __enter__(self):
        return self
    def __iter__(self):
        return self.__next__()
    def __next__(self):
        for item in self.model.all():
            yield (item.handle, self.func(item))
    def __exit__(self, *args, **kwargs):
        pass
    def iter(self):
        for item in self.model.all():
            yield (item.handle, self.func(item))
        yield None

class DbDjango(DbWriteBase, DbReadBase):
    """
    A Gramps Database Backend. This replicates the grampsdb functions.
    """

    def __init__(self):
        DbReadBase.__init__(self)
        DbWriteBase.__init__(self)
        self.dji = DjangoInterface()
        self.readonly = False
        self.db_is_open = True
        self.name_formats = range(4)
        self.bookmarks = []
        self.family_bookmarks = []
        self.event_bookmarks = []
        self.place_bookmarks = []
        self.source_bookmarks = []
        self.repo_bookmarks = []
        self.media_bookmarks = []
        self.note_bookmarks = []
        self.event_prefix = "E%04s"
        # ----------------------------------
        self.id_trans  = {}
        self.fid_trans = {}
        self.pid_trans = {}
        self.sid_trans = {}
        self.oid_trans = {}
        self.rid_trans = {}
        self.nid_trans = {}
        self.eid_trans = {}
        self.env = None
        self.person_map = {}
        self.family_map = {}
        self.place_map  = {}
        self.source_map = {}
        self.repository_map  = {}
        self.note_map = {}
        self.media_map  = {}
        self.event_map  = {}
        self.metadata   = {}
        self.name_group = {}
        self.undo_callback = None
        self.redo_callback = None
        self.undo_history_callback = None
        self.modified   = 0


    def get_researcher(self):
        obj = gen.lib.Name()
        return obj

    def get_event_from_handle(self, handle):
        obj = gen.lib.Event()
        obj.unserialize(self.dji.get_event(self.dji.Event.get(handle=handle)))
        return obj

    def get_family_from_handle(self, handle): 
        #print "get_family_from_handle", handle
        family = self.dji.Family.get(handle=handle)
        obj = self.make_family(family)
        return obj

    def get_family_from_gramps_id(self, gramps_id):
        #print "get_family_from_id", gramps_id
        try:
            family = self.dji.Family.get(gramps_id=gramps_id)
        except:
            return None
        obj = self.make_family(family)
        return obj

    def get_person_from_handle(self, handle):
        #print "get_person_from_handle", handle
        try:
            person = self.dji.Person.select_related().get(handle=handle)
        except:
            return None
        return self.make_person(person)

    def make_family(self, family):
        if family.cache:
            data = cPickle.loads(base64.decodestring(family.cache))
            obj = gen.lib.Family.create(data)
        else:
            data = self.dji.get_family(family)
            obj = gen.lib.Family.create(data)
        return obj

    def make_person(self, person):
        if person.cache:
            data = cPickle.loads(base64.decodestring(person.cache))
            obj = gen.lib.Person.create(data)
        else:
            data = self.dji.get_person(person)
            obj = gen.lib.Person.create(data)
        return obj

    def get_place_from_handle(self, handle):
        try:
            dji_obj = self.dji.Place.get(handle=handle)
        except:
            dji_obj = None
        if dji_obj:
            tuple_obj = self.dji.get_place(dji_obj)
            if tuple_obj:
                obj = gen.lib.Place()
                obj.unserialize(tuple_obj)
                return obj
        return None

    def get_source_from_handle(self, handle):
        obj = gen.lib.Source()
        obj.unserialize(self.dji.get_source(self.dji.Source.get(handle=handle)))
        return obj

    def get_note_from_handle(self, handle):
        obj = gen.lib.Note()
        obj.unserialize(self.dji.get_note(self.dji.Note.get(handle=handle)))
        return obj

    def get_object_from_handle(self, handle):
        obj = gen.lib.MediaObject()
        obj.unserialize(self.dji.get_media(self.dji.Media.get(handle=handle)))
        return obj

    def get_media_object_handles(self):
        return [media.handle for media in self.dji.Media.all()]

    def get_person_handles(self, sort_handles=False):
        return [person.handle for person in self.dji.Person.all()]

    def get_default_person(self):
        return None

    def iter_people(self):
        return (self.get_person_from_handle(person.handle) 
                for person in self.dji.Person.all())

    def iter_person_handles(self):
        return (person.handle for person in self.dji.Person.all())

    def get_tag_handles(self, sort_handles=False):
        return []

    def iter_families(self):
        return (self.get_family_from_handle(family.handle) 
                for family in self.dji.Family.all())

    def iter_family_handles(self):
        return (family.handle for family in self.dji.Family.all())

    def get_person_from_gramps_id(self, gramps_id):
        #print "get_person_from_gramps_id", gramps_id
        match_list = self.dji.Person.filter(gramps_id=gramps_id)
        if match_list.count() > 0:
            return self.make_person(match_list[0])
        else:
            return None

    def get_number_of_people(self):
        return self.dji.Person.count()

    def get_number_of_families(self):
        return self.dji.Family.count()

    def get_number_of_notes(self):
        return self.dji.Note.count()

    def get_number_of_sources(self):
        return self.dji.Source.count()

    def get_number_of_media_objects(self):
        return self.dji.Media.count()

    def get_number_of_repositories(self):
        return self.dji.Repository.count()

    def get_place_cursor(self):
        return Cursor(self.dji.Place, self.dji.get_place).iter()

    def get_person_cursor(self):
        return Cursor(self.dji.Person, self.dji.get_person).iter()

    def get_family_cursor(self):
        return Cursor(self.dji.Family, self.dji.get_family).iter()

    def get_events_cursor(self):
        return Cursor(self.dji.Event, self.dji.get_event).iter()

    def get_source_cursor(self):
        return Cursor(self.dji.Source, self.dji.get_source).iter()

    def has_person_handle(self, handle):
        return self.dji.Person.filter(handle=handle).count() == 1

    def has_family_handle(self, handle):
        return self.dji.Family.filter(handle=handle).count() == 1

    def has_source_handle(self, handle):
        return self.dji.Source.filter(handle=handle).count() == 1

    def has_repository_handle(self, handle):
        return self.dji.Repository.filter(handle=handle).count() == 1

    def has_note_handle(self, handle):
        return self.dji.Note.filter(handle=handle).count() == 1

    def has_place_handle(self, handle):
        return self.dji.Place.filter(handle=handle).count() == 1

    def get_raw_person_data(self, handle):
        return self.dji.get_person(self.dji.Person.get(handle=handle))

    def get_raw_family_data(self, handle):
        return self.dji.get_family(self.dji.Family.get(handle=handle))

    def get_raw_source_data(self, handle):
        return self.dji.get_source(self.dji.Source.get(handle=handle))

    def get_raw_repository_data(self, handle):
        return self.dji.get_repository(self.dji.Repository.get(handle=handle))

    def get_raw_note_data(self, handle):
        return self.dji.get_note(self.dji.Note.get(handle=handle))

    def get_raw_place_data(self, handle):
        return self.dji.get_place(self.dji.Place.get(handle=handle))

    def add_person(self, person, trans, set_gid=True):
        pass
        # if self.step == 0:
        #     if not person.handle:
        #         person.handle = Utils.create_id()
        #     if not person.gramps_id:
        #         person.gramps_id = self.find_next_person_gramps_id()
        #     self.lookup[person.gramps_id] = person.handle
        #     if self.dji.Person.filter(handle=person.handle).count() == 0:
        #         print "add_person:", person.handle
        #         self.dji.add_person(person.serialize())
        # else:
        #     print "update_person:", person.handle
        #     person.handle = self.lookup[person.gramps_id]
        #     self.dji.add_person_detail(person.serialize())

    def add_family(self, family, trans, set_gid=True):
        pass
        # if self.step == 0:
        #     if not family.handle:
        #         family.handle = Utils.create_id()
        #     if not family.gramps_id:
        #         family.gramps_id = self.find_next_family_gramps_id()
        #     self.lookup[family.gramps_id] = family.handle
        #     if self.dji.Family.filter(handle=family.handle).count() == 0:
        #         print "add_family:", family.handle
        #         self.dji.add_family(family.serialize())
        # else:
        #     family.handle = self.lookup[family.gramps_id]
        #     self.dji.add_family_detail(family.serialize())

    def add_source(self, source, trans, set_gid=True):
        pass
        #print "add_source:", source.handle
        #if not source.handle:
        #    source.handle = Utils.create_id()
        #    self.dji.add_source(source.serialize())
        #self.dji.add_source_detail(source.serialize())

    def add_repository(self, repository, trans, set_gid=True):
        pass
        #print "add_repository:", repository.handle
        #if not repository.handle:
        #    repository.handle = Utils.create_id()
        #    self.dji.add_repository(repository.serialize())
        #self.dji.add_repository_detail(repository.serialize())

    def add_note(self, note, trans, set_gid=True):
        pass
        #print "add_note:", note.handle
        #if not note.handle:
        #    note.handle = Utils.create_id()
        #    self.dji.add_note(note.serialize())
        #self.dji.add_note_detail(note.serialize())

    def add_place(self, place, trans, set_gid=True):
        print "add_place:", place.handle
        pass

    def add_event(self, event, trans, set_gid=True):
        pass
        #print "add_event:", event.handle
        #if not event.handle:
        #    event.handle = Utils.create_id()
        #    self.dji.add_event(event.serialize())
        #self.dji.add_event_detail(event.serialize())

    def commit_person(self, person, trans, change_time=None):
        pass
        #print "commit_person:", person.handle
        #self.add_person(person, trans)

    def commit_family(self, family, trans, change_time=None):
        pass
        #print "commit_family:", family.handle
        #self.add_family(family, trans)

    def commit_source(self, source, trans, change_time=None):
        pass
        #print "commit_source:", source.handle
        #self.add_source(source, change_time)

    def commit_repository(self, repository, trans, change_time=None):
        pass
        #print "commit_repository:", repository.handle
        #self.add_repository(repository, change_time)

    def commit_note(self, note, trans, change_time=None):
        pass
        #print "commit_note:", note.handle
        #self.add_note(note, change_time)

    def commit_place(self, place, trans, change_time=None):
        print "commit_place:", place.handle
        if self.dji.Place.filter(handle=place.handle).count() == 0:
            self.dji.add_place(place.serialize())
        self.dji.add_place_detail(place.serialize())

    def commit_event(self, event, change_time=None):
        pass
        #print "commit_event:", event.handle
        #self.add_event(event, change_time)

    # def find_family_from_handle(self, handle, trans):
    #     obj = gen.lib.Family()
    #     results = self.dji.Family.filter(handle=handle)
    #     if results.count() == 0:
    #         obj.handle = handle
    #         new = True
    #     else:
    #         data = self.dji.get_family(results[0])
    #         obj.unserialize(data)
    #         new = False
    #     return obj, new


    def get_gramps_ids(self, obj_key):
        key2table = {
            PERSON_KEY:     self.id_trans, 
            FAMILY_KEY:     self.fid_trans, 
            SOURCE_KEY:     self.sid_trans, 
            EVENT_KEY:      self.eid_trans, 
            MEDIA_KEY:      self.oid_trans, 
            PLACE_KEY:      self.pid_trans, 
            REPOSITORY_KEY: self.rid_trans, 
            NOTE_KEY:       self.nid_trans, 
            }

        table = key2table[obj_key]
        return table.keys()

    def get_gramps_ids(self, obj_key):
        print "object key:", obj_key
        return []

    def transaction_begin(self, transaction):
        return 

    def disable_signals(self):
        pass

    def set_researcher(self, owner):
        pass

    def find_next_place_gramps_id(self):
        return "P0"
