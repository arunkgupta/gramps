#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2002       Gary Shao
# Copyright (C) 2007       Brian G. Matherly
# Copyright (C) 2009       Benny Malengier
# Copyright (C) 2009       Gary Burton
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
Provide base interface to text based documents. Specific document
interfaces should be derived from the core classes.
"""

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
import os
from xml.sax.saxutils import escape

def escxml(string):
    """
    Escapes XML special characters.
    """
    return escape(string, { '"' : '&quot;' } )

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import Utils
import FontScale
import const

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".BaseDoc")

#-------------------------------------------------------------------------
#
# SAX interface
#
#-------------------------------------------------------------------------
try:
    from xml.sax import make_parser, handler, SAXParseException
except ImportError:
    from _xmlplus.sax import make_parser, handler, SAXParseException

#-------------------------------------------------------------------------
#
# constants
#
#-------------------------------------------------------------------------
FONT_SANS_SERIF = 0
FONT_SERIF      = 1
FONT_MONOSPACE  = 2

#-------------------------------------------------------------------------
#
# Page orientation
#
#-------------------------------------------------------------------------
PAPER_PORTRAIT  = 0
PAPER_LANDSCAPE = 1

#-------------------------------------------------------------------------
#
# Paragraph alignment
#
#-------------------------------------------------------------------------
PARA_ALIGN_CENTER  = 0
PARA_ALIGN_LEFT    = 1 
PARA_ALIGN_RIGHT   = 2
PARA_ALIGN_JUSTIFY = 3

#-------------------------------------------------------------------------
#
# Text vs. Graphics mode
#
#-------------------------------------------------------------------------
TEXT_MODE     = 0
GRAPHICS_MODE = 1

#-------------------------------------------------------------------------
#
# Line style
#
#-------------------------------------------------------------------------
SOLID  = 0
DASHED = 1

#-------------------------------------------------------------------------
#
# IndexMark types
#
#-------------------------------------------------------------------------
INDEX_TYPE_ALP = 0
INDEX_TYPE_TOC = 1

#------------------------------------------------------------------------
#
# cnv2color
#
#------------------------------------------------------------------------
def cnv2color(text):
    """
    converts a hex value in the form of #XXXXXX into a tuple of integers
    representing the RGB values
    """
    return (int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16))

#------------------------------------------------------------------------
#
# PaperSize
#
#------------------------------------------------------------------------
class PaperSize(object):
    """
    Defines the dimensions of a sheet of paper. All dimensions are in
    centimeters.
    """
    def __init__(self, name, height, width):
        """
        Create a new paper style with.

        @param name: name of the new style
        @param height: page height in centimeters
        @param width: page width in centimeters
        """
        self.name = name
        self.height = height
        self.width = width

    def get_name(self):
        "Return the name of the paper style"
        return self.name

    def get_height(self):
        "Return the page height in cm"
        return self.height

    def set_height(self, height):
        "Set the page height in cm"
        self.height = height

    def get_width(self):
        "Return the page width in cm"
        return self.width

    def set_width(self, width):
        "Set the page width in cm"
        self.width = width

    def get_height_inches(self):
        "Return the page height in inches"
        return self.height / 2.54

    def get_width_inches(self):
        "Return the page width in inches"
        return self.width / 2.54

#------------------------------------------------------------------------
#
# PaperStyle
#
#------------------------------------------------------------------------
class PaperStyle(object):
    """
    Define the various options for a sheet of paper.
    """
    def __init__(self, size, orientation,
                 lmargin=2.54, rmargin=2.54, tmargin=2.54, bmargin=2.54):
        """
        Create a new paper style.

        @param size: size of the new style
        @type size: PaperSize
        @param orientation: page orientation
        @type orientation: PAPER_PORTRAIT or PAPER_LANDSCAPE

        """
        self.__orientation = orientation

        if orientation == PAPER_PORTRAIT:
            self.__size = PaperSize(size.get_name(),
                                    size.get_height(),
                                    size.get_width())
        else:
            self.__size = PaperSize(size.get_name(),
                                    size.get_width(),
                                    size.get_height())
        self.__lmargin = lmargin
        self.__rmargin = rmargin
        self.__tmargin = tmargin
        self.__bmargin = bmargin
        
    def get_size(self):
        """
        Return the size of the paper.

        @returns: object indicating the paper size
        @rtype: PaperSize
        
        """
        return self.__size
        
    def get_orientation(self):
        """
        Return the orientation of the page.

        @returns: PAPER_PORTRIAT or PAPER_LANDSCAPE
        @rtype: int
        
        """
        return self.__orientation
        
    def get_usable_width(self):
        """
        Return the width of the page area in centimeters.
        
        The value is the page width less the margins.
        
        """
        return self.__size.get_width() - (self.__rmargin + self.__lmargin)

    def get_usable_height(self):
        """
        Return the height of the page area in centimeters.
        
        The value is the page height less the margins.
        
        """
        return self.__size.get_height() - (self.__tmargin + self.__bmargin)

    def get_right_margin(self):
        """
        Return the right margin.

        @returns: Right margin in centimeters
        @rtype: float
        
        """
        return self.__rmargin

    def get_left_margin(self):
        """
        Return the left margin.

        @returns: Left margin in centimeters
        @rtype: float
        
        """
        return self.__lmargin

    def get_top_margin(self):
        """
        Return the top margin.

        @returns: Top margin in centimeters
        @rtype: float
        
        """
        return self.__tmargin

    def get_bottom_margin(self):
        """
        Return the bottom margin.

        @returns: Bottom margin in centimeters
        @rtype: float
        
        """
        return self.__bmargin

#------------------------------------------------------------------------
#
# FontStyle
#
#------------------------------------------------------------------------
class FontStyle(object):
    """
    Defines a font style. Controls the font face, size, color, and
    attributes. In order to remain generic, the only font faces available
    are FONT_SERIF and FONT_SANS_SERIF. Document formatters should convert
    these to the appropriate fonts for the target format.

    The FontStyle represents the desired characteristics. There are no
    guarentees that the document format generator will be able implement
    all or any of the characteristics.
    """
    
    def __init__(self, style=None):
        """
        Create a new FontStyle object, accepting the default values.

        @param style: if specified, initializes the FontStyle from the passed
            FontStyle instead of using the defaults.
        """
        if style:
            self.face   = style.face
            self.size   = style.size
            self.italic = style.italic
            self.bold   = style.bold
            self.color  = style.color
            self.under  = style.under
        else:
            self.face   = FONT_SERIF
            self.size   = 12
            self.italic = 0
            self.bold   = 0
            self.color  = (0, 0, 0)
            self.under  = 0
            
    def set(self, face=None, size=None, italic=None, bold=None,
            underline=None, color=None):
        """
        Set font characteristics.

        @param face: font type face, either FONT_SERIF or FONT_SANS_SERIF
        @param size: type face size in points
        @param italic: True enables italics, False disables italics
        @param bold: True enables bold face, False disables bold face
        @param underline: True enables underline, False disables underline
        @param color: an RGB color representation in the form of three integers
            in the range of 0-255 represeting the red, green, and blue
            components of a color.
        """
        if face is not None:
            self.set_type_face(face)
        if size is not None:
            self.set_size(size)
        if italic is not None:
            self.set_italic(italic)
        if bold is not None:
            self.set_bold(bold)
        if underline is not None:
            self.set_underline(underline)
        if color is not None:
            self.set_color(color)

    def set_italic(self, val):
        "0 disables italics, 1 enables italics"
        self.italic = val

    def get_italic(self):
        "1 indicates use italics"
        return self.italic

    def set_bold(self, val):
        "0 disables bold face, 1 enables bold face"
        self.bold = val

    def get_bold(self):
        "1 indicates use bold face"
        return self.bold

    def set_color(self, val):
        "sets the color using an RGB color tuple"
        self.color = val

    def get_color(self):
        "Return an RGB color tuple"
        return self.color

    def set_size(self, val):
        "sets font size in points"
        self.size = val

    def get_size(self):
        "returns font size in points"
        return self.size

    def set_type_face(self, val):
        "sets the font face type"
        self.face = val

    def get_type_face(self):
        "returns the font face type"
        return self.face

    def set_underline(self, val):
        "1 enables underlining"
        self.under = val

    def get_underline(self):
        "1 indicates underlining"
        return self.under

#------------------------------------------------------------------------
#
# TableStyle
#
#------------------------------------------------------------------------
class TableStyle(object):
    """
    Specifies the style or format of a table. The TableStyle contains the
    characteristics of table width (in percentage of the full width), the
    number of columns, and the width of each column as a percentage of the
    width of the table.
    """
    def __init__(self, obj=None):
        """
        Create a new TableStyle object, with the values initialized to
        empty, with allocating space for up to 100 columns.

        @param obj: if not None, then the object created gets is attributes
            from the passed object instead of being initialized to empty.
        """
        if obj:
            self.width = obj.width
            self.columns = obj.columns
            self.colwid  = obj.colwid[:]
        else:
            self.width = 0
            self.columns = 0
            self.colwid = [ 0 ] * 100

    def set_width(self, width):
        """
        Set the width of the table in terms of percent of the available
        width
        """
        self.width = width

    def get_width(self):
        """
        Return the specified width as a percentage of the available space
        """
        return self.width

    def set_columns(self, columns):
        """
        Set the number of columns.

        @param columns: number of columns that should be used.
        """
        self.columns = columns

    def get_columns(self):
        """
        Return the number of columns
        """
        return self.columns 

    def set_column_widths(self, clist):
        """
        Set the width of all the columns at once, taking the percentages
        from the passed list.
        """
        self.columns = len(clist)
        for i in range(self.columns):
            self.colwid[i] = clist[i]

    def set_column_width(self, index, width):
        """
        Set the width of a specified column to the specified width.

        @param index: column being set (index starts at 0)
        @param width: percentage of the table width assigned to the column
        """
        self.colwid[index] = width

    def get_column_width(self, index):
        """
        Return the column width of the specified column as a percentage of
        the entire table width.

        @param index: column to return (index starts at 0)
        """
        return self.colwid[index]

#------------------------------------------------------------------------
#
# TableCellStyle
#
#------------------------------------------------------------------------
class TableCellStyle(object):
    """
    Defines the style of a particular table cell. Characteristics are:
    right border, left border, top border, bottom border, and padding.
    """
    def __init__(self, obj=None):
        """
        Create a new TableCellStyle instance.

        @param obj: if not None, specifies that the values should be
            copied from the passed object instead of being initialized to empty.
        """
        if obj:
            self.rborder = obj.rborder
            self.lborder = obj.lborder
            self.tborder = obj.tborder
            self.bborder = obj.bborder
            self.padding = obj.padding
            self.longlist = obj.longlist
        else:
            self.rborder = 0
            self.lborder = 0
            self.tborder = 0
            self.bborder = 0
            self.padding = 0
            self.longlist = 0
    
    def set_padding(self, val):
        "Return the cell padding in centimeters"
        self.padding = val

    def set_right_border(self, val):
        """
        Defines if a right border in used

        @param val: if True, a right border is used, if False, it is not
        """
        self.rborder = val

    def set_left_border(self, val):
        """
        Defines if a left border in used

        @param val: if True, a left border is used, if False, it is not
        """
        self.lborder = val

    def set_top_border(self, val):
        """
        Defines if a top border in used

        @param val: if True, a top border is used, if False, it is not
        """
        self.tborder = val

    def set_bottom_border(self, val):
        """
        Defines if a bottom border in used

        @param val: if 1, a bottom border is used, if 0, it is not
        """
        self.bborder = val

    def set_longlist(self, val):
        self.longlist = val

    def get_padding(self):
        "Return the cell padding in centimeters"
        return self.padding

    def get_right_border(self):
        "Return 1 if a right border is requested"
        return self.rborder

    def get_left_border(self):
        "Return 1 if a left border is requested"
        return self.lborder

    def get_top_border(self):
        "Return 1 if a top border is requested"
        return self.tborder

    def get_bottom_border(self):
        "Return 1 if a bottom border is requested"
        return self.bborder

    def get_longlist(self):
        return self.longlist

#------------------------------------------------------------------------
#
# ParagraphStyle
#
#------------------------------------------------------------------------
class ParagraphStyle(object):
    """
    Defines the characteristics of a paragraph. The characteristics are:
    font (a FontStyle instance), right margin, left margin, first indent,
    top margin, bottom margin, alignment, level, top border, bottom border,
    right border, left border, padding, and background color.

    """
    def __init__(self, source=None):
        """
        @param source: if not None, then the ParagraphStyle is created
            using the values of the source instead of the default values.
        """
        if source:
            self.font = FontStyle(source.font)
            self.rmargin = source.rmargin
            self.lmargin = source.lmargin
            self.first_indent = source.first_indent
            self.tmargin = source.tmargin
            self.bmargin = source.bmargin
            self.align = source.align
            self.level = source.level
            self.top_border = source.top_border
            self.bottom_border = source.bottom_border
            self.right_border = source.right_border
            self.left_border = source.left_border
            self.pad = source.pad
            self.bgcolor = source.bgcolor
            self.description = source.description
            self.tabs = source.tabs
        else:
            self.font = FontStyle()
            self.rmargin = 0
            self.lmargin = 0
            self.tmargin = 0
            self.bmargin = 0
            self.first_indent = 0
            self.align = PARA_ALIGN_LEFT
            self.level = 0
            self.top_border = 0
            self.bottom_border = 0
            self.right_border = 0
            self.left_border = 0
            self.pad = 0
            self.bgcolor = (255, 255, 255)
            self.description = ""
            self.tabs = []

    def set_description(self, text):
        """
        Set the desciption of the paragraph
        """
        self.description = text

    def get_description(self):
        """
        Return the desciption of the paragraph
        """
        return self.description

    def set(self, rmargin=None, lmargin=None, first_indent=None,
            tmargin=None, bmargin=None, align=None,
            tborder=None, bborder=None, rborder=None, lborder=None,
            pad=None, bgcolor=None, font=None):
        """
        Allows the values of the object to be set.

        @param rmargin: right indent in centimeters
        @param lmargin: left indent in centimeters
        @param first_indent: first line indent in centimeters
        @param tmargin: space above paragraph in centimeters
        @param bmargin: space below paragraph in centimeters
        @param align: alignment type (PARA_ALIGN_LEFT, PARA_ALIGN_RIGHT, PARA_ALIGN_CENTER, or PARA_ALIGN_JUSTIFY)
        @param tborder: non zero indicates that a top border should be used
        @param bborder: non zero indicates that a bottom border should be used
        @param rborder: non zero indicates that a right border should be used
        @param lborder: non zero indicates that a left border should be used
        @param pad: padding in centimeters
        @param bgcolor: background color of the paragraph as an RGB tuple.
        @param font: FontStyle instance that defines the font
        """
        if font is not None:
            self.font = FontStyle(font)
        if pad is not None:
            self.set_padding(pad)
        if tborder is not None:
            self.set_top_border(tborder)
        if bborder is not None:
            self.set_bottom_border(bborder)
        if rborder is not None:
            self.set_right_border(rborder)
        if lborder is not None:
            self.set_left_border(lborder)
        if bgcolor is not None:
            self.set_background_color(bgcolor)
        if align is not None:
            self.set_alignment(align)
        if rmargin is not None:
            self.set_right_margin(rmargin)
        if lmargin is not None:
            self.set_left_margin(lmargin)
        if first_indent is not None:
            self.set_first_indent(first_indent)
        if tmargin is not None:
            self.set_top_margin(tmargin)
        if bmargin is not None:
            self.set_bottom_margin(bmargin)
            
    def set_header_level(self, level):
        """
        Set the header level for the paragraph. This is useful for
        numbered paragraphs. A value of 1 indicates a header level
        format of X, a value of two implies X.X, etc. A value of zero
        means no header level.
        """
        self.level = level

    def get_header_level(self):
        "Return the header level of the paragraph"
        return self.level

    def set_font(self, font):
        """
        Set the font style of the paragraph.

        @param font: FontStyle object containing the font definition to use.
        """
        self.font = FontStyle(font)

    def get_font(self):
        "Return the FontStyle of the paragraph"
        return self.font

    def set_padding(self, val):
        """
        Set the paragraph padding in centimeters

        @param val: floating point value indicating the padding in centimeters
        """
        self.pad = val

    def get_padding(self):
        """Return a the padding of the paragraph"""
        return self.pad

    def set_top_border(self, val):
        """
        Set the presence or absence of top border.

        @param val: True indicates a border should be used, False indicates
            no border.
        """
        self.top_border = val

    def get_top_border(self):
        "Return 1 if a top border is specified"
        return self.top_border

    def set_bottom_border(self, val):
        """
        Set the presence or absence of bottom border.

        @param val: True indicates a border should be used, False
            indicates no border.
        """
        self.bottom_border = val

    def get_bottom_border(self):
        "Return 1 if a bottom border is specified"
        return self.bottom_border

    def set_left_border(self, val):
        """
        Set the presence or absence of left border.

        @param val: True indicates a border should be used, False
            indicates no border.
        """
        self.left_border = val

    def get_left_border(self):
        "Return 1 if a left border is specified"
        return self.left_border

    def set_right_border(self, val):
        """
        Set the presence or absence of rigth border.

        @param val: True indicates a border should be used, False
            indicates no border.
        """
        self.right_border = val

    def get_right_border(self):
        "Return 1 if a right border is specified"
        return self.right_border

    def get_background_color(self):
        """
        Return a tuple indicating the RGB components of the background
        color
        """
        return self.bgcolor

    def set_background_color(self, color):
        """
        Set the background color of the paragraph.

        @param color: tuple representing the RGB components of a color
            (0,0,0) to (255,255,255)
        """
        self.bgcolor = color

    def set_alignment(self, align):
        """
        Set the paragraph alignment.

        @param align: PARA_ALIGN_LEFT, PARA_ALIGN_RIGHT, PARA_ALIGN_CENTER,
            or PARA_ALIGN_JUSTIFY
        """
        self.align = align

    def get_alignment(self):
        "Return the alignment of the paragraph"
        return self.align

    def get_alignment_text(self):
        """
        Return a text string representing the alginment, either 'left',
        'right', 'center', or 'justify'
        """
        if self.align == PARA_ALIGN_LEFT:
            return "left"
        elif self.align == PARA_ALIGN_CENTER:
            return "center"
        elif self.align == PARA_ALIGN_RIGHT:
            return "right"
        elif self.align == PARA_ALIGN_JUSTIFY:
            return "justify"
        return "unknown"

    def set_left_margin(self, value):
        "sets the left indent in centimeters"
        self.lmargin = value

    def set_right_margin(self, value):
        "sets the right indent in centimeters"
        self.rmargin = value

    def set_first_indent(self, value):
        "sets the first line indent in centimeters"
        self.first_indent = value

    def set_top_margin(self, value):
        "sets the space above paragraph in centimeters"
        self.tmargin = value

    def set_bottom_margin(self, value):
        "sets the space below paragraph in centimeters"
        self.bmargin = value

    def get_left_margin(self):
        "returns the left indent in centimeters"
        return self.lmargin

    def get_right_margin(self):
        "returns the right indent in centimeters"
        return self.rmargin

    def get_first_indent(self):
        "returns the first line indent in centimeters"
        return self.first_indent

    def get_top_margin(self):
        "returns the space above paragraph in centimeters"
        return self.tmargin

    def get_bottom_margin(self):
        "returns the space below paragraph in centimeters"
        return self.bmargin

    def set_tabs(self, tab_stops):
        assert isinstance(tab_stops, list)
        self.tabs = tab_stops

    def get_tabs(self):
        return self.tabs

#------------------------------------------------------------------------
#
# StyleSheetList
#
#------------------------------------------------------------------------
class StyleSheetList(object):
    """
    Interface into the user's defined style sheets. Each StyleSheetList
    has a predefined default style specified by the report. Additional
    styles are loaded from a specified XML file if it exists.
    """
    
    def __init__(self, filename, defstyle):
        """
        Create a new StyleSheetList from the specified default style and
        any other styles that may be defined in the specified file.

        file - XML file that contains style definitions
        defstyle - default style
        """
        defstyle.set_name('default')
        self.map = { "default" : defstyle }
        self.file = os.path.join(const.HOME_DIR, filename)
        self.parse()

    def delete_style_sheet(self, name):
        """
        Remove a style from the list. Since each style must have a
        unique name, the name is used to delete the stylesheet.

        name - Name of the style to delete
        """
        del self.map[name]

    def get_style_sheet_map(self):
        """
        Return the map of names to styles.
        """
        return self.map

    def get_style_sheet(self, name):
        """
        Return the StyleSheet associated with the name

        name - name associated with the desired StyleSheet.
        """
        return self.map[name]

    def get_style_names(self):
        "Return a list of all the style names in the StyleSheetList"
        return self.map.keys()

    def set_style_sheet(self, name, style):
        """
        Add or replaces a StyleSheet in the StyleSheetList. The
        default style may not be replaced.

        name - name assocated with the StyleSheet to add or replace.
        style - definition of the StyleSheet
        """
        style.set_name(name)
        if name != "default":
            self.map[name] = style

    def save(self):
        """
        Saves the current StyleSheet definitions to the associated file.
        """
        xml_file = open(self.file,"w")
        xml_file.write("<?xml version=\"1.0\"?>\n")
        xml_file.write('<stylelist>\n')
        for name in self.map.keys():
            if name == "default":
                continue
            sheet = self.map[name]
            xml_file.write('<sheet name="%s">\n' % escxml(name))
            for p_name in sheet.get_paragraph_style_names():
                para = sheet.get_paragraph_style(p_name)
                xml_file.write('<style name="%s">\n' % escxml(p_name))
                font = para.get_font()
                xml_file.write('<font face="%d" ' % font.get_type_face())
                xml_file.write('size="%d" ' % font.get_size())
                xml_file.write('italic="%d" ' % font.get_italic())
                xml_file.write('bold="%d" ' % font.get_bold())
                xml_file.write('underline="%d" ' % font.get_underline())
                xml_file.write('color="#%02x%02x%02x"/>\n' % font.get_color())
                xml_file.write('<para ')
                rmargin = float(para.get_right_margin())
                lmargin = float(para.get_left_margin())
                findent = float(para.get_first_indent())
                tmargin = float(para.get_top_margin())
                bmargin = float(para.get_bottom_margin())
                padding = float(para.get_padding())
                xml_file.write('description="%s" ' % 
                               escxml(para.get_description()))
                xml_file.write('rmargin="%s" ' % Utils.gformat(rmargin))
                xml_file.write('lmargin="%s" ' % Utils.gformat(lmargin))
                xml_file.write('first="%s" ' % Utils.gformat(findent))
                xml_file.write('tmargin="%s" ' % Utils.gformat(tmargin))
                xml_file.write('bmargin="%s" ' % Utils.gformat(bmargin))
                xml_file.write('pad="%s" ' % Utils.gformat(padding))
                bg_color = para.get_background_color()
                xml_file.write('bgcolor="#%02x%02x%02x" ' % bg_color)
                xml_file.write('level="%d" ' % para.get_header_level())
                xml_file.write('align="%d" ' % para.get_alignment())
                xml_file.write('tborder="%d" ' % para.get_top_border())
                xml_file.write('lborder="%d" ' % para.get_left_border())
                xml_file.write('rborder="%d" ' % para.get_right_border())
                xml_file.write('bborder="%d"/>\n' % para.get_bottom_border())
                xml_file.write('</style>\n')
            xml_file.write('</sheet>\n')
        xml_file.write('</stylelist>\n')
        xml_file.close()
            
    def parse(self):
        """
        Loads the StyleSheets from the associated file, if it exists.
        """
        try:
            if os.path.isfile(self.file):
                parser = make_parser()
                parser.setContentHandler(SheetParser(self))
                the_file = open(self.file)
                parser.parse(the_file)
                the_file.close()
        except (IOError,OSError,SAXParseException):
            pass
        
#------------------------------------------------------------------------
#
# StyleSheet
#
#------------------------------------------------------------------------
class StyleSheet(object):
    """
    A collection of named paragraph styles.
    """
    
    def __init__(self, obj=None):
        """
        Create a new empty StyleSheet.

        @param obj: if not None, creates the StyleSheet from the values in
            obj, instead of creating an empty StyleSheet
        """
        self.para_styles = {}
        self.draw_styles = {}
        self.table_styles = {}
        self.cell_styles = {}
        self.name = ""
        if obj is not None:
            for style_name in obj.para_styles.keys():
                style = obj.para_styles[style_name]
                self.para_styles[style_name] = ParagraphStyle(style)
            for style_name in obj.draw_styles.keys():
                style = obj.draw_styles[style_name]
                self.draw_styles[style_name] = GraphicsStyle(style)
            for style_name in obj.table_styles.keys():
                style = obj.table_styles[style_name]
                self.table_styles[style_name] = TableStyle(style)
            for style_name in obj.cell_styles.keys():
                style = obj.cell_styles[style_name]
                self.cell_styles[style_name] = TableCellStyle(style)

    def set_name(self, name):
        """
        Set the name of the StyleSheet
        
        @param name: The name to be given to the StyleSheet
        """
        self.name = name

    def get_name(self):
        """
        Return the name of the StyleSheet
        """
        return self.name

    def clear(self):
        "Remove all styles from the StyleSheet"
        self.para_styles = {}
        self.draw_styles = {}
        self.table_styles = {}
        self.cell_styles = {}
        
    def is_empty(self):
        "Checks if any styles are defined"
        style_count = len(self.para_styles)  + \
                      len(self.draw_styles)  + \
                      len(self.table_styles) + \
                      len(self.cell_styles)
        if style_count > 0:
            return False
        else:
            return True      

    def add_paragraph_style(self, name, style):
        """
        Add a paragraph style to the style sheet.

        @param name: The name of the ParagraphStyle
        @param style: ParagraphStyle instance to be added.
        """
        self.para_styles[name] = ParagraphStyle(style)
        
    def get_paragraph_style(self, name):
        """
        Return the ParagraphStyle associated with the name

        @param name: name of the ParagraphStyle that is wanted
        """
        return ParagraphStyle(self.para_styles[name])

    def get_paragraph_style_names(self):
        "Return the the list of paragraph names in the StyleSheet"
        return self.para_styles.keys()

    def add_draw_style(self, name, style):
        """
        Add a draw style to the style sheet.

        @param name: The name of the GraphicsStyle
        @param style: GraphicsStyle instance to be added.
        """
        self.draw_styles[name] = GraphicsStyle(style)
        
    def get_draw_style(self, name):
        """
        Return the GraphicsStyle associated with the name

        @param name: name of the GraphicsStyle that is wanted
        """
        return GraphicsStyle(self.draw_styles[name])

    def get_draw_style_names(self):
        "Return the the list of draw style names in the StyleSheet"
        return self.draw_styles.keys()
    
    def add_table_style(self, name, style):
        """
        Add a table style to the style sheet.

        @param name: The name of the TableStyle
        @param style: TableStyle instance to be added.
        """
        self.table_styles[name] = TableStyle(style)
        
    def get_table_style(self, name):
        """
        Return the TableStyle associated with the name

        @param name: name of the TableStyle that is wanted
        """
        return TableStyle(self.table_styles[name])

    def get_table_style_names(self):
        "Return the the list of table style names in the StyleSheet"
        return self.table_styles.keys()
    
    def add_cell_style(self, name, style):
        """
        Add a cell style to the style sheet.

        @param name: The name of the TableCellStyle
        @param style: TableCellStyle instance to be added.
        """
        self.cell_styles[name] = TableCellStyle(style)
        
    def get_cell_style(self, name):
        """
        Return the TableCellStyle associated with the name

        @param name: name of the TableCellStyle that is wanted
        """
        return TableCellStyle(self.cell_styles[name])

    def get_cell_style_names(self):
        "Return the the list of cell style names in the StyleSheet"
        return self.cell_styles.keys()

#-------------------------------------------------------------------------
#
# SheetParser
#
#-------------------------------------------------------------------------
class SheetParser(handler.ContentHandler):
    """
    SAX parsing class for the StyleSheetList XML file.
    """
    
    def __init__(self, sheetlist):
        """
        Create a SheetParser class that populates the passed StyleSheetList
        class.

        sheetlist - StyleSheetList instance to be loaded from the file.
        """
        handler.ContentHandler.__init__(self)
        self.sheetlist = sheetlist
        self.f = None
        self.p = None
        self.s = None
        self.sname = None
        self.pname = None
        
    def startElement(self, tag, attrs):
        """
        Overridden class that handles the start of a XML element
        """
        if tag == "sheet":
            self.s = StyleSheet(self.sheetlist.map["default"])
            self.sname = attrs['name']
        elif tag == "font":
            self.f = FontStyle()
            self.f.set_type_face(int(attrs['face']))
            self.f.set_size(int(attrs['size']))
            self.f.set_italic(int(attrs['italic']))
            self.f.set_bold(int(attrs['bold']))
            self.f.set_underline(int(attrs['underline']))
            self.f.set_color(cnv2color(attrs['color']))
        elif tag == "para":
            if attrs.has_key('description'):
                self.p.set_description(attrs['description'])
            self.p.set_right_margin(Utils.gfloat(attrs['rmargin']))
            self.p.set_right_margin(Utils.gfloat(attrs['rmargin']))
            self.p.set_left_margin(Utils.gfloat(attrs['lmargin']))
            self.p.set_first_indent(Utils.gfloat(attrs['first']))
            try:
                # This is needed to read older style files
                # lacking tmargin and bmargin
                self.p.set_top_margin(Utils.gfloat(attrs['tmargin']))
                self.p.set_bottom_margin(Utils.gfloat(attrs['bmargin']))
            except KeyError:
                pass
            self.p.set_padding(Utils.gfloat(attrs['pad']))
            self.p.set_alignment(int(attrs['align']))
            self.p.set_right_border(int(attrs['rborder']))
            self.p.set_header_level(int(attrs['level']))
            self.p.set_left_border(int(attrs['lborder']))
            self.p.set_top_border(int(attrs['tborder']))
            self.p.set_bottom_border(int(attrs['bborder']))
            self.p.set_background_color(cnv2color(attrs['bgcolor']))
        elif tag == "style":
            self.p = ParagraphStyle()
            self.pname = attrs['name']

    def endElement(self, tag):
        "Overridden class that handles the start of a XML element"
        if tag == "style":
            self.p.set_font(self.f)
            self.s.add_paragraph_style(self.pname, self.p)
        elif tag == "sheet":
            self.sheetlist.set_style_sheet(self.sname, self.s)

#------------------------------------------------------------------------
#
# GraphicsStyle
#
#------------------------------------------------------------------------
class GraphicsStyle(object):
    """
    Defines the properties of graphics objects, such as line width,
    color, fill, ect.
    """
    def __init__(self, obj=None):
        """
        Initialize the object with default values, unless a source
        object is specified. In that case, make a copy of the source
        object.
        """
        if obj:
            self.para_name = obj.para_name
            self.shadow = obj.shadow
            self.shadow_space = obj.shadow_space
            self.color = obj.color
            self.fill_color = obj.fill_color
            self.lwidth = obj.lwidth
            self.lstyle = obj.lstyle
        else:
            self.para_name = ""
            self.shadow = 0
            self.shadow_space = 0.2
            self.lwidth = 0.5
            self.color = (0, 0, 0)
            self.fill_color = (255, 255, 255)
            self.lstyle = SOLID

    def set_line_width(self, val):
        """
        sets the line width
        """
        self.lwidth = val

    def get_line_width(self):
        """
        Return the name of the StyleSheet
        """
        return self.lwidth

    def get_line_style(self):
        return self.lstyle

    def set_line_style(self, val):
        self.lstyle = val

    def set_paragraph_style(self, val):
        self.para_name = val

    def set_shadow(self, val, space=0.2):
        self.shadow = val
        self.shadow_space = space

    def get_shadow_space(self):
        return self.shadow_space

    def set_color(self, val):
        self.color = val

    def set_fill_color(self, val):
        self.fill_color = val

    def get_paragraph_style(self):
        return self.para_name

    def get_shadow(self):
        return self.shadow

    def get_color(self):
        return self.color

    def get_fill_color(self):
        return self.fill_color

#------------------------------------------------------------------------
#
# IndexMark
#
#------------------------------------------------------------------------
class IndexMark(object):
    """
    Defines a mark to be associated with text for indexing.
    """
    def __init__(self, key="", itype=INDEX_TYPE_ALP, level=1):
        """
        Initialize the object with default values, unless values are specified.
        """
        self.key = key
        self.type = itype
        self.level = level

#------------------------------------------------------------------------
#
# BaseDoc
#
#------------------------------------------------------------------------
class BaseDoc(object):
    """
    Base class for document generators. Different output formats,
    such as OpenOffice, AbiWord, and LaTeX are derived from this base
    class, providing a common interface to all document generators.
    """
    def __init__(self, styles, paper_style, template):
        """
        Create a BaseDoc instance, which provides a document generation
        interface. This class should never be instantiated directly, but
        only through a derived class.

        @param styles: StyleSheet containing the styles used.
        @param paper_style: PaperStyle instance containing information about
            the paper. If set to None, then the document is not a page
            oriented document (e.g. HTML)
        @param template: Format template for document generators that are
            not page oriented.
        """
        self.template = template
        self.paper = paper_style
        self._style_sheet = styles
        self._creator = ""
        self.open_req = 0
        self.init_called = False
        self.type = "standard"

    def init(self):
        self.init_called = True
        
    def open_requested(self):
        self.open_req = 1

    def set_creator(self, name):
        "Set the owner name"
        self._creator = name
        
    def get_creator(self):
        "Return the owner name"
        return self._creator
        
    def get_style_sheet(self):
        """
        Return the StyleSheet of the document.
        """
        return StyleSheet(self._style_sheet)
    
    def set_style_sheet(self, style_sheet):
        """
        Set the StyleSheet of the document.

        @param style_sheet: The new style sheet for the document
        @type  style_sheet: StyleSheet
        """
        self._style_sheet = StyleSheet(style_sheet)

    def open(self, filename):
        """
        Opens the document.

        @param filename: path name of the file to create
        """
        raise NotImplementedError

    def close(self):
        "Closes the document"
        raise NotImplementedError


#------------------------------------------------------------------------
#
# TextDoc
#
#------------------------------------------------------------------------
def noescape(text):
    return text
    
class TextDoc(object):
    """
    Abstract Interface for text document generators. Output formats for
    text reports must implment this interface to be used by the report 
    system.
    """
    BOLD = 0
    ITALIC = 1
    UNDERLINE = 2
    FONTFACE = 3
    FONTSIZE = 4
    FONTCOLOR = 5
    HIGHLIGHT = 6
    SUPERSCRIPT = 7
    
    SUPPORTED_MARKUP = []

    ESCAPE_FUNC = lambda x: noescape
    #Map between styletypes and internally used values. This map is needed
    # to make TextDoc officially independant of gen.lib.styledtexttag
    STYLETYPE_MAP = {
        }
    CLASSMAP = None
    
    #STYLETAGTABLE to store markup for write_markup associated with style tags
    STYLETAG_MARKUP = {
        BOLD        : ("", ""),
        ITALIC      : ("", ""),
        UNDERLINE   : ("", ""),
        SUPERSCRIPT : ("", ""),
        }

    def page_break(self):
        "Forces a page break, creating a new page"
        raise NotImplementedError

    def start_bold(self):
        raise NotImplementedError

    def end_bold(self):
        raise NotImplementedError

    def start_superscript(self):
        raise NotImplementedError

    def end_superscript(self):
        raise NotImplementedError

    def start_paragraph(self, style_name, leader=None):
        """
        Starts a new paragraph, using the specified style name.

        @param style_name: name of the ParagraphStyle to use for the
            paragraph.
        @param leader: Leading text for a paragraph. Typically used
            for numbering.
        """
        raise NotImplementedError

    def end_paragraph(self):
        "Ends the current parsgraph"
        raise NotImplementedError

    def start_table(self, name, style_name):
        """
        Starts a new table.

        @param name: Unique name of the table.
        @param style_name: TableStyle to use for the new table
        """
        raise NotImplementedError

    def end_table(self):
        "Ends the current table"
        raise NotImplementedError

    def start_row(self):
        "Starts a new row on the current table"
        raise NotImplementedError

    def end_row(self):
        "Ends the current row on the current table"
        raise NotImplementedError

    def start_cell(self, style_name, span=1):
        """
        Starts a new table cell, using the paragraph style specified.

        @param style_name: TableCellStyle to use for the cell
        @param span: number of columns to span
        """
        raise NotImplementedError

    def end_cell(self):
        "Ends the current table cell"
        raise NotImplementedError

    def write_text(self, text, mark=None):
        """
        Writes the text in the current paragraph. Should only be used after a
        start_paragraph and before an end_paragraph.

        @param text: text to write.
        @param mark:  IndexMark to use for indexing (if supported)
        """
        raise NotImplementedError
    
    def write_markup(self, text, s_tags):
        """
        Writes the text in the current paragraph.  Should only be used after a
        start_paragraph and before an end_paragraph. Not all backends support
        s_tags, then the same happens as with write_text. Backends supporting
        write_markup will overwrite this method 
        
        @param text: text to write. The text is assumed to be _not_ escaped
        @param s_tags:  assumed to be list of styledtexttags to apply to the
                        text
        """
        self.write_text(text)

    def write_note(self, text, format, style_name):
        """
        Writes the note's text and take care of paragraphs, 
        depending on the format. 

        @param text: text to write.
        @param format: format to use for writing. True for flowed text, 
            1 for preformatted text.
        """
        raise NotImplementedError

    def write_styled_note(self, styledtext, format, style_name):
        """
        Convenience function to write a styledtext to the cairo doc. 
        styledtext : assumed a StyledText object to write
        format : = 0 : Flowed, = 1 : Preformatted
        style_name : name of the style to use for default presentation
        
        overwrite this method if the backend supports styled notes
        """
        text = str(styledtext)
        self.write_note(text, format, style_name)
    
    def write_text_citation(self, text, mark=None):
        """Method to write text with GRAMPS <super> citation marks"""
        if not text:
            return
        parts = text.split("<super>")
        markset = False
        for piece in parts:
            if not piece:
                # a text '<super>text ...' splits as '', 'text..'
                continue
            piecesplit = piece.split("</super>")
            if len(piecesplit) == 2:
                self.start_superscript()
                self.write_text(piecesplit[0])
                self.end_superscript()
                if not piecesplit[1]:
                    #text ended with ' ... </super>'
                    continue
                if not markset:
                    self.write_text(piecesplit[1], mark)
                    markset = True
                else:
                    self.write_text(piecesplit[1])
            else:
                if not markset:
                    self.write_text(piece, mark)
                    markset = True
                else:
                    self.write_text(piece)

    def add_media_object(self, name, align, w_cm, h_cm):
        """
        Add a photo of the specified width (in centimeters)

        @param name: filename of the image to add
        @param align: alignment of the image. Valid values are 'left',
            'right', 'center', and 'single'
        @param w_cm: width in centimeters
        @param h_cm: height in centimeters
        """
        raise NotImplementedError
    
    def find_tag_by_stag(self, s_tag):
        """
        @param s_tag: object: assumed styledtexttag
        @param s_tagvalue: None/int/str: value associated with the tag
        
        A styled tag is type with a value. 
        Every styled tag must be converted to the tags used in the corresponding
            markup for the backend, eg <b>text</b> for bold in html.
        These markups are stored in STYLETAG_MARKUP. They are tuples for begin
            and end tag
        If a markup is not present yet, it is created, using the 
            _create_xmltag method you can overwrite
        """
        type = s_tag.name
        
        if not self.STYLETYPE_MAP or \
        self.CLASSMAP <> type.__class__.__name__ :
            self.CLASSMAP == type.__class__.__name__
            self.STYLETYPE_MAP[type.__class__.BOLD]        = self.BOLD
            self.STYLETYPE_MAP[type.ITALIC]      = self.ITALIC
            self.STYLETYPE_MAP[type.UNDERLINE]   = self.UNDERLINE
            self.STYLETYPE_MAP[type.FONTFACE]    = self.FONTFACE
            self.STYLETYPE_MAP[type.FONTSIZE]    = self.FONTSIZE
            self.STYLETYPE_MAP[type.FONTCOLOR]   = self.FONTCOLOR
            self.STYLETYPE_MAP[type.HIGHLIGHT]   = self.HIGHLIGHT
            self.STYLETYPE_MAP[type.SUPERSCRIPT] = self.SUPERSCRIPT

        typeval = int(s_tag.name)
        s_tagvalue = s_tag.value
        tag_name = None
        if type.STYLE_TYPE[typeval] == bool:
            return self.STYLETAG_MARKUP[self.STYLETYPE_MAP[typeval]]
        elif type.STYLE_TYPE[typeval] == str:
            tag_name = "%d %s" % (typeval, s_tagvalue)
        elif type.STYLE_TYPE[typeval] == int:
            tag_name = "%d %d" % (typeval, s_tagvalue)
        if not tag_name:
            return None
        
        tags = self.STYLETAG_MARKUP.get(tag_name)
        if tags is not None:
            return tags
        #no tag known yet, create the markup, add to lookup, and return
        tags = self._create_xmltag(self.STYLETYPE_MAP[typeval], s_tagvalue)
        self.STYLETAG_MARKUP[tag_name] = tags
        return tags

    def _create_xmltag(self, type, value):
        """
        Create the xmltags for the backend.
        Overwrite this method to create functionality with a backend
        """
        if type not in self.SUPPORTED_MARKUP:
            return None
        return ('', '')
    
    def _add_markup_from_styled(self, text, s_tags, split=''):
        """
        Input is plain text, output is text with markup added according to the
        s_tags which are assumed to be styledtexttags.
        When split is given the text will be split over the value given, and 
        tags applied in such a way that it the text can be safely splitted in
        pieces along split
        
        @param text   : str, a piece of text
        @param s_tags : styledtexttags that must be applied to the text
        @param split  : str, optional. A string along which the output can 
                    be safely split without breaking the styling.
        As adding markup means original text must be escaped, ESCAPE_FUNC is 
            used
        This can be used to convert the text of a styledtext to the format 
            needed for a document backend
        Do not call this method in a report, use the write_markup method
            
        @note: the algorithm is complex as it assumes mixing of tags is not
                allowed: eg <b>text<i> here</b> not</i> is assumed invalid
                as markup. If the s_tags require such a setup, what is returned
                is <b>text</b><i><b> here</b> not</i>
               overwrite this method if this complexity is not needed. 
        """
        #unicode text most be sliced correctly
        text=unicode(text)
        FIRST = 0
        LAST = 1
        tagspos = {}
        for s_tag in s_tags:
            tag = self.find_tag_by_stag(s_tag)
            if tag is not None:
                for (start, end) in s_tag.ranges:
                    if start in tagspos:
                        tagspos[start] += [(tag, FIRST)]
                    else:
                        tagspos[start] = [(tag, FIRST)]
                    if end in tagspos:
                        tagspos[end] = [(tag, LAST)] + tagspos[end]
                    else:
                        tagspos[end] = [(tag, LAST)]
        start = 0
        end = len(text)
        keylist = tagspos.keys()
        keylist.sort()
        keylist = [x for x in keylist if x<=len(text)]
        opentags = []
        otext = u""  #the output, text with markup
        lensplit = len(split)
        for pos in keylist:
            #write text up to tag
            if pos > start:
                if split:
                    #make sure text can split
                    splitpos = text[start:pos].find(split)
                    while splitpos <> -1:
                        otext += self.ESCAPE_FUNC()(text[start:start+splitpos])
                        #close open tags
                        opentags.reverse()
                        for opentag in opentags:
                            otext += opentag[1]
                        opentags.reverse()
                        #add split text
                        otext += self.ESCAPE_FUNC()(split)
                        #open the tags again
                        for opentag in opentags:
                            otext += opentag[0]
                        #obtain new values
                        start = start + splitpos + lensplit
                        splitpos = text[start:pos].find(split)
                    
                otext += self.ESCAPE_FUNC()(text[start:pos])
            #write out tags
            for tag in tagspos[pos]:
                #close open tags starting from last open
                opentags.reverse()
                for opentag in opentags:
                    otext += opentag[1]
                opentags.reverse()
                #if start, add to opentag in beginning as first to open
                if tag[1] == FIRST:
                    opentags = [tag[0]] + opentags
                else:
                    #end tag, is closed already, remove from opentag
                    opentags = [x for x in opentags if not x == tag[0] ]
                #now all tags are closed, open the ones that should open
                for opentag in opentags:
                    otext += opentag[0]
            start = pos
        #add remainder of text, no markup present there
        otext += self.ESCAPE_FUNC()(text[start:end])
        
        #opentags should be empty. If not, user gave tags on positions that 
        # are over the end of the text. Just close the tags still open
        if opentags:
            print 'WARNING: TextDoc : More style tags in text than length '\
                    'of text allows.\n', opentags
            opentags.reverse()
            for opentag in opentags:
                otext += opentag[1]
        
        return otext
    

#------------------------------------------------------------------------
#
# DrawDoc
#
#------------------------------------------------------------------------
class DrawDoc(object):
    """
    Abstract Interface for graphical document generators. Output formats
    for graphical reports must implment this interface to be used by the
    report system.
    """

    def start_page(self):
        raise NotImplementedError

    def end_page(self):
        raise NotImplementedError

    def get_usable_width(self):
        """
        Return the width of the text area in centimeters. The value is
        the page width less the margins.
        """
        width = self.paper.get_size().get_width()
        right = self.paper.get_right_margin()
        left = self.paper.get_left_margin()
        return width - (right + left)

    def get_usable_height(self):
        """
        Return the height of the text area in centimeters. The value is
        the page height less the margins.
        """
        height = self.paper.get_size().get_height()
        top = self.paper.get_top_margin()
        bottom = self.paper.get_bottom_margin()
        return height - (top + bottom)

    def string_width(self, fontstyle, text):
        "Determine the width need for text in given font"
        return FontScale.string_width(fontstyle, text)

    def draw_path(self, style, path):
        raise NotImplementedError
    
    def draw_box(self, style, text, x, y, w, h):
        raise NotImplementedError

    def draw_text(self, style, text, x1, y1):
        raise NotImplementedError

    def center_text(self, style, text, x1, y1):
        raise NotImplementedError

    def rotate_text(self, style, text, x, y, angle):
        raise NotImplementedError
    
    def draw_line(self, style, x1, y1, x2, y2):
        raise NotImplementedError

#-------------------------------------------------------------------------------
#
# GVDoc
#
#-------------------------------------------------------------------------------
class GVDoc(object):
    """
    Abstract Interface for Graphviz document generators. Output formats
    for Graphviz reports must implment this interface to be used by the
    report system.
    """
    def add_node(self, node_id, label, shape="", color="", 
                 style="", fillcolor="", url="", htmloutput=False):
        """
        Add a node to this graph. Nodes can be different shapes like boxes and
        circles.
        
        @param node_id: A unique identification value for this node.
            Example: "p55"
        @type node_id: string
        @param label: The text to be displayed in the node.
            Example: "John Smith"
        @type label: string
        @param shape: The shape for the node.
            Examples: "box", "ellipse", "circle"
        @type shape: string
        @param color: The color of the node line.
            Examples: "blue", "lightyellow"
        @type color: string
        @param style: The style of the node.
        @type style: string
        @param fillcolor: The fill color for the node.
            Examples: "blue", "lightyellow"
        @type fillcolor: string
        @param url: A URL for the node.
        @type url: string
        @param htmloutput: Whether the label contains HTML.
        @type htmloutput: boolean
        @return: nothing
        """
        raise NotImplementedError

    def add_link(self, id1, id2, style="", head="", tail="", comment=""):
        """
        Add a link between two nodes.
        
        @param id1: The unique identifier of the starting node.
            Example: "p55"
        @type id1: string
        @param id2: The unique identifier of the ending node.
            Example: "p55"
        @type id2: string
        @param comment: A text string displayed at the end of the link line.
            Example: "person C is the son of person A and person B"
        @type comment: string
        @return: nothing
        """
        raise NotImplementedError

    def add_comment(self, comment):
        """
        Add a comment to the source file.

        @param comment: A text string to add as a comment.
            Example: "Next comes the individuals."
        @type comment: string
        @return: nothing
        """
        raise NotImplementedError

    def start_subgraph(self, graph_id):
        """
        Start a subgraph in this graph.
        
        @param id: The unique identifier of the subgraph.
            Example: "p55"
        @type id1: string
        @return: nothing
        """
        raise NotImplementedError

    def end_subgraph(self):
        """
        End a subgraph that was previously started in this graph.

        @return: nothing
        """
        raise NotImplementedError
