#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2005-2009  Serge Noiraud
# Copyright (C) 2007-2009  Brian G. Matherly
# Copyright (C) 2010       Peter Landgren
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
from math import pi, cos, sin, degrees, radians
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
from gen.plug.report import utils as ReportUtils
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
# Constants
#
#-------------------------------------------------------------------------

_XMLNS = '''\
xmlns:office="%(urn)soffice:1.0"
xmlns:style="%(urn)sstyle:1.0"
xmlns:text="%(urn)stext:1.0"
xmlns:table="%(urn)stable:1.0"
xmlns:draw="%(urn)sdrawing:1.0"
xmlns:fo="%(urn)sxsl-fo-compatible:1.0"
xmlns:xlink="http://www.w3.org/1999/xlink"
xmlns:dc="http://purl.org/dc/elements/1.1/"
xmlns:meta="%(urn)smeta:1.0"
xmlns:number="%(urn)sdatastyle:1.0"
xmlns:svg="%(urn)ssvg-compatible:1.0"
xmlns:chart="%(urn)schart:1.0"
xmlns:dr3d="%(urn)sdr3d:1.0"
xmlns:math="http://www.w3.org/1998/Math/MathML"
xmlns:form="%(urn)sform:1.0"
xmlns:script="%(urn)sscript:1.0"
xmlns:dom="http://www.w3.org/2001/xml-events"
xmlns:xforms="http://www.w3.org/2002/xforms"
''' % {"urn": "urn:oasis:names:tc:opendocument:xmlns:"}

_FONTS = '''\
<style:font-face style:name="Courier"
    svg:font-family="Courier"
    style:font-family-generic="modern"
    style:font-pitch="fixed"/>

<style:font-face style:name="Times New Roman"
    svg:font-family="&apos;Times New Roman&apos;"
    style:font-family-generic="roman"
    style:font-pitch="variable"/>

<style:font-face style:name="Arial"
    svg:font-family="Arial"
    style:font-family-generic="swiss"
    style:font-pitch="variable"/>
'''

_META_XML = '''\
<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta 
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" 
    xmlns:xlink="http://www.w3.org/1999/xlink" 
    xmlns:dc="http://purl.org/dc/elements/1.1/" 
    xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" 
    office:version="1.0">
<office:meta>
<meta:generator>
    %(generator)s
</meta:generator>
<dc:title>
</dc:title>
<dc:subject>
</dc:subject>
<dc:description>
</dc:description>
<meta:initial-creator>
    %(creator)s
</meta:initial-creator>
<meta:creation-date>
    %(date)s
</meta:creation-date>
<dc:creator>
    %(creator)s
</dc:creator>
<dc:date>
    %(date)s
</dc:date>
<meta:print-date>0-00-00T00:00:00</meta:print-date>
<dc:language>
    %(lang)s
</dc:language>
<meta:editing-cycles>1</meta:editing-cycles>
<meta:editing-duration>PT0S</meta:editing-duration>
<meta:user-defined
    meta:name="Genealogical Research and Analysis Management Programming System">
    http://gramps-project.org
</meta:user-defined>
<meta:user-defined meta:name="Info 1"/>
<meta:user-defined meta:name="Info 2"/>
<meta:user-defined meta:name="Info 3"/>
</office:meta>
</office:document-meta>
'''

_STYLES = '''\
<style:default-style 
    style:family="graphic">
    <style:graphic-properties 
        draw:shadow-offset-x="0.3cm"
        draw:shadow-offset-y="0.3cm" 
        draw:start-line-spacing-horizontal="0.283cm" 
        draw:start-line-spacing-vertical="0.283cm" 
        draw:end-line-spacing-horizontal="0.283cm" 
        draw:end-line-spacing-vertical="0.283cm" 
        style:flow-with-text="true"/>
    <style:paragraph-properties 
        style:text-autospace="ideograph-alpha" 
        style:line-break="strict" 
        style:writing-mode="lr-tb" 
        style:font-independent-line-spacing="false">
        <style:tab-stops/>
    </style:paragraph-properties>
    <style:text-properties 
        style:use-window-font-color="true" 
        fo:font-size="12pt" 
        style:font-size-asian="12pt" 
        style:language-asian="none" 
        style:country-asian="none" 
        style:font-size-complex="12pt" 
        style:language-complex="none" 
        style:country-complex="none"/>
</style:default-style>

<style:default-style 
     style:family="paragraph">
     <style:paragraph-properties
         style:text-autospace="ideograph-alpha"
         style:punctuation-wrap="hanging"
         style:line-break="strict"
         style:tab-stop-distance="2.205cm"
         style:writing-mode="page"/>
    <style:text-properties 
        style:font-name="Times New Roman" 
        fo:font-size="12pt" 
        style:font-name-asian="Times New Roman" 
        style:font-size-asian="12pt" 
        style:font-name-complex="Times New Roman" 
        style:font-size-complex="12pt" 
        style:tab-stop-distance="2.205cm"/>
</style:default-style>

<style:default-style 
     style:family="table"> 
     <style:table-properties 
        table:border-model="separating"/> 
</style:default-style>

<style:default-style 
    style:family="table-row"> 
    <style:table-row-properties 
        fo:keep-together="auto"/> 
</style:default-style>

<style:style style:name="Standard" 
    style:family="paragraph" style:class="text"/>

<style:style style:name="photo" 
    style:family="graphic">
    <style:graphic-properties 
        text:anchor-type="paragraph" 
        svg:x="0cm" svg:y="0cm" style:wrap="none" 
        style:vertical-pos="top" 
        style:vertical-rel="paragraph-content" 
        style:horizontal-pos="center" 
        style:horizontal-rel="paragraph-content"/>
</style:style>
'''

