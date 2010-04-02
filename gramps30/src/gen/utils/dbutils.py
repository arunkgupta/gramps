#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2006 Donald N. Allingham
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

from gettext import gettext as _
import copy

import gen.lib
from BasicUtils import UpdateCallback


def delete_person_from_database(db, person, trans):
    """
    Deletes a person from the database, cleaning up all associated references.
    """

    # clear out the default person if the person is the default person
    if db.get_default_person() == person:
        db.set_default_person_handle(None)

    # loop through the family list 
    for family_handle in [ f for f in person.get_family_handle_list() if f ]:

        family = db.get_family_from_handle(family_handle)

        if person.get_handle() == family.get_father_handle():
            family.set_father_handle(None)
        else:
            family.set_mother_handle(None)

        if not family.get_father_handle() and not family.get_mother_handle() and \
                not family.get_child_ref_list():
            db.remove_family(family_handle, trans)
        else:
            db.commit_family(family, trans)

    for family_handle in person.get_parent_family_handle_list():
        if family_handle:
            family = db.get_family_from_handle(family_handle)
            family.remove_child_handle(person.get_handle())
            db.commit_family(family, trans)

    handle = person.get_handle()

    person_list = [
        item[1] for item in
        db.find_backlink_handles(handle,['Person'])]

    for phandle in person_list:
        p = db.get_person_from_handle(phandle)
        p.remove_handle_references('Person', [handle])
        db.commit_person(p, trans)
    db.remove_person(handle, trans)

def remove_family_relationships(db, family_handle, trans=None):
    family = db.get_family_from_handle(family_handle)

    if trans == None:
        need_commit = True
        trans = db.transaction_begin()
    else:
        need_commit = False

    for phandle in [ family.get_father_handle(),
                     family.get_mother_handle()]:
        if phandle:
            person = db.get_person_from_handle(phandle)
            person.remove_family_handle(family_handle)
            db.commit_person(person, trans)

    for ref in family.get_child_ref_list():
        phandle = ref.ref
        person = db.get_person_from_handle(phandle)
        person.remove_parent_family_handle(family_handle)
        db.commit_person(person, trans)

    db.remove_family(family_handle, trans)
    
    if need_commit:
        db.transaction_commit(trans, _("Remove Family"))

def remove_parent_from_family(db, person_handle, family_handle, trans=None):
    """
    Remove a person as either the father or mother of a family,
    deleting the family if it becomes empty.
    """
    person = db.get_person_from_handle(person_handle)
    family = db.get_family_from_handle(family_handle)

    if trans == None:
        need_commit = True
        trans = db.transaction_begin()
    else:
        need_commit = False

    person.remove_family_handle(family_handle)
    if family.get_father_handle() == person_handle:
        family.set_father_handle(None)
        msg = _("Remove father from family")
    elif family.get_mother_handle() == person_handle:
        msg = _("Remove mother from family")
        family.set_mother_handle(None)

    child_list = family.get_child_ref_list()
    if (not family.get_father_handle() and not family.get_mother_handle() and
        len(child_list) <= 1):
        db.remove_family(family_handle, trans)
        if child_list:
            child = db.get_person_from_handle(child_list[0].ref)
            child.remove_parent_family_handle(family_handle)
            db.commit_person(child, trans)
    else:
        db.commit_family(family, trans)
    db.commit_person(person, trans)
    
    if need_commit:
        db.transaction_commit(trans,msg)

def remove_child_from_family(db, person_handle, family_handle, trans=None):
    """
    Remove a person as a child of the family, deleting the family if
    it becomes empty.
    """
    person = db.get_person_from_handle(person_handle)
    family = db.get_family_from_handle(family_handle)
    person.remove_parent_family_handle(family_handle)
    family.remove_child_handle(person_handle)

    if trans == None:
        need_commit = True
        trans = db.transaction_begin()
    else:
        need_commit = False
        
    child_list = family.get_child_ref_list()
    if (not family.get_father_handle() and not family.get_mother_handle() and
        len(child_list) <= 1):
        db.remove_family(family_handle, trans)
        if child_list:
            child = db.get_person_from_handle(child_list[0].ref)
            child.remove_parent_family_handle(family_handle)
            db.commit_person(child, trans)
    else:
        db.commit_family(family, trans)
    db.commit_person(person, trans)
    
    if need_commit:
        db.transaction_commit(trans,_("Remove child from family"))

def marriage_from_eventref_list(db, eventref_list):
    for eventref in eventref_list:
        event = db.get_event_from_handle(eventref.ref)
        if int(event.get_type()) == gen.lib.EventType.MARRIAGE:
            return event
    else:
        return None

