#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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
# standard python modules
#
#------------------------------------------------------------------------
import os

#------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#------------------------------------------------------------------------
from gtk import glade
#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
import soundex
import GrampsDisplay
import ManagedWindow
import AutoComp
from TransUtils import sgettext as _
from PluginUtils import Tool, register_tool

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = 'Gramps_3.0_Wiki_Manual_-_Tools'
WIKI_HELP_SEC = _('manual|Generate_SoundEx_codes')
#-------------------------------------------------------------------------
#
# SoundGen.py
#
#-------------------------------------------------------------------------

class SoundGen(Tool.Tool, ManagedWindow.ManagedWindow):

    def __init__(self, dbstate, uistate, options_class, name, callback=None):
        self.label = _('SoundEx code generator')
        Tool.Tool.__init__(self, dbstate, options_class, name)
        ManagedWindow.ManagedWindow.__init__(self,uistate,[],self.__class__)

        base = os.path.dirname(__file__)
        glade_file = base + os.sep + "soundex.glade"

        self.glade = glade.XML(glade_file,"soundEx","gramps")
        self.glade.signal_autoconnect({
            "destroy_passed_object" : self.close,
            "on_help_clicked"       : self.on_help_clicked,
        })

        window = self.glade.get_widget("soundEx")
        self.set_window(window,self.glade.get_widget('title'),self.label)

        self.value = self.glade.get_widget("value")
        self.autocomp = self.glade.get_widget("name_list")
        self.name = self.autocomp.child

        self.name.connect('changed',self.on_apply_clicked)

        names = []
        person = None
        for person_handle in self.db.get_person_handles(sort_handles=False):
            person = self.db.get_person_from_handle(person_handle)
            lastname = person.get_primary_name().get_surname()
            if lastname not in names:
                names.append(lastname)

        names.sort()

        AutoComp.fill_combo(self.autocomp, names)

        if person:
            n = person.get_primary_name().get_surname()
            self.name.set_text(n)
            try:
                se_text = soundex.soundex(n)
            except UnicodeEncodeError:
                se_text = soundex.soundex('')
            self.value.set_text(se_text)
        else:
            self.name.set_text("")
            
        self.show()

    def on_help_clicked(self, obj):
        """Display the relevant portion of GRAMPS manual"""
        GrampsDisplay.help('tools-util-other', WIKI_HELP_PAGE , WIKI_HELP_SEC)

    def build_menu_names(self, obj):
        return (self.label,None)

    def on_apply_clicked(self, obj):
        try:
            se_text = soundex.soundex(unicode(obj.get_text()))
        except UnicodeEncodeError:
            se_text = soundex.soundex('')
        self.value.set_text(se_text)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class SoundGenOptions(Tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name,person_id=None):
        Tool.ToolOptions.__init__(self, name,person_id)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
register_tool(
    name = 'soundgen',
    category = Tool.TOOL_UTILS,
    tool_class = SoundGen,
    options_class = SoundGenOptions,
    modes = Tool.MODE_GUI,
    translated_name = _("Generate SoundEx Codes"),
    status=(_("Stable")),
    author_name = "Donald N. Allingham",
    author_email = "don@gramps-project.org",
    description = _("Generates SoundEx codes for names")
    )
