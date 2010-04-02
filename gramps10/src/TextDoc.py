
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
#
# Modified September 2002 by Gary Shao
#
#   Added line_break() method to TextDoc class to allow breaking a line
#   in a paragraph (in those document generators that support it).
#
#   Added start_listing() and end_listing() methods to TextDoc class to
#   allow displaying text blocks without automatic filling and justification.
#   Creating a new listing element seems called for because many document
#   generator implementation have to use a different mechanism for text
#   that is not going to be automatically filled and justified than that
#   used for normal paragraphs. Examples are <pre> tags in HTML, using
#   the Verbatim environment in LaTeX, and using the Preformatted class
#   in reportlab for generating PDF.
#
#   Added another option, FONT_MONOSPACE, for use as a font face. This
#   calls for a fixed-width font (e.g. Courier). It is intended primarily
#   for supporting the display of text where alignment by character position
#   may be important, such as in code source or column-aligned data.
#   Especially useful in styles for the new listing element discussed above.
#
#   Added start_italic() and end_italic() methods to TextDoc class to
#   complement the emphasis of text in a paragraph by bolding with the
#   ability to italicize segments of text in a paragraph.
#
#   Added the show_link() method to TextDoc to enable the creation of
#   hyperlinks in HTML output. Only produces active links in HTML, while
#   link will be represented as text in other generator output. (active
#   links are technically possible in PDF documents, but the reportlab
#   modules the PDF generator is based on does not support them at this
#   time)
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

"""
Provides base interface to text based documents. Specific document
interfaces should be derived from the core classes.
"""

__author__ = "Donald N. Allingham"
__version__ = "Revision:$"

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
import string
import os

#-------------------------------------------------------------------------
#
# SAX interface
#
#-------------------------------------------------------------------------
try:
    from xml.sax import make_parser,handler,SAXParseException
except:
    from _xmlplus.sax import make_parser,handler,SAXParseException

#-------------------------------------------------------------------------
#
# constants
#
#-------------------------------------------------------------------------
FONT_SANS_SERIF = 0
FONT_SERIF = 1
FONT_MONOSPACE = 2

PAPER_PORTRAIT  = 0
PAPER_LANDSCAPE = 1

PARA_ALIGN_CENTER = 0
PARA_ALIGN_LEFT   = 1 
PARA_ALIGN_RIGHT  = 2
PARA_ALIGN_JUSTIFY= 3

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
    c0 = string.atoi(text[1:3],16)
    c1 = string.atoi(text[3:5],16)
    c2 = string.atoi(text[5:7],16)
    return (c0,c1,c2)

#------------------------------------------------------------------------
#
# PaperStyle
#
#------------------------------------------------------------------------
class PaperStyle:
    """
    Defines the dimensions of a sheet of paper. All dimensions are in
    centimeters.
    """
    def __init__(self,name,height,width):
        """
        Creates a new paper style with.

        name - Name of the new style
        height - page height in centimeters
        width - page width in centimeters
        """
        self.name = name
        self.orientation = PAPER_PORTRAIT
        self.height = height
        self.width = width

    def get_name(self):
        "Returns the name of the paper style"
        return self.name

    def get_orientation(self):
        "Returns the page orientation (PAPER_PORTRAIT or PAPER_LANDSCAPE)"
        return self.orientation

    def set_orientation(self,val):
        """
        Sets the page orientation.

        val - new orientation, should be either PAPER_PORTRAIT or
              PAPER_LANDSCAPE
        """
        self.orientation = val

    def get_height(self):
        "Returns the page height in cm"
        return self.height

    def get_width(self):
        "Returns the page width in cm"
        return self.width

    def get_height_inches(self):
        "Returns the page height in inches"
        return self.height / 2.54

    def get_width_inches(self):
        "Returns the page width in inches"
        return self.width / 2.54

