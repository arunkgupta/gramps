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

"Database Processing/Check and repair database"

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import os
import cStringIO
import sets
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# gtk modules
#
#-------------------------------------------------------------------------
import gtk
import gtk.glade

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import RelLib
import Utils
import const
import Tool
from QuestionDialog import OkDialog, MissingMediaDialog


#-------------------------------------------------------------------------
#
# Low Level repair
#
#-------------------------------------------------------------------------
def low_level(db):
    """
    This is a low-level repair routine.

    It is fixing DB inconsistencies such as duplicates.
    Returns a (status,name) tuple.
    The boolean status indicates the success of the procedure.
    The name indicates the problematic table (empty if status is True).
    """

    for the_map in [('Person',db.person_map),
                    ('Family',db.family_map),
                    ('Event',db.event_map),
                    ('Place',db.place_map),
                    ('Source',db.source_map),
                    ('Media',db.media_map)]:

        print "Low-level repair: table: %s" % the_map[0]
        if _table_low_level(db,the_map[1]):
            print "Done."
        else:
            print "Low-level repair: Problem with table: %s" % the_map[0]
            return (False,the_map[0])
    return (True,'')


def _table_low_level(db,table):
    """
    Low level repair for a given db table.
    """
    handle_list = table.keys()
    dup_handles = sets.Set(
        [ handle for handle in handle_list if handle_list.count(handle) > 1 ]
        )

    if not dup_handles:
        print "    No dupes found for this table"
        return True

    import GrampsBSDDB
    table_cursor = GrampsBSDDB.GrampsBSDDBDupCursor(table)
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
                print "    Succesfully deleted dupe #%d" % (count+1)
            except:
                print "    Failed deleting dupe."
                return False

            try:
                ret = table_cursor.next_dup()
            except:
                print "    Failed moving the cursor."
                return False

    table_cursor.close()
    table.sync()
    return True