_AUTOMATIC_STYLES = '''\
<style:style style:name="docgen_page_break"
    style:family="paragraph"
    style:parent-style-name="Standard">
    <style:paragraph-properties
        fo:break-before="page"/>
</style:style>

<style:style style:name="GSuper"
    style:family="text">
    <style:text-properties
        style:text-position="super 58%"/>
</style:style>

<style:style style:name="GRAMPS-preformat"
    style:family="text">
    <style:text-properties
        style:font-name="Courier"/>
</style:style>
'''

_CLEAR_STYLE = '''\
<style:style style:name="clear"
    style:family="graphic">\n
    <style:graphic-properties draw:stroke="none"
        draw:fill="none" draw:shadow="hidden"
        style:run-through="foreground"
        style:vertical-pos="from-top"
        style:vertical-rel="paragraph"
        style:horizontal-pos="from-left"
        style:horizontal-rel="paragraph"
        draw:wrap-influence-on-position="once-concurrent"
        style:flow-with-text="false"/>
</style:style>\n
'''
_OTHER_STYLES = '''\
<style:style style:name="Tbold" 
    style:family="text">\n
    <style:text-properties fo:font-weight="bold"/>\n
</style:style>\n

<style:style style:name="Titalic"
    style:family="text">\n
    <style:text-properties fo:font-style="italic"/>\n
</style:style>\n

<style:style style:name="Tunderline"
    style:family="text">\n
    <style:text-properties
        style:text-underline-style="solid"
        style:text-underline-width="auto"
        style:text-underline-color="font-color"/>
</style:style>\n

<style:style style:name="Left"
    style:family="graphic"
     style:parent-style-name="photo">
    <style:graphic-properties
        style:run-through="foreground"
         style:wrap="dynamic"
         style:number-wrapped-paragraphs="no-limit"
         style:wrap-contour="false"
         style:vertical-pos="from-top"
         style:vertical-rel="paragraph-content"
         style:horizontal-pos="left"
         style:horizontal-rel="paragraph-content"
         style:mirror="none" fo:clip="rect(0cm 0cm 0cm 0cm)"
         draw:luminance="0%" draw:contrast="0" draw:red="0%"
         draw:green="0%" draw:blue="0%" draw:gamma="1"
         draw:color-inversion="false"
         draw:transparency="-100%"
         draw:color-mode="standard"/>
</style:style>\n

<style:style style:name="Right"
    style:family="graphic"
     style:parent-style-name="photo">
    <style:graphic-properties
        style:run-through="foreground"
         style:wrap="dynamic"
         style:number-wrapped-paragraphs="no-limit"
         style:wrap-contour="false"
         style:vertical-pos="from-top"
         style:vertical-rel="paragraph-content"
         style:horizontal-pos="right"
         style:horizontal-rel="paragraph-content"
         style:mirror="none" fo:clip="rect(0cm 0cm 0cm 0cm)"
         draw:luminance="0%" draw:contrast="0" draw:red="0%"
         draw:green="0%" draw:blue="0%" draw:gamma="1"
         draw:color-inversion="false"
         draw:transparency="-100%"
         draw:color-mode="standard"/>
</style:style>\n

<style:style style:name="Single"
    style:family="graphic"
     style:parent-style-name="Graphics">
    <style:graphic-properties
        style:vertical-pos="from-top"
         style:mirror="none" fo:clip="rect(0cm 0cm 0cm 0cm)"
         draw:luminance="0%" draw:contrast="0" draw:red="0%"
         draw:green="0%" draw:blue="0%" draw:gamma="1"
         draw:color-inversion="false"
         draw:transparency="-100%"
         draw:color-mode="standard"/>
</style:style>\n

<style:style style:name="Row" style:family="graphic"
     style:parent-style-name="Graphics">
    <style:graphic-properties
        style:vertical-pos="from-top"
         style:vertical-rel="paragraph"
         style:horizontal-pos="from-left"
         style:horizontal-rel="paragraph"
         style:mirror="none" fo:clip="rect(0cm 0cm 0cm 0cm)"
         draw:luminance="0%" draw:contrast="0" draw:red="0%"
         draw:green="0%" draw:blue="0%" draw:gamma="1"
         draw:color-inversion="false"
         draw:transparency="-100%"
         draw:color-mode="standard"/>
</style:style>\n
'''

