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

# $Id$

"""
Spanish-specific classes for parsing and displaying dates.
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
from ..lib.date import Date
from _dateparser import DateParser
from _datedisplay import DateDisplay
from _datehandler import register_datehandler

#-------------------------------------------------------------------------
#
# Spanish parser
#
#-------------------------------------------------------------------------
class DateParserES(DateParser):

    modifier_to_int = {
        u'antes de'   : Date.MOD_BEFORE, 
        u'antes'      : Date.MOD_BEFORE, 
        u'ant.'       : Date.MOD_BEFORE, 
        u'ant'        : Date.MOD_BEFORE, 
        u'después de' : Date.MOD_AFTER, 
        u'después'    : Date.MOD_AFTER, 
        u'desp.'      : Date.MOD_AFTER, 
        u'desp'       : Date.MOD_AFTER, 
        u'aprox.'     : Date.MOD_ABOUT, 
        u'aprox'      : Date.MOD_ABOUT, 
        u'apr.'       : Date.MOD_ABOUT, 
        u'apr'        : Date.MOD_ABOUT, 
        u'circa'      : Date.MOD_ABOUT, 
        u'ca.'        : Date.MOD_ABOUT, 
        u'ca'         : Date.MOD_ABOUT, 
        u'c.'         : Date.MOD_ABOUT, 
        u'hacia'      : Date.MOD_ABOUT, 
        }

    calendar_to_int = {
        u'gregoriano'     : Date.CAL_GREGORIAN, 
        u'g'              : Date.CAL_GREGORIAN, 
        u'juliano'        : Date.CAL_JULIAN, 
        u'j'              : Date.CAL_JULIAN, 
        u'hebreo'         : Date.CAL_HEBREW, 
        u'h'              : Date.CAL_HEBREW, 
        u'islámico'       : Date.CAL_ISLAMIC, 
        u'i'              : Date.CAL_ISLAMIC, 
        u'revolucionario' : Date.CAL_FRENCH, 
        u'r'              : Date.CAL_FRENCH, 
        u'persa'          : Date.CAL_PERSIAN, 
        u'p'              : Date.CAL_PERSIAN, 
        u'swedish'        : Date.CAL_SWEDISH, 
        u's'              : Date.CAL_SWEDISH, 
        }

    quality_to_int = {
        u'estimado'   : Date.QUAL_ESTIMATED, 
        u'est.'       : Date.QUAL_ESTIMATED, 
        u'est'        : Date.QUAL_ESTIMATED, 
        u'calc.'      : Date.QUAL_CALCULATED, 
        u'calc'       : Date.QUAL_CALCULATED, 
        u'calculado'  : Date.QUAL_CALCULATED, 
        }

    def init_strings(self):
        DateParser.init_strings(self)
        _span_1 = [u'de']
        _span_2 = [u'a']
        _range_1 = [u'entre', u'ent\.', u'ent']
        _range_2 = [u'y']
        self._span  = re.compile("(%s)\s+(?P<start>.+)\s+(%s)\s+(?P<stop>.+)" % 
                                 ('|'.join(_span_1), '|'.join(_span_2)), 
                                 re.IGNORECASE)
        self._range = re.compile("(%s)\s+(?P<start>.+)\s+(%s)\s+(?P<stop>.+)" %
                                 ('|'.join(_range_1), '|'.join(_range_2)), 
                                 re.IGNORECASE)

#-------------------------------------------------------------------------
#
# Spanish display
#
#-------------------------------------------------------------------------
class DateDisplayES(DateDisplay):
    """
    Spanish language date display class. 
    """
    # TODO: Translate these month strings:
    long_months = ( u"", u"enero", u"febrero", u"marzo", u"abril", u"mayo", 
                    u"junio", u"julio", u"agosto", u"septiembre", u"octubre", 
                    u"noviembre", u"diciembre" )
    
    short_months = ( u"", u"enero", u"feb.", u"marzo", u"abr.", u"mayo", 
                     u"jun.", u"jul.", u"agosto", u"set.", u"oct.", u"nov.", 
                     u"dic" )

    calendar = (
        "", u"Juliano", u"Hebreo", 
        u"Revolucionario", u"Persa", u"Islámico", 
        u"Swedish" 
        )

    _mod_str = ("", u"antes de ", u"después de ", u"hacia ", "", "", "")

    _qual_str = ("", "estimado ", "calculado ")

    formats = (
        "AAAA-MM-DD (ISO)", "Numérica", "Mes Día, Año", 
        "MES Día, Año", "Día Mes, Año", "Día MES, Año"
        )
    
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
            return ""
        elif mod == Date.MOD_SPAN:
            d1 = self.display_cal[cal](start)
            d2 = self.display_cal[cal](date.get_stop_date())
            scal = self.format_extras(cal, newyear)
            return "%s%s %s %s %s%s" % (qual_str, u'de', d1, u'a', d2, scal)
        elif mod == Date.MOD_RANGE:
            d1 = self.display_cal[cal](start)
            d2 = self.display_cal[cal](date.get_stop_date())
            scal = self.format_extras(cal, newyear)
            return "%s%s %s %s %s%s" % (qual_str, u'entre', d1, u'y', d2, scal)
        else:
            text = self.display_cal[date.get_calendar()](start)
            scal = self.format_extras(cal, newyear)
            return "%s%s%s%s" % (qual_str, self._mod_str[mod], text, scal)

#-------------------------------------------------------------------------
#
# Register classes
#
#-------------------------------------------------------------------------
register_datehandler(('es_ES', 'es', 'spanish', 'Spanish'), DateParserES, DateDisplayES)
