#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007 Donald N. Allingham
# Copyright (C) 2007-2008 Brian G. Matherly
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
import gen.lib
import BaseDoc
import DateHandler
from gen.plug import PluginManager
from gen.plug.menu import BooleanOption, FilterOption, PersonOption
from ReportBase import Report, ReportUtils, MenuReportOptions, CATEGORY_TEXT
from ReportBase import Bibliography, Endnotes
from BasicUtils import name_displayer as _nd
from Utils import media_path_full
from QuestionDialog import WarningDialog

#------------------------------------------------------------------------
#
# IndivCompleteReport
#
#------------------------------------------------------------------------
class IndivCompleteReport(Report):

    def __init__(self, database, options_class):
        """
        Create the IndivCompleteReport object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        person          - currently selected person
        options_class   - instance of the Options class for this report

        This report needs the following parameters (class variables)
        that come in the options class.
        
        filter    - Filter to be applied to the people of the database.
                    The option class carries its number, and the function
                    returning the list of filters.
        cites     - Whether or not to include source informaiton.
        """

        Report.__init__(self, database, options_class)

        menu = options_class.menu
        self.use_srcs = menu.get_option_by_name('cites').get_value()

        filter_option = options_class.menu.get_option_by_name('filter')
        self.filter = filter_option.get_filter()
        self.bibli = None

    def write_fact(self,event_ref):
        event = self.database.get_event_from_handle(event_ref.ref)
        if event is None:
            return
        text = ""
        if event_ref.get_role() == gen.lib.EventRoleType.PRIMARY or \
           event_ref.get_role() == gen.lib.EventRoleType.FAMILY:
            name = str(event.get_type())
        else:
            name = '%(event)s (%(role)s)' % {'event' : str(event.get_type()),
                                             'role' : event_ref.get_role()}

        date = DateHandler.get_date(event)
        place_handle = event.get_place_handle()
        if place_handle:
            place = self.database.get_place_from_handle(
                place_handle).get_title()
        else:
            place = ""
        
        if place and date:
            text = _('%(date)s in %(place)s. ') % { 'date' : date,
                                                    'place' : place }
        elif place and not date:
            text = '%s. ' % place
        elif date and not place:
            text = '%s. ' % date

        description = event.get_description()
        if description:
            text = '%s, %s' % (description, text)
        endnotes = ""
        if self.use_srcs:
            endnotes = Endnotes.cite_source(self.bibli, event)

        self.doc.start_row()
        self.normal_cell(name)
        self.doc.start_cell('IDS-NormalCell')
        self.doc.start_paragraph('IDS-Normal')
        self.doc.write_text(text)
        if endnotes:
            self.doc.start_superscript()
            self.doc.write_text(endnotes)
            self.doc.end_superscript()
        self.doc.end_paragraph()
        
        for notehandle in event.get_note_list():
            note = self.database.get_note_from_handle(notehandle)
            text = note.get_styledtext()
            format = note.get_format()
            self.doc.write_styled_note(text, format, 'IDS-Normal')
        
        self.doc.end_cell()
        self.doc.end_row()

    def write_p_entry(self, label, parent, rel, pmark=None):
        self.doc.start_row()
        self.normal_cell(label)

        if parent:
            text = '%(parent)s, relationship: %(relation)s' % { 
                                                            'parent' : parent, 
                                                            'relation' : rel }
            self.normal_cell(text, mark=pmark)
        else:
            self.normal_cell('')
        self.doc.end_row()

    def write_note(self):
        notelist = self.person.get_note_list()
        if not notelist:
            return
        self.doc.start_table('note','IDS-IndTable')
        self.doc.start_row()
        self.doc.start_cell('IDS-TableHead', 2)
        self.doc.start_paragraph('IDS-TableTitle')
        self.doc.write_text(_('Notes'))
        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.end_row()

        for notehandle in notelist:
            note = self.database.get_note_from_handle(notehandle)
            text = note.get_styledtext()
            format = note.get_format()
            self.doc.start_row()
            self.doc.start_cell('IDS-NormalCell', 2)
            self.doc.write_styled_note(text, format, 'IDS-Normal')
            
            self.doc.end_cell()
            self.doc.end_row()

        self.doc.end_table()
        self.doc.start_paragraph("IDS-Normal")
        self.doc.end_paragraph()

    def write_alt_parents(self):

        if len(self.person.get_parent_family_handle_list()) < 2:
            return
        
        self.doc.start_table("altparents","IDS-IndTable")
        self.doc.start_row()
        self.doc.start_cell("IDS-TableHead", 2)
        self.doc.start_paragraph("IDS-TableTitle")
        self.doc.write_text(_("Alternate Parents"))
        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.end_row()
        
        family_handle_list = self.person.get_parent_family_handle_list()
        for family_handle in family_handle_list:
            if family_handle == \
                   self.person.get_main_parents_family_handle():
                continue
            
            family = self.database.get_family_from_handle(family_handle)
            
            # Get the mother and father relationships
            frel = ""
            mrel = ""
            child_handle = self.person.get_handle()
            child_ref_list = family.get_child_ref_list()
            for child_ref in child_ref_list:
                if child_ref.ref == child_handle:
                    frel = str(child_ref.get_father_relation())
                    mrel = str(child_ref.get_mother_relation())
            
            father_handle = family.get_father_handle()
            if father_handle:
                father = self.database.get_person_from_handle(father_handle)
                fname = _nd.display(father)
                mark = ReportUtils.get_person_mark(self.database,father)
                self.write_p_entry(_('Father'),fname,frel,mark)
            else:
                self.write_p_entry(_('Father'),'','')

            mother_handle = family.get_mother_handle()
            if mother_handle:
                mother = self.database.get_person_from_handle(mother_handle)
                mname = _nd.display(mother)
                mark = ReportUtils.get_person_mark(self.database,mother)
                self.write_p_entry(_('Mother'),mname,mrel,mark)
            else:
                self.write_p_entry(_('Mother'),'','')
                
        self.doc.end_table()
        self.doc.start_paragraph("IDS-Normal")
        self.doc.end_paragraph()

    def write_alt_names(self):

        if len(self.person.get_alternate_names()) < 1:
            return
        
        self.doc.start_table("altnames","IDS-IndTable")
        self.doc.start_row()
        self.doc.start_cell("IDS-TableHead",2)
        self.doc.start_paragraph("IDS-TableTitle")
        self.doc.write_text(_("Alternate Names"))
        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.end_row()
        
        for name in self.person.get_alternate_names():
            name_type = str( name.get_type() )
            self.doc.start_row()
            self.normal_cell(name_type)
            text = _nd.display_name(name)
            endnotes = ""
            if self.use_srcs:
                endnotes = Endnotes.cite_source(self.bibli, name)
            self.normal_cell(text,endnotes)
            self.doc.end_row()
        self.doc.end_table()
        self.doc.start_paragraph('IDS-Normal')
        self.doc.end_paragraph()
        
    def write_addresses(self):
        
        alist = self.person.get_address_list()

        if len(alist) == 0:
            return
        
        self.doc.start_table("addresses","IDS-IndTable")
        self.doc.start_row()
        self.doc.start_cell("IDS-TableHead",2)
        self.doc.start_paragraph("IDS-TableTitle")
        self.doc.write_text(_("Addresses"))
        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.end_row()
        
        for addr in alist:
            text = ReportUtils.get_address_str(addr)
            date = DateHandler.get_date(addr)
            endnotes = ""
            if self.use_srcs:
                endnotes = Endnotes.cite_source(self.bibli,addr)
            self.doc.start_row()
            self.normal_cell(date)
            self.normal_cell(text,endnotes)
            self.doc.end_row()
        self.doc.end_table()
        self.doc.start_paragraph('IDS-Normal')
        self.doc.end_paragraph()
        
    def write_families(self):

        if not len(self.person.get_family_handle_list()):
            return
        
        self.doc.start_table("three","IDS-IndTable")
        self.doc.start_row()
        self.doc.start_cell("IDS-TableHead", 2)
        self.doc.start_paragraph("IDS-TableTitle")
        self.doc.write_text(_("Marriages/Children"))
        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.end_row()
        
        for family_handle in self.person.get_family_handle_list():
            family = self.database.get_family_from_handle(family_handle)
            if self.person.get_handle() == family.get_father_handle():
                spouse_id = family.get_mother_handle()
            else:
                spouse_id = family.get_father_handle()
            self.doc.start_row()
            self.doc.start_cell("IDS-NormalCell", 2)
            self.doc.start_paragraph("IDS-Spouse")
            if spouse_id:
                spouse = self.database.get_person_from_handle(spouse_id)
                text = _nd.display(spouse)
                mark = ReportUtils.get_person_mark(self.database, spouse)
            else:
                text = _("unknown")
                mark = None
            self.doc.write_text(text, mark)
            self.doc.end_paragraph()
            self.doc.end_cell()
            self.doc.end_row()
            
            for event_ref in family.get_event_ref_list():
                if event_ref:
                    self.write_fact(event_ref)

            child_ref_list = family.get_child_ref_list()
            if len(child_ref_list):
                self.doc.start_row()
                self.normal_cell(_("Children"))

                self.doc.start_cell("IDS-ListCell")

                for child_ref in child_ref_list:
                    self.doc.start_paragraph("IDS-Normal")
                    child = self.database.get_person_from_handle(child_ref.ref)
                    name = _nd.display(child)
                    mark = ReportUtils.get_person_mark(self.database, child)
                    self.doc.write_text(name, mark)
                    self.doc.end_paragraph()
                self.doc.end_cell()
                self.doc.end_row()
        self.doc.end_table()
        self.doc.start_paragraph('IDS-Normal')
        self.doc.end_paragraph()

    def write_facts(self):
        self.doc.start_table("two","IDS-IndTable")
        self.doc.start_row()
        self.doc.start_cell("IDS-TableHead",2)
        self.doc.start_paragraph("IDS-TableTitle")
        self.doc.write_text(_("Individual Facts"))
        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.end_row()

        event_ref_list = self.person.get_event_ref_list()
        for event_ref in event_ref_list:
            if event_ref:
                self.write_fact(event_ref)
        self.doc.end_table()
        self.doc.start_paragraph("IDS-Normal")
        self.doc.end_paragraph()

    def normal_cell(self,text,endnotes=None,mark=None):
        self.doc.start_cell('IDS-NormalCell')
        self.doc.start_paragraph('IDS-Normal')
        self.doc.write_text(text,mark)
        if endnotes:
            self.doc.start_superscript()
            self.doc.write_text(endnotes)
            self.doc.end_superscript()
        self.doc.end_paragraph()
        self.doc.end_cell()

    def write_report(self):
        plist = self.database.get_person_handles(sort_handles=False)
        if self.filter:
            ind_list = self.filter.apply(self.database,plist)
        else:
            ind_list = plist
            
        count = 0
        for person_handle in ind_list:
            self.person = self.database.get_person_from_handle(
                person_handle)
            self.write_person(count)
            count = count + 1

    def write_person(self,count):
        if count != 0:
            self.doc.page_break()
        self.bibli = Bibliography(Bibliography.MODE_PAGE)
        
        media_list = self.person.get_media_list()
        name = _nd.display(self.person)
        title = _("Summary of %s") % name
        mark = BaseDoc.IndexMark(title,BaseDoc.INDEX_TYPE_TOC,1)
        self.doc.start_paragraph("IDS-Title")
        self.doc.write_text(title,mark)
        self.doc.end_paragraph()

        self.doc.start_paragraph("IDS-Normal")
        self.doc.end_paragraph()

        if len(media_list) > 0:
            object_handle = media_list[0].get_reference_handle()
            object = self.database.get_object_from_handle(object_handle)
            mime_type = object.get_mime_type()
            if mime_type and mime_type.startswith("image"):
                filename = media_path_full(self.database, object.get_path())
                if os.path.exists(filename):
                    self.doc.start_paragraph("IDS-Normal")
                    self.doc.add_media_object(filename, "right", 4.0, 4.0)
                    self.doc.end_paragraph()
                else:
                    WarningDialog(_("Could not add photo to page"),
                          "%s: %s" % (filename, _('File does not exist')))

        self.doc.start_table("one","IDS-IndTable")

        self.doc.start_row()
        self.normal_cell("%s:" % _("Name"))
        name = self.person.get_primary_name()
        text = _nd.display_name(name)
        mark = ReportUtils.get_person_mark(self.database, self.person)
        endnotes = ""
        if self.use_srcs:
            endnotes = Endnotes.cite_source(self.bibli, name)
        self.normal_cell(text,endnotes,mark)
        self.doc.end_row()

        self.doc.start_row()
        self.normal_cell("%s:" % _("Gender"))
        if self.person.get_gender() == gen.lib.Person.MALE:
            self.normal_cell(_("Male"))
        elif self.person.get_gender() == gen.lib.Person.FEMALE:
            self.normal_cell(_("Female"))
        else:
            self.normal_cell(_("Unknown"))
        self.doc.end_row()

        family_handle = self.person.get_main_parents_family_handle()
        if family_handle:
            family = self.database.get_family_from_handle(family_handle)
            father_inst_id = family.get_father_handle()
            if father_inst_id:
                father_inst = self.database.get_person_from_handle(
                    father_inst_id)
                father = _nd.display(father_inst)
                fmark = ReportUtils.get_person_mark(self.database,father_inst)
            else:
                father = ""
                fmark = None
            mother_inst_id = family.get_mother_handle()
            if mother_inst_id:
                mother_inst = self.database.get_person_from_handle(
                    mother_inst_id) 
                mother = _nd.display(mother_inst)
                mmark = ReportUtils.get_person_mark(self.database,mother_inst)
            else:
                mother = ""
                mmark = None
        else:
            father = ""
            fmark = None
            mother = ""
            mmark = None

        self.doc.start_row()
        self.normal_cell("%s:" % _("Father"))
        self.normal_cell(father,mark=fmark)
        self.doc.end_row()

        self.doc.start_row()
        self.normal_cell("%s:" % _("Mother"))
        self.normal_cell(mother,mark=mmark)
        self.doc.end_row()
        self.doc.end_table()

        self.doc.start_paragraph("IDS-Normal")
        self.doc.end_paragraph()

        self.write_alt_names()
        self.write_facts()
        self.write_alt_parents()
        self.write_families()
        self.write_addresses()
        self.write_note()
        if self.use_srcs:
            Endnotes.write_endnotes(self.bibli,self.database,self.doc)
            
