#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2002 Bruce J. DeGrasse
# Copyright (C) 2000-2007 Donald N. Allingham
# Copyright (C) 2007-2009 Brian G. Matherly
# Copyright (C) 2008      James Friedmann <jfriedmannj@gmail.com>
# Copyright (C) 2009      Benny Malengier <benny.malengier@gramps-project.org>
# Copyright (C) 2010      Jakim Friant
# Copyright (C) 2010      Vlada Peri\u0107
# Copyright (C) 2011       Tim G L Lyons
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

"""Reports/Text Reports/Detailed Ancestral Report"""

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
import copy
from gramps.gen.ggettext import gettext as _

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gramps.gen.display.name import displayer as global_name_display
from gramps.gen.errors import ReportError
from gramps.gen.lib import EventType, FamilyRelType, Person, NoteType
from gramps.gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle,
                            FONT_SANS_SERIF, FONT_SERIF, 
                            INDEX_TYPE_TOC, PARA_ALIGN_CENTER)
from gramps.gen.plug.menu import BooleanOption, NumberOption, PersonOption, EnumeratedListOption
from gramps.gen.plug.report import ( Report, Bibliography )
from gramps.gen.plug.report import endnotes
from gramps.gen.plug.report import utils as ReportUtils
from gramps.gen.plug.report import MenuReportOptions
from gramps.plugins.lib.libnarrate import Narrator
from gramps.gen.utils.trans import get_available_translations
from gramps.plugins.lib.libtranslate import Translator, get_language_string

