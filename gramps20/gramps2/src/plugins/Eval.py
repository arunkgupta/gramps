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

"""
Provides a python evaluation window
"""
#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
import os
import cStringIO
import sys
from gettext import gettext as _

#------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#------------------------------------------------------------------------
import gtk
import gtk.glade

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
import Utils
import Tool

#-------------------------------------------------------------------------
#
# Actual tool
#
#-------------------------------------------------------------------------
class Eval(Tool.Tool):
    def __init__(self,db,person,options_class,name,callback=None,parent=None):
        Tool.Tool.__init__(self,db,person,options_class,name)

        self.parent = parent
        if self.parent.child_windows.has_key(self.__class__):
            self.parent.child_windows[self.__class__].present(None)
            return
        self.win_key = self.__class__

        glade_file = "%s/%s" % (os.path.dirname(__file__),"eval.glade")
        self.glade = gtk.glade.XML(glade_file,"top","gramps")

        self.top = self.glade.get_widget("top")
        self.top.set_icon(self.parent.topWindow.get_icon())
        self.dbuf = self.glade.get_widget("display").get_buffer()
        self.ebuf = self.glade.get_widget("eval").get_buffer()
        self.error = self.glade.get_widget("error").get_buffer()

        self.glade.signal_autoconnect({
            "on_apply_clicked" : self.apply_clicked,
            "on_close_clicked" : self.close_clicked,
            "on_delete_event"  : self.on_delete_event,
            "on_clear_clicked" : self.clear_clicked,
            })

        Utils.set_titles(self.top,self.glade.get_widget('title'),
                         _("Python evaluation window"))

        self.add_itself_to_menu()
        self.top.show()

    def on_delete_event(self,obj,b):
        self.remove_itself_from_menu()

    def close_clicked(self,obj):
        self.remove_itself_from_menu()
        self.top.destroy()

    def add_itself_to_menu(self):
        self.parent.child_windows[self.win_key] = self
        self.parent_menu_item = gtk.MenuItem(_('Python evaluation window'))
        self.parent_menu_item.connect("activate",self.present)
        self.parent_menu_item.show()
        self.parent.winsmenu.append(self.parent_menu_item)

    def remove_itself_from_menu(self):
        del self.parent.child_windows[self.win_key]
        self.parent_menu_item.destroy()

    def present(self,obj):
        self.top.present()

    def apply_clicked(self,obj):
        text = unicode(self.ebuf.get_text(self.ebuf.get_start_iter(),
                                  self.ebuf.get_end_iter(),False))

        outtext = cStringIO.StringIO()
        errtext = cStringIO.StringIO()
        sys.stdout = outtext
        sys.stderr = errtext
        exec(text)
        self.dbuf.set_text(outtext.getvalue())
        self.error.set_text(errtext.getvalue())
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def clear_clicked(self,obj):
        self.dbuf.set_text("")
        self.ebuf.set_text("")
        self.error.set_text("")

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class EvalOptions(Tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self,name,person_id=None):
        Tool.ToolOptions.__init__(self,name,person_id)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------

if __debug__:
    from PluginMgr import register_tool

    register_tool(
        name = 'eval',
        category = Tool.TOOL_DEBUG,
        tool_class = Eval,
        options_class = EvalOptions,
        modes = Tool.MODE_GUI,
        translated_name = _("Python evaluation window"),
        status = _("Stable"),
        author_name = "Donald N. Allingham",
        author_email = "don@gramps-project.org",
        description=_("Provides a window that can evaluate python code")
        )