#------------------------------------------------------------------------
#
# FontStyle
#
#------------------------------------------------------------------------
class FontStyle:
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
        Creates a new FontStyle object, accepting the default values.

        style - if specified, initializes the FontStyle from the passed
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
            self.color  = (0,0,0)
            self.under  = 0
            
    def set(self,face=None,size=None,italic=None,bold=None,underline=None,color=None):
        """
        Sets font characteristics.

        face - font type face, either FONT_SERIF or FONT_SANS_SERIF
        size - type face size in points
        italic - 1 enables italics, 0 disables italics
        bold - 1 enables bold face, 0 disables bold face
        underline - 1 enables underline, 0 disables underline
        color - an RGB color representation in the form of three integers
                in the range of 0-255 represeting the red, green, and blue
                components of a color.
        """
        if face != None:
            self.set_type_face(face)
        if size != None:
            self.set_size(size)
        if italic != None:
            self.set_italic(italic)
        if bold != None:
            self.set_bold(bold)
        if underline != None:
            self.set_underline(underline)
        if color != None:
            self.set_color(color)

    def set_italic(self,val):
        "0 disables italics, 1 enables italics"
        self.italic = val

    def get_italic(self):
        "1 indicates use italics"
        return self.italic

    def set_bold(self,val):
        "0 disables bold face, 1 enables bold face"
        self.bold = val

    def get_bold(self):
        "1 indicates use bold face"
        return self.bold

    def set_color(self,val):
        "sets the color using an RGB color tuple"
        self.color = val

    def get_color(self):
        "Returns an RGB color tuple"
	return self.color

    def set_size(self,val):
        "sets font size in points"
        self.size = val

    def get_size(self):
        "returns font size in points"
        return self.size

    def set_type_face(self,val):
        "sets the font face type"
        self.face = val

    def get_type_face(self):
        "returns the font face type"
        return self.face

    def set_underline(self,val):
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
class TableStyle:
    """
    Specifies the style or format of a table. The TableStyle contains the
    characteristics of table width (in percentage of the full width), the
    number of columns, and the width of each column as a percentage of the
    width of the table.
    """
    def __init__(self,obj=None):
        """
        Creates a new TableStyle object, with the values initialized to
        empty, with allocating space for up to 100 columns.

        obj - if not None, then the object created gets is attributes from
              the passed object instead of being initialized to empty.
        """
        if obj:
            self.width = obj.width
            self.columns = obj.columns
            self.colwid  = obj.colwid[:]
        else:
            self.width = 0
            self.columns = 0
            self.colwid = [ 0 ] * 100

    def set_width(self,width):
        """Sets the width of the table in terms of percent of the available
           width"""
        self.width = width

    def get_width(self):
        "Returns the specified width as a percentage of the available space"
        return self.width

    def set_columns(self,columns):
        """Sets the number of columns.

           columns - number of columns that should be used.
        """
        self.columns = columns

    def get_columns(self):
        "Returns the number of columns"
        return self.columns 

    def set_column_widths(self, list):
        """Sets the width of all the columns at once, taking the percentages
           from the passed list.
        """
        self.columns = len(list)
        for i in range(self.columns):
            self.colwid[i] = list[i]

    def set_column_width(self,index,width):
        """Sets the width of a specified column to the specified width.

           index - column being set (index starts at 0)
           width - percentage of the table width assigned to the column
        """
	self.colwid[index] = width

    def get_column_width(self,index):
        """
        Returns the column width of the specified column as a percentage of
        the entire table width.

        index - column to return (index starts at 0)
        """
	return self.colwid[index]

