#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2005-2009  Serge Noiraud
# Copyright (C) 2007-2009  Brian G. Matherly
# Copyright (C) 2010       Peter Landgren
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
ODFDoc : used to generate Open Office Document
"""

#-------------------------------------------------------------------------
#
# pylint : disable messages ...
#
#-------------------------------------------------------------------------
# disable-msg=C0302 # Too many lines in module
# pylint: disable-msg=C0302
# disable-msg # Regular expression which should only match
# pylint: disable-msg=C0103
# disable-msg=R0902 # Too many instance attributes
# pylint: disable-msg=R0902
# disable-msg=R0904 # Too many public methods
# pylint: disable-msg=R0904
# disable-msg=R0912 # Too many branches
# pylint: disable-msg=R0912
# disable-msg=R0913 # Too many arguments
# pylint: disable-msg=R0913
# disable-msg=R0914 # Too many local variables
# pylint: disable-msg=R0914
# disable-msg=R0915 # Too many statements
# pylint: disable-msg=R0915
# warnings :
# disable-msg=W0613 # Unused argument
# pylint: disable-msg=W0613
# errors :
# disable-msg=E1101 # has no member
# pylint: disable-msg=E1101 

#-------------------------------------------------------------------------
#
# Standard Python Modules 
#
#-------------------------------------------------------------------------
import os
try:
    from hashlib import md5
except ImportError:
    from md5 import md5
import zipfile
import time
import locale
from cStringIO import StringIO
from math import pi, cos, sin
from xml.sax.saxutils import escape

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from gui.utils import open_file_with_default_application
from gen.plug.docgen import (BaseDoc, TextDoc, DrawDoc,
                    FONT_SANS_SERIF, DASHED, PAPER_PORTRAIT,
                    INDEX_TYPE_TOC, PARA_ALIGN_CENTER, PARA_ALIGN_LEFT, 
                    INDEX_TYPE_ALP, PARA_ALIGN_RIGHT)
from gen.plug.docgen.fontscale import string_width
from libodfbackend import OdfBackend
import const
from ReportBase import ReportUtils
import ImgManip
import Errors

#-------------------------------------------------------------------------
#
# internationalization
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _

_apptype = 'application/vnd.oasis.opendocument.text'

_esc_map = {
    '\x1a'           : '', 
    '\x0c'           : '', 
    '\n'             : '<text:line-break/>', 
    '\t'             : '<text:tab />',
    }

#-------------------------------------------------------------------------
#
# regexp for Styled Notes ...
#
#-------------------------------------------------------------------------
import re
NewStyle = re.compile('style-name="([a-zA-Z0-9]*)__([#a-zA-Z0-9 ]*)__">')

#-------------------------------------------------------------------------
#
# ODFDoc
#
#-------------------------------------------------------------------------
class ODFDoc(BaseDoc, TextDoc, DrawDoc):
    """
    The ODF document class
    """

    def __init__(self, styles, ftype):
        """
        Class init
        """
        BaseDoc.__init__(self, styles, ftype)
        self.media_list = []
        self.init_called = False
        self.cntnt = None
        self.cntnt1 = None
        self.cntnt2 = None
        self.cntntx = None
        self.sfile = None
        self.mimetype = None
        self.meta = None
        self.mfile = None
        self.filename = None
        self.lang = None
        self._backend = None
        self.span = 0
        self.level = 0
        self.time = "0000-00-00T00:00:00"
        self.new_page = 0
        self.new_cell = 0
        self.page = 0
        self.first_page = 1
        self.StyleList = [] # styles to create depending on styled notes.

    def open(self, filename):
        """
        Open the new document
        """
        t = time.localtime(time.time())
        self.time = "%04d-%02d-%02dT%02d:%02d:%02d" % t[:6]

        if filename[-4:] != ".odt":
            self.filename = filename + ".odt"
        else:
            self.filename = filename

        self.filename = os.path.normpath(os.path.abspath(self.filename))
        self._backend = OdfBackend()
        self.cntnt = StringIO()
        self.cntnt1 = StringIO()
        self.cntnt2 = StringIO()

    def init(self):
        """
        Create the document header
        """

        assert (not self.init_called)
        self.init_called = True
        
        current_locale = locale.getlocale()
        self.lang = current_locale[0]
        if self.lang:
            self.lang = self.lang.replace('_', '-')
        else:
            self.lang = "en-US"

        self.StyleList = [] # styles to create depending on styled notes.
        self.cntnt1.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.cntnt1.write('<office:document-content ')
        self.cntnt1.write('xmlns:office="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:office:1.0" ')
        self.cntnt1.write('xmlns:style="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:style:1.0" ')
        self.cntnt1.write('xmlns:text="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:text:1.0" ')
        self.cntnt1.write('xmlns:table="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:table:1.0" ')
        self.cntnt1.write('xmlns:draw="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:drawing:1.0" ')
        self.cntnt1.write('xmlns:fo="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:xsl-fo-compatible:1.0" ')
        self.cntnt1.write('xmlns:xlink="http://www.w3.org/1999/xlink" ')
        self.cntnt1.write('xmlns:dc="http://purl.org/dc/elements/1.1/" ')
        self.cntnt1.write('xmlns:meta="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:meta:1.0" ')
        self.cntnt1.write('xmlns:number="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:datastyle:1.0" ')
        self.cntnt1.write('xmlns:svg="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:svg-compatible:1.0" ')
        self.cntnt1.write('xmlns:chart="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:chart:1.0" ')
        self.cntnt1.write('xmlns:dr3d="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:dr3d:1.0" ')
        self.cntnt1.write('xmlns:math="http://www.w3.org/1998/Math/MathML" ')
        self.cntnt1.write('xmlns:form="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:form:1.0" ')
        self.cntnt1.write('xmlns:script="urn:oasis:names:tc:opendocument')
        self.cntnt1.write(':xmlns:script:1.0" ')
        self.cntnt1.write('xmlns:dom="http://www.w3.org/2001/xml-events" ')
        self.cntnt1.write('xmlns:xforms="http://www.w3.org/2002/xforms" ')
        #self.cntnt1.write('office:class="text" office:version="1.0">\n')
        self.cntnt1.write('office:version="1.0">\n')
        self.cntnt1.write('<office:scripts/>\n')
        self.cntnt1.write('<office:font-face-decls>\n')
        self.cntnt1.write('<style:font-face style:name="Courier" ')
        self.cntnt1.write('svg:font-family="Courier" ')
        self.cntnt1.write('style:font-family-generic="modern" ')
        self.cntnt1.write('style:font-pitch="fixed"/>\n')
        self.cntnt1.write('<style:font-face style:name="Times New Roman" ')
        self.cntnt1.write('svg:font-family="&apos;Times New Roman&apos;" ')
        self.cntnt1.write('style:font-family-generic="roman" ')
        self.cntnt1.write('style:font-pitch="variable"/>\n')
        self.cntnt1.write('<style:font-face style:name="Arial" ')
        self.cntnt1.write('svg:font-family="Arial" ')
        self.cntnt1.write('style:font-family-generic="swiss" ')
        self.cntnt1.write('style:font-pitch="variable"/>\n')
        self.cntnt2.write('</office:font-face-decls>\n')
        self.cntnt2.write('<office:automatic-styles>\n')
        self.cntnt2.write('<style:style style:name="docgen_page_break" ')
        self.cntnt2.write('style:family="paragraph" ')
        self.cntnt2.write('style:parent-style-name="Standard">\n')
        self.cntnt2.write('<style:paragraph-properties ')
        self.cntnt2.write('fo:break-before="page"/>\n')
        self.cntnt2.write('</style:style>\n')
        self.cntnt2.write('<style:style style:name="GSuper" ')
        self.cntnt2.write('style:family="text">')
        self.cntnt2.write('<style:text-properties ')
        self.cntnt2.write('style:text-position="super 58%"/>')
        self.cntnt2.write('</style:style>\n')
        self.cntnt2.write('<style:style style:name="GRAMPS-preformat" ')
        self.cntnt2.write('style:family="text">')
        self.cntnt2.write('<style:text-properties style:font-name="Courier"/>')
        self.cntnt2.write('</style:style>\n')
        
        styles = self.get_style_sheet()

        for style_name in styles.get_draw_style_names():
            style = styles.get_draw_style(style_name)
            self.cntnt.write('<style:style style:name="%s"' % style_name)
            self.cntnt.write(' style:family="graphic"')
            self.cntnt.write(' >\n')
            self.cntnt.write('<style:graphic-properties ')
                
            if style.get_line_width():
                self.cntnt.write('svg:stroke-width="%.2f" ' %
                                 (style.get_line_width()*10))
                self.cntnt.write('draw:marker-start="" ')
                self.cntnt.write('draw:marker-start-width="0.0" ')
                self.cntnt.write('draw:marker-end-width="0.0" ')
                self.cntnt.write('draw:stroke="solid" ')
                self.cntnt.write('draw:textarea-horizontal-align="center" ')
                self.cntnt.write('draw:textarea-vertical-align="middle" ')
            else:
                self.cntnt.write('draw:stroke="none" ')
                self.cntnt.write('draw:stroke-color="#000000" ')

            if style.get_line_style() == DASHED:
                self.cntnt.write('svg:fill-color="#cccccc" ')
            else:
                self.cntnt.write('svg:fill-color="#%02x%02x%02x" ' %
                                 style.get_color())
            self.cntnt.write('draw:fill-color="#%02x%02x%02x" ' %
                              style.get_fill_color())
            self.cntnt.write('draw:shadow="hidden" ')
            self.cntnt.write('style:run-through="foreground" ')
            self.cntnt.write('style:vertical-pos="from-top" ')
            self.cntnt.write('style:vertical-rel="paragraph" ')
            self.cntnt.write('style:horizontal-pos="from-left" ')
            self.cntnt.write('style:horizontal-rel="paragraph" ')
            self.cntnt.write('draw:wrap-influence-on-position=')
            self.cntnt.write('"once-concurrent" ')
            self.cntnt.write('style:flow-with-text="false" ')
            self.cntnt.write('/>\n')
            self.cntnt.write('</style:style>\n')

            self.cntnt.write('<style:style style:name="%s_shadow"' %
                             style_name)
            self.cntnt.write(' style:family="graphic">\n')
            self.cntnt.write('<style:graphic-properties ')
            self.cntnt.write('draw:stroke="none" ')
            self.cntnt.write('draw:fill="solid" ')
            self.cntnt.write('draw:fill-color="#cccccc" ')
            self.cntnt.write('draw:textarea-horizontal-align="center" ')
            self.cntnt.write('draw:textarea-vertical-align="middle" ')
            self.cntnt.write('draw:shadow="hidden" ')
            self.cntnt.write('style:run-through="foreground" ')
            self.cntnt.write('style:vertical-pos="from-top" ')
            self.cntnt.write('style:vertical-rel="paragraph" ')
            self.cntnt.write('style:horizontal-pos="from-left" ')
            self.cntnt.write('style:horizontal-rel="paragraph" ')
            self.cntnt.write('draw:wrap-influence-on-position=')
            self.cntnt.write('"once-concurrent" ')
            self.cntnt.write('style:flow-with-text="false" ')
            self.cntnt.write('/>\n')
            self.cntnt.write('</style:style>\n')

        # Graphic style for items with a clear background
        self.cntnt.write('<style:style style:name="clear" ')
        self.cntnt.write('style:family="graphic">\n')
        self.cntnt.write('<style:graphic-properties draw:stroke="none" ')
        self.cntnt.write('draw:fill="none" draw:shadow="hidden" ')
        self.cntnt.write('style:run-through="foreground" ')
        self.cntnt.write('style:vertical-pos="from-top" ')
        self.cntnt.write('style:vertical-rel="paragraph" ')
        self.cntnt.write('style:horizontal-pos="from-left" ')
        self.cntnt.write('style:horizontal-rel="paragraph" ')
        self.cntnt.write('draw:wrap-influence-on-position="once-concurrent" ')
        self.cntnt.write('style:flow-with-text="false"/>')
        self.cntnt.write('</style:style>\n')

        for style_name in styles.get_paragraph_style_names():
            style = styles.get_paragraph_style(style_name)

            self.cntnt.write('<style:style style:name="NL%s" ' % style_name)
            self.cntnt.write('style:family="paragraph" ')
            self.cntnt.write('style:parent-style-name="%s">\n' % style_name)
            self.cntnt.write('<style:paragraph-properties ')
            self.cntnt.write('fo:break-before="page"/>\n')
            self.cntnt.write('</style:style>\n')

            self.cntnt.write('<style:style style:name="X%s" ' % style_name)
            self.cntnt.write('style:family="paragraph"')
            self.cntnt.write('>\n')
            self.cntnt.write('<style:paragraph-properties ')

            if style.get_padding() != 0.0:
                self.cntnt.write('fo:padding="%.2fcm" ' % style.get_padding())
            if style.get_header_level() > 0:
                self.cntnt.write('fo:keep-with-next="true" ')

            align = style.get_alignment()
            if align == PARA_ALIGN_LEFT:
                self.cntnt.write('fo:text-align="start" ')
            elif align == PARA_ALIGN_RIGHT:
                self.cntnt.write('fo:text-align="end" ')
            elif align == PARA_ALIGN_CENTER:
                self.cntnt.write('fo:text-align="center" ')
                self.cntnt.write('style:justify-single-word="false" ')
            else:
                self.cntnt.write('fo:text-align="justify" ')
                self.cntnt.write('style:justify-single-word="false" ')
            font = style.get_font()
            if font.get_type_face() == FONT_SANS_SERIF:
                self.cntnt.write('style:font-name="Arial" ')
            else:
                self.cntnt.write('style:font-name="Times New Roman" ')
            self.cntnt.write('fo:font-size="%.2fpt" ' % font.get_size())
            self.cntnt.write('style:font-size-asian="%.2fpt" ' %
                             font.get_size())
            color = font.get_color()
            self.cntnt.write('fo:color="#%02x%02x%02x" ' % color)
            if font.get_bold():
                self.cntnt.write('fo:font-weight="bold" ')
            if font.get_italic():
                self.cntnt.write('fo:font-style="italic" ')
            if font.get_underline():
                self.cntnt.write('style:text-underline="single" ')
                self.cntnt.write('style:text-underline-color="font-color" ')
            self.cntnt.write('fo:text-indent="%.2fcm"\n' %
                             style.get_first_indent())
            self.cntnt.write('fo:margin-right="%.2fcm"\n' %
                             style.get_right_margin())
            self.cntnt.write('fo:margin-left="%.2fcm"\n' %
                             style.get_left_margin())
            self.cntnt.write('fo:margin-top="0.00cm"\n')
            self.cntnt.write('fo:margin-bottom="0.212cm" ')
            self.cntnt.write('/>\n')
            self.cntnt.write('</style:style>\n')

            self.cntnt.write('<style:style style:name="F%s" ' % style_name)
            self.cntnt.write('style:family="text">\n')
            self.cntnt.write('<style:text-properties ')
            align = style.get_alignment()
            if align == PARA_ALIGN_LEFT:
                self.cntnt.write('fo:text-align="start" ')
            elif align == PARA_ALIGN_RIGHT:
                self.cntnt.write('fo:text-align="end" ')
            elif align == PARA_ALIGN_CENTER:
                self.cntnt.write('fo:text-align="center" ')
                self.cntnt.write('style:justify-single-word="false" ')
            font = style.get_font()
            if font.get_type_face() == FONT_SANS_SERIF:
                self.cntnt.write('style:font-name="Arial" ')
            else:
                self.cntnt.write('style:font-name="Times New Roman" ')
            color = font.get_color()
            self.cntnt.write('fo:color="#%02x%02x%02x" ' % color)
            if font.get_bold():
                self.cntnt.write('fo:font-weight="bold" ')
            if font.get_italic():
                self.cntnt.write('fo:font-style="italic" ')
            self.cntnt.write('fo:font-size="%.2fpt" ' % font.get_size())
            self.cntnt.write('style:font-size-asian="%.2fpt"/> ' %
                             font.get_size())
            self.cntnt.write('</style:style>\n')

        for style_name in styles.get_table_style_names():
            style = styles.get_table_style(style_name)
            self.cntnt.write('<style:style style:name="%s" ' % style_name)
            self.cntnt.write('style:family="table-properties">\n')
            table_width = float(self.get_usable_width())
            table_width_str = "%.2f" % table_width
            self.cntnt.write('<style:table-properties-properties ')
            self.cntnt.write('style:width="%scm" '%table_width_str)
            self.cntnt.write('/>\n')
            self.cntnt.write('</style:style>\n')
            for col in range(0, style.get_columns()):
                self.cntnt.write('<style:style style:name="')
                self.cntnt.write(style_name + '.')
                self.cntnt.write(str(chr(ord('A')+col)) +'" ')
                self.cntnt.write('style:family="table-column">')
                width = table_width * float(style.get_column_width(col)/100.0)
                width_str = "%.4f" % width
                self.cntnt.write('<style:table-column-properties ')
                self.cntnt.write('style:column-width="%scm"/>' % width_str)
                self.cntnt.write('</style:style>\n')
                
        for cell in styles.get_cell_style_names():
            cell_style = styles.get_cell_style(cell)
            self.cntnt.write('<style:style style:name="%s" ' % cell)
            self.cntnt.write('style:family="table-cell">\n')
            self.cntnt.write('<style:table-cell-properties')
            self.cntnt.write(' fo:padding="%.2fcm"' % cell_style.get_padding())
            if cell_style.get_top_border():
                self.cntnt.write(' fo:border-top="0.002cm solid #000000"')
            else:
                self.cntnt.write(' fo:border-top="none"')
            if cell_style.get_bottom_border():
                self.cntnt.write(' fo:border-bottom="0.002cm solid #000000"')
            else:
                self.cntnt.write(' fo:border-bottom="none"')
            if cell_style.get_left_border():
                self.cntnt.write(' fo:border-left="0.002cm solid #000000"')
            else:
                self.cntnt.write(' fo:border-left="none"')
            if cell_style.get_right_border():
                self.cntnt.write(' fo:border-right="0.002cm solid #000000"')
            else:
                self.cntnt.write(' fo:border-right="none"')
            self.cntnt.write('/>\n')
            self.cntnt.write('</style:style>\n')
            
        self.cntnt.write('<style:style style:name="Tbold" ')
        self.cntnt.write('style:family="text">\n')
        self.cntnt.write('<style:text-properties fo:font-weight="bold"/>\n')
        self.cntnt.write('</style:style>\n')
        self.cntnt.write('<style:style style:name="Titalic" ')
        self.cntnt.write('style:family="text">\n')
        self.cntnt.write('<style:text-properties fo:font-style="italic"/>\n')
        self.cntnt.write('</style:style>\n')
        self.cntnt.write('<style:style style:name="Tunderline" ')
        self.cntnt.write('style:family="text">\n')
        self.cntnt.write('<style:text-properties ')
        self.cntnt.write('style:text-underline-style="solid" ')
        self.cntnt.write('style:text-underline-width="auto" ')
        self.cntnt.write('style:text-underline-color="font-color"/>')
        self.cntnt.write('</style:style>\n')

        #Begin photo style
        self.cntnt.write('<style:style style:name="Left" ')
        self.cntnt.write('style:family="graphic"')
        self.cntnt.write(' style:parent-style-name="photo">')
        self.cntnt.write('<style:graphic-properties ')
        self.cntnt.write('style:run-through="foreground"')
        self.cntnt.write(' style:wrap="dynamic"')
        self.cntnt.write(' style:number-wrapped-paragraphs="no-limit"')
        self.cntnt.write(' style:wrap-contour="false"')
        self.cntnt.write(' style:vertical-pos="from-top"')
        self.cntnt.write(' style:vertical-rel="paragraph-content"')
        self.cntnt.write(' style:horizontal-pos="left"')
        self.cntnt.write(' style:horizontal-rel="paragraph-content"')
        self.cntnt.write(' style:mirror="none" fo:clip="rect(0cm 0cm 0cm 0cm)"')
        self.cntnt.write(' draw:luminance="0%" draw:contrast="0" draw:red="0%"')
        self.cntnt.write(' draw:green="0%" draw:blue="0%" draw:gamma="1"')
        self.cntnt.write(' draw:color-inversion="false"')
        self.cntnt.write(' draw:transparency="-100%"')
        self.cntnt.write(' draw:color-mode="standard"/>')
        self.cntnt.write('</style:style>\n')

        self.cntnt.write('<style:style style:name="Right" ')
        self.cntnt.write('style:family="graphic"')
        self.cntnt.write(' style:parent-style-name="photo">')
        self.cntnt.write('<style:graphic-properties ')
        self.cntnt.write('style:run-through="foreground"')
        self.cntnt.write(' style:wrap="dynamic"')
        self.cntnt.write(' style:number-wrapped-paragraphs="no-limit"')
        self.cntnt.write(' style:wrap-contour="false" ')
        self.cntnt.write(' style:vertical-pos="from-top"')
        self.cntnt.write(' style:vertical-rel="paragraph-content"')
        self.cntnt.write(' style:horizontal-pos="right"')
        self.cntnt.write(' style:horizontal-rel="paragraph-content"')
        self.cntnt.write(' style:mirror="none" fo:clip="rect(0cm 0cm 0cm 0cm)"')
        self.cntnt.write(' draw:luminance="0%" draw:contrast="0" draw:red="0%"')
        self.cntnt.write(' draw:green="0%" draw:blue="0%" draw:gamma="1"')
        self.cntnt.write(' draw:color-inversion="false"')
        self.cntnt.write(' draw:transparency="-100%"')
        self.cntnt.write(' draw:color-mode="standard"/>')
        self.cntnt.write('</style:style>\n')

        self.cntnt.write('<style:style style:name="Single" ')
        self.cntnt.write('style:family="graphic"')
        self.cntnt.write(' style:parent-style-name="Graphics"> ')
        self.cntnt.write('<style:graphic-properties ')
        self.cntnt.write('style:vertical-pos="from-top"')
        self.cntnt.write(' style:mirror="none" fo:clip="rect(0cm 0cm 0cm 0cm)"')
        self.cntnt.write(' draw:luminance="0%" draw:contrast="0" draw:red="0%"')
        self.cntnt.write(' draw:green="0%" draw:blue="0%" draw:gamma="1"')
        self.cntnt.write(' draw:color-inversion="false"')
        self.cntnt.write(' draw:transparency="-100%"')
        self.cntnt.write(' draw:color-mode="standard"/> ')
        self.cntnt.write('</style:style>\n')

        self.cntnt.write('<style:style style:name="Row" style:family="graphic"')
        self.cntnt.write(' style:parent-style-name="Graphics">')
        self.cntnt.write('<style:graphic-properties ')
        self.cntnt.write('style:vertical-pos="from-top"')
        self.cntnt.write(' style:vertical-rel="paragraph"')
        self.cntnt.write(' style:horizontal-pos="from-left"')
        self.cntnt.write(' style:horizontal-rel="paragraph"')
        self.cntnt.write(' style:mirror="none" fo:clip="rect(0cm 0cm 0cm 0cm)"')
        self.cntnt.write(' draw:luminance="0%" draw:contrast="0" draw:red="0%"')
        self.cntnt.write(' draw:green="0%" draw:blue="0%" draw:gamma="1"')
        self.cntnt.write(' draw:color-inversion="false"')
        self.cntnt.write(' draw:transparency="-100%"')
        self.cntnt.write(' draw:color-mode="standard"/>')
        self.cntnt.write('</style:style>\n')

        #end of Photo style edits

        self.cntnt.write('</office:automatic-styles>\n')
        self.cntnt.write('<office:body>\n')
        self.cntnt.write(' <office:text>\n')
        self.cntnt.write(' <office:forms ')
        self.cntnt.write('form:automatic-focus="false" ')
        self.cntnt.write('form:apply-design-mode="false"/>\n')

    def uniq(self, List, funct=None):
        """
        We want no duplicate in the list
        """
        # order preserving
        if funct is None:
            def funct(x):
                """
                function used to compare elements
                """
                return x
        seen = {}
        result = []
        for item in List:
            marker = funct(item[0])
            if marker in seen: 
                continue
            seen[marker] = 1
            result.append(item)
        return result

    def finish_cntnt_creation(self):
        """
        We have finished the document.
        So me must integrate the new fonts and styles where they should be.
        The content.xml file is closed.
        """
        self.cntntx = StringIO()
        self.StyleList = self.uniq(self.StyleList)
        self.add_styled_notes_fonts()
        self.add_styled_notes_styles()
        self.cntntx.write(self.cntnt1.getvalue())
        self.cntntx.write(self.cntnt2.getvalue())
        self.cntntx.write(self.cntnt.getvalue())
        self.cntnt1.close()
        self.cntnt2.close()
        self.cntnt.close()

    def close(self):
        """
        Close the document and create the odt file
        """
        self.cntnt.write('</office:text>\n')
        self.cntnt.write('</office:body>\n')
        self.cntnt.write('</office:document-content>\n')
        self.finish_cntnt_creation()
        self._write_styles_file()
        self._write_manifest()
        self._write_meta_file()
        self._write_mimetype_file()
        self._write_zip()
        if self.open_req:
            open_file_with_default_application(self.filename)

    def add_styled_notes_fonts(self):
        """
        Add the new fonts for Styled notes in the font-face-decls section.
        """
        # Need to add new font for styled notes here.
        for style in self.StyleList:
            if ( style[1] == "FontFace" ):
                self.cntnt1.write('<style:font-face style:name="%s"' %
                                  style[2] )
                self.cntnt1.write(' svg:font-family="&apos;%s&apos;"' %
                                  style[2] )
                self.cntnt1.write(' style:font-pitch="fixed"/>\n')

    def add_styled_notes_styles(self):
        """
        Add the new styles for Styled notes in the automatic-styles section.
        """
        # Need to add new style for styled notes here.
        for style in self.StyleList:
            if ( style[1] == "FontSize" ):
                self.cntnt2.write('<style:style style:name="FontSize__%s__"' %
                                  style[2] )
                self.cntnt2.write(' style:family="text"> ')
                self.cntnt2.write('<style:text-properties fo:font-size="%spt"' %
                                   style[2])
                self.cntnt2.write(' style:font-size-asian="%spt"' % style[2])
                self.cntnt2.write(' style:font-size-complex="%spt"/>' %
                                  style[2])
                self.cntnt2.write('</style:style>\n')
            elif ( style[1] == "FontColor" ):
                self.cntnt2.write('<style:style style:name="FontColor__%s__"' %
                                  style[2] )
                self.cntnt2.write(' style:family="text">')
                self.cntnt2.write(' <style:text-properties fo:color="%s"/>' %
                                  style[2])
                self.cntnt2.write('</style:style>\n')
            elif ( style[1] == "FontHighlight" ):
                self.cntnt2.write('<style:style ')
                self.cntnt2.write('style:name="FontHighlight__%s__"' %
                                  style[2] )
                self.cntnt2.write(' style:family="text"> ')
                self.cntnt2.write('<style:text-properties ')
                self.cntnt2.write('fo:background-color="%s"/>' % style[2])
                self.cntnt2.write('</style:style>\n')
            elif ( style[1] == "FontFace" ):
                self.cntnt2.write('<style:style style:name="FontFace__%s__"' %
                                  style[2] )
                self.cntnt2.write(' style:family="text"> ')
                self.cntnt2.write('<style:text-properties ')
                self.cntnt2.write('style:font-name="%s"' % style[2] )
                self.cntnt2.write(' style:font-pitch="variable"/>')
                self.cntnt2.write('</style:style>\n')

    def add_media_object(self, file_name, pos, x_cm, y_cm, alt=''):
        """
        Add multi-media documents : photos
        """

        # try to open the image. If the open fails, it probably wasn't
        # a valid image (could be a PDF, or a non-image)
        (x, y) = ImgManip.image_size(file_name)
        if (x, y) == (0, 0):
            return
        
        ratio = float(x_cm)*float(y)/(float(y_cm)*float(x))
        if ratio < 1:
            act_width = x_cm
            act_height = y_cm*ratio
        else:
            act_height = y_cm
            act_width = x_cm/ratio
            
        not_extension, extension = os.path.splitext(file_name)
        odf_name = md5(file_name).hexdigest() + extension

        media_list_item = (file_name, odf_name)
        if not media_list_item in self.media_list:
            self.media_list.append(media_list_item)

        base = escape(os.path.basename(file_name))
        tag = base.replace('.', '_')
        
        if self.new_cell:
            self.cntnt.write('<text:p>')
        if pos == "left":
            self.cntnt.write('<draw:frame draw:style-name="Left" ')
        elif pos == "right":
            self.cntnt.write('<draw:frame draw:style-name="Right" ')
        elif pos == "single":
            self.cntnt.write('<draw:frame draw:style-name="Single" ')
        else:
            self.cntnt.write('<draw:frame draw:style-name="Row" ')

        self.cntnt.write('draw:name="%s" ' % tag)
        self.cntnt.write('text:anchor-type="paragraph" ')
        self.cntnt.write('svg:width="%.2fcm" ' % act_width)
        self.cntnt.write('svg:height="%.2fcm" ' % act_height)
        self.cntnt.write('draw:z-index="1" >')
        self.cntnt.write('<draw:image xlink:href="Pictures/')
        self.cntnt.write(odf_name)
        self.cntnt.write('" xlink:type="simple" xlink:show="embed" ')
        self.cntnt.write('xlink:actuate="onLoad"/>\n')
        self.cntnt.write('</draw:frame>\n')
        if self.new_cell:
            self.cntnt.write('</text:p>\n')

    def start_table(self, name, style_name):
        """
        open a table
        """
        self.cntnt.write('<table:table table:name="%s" ' % name)
        self.cntnt.write('table:style-name="%s">\n' % style_name)
        styles = self.get_style_sheet()
        table = styles.get_table_style(style_name)
        for col in range(0, table.get_columns()):
            self.cntnt.write('<table:table-column table:style-name="')
            self.cntnt.write(style_name + '.' + str(chr(ord('A')+col)) +'"/>\n')

    def end_table(self):
        """
        close a table
        """
        self.cntnt.write('</table:table>\n')

    def start_row(self):
        """
        open a row
        """
        self.cntnt.write('<table:table-row>\n')

    def end_row(self):
        """
        close a row
        """
        self.cntnt.write('</table:table-row>\n')

    def start_cell(self, style_name, span=1):
        """
        open a cell
        """
        self.span = span
        self.cntnt.write('<table:table-cell table:style-name="%s" ' %
                         style_name)
        self.cntnt.write('table:value-type="string"')
        if span > 1:
            self.cntnt.write(' table:number-columns-spanned="%s">\n' % span)
        else:             
            self.cntnt.write('>\n')
        self.new_cell = 1

    def end_cell(self):
        """
        close a cell
        """
        self.cntnt.write('</table:table-cell>\n')
        #for col in range(1, self.span):
        #    self.cntnt.write('<table:covered-table-cell/>\n')
        self.new_cell = 0

    def start_bold(self):
        """
        open bold
        """
        self.cntnt.write('<text:span text:style-name="Tbold">')

    def end_bold(self):
        """
        close bold
        """
        self.cntnt.write('</text:span>')
        
    def start_superscript(self):
        """
        open superscript
        """
        self.cntnt.write('<text:span text:style-name="GSuper">')

    def end_superscript(self):
        """
        close superscript
        """
        self.cntnt.write('</text:span>')

    def _add_zip(self, zfile, name, data, t):
        """
        Add a zip file to an archive
        """
        zipinfo = zipfile.ZipInfo(name.encode('utf-8'))
        zipinfo.date_time = t
        zipinfo.compress_type = zipfile.ZIP_DEFLATED
        zipinfo.external_attr = 0644 << 16L
        zfile.writestr(zipinfo, data)

    def _write_zip(self):
        """
        Create the odt file. This is a zip file
        """
        try:
            zfile = zipfile.ZipFile(self.filename, "w", zipfile.ZIP_DEFLATED)
        except IOError, msg:
            errmsg = "%s\n%s" % (_("Could not create %s") % self.filename, msg)
            raise Errors.ReportError(errmsg)
        except:
            raise Errors.ReportError(_("Could not create %s") % self.filename)
            
        t = time.localtime(time.time())[:6]

        self._add_zip(zfile, "META-INF/manifest.xml", self.mfile.getvalue(), t)
        self._add_zip(zfile, "content.xml", self.cntntx.getvalue(), t)
        self._add_zip(zfile, "meta.xml", self.meta.getvalue(), t)
        self._add_zip(zfile, "styles.xml", self.sfile.getvalue(), t)
        self._add_zip(zfile, "mimetype", self.mimetype.getvalue(), t)

        self.mfile.close()
        self.cntnt.close()
        self.meta.close()
        self.sfile.close()
        self.mimetype.close()
        
        for image in self.media_list:
            try:
                ifile = open(image[0], mode='rb')
                self._add_zip(zfile, "Pictures/%s" % image[1], ifile.read(), t)
                ifile.close()
            except:
                errmsg = "%s\n%s" % (_("Could not open %s") % image[0],
                                     msg)
                raise Errors.ReportError(errmsg)
        zfile.close()

    def _write_styles_file(self):
        """
        create the styles.xml file
        """
        self.sfile = StringIO()
                                     
        self.sfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.sfile.write('<office:document-styles ')
        self.sfile.write('xmlns:office="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:office:1.0" ')
        self.sfile.write('xmlns:style="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:style:1.0" ')
        self.sfile.write('xmlns:text="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:text:1.0" ')
        self.sfile.write('xmlns:table="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:table:1.0" ')
        self.sfile.write('xmlns:draw="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:drawing:1.0" ')
        self.sfile.write('xmlns:fo="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:xsl-fo-compatible:1.0" ')
        self.sfile.write('xmlns:xlink="http://www.w3.org/1999/xlink" ')
        self.sfile.write('xmlns:dc="http://purl.org/dc/elements/1.1/" ')
        self.sfile.write('xmlns:meta="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:meta:1.0" ')
        self.sfile.write('xmlns:number="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:datastyle:1.0" ')
        self.sfile.write('xmlns:svg="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:svg-compatible:1.0" ')
        self.sfile.write('xmlns:chart="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:chart:1.0" ')
        self.sfile.write('xmlns:dr3d="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:dr3d:1.0" ')
        self.sfile.write('xmlns:math="http://www.w3.org/1998/Math/MathML" ')
        self.sfile.write('xmlns:form="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:form:1.0" ')
        self.sfile.write('xmlns:script="urn:oasis:names:tc:opendocument')
        self.sfile.write(':xmlns:script:1.0" ')
        self.sfile.write('office:version="1.0">\n')
        self.sfile.write('<office:font-face-decls>\n')
        self.sfile.write('<style:font-face style:name="Times New Roman"')
        self.sfile.write(' svg:font-family="&apos;Times New Roman&apos;"')
        self.sfile.write(' style:font-family-generic="roman"')
        self.sfile.write(' style:font-pitch="variable"/>\n')
        self.sfile.write('<style:font-face style:name="Arial"')
        self.sfile.write(' svg:font-family="Arial"')
        self.sfile.write(' style:font-family-generic="swiss"')
        self.sfile.write(' style:font-pitch="variable"/>\n')
        self.sfile.write('</office:font-face-decls>\n')
        self.sfile.write('<office:styles>\n')
        self.sfile.write('<style:default-style ')
        self.sfile.write(' style:family="graphic">\n')
        self.sfile.write('<style:graphic-properties ')
        self.sfile.write(' draw:shadow-offset-x="0.3cm"') 
        self.sfile.write(' draw:shadow-offset-y="0.3cm" ')
        self.sfile.write(' draw:start-line-spacing-horizontal="0.283cm" ')
        self.sfile.write(' draw:start-line-spacing-vertical="0.283cm" ')
        self.sfile.write(' draw:end-line-spacing-horizontal="0.283cm" ')
        self.sfile.write(' draw:end-line-spacing-vertical="0.283cm" ')
        self.sfile.write(' style:flow-with-text="true"/>')
        self.sfile.write('<style:paragraph-properties ')
        self.sfile.write(' style:text-autospace="ideograph-alpha" ')
        self.sfile.write(' style:line-break="strict" ')
        self.sfile.write(' style:writing-mode="lr-tb" ')
        self.sfile.write(' style:font-independent-line-spacing="false">')
        self.sfile.write(' <style:tab-stops/>')
        self.sfile.write(' </style:paragraph-properties>')
        self.sfile.write('<style:text-properties ')
        self.sfile.write(' style:use-window-font-color="true" ')
        self.sfile.write(' fo:font-size="12pt" ')
        self.sfile.write(' style:font-size-asian="12pt" ')
        self.sfile.write(' style:language-asian="none" ')
        self.sfile.write(' style:country-asian="none" ')
        self.sfile.write(' style:font-size-complex="12pt" ')
        self.sfile.write(' style:language-complex="none" ')
        self.sfile.write(' style:country-complex="none"/>')
        self.sfile.write('</style:default-style>\n')
        self.sfile.write('<style:default-style ')
        self.sfile.write(' style:family="paragraph">\n')
        self.sfile.write(' <style:paragraph-properties\n')
        self.sfile.write(' style:text-autospace="ideograph-alpha"\n')
        self.sfile.write(' style:punctuation-wrap="hanging"\n')
        self.sfile.write(' style:line-break="strict"\n')
        self.sfile.write(' style:tab-stop-distance="2.205cm"\n')
        self.sfile.write(' style:writing-mode="page"/>\n')
        self.sfile.write('<style:text-properties \n')
        self.sfile.write('style:font-name="Times New Roman" ')
        self.sfile.write('fo:font-size="12pt" ')
        self.sfile.write('style:font-name-asian="Times New Roman" ')
        self.sfile.write('style:font-size-asian="12pt" ')
        self.sfile.write('style:font-name-complex="Times New Roman" ')
        self.sfile.write('style:font-size-complex="12pt" ')
        self.sfile.write('style:tab-stop-distance="2.205cm"/>\n')
        self.sfile.write('</style:default-style>\n')
        self.sfile.write('<style:default-style ')
        self.sfile.write(' style:family="table"> ')
        self.sfile.write(' <style:table-properties ')
        self.sfile.write('  table:border-model="separating"/> ')
        self.sfile.write('</style:default-style>\n')
        self.sfile.write('<style:default-style ')
        self.sfile.write(' style:family="table-row"> ')
        self.sfile.write(' <style:table-row-properties ')
        self.sfile.write('  fo:keep-together="auto"/> ')
        self.sfile.write('</style:default-style>\n')
        self.sfile.write('<style:style style:name="Standard" ')
        self.sfile.write('style:family="paragraph" style:class="text"/>\n')
        self.sfile.write('<style:style style:name="photo" ')
        self.sfile.write('style:family="graphic">\n')
        self.sfile.write('<style:graphic-properties ')
        self.sfile.write('text:anchor-type="paragraph" ')
        self.sfile.write('svg:x="0cm" svg:y="0cm" style:wrap="none" ')
        self.sfile.write('style:vertical-pos="top" ')
        self.sfile.write('style:vertical-rel="paragraph-content" ')
        self.sfile.write('style:horizontal-pos="center" ')
        self.sfile.write('style:horizontal-rel="paragraph-content"/>\n')
        self.sfile.write('</style:style>\n')
        
        styles = self.get_style_sheet()
        
        for style_name in styles.get_paragraph_style_names():
            style = styles.get_paragraph_style(style_name)
            self.sfile.write('<style:style style:name="%s" ' % style_name)
            self.sfile.write('style:family="paragraph" ')
            self.sfile.write('style:parent-style-name="Standard" ')
            self.sfile.write('style:class="text">\n')
            self.sfile.write('<style:paragraph-properties\n')
            self.sfile.write('fo:margin-left="%.2fcm"\n' %
                             style.get_left_margin())
            self.sfile.write('fo:margin-right="%.2fcm"\n' %
                             style.get_right_margin())
            self.sfile.write('fo:margin-top="0.00cm"\n')
            self.sfile.write('fo:margin-bottom="0.212cm"\n')

            if style.get_padding() != 0.0:
                self.sfile.write('fo:padding="%.2fcm" ' % style.get_padding())
            if style.get_header_level() > 0:
                self.sfile.write('fo:keep-with-next="always" ')

            align = style.get_alignment()
            if align == PARA_ALIGN_LEFT:
                self.sfile.write('fo:text-align="start" ')
                self.sfile.write('style:justify-single-word="false" ')
            elif align == PARA_ALIGN_RIGHT:
                self.sfile.write('fo:text-align="end" ')
            elif align == PARA_ALIGN_CENTER:
                self.sfile.write('fo:text-align="center" ')
                self.sfile.write('style:justify-single-word="false" ')
            else:
                self.sfile.write('fo:text-align="justify" ')
                self.sfile.write('style:justify-single-word="false" ')
            self.sfile.write('fo:text-indent="%.2fcm" ' %
                             style.get_first_indent())
            self.sfile.write('style:auto-text-indent="false"/> ')
            self.sfile.write('<style:text-properties ')
            font = style.get_font()
            color = font.get_color()
            self.sfile.write('fo:color="#%02x%02x%02x" ' % color)
            if font.get_type_face() == FONT_SANS_SERIF:
                self.sfile.write('style:font-name="Arial" ')
            else:
                self.sfile.write('style:font-name="Times New Roman" ')
            self.sfile.write('fo:font-size="%.0fpt" ' % font.get_size())
            if font.get_italic():
                self.sfile.write('fo:font-style="italic" ')
            if font.get_bold():
                self.sfile.write('fo:font-weight="bold" ')
            if font.get_underline():
                self.sfile.write('style:text-underline="single" ')
                self.sfile.write('style:text-underline-color="font-color" ')
                self.sfile.write('fo:text-indent="%.2fcm" ' %
                                 style.get_first_indent())
                self.sfile.write('fo:margin-right="%.2fcm" ' %
                                 style.get_right_margin())
                self.sfile.write('fo:margin-left="%.2fcm" ' %
                                 style.get_left_margin())
                self.sfile.write('fo:margin-top="0cm" ')
                self.sfile.write('fo:margin-bottom="0.212cm"')
            self.sfile.write('/>\n')
            self.sfile.write('</style:style>\n')

        # Current no leading number format for headers

        #self.sfile.write('<text:outline-style>\n')
        #self.sfile.write('<text:outline-level-style ')
        #self.sfile.write('text:level="1" style:num-format=""/>\n')
        #self.sfile.write('<text:outline-level-style ')
        #self.sfile.write('text:level="2" style:num-format=""/>\n')
        #self.sfile.write('<text:outline-level-style ')
        #self.sfile.write('text:level="3" style:num-format=""/>\n')
        #self.sfile.write('<text:outline-level-style ')
        #self.sfile.write('text:level="4" style:num-format=""/>\n')
        #self.sfile.write('<text:outline-level-style ')
        #self.sfile.write('text:level="5" style:num-format=""/>\n')
        #self.sfile.write('<text:outline-level-style ')
        #self.sfile.write('text:level="6" style:num-format=""/>\n')
        #self.sfile.write('<text:outline-level-style ')
        #self.sfile.write('text:level="7" style:num-format=""/>\n')
        #self.sfile.write('<text:outline-level-style ')
        #self.sfile.write('text:level="8" style:num-format=""/>\n')
        #self.sfile.write('<text:outline-level-style ')
        #self.sfile.write('text:level="9" style:num-format=""/>\n')
        #self.sfile.write('<text:outline-level-style ')
        #self.sfile.write('text:level="10" style:num-format=""/>\n')
        #self.sfile.write('</text:outline-style>\n')
            
        self.sfile.write('<text:notes-configuration  ')
        self.sfile.write('text:note-class="footnote"  ')
        self.sfile.write('style:num-format="1"  ')
        self.sfile.write('text:start-value="0"  ')
        self.sfile.write('text:footnotes-position="page"  ')
        self.sfile.write('text:start-numbering-at="document"/> ')
        self.sfile.write('<text:notes-configuration  ')
        self.sfile.write('text:note-class="endnote"  ')
        self.sfile.write('style:num-format="i"  ')
        self.sfile.write('text:start-value="0"/> ')
        self.sfile.write('<text:linenumbering-configuration  ')
        self.sfile.write('text:number-lines="false"  ')
        self.sfile.write('text:offset="0.499cm"  ')
        self.sfile.write('style:num-format="1"  ')
        self.sfile.write('text:number-position="left"  ')
        self.sfile.write('text:increment="5"/> ')
        self.sfile.write('</office:styles>\n')
        self.sfile.write('<office:automatic-styles>\n')
        self.sfile.write('<style:style style:name="S-Header" ')
        self.sfile.write('style:family="paragraph" ')
        self.sfile.write('style:parent-style-name="Standard">')
        self.sfile.write('<style:paragraph-properties fo:text-align="center" ')
        self.sfile.write('style:justify-single-word="false"/>')
        self.sfile.write('</style:style>\n')
        self.sfile.write('<style:style style:name="S-Footer" ')
        self.sfile.write('style:family="paragraph" ')
        self.sfile.write('style:parent-style-name="Header">')
        self.sfile.write('<style:paragraph-properties fo:text-align="center" ')
        self.sfile.write('style:justify-single-word="false"/>')
        self.sfile.write('</style:style>\n')
        self.sfile.write('<style:page-layout style:name="pm1">\n')
        self.sfile.write('<style:page-layout-properties ')
        self.sfile.write('fo:page-width="%.2fcm" ' %
                         self.paper.get_size().get_width())
        self.sfile.write('fo:page-height="%.2fcm" ' %
                         self.paper.get_size().get_height())
        self.sfile.write('style:num-format="1" ')
        if self.paper.get_orientation() == PAPER_PORTRAIT:
            self.sfile.write('style:print-orientation="portrait" ')
        else:
            self.sfile.write('style:print-orientation="landscape" ')
        self.sfile.write('fo:margin-top="%.2fcm" ' %
                         self.paper.get_top_margin())
        self.sfile.write('fo:margin-bottom="%.2fcm" ' %
                         self.paper.get_bottom_margin())
        self.sfile.write('fo:margin-left="%.2fcm" ' %
                         self.paper.get_left_margin())
        self.sfile.write('fo:margin-right="%.2fcm" ' %
                         self.paper.get_right_margin())
        self.sfile.write('style:writing-mode="lr-tb" ')
        self.sfile.write('style:footnote-max-height="0cm">\n')
        self.sfile.write('<style:footnote-sep style:width="0.018cm" ')
        self.sfile.write('style:distance-before-sep="0.101cm" ')
        self.sfile.write('style:distance-after-sep="0.101cm" ')
        self.sfile.write('style:adjustment="left" style:rel-width="25%" ')
        self.sfile.write('style:color="#000000"/>\n')
        self.sfile.write('</style:page-layout-properties>\n')
        # header
        self.sfile.write('<style:header-style>\n')
        self.sfile.write('<style:header-footer-properties ')
        self.sfile.write('fo:min-height="0cm" fo:margin-bottom="0.499cm"/>\n')
        self.sfile.write('</style:header-style>\n')
        # footer
        self.sfile.write('<style:footer-style>\n')
        self.sfile.write('<style:header-footer-properties ')
        self.sfile.write('fo:min-height="0cm" fo:margin-bottom="0.499cm"/>\n')
        self.sfile.write('</style:footer-style>\n')
        #
        self.sfile.write('</style:page-layout>\n')
        self.sfile.write('</office:automatic-styles>\n')
        self.sfile.write('<office:master-styles>\n')
        self.sfile.write('<style:master-page style:name="Standard" ')
        self.sfile.write('style:page-layout-name="pm1">\n')
        # header
        #self.sfile.write('<style:header>')
        #self.sfile.write('<text:p text:style-name="S-Header">')
        # How to get the document title here ?
        #self.sfile.write(' TITRE : %s' % self.title)
        #self.sfile.write('</text:p>')
        #self.sfile.write('</style:header>')
        # footer
        #self.sfile.write('<style:footer>')
        #self.sfile.write('<text:p text:style-name="S-Footer">')
        #self.sfile.write('<text:page-number text:select-page="current">1')
        #self.sfile.write('</text:page-number>/')
        #self.sfile.write('<text:page-count>1')
        #self.sfile.write('</text:page-count>')
        #self.sfile.write('</text:p>')
        #self.sfile.write('</style:footer>')
        #
        self.sfile.write('</style:master-page>')
        self.sfile.write('</office:master-styles>\n')
        self.sfile.write('</office:document-styles>\n')

    def page_break(self):
        """
        prepare a new page
        """
        self.new_page = 1

    def start_page(self):
        """
        create a new page
        """
        self.cntnt.write('<text:p text:style-name="docgen_page_break">\n')

    def end_page(self):
        """
        close the page
        """
        self.cntnt.write('</text:p>\n')
        
    def start_paragraph(self, style_name, leader=None):
        """
        open a new paragraph
        """
        style_sheet = self.get_style_sheet()
        style = style_sheet.get_paragraph_style(style_name)
        self.level = style.get_header_level()
        if self.new_page == 1:
            self.new_page = 0
            name = "NL%s" % style_name
        else:
            name = style_name
        if self.level == 0:
            self.cntnt.write('<text:p text:style-name="%s">' % name)
        else:
            self.cntnt.write('<text:h text:style-name="')
            self.cntnt.write(name)
            self.cntnt.write('" text:outline-level="' + str(self.level) + '">')
        if leader is not None:
            self.cntnt.write(leader)
            self.cntnt.write('<text:tab/>')
        self.new_cell = 0

    def end_paragraph(self):
        """
        close a paragraph
        """
        if self.level == 0:
            self.cntnt.write('</text:p>\n')
        else:
            self.cntnt.write('</text:h>\n')
        self.new_cell = 1

    def write_endnotes_ref(self, text, style_name):
        """
        Overwrite base method for lines of endnotes references
        """
        for line in text.split('\n'):
            text = escape(line, _esc_map)
            # Replace multiple spaces: have to go from the largest number down
            for n in range(text.count(' '), 1, -1):
                text = text.replace(' '*n, ' <text:s text:c="%d"/>' % (n-1) )
            self.start_paragraph(style_name)
#            self.cntnt.write('<text:span text:style-name="GRAMPS-preformat">')
            self.cntnt.write('<text:span text:style-name="Standard">')
            self.cntnt.write(text)
            self.cntnt.write('</text:span>')
            self.end_paragraph()

    def write_styled_note(self, styledtext, format, style_name):
        """
        Convenience function to write a styledtext to the latex doc. 
        styledtext : assumed a StyledText object to write
        format : = 0 : Flowed, = 1 : Preformatted
        style_name : name of the style to use for default presentation
        """
        text = str(styledtext)
        s_tags = styledtext.get_tags()
        text = text.replace('&', '\1') # must be the first
        text = text.replace('<', '\2')
        text = text.replace('>', '\3')
        markuptext = self._backend.add_markup_from_styled(text, s_tags)
        # we need to know if we have new styles to add.
        # if markuptext contains : FontColor, FontFace, FontSize ...
        # we must prepare the new styles for the styles.xml file.
        # We are looking for the following format :
        # style-name="([a-zA-Z0-9]*)__([a-zA-Z0-9 ])">
        # The first element is the StyleType and the second one is the value
        start = 0
        while 1:
            m = NewStyle.search(markuptext, start)
            if not m:
                break
            self.StyleList.append([m.group(1)+m.group(2),
                                  m.group(1),
                                  m.group(2)])
            start = m.end()
        linenb = 1
        self.start_paragraph(style_name)
        markuptext = markuptext.replace('\1', '&amp;') # must be the first
        markuptext = markuptext.replace('\2', '&lt;')
        markuptext = markuptext.replace('\3', '&gt;')
        for line in markuptext.split('\n'):
            if ( linenb > 1 ):
                self.cntnt.write('<text:line-break/>')
            self.cntnt.write(line)
            linenb += 1
        self.end_paragraph()

    def write_text(self, text, mark=None):
        """
        Uses the xml.sax.saxutils.escape function to convert XML
        entities. The _esc_map dictionary allows us to add our own
        mappings.
        """
        if mark:
            key = escape(mark.key, _esc_map)
            key = key.replace('"', '&quot;')
            if mark.type == INDEX_TYPE_ALP:
                self.cntnt.write('<text:alphabetical-index-mark ')
                self.cntnt.write('text:string-value="%s" />' % key)
            elif mark.type == INDEX_TYPE_TOC:
                self.cntnt.write('<text:toc-mark ')
                self.cntnt.write('text:string-value="%s" ' % key)
                self.cntnt.write('text:outline-level="%d" />' % mark.level)
        self.cntnt.write(escape(text, _esc_map))

    def _write_manifest(self):
        """
        create the manifest.xml file
        """
        self.mfile = StringIO()

        self.mfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.mfile.write('<manifest:manifest ')
        self.mfile.write('xmlns:manifest="urn:oasis:names:tc:opendocument')
        self.mfile.write(':xmlns:manifest:1.0">')
        self.mfile.write('<manifest:file-entry ')
        self.mfile.write('manifest:media-type="%s" ' % _apptype)
        self.mfile.write('manifest:full-path="/"/>')
        for image in self.media_list:
            self.mfile.write('<manifest:file-entry manifest:media-type="" ')
            self.mfile.write('manifest:full-path="Pictures/')
            self.mfile.write(image[1])
            self.mfile.write('"/>')
        self.mfile.write('<manifest:file-entry manifest:media-type="" ')
        self.mfile.write('manifest:full-path="Pictures/"/>')
        self.mfile.write('<manifest:file-entry manifest:media-type="text/xml" ')
        self.mfile.write('manifest:full-path="content.xml"/>')
        self.mfile.write('<manifest:file-entry manifest:media-type="text/xml" ')
        self.mfile.write('manifest:full-path="styles.xml"/>')
        self.mfile.write('<manifest:file-entry manifest:media-type="text/xml" ')
        self.mfile.write('manifest:full-path="meta.xml"/>')
        self.mfile.write('</manifest:manifest>\n')

    def _write_mimetype_file(self):
        """
        create the mimetype.xml file
        """
        self.mimetype = StringIO()
        self.mimetype.write('application/vnd.oasis.opendocument.text')

    def _write_meta_file(self):
        """
        create the meta.xml file
        """
        self.meta = StringIO()

        self.meta.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.meta.write('<office:document-meta ')
        self.meta.write('xmlns:office="urn:oasis:names:tc:opendocument')
        self.meta.write(':xmlns:office:1.0" ')
        self.meta.write('xmlns:xlink="http://www.w3.org/1999/xlink" ')
        self.meta.write('xmlns:dc="http://purl.org/dc/elements/1.1/" ')
        self.meta.write('xmlns:meta="urn:oasis:names:tc:opendocument')
        self.meta.write(':xmlns:meta:1.0" ')
        self.meta.write('office:version="1.0">\n')
        self.meta.write('<office:meta>\n')
        self.meta.write('<meta:generator>')
        self.meta.write(const.PROGRAM_NAME + ' ' + const.VERSION)
        self.meta.write('</meta:generator>\n')
        self.meta.write('<dc:title>')
        # It should be reasonable to have a true document title. but how ?
        # self.title ?
        #self.meta.write(_("Summary of %s") % self.name)
        self.meta.write('</dc:title>\n')
        self.meta.write('<dc:subject>')
        #self.meta.write(_("Summary of %s") % name)
        self.meta.write('</dc:subject>\n')
        self.meta.write('<dc:description>')
        self.meta.write('</dc:description>\n')
        self.meta.write('<meta:initial-creator>')
        self.meta.write(self.get_creator())
        self.meta.write('</meta:initial-creator>\n')
        self.meta.write('<meta:creation-date>')
        self.meta.write(self.time)
        self.meta.write('</meta:creation-date>\n')
        self.meta.write('<dc:creator>')
        self.meta.write(self.get_creator())
        self.meta.write('</dc:creator>\n')
        self.meta.write('<dc:date>')
        self.meta.write(self.time)
        self.meta.write('</dc:date>\n')
        #self.meta.write('<dc:keyword>')
        #self.meta.write('</dc:keyword>\n')
        self.meta.write('<meta:print-date>0-00-00T00:00:00</meta:print-date>\n')
        self.meta.write('<dc:language>%s</dc:language>\n' % self.lang)
        self.meta.write('<meta:editing-cycles>1</meta:editing-cycles>\n')
        self.meta.write('<meta:editing-duration>PT0S</meta:editing-duration>\n')
        self.meta.write('<meta:user-defined meta:name="Genealogical Research ')
        self.meta.write('and Analysis Management Programming System">')
        self.meta.write('http://gramps-project.org')
        self.meta.write('</meta:user-defined>\n')
        self.meta.write('<meta:user-defined meta:name="Info 1"/>\n')
        self.meta.write('<meta:user-defined meta:name="Info 2"/>\n')
        self.meta.write('<meta:user-defined meta:name="Info 3"/>\n')
        self.meta.write('</office:meta>\n')
        self.meta.write('</office:document-meta>\n')

    def rotate_text(self, style, text, x, y, angle):
        """
        Used to rotate a text with an angle.
        """
        style_sheet = self.get_style_sheet()
        stype = style_sheet.get_draw_style(style)
        pname = stype.get_paragraph_style()
        p = style_sheet.get_paragraph_style(pname)
        font = p.get_font()
        size = font.get_size()

        height = size*(len(text))
        width = 0
        for line in text:
            width = max(width, string_width(font, line))
        wcm = ReportUtils.pt2cm(width)
        hcm = ReportUtils.pt2cm(height)

        rangle = (pi/180.0) * angle

        self.cntnt.write('<draw:frame text:anchor-type="paragraph" ')
        self.cntnt.write('draw:z-index="2" ')
        self.cntnt.write('draw:style-name="clear" ')
        self.cntnt.write('svg:height="%.2fcm" ' % hcm)
        self.cntnt.write('svg:width="%.2fcm" ' % wcm)
        self.cntnt.write('draw:transform="')
        self.cntnt.write('rotate (%.8f) ' % -rangle)
        xloc = x-((wcm/2.0)*cos(rangle))+((hcm/2.0)*sin(rangle))
        yloc = y-((hcm/2.0)*cos(rangle))-((wcm/2.0)*sin(rangle))
        self.cntnt.write('translate (%.3fcm %.3fcm)">\n' % (xloc, yloc))
        self.cntnt.write('<draw:text-box>\n')
        self.cntnt.write('<text:p text:style-name="X%s">' % pname)
        self.cntnt.write('<text:span text:style-name="F%s">' % pname)
        self.cntnt.write(escape('\n'.join(text), _esc_map))
        self.cntnt.write('</text:span></text:p>\n</draw:text-box>\n')
        self.cntnt.write('</draw:frame>\n')
        
    def draw_path(self, style, path):
        """
        Draw a path
        """
        minx = 9e12
        miny = 9e12
        maxx = 0
        maxy = 0

        for point in path:
            minx = min(point[0], minx)
            miny = min(point[1], miny)
            maxx = max(point[0], maxx)
            maxy = max(point[1], maxy)

        self.cntnt.write('<draw:polygon draw:style-name="%s" ' % style )
        self.cntnt.write('draw:layer="layout" ')
        self.cntnt.write('draw:z-index="1" ')
        x = float(minx)
        y = float(miny)
        
        self.cntnt.write('svg:x="%2fcm" svg:y="%2fcm" ' % (x, y))
        self.cntnt.write('svg:viewBox="0 0 %d %d" ' % (int((maxx-minx)*1000),
                                                       int((maxy-miny)*1000)))
        self.cntnt.write('svg:width="%.4fcm" ' % (maxx-minx))
        self.cntnt.write('svg:height="%.4fcm" ' % (maxy-miny))
        
        point = path[0]
        x1 = int((point[0]-minx)*1000)
        y1 = int((point[1]-miny)*1000)
        self.cntnt.write('draw:points="%d, %d' % (x1, y1))

        for point in path[1:]:
            x1 = int((point[0]-minx)*1000)
            y1 = int((point[1]-miny)*1000)
            self.cntnt.write(' %d, %d' % (x1, y1))
        self.cntnt.write('"/>\n')

    def draw_line(self, style, x1, y1, x2, y2):
        """
        Draw a line
        """
        self.cntnt.write('<draw:line text:anchor-type="paragraph" ')
        self.cntnt.write('draw:z-index="3" ')
        self.cntnt.write('draw:text-style-name="%s" ' % style )
        self.cntnt.write('svg:x1="%.2fcm" ' % x1)
        self.cntnt.write('svg:y1="%.2fcm" ' % y1)
        self.cntnt.write('svg:x2="%.2fcm" ' % x2)
        self.cntnt.write('svg:y2="%.2fcm">' % y2)
        self.cntnt.write('<text:p/>\n')
        self.cntnt.write('</draw:line>\n')

    def draw_text(self, style, text, x, y):
        """
        Draw a text
        """
        style_sheet = self.get_style_sheet()
        box_style = style_sheet.get_draw_style(style)
        para_name = box_style.get_paragraph_style()
        pstyle = style_sheet.get_paragraph_style(para_name)
        font = pstyle.get_font()
        sw = ReportUtils.pt2cm(string_width(font, text))*1.3

        self.cntnt.write('<draw:frame text:anchor-type="paragraph" ')
        self.cntnt.write('draw:z-index="2" ')
        self.cntnt.write('draw:style-name="%s" ' % style)
        self.cntnt.write('svg:width="%.2fcm" ' % sw)
        self.cntnt.write('svg:height="%.2fcm" ' %
                         (ReportUtils.pt2cm(font.get_size()*1.4)))

        self.cntnt.write('svg:x="%.2fcm" ' % float(x))
        self.cntnt.write('svg:y="%.2fcm">' % float(y))
        self.cntnt.write('<draw:text-box> ' )
        self.cntnt.write('<text:p text:style-name="F%s">' % para_name)
        self.cntnt.write('<text:span text:style-name="F%s">' % para_name)
        #self.cntnt.write(' fo:max-height="%.2f">' % font.get_size() )
        self.cntnt.write(escape(text, _esc_map))
        self.cntnt.write('</text:span>')
        self.cntnt.write('</text:p>')
        self.cntnt.write('</draw:text-box>\n')
        self.cntnt.write('</draw:frame>\n')

    def draw_box(self, style, text, x, y, w, h):
        """
        Draw a box
        """
        style_sheet = self.get_style_sheet()
        box_style = style_sheet.get_draw_style(style)
        para_name = box_style.get_paragraph_style()
        shadow_width = box_style.get_shadow_space()

        if box_style.get_shadow():
            self.cntnt.write('<draw:rect text:anchor-type="paragraph" ')
            self.cntnt.write('draw:style-name="%s_shadow" ' % style)
            self.cntnt.write('draw:z-index="0" ')
            self.cntnt.write('draw:text-style-name="%s" ' % para_name)
            self.cntnt.write('svg:width="%.2fcm" ' % w)
            self.cntnt.write('svg:height="%.2fcm" ' % h)
            self.cntnt.write('svg:x="%.2fcm" ' % (float(x)+shadow_width))
            self.cntnt.write('svg:y="%.2fcm">\n' % (float(y)+shadow_width))
            self.cntnt.write('</draw:rect>\n')

        self.cntnt.write('<draw:rect text:anchor-type="paragraph" ')
        self.cntnt.write('draw:style-name="%s" ' % style)
        self.cntnt.write('draw:text-style-name="%s" ' % para_name)
        self.cntnt.write('draw:z-index="1" ')
        self.cntnt.write('svg:width="%.2fcm" ' % w)
        self.cntnt.write('svg:height="%.2fcm" ' % h)
        self.cntnt.write('svg:x="%.2fcm" ' % float(x))
        self.cntnt.write('svg:y="%.2fcm">\n' % float(y))
        if text != "":
            self.cntnt.write('<text:p text:style-name="%s">' % para_name)
            self.cntnt.write('<text:span text:style-name="F%s">' % para_name)
            self.cntnt.write(escape(text, _esc_map))
            self.cntnt.write('</text:span>')
            self.cntnt.write('</text:p>\n')
        self.cntnt.write('</draw:rect>\n')

    def center_text(self, style, text, x, y):
        """
        Center a text in a cell, a row, a line, ...
        """
        style_sheet = self.get_style_sheet()
        box_style = style_sheet.get_draw_style(style)
        para_name = box_style.get_paragraph_style()
        pstyle = style_sheet.get_paragraph_style(para_name)
        font = pstyle.get_font()

        size = (string_width(font, text)/72.0) * 2.54

        self.cntnt.write('<draw:frame text:anchor-type="paragraph" ')
        self.cntnt.write('draw:style-name="%s" ' % style)
        self.cntnt.write('draw:z-index="2" ')
        self.cntnt.write('svg:width="%.2fcm" ' % size)
        self.cntnt.write('svg:height="%.2fpt" ' % font.get_size())

        self.cntnt.write('svg:x="%.2fcm" ' % (x-(size/2.0)))
        self.cntnt.write('svg:y="%.2fcm">\n' % float(y))

        if text != "":
            self.cntnt.write('<draw:text-box>')
            self.cntnt.write('<text:p text:style-name="X%s">' % para_name)
            self.cntnt.write('<text:span text:style-name="F%s">' % para_name)
            self.cntnt.write(escape(text, _esc_map))
            self.cntnt.write('</text:span>\n')
            self.cntnt.write('</text:p>\n')
            self.cntnt.write('</draw:text-box>')
        self.cntnt.write('</draw:frame>\n')
