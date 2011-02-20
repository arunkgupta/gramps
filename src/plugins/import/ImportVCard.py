#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Martin Hawlisch, Donald N. Allingham
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

"Import from vCard"

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
import re
import time
from gen.ggettext import gettext as _
from gen.ggettext import ngettext

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".ImportVCard")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import Errors
import gen.lib
from gen.db import DbTxn
from QuestionDialog import ErrorDialog

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def importData(database, filename, cb=None):

    try:
        g = VCardParser(database,filename)
    except IOError,msg:
        ErrorDialog(_("%s could not be opened\n") % filename,str(msg))
        return

    try:
        status = g.parse_vCard_file()
    except IOError,msg:
        errmsg = _("%s could not be opened\n") % filename
        ErrorDialog(errmsg,str(msg))
        return

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class VCardParser(object):
    def __init__(self, dbase, file):
        self.db = dbase
        self.f = open(file,"rU")
        self.filename = file

    def get_next_line(self):
        line = self.f.readline()
        if line:
            line = line.strip()
        else:
            line = None
        return line
        
    def parse_vCard_file(self):
        with DbTxn(_("vCard import"), self.db, batch=True) as self.trans:
            self.db.disable_signals()
            t = time.time()
            self.person = None

            line_reg = re.compile('^([^:]+)+:(.*)$')
            try:
                while 1:
                    line = self.get_next_line()
                    if line is None:
                        break
                    if line == "":
                        continue
                    
                    if line.find(":") == -1:
                        continue
                    line_parts = line_reg.match( line)
                    if not line_parts:
                        continue
                
                    fields = line_parts.group(1).split(";")
                    
                    #for field in line_parts.groups():
                    #    print " p "+field
                    #for field in fields:
                    #    print " f "+field
                        
                    if fields[0] == "BEGIN":
                        self.next_person()
                    elif fields[0] == "END":
                        self.finish_person()
                    elif fields[0] == "FN":
                        self.set_nick_name(fields, line_parts.group(2))
                    elif fields[0] == "N":
                        self.add_name(fields, line_parts.group(2))
                    elif fields[0] == "ADR":
                        self.add_address(fields, line_parts.group(2))
                    elif fields[0] == "TEL":
                        self.add_phone(fields, line_parts.group(2))
                    elif fields[0] == "BDAY":
                        self.add_birthday(fields, line_parts.group(2))
                    elif fields[0] == "TITLE":
                        self.add_title(fields, line_parts.group(2))
                    elif fields[0] == "URL":
                        self.add_url(fields, line_parts.group(2))
                    else:
                        LOG.warn("Token >%s< unknown. line skipped: %s" % (fields[0],line))
            except Errors.GedcomError, err:
                self.errmsg(str(err))
                
            t = time.time() - t
            msg = ngettext('Import Complete: %d second','Import Complete: %d seconds', t ) % t
    
        self.db.enable_signals()
        self.db.request_rebuild()
        
        return None

    def finish_person(self):
        if self.person is not None:
            self.db.add_person(self.person,self.trans)
        self.person = None

    def next_person(self):
        if self.person is not None:
            self.db.add_person(self.person,self.trans)
        self.person = gen.lib.Person()

    def set_nick_name(self, fields, data):
        if self.person is not None:
            attr = gen.lib.Attribute()
            attr.set_type(gen.lib.AttributeType.NICKNAME)
            attr.set_value(data)
            self.person.add_attribute(attr)

    def add_name(self, fields, data):
        data_fields = data.split(";")
        name = gen.lib.Name()
        name.set_type(gen.lib.NameType(gen.lib.NameType.AKA))
        name.set_surname(data_fields[0])
        name.set_first_name(data_fields[1])
        if data_fields[2]:
            name.set_first_name(data_fields[1]+" "+data_fields[2])
        name.set_surname_prefix(data_fields[3])
        name.set_suffix(data_fields[4])
        
        self.person.set_primary_name(name)

    def add_title(self, fields, data):
        name = gen.lib.Name()
        name.set_type(gen.lib.NameType(gen.lib.NameType.AKA))
        name.set_title(data)
        self.person.add_alternate_name(name)

    def add_address(self, fields, data):
        data_fields = data.split(";")
        addr = gen.lib.Address()
        addr.set_street(data_fields[0]+data_fields[1]+data_fields[2])
        addr.set_city(data_fields[3])
        addr.set_state(data_fields[4])
        addr.set_postal_code(data_fields[5])
        addr.set_country(data_fields[6])
        self.person.add_address(addr)

    def add_phone(self, fields, data):
        addr = gen.lib.Address()
        addr.set_phone(data)
        self.person.add_address(addr)

    def add_birthday(self, fields, data):
        event = gen.lib.Event()
        event.set_type(gen.lib.EventType(gen.lib.EventType.BIRTH))
        self.db.add_event(event,self.trans)
        
        event_ref = gen.lib.EventRef()
        event_ref.set_reference_handle(event.get_handle())
        self.person.set_birth_ref(event_ref)

    def add_url(self, fields, data):
        url = gen.lib.Url()
        url.set_path(data)
        self.person.add_url(url)
