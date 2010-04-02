#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
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

import const
from latin_utf8 import utf8_to_latin
u2l = utf8_to_latin

ADOPT_NONE         = 0
ADOPT_EVENT        = 1
ADOPT_FTW          = 2
ADOPT_LEGACY       = 3
ADOPT_PEDI         = 4
ADOPT_STD          = 5
CONC_OK            = 0
CONC_BROKEN        = 1
ALT_NAME_NONE      = 0
ALT_NAME_STD       = 1
ALT_NAME_ALIAS     = 2
ALT_NAME_AKA       = 3
ALT_NAME_EVENT_AKA = 4
ALT_NAME_UALIAS    = 5
CALENDAR_NO        = 0
CALENDAR_YES       = 1
OBJE_NO            = 0
OBJE_YES           = 1
RESIDENCE_ADDR     = 0
RESIDENCE_PLAC     = 1
SOURCE_REFS_NO     = 0
SOURCE_REFS_YES    = 1

#-------------------------------------------------------------------------
#
# XML parser
#
#-------------------------------------------------------------------------
import xml.parsers.expat

class GedcomDescription:
    def __init__(self,name):
        self.name = name
        self.dest = ""
        self.adopt = ADOPT_STD
        self.conc = CONC_OK
        self.altname = ALT_NAME_STD
        self.cal = CALENDAR_YES
        self.obje = OBJE_YES
        self.resi = RESIDENCE_ADDR
        self.source_refs = SOURCE_REFS_YES
        self.gramps2tag_map = {}
        self.tag2gramps_map = {}

    def set_dest(self,val):
        self.dest = val

    def get_dest(self):
        return self.dest

    def set_adopt(self,val):
        self.adopt = val

    def get_adopt(self):
        return self.adopt

    def set_conc(self,val):
        self.conc = val

    def get_conc(self):
        return self.conc

    def set_alt_name(self,val):
        self.altname = val

    def get_alt_name(self):
        return self.altname

    def set_alt_calendar(self,val):
        self.cal = val

    def get_alt_calendar(self):
        return self.cal

    def set_obje(self,val):
        self.obje = val

    def get_obje(self):
        return self.obje

    def set_resi(self,val):
        self.resi = val

    def get_resi(self):
        return self.resi

    def set_source_refs(self,val):
        self.source_refs = val

    def get_source_refs(self):
        return self.source_refs

    def add_tag_value(self,tag,value):
        self.gramps2tag_map[value] = tag
        self.tag2gramps_map[tag] = value

    def gramps2tag(self,key):
        if self.gramps2tag_map.has_key(key):
            return self.gramps2tag_map[key]
        return ""

    def tag2gramps(self,key):
        if self.tag2gramps_map.has_key(key):
            return self.tag2gramps_map[key]
        return key

class GedcomInfoDB:
    def __init__(self):
        self.map = {}

        self.standard = GedcomDescription("GEDCOM 5.5 standard")
        self.standard.set_dest("GEDCOM 5.5")
        
        try:
            file = "%s/gedcom.xml" % const.dataDir
            f = open(file,"r")
        except:
            return
        
        try:
            parser = GedInfoParser(self)
            parser.parse(f)
            f.close()
        except:
            pass

    def add_description(self,name,obj):
        self.map[name] = obj

    def get_description(self,name):
        if self.map.has_key(name):
            return self.map[name]
        return self.standard

    def get_from_source_tag(self,name):
        for k in self.map.keys():
            val = self.map[k]
            if val.get_dest() == name:
                return val
        return self.standard

    def get_name_list(self):
        mylist = self.map.keys()
        mylist.sort()
        return ["GEDCOM 5.5 standard"] + mylist
    
#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
class GedInfoParser:
    def __init__(self,parent):
        self.parent = parent
        self.current = None

    def parse(self,file):
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = self.startElement
        p.ParseFile(file)
        
    def startElement(self,tag,attrs):
        tag = u2l(tag)
        if tag == "target":
            name = u2l(attrs['name'])
            self.current = GedcomDescription(name)
            self.parent.add_description(name,self.current)
        elif tag == "dest":
            self.current.set_dest(u2l(attrs['val']))
        elif tag == "adopt":
            val = u2l(attrs['val'])
            if val == 'none':
                self.current.set_adopt(ADOPT_NONE)
            elif val == 'event':
                self.current.set_adopt(ADOPT_EVENT)
            elif val == 'ftw':
                self.current.set_adopt(ADOPT_FTW)
            elif val == 'legacy':
                self.current.set_adopt(ADOPT_LEGACY)
            elif val == 'pedigree':
                self.current.set_adopt(ADOPT_PEDI)
        elif tag == "conc":
            if u2l(attrs['val']) == 'broken':
                self.current.set_conc(CONC_BROKEN)
        elif tag == "alternate_names":
            val = u2l(attrs['val'])
            if val == 'none':
                self.current.set_alt_name(ALT_NAME_NONE)
            elif val == 'event_aka':
                self.current.set_alt_name(ALT_NAME_EVENT_AKA)
            elif val == 'alias':
                self.current.set_alt_name(ALT_NAME_ALIAS)
            elif val == 'aka':
                self.current.set_alt_name(ALT_NAME_AKA)
            elif val == '_alias':
                self.current.set_alt_name(ALT_NAME_UALIAS)
        elif tag == "calendars":
            if u2l(attrs['val']) == 'no':
                self.current.set_alt_calendar(CALENDAR_NO)
        elif tag == "event":
            self.current.add_tag_value(u2l(attrs['tag']),u2l(attrs['value']))
        elif tag == "object_support":
            if u2l(attrs['val']) == 'no':
                self.current.set_obje(OBJE_NO)
        elif tag == "residence":
            if u2l(attrs['val']) == 'place':
                self.current.set_resi(RESIDENCE_PLAC)
        elif tag == "source_refs":
            if u2l(attrs['val']) == 'no':
                self.current.set_source_refs(SOURCE_REFS_NO)
