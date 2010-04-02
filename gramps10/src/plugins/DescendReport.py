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

"Generate files/Descendant Report"

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
import os
import sort
import string

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from Report import *
from TextDoc import *
import intl

_ = intl.gettext

#------------------------------------------------------------------------
#
# GTK/GNOME modules
#
#------------------------------------------------------------------------
import gtk
import libglade

#------------------------------------------------------------------------
#
# DescendantReport
#
#------------------------------------------------------------------------
class DescendantReport:

    def __init__(self,db,person,name,max,doc):
        self.creator = db.getResearcher().getName()
        self.name = name
        self.person = person
        self.max_generations = max
        self.doc = doc
        
    def setup(self):
        self.doc.open(self.name)

    def end(self):
        self.doc.close()

    def dump_dates(self, person):
        birth = person.getBirth().getDateObj().get_start_date()
        death = person.getDeath().getDateObj().get_start_date()
        if birth.getYearValid() or death.getYearValid():
            self.doc.write_text(' (')
            if birth.getYearValid():
                self.doc.write_text('b. ' + str(birth.getYear()))
            if death.getYearValid():
                if birth.getYearValid():
                    self.doc.write_text(', ')
                self.doc.write_text('d. ' + str(death.getYear()))
            self.doc.write_text(')')
        
    def report(self):
        self.doc.start_paragraph("Title")
        name = self.person.getPrimaryName().getRegularName()
        self.doc.write_text(_("Descendants of %s") % name)
        self.dump_dates(self.person)
        self.doc.end_paragraph()
        self.dump(0,self.person)

    def dump(self,level,person):

        if level != 0:
            self.doc.start_paragraph("Level%d" % level)
            self.doc.write_text("%d." % level)
            self.doc.write_text(person.getPrimaryName().getRegularName())
            self.dump_dates(person)
            self.doc.end_paragraph()

        if level >= self.max_generations:
            return
        
        childlist = []
        for family in person.getFamilyList():
            for child in family.getChildList():
                childlist.append(child)

        childlist.sort(sort.by_birthdate)
        for child in childlist:
            self.dump(level+1,child)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class DescendantReportDialog(TextReportDialog):
    def __init__(self,database,person):
        TextReportDialog.__init__(self,database,person)

    #------------------------------------------------------------------------
    #
    # Customization hooks
    #
    #------------------------------------------------------------------------
    def get_title(self):
        """The window title for this dialog"""
        return "%s - %s - GRAMPS" % (_("Descendant Report"),_("Text Reports"))

    def get_header(self, name):
        """The header line at the top of the dialog contents"""
        return _("Descendant Report for %s") % name

    def get_target_browser_title(self):
        """The title of the window created when the 'browse' button is
        clicked in the 'Save As' frame."""
        return _("Save Descendant Report")

    def get_stylesheet_savefile(self):
        """Where to save styles for this report."""
        return "descend_report.xml"
    
    def make_default_style(self):
        """Make the default output style for the Descendant Report."""
        f = FontStyle()
        f.set_size(14)
        f.set_type_face(FONT_SANS_SERIF)
        f.set_bold(1)
        p = ParagraphStyle()
        p.set_header_level(1)
        p.set_font(f)
        self.default_style.add_style("Title",p)

        f = FontStyle()
        for i in range(1,32):
            p = ParagraphStyle()
            p.set_font(f)
            p.set_left_margin(max(10.0,float(i-1)))
            self.default_style.add_style("Level%d" % i,p)

    def make_report(self):
        """Create the object that will produce the Descendant Report.
        All user dialog has already been handled and the output file
        opened."""
        try:
            MyReport = DescendantReport(self.db, self.person, self.target_path,
                                        self.max_gen, self.doc)
            MyReport.setup()
            MyReport.report()
            MyReport.end()
        except:
            import DisplayTrace
            DisplayTrace.DisplayTrace()
        
#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
def report(database,person):
    DescendantReportDialog(database,person)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
