# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
from gettext import gettext as _
from xml.parsers import expat
import datetime
import math
import time
import const
import os

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
import BaseDoc
from BasicUtils import name_displayer
from PluginUtils import register_report, relationship_class
from ReportBase import (Report, ReportUtils, MenuReportOptions, 
                        CATEGORY_DRAW, CATEGORY_TEXT, 
                        MODE_GUI, MODE_BKI, MODE_CLI)
from PluginUtils import (NumberOption, BooleanOption, StringOption, 
                         FilterOption, EnumeratedListOption, PersonOption)
import GrampsLocale
import gen.lib
from Utils import probably_alive, ProgressMeter
from FontScale import string_trim
pt2cm = ReportUtils.pt2cm
cm2pt = ReportUtils.cm2pt

#------------------------------------------------------------------------
#
# Support functions
#
#------------------------------------------------------------------------
def easter(year):
    """
    Computes the year/month/day of easter. Based on work by
    J.-M. Oudin (1940) and is reprinted in the "Explanatory Supplement
    to the Astronomical Almanac", ed. P. K.  Seidelmann (1992).  Note:
    Ash Wednesday is 46 days before Easter Sunday.
    """
    c = year / 100
    n = year - 19 * (year / 19)
    k = (c - 17) / 25
    i = c - c / 4 - (c - k) / 3 + 19 * n + 15
    i = i - 30 * (i / 30)
    i = i - (i / 28) * (1 - (i / 28) * (29 / (i + 1))
                           * ((21 - n) / 11))
    j = year + year / 4 + i + 2 - c + c / 4
    j = j - 7 * (j / 7)
    l = i - j
    month = 3 + (l + 40) / 44
    day = l + 28 - 31 * (month / 4)
    return "%d/%d/%d" % (year, month, day)

def g2iso(dow):
    """ Converst GRAMPS day of week to ISO day of week """
    # GRAMPS: SUN = 1
    # ISO: MON = 1
    return (dow + 5) % 7 + 1

def dst(year, area="us"):
    """
    Return Daylight Saving Time start/stop in a given area ("us", "eu").
    US calculation valid 1976-2099; EU 1996-2099
    """
    if area == "us":
        if year > 2006:
            start = "%d/%d/%d" % (year, 3, 14 - (math.floor(1 + year * 5 / 4) % 7)) # March
            stop = "%d/%d/%d" % (year, 11, 7 - (math.floor(1 + year * 5 / 4) % 7)) # November
        else:
            start = "%d/%d/%d" % (year, 4, (2 + 6 * year - math.floor(year / 4)) % 7 + 1) # April
            stop =  "%d/%d/%d" % (year, 10, (31 - (math.floor(year * 5 / 4) + 1) % 7)) # October
    elif area == "eu":
        start = "%d/%d/%d" % (year, 3, (31 - (math.floor(year * 5 / 4) + 4) % 7)) # March
        stop =  "%d/%d/%d" % (year, 10, (31 - (math.floor(year * 5 / 4) + 1) % 7)) # Oct
    return (start, stop)

def make_date(year, month, day):
    """
    Return a Date object of the particular year/month/day.
    """
    retval = gen.lib.Date()
    retval.set_yr_mon_day(year, month, day)
    return retval

