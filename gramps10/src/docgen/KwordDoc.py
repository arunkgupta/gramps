#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
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

from TextDoc import *
from latin_utf8 import latin_to_utf8

import time
import StringIO
import os
import gzip
from TarFile import TarFile
import Plugins
import ImgManip
import intl
_ = intl.gettext

def points(val):
    inch = float(val)/2.54
    return (int(inch*72))

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class KwordDoc(TextDoc):

    def open(self,filename):
        self.photo_list = []

        if filename[-4:] != ".kwd":
            self.filename = filename + ".kwd"
        else:
            self.filename = filename

        self.f = StringIO.StringIO()
        self.m = StringIO.StringIO()

        self.m.write('<?xml version="1.0" encoding="UTF-8"?>')
        self.m.write('<!DOCTYPE document-info ><document-info>\n')
        self.m.write('<log>\n')
        self.m.write('<text></text>\n')
        self.m.write('</log>\n')
        self.m.write('<author>\n')
        self.m.write('<full-name></full-name>\n')
        self.m.write('<title></title>\n')
        self.m.write('<company></company>\n')
        self.m.write('<email></email>\n')
        self.m.write('<telephone></telephone>\n')
        self.m.write('<fax></fax>\n')
        self.m.write('<country></country>\n')
        self.m.write('<postal-code></postal-code>\n')
        self.m.write('<city></city>\n')
        self.m.write('<street></street>\n')
        self.m.write('</author>\n')
        self.m.write('<about>\n')
        self.m.write('<abstract><![CDATA[]]></abstract>\n')
        self.m.write('<title></title>\n')
        self.m.write('</about>\n')
        self.m.write('</document-info>\n')

        self.f.write('<?xml version="1.0" encoding="UTF-8"?>')
        self.f.write('<!DOCTYPE DOC >')
        self.f.write('<DOC mime="application/x-kword" syntaxVersion="2" ')
        self.f.write('editor="KWord" >\n')
        self.mtime = time.time()

        if self.paper.name == "A3":
            self.f.write('<PAPER format="0" ')
        elif self.paper.name == "A4":
            self.f.write('<PAPER format="1" ')
        elif self.paper.name == "A5":
            self.f.write('<PAPER format="2" ')
        elif self.paper.name == "Letter":
            self.f.write('<PAPER format="3" ')
        elif self.paper.name == "Legal":
            self.f.write('<PAPER format="4" ')
        elif self.paper.name == "B5":
            self.f.write('<PAPER format="7" ')
        else:
            self.f.write('<PAPER format="6" ')

        self.f.write('width="%d" ' % points(self.width))
        self.f.write('height="%d" ' % points(self.height))
        if self.orientation == PAPER_PORTRAIT:
            self.f.write('orientation="0" ')
        else:
            self.f.write('orientation="1" ')
        self.f.write('columns="1" ')
        self.f.write('columnspacing="2.83" ')
        self.f.write('hType="0" ')
        self.f.write('fType="0" ')
        self.f.write('spHeadBody="9" ')
        self.f.write('spFootBody="9">\n')
        self.f.write('<PAPERBORDERS ')
        self.f.write('top="%d" ' % points(self.tmargin))
        self.f.write('right="%d" ' % points(self.rmargin))
        self.f.write('bottom="%d" ' % points(self.bmargin))
        self.f.write('left="%d"/>' % points(self.lmargin))
        self.f.write('</PAPER>\n')
        self.f.write('<ATTRIBUTES processing="0" ')
        self.f.write('standardpage="1" ')
        self.f.write('hasTOC="0" ')
        self.f.write('hasHeader="0" ')
        self.f.write('hasFooter="0" ')
        self.f.write('unit="mm"/>\n')
        self.f.write('<FRAMESETS>\n')
        self.f.write('<FRAMESET frameType="1" ')
        self.f.write('frameInfo="0" ')
        self.f.write('name="Frameset 1">\n')
        self.f.write('<FRAME left="%d" ' % points(self.lmargin))
        self.f.write('top="%d" ' % points(self.tmargin))
        self.f.write('right="%d" ' % points(self.width-self.rmargin))
        self.f.write('bottom="%d" ' % points(self.height-self.bmargin))
        self.f.write('runaround="1" />\n')

        self.cell_row= 0
        self.cell_col= 0
        self.frameset_flg= 1
        self.table_no= 0
        self.cell_style= ""
        self.cell_span= 1

    def close(self):
        if self.frameset_flg == 1:
            self.f.write('</FRAMESET>\n')
            self.frameset_flg= 0

        for p in self.photo_list:
            self.f.write('<FRAMESET frameType="2" frameInfo="0" ')
            self.f.write('name="%s" visible="1">\n' % p[1])
            self.f.write('<FRAME runaround="1" copy="0" newFrameBehaviour="1" ')
            self.f.write('right="%d" ' % p[2])
            self.f.write('left="0" ')
            self.f.write('bottom="%d" ' % p[3])
            self.f.write('top="0" ')
            self.f.write('runaroundGap="2.8"/>\n')
            self.f.write('<IMAGE keepAspectRatio="true">\n')
            self.f.write('<KEY filename="%s" ' % p[1])
            a = time.localtime(self.mtime)
            self.f.write('msec="%d" ' % a[6])
            self.f.write('second="%d" ' % a[5])
            self.f.write('minute="%d" ' % a[4])
            self.f.write('hour="%d" ' % a[3])
            self.f.write('day="%d" ' % a[2])
            self.f.write('month="%d" ' % a[1])
            self.f.write('year="%d"/>\n' % a[0])
            self.f.write('</IMAGE>\n')
            self.f.write('</FRAMESET>\n')
        self.f.write('</FRAMESETS>\n')
        self.f.write('<STYLES>\n')
        for name in self.style_list.keys():
            self.f.write('<STYLE>\n')
            self.f.write('<NAME value="%s"/>\n' % name)

            p = self.style_list[name]

            pad = points(p.get_padding())/2
            self.f.write('<OFFSETS before="%d" after="%d"/>\n' % (pad,pad))
            if p.get_alignment() == PARA_ALIGN_CENTER:
                self.f.write('<FLOW value="center"/>\n')
            elif p.get_alignment() == PARA_ALIGN_JUSTIFY:
                self.f.write('<FLOW value="justify"/>\n')
            elif p.get_alignment() == PARA_ALIGN_RIGHT:
                self.f.write('<FLOW value="right"/>\n')
            else:
                self.f.write('<FLOW value="left"/>\n')

            first = p.get_first_indent()
            left = p.get_left_margin()
            right = p.get_right_margin()
            self.f.write('<INDENTS first="%d" ' % points(first))
            self.f.write('left="%d" right="%d"/>\n' % (points(left),points(right)))

            font = p.get_font()
            self.f.write('<FORMAT>\n')
            if font.get_type_face==FONT_SANS_SERIF:
                self.f.write('<FONT name="helvetica"/>\n')
            else:
                self.f.write('<FONT name="times"/>\n')
            self.f.write('<SIZE value="%d"/>\n' % font.get_size())
            self.f.write('<COLOR red="%d" green="%d" blue="%d"/>\n' % font.get_color())
            if font.get_bold():
                self.f.write('<WEIGHT value="75"/>\n')
            if font.get_italic():
                self.f.write('<ITALIC value="1"/>\n')
            if font.get_underline():
                self.f.write('<UNDERLINE value="1"/>\n')
            self.f.write('</FORMAT>\n')
            if p.get_top_border():
                self.f.write('<TOPBORDER red="0" green="0"')
                self.f.write('blue="0" style="0" width="1"/>\n')
            if p.get_bottom_border():
                self.f.write('<BOTTOMBORDER red="0" green="0" ')
                self.f.write('blue="0" style="0" width="1"/>\n')
            if p.get_right_border():
                self.f.write('<RIGHTBORDER red="0" green="0" ')
                self.f.write('blue="0" style="0" width="1"/>\n')
            if p.get_left_border():
                self.f.write('<LEFTBORDER red="0" green="0" ')
                self.f.write('blue="0" style="0" width="1"/>\n')
            if left != 0:
                self.f.write('<TABULATOR ptpos="%d" type="0"/>\n' % points(left))
            self.f.write('</STYLE>\n')

        self.f.write('</STYLES>\n')
        self.f.write('<PIXMAPS>\n')
        for file in self.photo_list:
            self.f.write('<KEY name="%s" filename="%s" ' % (file[1],file[1]))
            a = time.localtime(self.mtime)
            self.f.write('msec="%d" ' % a[6])
            self.f.write('second="%d" ' % a[5])
            self.f.write('minute="%d" ' % a[4])
            self.f.write('hour="%d" ' % a[3])
            self.f.write('day="%d" ' % a[2])
            self.f.write('month="%d" ' % a[1])
            self.f.write('year="%d"/>\n' % a[0])
        self.f.write('</PIXMAPS>\n')
        self.f.write('</DOC>\n')

        tar = TarFile(self.filename)
        tar.add_file("documentinfo.xml",self.mtime,self.m)
        tar.add_file("maindoc.xml",self.mtime,self.f)
        for file in self.photo_list:
            f = open(file[0],"r")
            tar.add_file(file[1],self.mtime,f)
            f.close()
        tar.close()

        self.f.close()
        self.m.close()

    def start_page(self,orientation=None):
        pass

    def end_page(self):
        pass

    def start_paragraph(self,style_name,leader=None):
        self.format_list = []
        self.bold_start = 0
        self.text = ""
        self.style_name = style_name
        self.p = self.style_list[self.style_name]
        self.font = self.p.get_font()
        if self.font.get_type_face() == FONT_SERIF:
            self.font_face = "Arial"
        else:
            self.font_face = "Times New Roman"

        if leader != None:
            self.text = leader + '\t'
            txt = '<FORMAT id="1" pos="0" len="%d">\n' % (len(leader)+1)
            txt = txt + '<FONT name="%s"/>\n</FORMAT>\n' % self.font_face
            self.format_list.append(txt)

        self.bold_stop = len(self.text)

    def end_paragraph(self):
        if self.frameset_flg == 0:
			self.f.write('<FRAMESET>\n')
			self.frameset_flg= 1

        if self.bold_start != 0 and self.bold_stop != len(self.text):
            txt = '<FORMAT>\n<FONT name="%s"/>\n</FORMAT>\n' % self.font_face
            self.format_list.append(txt)

        self.f.write('<PARAGRAPH>\n')
        self.f.write('<TEXT>')
        self.f.write(latin_to_utf8(self.text))
        self.f.write('</TEXT>\n')
        self.f.write('<FORMATS>\n')
        for format in self.format_list:
            self.f.write(format)
        self.f.write('</FORMATS>\n')
        self.f.write('<LAYOUT>\n')
        self.f.write('<NAME value="%s"/>\n' % self.style_name)

        pad = points(self.p.get_padding())/2
        self.f.write('<OFFSETS before="%d" after="%d"/>\n' % (pad,pad))

        if self.p.get_alignment() == PARA_ALIGN_CENTER:
            self.f.write('<FLOW value="center"/>\n')
        elif self.p.get_alignment() == PARA_ALIGN_JUSTIFY:
            self.f.write('<FLOW value="justify"/>\n')
        elif self.p.get_alignment() == PARA_ALIGN_RIGHT:
            self.f.write('<FLOW value="right"/>\n')
        else:
            self.f.write('<FLOW value="left"/>\n')

        first = self.p.get_first_indent()
        left = self.p.get_left_margin()
        right = self.p.get_right_margin()
        self.f.write('<INDENTS first="%d" ' % points(first))
        self.f.write('left="%d" right="%d"/>\n' % (points(left),points(right)))

        self.f.write('<FORMAT>\n')
        self.f.write('<FONT name="%s"/>\n' % self.font_face)
        self.f.write('<SIZE value="%d"/>\n' % self.font.get_size())
        self.f.write('<COLOR red="%d" green="%d" blue="%d"/>\n' % self.font.get_color())
        if self.font.get_bold():
            self.f.write('<WEIGHT value="75"/>\n')
        if self.font.get_italic():
            self.f.write('<ITALIC value="1"/>\n')
        if self.font.get_underline():
            self.f.write('<UNDERLINE value="1"/>\n')
        if self.p.get_top_border():
            self.f.write('<TOPBORDER red="0" green="0" blue="0" style="0" width="1"/>\n')
        if self.p.get_bottom_border():
            self.f.write('<BOTTOMBORDER red="0" green="0" blue="0" style="0" width="1"/>\n')
        if self.p.get_right_border():
            self.f.write('<RIGHTBORDER red="0" green="0" blue="0" style="0" width="1"/>\n')
        if self.p.get_left_border():
            self.f.write('<LEFTBORDER red="0" green="0" blue="0" style="0" width="1"/>\n')
        self.f.write('</FORMAT>\n')
        if left != 0:
            self.f.write('<TABULATOR ptpos="%d" type="0"/>\n' % points(left))
        self.f.write('</LAYOUT>\n')
        self.f.write('</PARAGRAPH>\n')

    def start_bold(self):
        self.bold_start = len(self.text)
        if self.bold_stop != self.bold_start:
            length = self.bold_stop - self.bold_start
            txt = '<FORMAT id="1" pos="%d" len="%d">\n' % (self.bold_stop,length)
            txt = txt + '<FONT name="%s"/>\n</FORMAT>\n' % self.font_face
            self.format_list.append(txt)

    def end_bold(self):
        self.bold_stop = len(self.text)
        length = self.bold_stop - self.bold_start
        txt = '<FORMAT id="1" pos="%d" len="%d">\n' % (self.bold_start,length)
        txt = txt + '<FONT name="%s"/>\n<WEIGHT value="75"/>\n</FORMAT>\n' % self.font_face
        self.format_list.append(txt)

    def start_table(self,name,style_name):
        self.tbl= self.table_styles[style_name]
        self.cell_left= (self.lmargin * 72)/ 2.54
        self.tbl_width= ((self.width - self.lmargin - self.rmargin) * 72 ) / 2.54
        self.f.write(' </FRAMESET> \n')
        self.cell_row= 0
        self.cell_col= 0
        self.frameset_flg= 0

    def end_table(self):
        self.table_no= self.table_no + 1

    def start_row(self):
        pass

    def end_row(self):
        self.cell_row= self.cell_row + 1
        self.cell_col= 0
        self.cell_left= (self.lmargin * 72)/ 2.54

    def start_cell(self,style_name,span=1):
        self.cell_span= span
        self.cell_style= style_name
        self.cell_right = self.cell_left
        for i in range(0,span):
            col_width = self.tbl.get_column_width(self.cell_col+i)
            spc = (self.tbl_width * col_width) / 100
            self.cell_right = self.cell_right + spc
        self.f.write('<FRAMESET removable="0" cols="%d" rows="1" ' % span)
        self.f.write('grpMgr="Table %d" frameType="1" ' % self.table_no)
        self.f.write('frameInfo="0" row="%d" col="%d" ' % (self.cell_row,self.cell_col))
        self.f.write('name="Table %d Cell %d,%d" visible="1" >\n' % (self.table_no, self.cell_row, self.cell_col))
        self.f.write('<FRAME bleftpt="2.83465" ')
        self.f.write('copy="0" bbottompt="2.83465" btoppt="2.83465" ')
        self.f.write('right="%d" left="%d" ' % (self.cell_right, self.cell_left))
        self.f.write('newFrameBehaviour="1" brightpt="2.83465" ')
        self.f.write('bottom="%d" runaroundGap="2.83465" ' % (self.cell_row*23+self.table_no*125+117))
        self.f.write(' top="%d" autoCreateNewFrame="0" />\n' % (self.cell_row*23+self.table_no*125+95))
        self.frameset_flg= 1
        self.cell_col = self.cell_col + span - 1

    def end_cell(self):
        self.f.write('</FRAMESET>\n')
        self.cell_col= self.cell_col + 1
        self.frameset_flg= 0
        self.cell_left= self.cell_right

    def add_photo(self,name,pos,x_cm,y_cm):

        im = ImgManip.ImgManip(name)
        (x,y)= im.size()
        ratio = float(x_cm)*float(y)/(float(y_cm)*float(x))

        if ratio < 1:
            act_width = x_cm
            act_height = y_cm*ratio
        else:
            act_height = y_cm
            act_width = x_cm/ratio

        index = len(self.photo_list)+1
        tag = 'pictures/picture%d.jpeg' % index
        self.photo_list.append((name,tag,act_width,act_height))
        txt = '<FORMAT id="6" pos="%d" len="1">\n' % len(self.text)
        txt = txt + '<ANCHOR type="frameset" instance="%s"/>\n' % tag
        txt = txt + '</FORMAT>\n'

        self.bold_stop = len(self.text)
        self.format_list.append(txt)

        self.text = self.text + '#'

    def horizontal_line(self):
        pass

    def write_text(self,text):
        text = string.replace(text,'&','&amp;');       # Must be first
        text = string.replace(text,'<','&lt;');
        text = string.replace(text,'>','&gt;');
	self.text = self.text + text


