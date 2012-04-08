#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007-2008 Brian G. Matherly
# Copyright (C) 2009      Gary Burton
# Contribution  2009 by   Reinhard Mueller <reinhard.mueller@bytewise.at> 
# Copyright (C) 2010       Jakim Friant
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

"""Reports/Text Reports/Kinship Report"""

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
import copy
from gen.ggettext import gettext as _

#------------------------------------------------------------------------
#
# gramps modules
#
#------------------------------------------------------------------------
from gen.display.name import displayer as global_name_display
from Errors import ReportError
import Relationship
from gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle,
                    FONT_SANS_SERIF, INDEX_TYPE_TOC, PARA_ALIGN_CENTER)
from gen.plug.menu import (NumberOption, BooleanOption, PersonOption,
                        EnumeratedListOption)
from gen.plug.report import Report
from gen.plug.report import utils as ReportUtils
from gen.plug.report import MenuReportOptions
import DateHandler
from gen.utils import get_birth_or_fallback, get_death_or_fallback

#------------------------------------------------------------------------
#
# KinshipReport
#
#------------------------------------------------------------------------
class KinshipReport(Report):

    def __init__(self, database, options, user):
        """
        Create the KinshipReport object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        options         - instance of the Options class for this report
        user            - a gen.user.User() instance

        This report needs the following parameters (class variables)
        that come in the options class.
        
        maxdescend    - Maximum generations of descendants to include.
        maxascend     - Maximum generations of ancestors to include.
        incspouses    - Whether to include spouses.
        inccousins    - Whether to include cousins.
        incaunts      - Whether to include aunts/uncles/nephews/nieces.
        pid           - The Gramps ID of the center person for the report.
        name_format   - Preferred format to display names
        """
        Report.__init__(self, database, options, user)

        menu = options.menu
        self.max_descend = menu.get_option_by_name('maxdescend').get_value()
        self.max_ascend  = menu.get_option_by_name('maxascend').get_value()
        self.inc_spouses = menu.get_option_by_name('incspouses').get_value()
        self.inc_cousins = menu.get_option_by_name('inccousins').get_value()
        self.inc_aunts   = menu.get_option_by_name('incaunts').get_value()
        pid              = menu.get_option_by_name('pid').get_value()
        self.person = database.get_person_from_gramps_id(pid)
        if (self.person == None) :
            raise ReportError(_("Person %s is not in the Database") % pid )

        # Copy the global NameDisplay so that we don't change application 
        # defaults.
        self._name_display = copy.deepcopy(global_name_display)
        name_format = menu.get_option_by_name("name_format").get_value()
        if name_format != 0:
            self._name_display.set_default_format(name_format)

        self.__db = database
        self.rel_calc = Relationship.get_relationship_calculator()

        self.kinship_map = {}
        self.spouse_map = {}

    def write_report(self):
        """
        The routine the actually creates the report. At this point, the document
        is opened and ready for writing.
        """
        pname = self._name_display.display(self.person)
        
        self.doc.start_paragraph("KIN-Title")
        title = _("Kinship Report for %s") % pname
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()

        if self.inc_spouses:
            spouse_handles = self.get_spouse_handles(self.person.get_handle())
            if spouse_handles:
                self.write_people(_("Spouses"), spouse_handles)

        # Collect all descendants of the person
        self.traverse_down(self.person.get_handle(), 0, 1)
        
        # Collect all ancestors/aunts/uncles/nephews/cousins of the person
        self.traverse_up(self.person.get_handle(), 1, 0)
                
        # Write Kin
        for Ga, Gbs in self.kinship_map.iteritems():
            for Gb in Gbs:
                # To understand these calculations, see: 
                # http://en.wikipedia.org/wiki/Cousin#Mathematical_definitions
                x = min (Ga, Gb)
                y = abs(Ga-Gb)
                # Skip unrequested people
                if x == 1 and y > 0 and not self.inc_aunts:
                    continue
                elif x > 1 and not self.inc_cousins:
                    continue
                
                get_rel_str = self.rel_calc.get_plural_relationship_string
                
                title = get_rel_str(Ga, Gb, in_law_b=False)
                self.write_people(title, self.kinship_map[Ga][Gb])
                
                if (self.inc_spouses and
                   Ga in self.spouse_map and
                   Gb in self.spouse_map[Ga]):
                    title = get_rel_str(Ga, Gb, in_law_b=True)
                    self.write_people(title, self.spouse_map[Ga][Gb])

    def traverse_down(self, person_handle, Ga, Gb, skip_handle=None):
        """
        Populate a map of arrays containing person handles for the descendants
        of the passed person. This function calls itself recursively until it
        reaches max_descend.
        
        Parameters:
        person_handle: the handle of the person to go to next
        Ga: The number of generations from the main person to the common 
           ancestor. This should be incremented when going up generations, and 
           left alone when going down generations.
        Gb: The number of generations from this person (person_handle) to the 
           common ancestor. This should be incremented when going down 
           generations and set back to zero when going up generations.
        skip_handle: an optional handle to skip when going down. This is useful
           to skip the descendant that brought you this generation in the first
           place.
        """
        for child_handle in self.get_children_handles(person_handle):
            if child_handle != skip_handle:
                self.add_kin(child_handle, Ga, Gb)
            
                if self.inc_spouses:
                    for spouse_handle in self.get_spouse_handles(child_handle):
                        self.add_spouse(spouse_handle, Ga, Gb)
                    
                if Gb < self.max_descend:
                    self.traverse_down(child_handle, Ga, Gb+1)
                    
    def traverse_up(self, person_handle, Ga, Gb):
        """
        Populate a map of arrays containing person handles for the ancestors
        of the passed person. This function calls itself recursively until it
        reaches max_ascend.
        
        Parameters:
        person_handle: the handle of the person to go to next
        Ga: The number of generations from the main person to the common 
           ancestor. This should be incremented when going up generations, and 
           left alone when going down generations.
        Gb: The number of generations from this person (person_handle) to the 
           common ancestor. This should be incremented when going down 
           generations and set back to zero when going up generations.
        """
        parent_handles = self.get_parent_handles(person_handle)
        for parent_handle in parent_handles:
            self.add_kin(parent_handle, Ga, Gb)
            self.traverse_down(parent_handle, Ga, Gb+1, person_handle)
            if Ga < self.max_ascend:
                self.traverse_up(parent_handle, Ga+1, 0)
                
    def add_kin(self, person_handle, Ga, Gb):
        """
        Add a person handle to the kin map.
        """
        if Ga not in self.kinship_map:
            self.kinship_map[Ga] = {}
        if Gb not in self.kinship_map[Ga]:
            self.kinship_map[Ga][Gb] = []
        if person_handle not in self.kinship_map[Ga][Gb]:
            self.kinship_map[Ga][Gb].append(person_handle)
        
    def add_spouse(self, spouse_handle, Ga, Gb):
        """
        Add a person handle to the spouse map.
        """
        if Ga not in self.spouse_map:
            self.spouse_map[Ga] = {}
        if Gb not in self.spouse_map[Ga]:
            self.spouse_map[Ga][Gb] = []
        if spouse_handle not in self.spouse_map[Ga][Gb]:
            self.spouse_map[Ga][Gb].append(spouse_handle)
                
    def get_parent_handles(self, person_handle):
        """
        Return an array of handles for all the parents of the 
        given person handle.
        """
        parent_handles = []
        person = self.__db.get_person_from_handle(person_handle)
        family_handle = person.get_main_parents_family_handle()
        if family_handle:
            family = self.__db.get_family_from_handle(family_handle)
            father_handle = family.get_father_handle()
            if father_handle:
                parent_handles.append(father_handle)
            mother_handle = family.get_mother_handle()
            if mother_handle:
                parent_handles.append(mother_handle)
        return parent_handles
                
    def get_spouse_handles(self, person_handle):
        """
        Return an array of handles for all the spouses of the 
        given person handle.
        """
        spouses = []
        person = self.__db.get_person_from_handle(person_handle)
        for family_handle in person.get_family_handle_list():
            family = self.__db.get_family_from_handle(family_handle)
            father_handle = family.get_father_handle()
            mother_handle = family.get_mother_handle()
            spouse_handle = None
            if mother_handle and father_handle == person_handle:
                spouse_handle = mother_handle
            elif father_handle and mother_handle == person_handle:
                spouse_handle = father_handle
            
            if spouse_handle and spouse_handle not in spouses:
                spouses.append(spouse_handle)
        return spouses
    
    def get_children_handles(self, person_handle):
        """
        Return an array of handles for all the children of the 
        given person handle.
        """
        children = []
        person = self.__db.get_person_from_handle(person_handle)
        for family_handle in person.get_family_handle_list():
            family = self.__db.get_family_from_handle(family_handle)
            for child_ref in family.get_child_ref_list():
                children.append(child_ref.get_reference_handle())
        return children
    
    def write_people(self, title, people_handles):
        """
        Write information about a group of people - including the title.
        """
        cap_title = title[0].upper() + title[1:]
        subtitle = "%s (%d)" % (cap_title, len(people_handles))
        self.doc.start_paragraph("KIN-Subtitle")
        mark = IndexMark(cap_title, INDEX_TYPE_TOC, 2)
        self.doc.write_text(subtitle, mark)
        self.doc.end_paragraph()
        map(self.write_person, people_handles)

    def write_person(self, person_handle):
        """
        Write information about the given person.
        """
        person = self.database.get_person_from_handle(person_handle)

        name = self._name_display.display(person)
        mark = ReportUtils.get_person_mark(self.database, person)
        birth_date = ""
        birth = get_birth_or_fallback(self.database, person)
        if birth:
            birth_date = DateHandler.get_date(birth)
        
        death_date = ""
        death = get_death_or_fallback(self.database, person)
        if death:
            death_date = DateHandler.get_date(death)
        dates = _(" (%(birth_date)s - %(death_date)s)") % { 
                                            'birth_date' : birth_date,
                                            'death_date' : death_date }
        
        self.doc.start_paragraph('KIN-Normal')
        self.doc.write_text(name, mark)
        self.doc.write_text(dates)
        self.doc.end_paragraph()