#------------------------------------------------------------------------
#
# Calendar
#
#------------------------------------------------------------------------
class Calendar(Report):
    """
    Create the Calendar object that produces the report.
    """
    def __init__(self, database, options_class):
        Report.__init__(self, database, options_class)
        menu = options_class.menu
        if 'titletext' in menu.get_all_option_names():
            # report and graphic share most of the same code
            # but calendar doesn't have a title
            self.titletext = menu.get_option_by_name('titletext').get_value()
        if 'relationships' in menu.get_all_option_names():
            # report and graphic share most of the same code
            # but calendar doesn't show relationships
            self.relationships = \
                        menu.get_option_by_name('relationships').get_value()
        else:
            self.relationships = False
        self.year = menu.get_option_by_name('year').get_value()
        self.name_format = menu.get_option_by_name('name_format').get_value()
        self.country = menu.get_option_by_name('country').get_value()
        self.anniversaries = menu.get_option_by_name('anniversaries').get_value()
        self.start_dow = menu.get_option_by_name('start_dow').get_value()
        self.maiden_name = menu.get_option_by_name('maiden_name').get_value()
        self.alive = menu.get_option_by_name('alive').get_value()
        self.birthdays = menu.get_option_by_name('birthdays').get_value()
        self.text1 = menu.get_option_by_name('text1').get_value()
        self.text2 = menu.get_option_by_name('text2').get_value()
        self.text3 = menu.get_option_by_name('text3').get_value()
        self.filter_option =  menu.get_option_by_name('filter')
        self.filter = self.filter_option.get_filter()
        pid = menu.get_option_by_name('pid').get_value()
        self.center_person = database.get_person_from_gramps_id(pid)

        self.title = _("Calendar Report") #% name

    def get_name(self, person, maiden_name = None):
        """ Return person's name, unless maiden_name given, unless married_name listed. """
        # Get all of a person's names:
        primary_name = person.get_primary_name()
        married_name = None
        names = [primary_name] + person.get_alternate_names()
        for n in names:
            if int(n.get_type()) == gen.lib.NameType.MARRIED:
                married_name = n
                break # use first
        # Now, decide which to use:
        if maiden_name != None:
            if married_name != None:
                name = gen.lib.Name(married_name)
            else:
                name = gen.lib.Name(primary_name)
                name.set_surname(maiden_name)
        else:
            name = gen.lib.Name(primary_name)
        name.set_display_as(self.name_format)
        return name_displayer.display_name(name)
        
    def draw_rectangle(self, style, sx, sy, ex, ey):
        """ This should be in BaseDoc """
        self.doc.draw_line(style, sx, sy, sx, ey)
        self.doc.draw_line(style, sx, sy, ex, sy)
        self.doc.draw_line(style, ex, sy, ex, ey)
        self.doc.draw_line(style, sx, ey, ex, ey)

