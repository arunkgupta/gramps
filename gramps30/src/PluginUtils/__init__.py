#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2006  Donald N. Allingham
# Copyright (C) 2008       Brian Matherly
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

#The following is bad, we import lists here, and obtain pointers to them
#If in _PluginMgr the list changes, that is ok, if however the list is
#assigned to another pointer eg export_list = then in this module we
#still retain the old pointer! ==> all actions may not change the pointer
#Better would be to do: import _PluginMgr as PluginMgr and then access
# the list as PluginUtils.PluginMgr, or use a function that returns the pointer
# of the list.
from _MenuOptions import (NumberOption, BooleanOption, TextOption, 
                          EnumeratedListOption, FilterOption, StringOption, 
                          ColourOption, PersonOption, PersonListOption, 
                          SurnameColourOption, FamilyOption, DestinationOption,
                          NoteOption, MediaOption)
from _GuiOptions import GuiMenuOptions
from _PluginMgr import (register_export, register_import, register_tool, 
                        register_report, register_relcalc, relationship_class, 
                        textdoc_list, drawdoc_list, bookdoc_list, 
                        bkitems_list, cl_list, cli_tool_list, load_plugins, 
                        import_list, export_list, report_list, 
                        quick_report_list, tool_list, register_text_doc, 
                        register_draw_doc, register_book_doc, 
                        register_quick_report)

from _Options import Options, OptionListCollection, OptionList, OptionHandler

import _Tool as Tool
import _Plugins as Plugins
import _PluginWindows as PluginWindows

# This needs to go above Tool and MenuOption as it needs both
class MenuToolOptions(GuiMenuOptions,Tool.ToolOptions):
    """
    The MenuToolOptions class implementes the ToolOptions
    functionality in a generic way so that the user does not need to
    be concerned with the graphical representation of the options.
    
    The user should inherit the MenuToolOptions class and override the
    add_menu_options function. The user can add options to the menu
    and the MenuToolOptions class will worry about setting up the GUI.
    """
    def __init__(self, name, person_id=None, dbstate=None):
        Tool.ToolOptions.__init__(self, name, person_id)
        GuiMenuOptions.__init__(self)


