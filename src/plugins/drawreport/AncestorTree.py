#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2007-2008  Brian G. Matherly
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

"""Reports/Graphical Reports/Ancestor Tree"""

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
import math
from gen.ggettext import sgettext as _
#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gen.display.name import displayer as name_displayer
from Errors import ReportError
from gen.plug.docgen import (FontStyle, ParagraphStyle, GraphicsStyle,
                            FONT_SANS_SERIF, PARA_ALIGN_CENTER)
from gen.plug.menu import BooleanOption, NumberOption, TextOption, PersonOption
from gen.plug.report import Report
from gen.plug.report import utils as ReportUtils
from gui.plug.report import MenuReportOptions
from libsubstkeyword import SubstKeywords

pt2cm = ReportUtils.pt2cm

#------------------------------------------------------------------------
#
# Constants
#
#------------------------------------------------------------------------
_BORN = _('short for born|b.')
_DIED = _('short for died|d.')

#------------------------------------------------------------------------
#
# log2val
#
#------------------------------------------------------------------------
def log2(val):
    """
    Calculate the log base 2 of a value.
    """
    return int(math.log10(val)/math.log10(2))

#------------------------------------------------------------------------
#
# Layout class
#
#------------------------------------------------------------------------
class GenChart(object):

    def __init__(self, generations):
        self.generations = generations
        self.size = (2**(generations))
        self.array = {}
        self.map = {}
        self.compress_map = {}

        self.max_x = 0
        self.ad = (self.size, generations)

    def set(self, index, value):
        x = log2(index)
        y = index - (2**x)
        delta = int((self.size/(2**(x))))
        new_y = int((delta/2) + (y)*delta)
        if not new_y in self.array:
            self.array[new_y] = {}
        self.array[new_y][x] = (value, index)
        self.max_x = max(x, self.max_x)
        self.map[value] = (new_y, x)

    def index_to_xy(self, index):
        if index:
            x = log2(index)
            ty = index - (2**x)
            delta = int(self.size/(2**x))
            y = int(delta/2 + ty*delta)
        else:
            x = 0
            y = self.size/2
        
        if len(self.compress_map) > 0:
            return (x, self.compress_map[y])
        else:
            return (x, y)
    
    def get(self, index):
        (x,y) = self.index_to_xy(index)
        return self.get_xy(x, y)

    def get_xy(self, x, y):
        value = 0
        if y in self.array:
            if x in self.array[y]:
                value = self.array[y][x]
        return value

    def set_xy(self, x, y, value):
        if not y in self.array:
            self.array[y] = {}
        self.array[y][x] = value

    def dimensions(self):
        return (max(self.array)+1, self.max_x+1)

    def compress(self):
        new_map = {}
        new_array = {}
        old_y = 0
        new_y = 0
        for key, i in self.array.iteritems():
            old_y = key
            if self.not_blank(i.itervalues()):
                self.compress_map[old_y] = new_y
                new_array[new_y] = i
                x = 0
                for entry in i:
                    new_map[entry] = (new_y, x)
                    x += 1
                new_y += 1
        self.array = new_array
        self.map = new_map
        self.ad = (new_y, self.ad[1])

    def not_blank(self, line):
        for i in line:
            if i and isinstance(i, tuple):
                return 1
        return 0