### The rest of these all have to deal with calendar specific things

    def add_day_item(self, text, year, month, day):
        """ Add an item to a day. """
        month_dict = self.calendar.get(month, {})
        day_list = month_dict.get(day, [])
        day_list.append(text)
        month_dict[day] = day_list
        self.calendar[month] = month_dict

    def get_holidays(self, year, country = "United States"):
        """ Looks in multiple places for holidays.xml files """
        locations = [const.PLUGINS_DIR, const.USER_PLUGINS]
        holiday_file = 'holidays.xml'
        for dir in locations:
            holiday_full_path = os.path.join(dir, holiday_file)
            if os.path.exists(holiday_full_path):
                self.process_holiday_file(holiday_full_path, year, country)

    def process_holiday_file(self, filename, year, country):
        """ This will process a holiday file """
        parser = Xml2Obj()
        element = parser.Parse(filename) 
        calendar = Holidays(element, country)
        date = datetime.date(year, 1, 1)
        while date.year == year:
            holidays = calendar.check_date(date)
            for text in holidays:
                self.add_day_item(text, date.year, date.month, date.day)
            date = date.fromordinal(date.toordinal() + 1)

    def write_report(self):
        """ The short method that runs through each month and creates a page. """
        # initialize the dict to fill:
        self.progress = ProgressMeter(_('Calendar'))
        self.calendar = {}
        # get the information, first from holidays:
        if self.country != 0: # Don't include holidays
            self.get_holidays(self.year, _countries[self.country]) # _countries is currently global
        # get data from database:
        self.collect_data()
        # generate the report:
        self.progress.set_pass(_('Formatting months...'), 12)
        for month in range(1, 13):
            self.progress.step()
            self.print_page(month)
        self.progress.close()

    def print_page(self, month):
        """
        This method actually writes the calendar page.
        """
        style_sheet = self.doc.get_style_sheet()
        ptitle = style_sheet.get_paragraph_style("CAL-Title")
        ptext = style_sheet.get_paragraph_style("CAL-Text")
        pdaynames = style_sheet.get_paragraph_style("CAL-Daynames")
        pnumbers = style_sheet.get_paragraph_style("CAL-Numbers")
        ptext1style = style_sheet.get_paragraph_style("CAL-Text1style")

        self.doc.start_page()
        width = self.doc.get_usable_width()
        height = self.doc.get_usable_height()
        header = 2.54 # one inch
        self.draw_rectangle("CAL-Border", 0, 0, width, height)
        self.doc.draw_box("CAL-Title", "", 0, 0, width, header)
        self.doc.draw_line("CAL-Border", 0, header, width, header)
        year = self.year
        title = "%s %d" % (GrampsLocale.long_months[month].capitalize(), year)
        font_height = pt2cm(ptitle.get_font().get_size())
        self.doc.center_text("CAL-Title", title, width/2, font_height * 0.25)
        cell_width = width / 7
        cell_height = (height - header)/ 6
        current_date = datetime.date(year, month, 1)
        spacing = pt2cm(1.25 * ptext.get_font().get_size()) # 158
        if current_date.isoweekday() != g2iso(self.start_dow + 1):
            # Go back to previous first day of week, and start from there
            current_ord = (current_date.toordinal() -
                           ((current_date.isoweekday() + 7) -
                            g2iso(self.start_dow + 1)) % 7)
        else:
            current_ord = current_date.toordinal()
        for day_col in range(7):
            font_height = pt2cm(pdaynames.get_font().get_size())
            self.doc.center_text("CAL-Daynames", 
                                 GrampsLocale.long_days[(day_col+
                                                         g2iso(self.start_dow + 1))
                                                        % 7 + 1].capitalize(), 
                                 day_col * cell_width + cell_width/2, 
                                 header - font_height * 1.5)
        for week_row in range(6):
            something_this_week = 0
            for day_col in range(7):
                thisday = current_date.fromordinal(current_ord)
                if thisday.month == month:
                    something_this_week = 1
                    self.draw_rectangle("CAL-Border", day_col * cell_width, 
                                        header + week_row * cell_height, 
                                        (day_col + 1) * cell_width, 
                                        header + (week_row + 1) * cell_height)
                    last_edge = (day_col + 1) * cell_width
                    self.doc.center_text("CAL-Numbers", str(thisday.day), 
                                         day_col * cell_width + cell_width/2, 
                                         header + week_row * cell_height)
                    list = self.calendar.get(month, {}).get(thisday.day, [])
                    position = 0.0 
                    for p in list:
                        lines = p.count("\n") + 1 # lines in the text
                        position += (lines  * spacing)
                        current = 0
                        for line in p.split("\n"):
                            # make sure text will fit:
                            numpos = pt2cm(pnumbers.get_font().get_size())
                            if position + (current * spacing) - 0.1 >= cell_height - numpos: # font daynums
                                continue
                            font = ptext.get_font()
                            line = string_trim(font, line, cm2pt(cell_width + 0.2))
                            self.doc.draw_text("CAL-Text", line, 
                                              day_col * cell_width + 0.1, 
                                              header + (week_row + 1) * cell_height - position + (current * spacing) - 0.1)
                            current += 1
                current_ord += 1
        if not something_this_week:
            last_edge = 0
        font_height = pt2cm(1.5 * ptext1style.get_font().get_size())
        self.doc.center_text("CAL-Text1style", self.text1, last_edge + (width - last_edge)/2, height - font_height * 3) 
        self.doc.center_text("CAL-Text2style", self.text2, last_edge + (width - last_edge)/2, height - font_height * 2) 
        self.doc.center_text("CAL-Text3style", self.text3, last_edge + (width - last_edge)/2, height - font_height * 1) 
        self.doc.end_page()

    def collect_data(self):
        """
        This method runs through the data, and collects the relevant dates
        and text.
        """
        self.progress.set_pass(_('Filtering data...'), 0)
        people = self.filter.apply(self.database, 
                                   self.database.get_person_handles(sort_handles=False))
        rel_calc = relationship_class()
        self.progress.set_pass(_('Filtering data...'), len(people))
        for person_handle in people:
            self.progress.step()
            person = self.database.get_person_from_handle(person_handle)
            birth_ref = person.get_birth_ref()
            birth_date = None
            if birth_ref:
                birth_event = self.database.get_event_from_handle(birth_ref.ref)
                birth_date = birth_event.get_date_object()
            if self.birthdays and birth_date != None:
                year = birth_date.get_year()
                month = birth_date.get_month()
                day = birth_date.get_day()
                age = self.year - year
                # add some things to handle maiden name:
                father_lastname = None # husband, actually
                if self.maiden_name in ['spouse_first', 'spouse_last']: # get husband's last name:
                    if person.get_gender() == gen.lib.Person.FEMALE:
                        family_list = person.get_family_handle_list()
                        if len(family_list) > 0:
                            if self.maiden_name == 'spouse_first':
                                fhandle = family_list[0]
                            else:
                                fhandle = family_list[-1]
                            fam = self.database.get_family_from_handle(fhandle)
                            father_handle = fam.get_father_handle()
                            mother_handle = fam.get_mother_handle()
                            if mother_handle == person_handle:
                                if father_handle:
                                    father = self.database.get_person_from_handle(father_handle)
                                    if father != None:
                                        father_lastname = father.get_primary_name().get_surname()
                short_name = self.get_name(person, father_lastname)
                if age >= 0:
                    alive = probably_alive(person, self.database, make_date(self.year, month, day))
                    if ((self.alive and alive) or not self.alive):
                        comment = ""
                        if self.relationships:
                            relation = rel_calc.get_one_relationship(
                                                             self.database, 
                                                             self.center_person, 
                                                             person)
                            if relation:
                                comment = " --- %s" % relation
                        self.add_day_item("%s, %d%s" % (short_name, age, comment), self.year, month, day)
            if self.anniversaries:
                family_list = person.get_family_handle_list()
                for fhandle in family_list: 
                    fam = self.database.get_family_from_handle(fhandle)
                    father_handle = fam.get_father_handle()
                    mother_handle = fam.get_mother_handle()
                    if father_handle == person.get_handle():
                        spouse_handle = mother_handle
                    else:
                        continue # with next person if the father is not "person"
                                 # this will keep from duplicating the anniversary
                    if spouse_handle:
                        spouse = self.database.get_person_from_handle(spouse_handle)
                        if spouse:
                            spouse_name = self.get_name(spouse)
                            short_name = self.get_name(person)
                            # TEMP: this will hanlde ordered events
                            # GRAMPS 3.0 will have a new mechanism for start/stop events
                            are_married = None
                            for event_ref in fam.get_event_ref_list():
                                event = self.database.get_event_from_handle(event_ref.ref)
                                if int(event.get_type()) in [gen.lib.EventType.MARRIAGE, 
                                                             gen.lib.EventType.MARR_ALT]:
                                    are_married = event
                                elif int(event.get_type()) in [gen.lib.EventType.DIVORCE, 
                                                               gen.lib.EventType.ANNULMENT, 
                                                               gen.lib.EventType.DIV_FILING]:
                                    are_married = None
                            if are_married != None:
                                for event_ref in fam.get_event_ref_list():
                                    event = self.database.get_event_from_handle(event_ref.ref)
                                    event_obj = event.get_date_object()
                                    year = event_obj.get_year()
                                    month = event_obj.get_month()
                                    day = event_obj.get_day()
                                    years = self.year - year
                                    if years >= 0:
                                        text = _("%(spouse)s and\n %(person)s, %(nyears)d") % {
                                            'spouse' : spouse_name, 
                                            'person' : short_name, 
                                            'nyears' : years, 
                                            }
                                        alive1 = probably_alive(person, self.database, make_date(self.year, month, day))
                                        alive2 = probably_alive(spouse, self.database, make_date(self.year, month, day))
                                        if ((self.alive and alive1 and alive2) or not self.alive):
                                            self.add_day_item(text, self.year, month, day)
                                            
