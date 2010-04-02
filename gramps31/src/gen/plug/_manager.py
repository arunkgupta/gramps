#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2005  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
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
The core of the GRAMPS plugin system. This module provides capability to load
plugins from specfied directories and provide information about the loaded
plugins.

Plugins are divided into several categories. These are: reports, tools,
importers, exporters, quick reports, and document generators.
"""

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
import gen.utils
import Relationship

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
_UNAVAILABLE = _("No description was provided")

#-------------------------------------------------------------------------
#
# PluginManager
#
#-------------------------------------------------------------------------
class PluginManager(gen.utils.Callback):
    """ PluginManager is a Singleton which manages plugins """
    __instance = None
    
    __signals__ = { 'plugins-reloaded' : None }
    
    # Modes for generating reports
    REPORT_MODE_GUI = 1    # Standalone report using GUI
    REPORT_MODE_BKI = 2    # Book Item interface using GUI
    REPORT_MODE_CLI = 4    # Command line interface (CLI)
    
    # Modes for running tools
    TOOL_MODE_GUI = 1    # Standard tool using GUI
    TOOL_MODE_CLI = 2    # Command line interface (CLI)
    
    def get_instance():
        """ Use this function to get the instance of the PluginManager """
        if PluginManager.__instance is None:
            PluginManager.__instance = 1 # Set to 1 for __init__()
            PluginManager.__instance = PluginManager()
        return PluginManager.__instance
    get_instance = staticmethod(get_instance)
            
    def __init__(self):
        """ This function should only be run once by get_instance() """
        if PluginManager.__instance is not 1:
            raise Exception("This class is a singleton. "
                            "Use the get_instance() method")
            
        gen.utils.Callback.__init__(self)
            
        self.__report_list       = []
        self.__quick_report_list = []
        self.__tool_list         = []
        self.__import_plugins    = []
        self.__export_plugins    = []
        self.__general_plugins   = []
        self.__mapservice_list   = []
        self.__attempt_list      = []
        self.__loaddir_list      = []
        self.__textdoc_list      = []
        self.__bookdoc_list      = []
        self.__drawdoc_list      = []
        self.__failmsg_list      = []
        self.__bkitems_list      = []
        self.__cl_list           = []
        self.__cli_tool_list     = []
        self.__external_opt_dict = {}
        self.__success_list      = []
        self.__relcalc_class = Relationship.RelationshipCalculator

        self.__mod2text          = {}
        
    def load_plugins(self, direct):
        """
        Searches the specified directory, and attempts to load any python
        modules that it finds, adding name to the attempt_lists list. If the 
        module successfully loads, it is added to the success_list list. 
        Each plugin is responsible for registering itself in the correct 
        manner. No attempt is done in this routine to register the tasks. 
        Returns True on error. 
        """
        
        # if the directory does not exist, do nothing
        if not os.path.isdir(direct):
            return False # return value is True for error
    
        pymod = re.compile(r"^(.*)\.py$")
    
        # loop through each file in the directory, looking for files that
        # have a .py extention, and attempt to load the file. If it succeeds,
        # add it to the success_list list. If it fails, add it to the _failure
        # list
        
        for (dirpath, dirnames, filenames) in os.walk(direct):
            # add the directory to the python search path
            sys.path.append(dirpath)

        for (dirpath, dirnames, filenames) in os.walk(direct):
            # if the path has not already been loaded, save it in the 
            # loaddir_list list for use on reloading.
            if dirpath not in self.__loaddir_list:
                self.__loaddir_list.append(dirpath)
                       
            for filename in filenames:
                name = os.path.split(filename)
                match = pymod.match(name[1])
                if not match:
                    continue
                self.__attempt_list.append(filename)
                plugin = match.groups()[0]
                try: 
                    _module = __import__(plugin)
                    self.__success_list.append((filename, _module))
                except:
                    self.__failmsg_list.append((filename, sys.exc_info()))
                    
        return len(self.__failmsg_list) != 0 # return True if there are errors

    def reload_plugins(self):
        """ Reload previously loaded plugins """
        pymod = re.compile(r"^(.*)\.py$")
    
        oldfailmsg = self.__failmsg_list[:]
        self.__failmsg_list = []
    
        # attempt to reload all plugins that have succeeded in the past
        # TODO: do other lists need to be reset here, too?
        self.__import_plugins[:] = []
        self.__export_plugins[:] = []

        for plugin in self.__success_list:
            filename = plugin[0]
            filename = filename.replace('pyc','py')
            filename = filename.replace('pyo','py')
            try: 
                reload(plugin[1])
            except:
                self.__failmsg_list.append((filename, sys.exc_info()))
            
        # Remove previously good plugins that are now bad
        # from the registered lists
        self.__purge_failed()
    
        # attempt to load the plugins that have failed in the past
        for (filename, message) in oldfailmsg:
            name = os.path.split(filename)
            match = pymod.match(name[1])
            if not match:
                continue
            self.__attempt_list.append(filename)
            plugin = match.groups()[0]
            try: 
                # For some strange reason second importing of a failed plugin
                # results in success. Then reload reveals the actual error.
                # Looks like a bug in Python.
                _module = __import__(plugin)
                reload(_module)
                self.__success_list.append((filename, _module))
            except:
                self.__failmsg_list.append((filename, sys.exc_info()))
    
        # attempt to load any new files found
        for directory in self.__loaddir_list:
            for filename in os.listdir(directory):
                name = os.path.split(filename)
                match = pymod.match(name[1])
                if not match:
                    continue
                if filename in self.__attempt_list:
                    continue
                self.__attempt_list.append(filename)
                plugin = match.groups()[0]
                try: 
                    _module = __import__(plugin)
                    if _module not in [plugin[1]
                                 for plugin in self.__success_list]:
                        self.__success_list.append((filename, _module))
                except:
                    self.__failmsg_list.append((filename, sys.exc_info()))
                    
        self.emit('plugins-reloaded')

    def get_fail_list(self):
        """ Return the list of failed plugins. """
        return self.__failmsg_list
    
    def get_success_list(self):
        """ Return the list of succeeded plugins. """
        return self.__success_list
    
    def get_report_list(self):
        """ Return the list of report plugins. """
        return self.__report_list
    
    def get_tool_list(self):
        """ Return the list of tool plugins. """
        return self.__tool_list
    
    def get_quick_report_list(self):
        """ Return the list of quick report plugins. """
        return self.__quick_report_list
    
    def get_mapservice_list(self):
        """ Return the list of map services"""
        return self.__mapservice_list

    def get_book_item_list(self):
        """ Return the list of book plugins. """
        return self.__bkitems_list
    
    def get_text_doc_list(self):
        """ Return the list of text document generator plugins. """
        return self.__textdoc_list
    
    def get_draw_doc_list(self):
        """ Return the list of graphical document generator plugins. """
        return self.__drawdoc_list
    
    def get_book_doc_list(self):
        """ Return the list of book document generator plugins. """
        return self.__bookdoc_list
    
    def get_cl_list(self):
        """ Return the list of command line report plugins. """
        return self.__cl_list
    
    def get_cl_tool_list(self):
        """ Return the list of command line tool plugins. """
        return self.__cli_tool_list
    
    def get_external_opt_dict(self):
        """ Return the dictionary of external options. """
        return self.__external_opt_dict
    
    def get_module_description(self, module):
        """ Given a module name, return the module description. """
        return self.__mod2text.get(module, '')
    
    def register_plugin(self, plugin):
        """
        @param plugin: The plugin to be registered.
        @type plugin: gen.plug.Plugin
        @return: nothing
        """
        if isinstance(plugin, gen.plug.ImportPlugin):
            self.__import_plugins.append(plugin)
        elif isinstance(plugin, gen.plug.ExportPlugin):
            self.__export_plugins.append(plugin)
        elif isinstance(plugin, gen.plug.Plugin):
            self.__general_plugins.append(plugin)
        
        self.__mod2text[plugin.get_module_name()] = plugin.get_description()
            
    def get_import_plugins(self):
        """
        Get the list of import plugins.
        
        @return: [gen.plug.ImportPlugin] (a list of ImportPlugin instances)
        """
        return self.__import_plugins
    
    def get_export_plugins(self):
        """
        Get the list of export plugins.
        
        @return: [gen.plug.ExportPlugin] (a list of ExportPlugin instances)
        """
        return self.__export_plugins

    def register_tool(self, name, category, tool_class, options_class,
                      modes, translated_name, status=_("Unknown"), 
                      description=_UNAVAILABLE, author_name=_("Unknown"),
                      author_email=_("Unknown"), unsupported=False,
                      require_active=True ):
        """
        Register a tool with the plugin system.
    
        This function should be used to register tool in GUI and/or
        command-line mode.
        """
        (junk, gui_task) = divmod(modes, 2**PluginManager.TOOL_MODE_GUI)
        if gui_task:
            self.__register_gui_tool(tool_class, options_class, translated_name,
                               name, category, description,
                               status, author_name, author_email, unsupported,
                               require_active)
    
        (junk, cli_task) = divmod(modes-gui_task, 
                                  2**PluginManager.TOOL_MODE_CLI)
        if cli_task:
            self.__register_cli_tool(name, category, tool_class, options_class,
                               translated_name, unsupported)

    def __register_gui_tool(self, tool_class, options_class, translated_name,
                            name, category, description=_UNAVAILABLE,
                            status=_("Unknown"), author_name=_("Unknown"),
                            author_email=_("Unknown"), unsupported=False,
                            require_active=True):
        """
        Register a GUI tool.
        """
        del_index = -1
        for i in range(0, len(self.__tool_list)):
            val = self.__tool_list[i]
            if val[4] == name:
                del_index = i
        if del_index != -1:
            del self.__tool_list[del_index]
        self.__mod2text[tool_class.__module__] = description
        self.__tool_list.append( (tool_class, options_class, translated_name,
                                  category, name, description, status,
                                  author_name, author_email, unsupported, 
                                  require_active) )

    def __register_cli_tool(self, name, category, tool_class, options_class,
                           translated_name, unsupported=False):
        """
        Register a CLI tool.
        """
        del_index = -1
        for i in range(0, len(self.__cli_tool_list)):
            val = self.__cli_tool_list[i]
            if val[0] == name:
                del_index = i
        if del_index != -1:
            del self.__cli_tool_list[del_index]
        self.__cli_tool_list.append( (name, category, tool_class, options_class,
                                      translated_name, unsupported, None) )

    def register_report(self, name, category, report_class, options_class,
                        modes, translated_name, status=_("Unknown"),
                        description=_UNAVAILABLE, author_name=_("Unknown"),
                        author_email=_("Unknown"), unsupported=False,
                        require_active=True):
        """
        Registers report for all possible flavors.
    
        This function should be used to register report as a stand-alone,
        book item, or command-line flavor in any combination of those.
        The low-level functions (starting with '_') should not be used
        on their own. Instead, this function will call them as needed.
        """
        (junk, standalone_task) = divmod(modes, 
                                         2**PluginManager.REPORT_MODE_GUI)
        if standalone_task:
            self.__register_standalone(report_class, options_class, 
                                       translated_name, name, category, 
                                       description, status, author_name, 
                                       author_email, unsupported, 
                                       require_active)
    
        (junk, book_item_task) = divmod(modes-standalone_task, 
                                        2**PluginManager.REPORT_MODE_BKI)
        if book_item_task:
            book_item_category = category
            self.__register_book_item(translated_name, book_item_category,
                                      report_class, options_class, name, 
                                      unsupported, require_active)
    
        (junk, command_line_task) = divmod(modes-standalone_task-book_item_task,
                                           2**PluginManager.REPORT_MODE_CLI)
        if command_line_task:
            self.__register_cl_report(name, category, report_class, 
                                      options_class, translated_name, 
                                      unsupported, require_active)

    def __register_standalone(self, report_class, options_class, 
                              translated_name, name, category, 
                              description=_UNAVAILABLE, status=_("Unknown"), 
                              author_name=_("Unknown"), 
                              author_email=_("Unknown"), unsupported=False,
                              require_active=True):
        """
        Register a report with the plugin system.
        """
        del_index = -1
        for i in range(0, len(self.__report_list)):
            val = self.__report_list[i]
            if val[4] == name:
                del_index = i
        if del_index != -1:
            del self.__report_list[del_index]
    
        self.__report_list.append( (report_class, options_class, 
                                    translated_name, category, name, 
                                    description, status, author_name,
                                    author_email, unsupported, require_active) )
        self.__mod2text[report_class.__module__] = description

    def __register_book_item(self, translated_name, category, report_class,
                            option_class, name, unsupported, require_active):
        """
        Register a book item.
        """
        del_index = -1
        for i in range(0, len(self.__bkitems_list)):
            val = self.__bkitems_list[i]
            if val[4] == name:
                del_index = i
        if del_index != -1:
            del self.__bkitems_list[del_index]
    
        self.__bkitems_list.append( (translated_name, category, report_class,
                                     option_class, name, unsupported, 
                                     require_active) )

    def __register_cl_report(self, name, category, report_class, options_class,
                            translated_name, unsupported, require_active):
        """
        Register a command line report.
        """
        del_index = -1
        for i in range(0, len(self.__cl_list)):
            val = self.__cl_list[i]
            if val[0] == name:
                del_index = i
        if del_index != -1:
            del self.__cl_list[del_index]
        self.__cl_list.append( (name, category, report_class, options_class,
                                translated_name, unsupported, require_active) )

    def register_text_doc(self, name, classref, paper, style, ext,
                          print_report_label=None, clname=''):
        """
        Register a text document generator.
        """
        del_index = -1
        for i in range(0, len(self.__textdoc_list)):
            val = self.__textdoc_list[i]
            if val[0] == name:
                del_index = i
        if del_index != -1:
            del self.__textdoc_list[del_index]
    
        if not clname:
            clname = ext[1:]
    
        self.__textdoc_list.append( (name, classref, paper, style,
                                     ext, print_report_label, clname) )
        self.__mod2text[classref.__module__] = name

    def register_book_doc(self, name, classref, paper, style, ext, 
                          print_report_label=None, clname=''):
        """
        Register a text document generator.
        """
        del_index = -1
        for i in range(0, len(self.__bookdoc_list)):
            val = self.__bookdoc_list[i]
            if val[0] == name:
                del_index = i
        if del_index != -1:
            del self.__bookdoc_list[del_index]
    
        if not clname:
            clname = ext[1:]
        self.__bookdoc_list.append( (name, classref, paper, style, ext,
                                     print_report_label, clname) )

    def register_draw_doc(self, name, classref, paper, style, ext,
                          print_report_label=None, clname=''):
        """
        Register a drawing document generator.
        """
        del_index = -1
        for i in range(0, len(self.__drawdoc_list)):
            val = self.__drawdoc_list[i]
            if val[0] == name:
                del_index = i
        if del_index != -1:
            del self.__drawdoc_list[del_index]
        if not clname:
            clname = ext[1:]
        self.__drawdoc_list.append( (name, classref, paper, style, ext,
                                     print_report_label, clname) )
        self.__mod2text[classref.__module__] = name

    def register_quick_report(self, name, category, run_func, translated_name,
                              status=_("Unknown"), description=_UNAVAILABLE,
                              author_name=_("Unknown"),
                              author_email=_("Unknown"), unsupported=False ):
        """
        Registers quick report for all possible objects.
    
        This function should be used to register a quick report 
        so it appears in the quick report context menu of the object it is
        attached to.
        The low-level functions (starting with '_') should not be used
        on their own. Instead, this function will call them as needed.
        """
        del_index = -1
        for i in range(0, len(self.__quick_report_list)):
            val = self.__quick_report_list[i]
            if val[3] == name:
                del_index = i
        if del_index != -1:
            del self.__quick_report_list[del_index]
    
        self.__quick_report_list.append( (run_func, translated_name, 
                            category, name, description, status,
                            author_name, author_email, unsupported))
                            
        self.__mod2text[run_func.__module__] = description

    def register_mapservice(self, name, mapservice, translated_name,
                            status=_("Unknown"), tooltip=_UNAVAILABLE,
                            author_name=_("Unknown"),
                            author_email=_("Unknown"), unsupported=False ):
        """
        Register map services for the place view.
        A map service is a MapService class. The class can be called with a
        list of (place handle, description) values, and manipulate this data
        to show on a map.
        """
        del_index = -1
        for i in range(0, len(self.__mapservice_list)):
            val = self.__mapservice_list[i]
            if val[2] == name:
                del_index = i
        if del_index != -1:
            del self.__mapservice_list[del_index]
    
        self.__mapservice_list.append( (mapservice, translated_name, 
                            name, tooltip, status,
                            author_name, author_email, unsupported))
                            
        self.__mod2text[mapservice.__module__] = tooltip
        
    def register_option(self, option, guioption):
        """
        Register an external option.

        Register a mapping from option to guioption for an option
        that is not native to Gramps but provided by the plugin writer.
        This should typically be called during initialisation of a
        ReportOptions class.
        @param option:      the option class
        @type option:       class that inherits from gen.plug.menu.Option
        @param guioption:   the gui-option class
        @type guioption:    class that inherits from gtk.Widget.
        """
        self.__external_opt_dict[option] = guioption;

    def __purge_failed(self):
        """
        Purge the failed plugins from the corresponding lists.
        """
        failed_module_names = [
            os.path.splitext(os.path.basename(filename))[0]
            for filename, junk in self.__failmsg_list
            ]
    
        self.__general_plugins[:] = [ item for item in self.__export_plugins
                    if item.get_module_name() not in self.__general_plugins ][:]
        self.__export_plugins[:] = [ item for item in self.__export_plugins
                    if item.get_module_name() not in failed_module_names ][:]
        self.__import_plugins[:] = [ item for item in self.__import_plugins
                    if item.get_module_name() not in failed_module_names ][:]
        self.__tool_list[:] = [ item for item in self.__tool_list
                      if item[0].__module__ not in failed_module_names ][:]
        self.__cli_tool_list[:] = [ item for item in self.__cli_tool_list
                          if item[2].__module__ not in failed_module_names ][:]
        self.__report_list[:] = [ item for item in self.__report_list
                        if item[0].__module__ not in failed_module_names ][:]
        self.__quick_report_list[:] = \
                        [ item for item in self.__quick_report_list
                           if item[0].__module__ not in failed_module_names ][:]
        self.__bkitems_list[:] = [ item for item in self.__bkitems_list
                         if item[2].__module__ not in failed_module_names ][:]
        self.__cl_list[:] = [ item for item in self.__cl_list
                    if item[2].__module__ not in failed_module_names ][:]
        self.__textdoc_list[:] = [ item for item in self.__textdoc_list
                         if item[1].__module__ not in failed_module_names ][:]
        self.__bookdoc_list[:] = [ item for item in self.__bookdoc_list
                         if item[1].__module__ not in failed_module_names ][:]
        self.__drawdoc_list[:] = [ item for item in self.__drawdoc_list
                         if item[1].__module__ not in failed_module_names ][:]

    def register_relcalc(self, relclass, languages):
        """
        Register a relationship calculator.
        """
        try:
            if os.environ["LANG"] in languages:
                self.__relcalc_class = relclass
        except:
            pass
    
    def get_relationship_calculator(self):
        """ 
        Return the relationship calculator for the current language 
        """
        return self.__relcalc_class()
