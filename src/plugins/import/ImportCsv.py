#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007       Douglas S. Blank
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2008       Raphael Ackerman
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

"Import from CSV Spreadsheet"

#-------------------------------------------------------------------------
#
# Standard Python Modules
#
#-------------------------------------------------------------------------
import time
import csv
import codecs
import cStringIO

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".ImportCSV")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.ggettext import sgettext as _
from gen.ggettext import ngettext
import gen.lib
from gen.db import DbTxn
from QuestionDialog import ErrorDialog
from DateHandler import parser as _dp
from Utils import gender as gender_map
from Utils import create_id
from gui.utils import ProgressMeter
from gen.lib.eventroletype import EventRoleType

#-------------------------------------------------------------------------
#
# Support Functions
#
#-------------------------------------------------------------------------
def get_primary_event_ref_from_type(db, person, event_name):
    """
    >>> get_primary_event_ref_from_type(db, Person(), "Baptism"):
    """
    for ref in person.event_ref_list:
        if ref.get_role() == EventRoleType.PRIMARY:
            event = db.get_event_from_handle(ref.ref)
            if event and event.type.is_type(event_name):
                return ref
    return None

#-------------------------------------------------------------------------
#
# Encoding support for CSV, from http://docs.python.org/lib/csv-examples.html
#
#-------------------------------------------------------------------------
class UTF8Recoder(object):
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, encoding="utf-8", **kwds):
        self.first_row = True
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, **kwds)

    def next(self):
        row = self.reader.next()
        rowlist = [unicode(s, "utf-8") for s in row]
        # Add check for Byte Order Mark (Windows, Notepad probably):
        if self.first_row:
            if len(rowlist) > 0 and rowlist[0].startswith(u"\ufeff"):
                rowlist[0] = rowlist[0][1:]
            self.first_row = False
        return rowlist

    def __iter__(self):
        return self