#------------------------------------------------------------------------
#
# TableCellStyle
#
#------------------------------------------------------------------------
class TableCellStyle:
    """
    Defines the style of a particular table cell. Characteristics are:
    right border, left border, top border, bottom border, and padding.
    """
    def __init__(self,obj=None):
        """
        Creates a new TableCellStyle instance.

        obj - if not None, specifies that the values should be copied from
              the passed object instead of being initialized to empty.
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
	    
    def set_padding(self,val):
        "Returns the cell padding in centimeters"
        self.padding = val

    def set_right_border(self,val):
        """
        Defines if a right border in used

        val - if 1, a right border is used, if 0, it is not
        """
        self.rborder = val

    def set_left_border(self,val):
        """
        Defines if a left border in used

        val - if 1, a left border is used, if 0, it is not
        """
        self.lborder = val

    def set_top_border(self,val):
        """
        Defines if a top border in used

        val - if 1, a top border is used, if 0, it is not
        """
        self.tborder = val

    def set_bottom_border(self,val):
        """
        Defines if a bottom border in used

        val - if 1, a bottom border is used, if 0, it is not
        """
        self.bborder = val

    def set_longlist(self,val):
        self.longlist = val

    def get_padding(self):
        "Returns the cell padding in centimeters"
        return self.padding

    def get_right_border(self):
        "Returns 1 if a right border is requested"
        return self.rborder

    def get_left_border(self):
        "Returns 1 if a left border is requested"
        return self.lborder

    def get_top_border(self):
        "Returns 1 if a top border is requested"
        return self.tborder

    def get_bottom_border(self):
        "Returns 1 if a bottom border is requested"
        return self.bborder

    def get_longlist(self):
        return self.longlist

#------------------------------------------------------------------------
#
# ParagraphStyle
#
#------------------------------------------------------------------------
class ParagraphStyle:
    """
    Defines the characteristics of a paragraph. The characteristics are:
    font (a FontStyle instance), right margin, left margin, first indent,
    alignment, level, top border, bottom border, right border, left
    border, padding, and background color.

    source - if not None, then the ParagraphStyle is created using the
             values of the source instead of the default values.
    """
    def __init__(self,source=None):
        if source:
            self.font    = FontStyle(source.font)
            self.rmargin = source.rmargin
            self.lmargin = source.lmargin
            self.first_indent = source.first_indent
            self.align   = source.align
	    self.level   = source.level
	    self.top_border = source.top_border
	    self.bottom_border = source.bottom_border
	    self.right_border = source.right_border
	    self.left_border = source.left_border
            self.pad = source.pad
            self.bgcolor = source.bgcolor
        else:
            self.font    = FontStyle()
            self.rmargin = 0
            self.lmargin = 0
            self.first_indent = 0
            self.align   = PARA_ALIGN_LEFT
	    self.level   = 0
	    self.top_border = 0
	    self.bottom_border = 0
	    self.right_border = 0
	    self.left_border = 0
            self.pad = 0
            self.bgcolor = (255,255,255)

    def set(self,rmargin=None,lmargin=None,first_indent=None,align=None,
            tborder=None,bborder=None,rborder=None,lborder=None,pad=None,
            bgcolor=None,font=None):
        """
        Allows the values of the object to be set.

        rmargin - right margin in centimeters
        lmargin - left margin in centimeters
        first_indent - first line indent in centimeters
        align - alignment type (PARA_ALIGN_LEFT, PARA_ALIGN_RIGHT,
                PARA_ALIGN_CENTER, or PARA_ALIGN_JUSTIFY)
        tborder - non zero indicates that a top border should be used
        bborder - non zero indicates that a bottom border should be used
        rborder - non zero indicates that a right border should be used
        lborder - non zero indicates that a left border should be used
        pad - padding in centimeters
        bgcolor - background color of the paragraph as an RGB tuple.
        font - FontStyle instance that defines the font
        """
        if font != None:
            self.font = FontStyle(font)
        if pad != None:
            self.set_padding(pad)
        if tborder != None:
            self.set_top_border(tborder)
        if bborder != None:
            self.set_bottom_border(bborder)
        if rborder != None:
            self.set_right_border(rborder)
        if lborder != None:
            self.set_left_border(lborder)
        if bgcolor != None:
            self.set_background_color(bgcolor)
        if align != None:
            self.set_alignment(align)
        if rmargin != None:
            self.set_right_margin(rmargin)
        if lmargin != None:
            self.set_left_margin(lmargin)
        if first_indent != None:
            self.set_first_indent(first_indent)
            
    def set_header_level(self,level):
        """
        Sets the header level for the paragraph. This is useful for
        numbered paragraphs. A value of 1 indicates a header level
        format of X, a value of two implies X.X, etc. A value of zero
        means no header level.
        """
        self.level = level

    def get_header_level(self):
        "Returns the header level of the paragraph"
        return self.level

    def set_font(self,font):
        """
        Sets the font style of the paragraph.

        font - FontStyle object containing the font definition to use.
        """
        self.font = FontStyle(font)

    def get_font(self):
        "Returns the FontStyle of the paragraph"
        return self.font

    def set_padding(self,val):
        """
        Sets the paragraph padding in centimeters

        val - floating point value indicating the padding in centimeters
        """
        self.pad = val

    def get_padding(self):
        """Returns a the padding of the paragraph"""
        return self.pad

    def set_top_border(self,val):
        """
        Sets the presence or absence of top border.

        val - 1 indicates a border should be used, 0 indicates no border.
        """
        self.top_border = val

    def get_top_border(self):
        "Returns 1 if a top border is specified"
        return self.top_border

    def set_bottom_border(self,val):
        """
        Sets the presence or absence of bottom border.

        val - 1 indicates a border should be used, 0 indicates no border.
        """
        self.bottom_border = val

    def get_bottom_border(self):
        "Returns 1 if a bottom border is specified"
	return self.bottom_border

    def set_left_border(self,val):
        """
        Sets the presence or absence of left border.

        val - 1 indicates a border should be used, 0 indicates no border.
        """
        self.left_border = val

    def get_left_border(self):
        "Returns 1 if a left border is specified"
        return self.left_border

    def set_right_border(self,val):
        """
        Sets the presence or absence of rigth border.

        val - 1 indicates a border should be used, 0 indicates no border.
        """
        self.right_border = val

    def get_right_border(self):
        "Returns 1 if a right border is specified"
        return self.right_border

    def get_background_color(self):
        """
        Returns a tuple indicating the RGB components of the background
        color
        """
        return self.bgcolor

    def set_background_color(self,color):
        """
        Sets the background color of the paragraph.

        color - tuple representing the RGB components of a color (0,0,0)
                to (255,255,255)
        """
        self.bgcolor = color

    def set_alignment(self,align):
        """
        Sets the paragraph alignment.

        align - PARA_ALIGN_LEFT, PARA_ALIGN_RIGHT, PARA_ALIGN_CENTER, or
                PARA_ALIGN_JUSTIFY
        """
        self.align = align

    def get_alignment(self):
        "Returns the alignment of the paragraph"
        return self.align

    def get_alignment_text(self):
        """
        Returns a text string representing the alginment, either 'left',
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

    def set_left_margin(self,value):
	"sets the left paragraph margin in centimeters"
        self.lmargin = value

    def set_right_margin(self,value):
	"sets the right paragraph margin in centimeters"
        self.rmargin = value

    def set_first_indent(self,value):
	"sets the first indent margin in centimeters"
        self.first_indent = value

    def get_left_margin(self):
	"returns the left margin in centimeters"
        return self.lmargin

    def get_right_margin(self):
	"returns the right margin in centimeters"
        return self.rmargin

    def get_first_indent(self):
	"returns the first indent margin in centimeters"
        return self.first_indent

