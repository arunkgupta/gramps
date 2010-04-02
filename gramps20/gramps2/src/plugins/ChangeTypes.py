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

"Database Processing/Rename personal event types"

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
import os
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
import const
import Utils
from QuestionDialog import OkDialog
import AutoComp
import Tool

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class ChangeTypes(Tool.Tool):
    def __init__(self,db,person,options_class,name,callback=None,parent=None):
        Tool.Tool.__init__(self,db,person,options_class,name)

        if parent:
            self.init_gui(parent)
        else:
            self.run_tool(cli=True)

    def init_gui(self,parent):
        # Draw dialog and make it handle everything
        self.parent = parent
        if self.parent.child_windows.has_key(self.__class__):
            self.parent.child_windows[self.__class__].present(None)
            return
        self.win_key = self.__class__
        
        base = os.path.dirname(__file__)
        glade_file = "%s/%s" % (base,"changetype.glade")
        self.glade = gtk.glade.XML(glade_file,"top","gramps")
            
        self.auto1 = self.glade.get_widget("original")
        self.auto2 = self.glade.get_widget("new")
            
        AutoComp.fill_combo(self.auto1,const.personalEvents)
        AutoComp.fill_combo(self.auto2,const.personalEvents)
        # Need to display localized event names
        self.auto1.child.set_text(const.display_event(
            self.options.handler.options_dict['fromtype']))
        self.auto2.child.set_text(const.display_event(
            self.options.handler.options_dict['totype']))

        self.title = _('Change Event Types')
        self.window = self.glade.get_widget('top')
        self.window.set_icon(self.parent.topWindow.get_icon())
        Utils.set_titles(self.window,
                         self.glade.get_widget('title'),
                         self.title)

        self.glade.signal_autoconnect({
            "on_close_clicked"  : self.close,
            "on_delete_event"   : self.on_delete_event,
            "on_apply_clicked"  : self.on_apply_clicked,
            })
            
        self.add_itself_to_menu()
        self.window.show()

    def run_tool(self,cli=False):
        # Run tool and return results
        # These are English names, no conversion needed
        fromtype = self.options.handler.options_dict['fromtype']
        totype = self.options.handler.options_dict['totype']

        modified = 0

        self.trans = self.db.transaction_begin()
        if not cli:
            progress = Utils.ProgressMeter(_('Analyzing events'),'')
            progress.set_pass('',self.db.get_number_of_people())
            
        for person_handle in self.db.get_person_handles(sort_handles=False):
            person = self.db.get_person_from_handle(person_handle)
            for event_handle in person.get_event_list():
                if not event_handle:
                    continue
                event = self.db.get_event_from_handle(event_handle)
                if event.get_name() == fromtype:
                    event.set_name(totype)
                    modified = modified + 1
                    self.db.commit_event(event,self.trans)
            if not cli:
                progress.step()
        if not cli:
            progress.close()
        self.db.transaction_commit(self.trans,_('Change types'))

        if modified == 0:
            msg = _("No event record was modified.")
        elif modified == 1:
            msg = _("1 event record was modified.")
        else:
            msg = _("%d event records were modified.") % modified

        if cli:
            print "Done: ", msg
        return (bool(modified),msg)

    def on_delete_event(self,obj,b):
        self.remove_itself_from_menu()

    def close(self,obj):
        self.remove_itself_from_menu()
        self.window.destroy()

    def add_itself_to_menu(self):
        self.parent.child_windows[self.win_key] = self
        self.parent_menu_item = gtk.MenuItem(self.title)
        self.parent_menu_item.connect("activate",self.present)
        self.parent_menu_item.show()
        self.parent.winsmenu.append(self.parent_menu_item)

    def remove_itself_from_menu(self):
        del self.parent.child_windows[self.win_key]
        self.parent_menu_item.destroy()

    def present(self,obj):
        self.window.present()

    def on_apply_clicked(self,obj):
        # Need to store English names for later comparison
        self.options.handler.options_dict['fromtype'] = const.save_event(
            unicode(self.auto1.child.get_text()))
        self.options.handler.options_dict['totype']   = const.save_event(
            unicode(self.auto2.child.get_text()))
        
        modified,msg = self.run_tool(cli=False)
        OkDialog(_('Change types'),msg,self.parent.topWindow)

        # Save options
        self.options.handler.save_options()
        
        self.close(None)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class ChangeTypesOptions(Tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self,name,person_id=None):
        Tool.ToolOptions.__init__(self,name,person_id)

    def set_new_options(self):
        # Options specific for this report
        self.options_dict = {
            'fromtype'   : '',
            'totype'     : '',
        }
        self.options_help = {
            'fromtype'   : ("=str","Type of events to replace",
                            "Event type string"),
            'totype'     : ("=str","New type replacing the old one",
                            "Event type string"),
        }

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
from PluginMgr import register_tool
register_tool(
    name = 'chtype',
    category = Tool.TOOL_DBPROC,
    tool_class = ChangeTypes,
    options_class = ChangeTypesOptions,
    modes = Tool.MODE_GUI | Tool.MODE_CLI,
    translated_name = _("Rename personal event types"),
    status = _("Stable"),
    author_name = "Donald N. Allingham",
    author_email = "don@gramps-project.org",
    description = _("Allows all the events of a certain name "
                    "to be renamed to a new name.")
    )
