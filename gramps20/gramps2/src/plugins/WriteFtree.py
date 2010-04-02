#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2003-2005  Donald N. Allingham
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

"Export to Web Family Tree"

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
import os
from cStringIO import StringIO
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#-------------------------------------------------------------------------
import gtk
import gtk.glade
import gnome

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import Utils
import GenericFilter
import Errors
from QuestionDialog import ErrorDialog

#-------------------------------------------------------------------------
#
# writeData
#
#-------------------------------------------------------------------------
def writeData(database,filename,person,option_box):
    ret = 0
    try:
        writer = FtreeWriter(database,person,0,filename,option_box)
        ret = writer.export_data()
    except:
        import DisplayTrace
        DisplayTrace.DisplayTrace()
    return ret
    
class FtreeWriterOptionBox:
    """
    Create a VBox with the option widgets and define methods to retrieve
    the options. 
    """
    def __init__(self,person):
        self.person = person

    def get_option_box(self):
        self.restrict = True
        base = os.path.dirname(__file__)
        glade_file = "%s/%s" % (base,"writeftree.glade")
        
        self.top = gtk.glade.XML(glade_file,"top","gramps")

        filter_obj = self.top.get_widget("filter")

        all = GenericFilter.GenericFilter()
        all.set_name(_("Entire Database"))
        all.add_rule(GenericFilter.Everyone([]))
        
        if self.person:
            des = GenericFilter.GenericFilter()
            des.set_name(_("Descendants of %s") %
                         self.person.get_primary_name().get_name())
            des.add_rule(GenericFilter.IsDescendantOf(
                [self.person.get_gramps_id(),1]))
        
            ans = GenericFilter.GenericFilter()
            ans.set_name(_("Ancestors of %s")
                         % self.person.get_primary_name().get_name())
            ans.add_rule(GenericFilter.IsAncestorOf(
                [self.person.get_gramps_id(),1]))
        
            com = GenericFilter.GenericFilter()
            com.set_name(_("People with common ancestor with %s") %
                         self.person.get_primary_name().get_name())
            com.add_rule(GenericFilter.HasCommonAncestorWith(
                [self.person.get_gramps_id()]))
        
            self.filter_menu = GenericFilter.build_filter_menu([all,des,ans,com])
        else:
            self.filter_menu = GenericFilter.build_filter_menu([all])
        filter_obj.set_menu(self.filter_menu)

        the_box = self.top.get_widget("vbox1")
        the_parent = self.top.get_widget('dialog-vbox1')
        the_parent.remove(the_box)
        self.top.get_widget("top").destroy()
        return the_box

    def parse_options(self):
        self.restrict = self.top.get_widget("restrict").get_active()
        self.cfilter = self.filter_menu.get_active().get_data("filter")

#-------------------------------------------------------------------------
#
# FtreeWriter
#
#-------------------------------------------------------------------------
class FtreeWriter:

    def __init__(self,database,person,cl=0,filename="",option_box=None):
        self.db = database
        self.person = person
        self.option_box = option_box
        self.cl = cl
        self.filename = filename

        self.plist = {}

        if not option_box:
            self.cl_setup()
        else:
            self.option_box.parse_options()

            self.restrict = self.option_box.restrict
            if self.option_box.cfilter == None:
                for p in self.db.get_person_handles(sort_handles=False):
                    self.plist[p] = 1
            else:
                try:
                    for p in self.option_box.cfilter.apply(self.db, self.db.get_person_handles(sort_handles=False)):
                        self.plist[p] = 1
                except Errors.FilterError, msg:
                    (m1,m2) = msg.messages()
                    ErrorDialog(m1,m2)
                    return

    def cl_setup(self):
        self.restrict = True
        for p in self.db.get_person_handles(sort_handles=False):
            self.plist[p] = 1

    def export_data(self):
        name_map = {}
        id_map = {}
        id_name = {}
        for key in self.plist:
            pn = self.db.get_person_from_handle(key).get_primary_name()
            sn = pn.get_surname()
            items = pn.get_first_name().split()
            if len(items) > 0:
                n = "%s %s" % (items[0],sn)
            else:
                n = sn

            count = -1
            if name_map.has_key(n):
                count = 0
                while 1:
                    nn = "%s%d" % (n,count)
                    if not name_map.has_key(nn):
                        break;
                    count += 1
                name_map[nn] = key
                id_map[key] = nn
            else:
                name_map[n] = key
                id_map[key] = n
            id_name[key] = get_name(pn,count)

        f = open(self.filename,"w")

        for key in self.plist:
            p = self.db.get_person_from_handle(key)
            name = id_name[key]
            father = ""
            mother = ""
            email = ""
            web = ""

            family_handle = p.get_main_parents_family_handle()
            if family_handle:
                family = self.db.get_family_from_handle(family_handle)
                if family.get_father_handle() and id_map.has_key(family.get_father_handle()):
                    father = id_map[family.get_father_handle()]
                if family.get_mother_handle() and id_map.has_key(family.get_mother_handle()):
                    mother = id_map[family.get_mother_handle()]

            #
            # Calculate Date
            #
            birth_handle = p.get_birth_handle()
            death_handle = p.get_death_handle()
            if birth_handle:
                birth_event = self.db.get_event_from_handle(birth_handle)
                birth = birth_event.get_date_object()
            else:
                birth = None
            if death_handle:
                death_event = self.db.get_event_from_handle(death_handle)
                death = death_event.get_date_object()
            else:
                death = None

            if self.restrict:
                alive = Utils.probably_alive(p,self.db)
            else:
                alive = 0
                
            if birth and not alive:
                if death and not alive :
                    dates = "%s-%s" % (fdate(birth),fdate(death))
                else:
                    dates = fdate(birth)
            else:
                if death and not alive:
                    dates = fdate(death)
                else:
                    dates = ""
                        
            f.write('%s;%s;%s;%s;%s;%s\n' % (name,father,mother,email,web,dates))
            
        f.close()
        return 1

def fdate(val):
    if val.get_year_valid():
        if val.get_month_valid():
            if val.get_day_valid():
                return "%d/%d/%d" % (val.get_day(),val.get_month(),val.get_year())
            else:
                return "%d/%d" % (val.get_month(),val.get_year())
        else:
            return "%d" % val.get_year()
    else:
        return ""

def get_name(name,count):
    """returns a name string built from the components of the Name
    instance, in the form of Firstname Surname"""
    if count == -1:
        val = ""
    else:
        val = str(count)
        
    if (name.suffix == ""):
        if name.prefix:
            return "%s %s %s%s" % (name.first_name, name.prefix, name.surname, val)
        else:
            return "%s %s%s" % (name.first_name, name.surname, val)
    else:
        if name.prefix:
            return "%s %s %s%s, %s" % (name.first_name, name.prefix, name.surname, val, name.Suffix)
        else:
            return "%s %s%s, %s" % (name.first_name, name.surname, val, name.suffix)

#-------------------------------------------------------------------------
#
# Register the plugin
#
#-------------------------------------------------------------------------
_title = _('_Web Family Tree')
_description = _('Web Family Tree format.')
_config = (_('Web Family Tree export options'),FtreeWriterOptionBox)
_filename = 'wft'

from PluginMgr import register_export
register_export(writeData,_title,_description,_config,_filename)
