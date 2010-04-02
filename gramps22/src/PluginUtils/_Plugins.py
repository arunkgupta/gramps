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

"""
The core of the GRAMPS plugin system. This module provides tasks to load
plugins from specfied directories, build menus for the different categories,
and provide dialog to select and execute plugins.

Plugins are divided into several categories. This are: reports, tools,
importers, exporters, and document generators.
"""

#-------------------------------------------------------------------------
#
# GTK libraries
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
import os
import sys
import re
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import const
import Config
import Errors
from ReportBase import report, standalone_categories
import _Tool
import _PluginMgr
import _PluginStatus
import ManagedWindow

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
REPORTS = 0
TOOLS   = 1
UNSUPPORTED = _("Unsupported")

#-------------------------------------------------------------------------
#
# PluginDialog interface class
#
#-------------------------------------------------------------------------

class PluginDialog(ManagedWindow.ManagedWindow):
    """Displays the dialog box that allows the user to select the
    report that is desired."""

    def __init__(self,state, uistate, track, item_list,categories,msg,
                 label=None,button_label=None,tool_tip=None,content=REPORTS):
        """Display the dialog box, and build up the list of available
        reports. This is used to build the selection tree on the left
        hand side of the dailog box."""
        
        self.active = state.active
        self.imap = {}
        self.msg = msg
        self.content = content

        ManagedWindow.ManagedWindow.__init__(self,uistate,[],self.__class__)

        self.state = state
        self.uistate = uistate
        
        self.dialog = gtk.glade.XML(const.plugins_glade,"report","gramps")
        self.dialog.signal_autoconnect({
            "on_report_apply_clicked" : self.on_apply_clicked,
            "destroy_passed_object"   : self.close,
            })

        self.tree = self.dialog.get_widget("tree")
        window = self.dialog.get_widget("report")
        self.title = self.dialog.get_widget("title")

        self.set_window(window, self.title, msg )

        self.store = gtk.TreeStore(str)
        self.selection = self.tree.get_selection()
        self.selection.connect('changed', self.on_node_selected)
        col = gtk.TreeViewColumn('',gtk.CellRendererText(),text=0)
        self.tree.append_column(col)
        self.tree.set_model(self.store)
        
        self.description = self.dialog.get_widget("description")
        if label:
            self.description.set_text(label)
        self.status = self.dialog.get_widget("report_status")
        
        self.author_name = self.dialog.get_widget("author_name")
        self.author_email = self.dialog.get_widget("author_email")
        
        self.apply_button = self.dialog.get_widget("apply")
        if button_label:
            self.apply_button.set_label(button_label)
        else:
            self.apply_button.set_label(_("_Apply"))
        self.apply_button.set_use_underline(True)
        if tool_tip:
            try:
                tt = gtk.tooltips_data_get(self.apply_button)
                if tt:
                    tt[0].set_tip(self.apply_button,tool_tip)
            except AttributeError:
                pass

        self.item = None
        self.build_plugin_tree(item_list,categories)
        uistate.connect('plugins-reloaded',self.rebuild)
        self.show()

    def rebuild(self,tool_list,report_list):
        # This method needs to be overridden in the subclass
        assert False, "This method needs to be overridden in the subclass."

    def build_menu_names(self,obj):
        return (self.msg,None)

    def on_apply_clicked(self,obj):
        """Execute the selected report"""
        try:
            (item_class,options_class,title,category,
             name,require_active) = self.item
            if self.content == REPORTS:
                report(self.state,self.uistate,self.state.active,
                       item_class,options_class,title,name,category,require_active)
            else:
                _Tool.gui_tool(self.state,self.uistate, 
                              item_class,options_class,title,name,category,
                              self.state.db.request_rebuild)
        except TypeError:
            pass # ignore pressing apply without a plugin being selected
        
    def on_node_selected(self,obj):
        """Updates the informational display on the right hand side of
        the dialog box with the description of the selected report"""

        store,node = self.selection.get_selected()
        if node:
            path = store.get_path(node)
        if not node or not self.imap.has_key(path):
            return 
        data = self.imap[path]

        (report_class,options_class,title,category,name,
         doc,status,author,email,unsupported,require_active) = data
        self.description.set_text(doc)
        if unsupported:
            status = UNSUPPORTED
        self.status.set_text(status)
        self.title.set_text('<span weight="bold" size="larger">%s</span>' \
                            % title)
        self.title.set_use_markup(1)
        self.author_name.set_text(author)
        self.author_email.set_text(email)
        self.item = (report_class,options_class,title,category,
                     name,require_active)

    def build_plugin_tree(self,item_list,categories):
        """Populates a GtkTree with each menu item assocated with a entry
        in the lists. The list must consist of a tuples with the following
        format:
        
        (item_class,options_class,title,category,name,
         doc,status,author,email)

        Items in the same category are grouped under the same submenu.
        The categories must be dicts from integer to string.
        """

        ilist = []
        self.store.clear()

        # build the tree items and group together based on the category name
        item_hash = {}
        for plugin in item_list:
            if plugin[9]:
                category = UNSUPPORTED
            else:
                category = categories[plugin[3]]
            if item_hash.has_key(category):
                item_hash[category].append(plugin)
            else:
                item_hash[category] = [plugin]

        # add a submenu for each category, and populate it with the
        # GtkTreeItems that are associated with it.
        key_list = [ item for item in item_hash.keys() if item != UNSUPPORTED]
        key_list.sort()
        key_list.reverse()
        
        prev = None
        if item_hash.has_key(UNSUPPORTED):
            key = UNSUPPORTED
            data = item_hash[key]
            node = self.store.insert_after(None,prev)
            self.store.set(node,0,key)
            next = None
            data.sort(lambda x,y: cmp(x[2],y[2]))
            for item in data:
                next = self.store.insert_after(node,next)
                ilist.append((next,item))
                self.store.set(next,0,item[2])
        for key in key_list:
            data = item_hash[key]
            node = self.store.insert_after(None,prev)
            self.store.set(node,0,key)
            next = None
            data.sort(lambda x,y: cmp(x[2],y[2]))
            for item in data:
                next = self.store.insert_after(node,next)
                ilist.append((next,item))
                self.store.set(next,0,item[2])
        for next,tab in ilist:
            path = self.store.get_path(next)
            self.imap[path] = tab

