#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2005  Donald N. Allingham
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

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os
import sets
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gobject
import gtk
import gtk.glade

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import GrampsKeys
import RelLib
import const
import Utils
import DateHandler
import GrampsDisplay
import QuestionDialog
from WindowUtils import GladeIf

#-------------------------------------------------------------------------
#
# Constants 
#
#-------------------------------------------------------------------------
INDEX         = "i"
OBJECT        = "o"
DATA          = "d"

_surname_styles = [
    _("Father's surname"),
    _("None"),
    _("Combination of mother's and father's surname"),
    _("Icelandic style"),
    ]

panellist = [
    (_("Display"),
     [( _("General"), 3),
      ( _("Dates"), 4),
      ( _("Toolbar and Statusbar"), 2)]),
    (_("Database"),
     [( _("General"), 1),
      ( _("GRAMPS IDs"), 6),
      ( _("Researcher Information"), 5)]),
    ]


# Not exactly gconf keys, but the functions directly dependent on them

def set_calendar_date_format():
    format_list = DateHandler.get_date_formats()
    DateHandler.set_format(GrampsKeys.get_date_format(format_list))

def _update_calendar_date_format(active,dlist):
    GrampsKeys.save_date_format(active,dlist)
    DateHandler.set_format(active)

#-------------------------------------------------------------------------
#
# make_path - 
#   Creates a directory if it does not already exist. Assumes that the
#   parent directory already exits
#
#-------------------------------------------------------------------------
def make_path(path):
    if not os.path.isdir(path):
        os.mkdir(path)

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def loadConfig():
    """
    Load preferences on startup. Not much to do, since all the prefs
    are in gconf and can be retrieved any time. 
    """
    make_path(os.path.expanduser("~/.gramps"))
    make_path(os.path.expanduser("~/.gramps/filters"))
    make_path(os.path.expanduser("~/.gramps/plugins"))
    make_path(os.path.expanduser("~/.gramps/templates"))
    make_path(os.path.expanduser("~/.gramps/thumb"))
    
#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def get_researcher():
    n = GrampsKeys.get_researcher_name()
    a = GrampsKeys.get_researcher_addr()
    c = GrampsKeys.get_researcher_city()
    s = GrampsKeys.get_researcher_state()
    ct = GrampsKeys.get_researcher_country()
    p = GrampsKeys.get_researcher_postal()
    ph = GrampsKeys.get_researcher_phone()
    e = GrampsKeys.get_researcher_email()

    owner = RelLib.Researcher()
    owner.set(n,a,c,s,ct,p,ph,e)
    return owner
    