class CalendarReport(Calendar):
    """ The Calendar text report """
    def write_report(self):
        """ The short method that runs through each month and creates a page. """
        # initialize the dict to fill:
        self.progress = ProgressMeter(_('Birthday and Anniversary Report'))
        self.calendar = {}
        # get the information, first from holidays:
        if self.country != 0:
            self.get_holidays(self.year, _countries[self.country]) # _countries currently global
        # get data from database:
        self.collect_data()
        # generate the report:
        self.doc.start_paragraph('BIR-Title') 
        self.doc.write_text(str(self.titletext) + ": " + str(self.year))
        self.doc.end_paragraph()
        if self.text1.strip() != "":
            self.doc.start_paragraph('BIR-Text1style')
            self.doc.write_text(str(self.text1))
            self.doc.end_paragraph()
        if self.text2.strip() != "":
            self.doc.start_paragraph('BIR-Text2style')
            self.doc.write_text(str(self.text2))
            self.doc.end_paragraph()
        if self.text3.strip() != "":
            self.doc.start_paragraph('BIR-Text3style')
            self.doc.write_text(str(self.text3))
            self.doc.end_paragraph()
        if self.relationships:
            name = self.center_person.get_primary_name()
            self.doc.start_paragraph('BIR-Text3style')
            self.doc.write_text(_("Relationships shown are to %s") % name_displayer.display_name(name))
            self.doc.end_paragraph()
        self.progress.set_pass(_('Formatting months...'), 12)
        for month in range(1, 13):
            self.progress.step()
            self.print_page(month)
        self.progress.close()

    def print_page(self, month):
        """ Prints a month as a page """
        year = self.year
        self.doc.start_paragraph('BIR-Monthstyle')
        self.doc.write_text(GrampsLocale.long_months[month].capitalize())
        self.doc.end_paragraph()
        current_date = datetime.date(year, month, 1)
        current_ord = current_date.toordinal()
        started_day = {}
        for i in range(31):
            thisday = current_date.fromordinal(current_ord)
            if thisday.month == month:
                list = self.calendar.get(month, {}).get(thisday.day, [])
                for p in list:
                    p = p.replace("\n", " ")
                    if thisday not in started_day:
                        self.doc.start_paragraph("BIR-Daystyle")
                        self.doc.write_text(str(thisday.day))
                        self.doc.end_paragraph()
                        started_day[thisday] = 1
                    self.doc.start_paragraph("BIR-Datastyle")
                    self.doc.write_text(p)
                    self.doc.end_paragraph()
            current_ord += 1