#-------------------------------------------------------------------------
#
# ReportPlugins interface class
#
#-------------------------------------------------------------------------
class ReportPlugins(PluginDialog):
    """Displays the dialog box that allows the user to select the
    report that is desired."""

    def __init__(self,dbstate,uistate,track):
        """Display the dialog box, and build up the list of available
        reports. This is used to build the selection tree on the left
        hand side of the dailog box."""

        PluginDialog.__init__(
            self,
            dbstate,
            uistate,
            track,
            _PluginMgr.report_list,
            standalone_categories,
            _("Report Selection"),
            _("Select a report from those available on the left."),
            _("_Generate"), _("Generate selected report"),
            REPORTS)

    def rebuild(self,tool_list,report_list):
        self.build_plugin_tree(report_list,standalone_categories)

#-------------------------------------------------------------------------
#
# ToolPlugins interface class
#
#-------------------------------------------------------------------------
class ToolPlugins(PluginDialog):
    """Displays the dialog box that allows the user to select the tool
    that is desired."""

    __signals__ = {
        'plugins-reloaded' : (list,list),
        }
    def __init__(self,dbstate,uistate,track):
        """Display the dialog box, and build up the list of available
        reports. This is used to build the selection tree on the left
        hand side of the dailog box."""

        PluginDialog.__init__(
            self,
            dbstate,
            uistate,
            track,
            _PluginMgr.tool_list,
            _Tool.tool_categories,
            _("Tool Selection"),
            _("Select a tool from those available on the left."),
            _("_Run"),
            _("Run selected tool"),
            TOOLS)

    def rebuild(self,tool_list,report_list):
        self.build_plugin_tree(tool_list,_Tool.tool_categories)