def add_child_to_family(db, family, child,
                        mrel=gen.lib.ChildRefType(),
                        frel=gen.lib.ChildRefType(),
                        trans=None):

    cref = gen.lib.ChildRef()
    cref.ref = child.handle
    cref.set_father_relation(frel)
    cref.set_mother_relation(mrel)
    
    family.add_child_ref(cref)
    child.add_parent_family_handle(family.handle)

    if trans == None:
        need_commit = True
        trans = db.transaction_begin()
    else:
        need_commit = False

    db.commit_family(family,trans)
    db.commit_person(child,trans)

    if need_commit:
        db.transaction_commit(trans, _('Add child to family') )


def get_total(db):
    person_len = db.get_number_of_people()
    family_len = db.get_number_of_families()
    event_len = db.get_number_of_events()
    source_len = db.get_number_of_sources()
    place_len = db.get_number_of_places()
    repo_len = db.get_number_of_repositories()
    obj_len = db.get_number_of_media_objects()
        
    return person_len + family_len + event_len + \
           place_len + source_len + obj_len + repo_len
        
def db_copy(from_db,to_db,callback):
    """
    Copy all data in from_db into to_db.

    Both databases must be loaded.
    It is assumed that to_db is an empty database,
    so no care is taken to prevent handle collision or merge data.
    """

    uc = UpdateCallback(callback)
    uc.set_total(get_total(from_db))
    
    tables = {
        'Person': {'cursor_func': from_db.get_person_cursor,
                   'add_func' : to_db.add_person,
                   },
        'Family': {'cursor_func': from_db.get_family_cursor,
                   'add_func' : to_db.add_family,
                   },
        'Event': {'cursor_func': from_db.get_event_cursor,
                  'add_func' : to_db.add_event,
                  },
        'Place': {'cursor_func': from_db.get_place_cursor,
                  'add_func' : to_db.add_place,
                  },
        'Source': {'cursor_func': from_db.get_source_cursor,
                   'add_func' : to_db.add_source,
                   },
        'MediaObject': {'cursor_func': from_db.get_media_cursor,
                        'add_func' : to_db.add_object,
                        },
        'Repository': {'cursor_func': from_db.get_repository_cursor,
                       'add_func' : to_db.add_repository,
                       },
        'Note': {'cursor_func': from_db.get_note_cursor,
                 'add_func': to_db.add_note,
                 },
        }

    # Start batch transaction to use async TXN and other tricks
    trans = to_db.transaction_begin("", batch=True)

    for table_name in tables.keys():
        cursor_func = tables[table_name]['cursor_func']
        add_func = tables[table_name]['add_func']

        cursor = cursor_func()
        item = cursor.first()
        while item:
            (handle,data) = item
            exec('obj = gen.lib.%s()' % table_name)
            obj.unserialize(data)
            add_func(obj,trans)
            item = cursor.next()
            uc.update()
        cursor.close()

    # Copy name grouping
    group_map = from_db.get_name_group_keys()
    for key in group_map:
        value = from_db.get_name_group_mapping(key)
        to_db.set_name_group_mapping(key, value)

    # Commit batch transaction: does nothing, except undoing the tricks
    to_db.transaction_commit(trans, "")

    # Copy bookmarks over:
    # we already know that there's no overlap in handles anywhere
    to_db.bookmarks        = copy.deepcopy(from_db.bookmarks)
    to_db.family_bookmarks = copy.deepcopy(from_db.family_bookmarks)
    to_db.event_bookmarks  = copy.deepcopy(from_db.event_bookmarks)
    to_db.source_bookmarks = copy.deepcopy(from_db.source_bookmarks)
    to_db.place_bookmarks  = copy.deepcopy(from_db.place_bookmarks)
    to_db.media_bookmarks  = copy.deepcopy(from_db.media_bookmarks)
    to_db.repo_bookmarks   = copy.deepcopy(from_db.repo_bookmarks)
    to_db.note_bookmarks   = copy.deepcopy(from_db.note_bookmarks)

    # Copy name formats
    to_db.name_formats = from_db.name_formats
    
    # Copy db owner
    to_db.owner = from_db.owner
    
    # Copy other selected metadata
    if from_db.get_mediapath() is not None:
        to_db.set_mediapath(from_db.get_mediapath())
    
def set_birth_death_index(db, person):
    birth_ref_index = -1
    death_ref_index = -1
    event_ref_list = person.get_event_ref_list()
    for index in range(len(event_ref_list)):
        ref = event_ref_list[index]
        event = db.get_event_from_handle(ref.ref)
        if (int(event.get_type()) == gen.lib.EventType.BIRTH) \
               and (int(ref.get_role()) == gen.lib.EventRoleType.PRIMARY) \
               and (birth_ref_index == -1):
            birth_ref_index = index
        elif (int(event.get_type()) == gen.lib.EventType.DEATH) \
                 and (int(ref.get_role()) == gen.lib.EventRoleType.PRIMARY) \
                 and (death_ref_index == -1):
            death_ref_index = index

    person.birth_ref_index = birth_ref_index
    person.death_ref_index = death_ref_index