#------------------------------------------------------------------------
#
# StyleSheetList
#
#------------------------------------------------------------------------
class StyleSheetList:
    """
    Interface into the user's defined style sheets. Each StyleSheetList
    has a predefined default style specified by the report. Additional
    styles are loaded from a specified XML file if it exists.
    """
    
    def __init__(self,file,defstyle):
        """
        Creates a new StyleSheetList from the specified default style and
        any other styles that may be defined in the specified file.

        file - XML file that contains style definitions
        defstyle - default style
        """
        self.map = { "default" : defstyle }
        self.file = os.path.expanduser("~/.gramps/" + file)
        self.parse()

    def delete_style_sheet(self,name):
        """
        Removes a style from the list. Since each style must have a
        unique name, the name is used to delete the stylesheet.

        name - Name of the style to delete
        """
        del self.map[name]

    def get_style_sheet_map(self):
        """
        Returns the map of names to styles.
        """
        return self.map

    def get_style_sheet(self,name):
        """
        Returns the StyleSheet associated with the name

        name - name associated with the desired StyleSheet.
        """
        return self.map[name]

    def get_style_names(self):
        "Returns a list of all the style names in the StyleSheetList"
        return self.map.keys()

    def set_style_sheet(self,name,style):
        """
        Adds or replaces a StyleSheet in the StyleSheetList. The
        default style may not be replaced.

        name - name assocated with the StyleSheet to add or replace.
        style - definition of the StyleSheet
        """
        if name != "default":
            self.map[name] = style

    def save(self):
        """
        Saves the current StyleSheet definitions to the associated file.
        """
        f = open(self.file,"w")
        f.write("<?xml version=\"1.0\" encoding=\"iso-8859-1\"?>\n")
        f.write('<stylelist>\n')
        for name in self.map.keys():
            if name == "default":
                continue
            sheet = self.map[name]
            f.write('<sheet name="%s">\n' % name)
            for p_name in sheet.get_names():
                p = sheet.get_style(p_name)
                f.write('<style name="%s">\n' % p_name)
                font = p.get_font()
                f.write('<font face="%d" ' % font.get_type_face())
                f.write('size="%d" ' % font.get_size())
                f.write('italic="%d" ' % font.get_italic())
                f.write('bold="%d" ' % font.get_bold())
                f.write('underline="%d" ' % font.get_underline())
                f.write('color="#%02x%02x%02x"/>\n' % font.get_color())
                f.write('<para ')
                rm = float(p.get_right_margin())
                lm = float(p.get_left_margin())
                fi = float(p.get_first_indent())
                f.write('rmargin="%.3f" ' % rm)
                f.write('lmargin="%.3f" ' % lm)
                f.write('first="%.3f" ' % fi)
                f.write('pad="%.3f" ' % p.get_padding())
                f.write('bgcolor="#%02x%02x%02x" ' % p.get_background_color())
                f.write('level="%d" ' % p.get_header_level())
                f.write('align="%d" ' % p.get_alignment())
                f.write('tborder="%d" ' % p.get_top_border())
                f.write('lborder="%d" ' % p.get_left_border())
                f.write('rborder="%d" ' % p.get_right_border())
                f.write('bborder="%d"/>\n' % p.get_bottom_border())
                f.write('</style>\n')
            f.write('</sheet>\n')
        f.write('</stylelist>\n')
        f.close()
            
    def parse(self):
        """
        Loads the StyleSheets from the associated file, if it exists.
        """
        try:
            parser = make_parser()
            parser.setContentHandler(SheetParser(self))
            if self.file[0:7] != "file://":
                self.file = "file://" + self.file
            parser.parse(self.file)
        except (IOError,OSError,SAXParseException):
            pass
        