#-------------------------------------------------------------------------
#
# Reload plugins
#
#-------------------------------------------------------------------------
class Reload(_Tool.Tool):
    def __init__(self, dbstate, uistate, options_class, name, callback=None):
        """
        Treated as a callback, causes all plugins to get reloaded.
        This is useful when writing and debugging a plugin.
        """
        _Tool.Tool.__init__(self,dbstate,options_class,name)
    
        pymod = re.compile(r"^(.*)\.py$")

        oldfailmsg = _PluginMgr.failmsg_list[:]
        _PluginMgr.failmsg_list = []

        # attempt to reload all plugins that have succeeded in the past
        for plugin in _PluginMgr.success_list:
            filename = plugin[0]
            filename = filename.replace('pyc','py')
            filename = filename.replace('pyo','py')
            try: 
                reload(plugin[1])
            except:
                _PluginMgr.failmsg_list.append((filename,sys.exc_info()))
            
        # Remove previously good plugins that are now bad
        # from the registered lists
        (_PluginMgr.export_list,
         _PluginMgr.import_list,
         _PluginMgr.tool_list,
         _PluginMgr.cli_tool_list,
         _PluginMgr.report_list,
         _PluginMgr.bkitems_list,
         _PluginMgr.cl_list,
         _PluginMgr.textdoc_list,
         _PluginMgr.bookdoc_list,
         _PluginMgr.drawdoc_list) = _PluginMgr.purge_failed(
            _PluginMgr.failmsg_list,
            _PluginMgr.export_list,
            _PluginMgr.import_list,
            _PluginMgr.tool_list,
            _PluginMgr.cli_tool_list,
            _PluginMgr.report_list,
            _PluginMgr.bkitems_list,
            _PluginMgr.cl_list,
            _PluginMgr.textdoc_list,
            _PluginMgr.bookdoc_list,
            _PluginMgr.drawdoc_list)

        # attempt to load the plugins that have failed in the past
        for (filename,message) in oldfailmsg:
            name = os.path.split(filename)
            match = pymod.match(name[1])
            if not match:
                continue
            _PluginMgr.attempt_list.append(filename)
            plugin = match.groups()[0]
            try: 
                # For some strange reason second importing of a failed plugin
                # results in success. Then reload reveals the actual error.
                # Looks like a bug in Python.
                a = __import__(plugin)
                reload(a)
                _PluginMgr.success_list.append((filename,a))
            except:
                _PluginMgr.failmsg_list.append((filename,sys.exc_info()))

        # attempt to load any new files found
        for directory in _PluginMgr.loaddir_list:
            for filename in os.listdir(directory):
                name = os.path.split(filename)
                match = pymod.match(name[1])
                if not match:
                    continue
                if filename in _PluginMgr.attempt_list:
                    continue
                _PluginMgr.attempt_list.append(filename)
                plugin = match.groups()[0]
                try: 
                    a = __import__(plugin)
                    if a not in [plugin[1]
                                 for plugin in _PluginMgr.success_list]:
                        _PluginMgr.success_list.append((filename,a))
                except:
                    _PluginMgr.failmsg_list.append((filename,sys.exc_info()))

        if Config.get(Config.POP_PLUGIN_STATUS) \
               and len(_PluginMgr.failmsg_list):
            try:
                _PluginStatus.PluginStatus(dbstate,uistate)
            except Errors.WindowActiveError:
                old_win = uistate.gwm.get_item_from_id(
                    _PluginStatus.PluginStatus)
                old_win.close()
                _PluginStatus.PluginStatus(dbstate,uistate)

        # Emit signal to re-generate tool and report menus
        uistate.emit('plugins-reloaded',
                     (_PluginMgr.tool_list,_PluginMgr.report_list))

class ReloadOptions(_Tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self,name,person_id=None):
        _Tool.ToolOptions.__init__(self,name,person_id)

#-------------------------------------------------------------------------
#
# Register the plugin reloading tool
#
#-------------------------------------------------------------------------

if __debug__:
    _PluginMgr.register_tool(
        name = 'reload',
        category = _Tool.TOOL_DEBUG,
        tool_class = Reload,
        options_class = ReloadOptions,
        modes = _Tool.MODE_GUI,
        translated_name = _("Reload plugins"),
        description=_("Attempt to reload plugins. "
                      "Note: This tool itself is not reloaded!"),
        )
