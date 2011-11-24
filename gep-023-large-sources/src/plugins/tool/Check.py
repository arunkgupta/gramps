#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
# Copyright (C) 2011       Tim G Lyons
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

"""Tools/Database Repair/Check and Repair Database"""

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
from __future__ import with_statement
import os
import sys
import cStringIO

from gen.ggettext import gettext as _
from gen.ggettext import ngettext
from collections import defaultdict

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
log = logging.getLogger(".CheckRepair")

#-------------------------------------------------------------------------
#
# gtk modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import gen.lib
from gen.db import DbTxn
import Utils
from gui.utils import ProgressMeter
import ManagedWindow

from gui.plug import tool
from QuestionDialog import OkDialog, MissingMediaDialog
from gen.display.name import displayer as _nd
from glade import Glade

# table for handling control chars in notes.
# All except 09, 0A, 0D are replaced with space.
strip_dict = dict.fromkeys(range(9)+range(11,13)+range(14, 32),  u" ")

#-------------------------------------------------------------------------
#
# Low Level repair
#
#-------------------------------------------------------------------------
def low_level(db):
    """
    This is a low-level repair routine.

    It is fixing DB inconsistencies such as duplicates.
    Returns a (status, name) tuple.
    The boolean status indicates the success of the procedure.
    The name indicates the problematic table (empty if status is True).
    """

    for the_map in [('Person', db.person_map),
                    ('Family', db.family_map),
                    ('Event', db.event_map),
                    ('Place', db.place_map),
                    ('Source', db.source_map),
                    ('Media', db.media_map),
                    ('Repository', db.repository_map),
                    ('Note', db.note_map)]:

        print "Low-level repair: table: %s" % the_map[0]
        if _table_low_level(db, the_map[1]):
            print "Done."
        else:
            print "Low-level repair: Problem with table: %s" % the_map[0]
            return (False, the_map[0])
    return (True, '')


def _table_low_level(db,table):
    """
    Low level repair for a given db table.
    """

    handle_list = table.keys()
    handle_dict = defaultdict(int)
    for key in handle_list:
        handle_dict[key] += 1

    if len(handle_dict) == len(handle_list):
        print "    No duplicates found for this table"
        return True
    dup_handles = [handle for handle, count in handle_dict.items()
                        if count > 1] 
#    import gen.db
    from gen.db import DbBsddbAssocCursor
    table_cursor = DbBsddbAssocCursor(table)
    for handle in dup_handles:
        print "    Duplicates found for handle: %s" % handle
        try:
            ret = table_cursor.set(handle)
        except:
            print "    Failed setting initial cursor."
            return False

        for count in range(handle_list.count(handle)-1):
            try:
                table_cursor.delete()
                print "    Successfully deleted duplicate #%d" % (count+1)
            except:
                print "    Failed deleting duplicate."
                return False

            try:
                ret = table_cursor.next_dup()
            except:
                print "    Failed moving the cursor."
                return False

    table_cursor.close()
    table.sync()
    return True

def cross_table_duplicates(db):
    """
    Function to find the presence of identical handles that occur in different
    database tables.

    Assumes there are no intable duplicates, see low_level function.

    :param db: the database to check
    :type db: :class:`gen.db.read.DbBsddbRead`
    :returns: the presence of cross table duplicate handles
    :rtype: bool
    """
    total_nr_handles = 0
    all_handles = set([])
    for the_map in [db.person_map, db.family_map, db.event_map, db.place_map,
            db.source_map, db.media_map, db.repository_map, db.note_map]:
        handle_list = the_map.keys()
        total_nr_handles += len(handle_list)
        all_handles.update(handle_list)
    return total_nr_handles > len(all_handles)