_SHEADER_FOOTER = '''\
<style:style style:name="S-Header"
    style:family="paragraph"
    style:parent-style-name="Standard">
    <style:paragraph-properties fo:text-align="center"
        style:justify-single-word="false"/>
</style:style>\n
<style:style style:name="S-Footer"
    style:family="paragraph"
    style:parent-style-name="Header">
    <style:paragraph-properties fo:text-align="center"
        style:justify-single-word="false"/>
</style:style>\n
'''

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

        self.filename = filename
        if not filename.endswith("odt"):
            self.filename += ".odt"

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
        wrt = self.cntnt.write
        wrt1, wrt2 = self.cntnt1.write, self.cntnt2.write
        
        current_locale = locale.getlocale()
        self.lang = current_locale[0]
        self.lang = self.lang.replace('_', '-') if self.lang else "en-US"

        self.StyleList = [] # styles to create depending on styled notes.
        wrt1('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<office:document-content\n' +
            _XMLNS +
            'office:version="1.0">\n' +
            '<office:scripts/>\n'
            )
        wrt1('<office:font-face-decls>\n' +
            _FONTS
            )
        wrt2(
            '</office:font-face-decls>\n' +
            '<office:automatic-styles>\n' +
                _AUTOMATIC_STYLES
            )
        
        styles = self.get_style_sheet()

        for style_name in styles.get_draw_style_names():
            style = styles.get_draw_style(style_name)
            wrt(
                '<style:style ' +
                    'style:name="%s" ' % style_name +
                    'style:family="graphic">\n'
                    '<style:graphic-properties '
                )
                
            if style.get_line_width():
                wrt(
                    'svg:stroke-width="%.2f" '
                        % (style.get_line_width()*10) +
                    'draw:marker-start="" ' 
                    'draw:marker-start-width="0.0" '
                    'draw:marker-end-width="0.0" '
                    'draw:stroke="solid" '
                    'draw:textarea-horizontal-align="center" '
                    'draw:textarea-vertical-align="middle" '
                    )
            else:
                wrt(
                    'draw:stroke="none" '
                    'draw:stroke-color="#000000" '
                    )

            if style.get_line_style() == DASHED:
                wrt('svg:fill-color="#cccccc" ')
            else:
                wrt('svg:fill-color="#%02x%02x%02x" '
                    % style.get_color())

            wrt(
                'draw:fill-color="#%02x%02x%02x" '
                    % style.get_fill_color() +
                'draw:shadow="hidden" '
                'style:run-through="foreground" '
                'style:vertical-pos="from-top" '
                'style:vertical-rel="paragraph" '
                'style:horizontal-pos="from-left" '
                'style:horizontal-rel="paragraph" '
                'draw:wrap-influence-on-position='
                '"once-concurrent" '
                'style:flow-with-text="false" '
                '/>\n'
                '</style:style>\n'
                )

            wrt(
                '<style:style '
                    'style:name="%s_shadow" ' %  style_name +
                    'style:family="graphic">\n'
                    '<style:graphic-properties '
                        'draw:stroke="none" '
                        'draw:fill="solid" '
                        'draw:fill-color="#cccccc" '
                        'draw:textarea-horizontal-align="center" '
                        'draw:textarea-vertical-align="middle" '
                        'draw:shadow="hidden" '
                        'style:run-through="foreground" '
                        'style:vertical-pos="from-top" '
                        'style:vertical-rel="paragraph" '
                        'style:horizontal-pos="from-left" '
                        'style:horizontal-rel="paragraph" '
                        'draw:wrap-influence-on-position='
                        '"once-concurrent" '
                        'style:flow-with-text="false" '
                        '/>\n'
                '</style:style>\n'
                )

        # Graphic style for items with a clear background
        wrt(
            _CLEAR_STYLE
            )

        for style_name in styles.get_paragraph_style_names():
            style = styles.get_paragraph_style(style_name)

            wrt(
                '<style:style style:name="NL%s" ' % style_name +
                    'style:family="paragraph" ' +
                    'style:parent-style-name="%s">\n' % style_name +
                    '<style:paragraph-properties ' +
                        'fo:break-before="page"/>\n' +
                '</style:style>\n' +
    
                '<style:style style:name="X%s" ' % style_name +
                    'style:family="paragraph"' +
                    '>\n' +
                    '<style:paragraph-properties '
                )

            if style.get_padding() != 0.0:
                wrt('fo:padding="%.2fcm" ' % style.get_padding())
            if style.get_header_level() > 0:
                wrt('fo:keep-with-next="auto" ')

            align = style.get_alignment()
            if align == PARA_ALIGN_LEFT:
                wrt('fo:text-align="start" ')
            elif align == PARA_ALIGN_RIGHT:
                wrt('fo:text-align="end" ')
            elif align == PARA_ALIGN_CENTER:
                wrt(
                    'fo:text-align="center" ' 
                    'style:justify-single-word="false" '
                    )
            else:
                wrt(
                    'fo:text-align="justify" '
                    'style:justify-single-word="false" '
                    )
            font = style.get_font()
            wrt('style:font-name="%s" ' %
                ("Arial"
                    if font.get_type_face() == FONT_SANS_SERIF else
                "Times New Roman")
                )

            wrt(
                'fo:font-size="%.2fpt" ' % font.get_size() +
                'style:font-size-asian="%.2fpt" ' % font.get_size() +
                'fo:color="#%02x%02x%02x" ' % font.get_color()
                )

            if font.get_bold():
                wrt('fo:font-weight="bold" ')
            if font.get_italic():
                wrt('fo:font-style="italic" ')
            if font.get_underline():
                wrt(
                    'style:text-underline="single" '
                    'style:text-underline-color="font-color" '
                    )

            wrt(
                'fo:text-indent="%.2fcm"\n' % style.get_first_indent() +
                'fo:margin-right="%.2fcm"\n' % style.get_right_margin() +
                'fo:margin-left="%.2fcm"\n' % style.get_left_margin() +
                'fo:margin-top="%.2fcm"\n' % style.get_top_margin() +
                'fo:margin-bottom="%.2fcm"\n' % style.get_bottom_margin() +
                '/>\n' +
                '</style:style>\n'
                )

            wrt(
                '<style:style style:name="F%s" ' % style_name +
                    'style:family="text">\n' +
                    '<style:text-properties '
                )

            align = style.get_alignment()
            if align == PARA_ALIGN_LEFT:
                wrt('fo:text-align="start" ')
            elif align == PARA_ALIGN_RIGHT:
                wrt('fo:text-align="end" ')
            elif align == PARA_ALIGN_CENTER:
                wrt(
                    'fo:text-align="center" '
                    'style:justify-single-word="false" '
                    )

            font = style.get_font()
            wrt('style:font-name="%s" ' %
                ("Arial"
                    if font.get_type_face() == FONT_SANS_SERIF else
                "Times New Roman")
               )

            color = font.get_color()
            wrt('fo:color="#%02x%02x%02x" ' % color)
            if font.get_bold():
                wrt('fo:font-weight="bold" ')
            if font.get_italic():
                wrt('fo:font-style="italic" ')

            wrt(
                'fo:font-size="%.2fpt" ' % font.get_size() +
                'style:font-size-asian="%.2fpt"/> ' % font.get_size() +
                '</style:style>\n'
                )

        for style_name in styles.get_table_style_names():
            style = styles.get_table_style(style_name)
            table_width = float(self.get_usable_width())
            table_width_str = "%.2f" % table_width
            wrt(
                '<style:style style:name="%s" ' % style_name +
                'style:family="table-properties">\n'
                '<style:table-properties-properties ' +
                    'style:width="%scm" ' % table_width_str +
                    '/>\n' +
                '</style:style>\n'
                )

            for col in range(0, min(style.get_columns(), 50)):
                width = table_width * float(style.get_column_width(col) / 100.0)
                width_str = "%.4f" % width
                wrt(
                    '<style:style style:name="%s.%s" '
                            % (style_name, chr(ord('A')+col)) +
                        'style:family="table-column">' +
                        '<style:table-column-properties ' + 
                            'style:column-width="%scm"/>' % width_str +
                    '</style:style>\n'
                    )
                
        for cell in styles.get_cell_style_names():
            cell_style = styles.get_cell_style(cell)
            wrt(
                '<style:style style:name="%s" ' % cell +
                'style:family="table-cell">\n' +
                '<style:table-cell-properties' +
                    ' fo:padding="%.2fcm"' % cell_style.get_padding()
                )
            wrt(' fo:border-top="%s"' %
                ("0.002cm solid #000000"
                    if cell_style.get_top_border() else
                "none")
               ) 

            wrt(' fo:border-bottom="%s"' %
                ("0.002cm solid #000000"
                    if cell_style.get_bottom_border() else
                "none")
               )

            wrt(' fo:border-left="%s"' %
                ("0.002cm solid #000000"
                    if cell_style.get_left_border() else
                "none")
               ) 

            wrt(' fo:border-right="%s"' %
                ("0.002cm solid #000000"
                    if cell_style.get_right_border() else
                "none")
               )  

            wrt(
                '/>\n' 
                '</style:style>\n'
                )
            
        wrt(
            _OTHER_STYLES
            )

        wrt(
            '</office:automatic-styles>\n'
            '<office:body>\n'
            ' <office:text>\n'
            ' <office:forms '
            'form:automatic-focus="false" '
            'form:apply-design-mode="false"/>\n'
            )

    def uniq(self, list_, funct=None):
        """
        We want no duplicate in the list
        """
        # order preserving
        funct = funct or (lambda x:x)
        seen = set()
        result = []
        for item in list_:
            marker = funct(item[0])
            if marker in seen: 
                continue
            seen.add(marker)
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
        self.cntnt.write(
            '</office:text>\n' 
            '</office:body>\n' 
            '</office:document-content>\n'
            )
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
        wrt1 = self.cntnt1.write
        for style in self.StyleList:
            if style[1] == "FontFace":
                wrt1(
                    '<style:font-face ' +
                        'style:name="%s" ' %  style[2] +
                        'svg:font-family="&apos;%s&apos;" ' % style[2] +
                        'style:font-pitch="fixed"/>\n'
                    )

    def add_styled_notes_styles(self):
        """
        Add the new styles for Styled notes in the automatic-styles section.
        """
        # Need to add new style for styled notes here.
        wrt2 = self.cntnt2.write
        for style in self.StyleList:
            if style[1] == "FontSize":
                wrt2(
                    '<style:style ' +
                        'style:name="FontSize__%s__" ' % style[2] +
                        'style:family="text"> ' +
                        '<style:text-properties ' +
                            'fo:font-size="%spt" ' % style[2] +
                            'style:font-size-asian="%spt" ' % style[2] +
                            'style:font-size-complex="%spt"/>' %  style[2] +
                    '</style:style>\n'
                    )

            elif style[1] == "FontColor":
                wrt2(
                    '<style:style ' +
                        'style:name="FontColor__%s__" ' % style[2] +
                        'style:family="text">' +
                        ' <style:text-properties ' +
                            'fo:color="%s"/>' % style[2] +
                    '</style:style>\n'
                    )

            elif style[1] == "FontHighlight":
                wrt2(
                    '<style:style ' +
                        'style:name="FontHighlight__%s__" ' % style[2]  +
                        'style:family="text"> ' +
                        '<style:text-properties ' +
                            'fo:background-color="%s"/>' % style[2] +
                    '</style:style>\n'
                    )

            elif style[1] == "FontFace":
                wrt2(
                    '<style:style ' +
                        'style:name="FontFace__%s__" ' % style[2] +
                        'style:family="text"> ' +
                        '<style:text-properties ' +
                            'style:font-name="%s" ' % style[2]  +
                            'style:font-pitch="variable"/>' +
                    '</style:style>\n'
                    )

    def add_media_object(self, file_name, pos, x_cm, y_cm, alt=''):
        """
        Add multi-media documents : photos
        """

        # try to open the image. If the open fails, it probably wasn't
        # a valid image (could be a PDF, or a non-image)
        (x, y) = ImgManip.image_size(file_name)
        if (x, y) == (0, 0):
            return
        
        ratio = float(x_cm) * float(y) / (float(y_cm) * float(x))
        if ratio < 1:
            act_width = x_cm
            act_height = y_cm * ratio
        else:
            act_height = y_cm
            act_width = x_cm / ratio
            
        not_extension, extension = os.path.splitext(file_name)
        odf_name = md5(file_name).hexdigest() + extension

        media_list_item = (file_name, odf_name)
        if not media_list_item in self.media_list:
            self.media_list.append(media_list_item)

        base = escape(os.path.basename(file_name))
        tag = base.replace('.', '_')
        
        if self.new_cell:
            self.cntnt.write('<text:p>')

        pos = pos.title() if pos in ['left', 'right', 'single'] else 'Row'
        self.cntnt.write(
            '<draw:frame draw:style-name="%s" ' % pos +
                'draw:name="%s" ' % tag +
                'text:anchor-type="paragraph" ' +
                'svg:width="%.2fcm" ' % act_width +
                'svg:height="%.2fcm" ' % act_height +
                'draw:z-index="1" >' +
                '<draw:image xlink:href="Pictures/%s" ' % odf_name +
                    'xlink:type="simple" xlink:show="embed" ' +
                    'xlink:actuate="onLoad"/>\n' +
            '</draw:frame>\n'
            )

        if self.new_cell:
            self.cntnt.write('</text:p>\n')

    def start_table(self, name, style_name):
        """
        open a table
        """
        self.cntnt.write(
            '<table:table table:name="%s" ' % name +
                'table:style-name="%s">\n' % style_name
            )

        styles = self.get_style_sheet()
        table = styles.get_table_style(style_name)

        for col in range(table.get_columns()):
            self.cntnt.write(
                '<table:table-column table:style-name="%s.%s"/>\n'
                % (style_name, str(chr(ord('A')+col)))
                )

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
        self.cntnt.write(
            '<table:table-cell table:style-name="%s" ' % style_name +
                'table:value-type="string"'
            )
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
        wrtf = self.sfile.write
                                     
        wrtf('<?xml version="1.0" encoding="UTF-8"?>\n')
        wrtf('<office:document-styles ' +
            _XMLNS +
            'office:version="1.0">\n'
            )

        wrtf('<office:font-face-decls>\n' +
            _FONTS +
            '</office:font-face-decls>\n'
            )

        wrtf('<office:styles>\n' +
            _STYLES
            )
        
        styles = self.get_style_sheet()
        
        for style_name in styles.get_paragraph_style_names():
            style = styles.get_paragraph_style(style_name)
            wrtf(
                '<style:style style:name="%s" ' % style_name +
                    'style:family="paragraph" ' +
                    'style:parent-style-name="Standard" ' +
                    'style:class="text">\n' +
                    '<style:paragraph-properties\n' +
                        'fo:margin-left="%.2fcm"\n'
                             % style.get_left_margin() +
                        'fo:margin-right="%.2fcm"\n'
                             % style.get_right_margin() +
                        'fo:margin-top="%.2fcm"\n'
                             % style.get_top_margin() +
                        'fo:margin-bottom="%.2fcm"\n'
                             % style.get_bottom_margin()
                )

            if style.get_padding() != 0.0:
                wrtf('fo:padding="%.2fcm" ' % style.get_padding())
            if style.get_header_level() > 0:
                wrtf('fo:keep-with-next="auto" ')

            align = style.get_alignment()
            if align == PARA_ALIGN_LEFT:
                wrtf(
                    'fo:text-align="start" '
                    'style:justify-single-word="false" '
                    )

            elif align == PARA_ALIGN_RIGHT:
                wrtf('fo:text-align="end" ')
            elif align == PARA_ALIGN_CENTER:
                wrtf(
                    'fo:text-align="center" '
                    'style:justify-single-word="false" '
                    )
            else:
                wrtf(
                    'fo:text-align="justify" '
                    'style:justify-single-word="false" '
                    )

            wrtf(
                'fo:text-indent="%.2fcm" ' % style.get_first_indent() +
                'style:auto-text-indent="false"/> ' +
                '<style:text-properties '
                )

            font = style.get_font()
            color = font.get_color()
            wrtf('fo:color="#%02x%02x%02x" ' % color)

            wrtf('style:font-name="%s" ' %
                ("Arial"
                    if font.get_type_face() == FONT_SANS_SERIF else
                "Times New Roman")
                )

            wrtf('fo:font-size="%.0fpt" ' % font.get_size())
            if font.get_italic():
                wrtf('fo:font-style="italic" ')
            if font.get_bold():
                wrtf('fo:font-weight="bold" ')

            if font.get_underline():
                wrtf(
                    'style:text-underline="single" ' +
                    'style:text-underline-color="font-color" ' +
                    'fo:text-indent="%.2fcm" ' % style.get_first_indent() +
                    'fo:margin-right="%.2fcm" ' % style.get_right_margin() +
                    'fo:margin-left="%.2fcm" ' % style.get_left_margin() +
                    'fo:margin-top="%.2fcm" ' % style.get_top_margin() +
                    'fo:margin-bottom="%.2fcm"\n' % style.get_bottom_margin()
                    )
            wrtf(
                '/>\n'
                '</style:style>\n'
                )

        # Current no leading number format for headers

        #wrtf('<text:outline-style>\n')
        #wrtf('<text:outline-level-style ')
        #wrtf('text:level="1" style:num-format=""/>\n')
        #wrtf('<text:outline-level-style ')
        #wrtf('text:level="2" style:num-format=""/>\n')
        #wrtf('<text:outline-level-style ')
        #wrtf('text:level="3" style:num-format=""/>\n')
        #wrtf('<text:outline-level-style ')
        #wrtf('text:level="4" style:num-format=""/>\n')
        #wrtf('<text:outline-level-style ')
        #wrtf('text:level="5" style:num-format=""/>\n')
        #wrtf('<text:outline-level-style ')
        #wrtf('text:level="6" style:num-format=""/>\n')
        #wrtf('<text:outline-level-style ')
        #wrtf('text:level="7" style:num-format=""/>\n')
        #wrtf('<text:outline-level-style ')
        #wrtf('text:level="8" style:num-format=""/>\n')
        #wrtf('<text:outline-level-style ')
        #wrtf('text:level="9" style:num-format=""/>\n')
        #wrtf('<text:outline-level-style ')
        #wrtf('text:level="10" style:num-format=""/>\n')
        #wrtf('</text:outline-style>\n')
            
        wrtf(
            '<text:notes-configuration  '
                'text:note-class="footnote"  '
                'style:num-format="1"  '
                'text:start-value="0"  '
                'text:footnotes-position="page"  '
                'text:start-numbering-at="document"/> '
            )

        wrtf(
            '<text:notes-configuration  '
                'text:note-class="endnote"  '
                'style:num-format="i"  '
                'text:start-value="0"/> '
            )

        wrtf(
            '<text:linenumbering-configuration  '
                'text:number-lines="false"  '
                'text:offset="0.499cm"  '
                'style:num-format="1"  '
                'text:number-position="left"  '
                'text:increment="5"/> '
            )

        wrtf('</office:styles>\n')
        wrtf(
            '<office:automatic-styles>\n' +
                _SHEADER_FOOTER +
                '<style:page-layout style:name="pm1">\n' +
                    '<style:page-layout-properties ' +
                        'fo:page-width="%.2fcm" '
                            % self.paper.get_size().get_width() +
                        'fo:page-height="%.2fcm" '
                            % self.paper.get_size().get_height() +
                        'style:num-format="1" '
            )

        wrtf('style:print-orientation="%s" ' %
            ("portrait"
                if self.paper.get_orientation() == PAPER_PORTRAIT else
            "landscape")
            )

        wrtf(
            'fo:margin-top="%.2fcm" '
                % self.paper.get_top_margin() +
            'fo:margin-bottom="%.2fcm" '
                % self.paper.get_bottom_margin() +
            'fo:margin-left="%.2fcm" '
                % self.paper.get_left_margin() +
            'fo:margin-right="%.2fcm" '
                % self.paper.get_right_margin() +
            'style:writing-mode="lr-tb" ' +
            'style:footnote-max-height="0cm">\n' +
            '<style:footnote-sep style:width="0.018cm" ' +
                'style:distance-before-sep="0.101cm" ' +
                'style:distance-after-sep="0.101cm" ' +
                'style:adjustment="left" style:rel-width="25%" ' +
                'style:color="#000000"/>\n' +
            '</style:page-layout-properties>\n'
            )
        
        # header
        wrtf(
            '<style:header-style>\n'
            '<style:header-footer-properties '
            'fo:min-height="0cm" fo:margin-bottom="0.499cm"/>\n'
            '</style:header-style>\n'
            )

        # footer
        wrtf(
            '<style:footer-style>\n'
            '<style:header-footer-properties '
            'fo:min-height="0cm" fo:margin-bottom="0.499cm"/>\n'
            '</style:footer-style>\n'
            )

            # End of page layout
        wrtf(
            '</style:page-layout>\n'
            '</office:automatic-styles>\n'
            )

        # Master Styles        
        wrtf(
            '<office:master-styles>\n'
                '<style:master-page style:name="Standard" '
                    'style:page-layout-name="pm1">\n'
                    # header
                    #'<style:header>'
                    #'<text:p text:style-name="S-Header">'
                    # How to get the document title here ?
                    #' TITRE : %s' % self.title
                    #'</text:p>'
                    #'</style:header>'
                    # footer
                    #'<style:footer>'
                    #'<text:p text:style-name="S-Footer">'
                    #'<text:page-number text:select-page="current">1'
                    #'</text:page-number>/'
                    #'<text:page-count>1'
                    #'</text:page-count>'
                    #'</text:p>'
                    #'</style:footer>'
                    #
                    '</style:master-page>'
            '</office:master-styles>\n'
            )
        # End of document styles      
        wrtf('</office:document-styles>\n')

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
            self.cntnt.write(
                '<text:h text:style-name="%s"' % name +
                ' text:outline-level="%s">' % str(self.level)
                )
        if leader is not None:
            self.cntnt.write(leader + '<text:tab/>')
        self.new_cell = 0

    def end_paragraph(self):
        """
        close a paragraph
        """
        self.cntnt.write(
            '</text:%s>\n' % ('p' if self.level == 0 else 'h')
            )
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
            self.cntnt.write(
                '<text:span text:style-name="Standard">' +
                    text +
                '</text:span>'
                )
            self.end_paragraph()

    def write_styled_note(self, styledtext, format, style_name,
                          contains_html=False):
        """
        Convenience function to write a styledtext to the latex doc. 
        styledtext : assumed a StyledText object to write
        format : = 0 : Flowed, = 1 : Preformatted
        style_name : name of the style to use for default presentation
        contains_html: bool, the backend should not check if html is present. 
            If contains_html=True, then the textdoc is free to handle that in 
            some way. Eg, a textdoc could remove all tags, or could make sure
            a link is clickable. RTFDoc prints the html without handling it
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
        while True:
            m = NewStyle.search(markuptext, start)
            if not m:
                break
            self.StyleList.append(
                [m.group(1) + m.group(2), m.group(1), m.group(2)]
                )
            start = m.end()

        self.start_paragraph(style_name)
        markuptext = markuptext.replace('\1', '&amp;') # must be the first
        markuptext = markuptext.replace('\2', '&lt;')
        markuptext = markuptext.replace('\3', '&gt;')

        for l, line in enumerate(markuptext.split('\n')):
            if l:
                self.cntnt.write('<text:line-break/>')
            self.cntnt.write(line)
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
                self.cntnt.write(
                    '<text:alphabetical-index-mark '
                    'text:string-value="%s" />' % key
                    )

            elif mark.type == INDEX_TYPE_TOC:
                self.cntnt.write(
                    '<text:toc-mark ' +
                    'text:string-value="%s" ' % key +
                    'text:outline-level="%d" />' % mark.level
                    )
        self.cntnt.write(escape(text, _esc_map))

    def _write_manifest(self):
        """
        create the manifest.xml file
        """
        self.mfile = StringIO()

        # Header
        self.mfile.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n' +
            '<manifest:manifest ' +
            'xmlns:manifest="urn:oasis:names:tc:opendocument' +
            ':xmlns:manifest:1.0">' +
            '<manifest:file-entry ' +
            'manifest:media-type="%s" ' % _apptype +
            'manifest:full-path="/"/>'
            )

        # Images
        for image in self.media_list:
            self.mfile.write(
                '<manifest:file-entry manifest:media-type="" ' +
                    'manifest:full-path="Pictures/' +
                    image[1] +
                '"/>'
                )

        # Footer
        self.mfile.write(
            '<manifest:file-entry manifest:media-type="" '
                'manifest:full-path="Pictures/"/>'
            '<manifest:file-entry manifest:media-type="text/xml" '
                'manifest:full-path="content.xml"/>'
            '<manifest:file-entry manifest:media-type="text/xml" '
                'manifest:full-path="styles.xml"/>'
            '<manifest:file-entry manifest:media-type="text/xml" '
                'manifest:full-path="meta.xml"/>'
            '</manifest:manifest>\n'
            )

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
        generator = const.PROGRAM_NAME + ' ' + const.VERSION
        creator = self.get_creator()
        date = self.time
        lang = self.lang

        self.meta.write(
            _META_XML % locals()
            )

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

        height = size * (len(text))
        width = 0
        for line in text:
            width = max(width, string_width(font, line))
        wcm = ReportUtils.pt2cm(width)
        hcm = ReportUtils.pt2cm(height)

        rangle = radians(angle)
        xloc = x - (wcm / 2.0) * cos(rangle) + (hcm / 2.0) * sin(rangle)
        yloc = y - (hcm / 2.0) * cos(rangle) - (wcm / 2.0) * sin(rangle)

        self.cntnt.write(
            '<draw:frame text:anchor-type="paragraph" ' +
            'draw:z-index="2" ' +
            'draw:style-name="clear" ' +
            'svg:height="%.2fcm" ' % hcm +
            'svg:width="%.2fcm" ' % wcm +
            'draw:transform="' +
            'rotate (%.8f) ' % -rangle +
            'translate (%.3fcm %.3fcm)">\n' % (xloc, yloc) +
            '<draw:text-box>\n' +
            '<text:p text:style-name="X%s">' % pname +
            '<text:span text:style-name="F%s">' % pname +
                escape('\n'.join(text), _esc_map) +
            '</text:span></text:p>\n</draw:text-box>\n' +
            '</draw:frame>\n')
        
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

        self.cntnt.write(
            '<draw:polygon draw:style-name="%s" ' % style  +
            'draw:layer="layout" ' +
            'draw:z-index="1" ' +
            'svg:x="%2fcm" svg:y="%2fcm" '
                % (float(minx), float(miny)) +
            'svg:viewBox="0 0 %d %d" '
                % (int((maxx - minx) * 1000), int((maxy - miny) * 1000)) +
            'svg:width="%.4fcm" ' % (maxx - minx) +
            'svg:height="%.4fcm" ' % (maxy - miny)
            )
        
        point = path[0]
        x1 = int((point[0] - minx) * 1000)
        y1 = int((point[1] - miny) * 1000)
        self.cntnt.write('draw:points="%d, %d' % (x1, y1))

        for point in path[1:]:
            x1 = int((point[0] - minx) * 1000)
            y1 = int((point[1] - miny) * 1000)
            self.cntnt.write(' %d, %d' % (x1, y1))
        self.cntnt.write('"/>\n')

    def draw_line(self, style, x1, y1, x2, y2):
        """
        Draw a line
        """
        self.cntnt.write(
            '<draw:line text:anchor-type="paragraph" ' +
            'draw:z-index="3" ' +
            'draw:text-style-name="%s" ' % style  +
            'svg:x1="%.2fcm" ' % x1 +
            'svg:y1="%.2fcm" ' % y1 +
            'svg:x2="%.2fcm" ' % x2 +
            'svg:y2="%.2fcm">' % y2 +
            '<text:p/>\n' +
            '</draw:line>\n'
            )

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

        self.cntnt.write(
            '<draw:frame text:anchor-type="paragraph" ' +
            'draw:z-index="2" ' +
            'draw:style-name="%s" ' % style +
            'svg:width="%.2fcm" ' % sw +
            'svg:height="%.2fcm" '
                % (ReportUtils.pt2cm(font.get_size() * 1.4)) +
            'svg:x="%.2fcm" ' % float(x) +
            'svg:y="%.2fcm">' % float(y) +
            '<draw:text-box> '  +
            '<text:p text:style-name="F%s">' % para_name +
            '<text:span text:style-name="F%s">' % para_name +
            #' fo:max-height="%.2f">' % font.get_size()  +
                escape(text, _esc_map) +
            '</text:span>' +
            '</text:p>' +
            '</draw:text-box>\n' +
            '</draw:frame>\n'
            )

    def draw_box(self, style, text, x, y, w, h):
        """
        Draw a box
        """
        style_sheet = self.get_style_sheet()
        box_style = style_sheet.get_draw_style(style)
        para_name = box_style.get_paragraph_style()
        shadow_width = box_style.get_shadow_space()

        if box_style.get_shadow():
            self.cntnt.write(
                '<draw:rect text:anchor-type="paragraph" ' +
                'draw:style-name="%s_shadow" ' % style +
                'draw:z-index="0" ' +
                'draw:text-style-name="%s" ' % para_name +
                'svg:width="%.2fcm" ' % w +
                'svg:height="%.2fcm" ' % h +
                'svg:x="%.2fcm" ' % (float(x) + shadow_width) +
                'svg:y="%.2fcm">\n' % (float(y) + shadow_width) +
                '</draw:rect>\n'
                )

        self.cntnt.write(
            '<draw:rect text:anchor-type="paragraph" ' +
            'draw:style-name="%s" ' % style +
            'draw:text-style-name="%s" ' % para_name +
            'draw:z-index="1" ' +
            'svg:width="%.2fcm" ' % w +
            'svg:height="%.2fcm" ' % h +
            'svg:x="%.2fcm" ' % float(x) +
            'svg:y="%.2fcm">\n' % float(y)
            )
        if text:
            self.cntnt.write(
                '<text:p text:style-name="%s">' % para_name +
                '<text:span text:style-name="F%s">' % para_name +
                    escape(text, _esc_map) +
                '</text:span>'
                '</text:p>\n'
                )
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

        size = (string_width(font, text) / 72.0) * 2.54

        self.cntnt.write(
            '<draw:frame text:anchor-type="paragraph" ' +
            'draw:style-name="%s" ' % style +
            'draw:z-index="2" ' +
            'svg:width="%.2fcm" ' % size +
            'svg:height="%.2fpt" ' % font.get_size() +
            'svg:x="%.2fcm" ' % (x - (size / 2.0)) +
            'svg:y="%.2fcm">\n' % float(y)
            )

        if text:
            self.cntnt.write(
                '<draw:text-box>' +
                '<text:p text:style-name="X%s">' % para_name +
                '<text:span text:style-name="F%s">' % para_name +
                    escape(text, _esc_map) +
                '</text:span>\n' +
                '</text:p>\n' +
                '</draw:text-box>'
                )
        self.cntnt.write('</draw:frame>\n')