#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004  Donald N. Allingham
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
Class handling language-specific selection for date parser and displayer.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os
import locale

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import DateParser
import DateDisplay

#-------------------------------------------------------------------------
#
# Constants 
#
#-------------------------------------------------------------------------
_lang = locale.getlocale(locale.LC_TIME)[0]
if _lang:
    _lang_short = _lang.split('_')[0]
else:
    _lang_short = "C"

_lang_to_parser = {
    'C'      : DateParser.DateParser,
    'en'     : DateParser.DateParser,
    }

_lang_to_display = {
    'C'      : DateDisplay.DateDisplayEn,
    'en'     : DateDisplay.DateDisplayEn,
    'zh_CN'  : DateDisplay.DateDisplay,
    'zh_TW'  : DateDisplay.DateDisplay,
    'zh_SG'  : DateDisplay.DateDisplay,
    'zh_HK'  : DateDisplay.DateDisplay,
    'ja_JP'  : DateDisplay.DateDisplay,
    'ko_KR'  : DateDisplay.DateDisplay,
    }

def get_date_formats():
    """
    Returns the lists supported formats for date parsers and displayers
    """
    try:
        return _lang_to_display[_lang].formats
    except:
        return _lang_to_display["C"].formats

def set_format(value):
    try:
        displayer.set_format(value)
    except:
        pass

def register_datehandler(locales,parse_class,display_class):
    """
    Registers the passed date parser class and date displayer
    classes with the specfied language locales.

    @param locales: tuple of strings containing language codes.
        The character encoding is not included, so the langauge
        should be in the form of fr_FR, not fr_FR.utf8
    @type locales: tuple
    @param parse_class: Class to be associated with parsing
    @type parse_class: DateParse
    @param display_class: Class to be associated with displaying
    @type display_class: DateDisplay
    """
    for lang_str in locales:
        _lang_to_parser[lang_str] = parse_class
        _lang_to_display[lang_str] = display_class
    

#-------------------------------------------------------------------------
#
# Import localized date classes
#
#-------------------------------------------------------------------------
from PluginMgr import load_plugins
from const import datesDir
load_plugins(datesDir)

#-------------------------------------------------------------------------
#
# Initialize global parser
#
#-------------------------------------------------------------------------

try:
    if _lang_to_parser.has_key(_lang):
        parser = _lang_to_parser[_lang]()
    else:
        parser = _lang_to_parser[_lang_short]()
except:
    print "Date parser for",_lang,"not available, using default"
    parser = _lang_to_parser["C"]()

try:
    import GrampsKeys
    val = GrampsKeys.get_date_format(_lang_to_display[_lang].formats)
except:
    try:
        val = GrampsKeys.get_date_format(_lang_to_display["C"].formats)
    except:
        val = 0

try:
    if _lang_to_display.has_key(_lang):
        displayer = _lang_to_display[_lang](val)
    else:
        displayer = _lang_to_display[_lang_short](val)
except:
    print "Date displayer for",_lang,"not available, using default"
    displayer = _lang_to_display["C"](val)
    
