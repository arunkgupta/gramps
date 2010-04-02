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

# $Id$

"Generate files/Descendant Report"

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
import os
from gettext import gettext as _

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from PluginUtils import register_report
from ReportBase import Report, ReportUtils, ReportOptions, \
     CATEGORY_TEXT, MODE_GUI, MODE_BKI, MODE_CLI
import BaseDoc
import Errors
import Sort
from QuestionDialog import ErrorDialog
import NameDisplay
import DateHandler

#------------------------------------------------------------------------
#
# GTK/GNOME modules
#
#------------------------------------------------------------------------
import gtk

_BORN = _('b.')
_DIED = _('d.')

#------------------------------------------------------------------------
#
# DescendantReport
#
#------------------------------------------------------------------------
class DescendantReport(Report):

    def __init__(self,database,person,options_class):
        """
        Creates the DescendantReport object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        person          - currently selected person
        options_class   - instance of the Options class for this report

        This report needs the following parameters (class variables)
        that come in the options class.
        
        gen       - Maximum number of generations to include.
        pagebbg   - Whether to include page breaks between generations.

        """

        Report.__init__(self,database,person,options_class)

        (self.max_generations,self.pgbrk) \
                        = options_class.get_report_generations()
        sort = Sort.Sort(self.database)
        self.by_birthdate = sort.by_birthdate
        
    def dump_dates(self, person):
        birth_date = ""
        birth_ref = person.get_birth_ref()
        if birth_ref:
            birth = self.database.get_event_from_handle(birth_ref.ref)
            birth_date = DateHandler.get_date(birth)
        else:
            birth = None

        death_date = ""
        death_ref = person.get_death_ref()
        if death_ref:
            death = self.database.get_event_from_handle(death_ref.ref)
            death_date = DateHandler.get_date(death)
        else:
            death = None

        if birth or death:
            self.doc.write_text(' (')

            birth_place = ""
            if birth:
                bplace_handle = birth.get_place_handle()
                if bplace_handle:
                    birth_place = self.database.get_place_from_handle(
                        bplace_handle).get_title()

            death_place = ""
            if death:
                dplace_handle = death.get_place_handle()
                if dplace_handle:
                    death_place = self.database.get_place_from_handle(
                        dplace_handle).get_title()

            if birth:
                if birth_place:
                    self.doc.write_text(_("b. %(birth_date)s - %(place)s") % {
                        'birth_date' : birth_date,
                        'place' : birth_place,
                        })
                else:
                    self.doc.write_text(_("b. %(birth_date)s") % {
                        'birth_date' : birth_date
                        })

            if death:
                if birth:
                    self.doc.write_text(', ')
                if death_place:
                    self.doc.write_text(_("d. %(death_date)s - %(place)s") % {
                        'death_date' : death_date,
                        'place' : death_place,
                        })
                else:
                    self.doc.write_text(_("d. %(death_date)s") % {
                        'death_date' : death_date
                        })

            self.doc.write_text(')')
        
    def write_report(self):
        self.doc.start_paragraph("DR-Title")
        name = NameDisplay.displayer.display(self.start_person)
        title = _("Descendants of %s") % name
        mark = BaseDoc.IndexMark(title,BaseDoc.INDEX_TYPE_TOC,1)
        self.doc.write_text(title,mark)
        self.doc.end_paragraph()
        self.dump(1,self.start_person)

    def dump(self,level,person):

        self.doc.start_paragraph("DR-Level%d" % min(level,32),"%d." % level)
        mark = ReportUtils.get_person_mark(self.database,person)
        self.doc.write_text(NameDisplay.displayer.display(person),mark)
        self.dump_dates(person)
        self.doc.end_paragraph()

        if level >= self.max_generations:
            return
        
        for family_handle in person.get_family_handle_list():
            family = self.database.get_family_from_handle(family_handle)

            spouse_handle = ReportUtils.find_spouse(person,family)
            if spouse_handle:
                spouse = self.database.get_person_from_handle(spouse_handle)
                mark = ReportUtils.get_person_mark(self.database,person)
                self.doc.start_paragraph("DR-Spouse%d" % min(level,32))
                name = NameDisplay.displayer.display(spouse)
                self.doc.write_text(_("sp. %(spouse)s") % {'spouse':name},mark)
                self.dump_dates(spouse)
                self.doc.end_paragraph()

            childlist = family.get_child_ref_list()[:]
            for child_ref in childlist:
                child = self.database.get_person_from_handle(child_ref.ref)
                self.dump(level+1,child)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class DescendantOptions(ReportOptions):

    """
    Defines options and provides handling interface.
    """

    def __init__(self,name,person_id=None):
        ReportOptions.__init__(self,name,person_id)

    def enable_options(self):
        # Semi-common options that should be enabled for this report
        self.enable_dict = {
            'gen'       : 10,
            'pagebbg'   : 0,
        }

    def make_default_style(self,default_style):
        """Make the default output style for the Descendant Report."""
        f = BaseDoc.FontStyle()
        f.set_size(12)
        f.set_type_face(BaseDoc.FONT_SANS_SERIF)
        f.set_bold(1)
        p = BaseDoc.ParagraphStyle()
        p.set_header_level(1)
        p.set_bottom_border(1)
        p.set_top_margin(ReportUtils.pt2cm(3))
        p.set_bottom_margin(ReportUtils.pt2cm(3))
        p.set_font(f)
        p.set_alignment(BaseDoc.PARA_ALIGN_CENTER)
        p.set_description(_("The style used for the title of the page."))
        default_style.add_style("DR-Title",p)

        f = BaseDoc.FontStyle()
        f.set_size(10)
        for i in range(1,33):
            p = BaseDoc.ParagraphStyle()
            p.set_font(f)
            p.set_top_margin(ReportUtils.pt2cm(f.get_size()*0.125))
            p.set_bottom_margin(ReportUtils.pt2cm(f.get_size()*0.125))
            p.set_first_indent(-0.5)
            p.set_left_margin(min(10.0,float(i-0.5)))
            p.set_description(_("The style used for the "
                                "level %d display.") % i)
            default_style.add_style("DR-Level%d" % min(i,32), p)

            p = BaseDoc.ParagraphStyle()
            p.set_font(f)
            p.set_top_margin(ReportUtils.pt2cm(f.get_size()*0.125))
            p.set_bottom_margin(ReportUtils.pt2cm(f.get_size()*0.125))
            p.set_left_margin(min(10.0,float(i-0.5)))
            p.set_description(_("The style used for the "
                                "spouse level %d display.") % i)
            default_style.add_style("DR-Spouse%d" % min(i,32), p)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
register_report(
    name = 'descend_report',
    category = CATEGORY_TEXT,
    report_class = DescendantReport,
    options_class = DescendantOptions,
    modes = MODE_GUI | MODE_BKI | MODE_CLI,
    translated_name = _("Descendant Report"),
    status=(_("Stable")),
    description=_("Generates a list of descendants of the active person"),
    author_name="Donald N. Allingham",
    author_email="don@gramps-project.org"
    )
