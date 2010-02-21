#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007-2008 Douglas S. Blank
# Copyright (C) 2004-2007 Donald N. Allingham
# Copyright (C) 2008      Brian G. Matherly
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

"Export to CSV Spreadsheet."

#-------------------------------------------------------------------------
#
# Standard Python Modules
#
#-------------------------------------------------------------------------
import os
from gen.ggettext import sgettext as _
import csv
import cStringIO
import codecs

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".ExportCSV")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import gen.lib
from Filters import GenericFilter, Rules, build_filter_model
import Utils
from QuestionDialog import ErrorDialog
import gen.proxy
import DateHandler
from glade import Glade

#-------------------------------------------------------------------------
#
# The function that does the exporting
#
#-------------------------------------------------------------------------
def exportData(database, filename, option_box=None, callback=None):
    gw = CSVWriter(database, filename, option_box, callback)
    return gw.export_data()

#-------------------------------------------------------------------------
#
# Support Functions
#
#-------------------------------------------------------------------------
def sortable_string_representation(text):
    numeric = ""
    alpha   = ""
    for s in text:
        if s.isdigit():
            numeric += s
        else:
            alpha += s
    return alpha + (("0" * 10) + numeric)[-10:]

#-------------------------------------------------------------------------
#
# Encoding support for CSV, from http://docs.python.org/lib/csv-examples.html
#
#-------------------------------------------------------------------------
class UTF8Recoder(object):
    """Iterator that reads an encoded stream and reencodes the input to UTF-8."""
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f", which is 
    encoded in the given encoding.
    
    """

    def __init__(self, f, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter(object):
    """
    A CSV writer which will write rows to CSV file "f", which is encoded in 
    the given encoding.
    
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
# CSVWriter Options
#
#-------------------------------------------------------------------------
class CSVWriterOptionBox(object):
    """
    Create a VBox with the option widgets and define methods to retrieve
    the options. 
    
    """
    def __init__(self,person):
        self.person = person
        self.include_individuals = 1
        self.include_marriages = 1
        self.include_children = 1
        self.translate_headers = 1

    def get_option_box(self):
        self.topDialog = Glade()
        self.filters = self.topDialog.get_object("filter")

        all = GenericFilter()
        all.set_name(_("Entire Database"))
        all.add_rule(Rules.Person.Everyone([]))

        the_filters = [all]

        if self.person:
            des = GenericFilter()
            des.set_name(_("Descendants of %s") %
                         self.person.get_primary_name().get_name())
            des.add_rule(Rules.Person.IsDescendantOf(
                [self.person.get_gramps_id(),1]))

            ans = GenericFilter()
            ans.set_name(_("Ancestors of %s") %
                         self.person.get_primary_name().get_name())
            ans.add_rule(Rules.Person.IsAncestorOf(
                [self.person.get_gramps_id(),1]))

            com = GenericFilter()
            com.set_name(_("People with common ancestor with %s") %
                         self.person.get_primary_name().get_name())
            com.add_rule(Rules.Person.HasCommonAncestorWith(
                [self.person.get_gramps_id()]))

            the_filters += [des,ans,com]

        from Filters import CustomFilters
        the_filters.extend(CustomFilters.get_filters('Person'))
        self.filter_menu = build_filter_model(the_filters)
        self.filters.set_model(self.filter_menu)
        self.filters.set_active(0)

        the_box = self.topDialog.get_object('vbox1')
        the_parent = self.topDialog.get_object('dialog-vbox1')
        the_parent.remove(the_box)
        self.topDialog.toplevel.destroy()
        return the_box

    def parse_options(self):
        self.include_individuals = self.topDialog.get_object("individuals").get_active()
        self.include_marriages = self.topDialog.get_object("marriages").get_active()
        self.include_children = self.topDialog.get_object("children").get_active()
        self.translate_headers = self.topDialog.get_object("translate_headers").get_active()
        self.cfilter = self.filter_menu[self.filters.get_active()][1]

