#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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

"Import from GEDCOM"

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------

import re

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------

from GrampsDbUtils import (personalConstantEvents, personalConstantAttributes, 
                           familyConstantEvents)
import _GedcomTokens as GedcomTokens
import gen.lib
from DateHandler._DateParser import DateParser

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".GedcomImport")

#-------------------------------------------------------------------------
#
# constants #
#-------------------------------------------------------------------------

GED2GRAMPS = {}
for __val, __key in personalConstantEvents.iteritems():
    if __key != "":
        GED2GRAMPS[__key] = __val

for __val, __key in familyConstantEvents.iteritems():
    if __key != "":
        GED2GRAMPS[__key] = __val

GED2ATTR = {}
for __val, __key in personalConstantAttributes.iteritems():
    if __key != "":
        GED2ATTR[__key] = __val
    
#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------

MOD   = re.compile(r"\s*(INT|EST|CAL)\s+(.*)$")
CAL   = re.compile(r"\s*(ABT|BEF|AFT)?\s*@#D?([^@]+)@\s*(.*)$")
RANGE = re.compile(r"\s*BET\s+@#D?([^@]+)@\s*(.*)\s+AND\s+@#D?([^@]+)@\s*(.*)$")
SPAN  = re.compile(r"\s*FROM\s+@#D?([^@]+)@\s*(.*)\s+TO\s+@#D?([^@]+)@\s*(.*)$")

CALENDAR_MAP = {
    "FRENCH R" : gen.lib.Date.CAL_FRENCH,
    "JULIAN"   : gen.lib.Date.CAL_JULIAN,
    "HEBREW"   : gen.lib.Date.CAL_HEBREW,
}

QUALITY_MAP = {
    'CAL' : gen.lib.Date.QUAL_CALCULATED,
    'INT' : gen.lib.Date.QUAL_CALCULATED,
    'EST' : gen.lib.Date.QUAL_ESTIMATED,
}

SEX_MAP = {
    'F' : gen.lib.Person.FEMALE,
    'M' : gen.lib.Person.MALE,
}

#-----------------------------------------------------------------------
#
#
#
#-----------------------------------------------------------------------
class GedcomDateParser(DateParser):

    month_to_int = {
        'jan' : 1,  'feb' : 2,  'mar' : 3,  'apr' : 4,
        'may' : 5,  'jun' : 6,  'jul' : 7,  'aug' : 8,
        'sep' : 9,  'oct' : 10, 'nov' : 11, 'dec' : 12,
        }