#------------------------------------------------------------------------
#
# AncestorTree
#
#------------------------------------------------------------------------
class AncestorTree(Report):

    def __init__(self, database, options_class):
        """
        Create AncestorTree object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        person          - currently selected person
        options_class   - instance of the Options class for this report

        This report needs the following parameters (class variables)
        that come in the options class.
        
        gen       - Maximum number of generations to include.
        pagebbg   - Whether to include page breaks between generations.
        dispf     - Display format for the output box.
        singlep   - Whether to scale to fit on a single page.
        indblank  - Whether to include blank pages.
        compress  - Whether to compress chart.
        """
        Report.__init__(self, database, options_class)
        
        menu = options_class.menu
        self.display = menu.get_option_by_name('dispf').get_value()
        self.max_generations = menu.get_option_by_name('maxgen').get_value()
        self.force_fit = menu.get_option_by_name('singlep').get_value()
        self.incblank = menu.get_option_by_name('incblank').get_value()
        self.compress = menu.get_option_by_name('compress').get_value()
        
        pid = menu.get_option_by_name('pid').get_value()
        center_person = database.get_person_from_gramps_id(pid)
        if (center_person == None) :
            raise ReportError(_("Person %s is not in the Database") % pid )
        
        name = name_displayer.display_formal(center_person)
        self.title = _("Ancestor Graph for %s") % name

        self.map = {}
        self.text = {}

        self.box_width = 0
        self.box_height = 0
        self.lines = 0
        self.scale = 1

        self.apply_filter(center_person.get_handle(), 1)
        keys = sorted(self.map)
        max_key = log2(keys[-1])

        self.genchart = GenChart(max_key+1)
        for key, chart in self.map.iteritems():
            self.genchart.set(key, chart)
        self.calc()
        
        if self.force_fit:
            self.scale_styles()

    def apply_filter(self, person_handle, index):
        """traverse the ancestors recursively until either the end
        of a line is found, or until we reach the maximum number of 
        generations that we want to deal with"""

        if (not person_handle) or (index >= 2**self.max_generations):
            return
        self.map[index] = person_handle

        self.text[index] = []
        
        style_sheet = self.doc.get_style_sheet()
        pstyle = style_sheet.get_paragraph_style("AC2-Normal")
        font = pstyle.get_font()

        em = self.doc.string_width(font,"m")

        subst = SubstKeywords(self.database, person_handle)
        self.text[index] = subst.replace_and_clean(self.display)

        for line in self.text[index]:
            this_box_width = self.doc.string_width(font,line) + (2 * em)
            self.box_width = max(self.box_width, this_box_width)

        self.lines = max(self.lines, len(self.text[index]))    

        person = self.database.get_person_from_handle(person_handle)
        family_handle = person.get_main_parents_family_handle()
        if family_handle:
            family = self.database.get_family_from_handle(family_handle)
            self.apply_filter(family.get_father_handle(), index*2)
            self.apply_filter(family.get_mother_handle(), (index*2)+1)

    def write_report(self):

        (maxy, maxx) = self.genchart.dimensions()
        maxh = int(self.uh/self.box_height)
        
        if self.force_fit:
            self.print_page(0, maxx, 0, maxy, 0, 0)
        else:
            starty = 0
            coly = 0
            while starty < maxy:
                startx = 0
                colx = 0
                while startx < maxx:
                    stopx = min(maxx, startx + self.generations_per_page)
                    stopy = min(maxy, starty + maxh)
                    self.print_page(startx, stopx, starty, stopy, colx, coly)
                    colx += 1
                    startx += self.generations_per_page
                coly += 1
                starty += maxh
            
    def calc(self):
        """
        calc - calculate the maximum width that a box needs to be. From
        that and the page dimensions, calculate the proper place to put
        the elements on a page.
        """
        style_sheet = self.doc.get_style_sheet()

        self.add_lines()
        if self.compress:
            self.genchart.compress()

        self.box_pad_pts = 10
        if self.title and self.force_fit:
            pstyle = style_sheet.get_paragraph_style("AC2-Title")
            tfont = pstyle.get_font()
            self.offset = pt2cm(1.25 * tfont.get_size())
            
            gstyle = style_sheet.get_draw_style("AC2-box")
            shadow_height = gstyle.get_shadow_space()
        else:
            # Make space for the page number labels at the bottom.
            p = style_sheet.get_paragraph_style("AC2-Normal")
            font = p.get_font()
            lheight = pt2cm(1.2*font.get_size())
            lwidth = pt2cm(1.1*self.doc.string_width(font, "(00,00)"))
            self.page_label_x_offset = self.doc.get_usable_width()  - lwidth
            self.page_label_y_offset = self.doc.get_usable_height() - lheight

            self.offset = pt2cm(1.25 * font.get_size())
            shadow_height = 0
        self.uh = self.doc.get_usable_height() - self.offset - shadow_height
        uw = self.doc.get_usable_width() - pt2cm(self.box_pad_pts)

        calc_width = pt2cm(self.box_width + self.box_pad_pts) + 0.2 
        self.box_width = pt2cm(self.box_width)
        pstyle = style_sheet.get_paragraph_style("AC2-Normal")
        font = pstyle.get_font()
        self.box_height = self.lines*pt2cm(1.25*font.get_size())

        if self.force_fit:
            (maxy, maxx) = self.genchart.dimensions()

            bw = calc_width / (uw/maxx)
            bh = self.box_height / (self.uh/maxy)

            self.scale = max(bw ,bh)
            self.box_width /= self.scale
            self.box_height /= self.scale
            self.box_pad_pts /= self.scale

        maxh = int(self.uh / self.box_height)
        maxw = int(uw / calc_width) 

        if log2(maxh) < maxw:
            self.generations_per_page = int(log2(maxh))
        else:
            self.generations_per_page = maxw

        # build array of x indices

        self.delta = pt2cm(self.box_pad_pts) + self.box_width + 0.2
        if not self.force_fit:
            calc_width = self.box_width + 0.2 + pt2cm(self.box_pad_pts)
            remain = self.doc.get_usable_width() -                             \
                     ((self.generations_per_page)*calc_width)
            self.delta += remain / (self.generations_per_page)
            
    def scale_styles(self):
        """
        Scale the styles for this report. This must be done in the constructor.
        """
        style_sheet = self.doc.get_style_sheet()
        
        g = style_sheet.get_draw_style("AC2-box")
        g.set_shadow(g.get_shadow(), g.get_shadow_space() / self.scale)
        g.set_line_width(g.get_line_width() / self.scale)
        style_sheet.add_draw_style("AC2-box", g)

        p = style_sheet.get_paragraph_style("AC2-Normal")
        font = p.get_font()
        font.set_size(font.get_size() / self.scale)
        p.set_font(font)
        style_sheet.add_paragraph_style("AC2-Normal", p)
            
        self.doc.set_style_sheet(style_sheet)

    def print_page(self, startx, stopx, starty, stopy, colx, coly):
        
        if not self.incblank:
            blank = True
            for y in range(starty, stopy):
                for x in range(startx, stopx):
                    if self.genchart.get_xy(x, y) != 0:
                        blank = False
                        break
                if not blank: 
                    break
            if blank: 
                return

        self.doc.start_page()
        if self.title and self.force_fit:
            self.doc.center_text('AC2-title', self.title, 
                                 self.doc.get_usable_width() / 2, 0)
        phys_y = 0
        for y in range(starty, stopy):
            phys_x = 0
            for x in range(startx, stopx):
                value = self.genchart.get_xy(x, y)
                if value:
                    if isinstance(value, tuple):
                        (person, index) = value
                        text = '\n'.join(self.text[index])
                        self.doc.draw_box("AC2-box",
                                          text,
                                          phys_x*self.delta,
                                          phys_y*self.box_height+self.offset,
                                          self.box_width,
                                          self.box_height )
                    elif value == 2:
                        self.doc.draw_line("AC2-line",
                                           phys_x * self.delta+self.box_width * 0.5,
                                           phys_y * self.box_height + self.offset,
                                           phys_x * self.delta+self.box_width * 0.5,
                                           (phys_y + 1) * self.box_height + self.offset)
                    elif value == 1:
                        x1 = phys_x * self.delta + self.box_width * 0.5
                        x2 = (phys_x + 1) * self.delta
                        y1 = phys_y * self.box_height + self.offset + self.box_height / 2
                        y2 = (phys_y + 1) * self.box_height + self.offset
                        self.doc.draw_line("AC2-line", x1, y1, x1, y2)
                        self.doc.draw_line("AC2-line", x1, y1, x2, y1)
                    elif value == 3:
                        x1 = phys_x * self.delta + self.box_width * 0.5
                        x2 = (phys_x + 1) * self.delta
                        y1 = (phys_y) * self.box_height + self.offset + self.box_height / 2
                        y2 = (phys_y) * self.box_height + self.offset
                        self.doc.draw_line("AC2-line", x1, y1, x1, y2)
                        self.doc.draw_line("AC2-line", x1, y1, x2, y1)
                        
                phys_x +=1
            phys_y += 1
                    
        if not self.force_fit:
            self.doc.draw_text('AC2-box',
                               '(%d,%d)' % (colx + 1, coly + 1),
                               self.page_label_x_offset,
                               self.page_label_y_offset)
        self.doc.end_page()

    def add_lines(self):

        (my , mx) = self.genchart.dimensions()
        
        for y in range(0, my):
            for x in range(0, mx):
                value = self.genchart.get_xy(x, y)
                if not value:
                    continue
                if isinstance(value, tuple):
                    (person, index) = value
                    if self.genchart.get(index * 2):
                        (px, py) = self.genchart.index_to_xy(index * 2)
                        self.genchart.set_xy(x, py, 1)
                        for ty in range(py + 1, y):
                            self.genchart.set_xy(x, ty, 2)
                    if self.genchart.get(index * 2 + 1):
                        (px, py) = self.genchart.index_to_xy(index * 2 + 1)
                        self.genchart.set_xy(px - 1, py, 3)
                        for ty in range(y + 1, py):
                            self.genchart.set_xy(x, ty, 2)