class CalendarOptions(MenuReportOptions):
    """ Calendar options for graphic calendar """
    def __init__(self, name, dbase):
        self.__db = dbase
        self.__pid = None
        self.__filter = None
        MenuReportOptions.__init__(self, name, dbase)
    
    def add_menu_options(self, menu):
        """ Add the options for the graphical calendar """
        category_name = _("Report Options")

        year = NumberOption(_("Year of calendar"), time.localtime()[0], 
                            1000, 3000)
        year.set_help(_("Year of calendar"))
        menu.add_option(category_name, "year", year)

        self.__filter = FilterOption(_("Filter"), 0)
        self.__filter.set_help(
               _("Select filter to restrict people that appear on calendar"))
        menu.add_option(category_name, "filter", self.__filter)
        
        self.__pid = PersonOption(_("Center Person"))
        self.__pid.set_help(_("The center person for the report"))
        menu.add_option(category_name, "pid", self.__pid)
        self.__pid.connect('value-changed', self.__update_filters)
        
        self.__update_filters()

        name_format = EnumeratedListOption(_("Name format"), -1)
        for num, name, fmt_str, act in name_displayer.get_name_format():
            name_format.add_item(num, name)
        name_format.set_help(_("Select the format to display names"))
        menu.add_option(category_name, "name_format", name_format)

        country = EnumeratedListOption(_("Country for holidays"), 0)
        count = 0
        for c in  _countries:
            country.add_item(count, c)
            count += 1
        country.set_help(_("Select the country to see associated holidays"))
        menu.add_option(category_name, "country", country)

        start_dow = EnumeratedListOption(_("First day of week"), 1)
        for count in range(1, 8):
            # conversion between gramps numbering (sun=1) and iso numbering (mon=1) of weekdays below
            start_dow.add_item((count+5) % 7 + 1, GrampsLocale.long_days[count].capitalize()) 
        start_dow.set_help(_("Select the first day of the week for the calendar"))
        menu.add_option(category_name, "start_dow", start_dow) 

        maiden_name = EnumeratedListOption(_("Birthday surname"), "own")
        maiden_name.add_item("spouse_first", _("Wives use husband's surname (from first family listed)"))
        maiden_name.add_item("spouse_last", _("Wives use husband's surname (from last family listed)"))
        maiden_name.add_item("own", _("Wives use their own surname"))
        maiden_name.set_help(_("Select married women's displayed surname"))
        menu.add_option(category_name, "maiden_name", maiden_name)

        alive = BooleanOption(_("Include only living people"), True)
        alive.set_help(_("Include only living people in the calendar"))
        menu.add_option(category_name, "alive", alive)

        birthdays = BooleanOption(_("Include birthdays"), True)
        birthdays.set_help(_("Include birthdays in the calendar"))
        menu.add_option(category_name, "birthdays", birthdays)

        anniversaries = BooleanOption(_("Include anniversaries"), True)
        anniversaries.set_help(_("Include anniversaries in the calendar"))
        menu.add_option(category_name, "anniversaries", anniversaries)

        category_name = _("Text Options")

        text1 = StringOption(_("Text Area 1"), _("My Calendar")) 
        text1.set_help(_("First line of text at bottom of calendar"))
        menu.add_option(category_name, "text1", text1)

        text2 = StringOption(_("Text Area 2"), _("Produced with GRAMPS"))
        text2.set_help(_("Second line of text at bottom of calendar"))
        menu.add_option(category_name, "text2", text2)

        text3 = StringOption(_("Text Area 3"), "http://gramps-project.org/",)
        text3.set_help(_("Third line of text at bottom of calendar"))
        menu.add_option(category_name, "text3", text3)
        
    def __update_filters(self):
        """
        Update the filter list based on the selected person
        """
        gid = self.__pid.get_value()
        person = self.__db.get_person_from_gramps_id(gid)
        filter_list = ReportUtils.get_person_filters(person, False)
        self.__filter.set_filters(filter_list)

    def make_my_style(self, default_style, name, description, 
                      size=9, font=BaseDoc.FONT_SERIF, justified ="left", 
                      color=None, align=BaseDoc.PARA_ALIGN_CENTER, 
                      shadow = None, italic=0, bold=0, borders=0, indent=None):
        """ Create paragraph and graphic styles of the same name """
        # Paragraph:
        f = BaseDoc.FontStyle()
        f.set_size(size)
        f.set_type_face(font)
        f.set_italic(italic)
        f.set_bold(bold)
        p = BaseDoc.ParagraphStyle()
        p.set_font(f)
        p.set_alignment(align)
        p.set_description(description)
        p.set_top_border(borders)
        p.set_left_border(borders)
        p.set_bottom_border(borders)
        p.set_right_border(borders)
        if indent:
            p.set(first_indent=indent)
        if justified == "left":
            p.set_alignment(BaseDoc.PARA_ALIGN_LEFT)       
        elif justified == "right":
            p.set_alignment(BaseDoc.PARA_ALIGN_RIGHT)       
        elif justified == "center":
            p.set_alignment(BaseDoc.PARA_ALIGN_CENTER)       
        default_style.add_paragraph_style(name, p)
        # Graphics:
        g = BaseDoc.GraphicsStyle()
        g.set_paragraph_style(name)
        if shadow:
            g.set_shadow(*shadow)
        if color != None:
            g.set_fill_color(color)
        if not borders:
            g.set_line_width(0)
        default_style.add_draw_style(name, g)
        
    def make_default_style(self, default_style):
        """ Add the styles used in this report """
        self.make_my_style(default_style, "CAL-Title", 
                           _('Title text and background color'), 20, 
                           bold=1, italic=1, 
                           color=(0xEA, 0xEA, 0xEA))
        self.make_my_style(default_style, "CAL-Numbers", 
                           _('Calendar day numbers'), 13, 
                           bold=1)
        self.make_my_style(default_style, "CAL-Text", 
                           _('Daily text display'), 9)
        self.make_my_style(default_style, "CAL-Daynames", 
                           _('Days of the week text'), 12, 
                           italic=1, bold=1, 
                           color = (0xEA, 0xEA, 0xEA))
        self.make_my_style(default_style, "CAL-Text1style", 
                           _('Text at bottom, line 1'), 12)
        self.make_my_style(default_style, "CAL-Text2style", 
                           _('Text at bottom, line 2'), 12)
        self.make_my_style(default_style, "CAL-Text3style", 
                           _('Text at bottom, line 3'), 9)
        self.make_my_style(default_style, "CAL-Border", 
                           _('Borders'), borders=True)
        