#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class GrampsPreferences:
    def __init__(self,db):
        self.built = 0
        self.db = db
        self.top = gtk.glade.XML(const.prefsFile,"preferences","gramps")
        self.gladeif = GladeIf(self.top)

        self.gladeif.connect('button6','clicked',self.on_close_clicked)
        self.gladeif.connect('button7','clicked',self.on_propertybox_help)
        
        self.window = self.top.get_widget("preferences")
        self.window.connect('delete_event',self.on_close_clicked)
        self.tree = self.top.get_widget("tree")
        self.store = gtk.TreeStore(gobject.TYPE_STRING)
        self.selection = self.tree.get_selection()
        self.selection.connect('changed',self.select)
        col = gtk.TreeViewColumn('',gtk.CellRendererText(),text=0)
        self.tree.append_column(col)
        self.tree.set_model(self.store)
        self.panel = self.top.get_widget("panel")

        self.imap = {}
        self.build_tree()
        self.build()
        self.built = 1
        self.window.show()

    def build_tree(self):
        prev = None
        ilist = []
        for (name,lst) in panellist:
            node = self.store.insert_after(None, prev)
            self.store.set(node,0,name)
            next = None
            for (subname,tab) in lst:
                next = self.store.insert_after(node,next)
                ilist.append((next,tab))
                self.store.set(next,0,subname)
        for next,tab in ilist:
            path = self.store.get_path(next)
            self.imap[path] = tab
        
    def build(self):

        auto = self.top.get_widget("autoload")
        auto.set_active(GrampsKeys.get_autoload())
        auto.connect('toggled',
                lambda obj: GrampsKeys.save_autoload(obj.get_active()))

        spell = self.top.get_widget("spellcheck")
        spell.set_active(GrampsKeys.get_spellcheck())
        spell.connect('toggled',
                lambda obj: GrampsKeys.save_spellcheck(obj.get_active()))

        lds = self.top.get_widget("uselds")
        lds.set_active(GrampsKeys.get_uselds())
        lds.connect('toggled',
                lambda obj: GrampsKeys.save_uselds(obj.get_active()))

        self.ipr = self.top.get_widget("iprefix")
        self.ipr.set_text(GrampsKeys.get_person_id_prefix())
        self.opr = self.top.get_widget("oprefix")
        self.opr.set_text(GrampsKeys.get_object_id_prefix())
        self.fpr = self.top.get_widget("fprefix")
        self.fpr.set_text(GrampsKeys.get_family_id_prefix())
        self.spr = self.top.get_widget("sprefix")
        self.spr.set_text(GrampsKeys.get_source_id_prefix())
        self.ppr = self.top.get_widget("pprefix")
        self.ppr.set_text(GrampsKeys.get_place_id_prefix())

        sb2 = self.top.get_widget("stat2")
        sb3 = self.top.get_widget("stat3")
        if GrampsKeys.get_statusbar() == 0 or GrampsKeys.get_statusbar() == 1:
            sb2.set_active(1)
        else:
            sb3.set_active(1)
        sb2.connect('toggled',
                lambda obj: GrampsKeys.save_statusbar(2-obj.get_active()))

        toolbarmenu = self.top.get_widget("tooloptmenu")
        toolbarmenu.set_active(GrampsKeys.get_toolbar()+1)
        toolbarmenu.connect('changed',
                lambda obj: GrampsKeys.save_toolbar(obj.get_active()-1))

        pvbutton = self.top.get_widget('pvbutton')
        fvbutton = self.top.get_widget('fvbutton')
        if GrampsKeys.get_default_view() == 0:
            pvbutton.set_active(1)
        else:
            fvbutton.set_active(1)
        fvbutton.connect('toggled',
                lambda obj: GrampsKeys.save_default_view(obj.get_active()))

        familyview1 = self.top.get_widget('familyview1')
        familyview2 = self.top.get_widget('familyview2')
        if GrampsKeys.get_family_view() == 0:
            familyview1.set_active(1)
        else:
            familyview2.set_active(1)
        familyview2.connect('toggled',
                lambda obj: GrampsKeys.save_family_view(obj.get_active()))

        usetips = self.top.get_widget('usetips')
        usetips.set_active(GrampsKeys.get_usetips())
        usetips.connect('toggled',
                lambda obj: GrampsKeys.save_usetips(obj.get_active()))

        lastnamegen_obj = self.top.get_widget("lastnamegen")
        cell = gtk.CellRendererText()
        lastnamegen_obj.pack_start(cell,True)
        lastnamegen_obj.add_attribute(cell,'text',0)

        store = gtk.ListStore(str)
        for name in _surname_styles:
            store.append(row=[name])
        lastnamegen_obj.set_model(store)
        lastnamegen_obj.set_active(GrampsKeys.get_lastnamegen(_surname_styles))
        lastnamegen_obj.connect("changed", 
                lambda obj: 
                GrampsKeys.save_lastnamegen(obj.get_active(),_surname_styles)
                )

        date_option = self.top.get_widget("date_format")
        dlist = DateHandler.get_date_formats()
        date_option.pack_start(cell,True)
        date_option.add_attribute(cell,'text',0)

        store = gtk.ListStore(str)
        for item in dlist:
            store.append(row=[item])

        date_option.set_model(store)
        try:
            # Technically, a selected format might be out of range
            # for this locale's format list.
            date_option.set_active(GrampsKeys.get_date_format(dlist))
        except:
            date_option.set_active(0)

        date_option.connect("changed",
                lambda obj: 
                _update_calendar_date_format(obj.get_active(),dlist)
                )

        resname = self.top.get_widget("resname")
        resname.set_text(GrampsKeys.get_researcher_name())
        resname.connect('changed',
                    lambda obj: GrampsKeys.save_researcher_name(obj.get_text()))
        resaddr = self.top.get_widget("resaddr")
        resaddr.set_text(GrampsKeys.get_researcher_addr())
        resaddr.connect('changed',
                    lambda obj: GrampsKeys.save_researcher_addr(obj.get_text()))
        rescity = self.top.get_widget("rescity")
        rescity.set_text(GrampsKeys.get_researcher_city())
        rescity.connect('changed',
                    lambda obj: GrampsKeys.save_researcher_city(obj.get_text()))
        resstate = self.top.get_widget("resstate")
        resstate.set_text(GrampsKeys.get_researcher_state())
        resstate.connect('changed',
                    lambda obj: GrampsKeys.save_researcher_state(obj.get_text()))
        rescountry = self.top.get_widget("rescountry")
        rescountry.set_text(GrampsKeys.get_researcher_country())
        rescountry.connect('changed',
                    lambda obj: GrampsKeys.save_researcher_country(obj.get_text()))
        respostal = self.top.get_widget("respostal")
        respostal.set_text(GrampsKeys.get_researcher_postal())
        respostal.connect('changed',
                    lambda obj: GrampsKeys.save_researcher_postal(obj.get_text()))
        resphone = self.top.get_widget("resphone")
        resphone.set_text(GrampsKeys.get_researcher_phone())
        resphone.connect('changed',
                    lambda obj: GrampsKeys.save_researcher_phone(obj.get_text()))
        resemail = self.top.get_widget("resemail")
        resemail.set_text(GrampsKeys.get_researcher_email())
        resemail.connect('changed',
                    lambda obj: GrampsKeys.save_researcher_email(obj.get_text()))
                    
    def save_prefix(self):
        """ Validate the GRAMPS ID definitions to be usable"""
        ip = self.ipr.get_text()
        op = self.opr.get_text()
        fp = self.fpr.get_text()
        sp = self.spr.get_text()
        pp = self.ppr.get_text()
        
        # Do validation to the GRAMPS-ID format strings
        invalid_chars = sets.Set("# \t\n\r")
        prefixes = [ip,op,fp,sp,pp]
        testnums = [1,234,567890]
        testresult = {} # used to test that IDs for different objects will be different
        formaterror = False # true if formatstring is invalid
        incompatible = False    # true if ID string is possibly not GEDCOM compatible
        for p in prefixes:
            if invalid_chars & sets.Set(p):
                incompatible = True
            for n in testnums:
                try:
                    testresult[p % n] = 1
                except:
                    formaterror = True
        
        idexampletext = _('Example for valid IDs are:\n'+
                        'I%d which will be displayed as I123 or\n'+
                        'S%06d which will be displayed as S000123.')
        if formaterror:
            QuestionDialog.ErrorDialog( _("Invalid GRAMPS ID prefix"),
                _("The GRAMPS ID prefix is invalid.\n")+
                idexampletext,
                self.window)
            return False
        elif incompatible:
            QuestionDialog.OkDialog( _("Incompatible GRAMPS ID prefix"),
                _("The GRAMPS ID prefix is in an unusual format and may"+
                " cause problems when exporting the database to GEDCOM format.\n")+
                idexampletext,
                self.window)
        elif len(testresult) != len(prefixes)*len(testnums):
            QuestionDialog.ErrorDialog( _("Unsuited GRAMPS ID prefix"),
                _("The GRAMPS ID prefix is unsuited because it does not"+
                " distinguish between different objects.\n")+
                idexampletext,
                self.window)
            return False

        GrampsKeys.save_iprefix(ip)
        GrampsKeys.save_oprefix(op)
        GrampsKeys.save_fprefix(fp)
        GrampsKeys.save_sprefix(sp)
        GrampsKeys.save_pprefix(pp)
        return True
        
    def select(self,obj):
        store,node = self.selection.get_selected()
        if node:
            path = store.get_path(node)
        if node and self.imap.has_key(path):
            self.panel.set_current_page(self.imap[path])
        
    def on_propertybox_help(self,obj):
        GrampsDisplay.help('gramps-prefs')

    def on_close_clicked(self,obj=None,dummy=None):
        if not self.save_prefix():
            return False
        self.gladeif.close()
        self.window.destroy()
    
#-------------------------------------------------------------------------
#
# Create the property box, and set the elements off the current values
#
#-------------------------------------------------------------------------
def display_preferences_box(db):
    GrampsPreferences(db)