#------------------------------------------------------------------------
#
# AncestorTreeOptions
#
#------------------------------------------------------------------------
class AncestorTreeOptions(MenuReportOptions):

    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, dbase):
        MenuReportOptions.__init__(self, name, dbase)
        
    def add_menu_options(self, menu):
        
        category_name = _("Tree Options")

        pid = PersonOption(_("Center Person"))
        pid.set_help(_("The center person for the tree"))
        menu.add_option(category_name, "pid", pid)
        
        max_gen = NumberOption(_("Generations"), 10, 1, 50)
        max_gen.set_help(_("The number of generations to include in the tree"))
        menu.add_option(category_name, "maxgen", max_gen)
        
        disp = TextOption(_("Display Format"), 
                           ["$n","%s $b" % _BORN,"%s $d" %_DIED] )
        disp.set_help(_("Display format for the outputbox."))
        menu.add_option(category_name, "dispf", disp)
        
        scale = BooleanOption(_('Sc_ale to fit on a single page'), True)
        scale.set_help(_("Whether to scale to fit on a single page."))
        menu.add_option(category_name, "singlep", scale)
        
        blank = BooleanOption(_('Include Blank Pages'), True)
        blank.set_help(_("Whether to include pages that are blank."))
        menu.add_option(category_name, "incblank", blank)
        
        compress = BooleanOption(_('Co_mpress tree'), True)
        compress.set_help(_("Whether to compress the tree."))
        menu.add_option(category_name, "compress", compress)

    def make_default_style(self, default_style):
        """Make the default output style for the Ancestor Tree."""
        
        ## Paragraph Styles:
        f = FontStyle()
        f.set_size(9)
        f.set_type_face(FONT_SANS_SERIF)
        p = ParagraphStyle()
        p.set_font(f)
        p.set_description(_('The basic style used for the text display.'))
        default_style.add_paragraph_style("AC2-Normal", p)

        f = FontStyle()
        f.set_size(16)
        f.set_type_face(FONT_SANS_SERIF)
        p = ParagraphStyle()
        p.set_font(f)
        p.set_alignment(PARA_ALIGN_CENTER)
        p.set_description(_('The basic style used for the title display.'))
        default_style.add_paragraph_style("AC2-Title", p)
        
        ## Draw styles
        g = GraphicsStyle()
        g.set_paragraph_style("AC2-Normal")
        g.set_shadow(1, 0.2)
        g.set_fill_color((255, 255, 255))
        default_style.add_draw_style("AC2-box", g)

        g = GraphicsStyle()
        g.set_paragraph_style("AC2-Title")
        g.set_color((0, 0, 0))
        g.set_fill_color((255, 255, 255))
        g.set_line_width(0)
        default_style.add_draw_style("AC2-title", g)

        g = GraphicsStyle()
        default_style.add_draw_style("AC2-line", g)