#-----------------------------------------------------------------------
#
# GedLine - represents a tokenized version of a GEDCOM line
#
#-----------------------------------------------------------------------
class GedLine(object):
    """
    GedLine is a class the represents a GEDCOM line. The form of a  GEDCOM line 
    is:
    
    <LEVEL> <TOKEN> <TEXT>

    This gets parsed into

    Line Number, Level, Token Value, Token Text, and Data

    Data is dependent on the context the Token Value. For most of tokens, 
    this is just a text string. However, for certain tokens where we know 
    the context, we can provide some value. The current parsed tokens are:

    TOKEN_DATE   - gen.lib.Date
    TOKEN_SEX    - gen.lib.Person gender item
    TOEKN_UKNOWN - Check to see if this is a known event
    """

    def __init__(self, data):
        """
        If the level is 0, then this is a top level instance. In this case, 
        we may find items in the form of:

        <LEVEL> @ID@ <ITEM>

        If this is not the top level, we check the MAP_DATA array to see if 
        there is a conversion function for the data.
        """
        self.line = data[4]
        self.level = data[0]
        self.token = data[1]
        self.token_text = data[3].strip()
        self.data = data[2]

        if self.level == 0:
            if self.token_text and self.token_text[0] == '@' \
                    and self.token_text[-1] == '@':
                self.token = GedcomTokens.TOKEN_ID
                self.token_text = self.token_text[1:-1]
                self.data = self.data.strip()
        else:
            func = MAP_DATA.get(self.token)
            if func:
                func(self)

    def calc_sex(self):
        """
        Converts the data field to a gen.lib token indicating the gender
        """
        try:
            self.data = SEX_MAP.get(self.data.strip()[0], gen.lib.Person.UNKNOWN)
        except:
            self.data = gen.lib.Person.UNKNOWN

    def calc_date(self):
        """
        Converts the data field to a gen.lib.Date object
        """
        self.data = extract_date(self.data)

    def calc_unknown(self):
        """
        Checks to see if the token maps a known GEDCOM event. If so, we 
        change the type from UNKNOWN to TOKEN_GEVENT (gedcom event), and
        the data is assigned to the associated GRAMPS EventType
        """
        token = GED2GRAMPS.get(self.token_text)
        if token:
            event = gen.lib.Event()
            event.set_description(self.data)
            event.set_type(token)
            self.token = GedcomTokens.TOKEN_GEVENT
            self.data = event
        else:
            token = GED2ATTR.get(self.token_text)
            if token:
                attr = gen.lib.Attribute()
                attr.set_value(self.data)
                attr.set_type(token)
                self.token = GedcomTokens.TOKEN_ATTR
                self.data = attr

    def calc_note(self):
        gid = self.data.strip()
        if len(gid) > 2 and gid[0] == '@' and gid[-1] == '@':
            self.token = GedcomTokens.TOKEN_RNOTE
            self.data = gid[1:-1]

    def calc_nchi(self):
        attr = gen.lib.Attribute()
        attr.set_value(self.data)
        attr.set_type(gen.lib.AttributeType.NUM_CHILD)
        self.data = attr
        self.token = GedcomTokens.TOKEN_ATTR

    def calc_attr(self):
        attr = gen.lib.Attribute()
        attr.set_value(self.data)
        attr.set_type((gen.lib.AttributeType.CUSTOM, self.token_text))
        self.data = attr
        self.token = GedcomTokens.TOKEN_ATTR

    def __repr__(self):
        return "%d: %d (%d:%s) %s" % (self.line, self.level, self.token, 
                                      self.token_text, self.data)

#-------------------------------------------------------------------------
#
# MAP_DATA - kept as a separate table, so that it is static, and does not
#            have to be initialized every time in the GedLine constructor
#
#-------------------------------------------------------------------------
MAP_DATA = {
    GedcomTokens.TOKEN_UNKNOWN : GedLine.calc_unknown,
    GedcomTokens.TOKEN_DATE    : GedLine.calc_date,
    GedcomTokens.TOKEN_SEX     : GedLine.calc_sex,
    GedcomTokens.TOKEN_NOTE    : GedLine.calc_note,
    GedcomTokens.TOKEN_NCHI    : GedLine.calc_nchi,
    GedcomTokens.TOKEN__STAT   : GedLine.calc_attr,
    GedcomTokens.TOKEN__UID    : GedLine.calc_attr,
    GedcomTokens.TOKEN_AFN     : GedLine.calc_attr,
    }

#-------------------------------------------------------------------------
#
# extract_date
#
#-------------------------------------------------------------------------

DATE_CNV = GedcomDateParser()