#------------------------------------------------------------------------
#
# IndivCompleteOptions
#
#------------------------------------------------------------------------
class IndivCompleteOptions(MenuReportOptions):
    """
    Defines options and provides handling interface.
    """
    def __init__(self, name, dbase):
        self.__db = dbase
        self.__pid = None
        self.__filter = None
        MenuReportOptions.__init__(self, name, dbase)
        
    def add_menu_options(self, menu):
        ################################
        category_name = _("Report Options")
        ################################
        
        self.__filter = FilterOption(_("Filter"), 0)
        self.__filter.set_help(
                           _("Select the filter to be applied to the report"))
        menu.add_option(category_name, "filter", self.__filter)
        self.__filter.connect('value-changed', self.__filter_changed)

        self.__pid = PersonOption(_("Filter Person"))
        self.__pid.set_help(_("The center person for the filter"))
        menu.add_option(category_name, "pid", self.__pid)
        self.__pid.connect('value-changed', self.__update_filters)
        
        self.__update_filters()
        
        cites = BooleanOption(_("Include Source Information"), True)
        cites.set_help(_("Whether to cite sources."))
        menu.add_option(category_name, "cites", cites)
        
    def __update_filters(self):
        """
        Update the filter list based on the selected person
        """
        gid = self.__pid.get_value()
        person = self.__db.get_person_from_gramps_id(gid)
        filter_list = ReportUtils.get_person_filters(person, True)
        self.__filter.set_filters(filter_list)
        
    def __filter_changed(self):
        """
        Handle filter change. If the filter is not specific to a person,
        disable the person option
        """
        filter_value = self.__filter.get_value()
        if filter_value in [0, 2, 3, 4, 5]:
            # Filters 0, 2, 3, 4 and 5 rely on the center person
            self.__pid.set_available(True)
        else:
            # The rest don't
            self.__pid.set_available(False)

    def make_default_style(self,default_style):
        """Make the default output style for the Individual Complete Report."""
        # Paragraph Styles
        font = BaseDoc.FontStyle()
        font.set_bold(1)
        font.set_type_face(BaseDoc.FONT_SANS_SERIF)
        font.set_size(16)
        p = BaseDoc.ParagraphStyle()
        p.set_alignment(BaseDoc.PARA_ALIGN_CENTER)
        p.set_top_margin(ReportUtils.pt2cm(8))
        p.set_bottom_margin(ReportUtils.pt2cm(8))
        p.set_font(font)
        p.set_description(_("The style used for the title of the page."))
        default_style.add_paragraph_style("IDS-Title",p)
    
        font = BaseDoc.FontStyle()
        font.set_bold(1)
        font.set_type_face(BaseDoc.FONT_SANS_SERIF)
        font.set_size(12)
        font.set_italic(1)
        p = BaseDoc.ParagraphStyle()
        p.set_font(font)
        p.set_top_margin(ReportUtils.pt2cm(3))
        p.set_bottom_margin(ReportUtils.pt2cm(3))
        p.set_description(_("The style used for category labels."))
        default_style.add_paragraph_style("IDS-TableTitle",p)

        font = BaseDoc.FontStyle()
        font.set_bold(1)
        font.set_type_face(BaseDoc.FONT_SANS_SERIF)
        font.set_size(12)
        p = BaseDoc.ParagraphStyle()
        p.set_font(font)
        p.set_top_margin(ReportUtils.pt2cm(3))
        p.set_bottom_margin(ReportUtils.pt2cm(3))
        p.set_description(_("The style used for the spouse's name."))
        default_style.add_paragraph_style("IDS-Spouse",p)

        font = BaseDoc.FontStyle()
        font.set_size(12)
        p = BaseDoc.ParagraphStyle()
        p.set_font(font)
        p.set_top_margin(ReportUtils.pt2cm(3))
        p.set_bottom_margin(ReportUtils.pt2cm(3))
        p.set_description(_('The basic style used for the text display.'))
        default_style.add_paragraph_style("IDS-Normal",p)
        
        # Table Styles
        tbl = BaseDoc.TableStyle()
        tbl.set_width(100)
        tbl.set_columns(2)
        tbl.set_column_width(0,20)
        tbl.set_column_width(1,80)
        default_style.add_table_style("IDS-IndTable",tbl)

        tbl = BaseDoc.TableStyle()
        tbl.set_width(100)
        tbl.set_columns(2)
        tbl.set_column_width(0,50)
        tbl.set_column_width(1,50)
        default_style.add_table_style("IDS-ParentsTable",tbl)

        cell = BaseDoc.TableCellStyle()
        cell.set_top_border(1)
        cell.set_bottom_border(1)
        default_style.add_cell_style("IDS-TableHead",cell)

        cell = BaseDoc.TableCellStyle()
        default_style.add_cell_style("IDS-NormalCell",cell)

        cell = BaseDoc.TableCellStyle()
        cell.set_longlist(1)
        default_style.add_cell_style("IDS-ListCell",cell)
        
        Endnotes.add_endnote_styles(default_style)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
pmgr = PluginManager.get_instance()
pmgr.register_report(
    name = 'indiv_complete',
    category = CATEGORY_TEXT,
    report_class = IndivCompleteReport,
    options_class = IndivCompleteOptions,
    modes = PluginManager.REPORT_MODE_GUI | \
            PluginManager.REPORT_MODE_BKI | \
            PluginManager.REPORT_MODE_CLI,
    translated_name = _("Complete Individual Report"),
    status = _("Stable"),
    author_name = "Donald N. Allingham",
    author_email = "don@gramps-project.org",
    description = _("Produces a complete report on the selected people"),
    )