def get_xpm_image():
    return [
        "48 48 33 1",
        " 	c None",
        ".	c #1A1A1A",
        "+	c #6A665E",
        "@	c #A6A6A6",
        "#	c #BABAB6",
        "$	c #E9D9C0",
        "%	c #E6E6E6",
        "&	c #7A7262",
        "*	c #867A6E",
        "=	c #C2C2BE",
        "-	c #5C5854",
        ";	c #898783",
        ">	c #EEEEEC",
        ",	c #B2966E",
        "'	c #4E4E4E",
        ")	c #BCA076",
        "!	c #FAFAFA",
        "~	c #CECBC1",
        "{	c #E2CBA5",
        "]	c #DAD6D1",
        "^	c #D2D1D0",
        "/	c #9E9286",
        "(	c #ECE1D1",
        "_	c #423E3E",
        ":	c #A29E96",
        "<	c #B7AC9A",
        "[	c #DAD2C6",
        "}	c #E6E2E2",
        "|	c #E1DFDC",
        "1	c #322E2A",
        "2	c #E6D2B6",
        "3	c #F5F2EF",
        "4	c #F1EADE",
        "                                                ",
        "                                                ",
        "             ;*;*****&&&+&++++---+&             ",
        "             *##############<#<:;--&            ",
        "             *#!!!!!!!!!!!!!!4}^#;;/'           ",
        "             ;#!!!!!!!!!!!!!!!3}^@&~/_          ",
        "             *#!!!!!!!!!!!!!!!!3}^-%~;1         ",
        "             *#!!!!@@@@@@@@@@@@@@@'!}~;1        ",
        "             *#!!!!!!!!!!!!!!!!3!3'!!}~;1       ",
        "             *#!!!!!!!!!!!!!!!!!!!'4!!|~;_      ",
        "             *#!!!!3!!!!!!!!!!!!!!'}4!!}~/'     ",
        "             &#!!!!@@:@:@:@:@@@!!3'~}3!!}#/+    ",
        "             &#!!!!!!!!!!!!!!!!!!!'..1_'-&*+&   ",
        "             *#!!!!!!!!@@@@@:@@@@%!3#@:;*+-_+   ",
        "             &#!!!!!!!!!!!!!!!!!!!!>|~=:;;*'_   ",
        "             &#!!!!!!!!@:@@@@:@@@^|>%^~#::;+_   ",
        "             &#!!!!!!!!!!!!!!!!!!!!3%>^~#@:&1   ",
        "             &#!!!!!!!!@@@@@@@@@@%>3%|~^~#@*1   ",
        "             &<!!!!!!!!!!!!!!!!!!33!3>>]=~<;1   ",
        "             +#!!!!@@@@@:@@@:@]%33>>>>>[~~~;1   ",
        "             +#!!!!!!!!!!!!!!!!!33333>}^[=#;1   ",
        "             +#!!!!!!!!@@@@@@:@@@]>>>44]2{[/1   ",
        "             +#!!!!!!!!!!!!!!!33333444}(([~/1   ",
        "             +#!!!!33!3@@@@@@:@::]}|}||[2^{:1   ",
        "             +#!!!!!!!!!!!!!!>3333>4}44$[2~,1   ",
        "             +#!!!!!!!!33!>@@@@@@@@@@^}|${[/1   ",
        "             +#!!!!!!!!!!!!33334444(((44$2[,1   ",
        "             -#!!!!3333333%:::::::::/]||$2^,1   ",
        "             +#!!!!!!!!!3333>>44|(((((4($2{:1   ",
        "             -#!!!!!!!!:@@:::::::~]}}|$$$22,1   ",
        "             +#!!!!!!!!33333(44}44(44((($22/1   ",
        "             -#!!!!@@@:@::::::]}|||$||$]222)1   ",
        "             -#!!!!!33333(>4}444((($$$22222,1   ",
        "             -#!!!!!!!!::::::/://]$$$$($2{2,1   ",
        "             -#!!!333333444|((((($$$$[2$22{)1   ",
        "             -#!!!33334::/:::////[[]$2$22{{)1   ",
        "             '#!33333334}(((((($$$2222$22{{,1   ",
        "             -#33333333:::///////{2[{2[{{{{)1   ",
        "             '#3333%44}4((4(($$$$2222222{{{,1   ",
        "             '#33334444(((((2$$222222{{{{{{,1   ",
        "             '<334444((((($$$2$222{{2{{{{{{,1   ",
        "             -@3444444((($4$$$$2222{{{{{{{{,1   ",
        "             '#4444(((4$($$$$2$2${2{{{{{{{{,1   ",
        "             '<##<<<<<<<)))<)))))),,,,,,,,,,1   ",
        "             11111111111111111111111111.11111   ",
        "                                                ",
        "                                                ",
        "                                                "]

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
from Plugins import register_report

register_report(
    report,
    _("Descendant Report"),
    category=_("Text Reports"),
    status=(_("Beta")),
    description=_("Generates a list of descendants of the active person"),
    xpm=get_xpm_image()
    )

