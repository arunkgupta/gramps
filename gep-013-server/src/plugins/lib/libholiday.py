# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2008-2009  Brian G. Matherly
# Copyright (C) 2009       Rob G. Healey <robhealey1@gmail.com>
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
# $id: $
#
#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
from gettext import gettext as _
from xml.parsers import expat
import datetime
import math
import const
import os

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gen.plug import PluginManager, Plugin

#------------------------------------------------------------------------
#
# Support functions
#
#------------------------------------------------------------------------
def g2iso(dow):
    """ Converst GRAMPS day of week to ISO day of week """
    # GRAMPS: SUN = 1
    # ISO: MON = 1
    return (dow + 5) % 7 + 1

#------------------------------------------------------------------------
#
# HolidayTable
#
#------------------------------------------------------------------------
class HolidayTable(object):
    """ 
    HolidayTable is a class which provides holidays for various 
    countries and years.
    """
    __holiday_files = []
    __countries = []

    def __init__(self):
        """ 
        Find the holiday files and load the countries if it has not already 
        been done.
        """ 
        if( not HolidayTable.__holiday_files ):
            self.__find_holiday_files()
            
        if( not HolidayTable.__countries ):
            self.__build_country_list()

        # Initialize the holiday table to be empty
        self.__holidays = {}
        self.__init_table()             
     
    def __find_holiday_files(self):
        """ Looks in multiple places for holidays.xml files 
        It will search for the file in user;s plugin directories first,
        then it will search in program's plugins directories. """

        holiday_file = 'holidays.xml'
        
        # Look for holiday files in the user plugins directory and all
        # subdirectories.
        for (dirpath, dirnames, filenames) in os.walk(const.USER_PLUGINS):
            holiday_full_path = os.path.join(dirpath, holiday_file)
            if os.path.exists(holiday_full_path):
                HolidayTable.__holiday_files.append(holiday_full_path)

        # Look for holiday files in the installation plugins directory and all
        # subdirectories.
        for (dirpath, dirnames, filenames) in os.walk(const.PLUGINS_DIR):
            holiday_full_path = os.path.join(dirpath, holiday_file)
            if os.path.exists(holiday_full_path):
                HolidayTable.__holiday_files.append(holiday_full_path)
            
    def __build_country_list(self):
        """ Generate the list of countries that have holiday information. """
        for holiday_file_path in HolidayTable.__holiday_files:
            parser = _Xml2Obj()
            root_element = parser.parse(holiday_file_path)
            for country_element in root_element.get_children():
                if country_element.get_name() == "country":
                    country_name = country_element.get_attribute("name")
                    if country_name not in HolidayTable.__countries:
                        HolidayTable.__countries.append(country_name)
                        
    def __init_table(self):
        """ Initialize the holiday table structure. """
        for month in range(1, 13):
            self.__holidays[month] = {}
            for day in range(1, 32):
                self.__holidays[month][day] = []   

    def get_countries(self):
        """ 
        Get all the country names that holidays are available for.
        
        @return: nothing
        """
        return HolidayTable.__countries

    def load_holidays(self, year, country):
        """ 
        Load the holiday table for the specified year and country. 
        This must be called before get_holidays().
        
        @param year: The year for which the holidays should be loaded.
            Example: 2010
        @type year: int
        @param country: The country for which the holidays should be loaded.
            Example: "United States"
        @type country: str
        @return: nothing
        """
        self.__init_table()
        for holiday_file_path in HolidayTable.__holiday_files:
            parser = _Xml2Obj()
            element = parser.parse(holiday_file_path) 
            calendar = _Holidays(element, country)
            date = datetime.date(year, 1, 1)
            while date.year == year:
                holidays = calendar.check_date(date)
                for text in holidays:
                    self.__holidays[date.month][date.day].append(text)
                date = date.fromordinal(date.toordinal() + 1)
    
    def get_holidays(self, month, day):
        """ 
        Get the holidays for the given day of the year.
        
        @param month: The month for the requested holidays.
            Example: 1
        @type month: int
        @param month: The day for the requested holidays.
            Example: 1
        @type month: int
        @return: An array of strings with holiday names.
        @return type: [str]
        """
        return self.__holidays[month][day]

#------------------------------------------------------------------------
#
# _Element
#
#------------------------------------------------------------------------
class _Element:
    """ A parsed XML element """
    def __init__(self, name, attributes):
        'Element constructor'
        # The element's tag name
        self.__name = name
        # The element's attribute dictionary
        self.__attributes = attributes
        # The element's child element list (sequence)
        self.__children = []
        
    def add_child(self, element):
        'Add a reference to a child element'
        self.__children.append(element)
        
    def get_attribute(self, key):
        'Get an attribute value'
        return self.__attributes.get(key)
    
    def get_attributes(self):
        'Get all the attributes'
        return self.__attributes
    
    def get_name(self):
        """ Get the name of this element. """
        return self.__name
    
    def get_children(self):
        """ Get the children elements for this element. """
        return self.__children