def extract_date(text):
    """
    Converts the specified text to a gen.lib.Date object.
    """
    dateobj = gen.lib.Date()

    text = text.replace('BET ABT','EST BET') # Horrible hack for importing
                                             # illegal GEDCOM from
                                             # Apple Macintosh Classic
                                             # 'Gene' program

    try:
        # extract out the MOD line
        match = MOD.match(text)
        if match:
            (mod, text) = match.groups()
            qual = QUALITY_MAP.get(mod, gen.lib.Date.QUAL_NONE)
        else:
            qual = gen.lib.Date.QUAL_NONE

        # parse the range if we match, if so, return
        match = RANGE.match(text)
        if match:
            (cal1, data1, cal2, data2) = match.groups()

            cal = CALENDAR_MAP.get(cal1, gen.lib.Date.CAL_GREGORIAN)
                    
            start = DATE_CNV.parse(data1)
            stop =  DATE_CNV.parse(data2)
            dateobj.set(gen.lib.Date.QUAL_NONE, gen.lib.Date.MOD_RANGE, cal,
                        start.get_start_date() + stop.get_start_date())
            dateobj.set_quality(qual)
            return dateobj

        # parse a span if we match
        match = SPAN.match(text)
        if match:
            (cal1, data1, cal2, data2) = match.groups()

            cal = CALENDAR_MAP.get(cal1, gen.lib.Date.CAL_GREGORIAN)
                    
            start = DATE_CNV.parse(data1)
            stop =  DATE_CNV.parse(data2)
            dateobj.set(gen.lib.Date.QUAL_NONE, gen.lib.Date.MOD_SPAN, cal,
                        start.get_start_date() + stop.get_start_date())
            dateobj.set_quality(qual)
            return dateobj
        
        match = CAL.match(text)
        if match:
            (abt, cal, data) = match.groups()
            if abt:
                dateobj = DATE_CNV.parse("%s %s" % (abt, data))
            else:
                dateobj = DATE_CNV.parse(data)
            dateobj.set_calendar(CALENDAR_MAP.get(cal, 
                                                  gen.lib.Date.CAL_GREGORIAN))
            dateobj.set_quality(qual)
            return dateobj

        dateobj = DATE_CNV.parse(text)
        dateobj.set_quality(qual)
        return dateobj
    
    # FIXME: explain where/why an IOError might arise
    # and also: is such a long try-clause needed
    # having this fallback invites "what about other exceptions?"
    except IOError:
        # fallback strategy (evidently)
        return DATE_CNV.set_text(text)

#-------------------------------------------------------------------------
#
# Reader - serves as the lexical analysis engine
#
#-------------------------------------------------------------------------
class Reader(object):

    def __init__(self, ifile):
        self.ifile = ifile
        self.current_list = []
        self.eof = False
        self.cnv = None
        self.cnt = 0
        self.index = 0
        self.func_map = {
            GedcomTokens.TOKEN_CONT : self.__fix_token_cont,
            GedcomTokens.TOKEN_CONC : self.__fix_token_conc,
            }

    def readline(self):
        if len(self.current_list) <= 1 and not self.eof:
            self.__readahead()
        try:
            return GedLine(self.current_list.pop())
        except:
            return None

    def __fix_token_cont(self, data):
        line = self.current_list[0]
        new_value = line[2] + '\n' + data[2]
        self.current_list[0] = (line[0], line[1], new_value, line[3], line[4])

    def __fix_token_conc(self, data):
        line = self.current_list[0]
        if len(line[2]) == 4:
            # This deals with lines of the form
            # 0 @<XREF:NOTE>@ NOTE
            #   1 CONC <SUBMITTER TEXT>
            # The previous line contains only a tag and no data so concat a
            # space to separate the new line from the tag. This prevents the
            # first letter of the new line being lost later
            # in _GedcomParse.__parse_record
            new_value = line[2] + ' ' + data[2]
        else:
            new_value = line[2] + data[2]
        self.current_list[0] = (line[0], line[1], new_value, line[3], line[4])

    def __readahead(self):
        while len(self.current_list) < 5:
            line = self.ifile.readline()
            self.index += 1
            if not line:
                self.eof = True
                return

            try:
                # According to the GEDCOM 5.5 standard,
                # Chapter 1 subsection Grammar
                #"leading whitespace preceeding a GEDCOM line should be ignored"
                # We will also strip the terminator which is any combination
                # of carriage_return and line_feed
                line = line.lstrip(' ').rstrip('\n\r')
                # split into level+delim+rest
                line = line.partition(' ')
                level = int(line[0])
                # there should only be one space after the level,
                # but we can ignore more,
                # then split into tag+delim+line_value
                # or xfef_id+delim+rest
                line = line[2].lstrip(' ').partition(' ')
                tag = line[0]
                line_value = line[2]
            except:
                continue

            token = GedcomTokens.TOKENS.get(tag, GedcomTokens.TOKEN_UNKNOWN)
            data = (level, token, line_value, tag, self.index)

            func = self.func_map.get(data[1])
            if func:
                func(data)
            else:
                self.current_list.insert(0, data)

