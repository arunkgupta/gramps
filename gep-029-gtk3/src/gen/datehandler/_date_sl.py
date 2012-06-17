# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2007  Donald N. Allingham
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
#

# Slovenian version 2010 by Bernard Banko, based on croatian one by Josip

"""
Slovenian-specific classes for parsing and displaying dates.
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
from _dateparser import DateParser
from _datedisplay import DateDisplay
from _datehandler import register_datehandler

#-------------------------------------------------------------------------
#
# Slovenian parser
#
#-------------------------------------------------------------------------
class DateParserSL(DateParser):
    """
    Converts a text string into a Date object
    """
    month_to_int = DateParser.month_to_int
    
    month_to_int[u"januar"] = 1
    month_to_int[u"januarja"] = 1
    month_to_int[u"januarjem"] = 1
    month_to_int[u"jan"] = 1
    month_to_int[u"i"] = 1
    
    month_to_int[u"februar"] = 2
    month_to_int[u"februarjem"] = 2
    month_to_int[u"februarja"] = 2
    month_to_int[u"feb"] = 2
    month_to_int[u"ii"]  = 2
    
    month_to_int[u"mar"] = 3
    month_to_int[u"marcem"] = 3
    month_to_int[u"marec"] = 3
    month_to_int[u"marca"] = 3
    month_to_int[u"iii"]  = 3
    
    month_to_int[u"apr"] = 4
    month_to_int[u"april"] = 4
    month_to_int[u"aprilom"] = 4
    month_to_int[u"aprila"] = 4
    month_to_int[u"iv"]  = 4

    month_to_int[u"maj"] = 5
    month_to_int[u"maja"] = 5
    month_to_int[u"majem"] = 5
    month_to_int[u"v"]  = 5
    
    month_to_int[u"jun"] = 6
    month_to_int[u"junij"] = 6
    month_to_int[u"junijem"] = 6
    month_to_int[u"junija"] = 6
    month_to_int[u"vi"]  = 6

    month_to_int[u"jul"]  = 7
    month_to_int[u"julij"]  = 7
    month_to_int[u"julijem"]  = 7
    month_to_int[u"julija"]  = 7
    month_to_int[u"vii"]  = 7
    
    month_to_int[u"avg"]  = 8
    month_to_int[u"avgust"]  = 8
    month_to_int[u"avgustom"]  = 8
    month_to_int[u"avgusta"]  = 8
    month_to_int[u"viii"]  = 8
    
    month_to_int[u"sep"]  = 9
    month_to_int[u"sept"]  = 9
    month_to_int[u"september"]  = 9
    month_to_int[u"septembrom"]  = 9
    month_to_int[u"septembra"]  = 9
    month_to_int[u"ix"]  = 9
    
    month_to_int[u"okt"]  = 10
    month_to_int[u"oktober"]  = 10
    month_to_int[u"oktobrom"]  = 10
    month_to_int[u"oktobra"]  = 10
    month_to_int[u"x"]  = 10
    
    month_to_int[u"nov"]  = 11
    month_to_int[u"november"]  = 11
    month_to_int[u"novembrom"]  = 11
    month_to_int[u"novembra"]  = 11
    month_to_int[u"xi"]  = 11
    
    month_to_int[u"dec"]  = 12
    month_to_int[u"december"]  = 12
    month_to_int[u"decembrom"]  = 12
    month_to_int[u"decembra"]  = 12
    month_to_int[u"xii"]  = 12
    
    modifier_to_int = {
        u'pred'   : Date.MOD_BEFORE, 
        u'pr.'    : Date.MOD_BEFORE,
        u'po'     : Date.MOD_AFTER,
        u'okoli'  : Date.MOD_ABOUT,
        u'okrog'  : Date.MOD_ABOUT,
        u'okr.'   : Date.MOD_ABOUT,
        u'ok.'    : Date.MOD_ABOUT,
        u'cca.'   : Date.MOD_ABOUT,
        u'cca'    : Date.MOD_ABOUT,                      
        u'circa'  : Date.MOD_ABOUT, 
        u'ca.'    : Date.MOD_ABOUT, 
        }

    calendar_to_int = {
        u'gregorijanski'  : Date.CAL_GREGORIAN,
        u'greg.'          : Date.CAL_GREGORIAN,
        u'julijanski'     : Date.CAL_JULIAN,
        u'jul.'           : Date.CAL_JULIAN,
        u'hebrejski'      : Date.CAL_HEBREW,
        u'hebr.'          : Date.CAL_HEBREW,
        u'islamski'       : Date.CAL_ISLAMIC,
        u'isl.'           : Date.CAL_ISLAMIC,
        u'francoski republikanski': Date.CAL_FRENCH,
        u'franc.'         : Date.CAL_FRENCH,
        u'perzijski'      : Date.CAL_PERSIAN,
        u'perz. '         : Date.CAL_PERSIAN,
        u'švedski'        : Date.CAL_SWEDISH, 
        u'šved.'          : Date.CAL_SWEDISH, 
        }

    quality_to_int = {
        u'približno'   : Date.QUAL_ESTIMATED,
        u'pribl.'      : Date.QUAL_ESTIMATED,
        u'izračunano'  : Date.QUAL_CALCULATED,
        u'izrač.'        : Date.QUAL_CALCULATED,
        }

    bce = ["pred našim štetjem", "pred Kristusom",
           "p.n.š.", "p. n. š.", "pr.Kr.", "pr. Kr."] + DateParser.bce

    def init_strings(self):
        """
        compiles regular expression strings for matching dates
        """
        DateParser.init_strings(self)
        # match 'Day. MONTH year.' format with or without dots
        self._text2 = re.compile('(\d+)?\.?\s*?%s\.?\s*((\d+)(/\d+)?)?\s*\.?$'
                                % self._mon_str, re.IGNORECASE)
        # match Day.Month.Year.
        self._numeric  = re.compile("((\d+)[/\.-])?\s*((\d+)[/\.-])?\s*(\d+)\.?$")
       
        self._span  = re.compile("od\s+(?P<start>.+)\s+do\s+(?P<stop>.+)", 
                                re.IGNORECASE)
        self._range = re.compile(
                            u"med\s+(?P<start>.+)\s+in\s+(?P<stop>.+)", 
                            re.IGNORECASE)
        self._jtext2 = re.compile('(\d+)?.?\s+?%s\s*((\d+)(/\d+)?)?'\
                                % self._jmon_str, re.IGNORECASE)

#-------------------------------------------------------------------------
#
# Slovenian display
#
#-------------------------------------------------------------------------
class DateDisplaySL(DateDisplay):
    """
    Slovenian language date display class. 
    """
    long_months = ( u"", u"januarja", u"februarja", u"marca",u"aprila",
        u"maja", u"junija", u"julija", u"avgusta", u"septembra",
        u"oktobra", u"novembra", u"decembra" 
        )
   
    short_months = ( u"", u"jan", u"feb", u"mar", u"apr", u"maj", u"jun",
        u"jul", u"avg", u"sep", u"okt", u"nov", u"dec"
        )
    
    calendar = (
        "", u"julijanski", u"hebrejski", 
        u"francoski republikanski", u"perzijski", u"islamski",
        u"švedski" 
        )

    _mod_str = ("", "pred ", "po ", "okrog ", "", "", "")

    _qual_str = ("", "približno ", "izračunano ")
    
    _bce_str = "%s p.n.š."

    formats = (
        "ISO (leto-mm-dd)", 
        "številčno", 
        "dan. mes. leto",
        "dan. mesec leto"
        )
         
    def _display_gregorian(self, date_val):
        """
        display gregorian calendar date in different format
        """
        year = self._slash_year(date_val[2], date_val[3])
        if self.format == 0:
            return self.display_iso(date_val)
        elif self.format == 1:
            # D. M. YYYY
            if date_val[3]:
                return self.display_iso(date_val)
            else:
                if date_val[0] == 0 and date_val[1] == 0:
                    value = str(date_val[2])
                else:
                    value = self._tformat.replace('%m', str(date_val[1]))
                    value = value.replace('%d', str(date_val[0]))
                    value = value.replace('%Y', str(date_val[2]))
                    value = value.replace('-', '. ')
        elif self.format == 2:
            # D. mon. YYYY
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = year
                else:
                    value = "%s. %s" % (self.short_months[date_val[1]], year)
            else:
                value = "%d. %s. %s" % (date_val[0],
                                        self.short_months[date_val[1]], year)
        else:
            # D. month YYYY
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = "%s." % year
                else:
                   value = "%s %s" % (self.long_months[date_val[1]], year)
            else:
                value = "%d. %s %s" % (
                  date_val[0],self.long_months[date_val[1]], year)
        if date_val[2] < 0:
            return self._bce_str % value
        else:
            return value

    def display(self, date):
        """
        Return a text string representing the date.
        """
        mod = date.get_modifier()
        cal = date.get_calendar()
        qual = date.get_quality()
        start = date.get_start_date()
        newyear = date.get_new_year()

        qual_str = self._qual_str[qual]
        
        if mod == Date.MOD_TEXTONLY:
            return date.get_text()
        elif start == Date.EMPTY:
            return u""
        elif mod == Date.MOD_SPAN:
            d_1 = self.display_cal[cal](start)
            d_2 = self.display_cal[cal](date.get_stop_date())
            scal = self.format_extras(cal, newyear)
            return u"%sod %s do %s%s" % (qual_str, d_1, d_2, scal)
        elif mod == Date.MOD_RANGE:
            d_1 = self.display_cal[cal](start)
            d_2 = self.display_cal[cal](date.get_stop_date())
            scal = self.format_extras(cal, newyear)
            date_string = u"%smed %s in %s%s" % (qual_str, d_1, d_2, scal)
            date_string = date_string.replace(u"a ",u"em ") #to correct declination
            date_string = date_string.replace(u"lem ",u"lom ")
            date_string = date_string.replace(u"rem ",u"rom ")
            date_string = date_string.replace(u"tem ",u"tom ")
            return date_string
        else:
            text = self.display_cal[date.get_calendar()](start)
            scal = self.format_extras(cal, newyear)
            date_string = "%s%s%s%s" % (qual_str, self._mod_str[mod], text, scal)
        return date_string

#-------------------------------------------------------------------------
#
# Register classes
#
#-------------------------------------------------------------------------
register_datehandler(("sl", "SL", "sl_SI", "slovenščina", "slovenian", "Slovenian", 
                 "sl_SI.UTF8", "sl_SI.UTF-8", "sl_SI.utf-8", "sl_SI.utf8"),
                                    DateParserSL, DateDisplaySL)
