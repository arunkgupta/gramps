#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2005  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2009       Benny Malengier
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
plugins from specified directories and provide information about the loaded
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
from gen.ggettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import config
import gen.utils
from gen.plug import PluginRegister

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
_UNAVAILABLE = _("No description was provided")

#-------------------------------------------------------------------------
#
# BasePluginManager
#
#-------------------------------------------------------------------------
class BasePluginManager(object):
    """ unique singleton storage class for a PluginManager. """

    __instance = None
    
    def get_instance():
        """ Use this function to get the instance of the PluginManager """
        if BasePluginManager.__instance is None:
            BasePluginManager.__instance = 1 # Set to 1 for __init__()
            BasePluginManager.__instance = BasePluginManager()
        return BasePluginManager.__instance
    get_instance = staticmethod(get_instance)
    
    def __init__(self):
        """ This function should only be run once by get_instance() """
        if BasePluginManager.__instance is not 1:
            raise Exception("This class is a singleton. "
                            "Use the get_instance() method")

        self.__import_plugins    = []
        self.__export_plugins    = []
        self.__docgen_plugins    = []

        self.__attempt_list      = []
        self.__failmsg_list      = []
        self.__external_opt_dict = {}
        self.__success_list      = []

        self.__mod2text          = {}
        
        self.__pgr = PluginRegister.get_instance()
        self.__registereddir_set = set()
        self.__loaded_plugins = {}

    def reg_plugins(self, direct):
        """
        Searches the specified directory, and registers python plugin that
        are being defined in gpr.py files. 
        
        If a relationship calculator for env var LANG is present, it is 
        immediately loaded so it is available for all.
        """
        # if the directory does not exist, do nothing
        if not os.path.isdir(direct):
            return False # return value is True for error
        
        for (dirpath, dirnames, filenames) in os.walk(direct):
            root, subdir = os.path.split(dirpath)
            if subdir.startswith("."): 
                dirnames[:] = []
                continue
            for dirname in dirnames:
                # Skip hidden and system directories:
                if dirname.startswith(".") or dirname in ["po", "locale"]:
                    dirnames.remove(dirname)
            # add the directory to the python search path
            sys.path.append(dirpath)
            # if the path has not already been loaded, save it in the 
            # registereddir_list list for use on reloading.
            self.__registereddir_set.add(dirpath)
            self.__pgr.scan_dir(dirpath)

        # load plugins that request to be loaded on startup
        for plugin in self.__pgr.filter_load_on_reg():
            mod = self.load_plugin(plugin)

    def is_loaded(self, pdata_id):
        """
        return True if plugin is already loaded
        """
        if pdata_id in self.__loaded_plugins:
            return True
        return False

    def load_plugin(self, pdata):
        """
        Load a PluginData object. This means import of the python module.
        Plugin directories are added to sys path, so files are found
        """
        if pdata.id in self.__loaded_plugins:
            return self.__loaded_plugins[pdata.id]
        reload = False
        filename = pdata.fname
        if filename in self.__attempt_list:
            #new attempt after a fail, a reload needed
            reload = True
            dellist = []
            for index, data in enumerate(self.__failmsg_list):
                if data[0] == filename:
                    dellist.append(index)
            dellist.reverse()
            for index in dellist:
                del self.__failmsg_list[index]
                    
        else:
            self.__attempt_list.append(filename)
        plugin = pdata.mod_name
        try: 
            _module = __import__(plugin)
            if reload:
                # For some strange reason second importing of a failed plugin
                # results in success. Then reload reveals the actual error.
                # Looks like a bug in Python.
                reload(_module)
            self.__success_list.append((filename, _module, pdata))
            self.__loaded_plugins[pdata.id] = _module
            self.__mod2text[_module.__name__] = pdata.description
            return _module
        except:
            self.__failmsg_list.append((filename, sys.exc_info(), pdata))

        return None

    def empty_managed_plugins(self):
        """ For some plugins, managed Plugin are used. These are only 
        reobtained from the registry if this method is called
        """
        # TODO: do other lists need to be reset here, too?
        self.__import_plugins = []
        self.__export_plugins = []
        self.__docgen_plugins = []
        
    def reload_plugins(self):
        """ Reload previously loaded plugins """
        pymod = re.compile(r"^(.*)\.py$")
    
        oldfailmsg = self.__failmsg_list[:]
        self.__failmsg_list = []
    
        # attempt to reload all plugins that have succeeded in the past
        self.empty_managed_plugins()

        dellist = []
        for (index, plugin) in enumerate(self.__success_list):
            filename = plugin[0]
            pdata = plugin[2]
            filename = filename.replace('pyc','py')
            filename = filename.replace('pyo','py')
            try: 
                reload(plugin[1])
            except:
                dellist.append(index)
                self.__failmsg_list.append((filename, sys.exc_info(), pdata))
        dellist.reverse()
        for index in dellist:
            del self.__success_list[index]
            
        # Remove previously good plugins that are now bad
        # from the registered lists
        self.__purge_failed()
    
        # attempt to load the plugins that have failed in the past
        for (filename, message, pdata) in oldfailmsg:
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
                self.__success_list.append((filename, _module, pdata))
            except:
                self.__failmsg_list.append((filename, sys.exc_info(), pdata))

    def get_fail_list(self):
        """ Return the list of failed plugins. """
        return self.__failmsg_list
    
    def get_success_list(self):
        """ Return the list of succeeded plugins. """
        return self.__success_list

    def get_plugin(self, id):
        """ 
        Returns a plugin object from PluginRegister by id.
        """
        return self.__pgr.get_plugin(id)

    def get_reg_reports(self, gui=True):
        """ Return list of registered reports
        :Param gui: bool indicating if GUI reports or CLI reports must be
            returned
        """
        return self.__pgr.report_plugins(gui)
    
    def get_reg_tools(self, gui=True):
        """ Return list of registered tools
        :Param gui: bool indicating if GUI reports or CLI reports must be
            returned
        """
        return self.__pgr.tool_plugins(gui)
    
    def get_reg_quick_reports(self):
        """ Return list of registered quick reports
        """
        return self.__pgr.quickreport_plugins()
    
    def get_reg_views(self):
        """ Return list of registered views
        """
        return self.__pgr.view_plugins()
    
    def get_reg_mapservices(self):
        """ Return list of registered mapservices
        """
        return self.__pgr.mapservice_plugins()

    def get_reg_bookitems(self):
        """ Return list of reports registered as bookitem
        """
        return self.__pgr.bookitem_plugins()
    
    def get_reg_gramplets(self):
        """ Return list of non hidden gramplets.
        """
        return self.__pgr.gramplet_plugins()
    
    def get_external_opt_dict(self):
        """ Return the dictionary of external options. """
        return self.__external_opt_dict
    
    def get_module_description(self, module):
        """ Given a module name, return the module description. """
        return self.__mod2text.get(module, '')
    
    def get_reg_importers(self):
        """ Return list of registered importers
        """
        return self.__pgr.import_plugins()
    
    def get_reg_exporters(self):
        """ Return list of registered exporters
        """
        return self.__pgr.export_plugins()
    
    def get_reg_docgens(self):
        """ Return list of registered docgen
        """
        return self.__pgr.docgen_plugins()
    
    def get_import_plugins(self):
        """
        Get the list of import plugins.
        
        @return: [gen.plug.ImportPlugin] (a list of ImportPlugin instances)
        """
        ## TODO: would it not be better to remove ImportPlugin and use
        ## only PluginData, loading from module when importfunction needed?
        if self.__import_plugins == []:
            #The module still needs to be imported
            for pdata in self.get_reg_importers():
                if pdata.id in config.get("plugin.hiddenplugins"):
                    continue
                mod = self.load_plugin(pdata)
                if mod:
                    imp = gen.plug.ImportPlugin(name=pdata.name, 
                        description     = pdata.description,
                        import_function = getattr(mod, pdata.import_function),
                        extension       = pdata.extension)
                    self.__import_plugins.append(imp)

        return self.__import_plugins
    
    def get_export_plugins(self):
        """
        Get the list of export plugins.
        
        @return: [gen.plug.ExportPlugin] (a list of ExportPlugin instances)
        """
        ## TODO: would it not be better to remove ExportPlugin and use
        ## only PluginData, loading from module when export/options needed?
        if self.__export_plugins == []:
            #The modules still need to be imported
            for pdata in self.get_reg_exporters():
                if pdata.id in config.get("plugin.hiddenplugins"):
                    continue
                mod = self.load_plugin(pdata)
                if mod:
                    options = None
                    if (pdata.export_options and 
                        hasattr(mod, pdata.export_options)):
                        options = getattr(mod, pdata.export_options)
                    exp = gen.plug.ExportPlugin(name=pdata.name, 
                        description     = pdata.description,
                        export_function = getattr(mod, pdata.export_function),
                        extension       = pdata.extension,
                        config          = (pdata.export_options_title, options))
                    self.__export_plugins.append(exp)
                
        return self.__export_plugins
    
    def get_docgen_plugins(self):
        """
        Get the list of docgen plugins.
        
        @return: [gen.plug.DocGenPlugin] (a list of DocGenPlugin instances)
        """
        ## TODO: would it not be better to return list of plugindata, and only
        ##       import those docgen that will then actuallly be needed? 
        ##       So, only do import when docgen.get_basedoc() is requested
        if self.__docgen_plugins == []:
            #The modules still need to be imported
            for pdata in self.get_reg_docgens():
                if pdata.id in config.get("plugin.hiddenplugins"):
                    continue
                mod = self.load_plugin(pdata)
                if mod:
                    dgp = gen.plug.DocGenPlugin(name=pdata.name, 
                            description = pdata.description,
                            basedoc     = getattr(mod, pdata.basedocclass),
                            paper       = pdata.paper,
                            style       = pdata.style, 
                            extension   = pdata.extension )
                    self.__docgen_plugins.append(dgp)
                
        return self.__docgen_plugins

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
            for filename, msg, pdata in self.__failmsg_list
            ]

        self.__export_plugins[:] = [ item for item in self.__export_plugins
                    if item.get_module_name() not in failed_module_names ][:]
        self.__import_plugins[:] = [ item for item in self.__import_plugins
                    if item.get_module_name() not in failed_module_names ][:]
        self.__docgen_plugins[:] = [ item for item in self.__docgen_plugins
                    if item.get_module_name() not in failed_module_names ][:]
