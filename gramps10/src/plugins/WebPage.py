#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Pubilc License as published by
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

"Web Site/Generate Web Site"

from RelLib import *
from HtmlDoc import *

import const
import GrampsCfg
import GenericFilter
import Date
import intl
_ = intl.gettext

import os
import re
import sort
import string
import time
import shutil

from gtk import *
from gnome.ui import *
from libglade import *
from Report import *

_month = [
    "",    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC" ]

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
def by_date(a,b):
    return compare_dates(a.getDateObj(),b.getDateObj())

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class HtmlLinkDoc(HtmlDoc):

    def start_link(self,path):
        self.f.write('<A HREF="%s">' % path)

    def end_link(self):
        self.f.write('</A>')

    def newline(self):
        self.f.write('<BR>\n')

    def write_raw(self,text):
        self.f.write(text)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class IndividualPage:

    def __init__(self,person,photos,restrict,private,uc,link,map,dir_name,imgdir,doc,id,idlink,ext):
        self.person = person
        self.ext = ext
        self.doc = doc
        self.use_id = id
        self.id_link = idlink
	self.list = map
        self.private = private
        self.alive = person.probablyAlive() and restrict
        self.photos = (photos == 2) or (photos == 1 and not self.alive)
        self.usecomments = not uc
        self.dir = dir_name
        self.link = link
        self.slist = []
        self.scnt = 1
        self.image_dir = imgdir

        name = person.getPrimaryName().getRegularName()
        self.doc.set_title(_("Summary of %s") % name)

    #--------------------------------------------------------------------
    #
    # 
    #
    #--------------------------------------------------------------------
    def write_normal_row(self,label,data,sreflist):
        self.doc.start_row()
        self.doc.start_cell("NormalCell")
        self.doc.start_paragraph("Label")
        self.doc.write_text(label)
        self.doc.end_paragraph()
        self.doc.end_cell()

        self.doc.start_cell("NormalCell")
        self.doc.start_paragraph("Data")
        self.doc.write_text(data)
        if sreflist:
            for sref in sreflist:
                self.doc.start_link("#s%d" % self.scnt)
                self.doc.write_raw("<SUP>")
                self.doc.write_text("%d" % self.scnt)
                self.doc.write_raw("</SUP>")
                self.doc.end_link()
                self.scnt = self.scnt + 1
                self.slist.append(sref)
        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.end_row()

    #--------------------------------------------------------------------
    #
    # 
    #
    #--------------------------------------------------------------------
    def write_marriage_row(self,list):
        self.doc.start_row()

        self.doc.start_cell("NormalCell")
        self.doc.start_paragraph("Label")
        self.doc.write_text(list[0])
        self.doc.end_paragraph()
        self.doc.end_cell()

        self.doc.start_cell("NormalCell")
        self.doc.start_paragraph("Data")
        self.doc.write_text(list[1])
        self.doc.end_paragraph()
        self.doc.end_cell()

        self.doc.end_row()

    #--------------------------------------------------------------------
    #
    # 
    #
    #--------------------------------------------------------------------
    def write_link_row(self,title,person):
        self.doc.start_row()
        self.doc.start_cell("NormalCell")
        self.doc.start_paragraph("Label")
        self.doc.write_text(title)
        self.doc.end_paragraph()
        self.doc.end_cell()

        self.doc.start_cell("NormalCell")
        self.doc.start_paragraph("Data")
        if person:
            id = person.getId()
            if self.list.has_key(id):
                self.doc.start_link("%s.%s" % (id,self.ext))
	        self.doc.write_text(person.getPrimaryName().getRegularName())
                self.doc.end_link()
            else:
	        self.doc.write_text(person.getPrimaryName().getRegularName())

        self.doc.end_paragraph()
        self.doc.end_cell()
        self.doc.end_row()

    def write_sources(self):
        self.doc.start_paragraph("SourcesTitle")
        self.doc.write_text(_("Sources"))
        self.doc.end_paragraph()

        index = 1
        for sref in self.slist:
            self.doc.start_paragraph("SourceParagraph")
            self.doc.start_link("s%d" % index)
            self.doc.write_text('%d. ' % index)
            self.doc.end_link()
            index = index + 1
            self.write_info(sref.getBase().getTitle())
            self.write_info(sref.getBase().getAuthor())
            self.write_info(sref.getBase().getPubInfo())
            self.write_info(sref.getDate().getDate())
            self.write_info(sref.getPage())
            if self.usecomments:
                self.write_info(sref.getText())
                self.write_info(sref.getComments())
            self.doc.end_paragraph()

    def write_info(self,info):
        """Writes a line of text, after stripping leading and trailing
           spaces. If the last character is not a period, the period is
           appended to produce a sentance"""
        
        info = string.strip(info)
        if info != "":
            if info[-1] == '.':
                self.doc.write_text("%s " % info)
            else:
                self.doc.write_text("%s. " % info)
                
    def create_page(self):
        """Generate the HTML page for the specific person"""
        
        filebase = "%s.%s" % (self.person.getId(),self.ext)
        self.doc.open("%s/%s" % (self.dir,filebase))

        photo_list = self.person.getPhotoList()
        name_obj = self.person.getPrimaryName()
        name = name_obj.getRegularName()

        # Write out the title line.
        
        self.doc.start_paragraph("Title")
        self.doc.write_text(_("Summary of %s") % name)
        self.doc.end_paragraph()

        # blank line for spacing

        self.doc.start_paragraph("Data")
        self.doc.end_paragraph()

        # look for the primary media object if photos have been requested.
        # make sure that the media object is an image. If so, insert it
        # into the document.
        
        if self.photos and len(photo_list) > 0:
            object = photo_list[0].getReference()
            if object.getMimeType()[0:5] == "image":
                file = object.getPath()
                if os.path.isfile(file):
                    self.doc.start_paragraph("Data")
                    self.doc.add_photo(file,"row",4.0,4.0)
                    self.doc.end_paragraph()

        # Start the first table, which consists of basic information, including
        # name, gender, and parents
        
        self.doc.start_table("one","IndTable")
        self.write_normal_row("%s:" % _("Name"), name, name_obj.getSourceRefList())
        if self.use_id:
            if self.id_link:
                val = '<a href="%s">%s</a>' % (self.id_link,self.person.getId())
                val = string.replace(val,'*',self.person.getId())
            else:
                val = self.person.getId()
            self.write_normal_row("%s:" % _("ID Number"),val,None)
            
        if self.person.getGender() == Person.male:
            self.write_normal_row("%s:" % _("Gender"), _("Male"),None)
        elif self.person.getGender() == Person.female:
            self.write_normal_row("%s:" % _("Gender"), _("Female"),None)
	else:
            self.write_normal_row("%s:" % _("Gender"), _("Unknown"), None)

        family = self.person.getMainParents()
        if family:
            self.write_link_row("%s:" % _("Father"), family.getFather())
            self.write_link_row("%s:" % _("Mother"), family.getMother())
        else:
            self.write_link_row("%s:" % _("Father"), None)
            self.write_link_row("%s:" % _("Mother"), None)
        self.doc.end_table()

        # Another blank line between the tables
        
        self.doc.start_paragraph("Data")
        self.doc.end_paragraph()
        
        self.write_facts()
        self.write_notes()
        self.write_families()

        # if inclusion of photos has been enabled, write the photo
        # gallery.

        if self.photos:
            self.write_gallery()

        # write source information
        
        if self.scnt > 1:
            self.write_sources()

        if self.link:
            self.doc.start_paragraph("Data")
            self.doc.start_link("index.%s" % self.ext)
            self.doc.write_text(_("Return to the index of people"))
            self.doc.end_link()
            self.doc.end_paragraph()

    def close(self):
        """Close the document"""
        self.doc.close()

    def write_gallery(self):
        """Write the image gallery. Add images that are not marked
           as private, creating a thumbnail and copying the original
           image to the directory."""

        # build a list of the images to add, but skip the first image,
        # since it has been used at the top of the page.
        
        my_list = []
        index = 0
        for object in self.person.getPhotoList():
            if object.getReference().getMimeType()[0:5] == "image":
                if object.getPrivacy() == 0 and index != 0:
                    my_list.append(object)
            index = 1
            
        # if no images were found, return
        
        if len(my_list) == 0:
            return

        self.doc.start_paragraph("Data")
        self.doc.end_paragraph()

        self.doc.start_paragraph("GalleryTitle")
        self.doc.write_text(_("Gallery"))
        self.doc.end_paragraph()

        self.doc.start_table("gallery","IndTable")
        for obj in my_list:
            try:
                src = obj.getReference().getPath()
                base = os.path.basename(src)
                    
                if self.image_dir:
                    shutil.copy(src,"%s/%s/%s" % (self.dir,self.image_dir,base))
                else:
                    shutil.copy(src,"%s/%s" % (self.dir,base))

                self.doc.start_row()
                self.doc.start_cell("ImageCell")
                self.doc.start_paragraph("Data")
                if self.image_dir:
                    self.doc.start_link("%s/%s" % (self.image_dir,base))
                else:
                    self.doc.start_link("%s" % base)
                self.doc.add_photo(src,"row",1.5,1.5)
                self.doc.end_link()
                
                self.doc.end_paragraph()
                self.doc.end_cell()
                self.doc.start_cell("NoteCell")
                description = obj.getReference().getDescription()
                if description != "":
                    self.doc.start_paragraph("PhotoDescription")
                    self.doc.write_text(description)
                    self.doc.end_paragraph()
                if obj.getNote() != "":
                    self.doc.start_paragraph("PhotoNote")
                    self.doc.write_text(obj.getNote())
                    self.doc.end_paragraph()
                elif obj.getReference().getNote() != "":
                    self.doc.start_paragraph("PhotoNote")
                    self.doc.write_text(obj.getReference().getNote())
                    self.doc.end_paragraph()
                self.doc.end_cell()
                self.doc.end_row()
            except IOError:
                pass
        self.doc.end_table()
        
    #--------------------------------------------------------------------
    #
    # 
    #
    #--------------------------------------------------------------------
    def write_facts(self):

        if self.alive:
            return
        count = 0
        
        event_list = [ self.person.getBirth(), self.person.getDeath() ]
        event_list = event_list + self.person.getEventList()
        event_list.sort(by_date)
        for event in event_list:
            if event.getPrivacy():
                continue
            name = _(event.getName())
            date = event.getDate()
            descr = event.getDescription()
            place = event.getPlaceName()
            srcref = event.getSourceRefList()

            if date == "" and descr == "" and place == "" and len(srcref) == 0:
                continue

            if count == 0:
                self.doc.start_paragraph("EventsTitle")
                self.doc.write_text(_("Facts and Events"))
                self.doc.end_paragraph()
                self.doc.start_table("two","IndTable")
                count = 1

            if place != "" and place[-1] == ".":
                place = place[0:-1]
            if descr != "" and descr[-1] == ".":
                descr = descr[0:-1]

            if date != "":
                if place != "":
                    val = "%s, %s." % (date,place)
                else:
                    val = "%s." % date
            elif place != "":
                val = "%s." % place
            else:
                val = ""
                
            if descr != "":
                val = val + ("%s." % descr)

            self.write_normal_row(name, val, srcref)

        if count != 0:
            self.doc.end_table()

    #--------------------------------------------------------------------
    #
    # 
    #
    #--------------------------------------------------------------------
    def write_notes(self):

        if self.person.getNote() == "" or self.alive:
            return
        
        self.doc.start_paragraph("NotesTitle")
        self.doc.write_text(_("Notes"))
        self.doc.end_paragraph()

        self.doc.start_paragraph("NotesParagraph")
        self.doc.write_text(self.person.getNote())
        self.doc.end_paragraph()

    #--------------------------------------------------------------------
    #
    # 
    #
    #--------------------------------------------------------------------
    def write_fam_fact(self,event):

        if event == None:
            return
        name = _(event.getName())
        date = event.getDate()
        place = event.getPlaceName()
        descr = event.getDescription()
        if descr != "" and descr[-1] == ".":
            descr = descr[0:-1]
        if place != "" and place[-1] == ".":
            place = place[0:-1]

        if date == "" and place == "" and descr == "":
            return
        
        if date == "":
            if place == "":
                if descr == "":
                    val = ""
                else:
                    val = "%s." % descr
            else:
                if descr == "":
                    val = "%s." % place
                else:
                    val = "%s. %s." % (place,descr)
        else:
            if place == "":
                if descr == "":
                    val = "%s." % date
                else:
                    val = "%s. %s." % (date,descr)
            else:
                if descr == "":
                    val = "%s, %s." % (date,place)
                else:
                    val = "%s, %s. %s." % (date,place,descr)

        self.write_marriage_row([name, val])

    #--------------------------------------------------------------------
    #
    # 
    #
    #--------------------------------------------------------------------
    def write_families(self):
        if len(self.person.getFamilyList()) == 0:
            return
        
        self.doc.start_paragraph("FamilyTitle")
        self.doc.write_text(_("Marriages/Children"))
        self.doc.end_paragraph()

        self.doc.start_table("three","IndTable")
        
        for family in self.person.getFamilyList():
            if self.person == family.getFather():
                spouse = family.getMother()
            else:
                spouse = family.getFather()
            self.doc.start_row()
            self.doc.start_cell("NormalCell",2)
            self.doc.start_paragraph("Spouse")
            if spouse:
                id = spouse.getId()
                if self.list.has_key(id):
                    self.doc.start_link("%s.%s" % (id,self.ext))
                    self.doc.write_text(spouse.getPrimaryName().getRegularName())
                    self.doc.end_link()
                else:
                    self.doc.write_text(spouse.getPrimaryName().getRegularName())
            else:
                self.doc.write_text(_("unknown"))
            self.doc.end_paragraph()
            self.doc.end_cell()
            self.doc.end_row()
            
            if not self.alive:
                for event in family.getEventList():
                    if event.getPrivacy() == 0:
                        self.write_fam_fact(event)

            child_list = family.getChildList()
            if len(child_list) > 0:
                
                self.doc.start_row()
                self.doc.start_cell("NormalCell")
                self.doc.start_paragraph("Label")
                self.doc.write_text(_("Children"))
                self.doc.end_paragraph()
                self.doc.end_cell()
                
                self.doc.start_cell("NormalCell")
                self.doc.start_paragraph("Data")
                
                first = 1
                for child in family.getChildList():
                    name = child.getPrimaryName().getRegularName()
                    if first == 1:
                        first = 0
                    else:
                        self.doc.write_text('\n')
                    id = child.getId()
                    if self.list.has_key(id):
                        self.doc.start_link("%s.%s" % (id,self.ext))
                        self.doc.write_text(name)
                        self.doc.end_link()
                    else:
                        self.doc.write_text(name)
                self.doc.end_paragraph()
                self.doc.end_cell()
                self.doc.end_row()
        self.doc.end_table()

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class WebReport(Report):
    def __init__(self,db,person,target_path,max_gen,photos,filter,restrict,
                 private, srccomments, include_link, style, image_dir,
                 template_name,use_id,id_link,gendex,ext):
        self.db = db
        self.ext = ext
        self.use_id = use_id
        self.id_link = id_link
        self.person = person
        self.target_path = target_path
        self.max_gen = max_gen
        self.photos = photos
        self.filter = filter
        self.restrict = restrict
        self.private = private
        self.srccomments = srccomments
        self.include_link = include_link
        self.selected_style = style
        self.image_dir = image_dir
        self.use_gendex = gendex
        self.template_name = template_name

    def get_progressbar_data(self):
        return (_("Generate HTML reports - GRAMPS"), _("Creating Web Pages"))
    
    def make_date(self,date):
        start = date.get_start_date()
        if date.isEmpty():
            val = date.getText()
        elif date.isRange():
            val = "FROM %s TO %s" % (self.subdate(start),
                                     self.subdate(date.get_stop_date()))
        else:
            val = self.subdate(start)
        return val

    def subdate(self,subdate):
        retval = ""
        day = subdate.getDay()
        mon = subdate.getMonth()
        year = subdate.getYear()
        mode = subdate.getModeVal()
        day_valid = subdate.getDayValid()
        mon_valid = subdate.getMonthValid()
        year_valid = subdate.getYearValid()
        
        if not day_valid:
            try:
                if not mon_valid:
                    retval = str(year)
                elif not year_valid:
                    retval = _month[mon]
                else:
                    retval = "%s %d" % (_month[mon],year)
            except IndexError:
                print "Month index error - %d" % mon
                retval = str(year)
        elif not mon_valid:
            retval = str(year)
        else:
            try:
                month = _month[mon]
                if not year_valid:
                    retval = "%d %s ????" % (day,month)
                else:
                    retval = "%d %s %d" % (day,month,year)
            except IndexError:
                print "Month index error - %d" % mon
                retval = str(year)
        if mode == Date.SingleDate.about:
            retval = "ABT %s"  % retval
        elif mode == Date.SingleDate.before:
            retval = "BEF %s" % retval
        elif mode == Date.SingleDate.after:
            retval = "AFT %s" % retval
        return retval

    def dump_gendex(self,person_list,html_dir):
        fname = "%s/gendex.txt" % html_dir
        try:
            f = open(fname,"w")
        except:
            return
        for p in person_list:
            name = p.getPrimaryName()
            firstName = name.getFirstName()
            surName = name.getSurname()
            suffix = name.getSuffix()

            f.write("%s.%s|" % (p.getId(),self.ext))
            f.write("%s|" % surName)
            if suffix == "":
                f.write("%s /%s/|" % (firstName,surName))
            else:
                f.write("%s /%s/, %s|" % (firstName,surName, suffix))
            for e in [p.getBirth(),p.getDeath()]:
                if e:
                    f.write("%s|" % self.make_date(e.getDateObj()))
                    if e.getPlace():
                        f.write('%s|' % e.getPlace().get_title())
                    else:
                        f.write('|')
                else:
                    f.write('||')
            f.write('\n')
        f.close()

    def dump_index(self,person_list,styles,template,html_dir):
        """Writes a index file, listing all people in the person list."""
    
        doc = HtmlLinkDoc(self.selected_style,None,template,None)
        doc.set_extension(self.ext)
        doc.set_title(_("Family Tree Index"))
    
        doc.open("%s/index.%s" % (html_dir,self.ext))
        doc.start_paragraph("Title")
        doc.write_text(_("Family Tree Index"))
        doc.end_paragraph()
    
        person_list.sort(sort.by_last_name)

        a = {}
        for person in person_list:
            n = person.getPrimaryName().getSurname()
            if n:
                a[n[0]] = 1
            else:
                a[''] = 1

        col_len = len(person_list) + len(a.keys())
        col_len = col_len/2
        
        doc.write_raw('<table width="100%" border="0">')
        doc.write_raw('<tr><td width="50%" valign="top">')
        last = ''
        end_col = 0
        for person in person_list:
            name = person.getPrimaryName().getName()
            if name and name[0] != last:
                last = name[0]
                doc.start_paragraph('IndexLabel')
                doc.write_text(name[0])
                doc.end_paragraph()
                col_len = col_len - 1
            doc.start_link("%s.%s" % (person.getId(),self.ext))
            doc.write_text(name)
            doc.end_link()
            if col_len <= 0 and end_col == 0:
                doc.write_raw('</td><td valign="top">')
                doc.start_paragraph('IndexLabel')
                doc.write_text(_("%s (continued)") % name[0])
                doc.end_paragraph()
                end_col = 1
            else:
                doc.newline()
            col_len = col_len - 1
        doc.write_raw('</td></tr></table>')
        doc.close()
        doc.write_support_files()
        
    def write_report(self):
        dir_name = self.target_path
        if dir_name == None:
            dir_name = os.getcwd()
        elif not os.path.isdir(dir_name):
            parent_dir = os.path.dirname(dir_name)
            if not os.path.isdir(parent_dir):
                GnomeErrorDialog(_("Neither %s nor %s are directories") % \
                                 (dir_name,parent_dir))
                return
            else:
                try:
                    os.mkdir(dir_name)
                except IOError, value:
                    GnomeErrorDialog(_("Could not create the directory : %s") % \
                                     dir_name + "\n" + value[1])
                    return
                except:
                    GnomeErrorDialog(_("Could not create the directory : %s") % \
                                     dir_name)
                    return

        if self.image_dir:
            image_dir_name = os.path.join(dir_name, self.image_dir)
        else:
            image_dir_name = dir_name
        if not os.path.isdir(image_dir_name) and self.photos != 0:
            try:
                os.mkdir(image_dir_name)
            except IOError, value:
                GnomeErrorDialog(_("Could not create the directory : %s") % \
                                 image_dir_name + "\n" + value[1])
                return
            except:
                GnomeErrorDialog(_("Could not create the directory : %s") % \
                                 image_dir_name)
                return
    
        ind_list = self.filter.apply(self.db,self.db.getPersonMap().values())
        self.progress_bar_setup(float(len(ind_list)))
        
        doc = HtmlLinkDoc(self.selected_style,None,self.template_name,None)
        doc.set_extension(self.ext)
        doc.set_image_dir(self.image_dir)
        
        self.add_styles(doc)
        doc.build_style_declaration()

        my_map = {}
        for l in ind_list:
            my_map[l.getId()] = 1
        for person in ind_list:
            tdoc = HtmlLinkDoc(self.selected_style,None,None,None,doc)
            tdoc.set_extension(self.ext)
            idoc = IndividualPage(person, self.photos, self.restrict,
                                  self.private, self.srccomments,
                                  self.include_link, my_map, dir_name,
                                  self.image_dir, tdoc, self.use_id,self.id_link,self.ext)
            idoc.create_page()
            idoc.close()
            self.progress_bar_step()
            while events_pending():
                mainiteration()
            
        if len(ind_list) > 1:
            self.dump_index(ind_list,self.selected_style,
                            self.template_name,dir_name)
        if self.use_gendex == 1:
            self.dump_gendex(ind_list,dir_name)
        self.progress_bar_done()

    def add_styles(self,doc):
        tbl = TableStyle()
        tbl.set_width(100)
        tbl.set_column_widths([15,85])
        doc.add_table_style("IndTable",tbl)

        cell = TableCellStyle()
        doc.add_cell_style("NormalCell",cell)

        cell = TableCellStyle()
        cell.set_padding(0.2)
        doc.add_cell_style("ImageCell",cell)

        cell = TableCellStyle()
        cell.set_padding(0.2)
        doc.add_cell_style("NoteCell",cell)


#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class WebReportDialog(ReportDialog):
    def __init__(self,database,person):
        ReportDialog.__init__(self,database,person)

    def add_user_options(self):
        lnk_msg = _("Include a link to the index page")
        priv_msg = _("Do not include records marked private")
        restrict_msg = _("Restrict information on living people")
        no_img_msg = _("Do not use images")
        no_limg_msg = _("Do not use images for living people")
        no_com_msg = _("Do not include comments and text in source information")
        include_id_msg = _("Include the GRAMPS ID in the report")
        gendex_msg = _("Create a GENDEX index")
        imgdir_msg = _("Image subdirectory")
        ext_msg = _("File extension")

        self.use_link = GtkCheckButton(lnk_msg)
        self.use_link.set_active(1) 
        self.no_private = GtkCheckButton(priv_msg)
        self.no_private.set_active(1)
        self.restrict_living = GtkCheckButton(restrict_msg)
        self.no_images = GtkCheckButton(no_img_msg)
        self.no_living_images = GtkCheckButton(no_limg_msg)
        self.no_comments = GtkCheckButton(no_com_msg)
        self.include_id = GtkCheckButton(include_id_msg)
        self.gendex = GtkCheckButton(gendex_msg)
        self.imgdir = GtkEntry()
        self.imgdir.set_text("images")
        self.linkpath = GtkEntry()
        self.linkpath.set_sensitive(0)
        self.include_id.connect('toggled',self.show_link)
        self.ext = GtkCombo()
        self.ext.set_popdown_strings(['.html','.htm','.php','.php3',
                                      '.cgi'])

        self.add_option(imgdir_msg,self.imgdir)
        self.add_option('',self.use_link)

        title = _("Privacy")
        self.add_frame_option(title,None,self.no_private)
        self.add_frame_option(title,None,self.restrict_living)
        self.add_frame_option(title,None,self.no_images)
        self.add_frame_option(title,None,self.no_living_images)
        self.add_frame_option(title,None,self.no_comments)

        title = _('Advanced')
        self.add_frame_option(title,'',self.include_id)
        self.add_frame_option(title,_('GRAMPS ID link URL'),self.linkpath)
        self.add_frame_option(title,'',self.gendex)
        self.add_frame_option(title,ext_msg,self.ext)

        self.no_images.connect('toggled',self.on_nophotos_toggled)

    def show_link(self,obj):
        self.linkpath.set_sensitive(obj.get_active())

    #------------------------------------------------------------------------
    #
    # Customization hooks
    #
    #------------------------------------------------------------------------
    def get_title(self):
        """The window title for this dialog"""
        return "%s - %s - GRAMPS" % (_("Generate Web Site"),_("Web Page"))

    def get_target_browser_title(self):
        """The title of the window created when the 'browse' button is
        clicked in the 'Save As' frame."""
        return _("Target Directory")

    def get_target_is_directory(self):
        """This report creates a directory full of files, not a single file."""
        return 1
    
    def get_stylesheet_savefile(self):
        """Where to save styles for this report."""
        return "webpage.xml"
    
    def get_report_generations(self):
        """Default to ten generations, no page break box."""
        return (10, 0)

    def get_report_filters(self):
        """Set up the list of possible content filters."""

        name = self.person.getPrimaryName().getName()
        
        all = GenericFilter.GenericFilter()
        all.set_name(_("Entire Database"))
        all.add_rule(GenericFilter.Everyone([]))

        des = GenericFilter.GenericFilter()
        des.set_name(_("Direct Descendants of %s") % name)
        des.add_rule(GenericFilter.IsDescendantOf([self.person.getId()]))

        df = GenericFilter.GenericFilter()
        df.set_name(_("Descendant Families of %s") % name)
        df.add_rule(GenericFilter.IsDescendantFamilyOf([self.person.getId()]))
        
        ans = GenericFilter.GenericFilter()
        ans.set_name(_("Ancestors of %s") % name)
        ans.add_rule(GenericFilter.IsAncestorOf([self.person.getId()]))

        com = GenericFilter.GenericFilter()
        com.set_name(_("People with common ancestor with %s") % name)
        com.add_rule(GenericFilter.HasCommonAncestorWith([self.person.getId()]))

        return [all,des,df,ans,com]

    #------------------------------------------------------------------------
    #
    # Functions related to the default directory
    #
    #------------------------------------------------------------------------
    def get_default_directory(self):
        """Get the name of the directory to which the target dialog
        box should default.  This value can be set in the preferences
        panel."""
        return GrampsCfg.web_dir
    
    def set_default_directory(self, value):
        """Save the name of the current directory, so that any future
        reports will default to the most recently used directory.
        This also changes the directory name that will appear in the
        preferences panel, but does not change the preference in disk.
        This means that the last directory used will only be
        remembered for this session of gramps unless the user saves
        his/her preferences."""
        GrampsCfg.web_dir = value
    
    #------------------------------------------------------------------------
    #
    # Create output style appropriate to this report.
    #
    #------------------------------------------------------------------------
    def make_default_style(self):
        """Make the default output style for the Web Pages Report."""
        font = FontStyle()
        font.set(bold=1, face=FONT_SANS_SERIF, size=16)
        p = ParagraphStyle()
        p.set(align=PARA_ALIGN_CENTER,font=font)
        self.default_style.add_style("Title",p)
        
        font = FontStyle()
        font.set(bold=1,face=FONT_SANS_SERIF,size=12,italic=1)
        p = ParagraphStyle()
        p.set(font=font,bborder=1)
        self.default_style.add_style("EventsTitle",p)
    
        font = FontStyle()
        font.set(bold=1,face=FONT_SANS_SERIF,size=12,italic=1)
        p = ParagraphStyle()
        p.set(font=font,bborder=1)
        self.default_style.add_style("NotesTitle",p)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF,size=10)
        p = ParagraphStyle()
        p.set(font=font,align=PARA_ALIGN_CENTER)
        self.default_style.add_style("Copyright",p)
    
        font = FontStyle()
        font.set(bold=1,face=FONT_SANS_SERIF,size=12,italic=1)
        p = ParagraphStyle()
        p.set(font=font,bborder=1)
        self.default_style.add_style("SourcesTitle",p)

        font = FontStyle()
        font.set(bold=1,face=FONT_SANS_SERIF,size=14,italic=1)
        p = ParagraphStyle()
        p.set(font=font)
        self.default_style.add_style("IndexLabel",p)

        font = FontStyle()
        font.set(bold=1,face=FONT_SANS_SERIF,size=12,italic=1)
        p = ParagraphStyle()
        p.set(font=font,bborder=1)
        self.default_style.add_style("GalleryTitle",p)
    
        font = FontStyle()
        font.set(bold=1,face=FONT_SANS_SERIF,size=12,italic=1)
        p = ParagraphStyle()
        p.set(font=font,bborder=1)
        self.default_style.add_style("FamilyTitle",p)
        
        font = FontStyle()
        font.set(bold=1,face=FONT_SANS_SERIF,size=12)
        p = ParagraphStyle()
        p.set_font(font)
        self.default_style.add_style("Spouse",p)
    
        font = FontStyle()
        font.set(size=12,italic=1)
        p = ParagraphStyle()
        p.set_font(font)
        self.default_style.add_style("Label",p)
    
        font = FontStyle()
        font.set_size(12)
        p = ParagraphStyle()
        p.set_font(font)
        self.default_style.add_style("Data",p)
    
        font = FontStyle()
        font.set(bold=1,face=FONT_SANS_SERIF,size=12)
        p = ParagraphStyle()
        p.set_font(font)
        self.default_style.add_style("PhotoDescription",p)
    
        font = FontStyle()
        font.set(size=12)
        p = ParagraphStyle()
        p.set_font(font)
        self.default_style.add_style("PhotoNote",p)
    
        font = FontStyle()
        font.set_size(10)
        p = ParagraphStyle()
        p.set_font(font)
        self.default_style.add_style("SourceParagraph",p)
    
        font = FontStyle()
        font.set_size(12)
        p = ParagraphStyle()
        p.set_font(font)
        self.default_style.add_style("NotesParagraph",p)

    #------------------------------------------------------------------------
    #
    # Functions related to selecting/changing the current file format
    #
    #------------------------------------------------------------------------
    def make_document(self):
        """Do Nothing.  This document will be created in the
        make_report routine."""
        pass


    def setup_format_frame(self):
        """Do nothing, since we don't want a format frame (HTML only)"""
        pass
    
    #------------------------------------------------------------------------
    #
    # Functions related to setting up the dialog window
    #
    #------------------------------------------------------------------------
    def setup_post_process(self):
        """The format frame is not used in this dialog.  Hide it, and
        set the output notebook to always display the html template
        page."""
        self.output_notebook.set_page(1)

    #------------------------------------------------------------------------
    #
    # Functions related to retrieving data from the dialog window
    #
    #------------------------------------------------------------------------

    def parse_format_frame(self):
        """The format frame is not used in this dialog."""
        pass
    
    def parse_report_options_frame(self):
        """Parse the report options frame of the dialog.  Save the
        user selected choices for later use."""
        ReportDialog.parse_report_options_frame(self)
        self.include_link = self.use_link.get_active()

    def parse_other_frames(self):
        """Parse the privacy options frame of the dialog.  Save the
        user selected choices for later use."""
        self.restrict = self.restrict_living.get_active()
        self.private = self.no_private.get_active()
        self.img_dir_text = self.imgdir.get_text()

        self.html_ext = string.strip(self.ext.entry.get_text())
        if self.html_ext[0] == '.':
            self.html_ext = self.html_ext[1:]
        self.use_id = self.include_id.get_active()
        self.use_gendex = self.gendex.get_active()
        self.id_link = string.strip(self.linkpath.get_text())
        self.srccomments = self.no_comments.get_active()
        if self.no_images.get_active() == 1:
            self.photos = 0
        elif self.no_living_images.get_active() == 1:
            self.photos = 1
        else:
            self.photos = 2

    #------------------------------------------------------------------------
    #
    # Callback functions from the dialog
    #
    #------------------------------------------------------------------------
    def on_nophotos_toggled(self,obj):
        """Keep the 'restrict photos' checkbox in line with the 'no
        photos' checkbox.  If there are no photos included, it makes
        no sense to worry about restricting which photos are included,
        now does it?"""
        if obj.get_active():
            self.no_living_images.set_sensitive(0)
        else:
            self.no_living_images.set_sensitive(1)

    #------------------------------------------------------------------------
    #
    # Functions related to creating the actual report document.
    #
    #------------------------------------------------------------------------
    def make_report(self):
        """Create the object that will produce the web pages."""
        MyReport = WebReport(self.db, self.person, self.target_path,
                             self.max_gen, self.photos, self.filter,
                             self.restrict, self.private, self.srccomments,
                             self.include_link, self.selected_style,
                             self.img_dir_text,self.template_name,
                             self.use_id,self.id_link,self.use_gendex,
                             self.html_ext)
        MyReport.write_report()
    