#------------------------------------------------------------------------
#
# _Xml2Obj
#
#------------------------------------------------------------------------
class _Xml2Obj:
    """ XML to Object """
    def __init__(self):
        self.root = None
        self.nodeStack = []
        
    def start_element(self, name, attributes):
        'SAX start element even handler'
        # Instantiate an Element object
        element = _Element(name.encode(), attributes)
        # Push element onto the stack and make it a child of parent
        if len(self.nodeStack) > 0:
            parent = self.nodeStack[-1]
            parent.add_child(element)
        else:
            self.root = element
        self.nodeStack.append(element)
        
    def end_element(self, name):
        'SAX end element event handler'
        self.nodeStack = self.nodeStack[:-1]

    def parse(self, filename):
        'Create a SAX parser and parse filename '
        parser = expat.ParserCreate()
        # SAX event handlers
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        # Parse the XML File
        parser.Parse(open(filename, 'r').read(), 1)
        return self.root

#------------------------------------------------------------------------
#
# _Holidays
#
#------------------------------------------------------------------------
class _Holidays:
    """ Class used to read XML holidays to add to calendar. """
    def __init__(self, elements, country="US"):
        self.debug = 0
        self.elements = elements
        self.country = country
        self.dates = []
        self.initialize()
        
    def set_country(self, country):
        """ Set the contry of holidays to read """
        self.country = country
        self.dates = []
        self.initialize()
                
    def initialize(self):
        """ Parse the holiday date XML items """
        for country_set in self.elements.get_children():
            if country_set.get_name() == "country" and \
               country_set.get_attribute("name") == self.country:
                for date in country_set.get_children():
                    if date.get_name() == "date":
                        data = {"value" : "", 
                                "name" : "", 
                                "offset": "", 
                                "type": "", 
                                } # defaults
                        for attr in date.get_attributes():
                            data[attr] = date.get_attribute(attr)
                        self.dates.append(data)
                        
    def get_daynames(self, year, month, dayname):
        """ Get the items for a particular year/month and day of week """
        if self.debug: 
            print "%s's in %d %d..." % (dayname, month, year)
             
        retval = [0]
        dow = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'].index(dayname)
        for day in range(1, 32):
            try:
                date = datetime.date(year, month, day)
            except ValueError:
                continue
            if date.weekday() == dow:
                retval.append(day)
                
        if self.debug: 
            print "dow=", dow, "days=", retval
            
        return retval
    
    def check_date(self, date):
        """ Return items that match rules """
        retval = []
        for rule in self.dates:
            
            if self.debug: 
                print "Checking ", rule["name"], "..."
                
            offset = 0
            if rule["offset"] != "":
                if rule["offset"].isdigit():
                    offset = int(rule["offset"])
                elif rule["offset"][0] in ["-", "+"] and \
                     rule["offset"][1:].isdigit():
                    offset = int(rule["offset"])
                else:
                    # must be a dayname
                    offset = rule["offset"]
                
            if self.debug: 
                print "rule['value']:", rule["value"]
                
            if rule["value"].count("/") == 3: # year/num/day/month, "3rd wednesday in april"
                y, num, dayname, mon = rule["value"].split("/")
                if y == "*":
                    y = date.year
                else:
                    y = int(y)
                if mon.isdigit():
                    m = int(mon)
                elif mon == "*":
                    m = date.month
                else:
                    m = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                         'jul', 'aug', 'sep', 'oct', 'nov', 'dec'].index(mon) + 1
                dates_of_dayname = self.get_daynames(y, m, dayname)
                
                if self.debug: 
                    print "num =", num
                    
                d = dates_of_dayname[int(num)]
                
            elif rule["value"].count("/") == 2: # year/month/day
                y, m, d = rule["value"].split("/")
                if y == "*":
                    y = date.year
                else:
                    y = int(y)
                if m == "*":
                    m = date.month
                else:
                    m = int(m)
                if d == "*":
                    d = date.day
                else:
                    d = int(d)
            ndate = datetime.date(y, m, d)
            
            if self.debug: 
                print ndate, offset, type(offset)
                
            if isinstance(offset, int):
                if offset != 0:
                    ndate = ndate.fromordinal(ndate.toordinal() + offset)
            elif isinstance(offset, basestring):
                direction = 1
                if offset[0] == "-":
                    direction = -1
                    offset = offset[1:]
                if offset in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
                    # next tuesday you come to, including this one
                    dow = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'].index(offset)
                    ordinal = ndate.toordinal()
                    while ndate.fromordinal(ordinal).weekday() != dow:
                        ordinal += direction
                    ndate = ndate.fromordinal(ordinal)
            
            if self.debug: 
                print "ndate:", ndate, "date:", date
                
            if ndate == date:
                retval.append(rule["name"])
        return retval

#------------------------------------------------------------------------
#
# Register the plugins
#
#------------------------------------------------------------------------
PluginManager.get_instance().register_plugin( 
Plugin(
    name = __name__, 
    description = _("Provides holiday information for different countries."),
    module_name = __name__ 
      )
)