#-------------------------------------------------------------------------
#
# runTool
#
#-------------------------------------------------------------------------
class Check(tool.BatchTool):
    def __init__(self, dbstate, uistate, options_class, name, callback=None):

        tool.BatchTool.__init__(self, dbstate, options_class, name)
        if self.fail:
            return

        cli = uistate is None

        if self.db.readonly:
            # TODO: split plugin in a check and repair part to support
            # checking of a read only database
            return

        # The low-level repair is bypassing the transaction mechanism.
        # As such, we run it before starting the transaction.
        # We only do this for the dbdir backend.
        if self.db.__class__.__name__ == 'DbBsddb':
            low_level(self.db)
            if cross_table_duplicates(self.db):
                Report(uistate, _(
                    "Your family tree contains cross table duplicate handles.\n "
                    "This is bad and can be fixed by making a backup of your\n"
                    "family tree and importing that backup in an empty family\n"
                    "tree. The rest of the checking is skipped, the Check and\n"
                    "Repair tool should be run anew on this new family tree."), cli)
                return

        with DbTxn(_("Check Integrity"), self.db, batch=True) as trans:
            self.db.disable_signals()
            checker = CheckIntegrity(dbstate, uistate, trans)
            checker.fix_encoding()
            checker.fix_ctrlchars_in_notes()
            checker.cleanup_missing_photos(cli)
            checker.cleanup_deleted_name_formats()
            
            prev_total = -1
            total = 0
        
            #start with empty objects, broken links can be corrected below then
            checker.cleanup_empty_objects()
            while prev_total != total:
                prev_total = total
                
                checker.check_for_broken_family_links()
                checker.check_parent_relationships()
                checker.cleanup_empty_families(cli)
                checker.cleanup_duplicate_spouses()
    
                total = checker.family_errors()

            checker.check_events()
            checker.check_person_references()
            checker.check_family_references()
            checker.check_place_references()
            checker.check_citation_references()
            # FIXME: CITATION should also check source references
            checker.check_media_references()
            checker.check_repo_references()
            checker.check_note_references()
        self.db.enable_signals()
        self.db.request_rebuild()

        errs = checker.build_report(uistate)
        if errs:
            Report(uistate, checker.text.getvalue(), cli)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class CheckIntegrity(object):
    
    def __init__(self, dbstate, uistate, trans):
        self.db = dbstate.db
        self.trans = trans
        self.bad_photo = []
        self.replaced_photo = []
        self.removed_photo = []
        self.empty_family = []
        self.broken_links = []
        self.duplicate_links = []
        self.broken_parent_links = []
        self.fam_rel = []
        self.invalid_events = []
        self.invalid_birth_events = []
        self.invalid_death_events = []
        self.invalid_person_references = []
        self.invalid_family_references = []
        self.invalid_place_references = []
        self.invalid_citation_references = []
        self.invalid_repo_references = []
        self.invalid_media_references = []
        self.invalid_note_references = []
        self.invalid_dates = []
        self.removed_name_format = []
        self.empty_objects = defaultdict(list)
        self.progress = ProgressMeter(_('Checking Database'),'')

    def family_errors(self):
        return (len(self.broken_parent_links) +
               len(self.broken_links) +
               len(self.empty_family) +
               len(self.duplicate_links)
               )

    def cleanup_deleted_name_formats(self):
        """
        Permanently remove deleted name formats from db.
        
        When user deletes custom name format those are not removed only marked
        as "inactive". This method does the cleanup of the name format table,
        as well as fixes the display_as, sort_as values for each Name in the db.

        """
        self.progress.set_pass(_('Looking for invalid name format references'),
                               self.db.get_number_of_people())
        
        deleted_name_formats = [number for (number, name, fmt_str,act)
                                in self.db.name_formats if not act]
        
        # remove the invalid references from all Name objects
        for person_handle in self.db.get_person_handles():
            person = self.db.get_person_from_handle(person_handle)

            p_changed = False
            name = person.get_primary_name()
            if name.get_sort_as() in deleted_name_formats:
                name.set_sort_as(gen.lib.Name.DEF)
                p_changed = True
            if name.get_display_as() in deleted_name_formats:
                name.set_display_as(gen.lib.Name.DEF)
                p_changed = True
            if p_changed:
                person.set_primary_name(name)

            a_changed = False
            name_list = []
            for name in person.get_alternate_names():
                if name.get_sort_as() in deleted_name_formats:
                    name.set_sort_as(gen.lib.Name.DEF)
                    a_changed = True
                if name.get_display_as() in deleted_name_formats:
                    name.set_display_as(gen.lib.Name.DEF)
                    a_changed = True
                name_list.append(name)
            if a_changed:
                person.set_alternate_names(name_list)
            
            if p_changed or a_changed:
                self.db.commit_person(person, self.trans)
                self.removed_name_format.append(person_handle)
                
            self.progress.step()

        # update the custom name name format table
        for number in deleted_name_formats:
            _nd.del_name_format(number)
        self.db.name_formats = _nd.get_name_format(only_custom=True,
                                                           only_active=False)            

    def cleanup_duplicate_spouses(self):

        self.progress.set_pass(_('Looking for duplicate spouses'),
                               self.db.get_number_of_people())

        for handle in self.db.person_map.keys():
            value = self.db.person_map[handle]
            p = gen.lib.Person(value)
            splist = p.get_family_handle_list()
            if len(splist) != len(set(splist)):
                new_list = []
                for value in splist:
                    if value not in new_list:
                        new_list.append(value)
                        self.duplicate_links.append((handle, value))
                p.set_family_handle_list(new_list)
                self.db.commit_person(p, self.trans)
            self.progress.step()

    def fix_encoding(self):
        self.progress.set_pass(_('Looking for character encoding errors'),
                               self.db.get_number_of_media_objects())
        for handle in self.db.media_map.keys():
            data = self.db.media_map[handle]
            if not isinstance(data[2], unicode) or not isinstance(data[4], unicode):
                obj = self.db.get_object_from_handle(handle)
                obj.path = Utils.fix_encoding( obj.path)
                obj.desc = Utils.fix_encoding( obj.desc)
                self.db.commit_media_object(obj, self.trans)
            # Once we are here, fix the mime string if not str
            if not isinstance(data[3], str):
                obj = self.db.get_object_from_handle(handle)
                try:
                    if data[3] == str(data[3]):
                        obj.mime = str(data[3])
                    else:
                        obj.mime = ""
                except:
                    obj.mime = ""
                self.db.commit_media_object(obj, self.trans)
            self.progress.step()

    def fix_ctrlchars_in_notes(self):
        self.progress.set_pass(_('Looking for ctrl characters in notes'),
                               self.db.get_number_of_notes())
        for handle in self.db.note_map.keys():
            note = self.db.get_note_from_handle(handle)
            stext = note.get_styledtext()
            old_text = unicode(stext)
            new_text = old_text.translate(strip_dict)
            if old_text != new_text:
                print "Note=", self.db.note_map[handle][1], " had control character"
            # Commit only if ctrl char found.
                note.set_styledtext(gen.lib.StyledText(text=new_text, tags=stext.get_tags()))
                self.db.commit_note(note, self.trans)
            self.progress.step()

    def check_for_broken_family_links(self):
        # Check persons referenced by the family objects

        fhandle_list = self.db.get_family_handles()
        self.progress.set_pass(_('Looking for broken family links'),
                               len(fhandle_list) +
                               self.db.get_number_of_people()
                              )
        
        for family_handle in fhandle_list:
            family = self.db.get_family_from_handle(family_handle)
            father_handle = family.get_father_handle()
            mother_handle = family.get_mother_handle()
            if father_handle:
                father = self.db.get_person_from_handle(father_handle)
                if not father:
                    # The person referenced by the father handle does not exist in the database
                    family.set_father_handle(None)
                    self.db.commit_family(family, self.trans)
                    self.broken_parent_links.append((father_handle, family_handle))
                    father_handle = None
            if mother_handle:
                mother = self.db.get_person_from_handle(mother_handle)
                if not mother:
                    # The person referenced by the mother handle does not exist in the database
                    family.set_mother_handle(None)
                    self.db.commit_family(family, self.trans)
                    self.broken_parent_links.append((mother_handle, family_handle))
                    mother_handle = None

            if father_handle and father and \
                    family_handle not in father.get_family_handle_list():
                # The referenced father has no reference back to the family
                self.broken_parent_links.append((father_handle, family_handle))
                father.add_family_handle(family_handle)
                self.db.commit_person(father, self.trans)
                
            if mother_handle and mother and \
                    family_handle not in mother.get_family_handle_list():
                # The referenced mother has no reference back to the family
                self.broken_parent_links.append((mother_handle, family_handle))
                mother.add_family_handle(family_handle)
                self.db.commit_person(mother, self.trans)
            for child_ref in family.get_child_ref_list():
                child_handle = child_ref.ref
                child = self.db.get_person_from_handle(child_handle)
                if child:
                    if child_handle in [father_handle, mother_handle]:
                        # The child is one of the parents: impossible
                        # Remove such child from the family
                        family.remove_child_ref(child_ref)
                        self.db.commit_family(family, self.trans)
                        self.broken_links.append((child_handle, family_handle))
                        continue
                    if family_handle == child.get_main_parents_family_handle():
                        continue
                    if family_handle not in \
                           child.get_parent_family_handle_list():
                        # The referenced child has no reference to the family
                        family.remove_child_ref(child_ref)
                        self.db.commit_family(family, self.trans)
                        self.broken_links.append((child_handle, family_handle))
                else:
                    # The person referenced by the child handle
                    # does not exist in the database
                    family.remove_child_ref(child_ref)
                    self.db.commit_family(family, self.trans)
                    self.broken_links.append((child_handle, family_handle))

            new_ref_list = []
            new_ref_handles = []
            replace = False
            for child_ref in family.get_child_ref_list():
                child_handle = child_ref.ref
                if child_handle in new_ref_handles:
                    replace = True
                else:
                    new_ref_list.append(child_ref)
                    new_ref_handles.append(child_handle)

            if replace:
                family.set_child_ref_list(new_ref_list)
                self.db.commit_family(family, self.trans)

            self.progress.step()
            
        # Check persons membership in referenced families
        for person_handle in self.db.get_person_handles():
            person = self.db.get_person_from_handle(person_handle)

            phandle_list = person.get_parent_family_handle_list()
            new_list = list(set(phandle_list))
            if len(phandle_list) != len(new_list):
                person.set_parent_family_handle_list(new_list)
                self.db.commit_person(person, self.trans)

            for par_family_handle in person.get_parent_family_handle_list():
                family = self.db.get_family_from_handle(par_family_handle)
                if not family:
                    person.remove_parent_family_handle(par_family_handle)
                    self.db.commit_person(person, self.trans)
                    continue
                for child_handle in [child_ref.ref for child_ref
                                     in family.get_child_ref_list()]:
                    if child_handle == person_handle:
                        break
                else:
                    # Person is not a child in the referenced parent family
                    person.remove_parent_family_handle(par_family_handle)
                    self.db.commit_person(person, self.trans)
                    self.broken_links.append((person_handle,family_handle))
            for family_handle in person.get_family_handle_list():
                family = self.db.get_family_from_handle(family_handle)
                if not family:
                    # The referenced family does not exist in database
                    person.remove_family_handle(family_handle)
                    self.db.commit_person(person, self.trans)
                    self.broken_links.append((person_handle, family_handle))
                    continue
                if family.get_father_handle() == person_handle:
                    continue
                if family.get_mother_handle() == person_handle:
                    continue
                # The person is not a member of the referenced family
                person.remove_family_handle(family_handle)
                self.db.commit_person(person, self.trans)
                self.broken_links.append((person_handle, family_handle))
            self.progress.step()

    def cleanup_missing_photos(self, cl=0):

        self.progress.set_pass(_('Looking for unused objects'),
                               len(self.db.get_media_object_handles()))
                               
        missmedia_action = 0
        #-------------------------------------------------------------------------
        def remove_clicked():
            # File is lost => remove all references and the object itself
            
            for handle in self.db.get_person_handles(sort_handles=False):
                person = self.db.get_person_from_handle(handle)
                if person.has_media_reference(ObjectId):
                    person.remove_media_references([ObjectId])
                    self.db.commit_person(person, self.trans)

            for handle in self.db.get_family_handles():
                family = self.db.get_family_from_handle(handle)
                if family.has_media_reference(ObjectId):
                    family.remove_media_references([ObjectId])
                    self.db.commit_family(family, self.trans)
                    
            for handle in self.db.get_event_handles():
                event = self.db.get_event_from_handle(handle)
                if event.has_media_reference(ObjectId):
                    event.remove_media_references([ObjectId])
                    self.db.commit_event(event,self.trans)
                
            for handle in self.db.get_source_handles():
                source = self.db.get_source_from_handle(handle)
                if source.has_media_reference(ObjectId):
                    source.remove_media_references([ObjectId])
                    self.db.commit_source(source, self.trans)
                
            for handle in self.db.get_place_handles():
                place = self.db.get_place_from_handle(handle)
                if place.has_media_reference(ObjectId):
                    place.remove_media_references([ObjectId])
                    self.db.commit_place(place, self.trans)

            self.removed_photo.append(ObjectId)
            self.db.remove_object(ObjectId,self.trans) 
    
        def leave_clicked():
            self.bad_photo.append(ObjectId)

        def select_clicked():
            # File is lost => select a file to replace the lost one
            def fs_close_window(obj):
                self.bad_photo.append(ObjectId)

            def fs_ok_clicked(obj):
                name = Utils.get_unicode_path_from_file_chooser(fs_top.get_filename())
                if os.path.isfile(name):
                    obj = self.db.get_object_from_handle(ObjectId)
                    obj.set_path(name)
                    self.db.commit_media_object(obj, self.trans)
                    self.replaced_photo.append(ObjectId)
                else:
                    self.bad_photo.append(ObjectId)

            fs_top = gtk.FileChooserDialog("%s - Gramps" % _("Select file"),
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_OK, gtk.RESPONSE_OK)
                        )
            response = fs_top.run()
            if response == gtk.RESPONSE_OK:
                fs_ok_clicked(fs_top)
            elif response == gtk.RESPONSE_CANCEL:
                fs_close_window(fs_top)
            fs_top.destroy()

        #-------------------------------------------------------------------------
        
        for ObjectId in self.db.get_media_object_handles():
            obj = self.db.get_object_from_handle(ObjectId)
            photo_name = Utils.media_path_full(self.db, obj.get_path())
            if photo_name is not None and photo_name != "" and not Utils.find_file(photo_name):
                if cl:
                    # Convert to file system encoding before prining
                    fn = os.path.basename(photo_name).encode(sys.getfilesystemencoding())
                    print "Warning: media file %s was not found." % fn
                    self.bad_photo.append(ObjectId)
                else:
                    if missmedia_action == 0:
                        mmd = MissingMediaDialog(_("Media object could not be found"),
                        _("The file:\n %(file_name)s \nis referenced in the database, but no longer exists. " 
                        "The file may have been deleted or moved to a different location. " 
                        "You may choose to either remove the reference from the database, " 
                        "keep the reference to the missing file, or select a new file." 
                        ) % {'file_name' : '<b>%s</b>' % photo_name},
                            remove_clicked, leave_clicked, select_clicked)
                        missmedia_action = mmd.default_action
                    elif missmedia_action == 1:
                        remove_clicked()
                    elif missmedia_action == 2:
                        leave_clicked()
                    elif missmedia_action == 3:
                        select_clicked()
            self.progress.step()
    
    def cleanup_empty_objects(self):
        #the position of the change column in the primary objects
        CHANGE_PERSON = 17
        CHANGE_FAMILY = 12
        CHANGE_EVENT  = 10
        CHANGE_SOURCE = 8
        CHANGE_PLACE  = 11
        CHANGE_MEDIA  = 8
        CHANGE_REPOS  = 7
        CHANGE_NOTE   = 5
        
        empty_person_data = gen.lib.Person().serialize()
        empty_family_data = gen.lib.Family().serialize()
        empty_event_data = gen.lib.Event().serialize()
        empty_source_data = gen.lib.Source().serialize()
        empty_place_data = gen.lib.Place().serialize()
        empty_media_data = gen.lib.MediaObject().serialize()
        empty_repos_data = gen.lib.Repository().serialize()
        empty_note_data = gen.lib.Note().serialize()

        _db = self.db
        def _empty(empty, flag):
            ''' Closure for dispatch table, below '''
            def _f(value):
                return self._check_empty(value, empty, flag)
            return _f
                            
        table = (

            # Dispatch table for cleaning up empty objects. Each entry is
            # a tuple containing:
            #    0. Type of object being cleaned up
            #    1. function to read the object from the database
            #    2. function returning cursor over the object type
            #    3. function returning number of objects of this type
            #    4. text identifying the object being cleaned up
            #    5. function to check if the data is empty
            #    6. function to remove the object, if empty
                
            ('persons',
                _db.get_person_from_handle,
                _db.get_person_cursor,
                _db.get_number_of_people,
                _('Looking for empty people records'),
                _empty(empty_person_data, CHANGE_PERSON),
                _db.remove_person,
                ),
            ('families',
                _db.get_family_from_handle,
                _db.get_family_cursor,
                _db.get_number_of_families,
                _('Looking for empty family records'),
                _empty(empty_family_data, CHANGE_FAMILY),
                _db.remove_family,
                ),
            ('events',
                _db.get_event_from_handle,
                _db.get_event_cursor,
                _db.get_number_of_events,
                _('Looking for empty event records'),
                _empty(empty_event_data, CHANGE_EVENT),
                _db.remove_event,
                ),
            ('sources',
                _db.get_source_from_handle,
                _db.get_source_cursor,
                _db.get_number_of_sources,
                _('Looking for empty source records'),
                _empty(empty_source_data, CHANGE_SOURCE),
                _db.remove_source,
                ),
            ('places',
                _db.get_place_from_handle,
                _db.get_place_cursor,
                _db.get_number_of_places,
                _('Looking for empty place records'),
                _empty(empty_place_data, CHANGE_PLACE),
                _db.remove_place,
                ),
            ('media',
                _db.get_object_from_handle,
                _db.get_media_cursor,
                _db.get_number_of_media_objects,
                _('Looking for empty media records'),
                _empty(empty_media_data, CHANGE_MEDIA),
                _db.remove_object,
                ),
            ('repos',
                _db.get_repository_from_handle,
                _db.get_repository_cursor,
                _db.get_number_of_repositories,
                _('Looking for empty repository records'),
                _empty(empty_repos_data, CHANGE_REPOS),
                _db.remove_repository,
                ),
            ('notes',
                _db.get_note_from_handle,
                _db.get_note_cursor,
                _db.get_number_of_notes,
                _('Looking for empty note records'),
                _empty(empty_note_data, CHANGE_NOTE),
                _db.remove_note,
                ),
            )

        # Now, iterate over the table, dispatching the functions

        for (the_type, get_func, cursor_func, total_func,
             text, check_func, remove_func) in table:

            with cursor_func() as cursor:
                total = total_func()
                self.progress.set_pass(text, total)

                for handle, data in cursor:
                    self.progress.step()
                    if check_func(data):
                        # we cannot remove here as that would destroy cursor
                        # so save the handles for later removal               
                        self.empty_objects[the_type].append(handle)

            #now remove
            for handle in self.empty_objects[the_type]:
                remove_func(handle, self.trans)
    
    def _check_empty(self, data, empty_data, changepos):
        """compare the data with the data of an empty object
            change, handle and gramps_id are not compared """
        if changepos is not None:
            return (data[2:changepos] == empty_data[2:changepos] and 
                    data[changepos+1:] == empty_data[changepos+1:]
                   )
        else :
            return data[2:] == empty_data[2:]

    def cleanup_empty_families(self, automatic):

        fhandle_list = self.db.get_family_handles()

        self.progress.set_pass(_('Looking for empty families'),
                               len(fhandle_list))
        for family_handle in fhandle_list:
            self.progress.step()
            
            family = self.db.get_family_from_handle(family_handle)
            family_id = family.get_gramps_id()
            father_handle = family.get_father_handle()
            mother_handle = family.get_mother_handle()

            if not father_handle and not mother_handle and \
                   len(family.get_child_ref_list()) == 0:
                self.empty_family.append(family_id)
                self.delete_empty_family(family_handle)

    def delete_empty_family(self, family_handle):
        for key in self.db.get_person_handles(sort_handles=False):
            child = self.db.get_person_from_handle(key)
            changed = False
            changed |= child.remove_parent_family_handle(family_handle)
            changed |= child.remove_family_handle(family_handle)
            if changed:
                self.db.commit_person(child, self.trans)
        self.db.remove_family(family_handle, self.trans)

    def check_parent_relationships(self):
        """Repair father=female or mother=male in hetero families
        """

        fhandle_list = self.db.get_family_handles()
        self.progress.set_pass(_('Looking for broken parent relationships'),
                               len(fhandle_list))

        for family_handle in fhandle_list:
            self.progress.step()
            family = self.db.get_family_from_handle(family_handle)

            father_handle = family.get_father_handle()
            if father_handle:
                fgender = self.db.get_person_from_handle(father_handle
                                                         ).get_gender()
            else:
                fgender = None

            mother_handle = family.get_mother_handle()
            if mother_handle:
                mgender = self.db.get_person_from_handle(mother_handle
                                                         ).get_gender()
            else:
                mgender = None

            if (fgender == gen.lib.Person.FEMALE 
                    or mgender == gen.lib.Person.MALE) and fgender != mgender:
                # swap. note: (at most) one handle may be None
                family.set_father_handle(mother_handle)
                family.set_mother_handle(father_handle)
                self.db.commit_family(family, self.trans)
                self.fam_rel.append(family_handle)

    def check_events(self):
        self.progress.set_pass(_('Looking for event problems'),
                               self.db.get_number_of_people()
                               +self.db.get_number_of_families())
        
        for key in self.db.get_person_handles(sort_handles=False):
            self.progress.step()
            
            person = self.db.get_person_from_handle(key)
            birth_ref = person.get_birth_ref()
            if birth_ref:
                birth_handle = birth_ref.ref
                birth = self.db.get_event_from_handle(birth_handle)
                if not birth:
                    # The birth event referenced by the birth handle
                    # does not exist in the database
                    person.set_birth_ref(None)
                    self.db.commit_person(person, self.trans)
                    self.invalid_events.append(key)
                else:
                    if int(birth.get_type()) != gen.lib.EventType.BIRTH:
                        # Birth event was not of the type "Birth"
                        birth.set_type(gen.lib.EventType(gen.lib.EventType.BIRTH))
                        self.db.commit_event(birth, self.trans)
                        self.invalid_birth_events.append(key)
            death_ref = person.get_death_ref()
            if death_ref:
                death_handle = death_ref.ref
                death = self.db.get_event_from_handle(death_handle)
                if not death:
                    # The death event referenced by the death handle
                    # does not exist in the database
                    person.set_death_ref(None)
                    self.db.commit_person(person, self.trans)
                    self.invalid_events.append(key)
                else:
                    if int(death.get_type()) != gen.lib.EventType.DEATH:
                        # Death event was not of the type "Death"
                        death.set_type(gen.lib.EventType(gen.lib.EventType.DEATH))
                        self.db.commit_event(death, self.trans)
                        self.invalid_death_events.append(key)

            if person.get_event_ref_list():
                for event_ref in person.get_event_ref_list():
                    event_handle = event_ref.ref
                    event = self.db.get_event_from_handle(event_handle)
                    if not event:
                        # The event referenced by the person
                        # does not exist in the database
                        #TODO: There is no better way?
                        person.get_event_ref_list().remove(event_ref)
                        self.db.commit_person(person,self.trans)
                        self.invalid_events.append(key)
            elif not isinstance(person.get_event_ref_list(), list):
                # event_list is None or other garbage
                person.set_event_ref_list([])
                self.db.commit_person(person, self.trans)
                self.invalid_events.append(key)

        for key in self.db.get_family_handles():
            self.progress.step()
            family = self.db.get_family_from_handle(key)
            if family.get_event_ref_list():
                for event_ref in family.get_event_ref_list():
                    event_handle = event_ref.ref
                    event = self.db.get_event_from_handle(event_handle)
                    if not event:
                        # The event referenced by the family
                        # does not exist in the database
                        print family.gramps_id
                        nlist = [x for x in family.get_event_ref_list()
                                      if x.ref != event_handle]
                        family.set_event_ref_list(nlist)
                        self.db.commit_family(family, self.trans)
                        self.invalid_events.append(key)
            elif not isinstance(family.get_event_ref_list(), list):
                # event_list is None or other garbage
                family.set_event_ref_list([])
                self.db.commit_family(family, self.trans)
                self.invalid_events.append(key)

    def check_person_references(self):
        plist = self.db.get_person_handles()
        
        self.progress.set_pass(_('Looking for person reference problems'),
                               len(plist))
        
        for key in plist:
            person = self.db.get_person_from_handle(key)
            for pref in person.get_person_ref_list():
                p = self.db.get_person_from_handle( pref.ref)
                if not p:
                    # The referenced person does not exist in the database
                    person.get_person_ref_list().remove(pref)
                    self.db.commit_person(person, self.trans)
                    self.invalid_person_references.append(key)

    def check_family_references(self):
        plist = self.db.get_person_handles()

        self.progress.set_pass(_('Looking for family reference problems'),
                               len(plist))

        for key in plist:
            person = self.db.get_person_from_handle(key)
            for ordinance in person.get_lds_ord_list():
                family_handle = ordinance.get_family_handle()
                if family_handle:
                    family = self.db.get_family_from_handle(family_handle)
                    if not family:
                        # The referenced family does not exist in the database
                        ordinance.set_family_handle(None)
                        self.db.commit_person(person, self.trans)
                        self.invalid_family_references.append(key)

    def check_repo_references(self):
        slist = self.db.get_source_handles()
        
        self.progress.set_pass(_('Looking for repository reference problems'),
                               len(slist))
        
        for key in slist:
            source = self.db.get_source_from_handle(key)
            for reporef in source.get_reporef_list():
                r = self.db.get_repository_from_handle(reporef.ref)
                if not r:
                    # The referenced repository does not exist in the database
                    source.get_reporef_list().remove(reporef)
                    self.db.commit_source(source, self.trans)
                    self.invalid_repo_references.append(key)

    def check_place_references(self):
        plist = self.db.get_person_handles()
        flist = self.db.get_family_handles()
        elist = self.db.get_event_handles()
        self.progress.set_pass(_('Looking for place reference problems'),
                               len(elist)+len(plist)+len(flist))
        # check persons -> the LdsOrd references a place
        for key in plist:
            person = self.db.get_person_from_handle(key)
            for ordinance in person.lds_ord_list:
                place_handle = ordinance.get_place_handle()
                if place_handle:
                    place = self.db.get_place_from_handle(place_handle)
                    if not place:
                        # The referenced place does not exist in the database
                        ordinance.set_place_handle("")
                        self.db.commit_person(person, self.trans)
                        self.invalid_place_references.append(key)
        # check families -> the LdsOrd references a place
        for key in flist:
            family = self.db.get_family_from_handle(key)
            for ordinance in family.lds_ord_list:
                place_handle = ordinance.get_place_handle()
                if place_handle:
                    place = self.db.get_place_from_handle(place_handle)
                    if not place:
                        # The referenced place does not exist in the database
                        ordinance.set_place_handle("")
                        self.db.commit_family(family, self.trans)
                        self.invalid_place_references.append(key)
        # check events
        for key in elist:
            event = self.db.get_event_from_handle(key)
            place_handle = event.get_place_handle()
            if place_handle:
                place = self.db.get_place_from_handle(place_handle)
                if not place:
                    # The referenced place does not exist in the database
                    event.set_place_handle("")
                    self.db.commit_event(event, self.trans)
                    self.invalid_place_references.append(key)

    def check_citation_references(self):
        known_handles = self.db.get_citation_handles()

        total = (
                self.db.get_number_of_people() +
                self.db.get_number_of_families() +
                self.db.get_number_of_events() +
                self.db.get_number_of_places() +
                self.db.get_number_of_media_objects() +
                self.db.get_number_of_sources() +
                self.db.get_number_of_repositories()
                )

        self.progress.set_pass(_('Looking for citation reference problems'),
                               total)
        
        for handle in self.db.person_map.keys():
            self.progress.step()
            info = self.db.person_map[handle]
            person = gen.lib.Person()
            person.unserialize(info)
            handle_list = person.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Citation' and
                            item[1] not in known_handles ]
            if bad_handles:
                person.remove_citation_references(bad_handles)
                self.db.commit_person(person,self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_citation_references]
                self.invalid_citation_references += new_bad_handles

        for handle in self.db.family_map.keys():
            self.progress.step()
            info = self.db.family_map[handle]
            family = gen.lib.Family()
            family.unserialize(info)
            handle_list = family.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Citation' and
                            item[1] not in known_handles ]
            if bad_handles:
                family.remove_citation_references(bad_handles)
                self.db.commit_family(family, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_citation_references]
                self.invalid_citation_references += new_bad_handles

        for handle in self.db.place_map.keys():
            self.progress.step()
            info = self.db.place_map[handle]
            place = gen.lib.Place()
            place.unserialize(info)
            handle_list = place.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Citation' and
                            item[1] not in known_handles ]
            if bad_handles:
                place.remove_citation_references(bad_handles)
                self.db.commit_place(place,self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_citation_references]
                self.invalid_citation_references += new_bad_handles

        for handle in self.db.repository_map.keys():
            self.progress.step()
            info = self.db.repository_map[handle]
            repo = gen.lib.Repository()
            repo.unserialize(info)
            handle_list = repo.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Citation' and
                            item[1] not in known_handles ]
            if bad_handles:
                repo.remove_citation_references(bad_handles)
                self.db.commit_repository(repo, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_citation_references]
                self.invalid_citation_references += new_bad_handles

        #I think this for loop is useless! citations in citations map exist...
        for handle in known_handles:
            self.progress.step()
            info = self.db.citation_map[handle]
            citation = gen.lib.Citation()
            citation.unserialize(info)
            handle_list = citation.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Citation' and
                            item[1] not in known_handles ]
            if bad_handles:
                citation.remove_citation_references(bad_handles)
                self.db.commit_citation(citation, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_citation_references]
                self.invalid_citation_references += new_bad_handles

        for handle in self.db.media_map.keys():
            self.progress.step()
            info = self.db.media_map[handle]
            obj = gen.lib.MediaObject()
            obj.unserialize(info)
            handle_list = obj.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Citation' and
                            item[1] not in known_handles ]
            if bad_handles:
                obj.remove_citation_references(bad_handles)
                self.db.commit_media_object(obj, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_citation_references]
                self.invalid_citation_references += new_bad_handles

        for handle in self.db.event_map.keys():
            self.progress.step()
            info = self.db.event_map[handle]
            event = gen.lib.Event()
            event.unserialize(info)
            handle_list = event.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Citation' and
                            item[1] not in known_handles ]
            if bad_handles:
                event.remove_citation_references(bad_handles)
                self.db.commit_event(event, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_citation_references]
                self.invalid_citation_references += new_bad_handles

    def check_media_references(self):
        known_handles = self.db.get_media_object_handles(False)

        total = (
                self.db.get_number_of_people() + 
                self.db.get_number_of_families() +
                self.db.get_number_of_events() + 
                self.db.get_number_of_places() +
                self.db.get_number_of_sources()
                )

        self.progress.set_pass(_('Looking for media object reference problems'),
                               total)
        
        for handle in self.db.person_map.keys():
            self.progress.step()
            info = self.db.person_map[handle]
            person = gen.lib.Person()
            person.unserialize(info)
            handle_list = person.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'MediaObject' and
                            item[1] not in known_handles ]
            if bad_handles:
                person.remove_media_references(bad_handles)
                self.db.commit_person(person, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_media_references]
                self.invalid_media_references += new_bad_handles

        for handle in self.db.family_map.keys():
            self.progress.step()
            info = self.db.family_map[handle]
            family = gen.lib.Family()
            family.unserialize(info)
            handle_list = family.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'MediaObject' and
                            item[1] not in known_handles ]
            if bad_handles:
                family.remove_media_references(bad_handles)
                self.db.commit_family(family, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_media_references]
                self.invalid_media_references += new_bad_handles

        for handle in self.db.place_map.keys():
            self.progress.step()
            info = self.db.place_map[handle]
            place = gen.lib.Place()
            place.unserialize(info)
            handle_list = place.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'MediaObject' and
                            item[1] not in known_handles ]
            if bad_handles:
                place.remove_media_references(bad_handles)
                self.db.commit_place(place, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_media_references]
                self.invalid_media_references += new_bad_handles
        
        for handle in self.db.event_map.keys():
            self.progress.step()
            info = self.db.event_map[handle]
            event = gen.lib.Event()
            event.unserialize(info)
            handle_list = event.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'MediaObject' and
                            item[1] not in known_handles ]
            if bad_handles:
                event.remove_media_references(bad_handles)
                self.db.commit_event(event, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_media_references]
                self.invalid_media_references += new_bad_handles
        
        for handle in self.db.source_map.keys():
            self.progress.step()
            info = self.db.source_map[handle]
            source = gen.lib.Source()
            source.unserialize(info)
            handle_list = source.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'MediaObject' and
                            item[1] not in known_handles ]
            if bad_handles:
                source.remove_media_references(bad_handles)
                self.db.commit_source(source, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_media_references]
                self.invalid_media_references += new_bad_handles

    def check_note_references(self):
        known_handles = self.db.get_note_handles()

        total = (
                self.db.get_number_of_people() + 
                self.db.get_number_of_families() +
                self.db.get_number_of_events() + 
                self.db.get_number_of_places() +
                self.db.get_number_of_media_objects() +
                self.db.get_number_of_sources() +
                self.db.get_number_of_repositories()
                )

        self.progress.set_pass(_('Looking for note reference problems'),
                               total)
        
        for handle in self.db.person_map.keys():
            self.progress.step()
            info = self.db.person_map[handle]
            person = gen.lib.Person()
            person.unserialize(info)
            handle_list = person.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Note' and
                            item[1] not in known_handles ]
            if bad_handles:
                map(person.remove_note, bad_handles)
                self.db.commit_person(person, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_note_references]
                self.invalid_note_references += new_bad_handles

        for handle in self.db.family_map.keys():
            self.progress.step()
            info = self.db.family_map[handle]
            family = gen.lib.Family()
            family.unserialize(info)
            handle_list = family.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Note' and
                            item[1] not in known_handles ]
            if bad_handles:
                map(family.remove_note, bad_handles)
                self.db.commit_family(family, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_note_references]
                self.invalid_note_references += new_bad_handles

        for handle in self.db.place_map.keys():
            self.progress.step()
            info = self.db.place_map[handle]
            place = gen.lib.Place()
            place.unserialize(info)
            handle_list = place.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Note' and
                            item[1] not in known_handles ]
            if bad_handles:
                map(place.remove_note, bad_handles)
                self.db.commit_place(place, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_note_references]
                self.invalid_note_references += new_bad_handles

        for handle in self.db.source_map.keys():
            self.progress.step()
            info = self.db.source_map[handle]
            source = gen.lib.Source()
            source.unserialize(info)
            handle_list = source.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Note' and
                            item[1] not in known_handles ]
            for bad_handle in bad_handles:
                source.remove_note(bad_handle)
            if bad_handles:
                map(source.remove_note, bad_handles)
                self.db.commit_source(source, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_note_references]
                self.invalid_note_references += new_bad_handles

        for handle in self.db.media_map.keys():
            self.progress.step()
            info = self.db.media_map[handle]
            obj = gen.lib.MediaObject()
            obj.unserialize(info)
            handle_list = obj.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Note' and
                            item[1] not in known_handles ]
            if bad_handles:
                map(obj.remove_note, bad_handles)
                self.db.commit_media_object(obj, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_note_references]
                self.invalid_note_references += new_bad_handles

        for handle in self.db.event_map.keys():
            self.progress.step()
            info = self.db.event_map[handle]
            event = gen.lib.Event()
            event.unserialize(info)
            handle_list = event.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Note' and
                            item[1] not in known_handles ]
            if bad_handles:
                map(event.remove_note, bad_handles)
                self.db.commit_event(event, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_note_references]
                self.invalid_note_references += new_bad_handles

        for handle in self.db.repository_map.keys():
            self.progress.step()
            info = self.db.repository_map[handle]
            repo = gen.lib.Repository()
            repo.unserialize(info)
            handle_list = repo.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Note' and
                            item[1] not in known_handles ]
            if bad_handles:
                map(repo.remove_note, bad_handles)
                self.db.commit_repository(repo, self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_note_references]
                self.invalid_note_references += new_bad_handles

    def build_report(self, uistate=None):
        self.progress.close()
        bad_photos = len(self.bad_photo)
        replaced_photos = len(self.replaced_photo)
        removed_photos = len(self.removed_photo)
        photos = bad_photos + replaced_photos + removed_photos
        efam = len(self.empty_family)
        blink = len(self.broken_links)
        plink = len(self.broken_parent_links)
        slink = len(self.duplicate_links)
        rel = len(self.fam_rel)
        event_invalid = len(self.invalid_events)
        birth_invalid = len(self.invalid_birth_events)
        death_invalid = len(self.invalid_death_events)
        person = birth_invalid + death_invalid
        person_references = len(self.invalid_person_references)
        family_references = len(self.invalid_family_references)
        invalid_dates = len(self.invalid_dates)
        place_references = len(self.invalid_place_references)
        citation_references = len(self.invalid_citation_references)
        repo_references = len(self.invalid_repo_references)
        media_references = len(self.invalid_media_references)
        note_references = len(self.invalid_note_references)
        name_format = len(self.removed_name_format)
        empty_objs = sum(len(obj) for obj in self.empty_objects.itervalues())

        errors = (photos + efam + blink + plink + slink + rel +
                  event_invalid + person +
                  person_references  + family_references + place_references +
                  citation_references + repo_references + media_references  +
                  note_references + name_format + empty_objs + invalid_dates
                 )
        
        if errors == 0:
            if uistate:
                OkDialog(_("No errors were found"),
                         _('The database has passed internal checks'),
                         parent=uistate.window)
            else:
                print("No errors were found: the database has passed internal checks.")
            return 0

        self.text = cStringIO.StringIO()
        if blink > 0:
            self.text.write(
                ngettext("%(quantity)d broken child/family link was fixed\n",
                         "%(quantity)d broken child-family links were fixed\n",
                         blink) % {'quantity': blink}
                 )
            for (person_handle, family_handle) in self.broken_links:
                person = self.db.get_person_from_handle(person_handle)
                if person:
                    cn = person.get_primary_name().get_name()
                else:
                    cn = _("Non existing child")
                try:
                    family = self.db.get_family_from_handle(family_handle)
                    pn = Utils.family_name(family, self.db)
                except:
                    pn = _("Unknown")
                self.text.write('\t')
                self.text.write(
                    _("%(person)s was removed from the family of %(family)s\n")
                        % {'person': cn, 'family': pn}
                    )

        if plink > 0:
            self.text.write(
                ngettext("%(quantity)d broken spouse/family link was fixed\n", 
                         "%(quantity)d broken spouse/family links were fixed\n",
                         plink) % {'quantity' : plink}
                )
            for (person_handle, family_handle) in self.broken_parent_links:
                person = self.db.get_person_from_handle(person_handle)
                if person:
                    cn = person.get_primary_name().get_name()
                else:
                    cn = _("Non existing person")
                family = self.db.get_family_from_handle(family_handle)
                if family:
                    pn = Utils.family_name(family, self.db)
                else:
                    pn = family_handle
                self.text.write('\t')
                self.text.write(
                    _("%(person)s was restored to the family of %(family)s\n")
                        % {'person': cn, 'family': pn}
                    )

        if slink > 0:
            self.text.write(
                ngettext("%(quantity)d duplicate spouse/family link was found\n",
                         "%(quantity)d duplicate spouse/family links were found\n",
                         slink) % {'quantity': slink}
                )
            for (person_handle, family_handle) in self.broken_parent_links:
                person = self.db.get_person_from_handle(person_handle)
                if person:
                    cn = person.get_primary_name().get_name()
                else:
                    cn = _("Non existing person")
                family = self.db.get_family_from_handle(family_handle)
                if family:
                    pn = Utils.family_name(family, self.db)
                else:
                    pn = _("None")
                self.text.write('\t')
                self.text.write(
                    _("%(person)s was restored to the family of %(family)s\n")
                        % {'person': cn, 'family': pn}
                    )

        if efam == 1:
            self.text.write(
                _("1 family with no parents or children found, removed.\n")
                )
            self.text.write("\t%s\n" % self.empty_family[0])
        elif efam > 1:
            self.text.write(
                _("%(quantity)d families with no parents or children, "
                    "removed.\n") % {'quantity': efam}
                )

        if rel:
            self.text.write(
                ngettext("%d corrupted family relationship fixed\n", 
                         "%d corrupted family relationship fixed\n",
                         rel) % rel
                )

        if person_references:
            self.text.write(
                ngettext("%d person was referenced but not found\n", 
                         "%d persons were referenced, but not found\n", 
                         person_references) % person_references
                )
        
        if family_references:
            self.text.write(
                ngettext("%d family was referenced but not found\n", 
                         "%d families were referenced, but not found\n", 
                         family_references) % family_references
                )
        
        if invalid_dates:
            self.text.write(ngettext("%d date was corrected\n", 
                                     "%d dates were corrected\n", 
                                     invalid_dates) % invalid_dates)
        
        if repo_references:
            self.text.write(
                ngettext("%(quantity)d repository was referenced but not found\n",
                         "%(quantity)d repositories were referenced, but not found\n",
                         repo_references) % {'quantity': repo_references})

        if photos:
            self.text.write(
                ngettext("%(quantity)d media object was referenced, but not found\n",
                         "%(quantity)d media objects were referenced, but not found\n",
                         photos) % {'quantity' :photos}
                )

        if bad_photos:
            self.text.write(
                ngettext("Reference to %(quantity)d missing media object was kept\n",
                         "References to %(quantity)d media objects were kept\n",
                        bad_photos) % {'quantity' :bad_photos}
                )

        if replaced_photos:
            self.text.write(
                ngettext("%(quantity)d missing media object was replaced\n",
                         "%(quantity)d missing media objects were replaced\n",
                         replaced_photos) % {'quantity': replaced_photos}
                )

        if removed_photos:
            self.text.write(
                ngettext("%(quantity)d missing media object was removed\n",
                         "%(quantity)d missing media objects were removed\n",
                         removed_photos) % {'quantity' : removed_photos}
                )

        if event_invalid:
            self.text.write(
                ngettext("%(quantity)d invalid event reference was removed\n",
                         "%(quantity)d invalid event references were removed\n",
                         event_invalid) % {'quantity': event_invalid}
                )

        if birth_invalid:
            self.text.write(
                ngettext("%(quantity)d invalid birth event name was fixed\n",
                         "%(quantity)d invalid birth event names were fixed\n",
                         birth_invalid) % {'quantity' : birth_invalid}
                )

        if death_invalid:
            self.text.write(
                ngettext("%(quantity)d invalid death event name was fixed\n",
                         "%(quantity)d invalid death event names were fixed\n",
                         death_invalid) % {'quantity': death_invalid}
                )

        if place_references:
            self.text.write(
                ngettext("%(quantity)d place was referenced but not found\n",
                         "%(quantity)d places were referenced, but not found\n",
                         place_references) % {'quantity': place_references}
                )

        if citation_references:
            self.text.write(
                ngettext("%(quantity)d citation was referenced but not found\n",
                         "%(quantity)d citations were referenced, but not found\n",
                         citation_references) % {'quantity': citation_references}
                )

        if media_references:
            self.text.write(
                ngettext("%(quantity)d media object was referenced but not found\n",
                         "%(quantity)d media objects were referenced but not found\n",
                         media_references) % {'quantity': media_references}
                )

        if note_references:
            self.text.write(
                ngettext("%(quantity)d note object was referenced but not found\n",
                         "%(quantity)d note objects were referenced but not found\n",
                         note_references) % {'quantity': note_references})

        if name_format:
            self.text.write(
                ngettext("%(quantity)d invalid name format reference was removed\n",
                         "%(quantity)d invalid name format references were removed\n",
                         name_format) % {'quantity' : name_format}
                )

        if empty_objs > 0 :
            self.text.write(_("%(empty_obj)d empty objects removed:\n"
                              "   %(person)d person objects\n"
                              "   %(family)d family objects\n"
                              "   %(event)d event objects\n"
                              "   %(source)d source objects\n"
                              "   %(media)d media objects\n"
                              "   %(place)d place objects\n"
                              "   %(repo)d repository objects\n"
                              "   %(note)d note objects\n") % {
                                 'empty_obj' : empty_objs, 
                                 'person' : len(self.empty_objects['persons']),
                                 'family' : len(self.empty_objects['families']),
                                 'event' : len(self.empty_objects['events']),
                                 'source' : len(self.empty_objects['sources']),
                                 'media' : len(self.empty_objects['media']),
                                 'place' : len(self.empty_objects['places']),
                                 'repo' : len(self.empty_objects['repos']),
                                 'note' : len(self.empty_objects['notes'])
                                 }
                            )

        return errors

#-------------------------------------------------------------------------
#
# Display the results
#
#-------------------------------------------------------------------------
class Report(ManagedWindow.ManagedWindow):
    
    def __init__(self, uistate, text, cl=0):
        if cl:
            # Convert to file system encoding before prining
            print text.encode(sys.getfilesystemencoding())
            return

        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self)
        
        topDialog = Glade()
        topDialog.get_object("close").connect('clicked', self.close)
        window = topDialog.toplevel
        textwindow = topDialog.get_object("textwindow")
        textwindow.get_buffer().set_text(text)

        self.set_window(window,
                        #topDialog.get_widget("title"),
                        topDialog.get_object("title"),
                        _("Integrity Check Results"))

        self.show()

    def build_menu_names(self, obj):
        return (_('Check and Repair'), None)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class CheckOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, person_id=None):
        tool.ToolOptions.__init__(self, name, person_id)