#-------------------------------------------------------------------------
#
# runTool
#
#-------------------------------------------------------------------------
class Check(Tool.Tool):
    def __init__(self,db,person,options_class,name,callback=None,parent=None):
        Tool.Tool.__init__(self,db,person,options_class,name)

        # def runTool(database,active_person,callback,parent=None):
        cli = int(parent == None)

        try:
            if db.readonly:
                # TODO: split plugin in a check and repair part to support
                # checking of a read only database
                return

            # The low-level repair is bypassing the transaction mechanism.
            # As such, we run it before starting the transaction.
            # We only do this for the BSDDB backend.
            if db.__class__.__name__ == 'GrampsBSDDB':
                low_level(db)
        
            trans = db.transaction_begin()
            trans.set_batch(True)
            db.disable_signals()
            checker = CheckIntegrity(db,parent,trans)
            checker.fix_encoding()
            checker.cleanup_missing_photos(cli)
            
            prev_total = -1
            total = 0
        
            while prev_total != total:
                prev_total = total
            
                checker.check_for_broken_family_links()
                checker.check_parent_relationships()
                checker.cleanup_empty_families(cli)
                checker.cleanup_duplicate_spouses()

                total = checker.family_errors()

            checker.check_events()
            checker.check_place_references()
            checker.check_source_references()
            db.transaction_commit(trans, _("Check Integrity"))
            db.enable_signals()
            db.request_rebuild()

            errs = checker.build_report(cli)
            if errs:
                Report(checker.text.getvalue(),parent)
        except:
            import DisplayTrace
            DisplayTrace.DisplayTrace()

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class CheckIntegrity:
    
    def __init__(self,db,parent,trans):
        self.db = db
        self.trans = trans
        self.parent = parent
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
        self.invalid_place_references = []
        self.invalid_source_references = []
        self.progress = Utils.ProgressMeter(_('Checking database'),'')

    def family_errors(self):
        return len(self.broken_parent_links) + len(self.broken_links) + len(self.empty_family) + len(self.duplicate_links)

    def cleanup_duplicate_spouses(self):

        self.progress.set_pass(_('Looking for duplicate spouses'),
                               self.db.get_number_of_people())

        for handle in self.db.person_map.keys():
            value = self.db.person_map[handle]
            p = RelLib.Person(value)
            splist = p.get_family_handle_list()
            if len(splist) != len(sets.Set(splist)):
                new_list = []
                for value in splist:
                    if value not in new_list:
                        new_list.append(value)
                        self.duplicate_links.append((handle,value))
                p.set_family_handle_list(new_list)
                self.db.commit_person(p,self.trans)
            self.progress.step()


    def fix_encoding(self):
        self.progress.set_pass(_('Looking for character encoding errors'),
                               self.db.get_number_of_media_objects())

        for handle in self.db.media_map.keys():
            data = self.db.media_map[handle]
            if type(data[2]) != unicode or type(data[4]) != unicode:
                obj = self.db.get_object_from_handle(handle)
                obj.path = Utils.fix_encoding( obj.path)
                obj.desc = Utils.fix_encoding( obj.desc)
                self.db.commit_media_object(obj,self.trans)
            self.progress.step()

    def check_for_broken_family_links(self):
        # Check persons referenced by the family objects

        fhandle_list = self.db.get_family_handles()
        self.progress.set_pass(_('Looking for broken family links'),
                               len(fhandle_list) + self.db.get_number_of_people())
        
        for family_handle in fhandle_list:
            family = self.db.get_family_from_handle(family_handle)
            father_handle = family.get_father_handle()
            mother_handle = family.get_mother_handle()
            if father_handle:
                father = self.db.get_person_from_handle(father_handle)
                if not father:
                    # The person referenced by the father handle does not exist in the database
                    family.set_father_handle(None)
                    self.db.commit_family(family,self.trans)
                    self.broken_parent_links.append((father_handle,family_handle))
                    father_handle = None
            if mother_handle:
                mother = self.db.get_person_from_handle(mother_handle)
                if not mother:
                    # The person referenced by the mother handle does not exist in the database
                    family.set_mother_handle(None)
                    self.db.commit_family(family,self.trans)
                    self.broken_parent_links.append((mother_handle,family_handle))
                    mother_handle = None

            if father_handle and father and family_handle not in father.get_family_handle_list():
                # The referenced father has no reference back to the family
                self.broken_parent_links.append((father_handle,family_handle))
                father.add_family_handle(family_handle)
                self.db.commit_person(father,self.trans)
            if mother_handle and mother and family_handle not in mother.get_family_handle_list():
                # The referenced mother has no reference back to the family
                self.broken_parent_links.append((mother_handle,family_handle))
                mother.add_family_handle(family_handle)
                self.db.commit_person(mother,self.trans)
            for child_handle in family.get_child_handle_list():
                child = self.db.get_person_from_handle(child_handle)
                if child:
                    if family_handle == child.get_main_parents_family_handle():
                       continue
                    for family_type in child.get_parent_family_handle_list():
                        if family_type[0] == family_handle:
                            break
                    else:
                        # The referenced child has no reference back to the family
                        family.remove_child_handle(child_handle)
                        self.db.commit_family(family,self.trans)
                        self.broken_links.append((child_handle,family_handle))
                else:
                    # The person referenced by the child handle does not exist in the database
                    family.remove_child_handle(child_handle)
                    self.db.commit_family(family,self.trans)
                    self.broken_links.append((child_handle,family_handle))
            self.progress.step()
            
        # Check persons membership in referenced families
        for person_handle in self.db.get_person_handles():
            person = self.db.get_person_from_handle(person_handle)
            for family_type in person.get_parent_family_handle_list():
                family = self.db.get_family_from_handle(family_type[0])
                if not family:
                    person.remove_parent_family_handle(family_type[0])
                    self.db.commit_person(person,self.trans)
                    continue
                for child_handle in family.get_child_handle_list():
                    if child_handle == person_handle:
                        break
                else:
                    # Person is not a child in the referenced parent family
                    person.remove_parent_family_handle(family_type[0])
                    self.db.commit_person(person,self.trans)
                    self.broken_links.append((person_handle,family_handle))
            for family_handle in person.get_family_handle_list():
                family = self.db.get_family_from_handle(family_handle)
                if not family:
                    # The referenced family does not exist in database
                    person.remove_family_handle(family_handle)
                    self.db.commit_person(person,self.trans)
                    self.broken_links.append((person_handle,family_handle))
                    continue
                if family.get_father_handle() == person_handle:
                    continue
                if family.get_mother_handle() == person_handle:
                    continue
                # The person is not a member of the referenced family
                person.remove_family_handle(family_handle)
                self.db.commit_person(person,self.trans)
                self.broken_links.append((person_handle,family_handle))
            self.progress.step()

    def cleanup_missing_photos(self,cl=0):

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
                    self.db.commit_person(person,self.trans)

            for handle in self.db.get_family_handles():
                family = self.db.get_family_from_handle(handle)
                if family.has_media_reference(ObjectId):
                    family.remove_media_references([ObjectId])
                    self.db.commit_family(family,self.trans)
                    
            for handle in self.db.get_event_handles():
                event = self.db.get_event_from_handle(handle)
                if event.has_media_reference(ObjectId):
                    event.remove_media_references([ObjectId])
                    self.db.commit_event(event,self.trans)
                
            for handle in self.db.get_source_handles():
                source = self.db.get_source_from_handle(handle)
                if source.has_media_reference(ObjectId):
                    source.remove_media_references([ObjectId])
                    self.db.commit_source(source,self.trans)
                
            for handle in self.db.get_place_handles():
                place = self.db.get_place_from_handle(handle)
                if place.has_media_reference(ObjectId):
                    place.remove_media_references([ObjectId])
                    self.db.commit_place(place,self.trans)

            self.removed_photo.append(ObjectId)
            self.db.remove_object(ObjectId,self.trans) 
    
        def leave_clicked():
            self.bad_photo.append(ObjectId)

        def select_clicked():
            # File is lost => select a file to replace the lost one
            def fs_close_window(obj):
                self.bad_photo.append(ObjectId)

            def fs_ok_clicked(obj):
                name = fs_top.get_filename()
                if os.path.isfile(name):
                    obj = self.db.get_object_from_handle(ObjectId)
                    obj.set_path(name)
                    self.db.commit_media_object(obj,self.trans)
                    self.replaced_photo.append(ObjectId)
                else:
                    self.bad_photo.append(ObjectId)

            fs_top = gtk.FileSelection("%s - GRAMPS" % _("Select file"))
            fs_top.hide_fileop_buttons()
            fs_top.ok_button.connect('clicked',fs_ok_clicked)
            fs_top.cancel_button.connect('clicked',fs_close_window)
            fs_top.run()
            fs_top.destroy()

        #-------------------------------------------------------------------------
        
        for ObjectId in self.db.get_media_object_handles():
            obj = self.db.get_object_from_handle(ObjectId)
            photo_name = obj.get_path()
            if photo_name is not None and photo_name != "" and not Utils.find_file(photo_name):
                if cl:
                    print "Warning: media file %s was not found." \
                        % os.path.basename(photo_name)
                    self.bad_photo.append(ObjectId)
                else:
                    if missmedia_action == 0:
                        mmd = MissingMediaDialog(_("Media object could not be found"),
                        _("The file:\n %(file_name)s \nis referenced in the database, but no longer exists. " 
                        "The file may have been deleted or moved to a different location. " 
                        "You may choose to either remove the reference from the database, " 
                        "keep the reference to the missing file, or select a new file." 
                        ) % { 'file_name' : '<b>%s</b>' % photo_name },
                            remove_clicked, leave_clicked, select_clicked)
                        missmedia_action = mmd.default_action
                    elif missmedia_action == 1:
                        remove_clicked()
                    elif missmedia_action == 2:
                        leave_clicked()
                    elif missmedia_action == 3:
                        select_clicked()
            self.progress.step()

    def cleanup_empty_families(self,automatic):

        fhandle_list = self.db.get_family_handles()

        self.progress.set_pass(_('Looking for empty families'),
                               len(fhandle_list))
        for family_handle in fhandle_list:
            self.progress.step()
            
            family = self.db.get_family_from_handle(family_handle)
            father_handle = family.get_father_handle()
            mother_handle = family.get_mother_handle()

            if not father_handle and not mother_handle:
                self.empty_family.append(family_handle)
                self.delete_empty_family(family_handle)
                continue
            elif not father_handle and len(family.get_child_handle_list()) == 0:
                person = self.db.get_person_from_handle(mother_handle)
                person.remove_family_handle(family_handle)
                self.db.commit_person(person,self.trans)
                self.db.remove_family(family_handle,self.trans)
                self.empty_family.append(family_handle)
                continue
            elif not mother_handle and len(family.get_child_handle_list()) == 0:
                person = self.db.get_person_from_handle(father_handle)
                person.remove_family_handle(family_handle)
                self.db.commit_person(person,self.trans)
                self.db.remove_family(family_handle,self.trans)
                self.empty_family.append(family_handle)
                continue

    def delete_empty_family(self,family_handle):
        for key in self.db.get_person_handles(sort_handles=False):
            child = self.db.get_person_from_handle(key)
            child.remove_parent_family_handle(family_handle)
            child.remove_family_handle(family_handle)
        self.db.remove_family(family_handle,self.trans)

    def check_parent_relationships(self):

        fhandle_list = self.db.get_family_handles()
        self.progress.set_pass(_('Looking for broken parent relationships'),
                               len(fhandle_list))
        
        for family_handle in fhandle_list:
            self.progress.step()
            family = self.db.get_family_from_handle(family_handle)
            mother_handle = family.get_mother_handle()
            father_handle = family.get_father_handle()
            father = None
            if father_handle:
                father = self.db.get_person_from_handle(father_handle)
            mother = None
            if mother_handle:
                mother = self.db.get_person_from_handle(mother_handle)
            rel_type = family.get_relationship()

            if not father_handle and not mother_handle:
                continue
            elif not father_handle:
                if mother and mother.get_gender() == RelLib.Person.MALE:
                    # No father set and mother is male
                    family.set_father_handle(mother_handle)
                    family.set_mother_handle(None)
                    self.db.commit_family(family,self.trans)
            elif not mother_handle:
                if father and father.get_gender() == RelLib.Person.FEMALE:
                    # No mother set and father is female
                    family.set_mother_handle(father_handle)
                    family.set_father_handle(None)
                    self.db.commit_family(family,self.trans)
            else:
                fgender = father.get_gender()
                mgender = mother.get_gender()
                if rel_type != RelLib.Family.CIVIL_UNION:
                    if fgender == mgender and fgender != RelLib.Person.UNKNOWN:
                        family.set_relationship(RelLib.Family.CIVIL_UNION)
                        self.fam_rel.append(family_handle)
                        self.db.commit_family(family,self.trans)
                    elif fgender == RelLib.Person.FEMALE or mgender == RelLib.Person.MALE:
                        family.set_father_handle(mother_handle)
                        family.set_mother_handle(father_handle)
                        self.fam_rel.append(family_handle)
                        self.db.commit_family(family,self.trans)
                elif fgender != mgender:
                    family.set_relationship(RelLib.Family.UNKNOWN)
                    self.fam_rel.append(family_handle)
                    if fgender == RelLib.Person.FEMALE or mgender == RelLib.Person.MALE:
                        family.set_father_handle(mother_handle)
                        family.set_mother_handle(father_handle)
                    self.db.commit_family(family,self.trans)

    def check_events(self):
        self.progress.set_pass(_('Looking for event problems'),
                               self.db.get_number_of_people()
                               +self.db.get_number_of_families())
        
        for key in self.db.get_person_handles(sort_handles=False):
            self.progress.step()
            
            person = self.db.get_person_from_handle(key)
            birth_handle = person.get_birth_handle()
            if birth_handle:
                birth = self.db.get_event_from_handle(birth_handle)
                if not birth:
                    # The birth event referenced by the birth handle
                    # does not exist in the database
                    person.set_birth_handle("")
                    self.db.commit_person(person,self.trans)
                    self.invalid_events.append(key)
                else:
                    if not birth.get_name() == "Birth":
                        # Birth event was not of the type "Birth"
                        birth.set_name("Birth");
                        self.db.commit_event(birth,self.trans)
                        self.invalid_birth_events.append(key)
            death_handle = person.get_death_handle()
            if death_handle:
                death = self.db.get_event_from_handle(death_handle)
                if not death:
                    # The death event referenced by the death handle
                    # does not exist in the database
                    person.set_death_handle("")
                    self.db.commit_person(person,self.trans)
                    self.invalid_events.append(key)
                else:
                    if not death.get_name() == "Death":
                        # Death event was not of the type "Death"
                        death.set_name("Death");
                        self.db.commit_event(death,self.trans)
                        self.invalid_death_events.append(key)

            if person.get_event_list():
                for event_handle in person.get_event_list():
                    event = self.db.get_event_from_handle(event_handle)
                    if not event:
                        # The event referenced by the person
                        # does not exist in the database
                        #TODO: There is no better way?
                        person.set_event_list(
                            person.get_event_list().remove(event_handle))
                        self.db.commit_person(person,self.trans)
                        self.invalid_events.append(key)
            elif type(person.get_event_list()) != list:
                # event_list is None or other garbage
                person.set_event_list([])
                self.db.commit_person(person,self.trans)
                self.invalid_events.append(key)

        for key in self.db.get_family_handles():
            self.progress.step()
            family = self.db.get_family_from_handle(key)
            if family.get_event_list():
                for event_handle in family.get_event_list():
                    event = self.db.get_event_from_handle(event_handle)
                    if not event:
                        # The event referenced by the family
                        # does not exist in the database
                        family.set_event_list(
                            family.get_event_list().remove(event_handle))
                        self.db.commit_family(family,self.trans)
                        self.invalid_events.append(key)
            elif type(family.get_event_list()) != list:
                # event_list is None or other garbage
                family.set_event_list([])
                self.db.commit_family(family,self.trans)
                self.invalid_events.append(key)

    def check_place_references(self):
        elist = self.db.get_event_handles()
        
        self.progress.set_pass(_('Looking for place reference problems'),
                               len(elist))
        
        for key in elist:
            event = self.db.get_event_from_handle(key)
            place_handle = event.get_place_handle()
            if place_handle:
                place = self.db.get_place_from_handle(place_handle)
                if not place:
                    # The referenced place does not exist in the database
                    event.set_place_handle("")
                    self.db.commit_event(event,self.trans)
                    self.invalid_place_references.append(key)

    def check_source_references(self):
        known_handles = self.db.get_source_handles()

        total = self.db.get_number_of_people() + self.db.get_number_of_families() + \
                self.db.get_number_of_events() + self.db.get_number_of_places() + \
                self.db.get_number_of_media_objects() + \
                self.db.get_number_of_sources()

        self.progress.set_pass(_('Looking for source reference problems'),
                               total)
        
        for handle in self.db.person_map.keys():
            self.progress.step()
            info = self.db.person_map[handle]
            person = RelLib.Person()
            person.unserialize(info)
            handle_list = person.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Source' and
                            item[1] not in known_handles ]
            if bad_handles:
                person.remove_source_references(bad_handles)
                self.db.commit_person(person,self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_source_references]
                self.invalid_source_references += new_bad_handles

        for handle in self.db.family_map.keys():
            self.progress.step()
            info = self.db.family_map[handle]
            family = RelLib.Family()
            family.unserialize(info)
            handle_list = family.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Source' and
                            item[1] not in known_handles ]
            if bad_handles:
                family.remove_source_references(bad_handles)
                self.db.commit_family(family,self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_source_references]
                self.invalid_source_references += new_bad_handles

        for handle in self.db.place_map.keys():
            self.progress.step()
            info = self.db.place_map[handle]
            place = RelLib.Place()
            place.unserialize(info)
            handle_list = place.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Source' and
                            item[1] not in known_handles ]
            if bad_handles:
                place.remove_source_references(bad_handles)
                self.db.commit_place(place,self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_source_references]
                self.invalid_source_references += new_bad_handles
            
        for handle in known_handles:
            self.progress.step()
            info = self.db.source_map[handle]
            source = RelLib.Source()
            source.unserialize(info)
            handle_list = source.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Source' and
                            item[1] not in known_handles ]
            if bad_handles:
                source.remove_source_references(bad_handles)
                self.db.commit_source(source,self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_source_references]
                self.invalid_source_references += new_bad_handles

        for handle in self.db.media_map.keys():
            self.progress.step()
            info = self.db.media_map[handle]
            obj = RelLib.MediaObject()
            obj.unserialize(info)
            handle_list = obj.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Source' and
                            item[1] not in known_handles ]
            if bad_handles:
                obj.remove_source_references(bad_handles)
                self.db.commit_object(obj,self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_source_references]
                self.invalid_source_references += new_bad_handles

        for handle in self.db.event_map.keys():
            self.progress.step()
            info = self.db.event_map[handle]
            event = RelLib.Event()
            event.unserialize(info)
            handle_list = event.get_referenced_handles_recursively()
            bad_handles = [ item[1] for item in handle_list
                            if item[0] == 'Source' and
                            item[1] not in known_handles ]
            if bad_handles:
                event.remove_source_references(bad_handles)
                self.db.commit_event(event,self.trans)
                new_bad_handles = [handle for handle in bad_handles if handle
                                   not in self.invalid_source_references]
                self.invalid_source_references += new_bad_handles

    def build_report(self,cl=0):
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
        place_references = len(self.invalid_place_references)
        source_references = len(self.invalid_source_references)

        errors = blink + efam + photos + rel + person \
                 + event_invalid + place_references + source_references
        
        if errors == 0:
            if cl:
                print "No errors were found: the database has passed internal checks."
            else:
                OkDialog(_("No errors were found"),
                         _('The database has passed internal checks'),
                         self.parent.topWindow)
            return 0

        self.text = cStringIO.StringIO()
        if blink > 0:
            if blink == 1:
                self.text.write(_("1 broken child/family link was fixed\n"))
            else:
                self.text.write(_("%d broken child/family links were found\n") % blink)
            for (person_handle,family_handle) in self.broken_links:
                person = self.db.get_person_from_handle(person_handle)
                if person:
                    cn = person.get_primary_name().get_name()
                else:
                    cn = _("Non existing child")
                try:
                    family = self.db.get_family_from_handle(family_handle)
                    pn = Utils.family_name(family,self.db)
                except:
                    pn = _("Unknown")
                self.text.write('\t')
                self.text.write(_("%s was removed from the family of %s\n") % (cn,pn))

        if plink > 0:
            if plink == 1:
                self.text.write(_("1 broken spouse/family link was fixed\n"))
            else:
                self.text.write(_("%d broken spouse/family links were found\n") % plink)
            for (person_handle,family_handle) in self.broken_parent_links:
                person = self.db.get_person_from_handle(person_handle)
                if person:
                    cn = person.get_primary_name().get_name()
                else:
                    cn = _("Non existing person")
                family = self.db.get_family_from_handle(family_handle)
                if family:
                    pn = Utils.family_name(family,self.db)
                else:
                    pn = family_handle
                self.text.write('\t')
                self.text.write(_("%s was restored to the family of %s\n") % (cn,pn))

        if slink > 0:
            if slink == 1:
                self.text.write(_("1 duplicate spouse/family link was found\n"))
            else:
                self.text.write(_("%d duplicate spouse/family links were found\n") % slink)
            for (person_handle,family_handle) in self.broken_parent_links:
                person = self.db.get_person_from_handle(person_handle)
                if person:
                    cn = person.get_primary_name().get_name()
                else:
                    cn = _("Non existing person")
                family = self.db.get_family_from_handle(family_handle)
                if family:
                    pn = Utils.family_name(family,self.db)
                else:
                    pn = _("None")
                self.text.write('\t')
                self.text.write(_("%s was restored to the family of %s\n") % (cn,pn))

        if efam == 1:
            self.text.write(_("1 empty family was found\n"))
            self.text.write("\t%s\n" % self.empty_family[0])
        elif efam > 1:
            self.text.write(_("%d empty families were found\n") % efam)
        if rel == 1:
            self.text.write(_("1 corrupted family relationship fixed\n"))
        elif rel > 1:
            self.text.write(_("%d corrupted family relationship fixed\n") % rel)
        if photos == 1:
            self.text.write(_("1 media object was referenced, but not found\n"))
        elif photos > 1:
            self.text.write(_("%d media objects were referenced, but not found\n") % photos)
        if bad_photos == 1:
            self.text.write(_("Reference to 1 missing media object was kept\n"))
        elif bad_photos > 1:
            self.text.write(_("References to %d media objects were kept\n") % bad_photos)
        if replaced_photos == 1:
            self.text.write(_("1 missing media object was replaced\n"))
        elif replaced_photos > 1:
            self.text.write(_("%d missing media objects were replaced\n") % replaced_photos)
        if removed_photos == 1:
            self.text.write(_("1 missing media object was removed\n"))
        elif removed_photos > 1:
            self.text.write(_("%d missing media objects were removed\n") % removed_photos)
        if event_invalid == 1:
            self.text.write(_("1 invalid event reference was removed\n"))
        elif event_invalid > 1:
            self.text.write(_("%d invalid event references were removed\n") % event_invalid)
        if birth_invalid == 1:
            self.text.write(_("1 invalid birth event name was fixed\n"))
        elif birth_invalid > 1:
            self.text.write(_("%d invalid birth event names were fixed\n") % birth_invalid)
        if death_invalid == 1:
            self.text.write(_("1 invalid death event name was fixed\n"))
        elif death_invalid > 1:
            self.text.write(_("%d invalid death event names were fixed\n") % death_invalid)
        if place_references == 1:
            self.text.write(_("1 place was referenced but not found\n"))
        elif place_references > 1:
            self.text.write(_("%d places were referenced, but not found\n") % place_references)
        if source_references == 1:
            self.text.write(_("1 source was referenced but not found\n"))
        elif source_references > 1:
            self.text.write(_("%d sources were referenced, but not found\n") % source_references)

        return errors