class CalendarReportOptions(CalendarOptions):
    """ Options for the calendar (birthday and anniversary) report """
    def __init__(self, name, dbstate=None):
        CalendarOptions.__init__(self, name, dbstate)

    def add_menu_options(self, menu):
        """ Add the options for the graphical calendar """
        category_name = _("Text Options")
        titletext = StringOption(_("Title text"), 
                                 _("Birthday and Anniversary Report"))
        titletext.set_help(_("Title of calendar"))
        menu.add_option(category_name, "titletext", titletext)
        CalendarOptions.add_menu_options(self, menu)
        category_name = _("Report Options")
        option = BooleanOption(_("Include relationships to center person"), 
                               False)
        option.set_help(_("Include relationships to center person (slower)"))
        menu.add_option(category_name, "relationships", option)

    def make_default_style(self, default_style):
        """ Add the options for the textual report """
        self.make_my_style(default_style, "BIR-Title", 
                           _('Title text style'), 14, 
                           bold=1, justified="center")
        self.make_my_style(default_style, "BIR-Datastyle", 
                           _('Data text display'), 12, indent=1.0)
        self.make_my_style(default_style, "BIR-Daystyle", 
                           _('Day text style'), 12, indent=.5, 
                           italic=1, bold=1)
        self.make_my_style(default_style, "BIR-Monthstyle", 
                           _('Month text style'), 14, bold=1)
        self.make_my_style(default_style, "BIR-Text1style", 
                           _('Text at bottom, line 1'), 12, justified="center")
        self.make_my_style(default_style, "BIR-Text2style", 
                           _('Text at bottom, line 2'), 12, justified="center")
        self.make_my_style(default_style, "BIR-Text3style", 
                           _('Text at bottom, line 3'), 12, justified="center")