if __name__ == "__main__":

    paper = PaperStyle("Letter",27.94,21.59)

    styles = StyleSheet()
    foo = FontStyle()
    foo.set_type_face(FONT_SANS_SERIF)
    foo.set_color((255,0,0))
    foo.set_size(24)
    foo.set_underline(1)
    foo.set_bold(1)
    foo.set_italic(1)

    para = ParagraphStyle()
    para.set_alignment(PARA_ALIGN_RIGHT)
    para.set_font(foo)
    styles.add_style("Title",para)

    foo = FontStyle()
    foo.set_type_face(FONT_SERIF)
    foo.set_size(12)

    para = ParagraphStyle()
    para.set_font(foo)
    styles.add_style("Normal",para)

    doc = KwordDoc(styles,paper,PAPER_PORTRAIT)
    doc.open("/home/dona/test")

    doc.start_paragraph("Title")
    doc.write_text("My Title")
    doc.end_paragraph()

    doc.start_paragraph("Normal")
    doc.write_text("Hello there. This is fun")
    doc.end_paragraph()

    doc.start_paragraph("Normal")
    doc.write_text("This is fun. ")
    doc.add_photo("/home/dona/dad.jpg",2.0,2.0)
    doc.write_text("So is this. ")
    doc.end_paragraph()

    doc.close()

#Change to support tables (args were: 0,1,1)
Plugins.register_text_doc(_("KWord"),KwordDoc,1,1,1)