#-------------------------------------------------------------------------
#
# Display the results
#
#-------------------------------------------------------------------------
class Report:
    def __init__(self,text,parent,cl=0):
        if cl:
            print text
            return
        self.text = text
        self.parent = parent

        self.win_key = self

        base = os.path.dirname(__file__)
        glade_file = base + os.sep + "summary.glade"
        topDialog = gtk.glade.XML(glade_file,"summary","gramps")
        topDialog.signal_autoconnect({
            "destroy_passed_object"  : self.close_result,
            "on_result_delete_event" : self.on_result_delete_event,
        })
        
        self.title = _("Integrity Check Results")
        self.window = topDialog.get_widget("summary")
        self.window.set_icon(self.parent.topWindow.get_icon())
        textwindow = topDialog.get_widget("textwindow")
        textwindow.get_buffer().set_text(self.text)

        Utils.set_titles(self.window,topDialog.get_widget("title"),self.title)

        self.add_result_to_menu()
        self.window.show()

    def on_result_delete_event(self,obj,b):
        self.remove_result_from_menu()

    def close_result(self,obj):
        self.remove_result_from_menu()
        self.window.destroy()

    def add_result_to_menu(self):
        self.parent.child_windows[self.win_key] = self.window
        self.result_parent_menu_item = gtk.MenuItem(self.title)
        self.result_parent_menu_item.connect("activate",self.present_result)
        self.result_parent_menu_item.show()
        self.parent.winsmenu.append(self.result_parent_menu_item)

    def remove_result_from_menu(self):
        del self.parent.child_windows[self.win_key]
        self.result_parent_menu_item.destroy()

    def present_result(self,obj):
        self.window.present()

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class CheckOptions(Tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self,name,person_id=None):
        Tool.ToolOptions.__init__(self,name,person_id)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
from PluginMgr import register_tool

register_tool(
    name = 'check',
    category = Tool.TOOL_DBFIX,
    tool_class = Check,
    options_class = CheckOptions,
    modes = Tool.MODE_GUI | Tool.MODE_CLI,
    translated_name = _("Check and repair database"),
    status = _("Stable"),
    author_name = "Donald N. Allingham",
    author_email = "don@gramps-project.org",
    description=_("Checks the database for integrity problems, fixing the problems that it can")
    )