#------------------------------------------------------------------------
#
# StyleSheet
#
#------------------------------------------------------------------------
class StyleSheet:
    """
    A collection of named paragraph styles.
    """
    
    def __init__(self,obj=None):
        """
        Creates a new empty StyleSheet.

        obj - if not None, creates the StyleSheet from the values in
              obj, instead of creating an empty StyleSheet
        """
        self.style_list = {}
        if obj != None:
            for style_name in obj.style_list.keys():
                style = obj.style_list[style_name]
                self.style_list[style_name] = ParagraphStyle(style)

    def clear(self):
        "Removes all paragraph styles from the StyleSheet"
        self.style_list = {}

    def add_style(self,name,style):
        """
        Adds a paragraph style to the style sheet.

        name - name of the ParagraphStyle
        style - ParagraphStyle instance to be added.
        """
        self.style_list[name] = ParagraphStyle(style)

    def get_names(self):
        "Returns the the list of paragraph names in the StyleSheet"
        return self.style_list.keys()

    def get_styles(self):
        "Returns the paragraph name/ParagraphStyle map"
        return self.style_list

    def get_style(self,name):
        """
        Returns the ParagraphStyle associated with the name

        name - name of the ParagraphStyle that is wanted
        """
        return self.style_list[name]

#-------------------------------------------------------------------------
#
# SheetParser
#
#-------------------------------------------------------------------------
class SheetParser(handler.ContentHandler):
    """
    SAX parsing class for the StyleSheetList XML file.
    """
    
    def __init__(self,sheetlist):
        """
        Creates a SheetParser class that populates the passed StyleSheetList
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
        
    def startElement(self,tag,attrs):
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
            self.p.set_right_margin(float(attrs['rmargin']))
            self.p.set_left_margin(float(attrs['lmargin']))
            self.p.set_first_indent(float(attrs['first']))
            self.p.set_padding(float(attrs['pad']))
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

    def endElement(self,tag):
        "Overridden class that handles the start of a XML element"
        if tag == "style":
            self.p.set_font(self.f)
            self.s.add_style(self.pname,self.p)
        elif tag == "sheet":
            self.sheetlist.set_style_sheet(self.sname,self.s)
            
#------------------------------------------------------------------------
#
# TextDoc
#
#------------------------------------------------------------------------
class TextDoc:
    """
    Base class for text document generators. Different output formats,
    such as OpenOffice, AbiWord, and LaTeX are derived from this base
    class, providing a common interface to all document generators.
    """
    def __init__(self,styles,paper_type,template,orientation=PAPER_PORTRAIT):
        """
        Creates a TextDoc instance, which provides a document generation
        interface. This class should never be instantiated directly, but
        only through a derived class.

        styles      - StyleSheet containing the paragraph styles used.
        paper_type  - PaperStyle instance containing information about
                      the paper. If set to None, then the document is
                      not a page oriented document (e.g. HTML)
        template    - Format template for document generators that are
                      not page oriented.
        orientation - page orientation, either PAPER_PORTRAIT or
                      PAPER_LANDSCAPE
        """
        self.orientation = orientation
        self.template = template
        if orientation == PAPER_PORTRAIT:
            self.width = paper_type.get_width()
            self.height = paper_type.get_height()
        else:
            self.width = paper_type.get_height()
            self.height = paper_type.get_width()
        self.paper = paper_type
        self.tmargin = 2.54
        self.bmargin = 2.54
        self.lmargin = 2.54
        self.rmargin = 2.54
        self.title = ""
        self.owner = ''
                
        self.font = FontStyle()
        self.style_list = styles.get_styles()
	self.table_styles = {}
        self.cell_styles = {}
        self.name = ""
        self.photo_list = []

    def set_owner(self,owner):
        """
        Sets the name of the owner of the document.

        owner - User's name
        """
        self.owner = owner
        
    def add_photo(self,name,align,w_cm,h_cm):
        """
        Adds a photo of the specified width (in centimeters)

        name  - filename of the image to add
        align - alignment of the image. Valid values are 'left', 'right',
                'center', and 'single'
        w_cm  - width in centimeters
        h_cm  - height in centimeters
        """
        pass
    
    def get_usable_width(self):
        """
        Returns the width of the text area in centimeters. The value is
        the page width less the margins.
        """
        return self.width - (self.rmargin + self.lmargin)

    def get_usable_height(self):
        """
        Returns the height of the text area in centimeters. The value is
        the page height less the margins.
        """
        return self.height - (self.tmargin + self.bmargin)

    def creator(self,name):
        "Returns the owner name"
        self.name = name

    def set_title(self,name):
        """
        Sets the title of the document.

        name - Title of the document
        """
        self.title = name

    def add_table_style(self,name,style):
        """
        Adds the TableStyle with the specfied name.

        name  - name of the table style
        style - TableStyle instance to be added
        """
        self.table_styles[name] = TableStyle(style)

    def add_cell_style(self,name,style):
        """
        Adds the TableCellStyle with the specfied name.

        name  - name of the table cell style
        style - TableCellStyle instance to be added
        """
        self.cell_styles[name] = TableCellStyle(style)

    def open(self,filename):
        """
        Opens the document.

        filename - path name of the file to create
        """
        pass

    def close(self):
        "Closes the document"
        pass

    def line_break(self):
        "Forces a line break within a paragraph"
	pass

    def page_break(self):
        "Forces a page break, creating a new page"
        pass

    def start_bold(self):
        pass

    def end_bold(self):
        pass

    def start_listing(self,style_name):
        """
	Starts a new listing block, using the specified style name.

        style_name - name of the ParagraphStyle to use for the block.
	"""
        pass

    def end_listing(self):
        pass

    def start_paragraph(self,style_name,leader=None):
        """
        Starts a new paragraph, using the specified style name.

        style_name - name of the ParagraphStyle to use for the paragraph.
        leader     - Leading text for a paragraph. Typically used for numbering.
        """
        pass

    def end_paragraph(self):
        "Ends the current parsgraph"
        pass

    def start_table(self,name,style_name):
        """
        Starts a new table.

        name       - Unique name of the table.
        style_name - TableStyle to use for the new table
        """
        pass

    def end_table(self):
        "Ends the current table"
        pass

    def start_row(self):
        "Starts a new row on the current table"
        pass

    def end_row(self):
        "Ends the current row on the current table"
        pass

    def start_cell(self,style_name,span=1):
        """
        Starts a new table cell, using the paragraph style specified.

        style_name - TableCellStyle to use for the cell
        span       - number of columns to span
        """
        pass

    def end_cell(self):
        "Ends the current table cell"
        pass

    def horizontal_line(self):
        "Creates a horizontal line"
        pass

    def write_text(self,text):
        """
        Writes the text in the current paragraph. Should only be used after a
        start_paragraph and before an end_paragraph.

        text - text to write.
        """
        pass
