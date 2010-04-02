# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2005  Donald N. Allingham
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

"""
French-specific classes for parsing and displaying dates.
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
import Date
from DateParser import DateParser
from DateDisplay import DateDisplay

#-------------------------------------------------------------------------
#
# French parser
#
#-------------------------------------------------------------------------
class DateParserFR(DateParser):

    month_to_int = DateParser.month_to_int
    # Add common latin, local and historical variants (now only on east france)
    month_to_int[u"januaris"] = 1
    month_to_int[u"janer"] = 1
    month_to_int[u"jenner"] = 1
    month_to_int[u"hartmonat"] = 1
    month_to_int[u"hartung"] = 1
    month_to_int[u"eismond"] = 1
    month_to_int[u"bluviose"] = 1
    month_to_int[u"februaris"]  = 2
    month_to_int[u"hornung"]  = 2
    month_to_int[u"wintermonat"]  = 2
    month_to_int[u"taumond"]  = 2
    month_to_int[u"narrenmond"]  = 2
    month_to_int[u"vendose"]  = 2
    month_to_int[u"martius"]  = 3
    month_to_int[u"aprilis"]  = 4
    month_to_int[u"wiesenmonat"]  = 5
    month_to_int[u"maius"]  = 5
    month_to_int[u"junius"]  = 6
    month_to_int[u"julius"]  = 7
    month_to_int[u"augustus"]  = 8
    month_to_int[u"september"]  = 9
    month_to_int[u"7bre"]  = 9
    month_to_int[u"7bris"]  = 9
    month_to_int[u"october"]  = 10
    month_to_int[u"8bre"]  = 10
    month_to_int[u"8bris"]  = 10
    month_to_int[u"nebelmonat"]  = 10
    month_to_int[u"november"]  = 11
    month_to_int[u"9bre"]  = 11
    month_to_int[u"9bris"]  = 11
    month_to_int[u"december"]  = 12
    month_to_int[u"10bre"]  = 12
    month_to_int[u"10bris"]  = 12
    month_to_int[u"xbre"]  = 12
    month_to_int[u"xbris"]  = 12

    modifier_to_int = {
        u'avant'  : Date.MOD_BEFORE,
        u'av.'    : Date.MOD_BEFORE,
        u'av'     : Date.MOD_BEFORE,
        u'après'  : Date.MOD_AFTER,
        u'ap.'    : Date.MOD_AFTER,
        u'ap'     : Date.MOD_AFTER,
        u'env.'   : Date.MOD_ABOUT,
        u'env'    : Date.MOD_ABOUT,
        u'environ': Date.MOD_ABOUT,
        u'circa'  : Date.MOD_ABOUT,
        u'c.'     : Date.MOD_ABOUT,
        u'ca'     : Date.MOD_ABOUT,
        u'ca.'    : Date.MOD_ABOUT,
        u'vers'   : Date.MOD_ABOUT,
        u'~'      : Date.MOD_ABOUT,
        }

    calendar_to_int = {
        u'grégorien'             : Date.CAL_GREGORIAN,
        u'g'                     : Date.CAL_GREGORIAN,
        u'julien'                : Date.CAL_JULIAN,
        u'j'                     : Date.CAL_JULIAN,
        u'hébreu'                : Date.CAL_HEBREW,
        u'h'                     : Date.CAL_HEBREW,
        u'islamique'             : Date.CAL_ISLAMIC,
        u'i'                     : Date.CAL_ISLAMIC,
        u'révolutionnaire'       : Date.CAL_FRENCH,
        u'r'                     : Date.CAL_FRENCH,
        u'perse'                 : Date.CAL_PERSIAN,
        u'p'                     : Date.CAL_PERSIAN,
        }

    quality_to_int = {
        u'estimée'    : Date.QUAL_ESTIMATED,
        u'est.'       : Date.QUAL_ESTIMATED,
        u'est'        : Date.QUAL_ESTIMATED,
        u'calculée'   : Date.QUAL_CALCULATED,
        u'calc.'      : Date.QUAL_CALCULATED,
        u'calc'       : Date.QUAL_CALCULATED,
        u'comptée'    : Date.QUAL_CALCULATED,
        u'compt'      : Date.QUAL_CALCULATED,
        u'compt.'     : Date.QUAL_CALCULATED,
        }

    def init_strings(self):
        DateParser.init_strings(self)
        self._span     =  re.compile("(de)\s+(?P<start>.+)\s+(à)\s+(?P<stop>.+)",re.IGNORECASE)
        self._range    = re.compile("(entre|ent|ent.)\s+(?P<start>.+)\s+(et)\s+(?P<stop>.+)",re.IGNORECASE)
	self._text2 =re.compile('(\d+)?.?\s+?%s\s*((\d+)(/\d+)?)?' % self._mon_str,
				re.IGNORECASE)
	self._jtext2 =re.compile('(\d+)?.?\s+?%s\s*((\d+)(/\d+)?)?' % self._mon_str,
				re.IGNORECASE)

#-------------------------------------------------------------------------
#
# French display
#
#-------------------------------------------------------------------------
class DateDisplayFR(DateDisplay):

    calendar = (
        "", u" (Julien)", u" (Hébreu)",
        u" (Révolutionnaire)", u" (Perse)", u" (Islamique)"
        )

    _mod_str = ("",u"avant ",u"après ",u"vers ","","","")
    
    _qual_str = ("","estimée ","calculée ","")

    formats = (
        "AAAA-MM-DD (ISO)", "Numérique", "Mois Jour, Année",
        "MOI Jour, Année", "Jour Mois, Année", "Jour MOIS Année"
        )

    def _display_gregorian(self,date_val):
        year = self._slash_year(date_val[2],date_val[3])
        if self.format == 0:
            value = self.display_iso(date_val)
        elif self.format == 1:
            if date_val[0] == 0 and date_val[1] == 0:
                value = str(date_val[2])
            else:
                value = self._tformat.replace('%m',str(date_val[1]))
                value = value.replace('%d',str(date_val[0]))
                value = value.replace('%Y',str(date_val[2]))
        elif self.format == 2:
            # Month Day, Year
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = year
                else:
                    value = "%s %s" % (self._months[date_val[1]],year)
            else:
                value = "%s %d, %s" % (self._months[date_val[1]],date_val[0],year)
        elif self.format == 3:
            # MON Day, Year
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = year
                else:
                    value = "%s %s" % (self._MONS[date_val[1]],year)
            else:
                value = "%s %d, %s" % (self._MONS[date_val[1]],date_val[0],year)
        elif self.format == 4:
            # Day Month Year
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = year
                else:
                    value = "%s %s" % (self._months[date_val[1]],year)
            else:
                value = "%d. %s %s" % (date_val[0],self._months[date_val[1]],year)
        else:
            # Day MON Year
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = year
                else:
                    value = "%s %s" % (self._MONS[date_val[1]],year)
            else:
                value = "%d. %s %s" % (date_val[0],self._MONS[date_val[1]],year)
        return value

    def display(self,date):
        """
        Returns a text string representing the date.
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
            return "%s%s %s %s %s%s" % (qual_str,u'de',d1,u'à',d2,self.calendar[cal])
        elif mod == Date.MOD_RANGE:
            d1 = self.display_cal[cal](start)
            d2 = self.display_cal[cal](date.get_stop_date())
            return "%s%s %s %s %s%s" % (qual_str,u'entre',d1,u'et',d2,self.calendar[cal])
        else:
            text = self.display_cal[date.get_calendar()](start)
            return "%s%s%s%s" % (qual_str,self._mod_str[mod],text,self.calendar[cal])

#-------------------------------------------------------------------------
#
# Register classes
#
#-------------------------------------------------------------------------
from DateHandler import register_datehandler
register_datehandler(('fr_FR','fr','french','fr_CA','fr_BE','fr_CH'),DateParserFR,DateDisplayFR)