#------------------------------------------------------------------------
#
# Constants
#
#------------------------------------------------------------------------
EMPTY_ENTRY = "_____________"

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class DetAncestorReport(Report):

    def __init__(self, database, options, user):
        """
        Create the DetAncestorReport object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        options         - instance of the Options class for this report
        user            - a gen.user.User() instance

        This report needs the following parameters (class variables)
        that come in the options class.
        
        gen           - Maximum number of generations to include.
        pagebgg       - Whether to include page breaks between generations.
        pageben       - Whether to include page break before End Notes.
        firstName     - Whether to use first names instead of pronouns.
        fulldate      - Whether to use full dates instead of just year.
        listchildren  - Whether to list children.
        includenotes  - Whether to include notes.
        incattrs      - Whether to include attributes
        blankplace    - Whether to replace missing Places with ___________.
        blankDate     - Whether to replace missing Dates with ___________.
        calcageflag   - Whether to compute age.
        dupperson     - Whether to omit duplicate ancestors (e.g. when distant cousins mary).
        verbose       - Whether to use complete sentences
        childref      - Whether to add descendant references in child list.
        addimages     - Whether to include images.
        pid           - The Gramps ID of the center person for the report.
        name_format   - Preferred format to display names
        """
        Report.__init__(self, database, options, user)

        self.map = {}
        self._user = user

        menu = options.menu
        get_option_by_name = menu.get_option_by_name
        get_value = lambda name: get_option_by_name(name).get_value()

        self.max_generations = get_value('gen')
        self.pgbrk         = get_value('pagebbg')
        self.pgbrkenotes   = get_value('pageben')
        self.fulldate      = get_value('fulldates')
        use_fulldate     = self.fulldate
        self.listchildren  = get_value('listc')
        self.includenotes  = get_value('incnotes')
        use_call           = get_value('usecall')
        blankplace         = get_value('repplace')
        blankdate          = get_value('repdate')
        self.calcageflag   = get_value('computeage')
        self.dupperson     = get_value('omitda')
        self.verbose       = get_value('verbose')
        self.childref      = get_value('desref')
        self.addimages     = get_value('incphotos')
        self.inc_names     = get_value('incnames')
        self.inc_events    = get_value('incevents')
        self.inc_addr      = get_value('incaddresses')
        self.inc_sources   = get_value('incsources')
        self.inc_srcnotes  = get_value('incsrcnotes')
        self.inc_attrs     = get_value('incattrs')
        pid                = get_value('pid')
        self.center_person = database.get_person_from_gramps_id(pid)
        if (self.center_person == None) :
            raise ReportError(_("Person %s is not in the Database") % pid )

        # Copy the global NameDisplay so that we don't change application 
        # defaults.
        self._name_display = copy.deepcopy(global_name_display)
            
        name_format = menu.get_option_by_name("name_format").get_value()
        if name_format != 0:
            self._name_display.set_default_format(name_format)

        self.gen_handles = {}
        self.prev_gen_handles = {}
        
        if blankdate:
            empty_date = EMPTY_ENTRY
        else:
            empty_date = ""

        if blankplace:
            empty_place = EMPTY_ENTRY
        else:
            empty_place = ""

        language = get_value('trans')
        translator = Translator(language)
        self._ = translator.gettext

        self.__narrator = Narrator(self.database, self.verbose, use_call,use_fulldate , 
                                   empty_date, empty_place,
                                   translator=translator,
                                   get_endnote_numbers=self.endnotes)

        self.__get_date = translator.get_date

        self.__get_type = translator.get_type

        self.bibli = Bibliography(Bibliography.MODE_DATE|Bibliography.MODE_PAGE)

    def apply_filter(self, person_handle, index):
        if (not person_handle) or (index >= 2**self.max_generations):
            return
        self.map[index] = person_handle

        person = self.database.get_person_from_handle(person_handle)
        family_handle = person.get_main_parents_family_handle()
        if family_handle:
            family = self.database.get_family_from_handle(family_handle)
            self.apply_filter(family.get_father_handle(), index*2)
            self.apply_filter(family.get_mother_handle(), (index*2)+1)

    def write_report(self):
        self.apply_filter(self.center_person.get_handle(), 1)

        name = self._name_display.display_name(self.center_person.get_primary_name())
        self.doc.start_paragraph("DAR-Title")
        # feature request 2356: avoid genitive form
        title = self._("Ancestral Report for %s") % name
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()

        generation = 0

        for key in sorted(self.map):
            if generation == 0 or key >= 2**generation:
                if self.pgbrk and generation > 0:
                    self.doc.page_break()
                self.doc.start_paragraph("DAR-Generation")
                text = self._("Generation %d") % (generation+1)
                mark = IndexMark(text, INDEX_TYPE_TOC, 2)
                self.doc.write_text(text, mark)
                self.doc.end_paragraph()
                generation += 1
                if self.childref:
                    self.prev_gen_handles = self.gen_handles.copy()
                    self.gen_handles.clear()

            person_handle = self.map[key]
            person = self.database.get_person_from_handle(person_handle)
            self.gen_handles[person_handle] = key
            dupperson = self.write_person(key)
            if dupperson == 0:      # Is this a duplicate ind record
                if self.listchildren or self.inc_events:
                    for family_handle in person.get_family_handle_list():
                        family = self.database.get_family_from_handle(family_handle)
                        mother_handle = family.get_mother_handle()
                        if (mother_handle is None                      or
                            mother_handle not in self.map.itervalues()  or
                            person.get_gender() == Person.FEMALE):
                            # The second test above also covers the 1. person's
                            # mate, which is not an ancestor and as such is not
                            # included in the self.map dictionary
                            if self.listchildren:
                                self.write_children(family)
                            if self.inc_events:
                                self.write_family_events(family)
        if self.inc_sources:
            if self.pgbrkenotes:
                self.doc.page_break()
            # it ignores language set for Note type (use locale)
            endnotes.write_endnotes(self.bibli, self.database, self.doc,
                                    printnotes=self.inc_srcnotes)

    def write_person(self, key):
        """Output birth, death, parentage, marriage and notes information """

        person_handle = self.map[key]
        person = self.database.get_person_from_handle(person_handle)
        plist = person.get_media_list()
        self.__narrator.set_subject(person)
        
        if self.addimages and len(plist) > 0:
            photo = plist[0]
            ReportUtils.insert_image(self.database, self.doc, photo, self._user)

        self.doc.start_paragraph("DAR-First-Entry","%s." % str(key))

        name = self._name_display.display_formal(person)
        mark = ReportUtils.get_person_mark(self.database, person)

        self.doc.start_bold()
        self.doc.write_text(name, mark)
        if name[-1:] == '.':
            self.doc.write_text_citation("%s " % self.endnotes(person))
        else:
            self.doc.write_text_citation("%s. " % self.endnotes(person))
        self.doc.end_bold()

        if self.dupperson:
            # Check for duplicate record (result of distant cousins marrying)
            for dkey in sorted(self.map):
                if dkey >= key: 
                    break
                if self.map[key] == self.map[dkey]:
                    self.doc.write_text(
                        self._("%(name)s is the same person as [%(id_str)s].") % 
                        { 'name' : '', 'id_str' : str(dkey) })
                    self.doc.end_paragraph()
                    return 1    # Duplicate person
        
        if not self.verbose:
            self.write_parents(person)

        text = self.__narrator.get_born_string()
        if text:
            self.doc.write_text_citation(text)

        text = self.__narrator.get_baptised_string()
        if text:
            self.doc.write_text_citation(text)
            
        text = self.__narrator.get_christened_string()
        if text:
            self.doc.write_text_citation(text)

        text = self.__narrator.get_died_string(self.calcageflag)
        if text:
            self.doc.write_text_citation(text)

        text = self.__narrator.get_buried_string()
        if text:
            self.doc.write_text_citation(text)

        if self.verbose:
            self.write_parents(person)

        if not key % 2 or key == 1:
            self.write_marriage(person)
        self.doc.end_paragraph()

        if key == 1:
            self.write_mate(person)

        notelist = person.get_note_list()
        if len(notelist) > 0 and self.includenotes:
            self.doc.start_paragraph("DAR-NoteHeader")
            # feature request 2356: avoid genitive form
            self.doc.write_text(self._("Notes for %s") % name)
            self.doc.end_paragraph()
            for notehandle in notelist:
                note = self.database.get_note_from_handle(notehandle)
                self.doc.write_styled_note(note.get_styledtext(), 
                                           note.get_format(), "DAR-Entry",
                                           contains_html = note.get_type()
                                                        == NoteType.HTML_CODE
                                          )

        first = True
        if self.inc_names:
            for alt_name in person.get_alternate_names():
                if first:
                    self.doc.start_paragraph('DAR-MoreHeader')
                    self.doc.write_text(self._('More about %(person_name)s:')
                                                % {'person_name': name})
                    self.doc.end_paragraph()
                    first = False
                self.doc.start_paragraph('DAR-MoreDetails')
                atype = self.__get_type(alt_name.get_type())
                self.doc.write_text_citation(
                    self._('%(name_kind)s: %(name)s%(endnotes)s') % {
                                'name_kind' : self._(atype),
                                'name' : alt_name.get_regular_name(),
                                'endnotes' : self.endnotes(alt_name),
                                }
                          )
                self.doc.end_paragraph()

        if self.inc_events:
            birth_ref = person.get_birth_ref()
            death_ref = person.get_death_ref()
            for event_ref in person.get_primary_event_ref_list():
                if event_ref == birth_ref or event_ref == death_ref:
                    continue
                
                if first:
                    self.doc.start_paragraph('DAR-MoreHeader')
                    self.doc.write_text(self._('More about %(person_name)s:') % { 
                        'person_name' : self._name_display.display(person) })
                    self.doc.end_paragraph()
                    first = 0
                    
                self.write_event(event_ref)
                
        if self.inc_addr:
            for addr in person.get_address_list():
                if first:
                    self.doc.start_paragraph('DAR-MoreHeader')
                    self.doc.write_text(self._('More about %(person_name)s:') % { 
                        'person_name' : name })
                    self.doc.end_paragraph()
                    first = False
                self.doc.start_paragraph('DAR-MoreDetails')
                
                text = ReportUtils.get_address_str(addr)
                self.doc.write_text(self._('Address: '))

                if self.fulldate:
                    date = self.__get_date(addr.get_date_object())
                else:
                    date = addr.get_date_object().get_year()

                if date:
                    self.doc.write_text( '%s, ' % date )
                self.doc.write_text( text )
                self.doc.write_text_citation( self.endnotes(addr) )
                self.doc.end_paragraph()
                
        if self.inc_attrs:
            attrs = person.get_attribute_list()
            if first and attrs:
                self.doc.start_paragraph('DAR-MoreHeader')
                self.doc.write_text(self._('More about %(person_name)s:') % { 
                    'person_name' : name })
                self.doc.end_paragraph()
                first = False

            for attr in attrs:
                self.doc.start_paragraph('DAR-MoreDetails')
                attrName = self.__get_type(attr.get_type())
                text = self._("%(type)s: %(value)s%(endnotes)s") % {
                    'type'     : self._(attrName),
                    'value'    : attr.get_value(),
                    'endnotes' : self.endnotes(attr) }
                self.doc.write_text_citation( text )
                self.doc.end_paragraph()

        return 0        # Not duplicate person
    
    def write_event(self, event_ref):
        text = ""
        event = self.database.get_event_from_handle(event_ref.ref)

        if self.fulldate:
            date = self.__get_date(event.get_date_object())
        else:
            date = event.get_date_object().get_year()

        ph = event.get_place_handle()
        if ph:
            place = self.database.get_place_from_handle(ph).get_title()
        else:
            place = u''

        self.doc.start_paragraph('DAR-MoreDetails')
        evtName = self.__get_type(event.get_type())
        if date and place:
            text +=  self._('%(date)s, %(place)s') % { 
                       'date' : date, 'place' : place }
        elif date:
            text += self._('%(date)s') % {'date' : date}
        elif place:
            text += self._('%(place)s') % { 'place' : place }

        if event.get_description():
            if text:
                text += ". "
            text += event.get_description()
            
        text += self.endnotes(event)
        
        if text:
            text += ". "
            
        text = self._('%(event_name)s: %(event_text)s') % {
                 'event_name' : self._(evtName),
                 'event_text' : text }
        
        self.doc.write_text_citation(text)
        
        if self.inc_attrs:
            text = ""
            attr_list = event.get_attribute_list()
            attr_list.extend(event_ref.get_attribute_list())
            for attr in attr_list:
                if text:
                    text += "; "
                attrName = self.__get_type(attr.get_type())
                text += self._("%(type)s: %(value)s%(endnotes)s") % {
                    'type'     : self._(attrName),
                    'value'    : attr.get_value(),
                    'endnotes' : self.endnotes(attr) }
            text = " " + text
            self.doc.write_text_citation(text)
        
        self.doc.end_paragraph()

        if self.includenotes:
            # if the event or event reference has a note attached to it,
            # get the text and format it correctly
            notelist = event.get_note_list()
            notelist.extend(event_ref.get_note_list())
            for notehandle in notelist:
                note = self.database.get_note_from_handle(notehandle)
                self.doc.write_styled_note(note.get_styledtext(), 
                                           note.get_format(),"DAR-MoreDetails",
                                           contains_html = (note.get_type()
                                                        == NoteType.HTML_CODE)
                                          )
                
    def write_parents(self, person):
        family_handle = person.get_main_parents_family_handle()
        if family_handle:
            family = self.database.get_family_from_handle(family_handle)
            mother_handle = family.get_mother_handle()
            father_handle = family.get_father_handle()
            if mother_handle:
                mother = self.database.get_person_from_handle(mother_handle)
                mother_name = \
                    self._name_display.display_name(mother.get_primary_name())
                mother_mark = ReportUtils.get_person_mark(self.database, mother)
            else:
                mother_name = ""
                mother_mark = ""
            if father_handle:
                father = self.database.get_person_from_handle(father_handle)
                father_name = \
                    self._name_display.display_name(father.get_primary_name())
                father_mark = ReportUtils.get_person_mark(self.database, father)
            else:
                father_name = ""
                father_mark = ""

            text = self.__narrator.get_child_string(father_name, mother_name)
            if text:
                self.doc.write_text(text)
                if father_mark:
                    self.doc.write_text("", father_mark)
                if mother_mark:
                    self.doc.write_text("", mother_mark)

    def write_marriage(self, person):
        """ 
        Output marriage sentence.
        """
        is_first = True
        for family_handle in person.get_family_handle_list():
            family = self.database.get_family_from_handle(family_handle)
            spouse_handle = ReportUtils.find_spouse(person,family)
            spouse = self.database.get_person_from_handle(spouse_handle)
            if spouse:
                name = self._name_display.display_formal(spouse)
            else:
                name = ""
            text = ""
            spouse_mark = ReportUtils.get_person_mark(self.database, spouse)
            
            text = self.__narrator.get_married_string(family, is_first, self._name_display)

            if text:
                self.doc.write_text_citation(text, spouse_mark)
                is_first = False

    def write_children(self, family):
        """ List children.
        """

        if not family.get_child_ref_list():
            return

        mother_handle = family.get_mother_handle()
        if mother_handle:
            mother = self.database.get_person_from_handle(mother_handle)
            mother_name = self._name_display.display(mother)
        else:
            mother_name = self._("unknown")

        father_handle = family.get_father_handle()
        if father_handle:
            father = self.database.get_person_from_handle(father_handle)
            father_name = self._name_display.display(father)
        else:
            father_name = self._("unknown")

        self.doc.start_paragraph("DAR-ChildTitle")
        self.doc.write_text(
                        self._("Children of %(mother_name)s and %(father_name)s") % 
                            {'father_name': father_name,
                             'mother_name': mother_name} )
        self.doc.end_paragraph()

        cnt = 1
        for child_ref in family.get_child_ref_list():
            child_handle = child_ref.ref
            child = self.database.get_person_from_handle(child_handle)
            child_name = self._name_display.display(child)
            child_mark = ReportUtils.get_person_mark(self.database, child)

            if self.childref and self.prev_gen_handles.get(child_handle):
                value = str(self.prev_gen_handles.get(child_handle))
                child_name += " [%s]" % value

            self.doc.start_paragraph("DAR-ChildList",
                                     ReportUtils.roman(cnt).lower() + ".")
            cnt += 1

            self.__narrator.set_subject(child)
            self.doc.write_text("%s. " % child_name, child_mark)
            self.doc.write_text_citation(self.__narrator.get_born_string() or
                                self.__narrator.get_christened_string() or
                                self.__narrator.get_baptised_string())
            self.doc.write_text_citation(self.__narrator.get_died_string() or
                                self.__narrator.get_buried_string())
            self.doc.end_paragraph()

    def write_family_events(self, family):
        
        if not family.get_event_ref_list():
            return

        mother_handle = family.get_mother_handle()
        if mother_handle:
            mother = self.database.get_person_from_handle(mother_handle)
            mother_name = self._name_display.display(mother)
        else:
            mother_name = self._("unknown")

        father_handle = family.get_father_handle()
        if father_handle:
            father = self.database.get_person_from_handle(father_handle)
            father_name = self._name_display.display(father)
        else:
            father_name = self._("unknown")

        first = 1
        for event_ref in family.get_event_ref_list():
            if first:
                self.doc.start_paragraph('DAR-MoreHeader')
                self.doc.write_text(
                    self._('More about %(mother_name)s and %(father_name)s:') % { 
                    'mother_name' : mother_name,
                    'father_name' : father_name })
                self.doc.end_paragraph()
                first = 0
            self.write_event(event_ref)

    def write_mate(self, person):
        """Output birth, death, parentage, marriage and notes information """
        ind = None
        has_info = False
        
        for family_handle in person.get_family_handle_list():
            family = self.database.get_family_from_handle(family_handle)
            ind_handle = None
            if person.get_gender() == Person.MALE:
                ind_handle = family.get_mother_handle()
            else:
                ind_handle = family.get_father_handle()
            if ind_handle:
                ind = self.database.get_person_from_handle(ind_handle)
                for event_ref in ind.get_primary_event_ref_list():
                    event = self.database.get_event_from_handle(event_ref.ref)
                    if event:
                        etype = event.get_type()
                        if (etype == EventType.BAPTISM or
                            etype == EventType.BURIAL or
                            etype == EventType.BIRTH  or
                            etype == EventType.DEATH):
                                has_info = True
                                break   
                if not has_info:
                    family_handle = ind.get_main_parents_family_handle()
                    if family_handle:
                        f = self.database.get_family_from_handle(family_handle)
                        if f.get_mother_handle() or f.get_father_handle():
                            has_info = True
                            break

            if has_info:
                self.doc.start_paragraph("DAR-MoreHeader")

                plist = ind.get_media_list()
                
                if self.addimages and len(plist) > 0:
                    photo = plist[0]
                    ReportUtils.insert_image(self.database, self.doc, 
                                             photo, self._user)
        
                name = self._name_display.display_formal(ind)
                mark = ReportUtils.get_person_mark(self.database, ind)
        
                if family.get_relationship() == FamilyRelType.MARRIED:
                    self.doc.write_text(self._("Spouse: %s") % name, mark)
                else:
                    self.doc.write_text(self._("Relationship with: %s") % name, mark)
                if name[-1:] != '.':
                    self.doc.write_text(".")
                self.doc.write_text_citation(self.endnotes(ind))
                self.doc.end_paragraph()

                self.doc.start_paragraph("DAR-Entry")

                self.__narrator.set_subject(ind)

                text = self.__narrator.get_born_string()
                if text:
                    self.doc.write_text_citation(text)

                text = self.__narrator.get_baptised_string()
                if text:
                    self.doc.write_text_citation(text)

                text = self.__narrator.get_christened_string()
                if text:
                    self.doc.write_text_citation(text)

                text = self.__narrator.get_died_string(self.calcageflag)
                if text:
                    self.doc.write_text_citation(text)
                
                text = self.__narrator.get_buried_string()
                if text:
                    self.doc.write_text_citation(text)

                self.write_parents(ind)

                self.doc.end_paragraph()

    def endnotes(self, obj):
        if not obj or not self.inc_sources:
            return ""
        
        txt = endnotes.cite_source(self.bibli, self.database, obj)
        if txt:
            txt = '<super>' + txt + '</super>'
        return txt