class UnicodeWriter(object):
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, **kwds)
        self.stream = f
        self.encoder = codecs.getencoder(encoding)

    def writerow(self, row):
        self.writer.writerow([s.encode('utf-8') for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        # ... and reencode it into the target encoding
        data, length = self.encoder(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        map(self.writerow, rows)

    def close(self):
        self.stream.close()

#-------------------------------------------------------------------------
#
# Support and main functions
#
#-------------------------------------------------------------------------
def rd(line_number, row, col, key, default = None):
    """ Return Row data by column name """
    if key in col:
        if col[key] >= len(row):
            LOG.warn("missing '%s, on line %d" % (key, line_number))
            return default
        retval = row[col[key]].strip()
        if retval == "":
            return default
        else:
            return retval
    else:
        return default

def cleanup_column_name(column):
    """ Handle column aliases for CSV spreadsheet import and SQL """
    retval = column
    # Title case:
    if retval in ["Lastname", 
                  "Surname", _("Surname")]:
        return "surname"
    elif retval in ["Firstname", 
                    "Given name", _("Given name"), 
                    "Given", _("Given")]:
        return "firstname"
    elif retval in ["Callname", 
                    "Call name", _("Call name"),
                    "Call", _("Call")]:
        return "callname"
    elif retval in ["Title", _("Person|Title")]:
        return "title"
    elif retval in ["Prefix", _("Prefix")]:
        return "prefix"
    elif retval in ["Suffix", _("Suffix")]:
        return "suffix"
    elif retval in ["Gender", _("Gender")]:
        return "gender"
    elif retval in ["Source", _("Source")]:
        return "source"
    elif retval in ["Note", _("Note")]:
        return "note"
    elif retval in ["Birthplace", 
                    "Birth place", _("Birth place")]:
        return "birthplace"
    elif retval in ["Birthdate", 
                    "Birth date", _("Birth date")]:
        return "birthdate"
    elif retval in ["Birthsource", 
                    "Birth source", _("Birth source")]:
        return "birthsource"
    elif retval in ["Baptismplace", 
                    "Baptism place", _("Baptism place")]:
        return "baptismplace"
    elif retval in ["Baptismdate", 
                    "Baptism date", _("Baptism date")]:
        return "baptismdate"
    elif retval in ["Baptismsource", 
                    "Baptism source", _("Baptism source")]:
        return "baptismsource"
    elif retval in ["Burialplace", 
                    "Burial place", _("Burial place")]:
        return "burialplace"
    elif retval in ["Burialdate", 
                    "Burial date", _("Burial date")]:
        return "burialdate"
    elif retval in ["Burialsource", 
                    "Burial source", _("Burial source")]:
        return "burialsource"
    elif retval in ["Deathplace", 
                    "Death place", _("Death place")]:
        return "deathplace"
    elif retval in ["Deathdate", 
                    "Death date", _("Death date")]:
        return "deathdate"
    elif retval in ["Deathsource", 
                    "Death source", _("Death source")]:
        return "deathsource"
    elif retval in ["Deathcause", 
                    "Death cause", _("Death cause")]:
        return "deathcause"
    elif retval in ["Grampsid", "ID",
                    "Gramps id", _("Gramps ID")]:
        return "grampsid"
    elif retval in ["Person", _("Person")]:
        return "person"
    # ----------------------------------
    elif retval in ["Child", _("Child")]:
        return "child"
    elif retval in ["Source", _("Source")]:
        return "source"
    elif retval in ["Family", _("Family")]:
        return "family"
    # ----------------------------------
    elif retval in ["Mother", _("Mother"), 
                    "Wife", _("Wife"),
                    "Parent2", _("Parent2")]:
        return "wife"
    elif retval in ["Father", _("Father"), 
                    "Husband", _("Husband"),
                    "Parent1", _("Parent1")]:
        return "husband"
    elif retval in ["Marriage", _("Marriage")]:
        return "marriage"
    elif retval in ["Date", _("Date")]:
        return "date"
    elif retval in ["Place", _("Place")]:
        return "place"
    # lowercase
    elif retval in ["lastname", "last_name", 
                  "surname", _("surname")]:
        return "surname"
    elif retval in ["firstname", "first_name", "given_name",
                    "given name", _("given name"), 
                    "given", _("given")]:
        return "firstname"
    elif retval in ["callname", "call_name",
                    "call name", 
                    "call", _("call")]:
        return "callname"
    elif retval in ["title", _("Person|title")]:
        return "title"
    elif retval in ["prefix", _("prefix")]:
        return "prefix"
    elif retval in ["suffix", _("suffix")]:
        return "suffix"
    elif retval in ["gender", _("gender")]:
        return "gender"
    elif retval in ["source", _("source")]:
        return "source"
    elif retval in ["note", _("note")]:
        return "note"
    elif retval in ["birthplace", "birth_place",
                    "birth place", _("birth place")]:
        return "birthplace"
    elif retval in ["birthdate", "birth_date",
                    "birth date", _("birth date")]:
        return "birthdate"
    elif retval in ["birthsource", "birth_source",
                    "birth source", _("birth source")]:
        return "birthsource"
    elif retval in ["baptismplace", 
                    "baptism place", _("baptism place")]:
        return "baptismplace"
    elif retval in ["baptismdate", 
                    "baptism date", _("baptism date")]:
        return "baptismdate"
    elif retval in ["baptismsource", 
                    "baptism source", _("baptism source")]:
        return "baptismsource"
    elif retval in ["burialplace", 
                    "burial place", _("burial place")]:
        return "burialplace"
    elif retval in ["burialdate", 
                    "burial date", _("burial date")]:
        return "burialdate"
    elif retval in ["burialsource", 
                    "burial source", _("burial source")]:
        return "burialsource"
    elif retval in ["deathplace", "death_place",
                    "death place", _("death place")]:
        return "deathplace"
    elif retval in ["deathdate", "death_date",
                    "death date", _("death date")]:
        return "deathdate"
    elif retval in ["deathsource", "death_source",
                    "death source", _("death source")]:
        return "deathsource"
    elif retval in ["deathcause", "death_cause",
                    "death cause", _("death cause")]:
        return "deathcause"
    elif retval in ["grampsid", "id", "gramps_id", 
                    "gramps id", _("Gramps ID")]:
        return "grampsid"
    elif retval in ["person", _("person")]:
        return "person"
    # ----------------------------------
    elif retval in ["child", _("child")]:
        return "child"
    elif retval in ["source", _("source")]:
        return "source"
    elif retval in ["family", _("family")]:
        return "family"
    # ----------------------------------
    elif retval in ["mother", _("mother"), 
                    "wife", _("wife"),
                    "parent2", _("parent2")]:
        return "wife"
    elif retval in ["father", _("father"), 
                    "husband", _("husband"),
                    "parent1", _("parent1")]:
        return "husband"
    elif retval in ["marriage", _("marriage")]:
        return "marriage"
    elif retval in ["date", _("date")]:
        return "date"
    elif retval in ["place", _("place")]:
        return "place"
    #----------------------------------------------------
    return retval

def importData(db, filename, callback=None):
    g = CSVParser(db, filename, callback)
    g.process()

#-------------------------------------------------------------------------
#
# CSV Parser 
#
#-------------------------------------------------------------------------
class CSVParser(object):
    def __init__(self, db, filename, callback):
        self.db = db
        self.filename = filename
        self.callback = callback

    def readCSV(self):
        fp = None
        reader = []
        try:
            fp = open(self.filename, "rb")
            reader = UnicodeReader(fp) 
        except IOError, msg:
            errmsg = _("%s could not be opened\n") % self.filename
            ErrorDialog(errmsg,str(msg))
            try:
                fp.close()
            except:
                pass
            return None
        try:
            data = [[r.strip() for r in row] for row in reader]
        except csv.Error, e:
            ErrorDialog(_('format error: file %(fname)s, line %(line)d: %(zero)s') % {
                        'fname' : self.filename, 'line' : reader.line_num, 'zero' : e } )
            try:
                fp.close()
            except:
                pass
            return None
        return data

    def lookup(self, type, id):
        if id is None: return None
        if type == "family":
            if id.startswith("[") and id.endswith("]"):
                id = id[1:-1]
                db_lookup = self.db.get_family_from_gramps_id(id)
                if db_lookup is None:
                    return self.lookup(type, id)
                else:
                    return db_lookup
            elif id.lower() in self.fref:
                return self.fref[id.lower()]
            else:
                return None
        elif type == "person":
            if id.startswith("[") and id.endswith("]"):
                id = id[1:-1]
                db_lookup = self.db.get_person_from_gramps_id(id)
                if db_lookup is None:
                    return self.lookup(type, id)
                else:
                    return db_lookup
            elif id.lower() in self.pref:
                return self.pref[id.lower()]
            else:
                return None
        else:
            LOG.warn("invalid lookup type in CSV import: '%s'" % type)
            return None

    def storeup(self, type, id, object):
        if id.startswith("[") and id.endswith("]"):
            id = id[1:-1]
            #return # do not store gramps people; go look them up
        if type == "person":
            self.pref[id.lower()] = object
        elif type == "family":
            self.fref[id.lower()] = object
        else:
            LOG.warn("invalid storeup type in CSV import: '%s'" % type)

    def process(self):
        progress = ProgressMeter(_('CSV Import'))
        progress.set_pass(_('Reading data...'), 1)
        data = self.readCSV() 
        progress.set_pass(_('Importing data...'), len(data))
        with DbTxn(_("CSV import"), self.db, batch=True) as self.trans:
            self.db.disable_signals()
            t = time.time()
            self.lineno = 0
            self.index = 0
            self.fam_count = 0
            self.indi_count = 0
            self.pref  = {} # person ref, internal to this sheet
            self.fref  = {} # family ref, internal to this sheet        
            header = None
            line_number = 0
            for row in data:
                progress.step()
                line_number += 1
                if "".join(row) == "": # no blanks are allowed inside a table
                    header = None # clear headers, ready for next "table"
                    continue
                ######################################
                if header is None:
                    header = [cleanup_column_name(r) for r in row]
                    col = {}
                    count = 0
                    for key in header:
                        col[key] = count
                        count += 1
                    continue
                # three different kinds of data: person, family, and marriage
                if (("marriage" in header) or
                    ("husband" in header) or
                    ("wife" in header)):
                    # marriage, husband, wife
                    marriage_ref   = rd(line_number, row, col, "marriage")
                    husband  = rd(line_number, row, col, "husband")
                    wife     = rd(line_number, row, col, "wife")
                    marriagedate = rd(line_number, row, col, "date")
                    marriageplace = rd(line_number, row, col, "place")
                    marriagesource = rd(line_number, row, col, "source")
                    note = rd(line_number, row, col, "note")
                    wife = self.lookup("person", wife)
                    husband = self.lookup("person", husband)
                    if husband is None and wife is None:
                        # might have children, so go ahead and add
                        LOG.warn("no parents on line %d; adding family anyway" % line_number)
                    family = self.get_or_create_family(marriage_ref, husband, wife)
                    # adjust gender, if not already provided
                    if husband:
                        # this is just a guess, if unknown
                        if husband.get_gender() == gen.lib.Person.UNKNOWN:
                            husband.set_gender(gen.lib.Person.MALE)
                            self.db.commit_person(husband, self.trans)
                    if wife:
                        # this is just a guess, if unknown
                        if wife.get_gender() == gen.lib.Person.UNKNOWN:
                            wife.set_gender(gen.lib.Person.FEMALE)
                            self.db.commit_person(wife, self.trans)
                    if marriage_ref:
                        self.storeup("family", marriage_ref.lower(), family)
                    if marriagesource:
                        # add, if new
                        new, marriagesource = self.get_or_create_source(marriagesource)
                    if marriageplace:
                        # add, if new
                        new, marriageplace = self.get_or_create_place(marriageplace)
                    if marriagedate:
                        marriagedate = _dp.parse(marriagedate)
                    if marriagedate or marriageplace or marriagesource or note:
                        # add, if new; replace, if different
                        new, marriage = self.get_or_create_event(family, gen.lib.EventType.MARRIAGE, 
                                                                 marriagedate, marriageplace, marriagesource)
                        if new:
                            mar_ref = gen.lib.EventRef()
                            mar_ref.set_reference_handle(marriage.get_handle())
                            family.add_event_ref(mar_ref)
                            self.db.commit_family(family, self.trans)
                        # only add note to event:
                        # append notes, if previous notes
                        if note:
                            previous_notes_list = marriage.get_note_list()
                            updated_note = False
                            for note_handle in previous_notes_list:
                                previous_note = self.db.get_note_from_handle(note_handle)
                                if previous_note.type == gen.lib.NoteType.EVENT:
                                    previous_text = previous_note.get()
                                    if note not in previous_text:
                                        note = previous_text + "\n" + note
                                    previous_note.set(note)
                                    self.db.commit_note(previous_note, self.trans)
                                    updated_note = True
                                    break
                            if not updated_note:
                                # add new note here
                                new_note = gen.lib.Note()
                                new_note.handle = create_id()
                                new_note.type.set(gen.lib.NoteType.EVENT)
                                new_note.set(note)
                                self.db.add_note(new_note, self.trans)
                                marriage.add_note(new_note.handle)
                            self.db.commit_event(marriage, self.trans)
                elif "family" in header:
                    # family, child
                    family_ref   = rd(line_number, row, col, "family")
                    if family_ref is None:
                        LOG.warn("no family reference found for family on line %d" % line_number)
                        continue # required
                    child   = rd(line_number, row, col, "child")
                    source  = rd(line_number, row, col, "source")
                    note  = rd(line_number, row, col, "note")
                    gender  = rd(line_number, row, col, "gender")
                    child = self.lookup("person", child)
                    family = self.lookup("family", family_ref)
                    if family is None:
                        LOG.warn("no matching family reference found for family on line %d" % line_number)
                        continue
                    if child is None:
                        LOG.warn("no matching child reference found for family on line %d" % line_number)
                        continue
                    # is this child already in this family? If so, don't add
                    LOG.debug("children: %s", [ref.ref for ref in family.get_child_ref_list()])
                    LOG.debug("looking for: %s", child.get_handle())
                    if child.get_handle() not in [ref.ref for ref in family.get_child_ref_list()]:
                        # add child to family
                        LOG.debug("   adding child [%s] to family [%s]", child.get_gramps_id(), 
                                  family.get_gramps_id())
                        childref = gen.lib.ChildRef()
                        childref.set_reference_handle(child.get_handle())
                        family.add_child_ref( childref)
                        self.db.commit_family(family, self.trans)
                        child.add_parent_family_handle(family.get_handle())
                    if gender:
                        # replace
                        gender = gender.lower()
                        if gender == gender_map[gen.lib.Person.MALE].lower():
                            gender = gen.lib.Person.MALE
                        elif gender == gender_map[gen.lib.Person.FEMALE].lower():
                            gender = gen.lib.Person.FEMALE
                        else:
                            gender = gen.lib.Person.UNKNOWN
                        child.set_gender(gender)
                    if source:
                        # add, if new
                        new, source = self.get_or_create_source(source)
                        source_refs = child.get_source_references()
                        found = 0
                        for ref in source_refs:
                            LOG.debug("child: %s looking for ref: %s", ref.ref, source.get_handle())
                            if ref.ref == source.get_handle():
                                found = 1
                        if not found:
                            sref = gen.lib.SourceRef()
                            sref.set_reference_handle(source.get_handle())
                            child.add_source_reference(sref)
                    # put note on child
                    if note:
                        # append notes, if previous notes
                        previous_notes_list = child.get_note_list()
                        updated_note = False
                        for note_handle in previous_notes_list:
                            previous_note = self.db.get_note_from_handle(note_handle)
                            if previous_note.type == gen.lib.NoteType.PERSON:
                                previous_text = previous_note.get()
                                if note not in previous_text:
                                    note = previous_text + "\n" + note
                                previous_note.set(note)
                                self.db.commit_note(previous_note, self.trans)
                                updated_note = True
                                break
                        if not updated_note:
                            # add new note here
                            new_note = gen.lib.Note()
                            new_note.handle = create_id()
                            new_note.type.set(gen.lib.NoteType.PERSON)
                            new_note.set(note)
                            self.db.add_note(new_note, self.trans)
                            child.add_note(new_note.handle)
                    self.db.commit_person(child, self.trans)
                elif "surname" in header:              # person data
                    # surname, and any of the following
                    surname   = rd(line_number, row, col, "surname")
                    firstname = rd(line_number, row, col, "firstname", "")
                    callname  = rd(line_number, row, col, "callname")
                    title     = rd(line_number, row, col, "title")
                    prefix    = rd(line_number, row, col, "prefix")
                    suffix    = rd(line_number, row, col, "suffix")
                    gender    = rd(line_number, row, col, "gender")
                    source    = rd(line_number, row, col, "source")
                    note      = rd(line_number, row, col, "note")
                    birthplace  = rd(line_number, row, col, "birthplace")
                    birthdate   = rd(line_number, row, col, "birthdate")
                    birthsource = rd(line_number, row, col, "birthsource")
                    baptismplace  = rd(line_number, row, col, "baptismplace")
                    baptismdate   = rd(line_number, row, col, "baptismdate")
                    baptismsource = rd(line_number, row, col, "baptismsource")
                    burialplace  = rd(line_number, row, col, "burialplace")
                    burialdate   = rd(line_number, row, col, "burialdate")
                    burialsource = rd(line_number, row, col, "burialsource")
                    deathplace  = rd(line_number, row, col, "deathplace")
                    deathdate   = rd(line_number, row, col, "deathdate")
                    deathsource = rd(line_number, row, col, "deathsource")
                    deathcause  = rd(line_number, row, col, "deathcause")
                    grampsid    = rd(line_number, row, col, "grampsid")
                    person_ref  = rd(line_number, row, col, "person")
                    #########################################################
                    # if this person already exists, don't create them
                    person = self.lookup("person", person_ref)
                    if person is None:
                        if surname is None:
                            LOG.warn("empty surname for new person on line %d" % line_number)
                            surname = ""
                        # new person
                        person = self.create_person()
                        name = gen.lib.Name()
                        name.set_type(gen.lib.NameType(gen.lib.NameType.BIRTH))
                        name.set_first_name(firstname)
                        surname_obj = gen.lib.Surname()
                        surname_obj.set_surname(surname)
                        name.add_surname(surname_obj)
                        person.set_primary_name(name)
                    else:
                        name = person.get_primary_name()
                    #########################################################
                    if person_ref is not None:
                        self.storeup("person", person_ref, person)
                    # replace
                    if surname is not None:
                        name.get_primary_surname().set_surname(surname)
                    if firstname is not None:
                        name.set_first_name(firstname)
                    if callname is not None:
                        name.set_call_name(callname)
                    if title is not None:
                        name.set_title(title)
                    if prefix is not None:
                        name.get_primary_surname().set_prefix(prefix)
                        name.group_as = '' # HELP? what should I do here?
                    if suffix is not None:
                        name.set_suffix(suffix)
                    if note is not None:
                        # append notes, if previous notes
                        previous_notes_list = person.get_note_list()
                        updated_note = False
                        for note_handle in previous_notes_list:
                            previous_note = self.db.get_note_from_handle(note_handle)
                            if previous_note.type == gen.lib.NoteType.PERSON:
                                previous_text = previous_note.get()
                                if note not in previous_text:
                                    note = previous_text + "\n" + note
                                previous_note.set(note)
                                self.db.commit_note(previous_note, self.trans)
                                updated_note = True
                                break
                        if not updated_note:
                            # add new note here
                            new_note = gen.lib.Note()
                            new_note.handle = create_id()
                            new_note.type.set(gen.lib.NoteType.PERSON)
                            new_note.set(note)
                            self.db.add_note(new_note, self.trans)
                            person.add_note(new_note.handle)
                    if grampsid is not None:
                        person.gramps_id = grampsid
                    elif person_ref is not None:
                        if person_ref.startswith("[") and person_ref.endswith("]"):
                            person.gramps_id = person_ref[1:-1]
                    if person.get_gender() == gen.lib.Person.UNKNOWN and gender is not None:
                        gender = gender.lower()
                        if gender == gender_map[gen.lib.Person.MALE].lower():
                            gender = gen.lib.Person.MALE
                        elif gender == gender_map[gen.lib.Person.FEMALE].lower():
                            gender = gen.lib.Person.FEMALE
                        else:
                            gender = gen.lib.Person.UNKNOWN
                        person.set_gender(gender)
                    #########################################################
                    # add if new, replace if different
                    # Birth:
                    if birthdate is not None:
                        birthdate = _dp.parse(birthdate)
                    if birthplace is not None:
                        new, birthplace = self.get_or_create_place(birthplace)
                    if birthsource is not None:
                        new, birthsource = self.get_or_create_source(birthsource)
                    if birthdate or birthplace or birthsource:
                        new, birth = self.get_or_create_event(person, 
                             gen.lib.EventType.BIRTH, birthdate, 
                             birthplace, birthsource)
                        birth_ref = person.get_birth_ref()
                        if birth_ref is None:
                            # new
                            birth_ref = gen.lib.EventRef()
                        birth_ref.set_reference_handle( birth.get_handle())
                        person.set_birth_ref( birth_ref)
                    # Baptism:
                    if baptismdate is not None:
                        baptismdate = _dp.parse(baptismdate)
                    if baptismplace is not None:
                        new, baptismplace = self.get_or_create_place(baptismplace)
                    if baptismsource is not None:
                        new, baptismsource = self.get_or_create_source(baptismsource)
                    if baptismdate or baptismplace or baptismsource:
                        new, baptism = self.get_or_create_event(person, 
                             gen.lib.EventType.BAPTISM, baptismdate, 
                             baptismplace, baptismsource)
                        baptism_ref = get_primary_event_ref_from_type(self.db, person, "Baptism")
                        if baptism_ref is None:
                            # new
                            baptism_ref = gen.lib.EventRef()
                        baptism_ref.set_reference_handle( baptism.get_handle())
                        person.add_event_ref( baptism_ref)
                    # Death:
                    if deathdate is not None:
                        deathdate = _dp.parse(deathdate)
                    if deathplace is not None:
                        new, deathplace = self.get_or_create_place(deathplace)
                    if deathsource is not None:
                        new, deathsource = self.get_or_create_source(deathsource)
                    if deathdate or deathplace or deathsource or deathcause:
                        new, death = self.get_or_create_event(person, gen.lib.EventType.DEATH, 
                                                              deathdate, deathplace, deathsource)
                        if deathcause:
                            death.set_description(deathcause)
                            self.db.commit_event(death, self.trans)
                        death_ref = person.get_death_ref()
                        if death_ref is None:
                            # new
                            death_ref = gen.lib.EventRef()
                        death_ref.set_reference_handle(death.get_handle())
                        person.set_death_ref(death_ref)
                    # Burial:
                    if burialdate is not None:
                        burialdate = _dp.parse(burialdate)
                    if burialplace is not None:
                        new, burialplace = self.get_or_create_place(burialplace)
                    if burialsource is not None:
                        new, burialsource = self.get_or_create_source(burialsource)
                    if burialdate or burialplace or burialsource:
                        new, burial = self.get_or_create_event(person, 
                             gen.lib.EventType.BURIAL, burialdate, 
                             burialplace, burialsource)
                        burial_ref = get_primary_event_ref_from_type(self.db, person, "Burial")
                        if burial_ref is None:
                            # new
                            burial_ref = gen.lib.EventRef()
                        burial_ref.set_reference_handle( burial.get_handle())
                        person.add_event_ref( burial_ref)
                    if source:
                        # add, if new
                        new, source = self.get_or_create_source(source)
                        source_refs = person.get_source_references()
                        found = 0
                        for ref in source_refs:
                            LOG.debug("person: %s looking for ref: %s", ref.ref, source.get_handle())
                            if ref.ref == source.get_handle():
                                found = 1
                        if not found:
                            sref = gen.lib.SourceRef()
                            sref.set_reference_handle(source.get_handle())
                            person.add_source_reference(sref)
                    self.db.commit_person(person, self.trans)
                else:
                    LOG.warn("ignoring line %d" % line_number)
            t = time.time() - t
            msg = ngettext('Import Complete: %d second','Import Complete: %d seconds', t ) % t

        self.db.enable_signals()
        self.db.request_rebuild()
        LOG.debug(msg)
        LOG.debug("New Families: %d" % self.fam_count)
        LOG.debug("New Individuals: %d" % self.indi_count)
        progress.close()
        return None

    def get_or_create_family(self, family_ref, husband, wife):
        # if a gramps_id and exists:
        LOG.debug("get_or_create_family")
        if family_ref.startswith("[") and family_ref.endswith("]"):
            family = self.db.get_family_from_gramps_id(family_ref[1:-1])
            if family:
                # don't delete, only add
                fam_husband_handle = family.get_father_handle()
                fam_wife_handle = family.get_mother_handle()
                if husband:
                    if husband.get_handle() != fam_husband_handle:
                        # this husband is not the same old one! Add him!
                        family.set_father_handle(husband.get_handle())
                if wife:
                    if wife.get_handle() != fam_wife_handle:
                        # this wife is not the same old one! Add her!
                        family.set_mother_handle(wife.get_handle())
                LOG.debug("   returning existing family")
                return family
        # if not, create one:
        family = gen.lib.Family()
        # was marked with a gramps_id, but didn't exist, so we'll use it:
        if family_ref.startswith("[") and family_ref.endswith("]"):
            family.set_gramps_id(family_ref[1:-1])
        # add it:
        family.set_handle(self.db.create_id())
        if husband:
            family.set_father_handle(husband.get_handle())
            husband.add_family_handle(family.get_handle())
        if wife:
            family.set_mother_handle(wife.get_handle())
            wife.add_family_handle(family.get_handle())
        if husband and wife:
            family.set_relationship(gen.lib.FamilyRelType.MARRIED)
        self.db.add_family(family, self.trans)
        if husband:
            self.db.commit_person(husband, self.trans)
        if wife:
            self.db.commit_person(wife, self.trans)
        self.fam_count += 1
        return family
        
    def get_or_create_event(self, object, type, date=None, place=None, source=None):
        """ Add or find a type event on object """
        # first, see if it exists
        LOG.debug("get_or_create_event")
        ref_list = object.get_event_ref_list()
        LOG.debug("refs: %s", ref_list)
        # look for a match, and possible correction
        for ref in ref_list:
            event = self.db.get_event_from_handle(ref.ref)
            LOG.debug("   compare event type %s == %s", int(event.get_type()), type)
            if int(event.get_type()) == type:
                # Match! Let's update
                if date:
                    event.set_date_object(date)
                if place:
                    event.set_place_handle(place.get_handle())
                if source:
                    source_refs = event.get_source_references()
                    found = 0
                    for ref in source_refs:
                        LOG.debug("get_or_create_event: %s looking for ref: %s", ref.ref, source.get_handle())
                        if ref.ref == source.get_handle():
                            found = 1
                    if not found:
                        sref = gen.lib.SourceRef()
                        sref.set_reference_handle(source.get_handle())
                        event.add_source_reference(sref)
                self.db.commit_event(event,self.trans)
                LOG.debug("   returning existing event")
                return (0, event)
        # else create it:
        LOG.debug("   creating event")
        event = gen.lib.Event()
        if type:
            event.set_type(gen.lib.EventType(type))
        if date:
            event.set_date_object(date)
        if place:
            event.set_place_handle(place.get_handle())
        if source:
            source_refs = event.get_source_references()
            found = 0
            for ref in source_refs:
                LOG.debug("%s looking for ref: %s", ref.ref, source.get_handle())
                if ref.ref == source.get_handle():
                    found = 1
            if not found:
                sref = gen.lib.SourceRef()
                sref.set_reference_handle(source.get_handle())
                event.add_source_reference(sref)
        self.db.add_event(event,self.trans)
        return (1, event)
    
    def create_person(self):
        """ Used to create a new person we know doesn't exist """
        person = gen.lib.Person()
        self.db.add_person(person,self.trans)
        self.indi_count += 1
        return person

    def get_or_create_place(self,place_name):
        LOG.debug("get_or_create_place: looking for: %s", place_name)
        for place_handle in self.db.iter_place_handles():
            place = self.db.get_place_from_handle(place_handle)
            if place.get_title() == place_name:
                return (0, place)
        place = gen.lib.Place()
        place.set_title(place_name)
        self.db.add_place(place,self.trans)
        return (1, place)

    def get_or_create_source(self, source_text):
        source_list = self.db.get_source_handles()
        LOG.debug("get_or_create_source: list: %s", source_list)
        LOG.debug("get_or_create_source: looking for: %s", source_text)
        for source_handle in source_list:
            source = self.db.get_source_from_handle(source_handle)
            if source.get_title() == source_text:
                return (0, source)
        source = gen.lib.Source()
        source.set_title(source_text)
        self.db.add_source(source, self.trans)
        return (1, source)