#-------------------------------------------------------------------------
#
# CSVWriter class
#
#-------------------------------------------------------------------------
class CSVWriter(object):
    def __init__(self, database, filename, option_box=None, callback=None):
        self.db = database
        self.option_box = option_box
        self.filename = filename
        self.callback = callback
        if callable(self.callback): # callback is really callable
            self.update = self.update_real
        else:
            self.update = self.update_empty

        self.plist = {}
        self.flist = {}
        
        self.persons_details_done = []
        self.persons_notes_done = []
        self.person_ids = {}
        
        if not option_box:
            self.include_individuals = 1
            self.include_marriages = 1
            self.include_children = 1
            self.translate_headers = 1
        else:
            self.option_box.parse_options()

            self.include_individuals = self.option_box.include_individuals
            self.include_marriages = self.option_box.include_marriages
            self.include_children = self.option_box.include_children
            self.translate_headers = self.option_box.translate_headers
            
            if not option_box.cfilter.is_empty():
                self.db = gen.proxy.FilterProxyDb(self.db, option_box.cfilter)

        self.plist.update([p, 1] for p in self.db.iter_person_handles())

        # get the families for which these people are spouses:
        self.flist = {}
        for key in self.plist:
            p = self.db.get_person_from_handle(key)
            for family_handle in p.get_family_handle_list():
                self.flist[family_handle] = 1
        # now add the families for which these people are a child:
        family_handles = self.db.iter_family_handles()
        for family_handle in family_handles:
            family = self.db.get_family_from_handle(family_handle)
            for child_ref in family.get_child_ref_list():
                child_handle = child_ref.ref
                if child_handle in self.plist:
                    self.flist[family_handle] = 1
                        
    def update_empty(self):
        pass

    def update_real(self):
        self.count += 1
        newval = int(100*self.count/self.total)
        if newval != self.oldval:
            self.callback(newval)
            self.oldval = newval

    def writeln(self):
        self.g.writerow([])

    def write_csv(self, *items):
        self.g.writerow(items)

    def export_data(self):
        self.dirname = os.path.dirname (self.filename)
        try:
            self.g = open(self.filename,"w")
            self.fp = open(self.filename, "wb")
            self.g = UnicodeWriter(self.fp)
        except IOError,msg:
            msg2 = _("Could not create %s") % self.filename
            ErrorDialog(msg2,str(msg))
            return False
        except:
            ErrorDialog(_("Could not create %s") % self.filename)
            return False
        ######################### initialize progress bar
        self.count = 0
        self.total = 0
        self.oldval = 0
        if self.include_individuals:
            self.total += len(self.plist)
        if self.include_marriages:
            self.total += len(self.flist)
        if self.include_children:
            self.total += len(self.flist)
        ######################## 
        LOG.debug("Possible people to export: %s", len(self.plist))
        LOG.debug("Possible families to export: %s", len(self.flist))
        ########################### sort:
        sortorder = []
        for key in self.plist:
            person = self.db.get_person_from_handle(key)
            if person:
                primary_name = person.get_primary_name()
                first_name = primary_name.get_first_name()
                surname = primary_name.get_surname()
                sortorder.append( (surname, first_name, key) )
        sortorder.sort() # will sort on tuples
        plist = [data[2] for data in sortorder]
        ###########################
        if self.include_individuals:
            if self.translate_headers:
                self.write_csv(_("Person"), _("Surname"), _("Given"), 
                               _("Call"), _("Suffix"), _("Prefix"), 
                               _("Person|Title"), _("Gender"), _("Birth date"), 
                               _("Birth place"), _("Birth source"),
                               _("Death date"), _("Death place"), 
                               _("Death source"), _("Note"))
            else:
                self.write_csv("Person", "Surname", "Given", 
                               "Call", "Suffix", "Prefix", 
                               "Title", "Gender", "Birth date", 
                               "Birth place", "Birth source",
                               "Death date", "Death place", 
                               "Death source", "Note")
            for key in plist:
                person = self.db.get_person_from_handle(key)
                if person:
                    primary_name = person.get_primary_name()
                    first_name = primary_name.get_first_name()
                    surname = primary_name.get_surname()
                    prefix = primary_name.get_surname_prefix()
                    suffix = primary_name.get_suffix()
                    title = primary_name.get_title()
                    grampsid = person.get_gramps_id()
                    grampsid_ref = ""
                    if grampsid != "":
                        grampsid_ref = "[" + grampsid + "]"
                    note = '' # don't export notes or source
                    callname = primary_name.get_call_name()
                    gender = person.get_gender()
                    if gender == gen.lib.Person.MALE:
                        gender = Utils.gender[gen.lib.Person.MALE]
                    elif gender == gen.lib.Person.FEMALE:
                        gender = Utils.gender[gen.lib.Person.FEMALE]
                    else:
                        gender = Utils.gender[gen.lib.Person.UNKNOWN]
                    # Birth:
                    birthdate = ""
                    birthplace = ""
                    birth_ref = person.get_birth_ref()
                    if birth_ref:
                        birth = self.db.get_event_from_handle(birth_ref.ref)
                        if birth:
                            birthdate = self.format_date( birth)
                            place_handle = birth.get_place_handle()
                            if place_handle:
                                place = self.db.get_place_from_handle(place_handle)
                                birthplace = place.get_title()
                    # Death:
                    deathdate = ""
                    deathplace = ""
                    death_ref = person.get_death_ref()
                    if death_ref:
                        death = self.db.get_event_from_handle(death_ref.ref)
                        if death:
                            deathdate = self.format_date( death)
                            place_handle = death.get_place_handle()
                            if place_handle:
                                place = self.db.get_place_from_handle(place_handle)
                                deathplace = place.get_title()
                    self.write_csv(grampsid_ref, surname, first_name, callname,
                                   suffix, prefix, title, gender,
                                   birthdate, birthplace, "",
                                   deathdate, deathplace, "",
                                   note)
                self.update()
            self.writeln()
        ########################### sort:
        sortorder = []
        for key in self.flist:
            family = self.db.get_family_from_handle(key)
            if family:
                marriage_id = family.get_gramps_id()
                sortorder.append(
                    (sortable_string_representation(marriage_id), key)
                    )
        sortorder.sort() # will sort on tuples
        flist = [data[1] for data in sortorder]
        ########################### 
        if self.include_marriages:
            if self.translate_headers:
                self.write_csv(_("Marriage"), _("Husband"), _("Wife"), 
                               _("Date"), _("Place"), _("Source"), _("Note"))
            else:
                self.write_csv("Marriage", "Husband", "Wife", 
                               "Date", "Place", "Source", "Note")
            for key in flist:
                family = self.db.get_family_from_handle(key)
                if family:
                    marriage_id = family.get_gramps_id()
                    if marriage_id != "":
                        marriage_id = "[" + marriage_id + "]"
                    mother_id = ''
                    father_id = ''
                    father_handle = family.get_father_handle()
                    if father_handle:
                        father = self.db.get_person_from_handle(father_handle)
                        father_id = father.get_gramps_id()
                        if father_id != "":
                            father_id = "[" + father_id + "]"
                    mother_handle = family.get_mother_handle()
                    if mother_handle:
                        mother = self.db.get_person_from_handle(mother_handle)
                        mother_id = mother.get_gramps_id()
                        if mother_id != "":
                            mother_id = "[" + mother_id + "]"
                    # get mdate, mplace
                    mdate, mplace = '', ''
                    event_ref_list = family.get_event_ref_list()
                    for event_ref in event_ref_list:
                        event = self.db.get_event_from_handle(event_ref.ref)
                        if event.get_type() == gen.lib.EventType.MARRIAGE:
                            mdate = self.format_date( event)
                            place_handle = event.get_place_handle()
                            if place_handle:
                                place = self.db.get_place_from_handle(place_handle)
                                mplace = place.get_title()
                                # m_source = self.get_primary_source( event.get_source_references())
                    source, note = '', ''
                    self.write_csv(marriage_id, father_id, mother_id, mdate,
                                   mplace, source, note)
                self.update()
            self.writeln()
        if self.include_children:
            if self.translate_headers:
                self.write_csv(_("Family"), _("Child"))
            else:
                self.write_csv("Family", "Child")
            for key in flist:
                family = self.db.get_family_from_handle(key)
                if family:
                    family_id = family.get_gramps_id()
                    if family_id != "":
                        family_id = "[" + family_id + "]"
                    for child_ref in family.get_child_ref_list():
                        child_handle = child_ref.ref
                        child = self.db.get_person_from_handle(child_handle)
                        grampsid = child.get_gramps_id()
                        grampsid_ref = ""
                        if grampsid != "":
                            grampsid_ref = "[" + grampsid + "]"
                        self.write_csv(family_id, grampsid_ref)
                self.update()
            self.writeln()
        self.g.close()
        return True 
    
    def format_date(self, date):
        return DateHandler.get_date(date)
