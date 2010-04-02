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

"Database Processing/Rename event types"

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
import locale
import ManagedWindow
import AutoComp
from RelLib import EventType
from QuestionDialog import OkDialog
from PluginUtils import Tool, register_tool

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class ChangeTypes(Tool.BatchTool, ManagedWindow.ManagedWindow):

    def __init__(self, dbstate, uistate, options_class, name, callback=None):

        Tool.BatchTool.__init__(self, dbstate, options_class, name)
        if self.fail:
            return

        if uistate:
            self.title = _('Change Event Types')
            ManagedWindow.ManagedWindow.__init__(self,uistate,[],
                                                 self.__class__)
            self.init_gui()
        else:
            self.run_tool(cli=True)

    def init_gui(self):
        # Draw dialog and make it handle everything
        
        base = os.path.dirname(__file__)
        glade_file = "%s/%s" % (base,"changetype.glade")
        self.glade = gtk.glade.XML(glade_file,"top","gramps")
            
        self.auto1 = self.glade.get_widget("original")
        self.auto2 = self.glade.get_widget("new")

        # Need to display localized event names
        etype = EventType()
        event_names = etype.get_standard_names()
        event_names.sort(locale.strcoll)
        
        AutoComp.fill_combo(self.auto1,event_names)
        AutoComp.fill_combo(self.auto2,event_names)

        etype.set_from_xml_str(self.options.handler.options_dict['fromtype'])
        self.auto1.child.set_text(str(etype))

        etype.set_from_xml_str(self.options.handler.options_dict['totype'])
        self.auto2.child.set_text(str(etype))

        window = self.glade.get_widget('top')
        self.set_window(window,self.glade.get_widget('title'),self.title)

        self.glade.signal_autoconnect({
            "on_close_clicked"  : self.close,
            "on_apply_clicked"  : self.on_apply_clicked,
            })
            
        self.show()

    def build_menu_names(self,obj):
        return (self.title,None)

    def run_tool(self,cli=False):
        # Run tool and return results
        # These are English names, no conversion needed
        fromtype = self.options.handler.options_dict['fromtype']
        totype = self.options.handler.options_dict['totype']

        modified = 0

        self.trans = self.db.transaction_begin("",batch=True)
        self.db.disable_signals()
        if not cli:
            progress = Utils.ProgressMeter(_('Analyzing events'),'')
            progress.set_pass('',self.db.get_number_of_events())
            
        for event_handle in self.db.get_event_handles():
            event = self.db.get_event_from_handle(event_handle)
            if event.get_type().xml_str() == fromtype:
                event.type.set_from_xml_str(totype)
                modified += 1
                self.db.commit_event(event,self.trans)
            if not cli:
                progress.step()
        if not cli:
            progress.close()
        self.db.transaction_commit(self.trans,_('Change types'))
        self.db.enable_signals()
        self.db.request_rebuild()

        if modified == 0:
            msg = _("No event record was modified.")
        elif modified == 1:
            msg = _("1 event record was modified.")
        else:
            msg = _("%d event records were modified.") % modified

        if cli:
            print "Done: ", msg
        return (bool(modified),msg)

    def on_apply_clicked(self,obj):
        # Need to store English names for later comparison
        the_type = EventType()

        the_type.set(self.auto1.child.get_text())
        self.options.handler.options_dict['fromtype'] = the_type.xml_str()

        the_type.set(self.auto2.child.get_text())
        self.options.handler.options_dict['totype'] = the_type.xml_str()
        
        modified,msg = self.run_tool(cli=False)
        OkDialog(_('Change types'),msg,self.window)

        # Save options
        self.options.handler.save_options()
        
        self.close()

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
register_tool(
    name = 'chtype',
    category = Tool.TOOL_DBPROC,
    tool_class = ChangeTypes,
    options_class = ChangeTypesOptions,
    modes = Tool.MODE_GUI | Tool.MODE_CLI,
    translated_name = _("Rename event types"),
    status = _("Stable"),
    author_name = "Donald N. Allingham",
    author_email = "don@gramps-project.org",
    description = _("Allows all the events of a certain name "
                    "to be renamed to a new name.")
    )