#------------------------------------------------------------------------
#
# XML Classes
#
#------------------------------------------------------------------------
class Element:
    """ A parsed XML element """
    def __init__(self, name, attributes):
        'Element constructor'
        # The element's tag name
        self.name = name
        # The element's attribute dictionary
        self.attributes = attributes
        # The element's cdata
        self.cdata = ''
        # The element's child element list (sequence)
        self.children = []
        
    def AddChild(self, element):
        'Add a reference to a child element'
        self.children.append(element)
        
    def getAttribute(self, key):
        'Get an attribute value'
        return self.attributes.get(key)
    
    def getData(self):
        'Get the cdata'
        return self.cdata
        
    def getElements(self, name=''):
        'Get a list of child elements'
        #If no tag name is specified, return the all children
        if not name:
            return self.children
        else:
            # else return only those children with a matching tag name
            elements = []
            for element in self.children:
                if element.name == name:
                    elements.append(element)
            return elements

    def toString(self, level=0):
        """ Convert item at level to a XML string """
        retval = " " * level
        retval += "<%s" % self.name
        for attribute in self.attributes:
            retval += " %s=\"%s\"" % (attribute, self.attributes[attribute])
        c = ""
        for child in self.children:
            c += child.toString(level+1)
        if c == "":
            retval += "/>\n"
        else:
            retval += ">\n" + c + ("</%s>\n" % self.name)
        return retval

class Xml2Obj:
    """ XML to Object """
    def __init__(self):
        self.root = None
        self.nodeStack = []
        
    def StartElement(self, name, attributes):
        'SAX start element even handler'
        # Instantiate an Element object
        element = Element(name.encode(), attributes)
        # Push element onto the stack and make it a child of parent
        if len(self.nodeStack) > 0:
            parent = self.nodeStack[-1]
            parent.AddChild(element)
        else:
            self.root = element
        self.nodeStack.append(element)
        
    def EndElement(self, name):
        'SAX end element event handler'
        self.nodeStack = self.nodeStack[:-1]

    def CharacterData(self, data):
        'SAX character data event handler'
        if data.strip():
            data = data.encode()
            element = self.nodeStack[-1]
            element.cdata += data
            return

    def Parse(self, filename):
        'Create a SAX parser and parse filename '
        Parser = expat.ParserCreate()
        # SAX event handlers
        Parser.StartElementHandler = self.StartElement
        Parser.EndElementHandler = self.EndElement
        Parser.CharacterDataHandler = self.CharacterData
        # Parse the XML File
        ParserStatus = Parser.Parse(open(filename, 'r').read(), 1)
        return self.root

