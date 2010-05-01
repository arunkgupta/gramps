#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004  Martin Hawlisch
# Copyright (C) 2005-2008  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
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

"Export Persons to vCard."

#-------------------------------------------------------------------------
#
# Standard Python Modules
#
#-------------------------------------------------------------------------
import sys
import os
from gen.ggettext import gettext as _

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
log = logging.getLogger(".ExportVCard")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from Filters import GenericFilter, Rules, build_filter_model
from gen.lib import Date
import Errors
from glade import Glade

#-------------------------------------------------------------------------
#
# CardWriterOptionBox class
#
#-------------------------------------------------------------------------
class CardWriterOptionBox(object):
    """
    Create a VBox with the option widgets and define methods to retrieve
    the options.
     
    """
    def __init__(self, person):
        self.person = person

    def get_option_box(self):

        self.topDialog = Glade()

        self.filters = self.topDialog.get_object("filter")
        self.copy = 0

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

            the_filters += [des, ans, com]

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
        self.cfilter = self.filter_menu[self.filters.get_active()][1]

class CardWriter(object):
    def __init__(self, database, msg_callback, cl=0, filename="", option_box=None,
                 callback=None):
        self.db = database
        self.option_box = option_box
        self.cl = cl
        self.filename = filename
        self.callback = callback
        self.msg_callback = msg_callback
        if callable(self.callback): # callback is really callable
            self.update = self.update_real
        else:
            self.update = self.update_empty

        self.plist = {}
        
        if not option_box:
            self.cl_setup()
        else:
            self.option_box.parse_options()

            if self.option_box.cfilter is None:
                for p in self.db.iter_person_handles():
                    self.plist[p] = 1
            else:
                try:
                    for p in self.option_box.cfilter.apply(self.db, 
                               self.db.iter_person_handles()):
                        self.plist[p] = 1
                except Errors.FilterError, msg:
                    (m1, m2) = msg.messages()
                    self.msg_callback(m1, m2)
                    return

    def update_empty(self):
        pass

    def update_real(self):
        self.count += 1
        newval = int(100*self.count/self.total)
        if newval != self.oldval:
            self.callback(newval)
            self.oldval = newval

    def cl_setup(self):
        self.plist.update([p, 1] for p in self.db.iter_person_handles())

    def writeln(self, text):
        #self.g.write('%s\n' % (text.encode('iso-8859-1')))
        self.g.write('%s\n' % (text.encode(sys.getfilesystemencoding())))

    def export_data(self, filename):

        self.dirname = os.path.dirname (filename)
        try:
            self.g = open(filename,"w")
        except IOError,msg:
            msg2 = _("Could not create %s") % filename
            self.msg_callback(msg2, str(msg))
            return False
        except:
            self.msg_callback(_("Could not create %s") % filename)
            return False

        self.count = 0
        self.oldval = 0
        self.total = len(self.plist)
        for key in self.plist:
            self.write_person(key)
            self.update()

        self.g.close()
        return True   
                    
    def write_person(self, person_handle):
        person = self.db.get_person_from_handle(person_handle)
        if person:
            self.writeln("BEGIN:VCARD");
            prname = person.get_primary_name()
            
            self.writeln("FN:%s" % prname.get_regular_name())
            self.writeln("N:%s;%s;%s;%s;%s" % 
                    (prname.get_surname(), 
                    prname.get_first_name(), 
                    person.get_nick_name(), 
                    prname.get_surname_prefix(), 
                    prname.get_suffix()
                    )
                )
            if prname.get_title():
                self.writeln("TITLE:%s" % prname.get_title())
                
            birth_ref = person.get_birth_ref()
            if birth_ref:
                birth = self.db.get_event_from_handle(birth_ref.ref)
                if birth:
                    b_date = birth.get_date_object()
                    mod = b_date.get_modifier()
                    if (mod != Date.MOD_TEXTONLY and 
                        not b_date.is_empty() and 
                        not mod == Date.MOD_SPAN and 
                        not mod == Date.MOD_RANGE):
                        (day, month, year, sl) = b_date.get_start_date()
                        if day > 0 and month > 0 and year > 0:
                            self.writeln("BDAY:%s-%02d-%02d" % (year, month, 
                                                                day))

            address_list = person.get_address_list()
            for address in address_list:
                postbox = ""
                ext = ""
                street = address.get_street()
                city = address.get_city()
                state = address.get_state()
                zip = address.get_postal_code()
                country = address.get_country()
                if street or city or state or zip or country:
                    self.writeln("ADR:%s;%s;%s;%s;%s;%s;%s" % 
                        (postbox, ext, street, city,state, zip, country))
                
                phone = address.get_phone()
                if phone:
                    self.writeln("TEL:%s" % phone)
                
            url_list = person.get_url_list()
            for url in url_list:
                href = url.get_path()
                if href:
                    self.writeln("URL:%s" % href)

        self.writeln("END:VCARD");
        self.writeln("");

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def exportData(database, filename, option_box=None, callback=None):
    cw = CardWriter(database, 0, filename, option_box, callback)
    return cw.export_data(filename)
