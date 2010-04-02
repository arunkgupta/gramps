# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2006  Donald N. Allingham
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

"""
Czech-specific classes for parsing and displaying dates.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import re

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib import Date
from _DateParser import DateParser
from _DateDisplay import DateDisplay
from _DateHandler import register_datehandler

#-------------------------------------------------------------------------
#
# Czech parser
#
#-------------------------------------------------------------------------
class DateParserCZ(DateParser):

    modifier_to_int = {
        u'před'   : Date.MOD_BEFORE, 
        u'do'     : Date.MOD_BEFORE, 
        u'po'     : Date.MOD_AFTER, 
        u'asi'    : Date.MOD_ABOUT, 
        u'kolem'  : Date.MOD_ABOUT, 
        u'přibl.' : Date.MOD_ABOUT, 
        }

    calendar_to_int = {
        u'gregoriánský'  : Date.CAL_GREGORIAN, 
        u'g'             : Date.CAL_GREGORIAN, 
        u'juliánský'     : Date.CAL_JULIAN, 
        u'j'             : Date.CAL_JULIAN, 
        u'hebrejský'     : Date.CAL_HEBREW, 
        u'h'             : Date.CAL_HEBREW, 
        u'islámský'      : Date.CAL_ISLAMIC, 
        u'i'             : Date.CAL_ISLAMIC, 
        u'republikánský' : Date.CAL_FRENCH, 
        u'r'             : Date.CAL_FRENCH, 
        u'perský'       : Date.CAL_PERSIAN, 
        u'p'             : Date.CAL_PERSIAN, 
        u'švédský'       : Date.CAL_SWEDISH, 
        u's'             : Date.CAL_SWEDISH, 
        }

    quality_to_int = {
        u'odhadovaný' : Date.QUAL_ESTIMATED, 
        u'odh.'       : Date.QUAL_ESTIMATED, 
        u'vypočtený' : Date.QUAL_CALCULATED, 
        u'vyp.'       : Date.QUAL_CALCULATED, 
        }

    def init_strings(self):
        DateParser.init_strings(self)
        _span_1 = [u'od']
        _span_2 = [u'do']
        _range_1 = [u'mezi']
        _range_2 = [u'a']
        self._span  = re.compile("(%s)\s+(?P<start>.+)\s+(%s)\s+(?P<stop>.+)" % 
                                 ('|'.join(_span_1), '|'.join(_span_2)), 
                                 re.IGNORECASE)
        self._range = re.compile("(%s)\s+(?P<start>.+)\s+(%s)\s+(?P<stop>.+)" %
                                 ('|'.join(_range_1), '|'.join(_range_2)), 
                                 re.IGNORECASE)

#-------------------------------------------------------------------------
#
# Czech display
#
#-------------------------------------------------------------------------
class DateDisplayCZ(DateDisplay):

    calendar = (
        "", u" (juliánský)", u" (hebrejský)", 
        u" (republikánský)", u" (perský)", u" (islámský)", 
        u" (švédský)" 
        )

    _mod_str = ("", u"před ", u"po ", u"kolem ", "", "", "")
    
    _qual_str = ("", "odh. ", "vyp. ")

    formats = (
        "RRRR-MM-DD (ISO)", "numerický", "Měsíc Den, Rok", 
        "MĚS Den, Rok", "Den, Měsíc, Rok", "Den MĚS Rok"
        )

    def display(self, date):
        """
        Return a text string representing the date.
        """
        mod = date.get_modifier()
        cal = date.get_calendar()
        qual = date.get_quality()
        start = date.get_start_date()

        qual_str = self._qual_str[qual]
        
        if mod == Date.MOD_TEXTONLY:
            return date.get_text()
        elif start == Date.EMPTY:
            return ""
        elif mod == Date.MOD_SPAN:
            d1 = self.display_cal[cal](start)
            d2 = self.display_cal[cal](date.get_stop_date())
            return "%s%s %s %s %s%s" % (qual_str, u'od', d1, 
                                        u'do', d2, self.calendar[cal])
        elif mod == Date.MOD_RANGE:
            d1 = self.display_cal[cal](start)
            d2 = self.display_cal[cal](date.get_stop_date())
            return "%s%s %s %s %s%s" % (qual_str, u'mezi', 
                                        d1, u'a', d2, self.calendar[cal])
        else:
            text = self.display_cal[date.get_calendar()](start)
            return "%s%s%s%s" % (qual_str, self._mod_str[mod],
                                 text, self.calendar[cal])

#-------------------------------------------------------------------------
#
# Register classes
#
#-------------------------------------------------------------------------
register_datehandler(('cs_CZ', 'cs', 'CZ', 'Czech'), DateParserCZ, DateDisplayCZ)