class Holidays:
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
        for country_set in self.elements.children:
            if country_set.name == "country" and country_set.attributes["name"] == self.country:
                for date in country_set.children:
                    if date.name == "date":
                        data = {"value" : "", 
                                "name" : "", 
                                "offset": "", 
                                "type": "", 
                                "if": "", 
                                } # defaults
                        for attr in date.attributes:
                            data[attr] = date.attributes[attr]
                        self.dates.append(data)
    def get_daynames(self, y, m, dayname):
        """ Get the items for a particular year/month and day of week """
        if self.debug: print "%s's in %d %d..." % (dayname, m, y) 
        retval = [0]
        dow = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'].index(dayname)
        for d in range(1, 32):
            try:
                date = datetime.date(y, m, d)
            except ValueError:
                continue
            if date.weekday() == dow:
                retval.append(d)
        if self.debug: print "dow=", dow, "days=", retval
        return retval
    def check_date(self, date):
        """ Return items that match rules """
        retval = []
        for rule in self.dates:
            if self.debug: print "Checking ", rule["name"], "..."
            offset = 0
            if rule["offset"] != "":
                if rule["offset"].isdigit():
                    offset = int(rule["offset"])
                elif rule["offset"][0] in ["-", "+"] and rule["offset"][1:].isdigit():
                    offset = int(rule["offset"])
                else:
                    # must be a dayname
                    offset = rule["offset"]
            if len(rule["value"]) > 0 and rule["value"][0] == '>':
                # eval exp -> year/num[/day[/month]]
                y, m, d = date.year, date.month, date.day
                rule["value"] = eval(rule["value"][1:])
            if self.debug: print "rule['value']:", rule["value"]
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
                if self.debug: print "num =", num
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
            if self.debug: print ndate, offset, type(offset)
            if type(offset) == int:
                if offset != 0:
                    ndate = ndate.fromordinal(ndate.toordinal() + offset)
            elif type(offset) in [type(u''), str]:
                dir = 1
                if offset[0] == "-":
                    dir = -1
                    offset = offset[1:]
                if offset in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
                    # next tuesday you come to, including this one
                    dow = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'].index(offset)
                    ord = ndate.toordinal()
                    while ndate.fromordinal(ord).weekday() != dow:
                        ord += dir
                    ndate = ndate.fromordinal(ord)
            if self.debug: print "ndate:", ndate, "date:", date
            if ndate == date:
                if rule["if"] != "":
                    if not eval(rule["if"]):
                        continue
                retval.append(rule["name"])
        return retval

def get_countries():
    """ Looks in multiple places for holidays.xml files """
    locations = [const.PLUGINS_DIR, const.USER_PLUGINS]
    holiday_file = 'holidays.xml'
    country_list = []
    for dir in locations:
        holiday_full_path = os.path.join(dir, holiday_file)
        if os.path.exists(holiday_full_path):
            cs = process_holiday_file(holiday_full_path)
            for c in cs:
                if c not in country_list:
                    country_list.append(c)
    country_list.sort()
    country_list.insert(0, _("Don't include holidays"))
    return country_list

def process_holiday_file(filename):
    """ This will process a holiday file for country names """
    parser = Xml2Obj()
    element = parser.Parse(filename)
    country_list = []
    for country_set in element.children:
        if country_set.name == "country":
            if country_set.attributes["name"] not in country_list:
                country_list.append(country_set.attributes["name"])
    return country_list

## Currently reads the XML file on load. Could move this someplace else
## so it only loads when needed.

_countries = get_countries()

#------------------------------------------------------------------------
#
# Register the plugins
#
#------------------------------------------------------------------------
register_report(
    name = 'calendar', 
    category = CATEGORY_DRAW, 
    report_class = Calendar, 
    options_class = CalendarOptions, 
    modes = MODE_GUI | MODE_BKI | MODE_CLI, 
    translated_name = _("Calendar"), 
    status = _("Stable"), 
    author_name = "Douglas S. Blank", 
    author_email = "dblank@cs.brynmawr.edu", 
    description = _("Produces a graphical calendar"), 
    )

register_report(
    name = 'birthday_report', 
    category = CATEGORY_TEXT, 
    report_class = CalendarReport, 
    options_class = CalendarReportOptions, 
    modes = MODE_GUI | MODE_BKI | MODE_CLI, 
    translated_name = _("Birthday and Anniversary Report"), 
    status = _("Stable"), 
    author_name = "Douglas S. Blank", 
    author_email = "dblank@cs.brynmawr.edu", 
    description = _("Produces a report of birthdays and anniversaries"), 
    )