#------------------------------------------------------------------------
#
# KinshipOptions
#
#------------------------------------------------------------------------
class KinshipOptions(MenuReportOptions):

    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, dbase):
        MenuReportOptions.__init__(self, name, dbase)
        
    def add_menu_options(self, menu):
        """
        Add options to the menu for the kinship report.
        """
        category_name = _("Report Options")
        
        pid = PersonOption(_("Center Person"))
        pid.set_help(_("The center person for the report"))
        menu.add_option(category_name, "pid", pid)

        # We must figure out the value of the first option before we can
        # create the EnumeratedListOption
        fmt_list = global_name_display.get_name_format()
        name_format = EnumeratedListOption(_("Name format"), 0)
        name_format.add_item(0, _("Default"))
        for num, name, fmt_str, act in fmt_list:
            name_format.add_item(num, name)
        name_format.set_help(_("Select the format to display names"))
        menu.add_option(category_name, "name_format", name_format)

        maxdescend = NumberOption(_("Max Descendant Generations"), 2, 1, 20)
        maxdescend.set_help(_("The maximum number of descendant generations"))
        menu.add_option(category_name, "maxdescend", maxdescend)
        
        maxascend = NumberOption(_("Max Ancestor Generations"), 2, 1, 20)
        maxascend.set_help(_("The maximum number of ancestor generations"))
        menu.add_option(category_name, "maxascend", maxascend)
        
        incspouses = BooleanOption(_("Include spouses"), True)
        incspouses.set_help(_("Whether to include spouses"))
        menu.add_option(category_name, "incspouses", incspouses)
        
        inccousins = BooleanOption(_("Include cousins"), True)
        inccousins.set_help(_("Whether to include cousins"))
        menu.add_option(category_name, "inccousins", inccousins)
        
        incaunts = BooleanOption(_("Include aunts/uncles/nephews/nieces"), True)
        incaunts.set_help(_("Whether to include aunts/uncles/nephews/nieces"))
        menu.add_option(category_name, "incaunts", incaunts)        

    def make_default_style(self, default_style):
        """Make the default output style for the Kinship Report."""
        f = FontStyle()
        f.set_size(16)
        f.set_type_face(FONT_SANS_SERIF)
        f.set_bold(1)
        p = ParagraphStyle()
        p.set_header_level(1)
        p.set_bottom_border(1)
        p.set_bottom_margin(ReportUtils.pt2cm(8))
        p.set_font(f)
        p.set_alignment(PARA_ALIGN_CENTER)
        p.set_description(_("The style used for the title of the page."))
        default_style.add_paragraph_style("KIN-Title", p)
        
        font = FontStyle()
        font.set_size(12)
        font.set_bold(True)
        p = ParagraphStyle()
        p.set_header_level(3)
        p.set_font(font)
        p.set_top_margin(ReportUtils.pt2cm(6))
        p.set_description(_('The basic style used for sub-headings.'))
        default_style.add_paragraph_style("KIN-Subtitle", p)
        
        font = FontStyle()
        font.set_size(10)
        p = ParagraphStyle()
        p.set_font(font)
        p.set_left_margin(0.5)
        p.set_description(_('The basic style used for the text display.'))
        default_style.add_paragraph_style("KIN-Normal", p)