#------------------------------------------------------------------------
#
# DetAncestorOptions
#
#------------------------------------------------------------------------
class DetAncestorOptions(MenuReportOptions):

    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, dbase):
        MenuReportOptions.__init__(self, name, dbase)
        
    def add_menu_options(self, menu):
        from functools import partial

        # Report Options

        addopt = partial(menu.add_option, _("Report Options"))
        
        pid = PersonOption(_("Center Person"))
        pid.set_help(_("The center person for the report"))
        addopt("pid", pid)

        # We must figure out the value of the first option before we can
        # create the EnumeratedListOption
        fmt_list = global_name_display.get_name_format()
        name_format = EnumeratedListOption(_("Name format"), 0)
        name_format.add_item(0, _("Default"))
        for num, name, fmt_str, act in fmt_list:
            name_format.add_item(num, name)
        name_format.set_help(_("Select the format to display names"))
        addopt("name_format", name_format)
        
        gen = NumberOption(_("Generations"),10,1,100)
        gen.set_help(_("The number of generations to include in the report"))
        addopt("gen", gen)
        
        pagebbg = BooleanOption(_("Page break between generations"),False)
        pagebbg.set_help(
                     _("Whether to start a new page after each generation."))
        addopt("pagebbg", pagebbg)

        pageben = BooleanOption(_("Page break before end notes"),False)
        pageben.set_help(
                     _("Whether to start a new page before the end notes."))
        addopt("pageben", pageben)
        
        trans = EnumeratedListOption(_("Translation"),
                                      Translator.DEFAULT_TRANSLATION_STR)
        trans.add_item(Translator.DEFAULT_TRANSLATION_STR, _("Default"))
        for language in get_available_translations():
            trans.add_item(language, get_language_string(language))
        trans.set_help(_("The translation to be used for the report."))
        addopt("trans", trans)

        # Content options

        addopt = partial(menu.add_option, _("Content"))

        usecall = BooleanOption(_("Use callname for common name"),False)
        usecall.set_help(_("Whether to use the call name as the first name."))
        addopt("usecall", usecall)
        
        fulldates = BooleanOption(
                              _("Use full dates instead of only the year"),True)
        fulldates.set_help(_("Whether to use full dates instead of just year."))
        addopt("fulldates", fulldates)
        
        listc = BooleanOption(_("List children"),True)
        listc.set_help(_("Whether to list children."))
        addopt("listc", listc)
        
        computeage = BooleanOption(_("Compute death age"),True)
        computeage.set_help(_("Whether to compute a person's age at death."))
        addopt("computeage", computeage)
        
        omitda = BooleanOption(_("Omit duplicate ancestors"),True)
        omitda.set_help(_("Whether to omit duplicate ancestors."))
        addopt("omitda", omitda)
        
        verbose = BooleanOption(_("Use Complete Sentences"),True)
        verbose.set_help(
                 _("Whether to use complete sentences or succinct language."))
        addopt("verbose", verbose)

        desref = BooleanOption(_("Add descendant reference in child list"),True)
        desref.set_help(
                    _("Whether to add descendant references in child list."))
        addopt("desref", desref)

        # What to include

        addopt = partial(menu.add_option, _("Include"))
        
        incnotes = BooleanOption(_("Include notes"),True)
        incnotes.set_help(_("Whether to include notes."))
        addopt("incnotes", incnotes)

        incattrs = BooleanOption(_("Include attributes"),False)
        incattrs.set_help(_("Whether to include attributes."))
        addopt("incattrs", incattrs)
        
        incphotos = BooleanOption(_("Include Photo/Images from Gallery"),False)
        incphotos.set_help(_("Whether to include images."))
        addopt("incphotos", incphotos)

        incnames = BooleanOption(_("Include alternative names"),False)
        incnames.set_help(_("Whether to include other names."))
        addopt("incnames", incnames)

        incevents = BooleanOption(_("Include events"),False)
        incevents.set_help(_("Whether to include events."))
        addopt("incevents", incevents)

        incaddresses = BooleanOption(_("Include addresses"),False)
        incaddresses.set_help(_("Whether to include addresses."))
        addopt("incaddresses", incaddresses)

        incsources = BooleanOption(_("Include sources"),False)
        incsources.set_help(_("Whether to include source references."))
        addopt("incsources", incsources)

        incsrcnotes = BooleanOption(_("Include sources notes"), False)
        incsrcnotes.set_help(_("Whether to include source notes in the "
            "Endnotes section. Only works if Include sources is selected."))
        addopt("incsrcnotes", incsrcnotes)

        # How to handle missing information

        addopt = partial(menu.add_option, _("Missing information"))

        repplace = BooleanOption(_("Replace missing places with ______"),False)
        repplace.set_help(_("Whether to replace missing Places with blanks."))
        addopt("repplace", repplace)

        repdate = BooleanOption(_("Replace missing dates with ______"),False)
        repdate.set_help(_("Whether to replace missing Dates with blanks."))
        addopt("repdate", repdate)

    def make_default_style(self,default_style):
        """Make the default output style for the Detailed Ancestral Report"""
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF,size=16,bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(1)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_alignment(PARA_ALIGN_CENTER)
        para.set_description(_('The style used for the title of the page.'))
        default_style.add_paragraph_style("DAR-Title",para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF,size=14,italic=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(2)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the generation header.'))
        default_style.add_paragraph_style("DAR-Generation",para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF,size=10,italic=0, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_left_margin(1.0)   # in centimeters
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the children list title.'))
        default_style.add_paragraph_style("DAR-ChildTitle",para)

        font = FontStyle()
        font.set(size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=-0.75,lmargin=1.75)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the children list.'))
        default_style.add_paragraph_style("DAR-ChildList",para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF,size=10,italic=0, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0,lmargin=1.0)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        default_style.add_paragraph_style("DAR-NoteHeader",para)

        para = ParagraphStyle()
        para.set(lmargin=1.0)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The basic style used for the text display.'))
        default_style.add_paragraph_style("DAR-Entry",para)

        para = ParagraphStyle()
        para.set(first_indent=-1.0,lmargin=1.0)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the first personal entry.'))
        default_style.add_paragraph_style("DAR-First-Entry",para)

        font = FontStyle()
        font.set(size=10,face=FONT_SANS_SERIF,bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0,lmargin=1.0)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the More About header.'))
        default_style.add_paragraph_style("DAR-MoreHeader",para)

        font = FontStyle()
        font.set(face=FONT_SERIF,size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0,lmargin=1.0)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for additional detail data.'))
        default_style.add_paragraph_style("DAR-MoreDetails",para)

        endnotes.add_endnote_styles(default_style)