#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
def report(database,person):
    WebReportDialog(database,person)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
def get_xpm_image():
    return [
        "48 48 33 1",
        " 	c None",
        ".	c #191B1E",
        "+	c #746F5F",
        "@	c #6EA2C9",
        "#	c #F2E8DA",
        "$	c #B4A766",
        "%	c #2F383A",
        "&	c #9F8F53",
        "*	c #BBB774",
        "=	c #6E614B",
        "-	c #506E8C",
        ";	c #2B559A",
        ">	c #E1CB95",
        ",	c #5992CD",
        "'	c #5A584F",
        ")	c #86827D",
        "!	c #CBCAC7",
        "~	c #294A76",
        "{	c #E3D0B6",
        "]	c #7B7D7C",
        "^	c #D5BE97",
        "/	c #FBFAF8",
        "(	c #EADECB",
        "_	c #4E84C7",
        ":	c #474943",
        "<	c #95A992",
        "[	c #ADA69B",
        "}	c #3F72B7",
        "|	c #C4A985",
        "1	c #9B9383",
        "2	c #213C60",
        "3	c #BBB9AF",
        "4	c #7F959D",
        "            )11)1))))))]]+++=='=''              ",
        "            13!!!{!!!!^!!!!!33[<]')=            ",
        "            1!////////////#/##!![]<4:           ",
        "            1!////////////////#(![[3):          ",
        "            )!////////////////##(33(3]%         ",
        "            1!//////////////////#3</!3]%        ",
        "            1!///////////////////3[//{3]%       ",
        "            )[<<33<3#////////////!4///(3)%      ",
        "           ::';__]}-)+[//////////!1(#//{3):     ",
        "          =$$&1$<<_}}::2!#///////{-:::'-]]':    ",
        "        :)&^^^^**<__};-:~-(////////{!331]]:%    ",
        "       ~=|^^>>>$4,4<,};;~2-#///////#!!331)=:    ",
        "      ;-$>>>>>>><@4<*];}~22;!///////#!!33[]'    ",
        "     ;_@>>##((>>*@4$*<-;;~2%-!#/////#((!33):.   ",
        "    ~},<(##(##(>>*$*$+-;;~22%[##/////#(!!^1'.   ",
        "    -_@!(####(>>>>**$-}};;2222!(#////#(({3['.   ",
        "   ;}_,!##//#(>(>**&&]}}};2222)!(#/#/##{!![=.   ",
        "   ;_,@>/#//##>>>^$)}}}};;~22%;!!(/#/##({^['.   ",
        "   ;_,@!#///#>>>>*&__}}};;;22.:<!!##/##((![=.   ",
        "  ';_,@>###/#>>>*&___}_};;~22%%+3!(####({{|'.   ",
        "  ~}_,@@(###><<<$4,_,_}}};;22%.+[!{###(({{[=.   ",
        "  2},,,@*#((@@@@4,_,___};;~22%%+[3!(###({{|=.   ",
        "  ~}_,,@@*(><@<@@4,,_}}};;~2.2.-[3!{(##({{[=.   ",
        "  2;_,,,@@*>*<*,,,____}};~~2.%%'[[!{((#({{|=.   ",
        "  ~}__,@,@,<*!<,___}}}};;~~22..-[[3{((((({[=.   ",
        "   ;}_,,,@@@,<<<_}}}}}};;~2222%+[[!{(((({{|=.   ",
        "   ~}}_,,,@,,,,<}]44};;;;222..:11[^!((({{{|=.   ",
        "   ;;}_,,,,@@@,,$&&&)-;22222.2'1[[^{{{(({{|=.   ",
        "    ;}}___,,,,_)&<&&+='~222..211[[^{({{({>|=.   ",
        "    ~;}}____,__&&&&+++'22.2.%=11[3^{({({{>|=.   ",
        "     ;}}}}}}}}}]&&]+=:::22..2)11|3{{{{{{{{|=.   ",
        "      ;;}}}}}}}=]]+='::%%.2%)11[|^{{({{{>>|=.   ",
        "       ;;;;;};;;=''::::%.%.)11[[|!>{{>{>>>|=.   ",
        "        ;;;};;;~%::%%:%%%%1111[|^{{({{>{>>|=.   ",
        "         ~~;~;~~2%:%%%%.=]11[[|3{{{{{{{>>^|=.   ",
        "           '~~~~%%:%%.')1111[[^^>{{{{>>>>^|=.   ",
        "            :+-''::'&111[1[||3{{{{{>>>>^>^|=.   ",
        "            '1*$[$[1[1[1[[[3^^{{{{{>{>^>^^|=.   ",
        "            '<333[[[[[[||3^^{{{{{{>>>^>^^^|=.   ",
        "            '3({!!^^3^3^^!{{{{{{{>>>>^>^^^|=.   ",
        "            =3((({!{!{!{{{{{{{{{>>>^^>^^^^|=.   ",
        "            '3###((({(({((({{{{{>{>>^^^^^^|=.   ",
        "            =3!!!!!^!^^^^|^^|^|||||||||||||'.   ",
        "            :++++++=+======================:.   ",
        "               .............................    ",
        "                                                ",
        "                                                ",
        "                                                "]


#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
from Plugins import register_report

register_report(
    report,
    _("Generate Web Site"),
    category=_("Web Page"),
    status=(_("Beta")),
    description=_("Generates web (HTML) pages for individuals, or a set of individuals."),
    xpm=get_xpm_image()
    )
