#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
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

"""Tools/Utilities/Generate SoundEx Codes"""

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gramps.gen.const import URL_MANUAL_PAGE
from gramps.gen.soundex import soundex
from gramps.gui.display import display_help
from gramps.gui.managedwindow import ManagedWindow
from gramps.gui.autocomp import fill_combo
from gramps.gen.ggettext import sgettext as _
from gramps.gui.plug import tool
from gramps.gui.glade import Glade

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = '%s_-_Tools' % URL_MANUAL_PAGE
WIKI_HELP_SEC = _('manual|Generate_SoundEx_codes')

#-------------------------------------------------------------------------
#
# SoundGen.py
#
#-------------------------------------------------------------------------

class SoundGen(tool.Tool, ManagedWindow):

    def __init__(self, dbstate, uistate, options_class, name, callback=None):
        self.label = _('SoundEx code generator')
        tool.Tool.__init__(self, dbstate, options_class, name)
        ManagedWindow.__init__(self,uistate,[],self.__class__)

        self.glade = Glade()
        self.glade.connect_signals({
            "destroy_passed_object" : self.close,
            "on_help_clicked"       : self.on_help_clicked,
            "on_delete_event"       : self.close,
        })

        window = self.glade.toplevel
        self.set_window(window,self.glade.get_object('title'),self.label)

        self.value = self.glade.get_object("value")
        self.autocomp = self.glade.get_object("name_list")
        self.name = self.autocomp.get_child()

        self.name.connect('changed',self.on_apply_clicked)

        names = []
        person = None
        for person in self.db.iter_people():
            lastname = person.get_primary_name().get_surname()
            if lastname not in names:
                names.append(lastname)

        names.sort()

        fill_combo(self.autocomp, names)

        if person:
            n = person.get_primary_name().get_surname()
            self.name.set_text(n)
            try:
                se_text = soundex(n)
            except UnicodeEncodeError:
                se_text = soundex('')
            self.value.set_text(se_text)
        else:
            self.name.set_text("")
            
        self.show()

    def on_help_clicked(self, obj):
        """Display the relevant portion of GRAMPS manual"""
        display_help(WIKI_HELP_PAGE , WIKI_HELP_SEC)

    def build_menu_names(self, obj):
        return (self.label,None)

    def on_apply_clicked(self, obj):
        try:
            se_text = soundex(unicode(obj.get_text()))
        except UnicodeEncodeError:
            se_text = soundex('')
        self.value.set_text(se_text)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class SoundGenOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name,person_id=None):
        tool.ToolOptions.__init__(self, name,person_id)
