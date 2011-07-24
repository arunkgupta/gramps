#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2005  Donald N. Allingham
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
# $Id:_Options.py 9912 2008-01-22 09:17:46Z acraphae $

# Written by Alex Roitman

"""
General option handling, including saving and parsing.
"""

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
import os

#-------------------------------------------------------------------------
#
# SAX interface
#
#-------------------------------------------------------------------------
try:
    from xml.sax import make_parser, handler,SAXParseException
    from xml.sax.saxutils import quoteattr
except:
    from _xmlplus.sax import make_parser, handler,SAXParseException
    from _xmlplus.sax.saxutils import quoteattr

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import Utils

#-------------------------------------------------------------------------
#
# List of options for a single module
#
#-------------------------------------------------------------------------
class OptionList(object):
    """
    Implements a set of options to parse and store for a given module.
    """

    def __init__(self):
        self.options = {}
    
    def set_options(self, options):
        """
        Set the whole bunch of options for the OptionList.
        @param options: list of options to set.
        @type options: list
        """
        self.options = options

    def get_options(self):
        """
        Return the whole bunch of  options for the OptionList.
        @returns: list of options
        @rtype: list
        """
        return self.options

    def set_option(self, name,value):
        """
        Set a particular option in the OptionList.
        @param name: name of the option to set.
        @type name: str
        @param value: value of the option to set.
        @type str
        """
        self.options[name] = value

    def remove_option(self, name):
        """
        Remove a particular option from the OptionList.
        @param name: name of the option to remove.
        @type name: str
        """
        if name in self.options:
            del self.options[name]

    def get_option(self, name):
        """
        Return the value of a particular option in the OptionList.
        @param name: name of the option to retrieve
        @type name: str
        @returns: value associated with the passed option
        @rtype: str
        """
        return self.options.get(name,None)

#-------------------------------------------------------------------------
#
# Collection of option lists
#
#-------------------------------------------------------------------------
class OptionListCollection(object):
    """
    Implements a collection of option lists.
    """

    def __init__(self,filename):
        """
        Create an OptionListCollection instance from the list defined
        in the specified file.
        @param filename: XML file that contains option definitions
        @type filename: str
        """

        self.filename = os.path.expanduser(filename)
        self.option_list_map = {}
        self.init_common()
        self.parse()

    def init_common(self):
        pass
    
    def get_option_list_map(self):
        """
        Return the map of module names to option lists.
        @returns: Returns the map of module names to option lists.
        @rtype: dictionary
        """
        return self.option_list_map

    def get_option_list(self, name):
        """
        Return the option_list associated with the module name
        @param name: name associated with the desired module.
        @type name: str
        @returns: returns the option list associated with the name,
            or None of no such option exists
        @rtype: str
        """
        return self.option_list_map.get(name,None)

    def get_module_names(self):
        """
        Return a list of all the module names in the OptionListCollection
        @returns: returns the list of module names
        @rtype: list
        """
        return self.option_list_map.keys()

    def set_option_list(self, name, option_list):
        """
        Add or replaces an option_list in the OptionListCollection. 
        @param name: name assocated with the module to add or replace.
        @type name: str
        @param option_list: list of options
        @type option_list: str
        """
        self.option_list_map[name] = option_list

    def write_common(self,f):
        """
        Stub function for common options. Overridden by reports.
        """
        pass

    def write_module_common(self,f, option_list):
        """
        Stub function for common options. Overridden by reports.
        """
        pass

    def save(self):
        """
        Saves the current OptionListCollection to the associated file.
        """
        f = open(self.filename,"w")
        f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
        f.write('<options>\n')

        self.write_common(f)

        for module_name in self.get_module_names():
            option_list = self.get_option_list(module_name)
            f.write('<module name=%s>\n' % quoteattr(module_name))
            options = option_list.get_options()
            for option_name, option_data in options.iteritems():
                if isinstance(option_data, (list, tuple)):
                    f.write('  <option name=%s value="" length="%d">\n' % (
                                quoteattr(option_name),
                                len(option_data) ) )
                    for list_index, list_data in enumerate(option_data):
                        f.write('    <listitem number="%d" value=%s/>\n' % (
                                list_index,
                                quoteattr(unicode(list_data))) )
                    f.write('  </option>\n')
                else:
                    f.write('  <option name=%s value=%s/>\n' % (
                            quoteattr(option_name),
                            quoteattr(unicode(option_data))) )

            self.write_module_common(f, option_list)

            f.write('</module>\n')

        f.write('</options>\n')
        f.close()
    
    def parse(self):
        """
        Loads the OptionList from the associated file, if it exists.
        """
        try:
            if os.path.isfile(self.filename):
                p = make_parser()
                p.setContentHandler(OptionParser(self))
                p.parse(self.filename)
        except (IOError,OSError,SAXParseException):
            pass

#-------------------------------------------------------------------------
#
# OptionParser
#
#-------------------------------------------------------------------------
class OptionParser(handler.ContentHandler):
    """
    SAX parsing class for the OptionListCollection XML file.
    """
    
    def __init__(self,collection):
        """
        Create a OptionParser class that populates the passed collection.

        collection:   OptionListCollection to be loaded from the file.
        """
        handler.ContentHandler.__init__(self)
        self.collection = collection
    
        self.mname = None
        self.option_list = None
        self.oname = None
        self.o = None
        self.an_o = None
        self.list_class = OptionList

    def startElement(self,tag,attrs):
        """
        Overridden class that handles the start of a XML element
        """
        if tag in ("report","module"):
            self.mname = attrs['name']
            self.option_list = self.list_class()
            self.o = {}
        elif tag == "option":
            self.oname = attrs['name']
            if attrs.has_key('length'):
                self.an_o = []
            else:
                self.an_o = attrs['value']
        elif tag == "listitem":
            self.an_o.append(attrs['value'])

    def endElement(self,tag):
        "Overridden class that handles the end of a XML element"
        if tag == "option":
            self.o[self.oname] = self.an_o
        elif tag in ("report","module"):
            self.option_list.set_options(self.o)
            self.collection.set_option_list(self.mname,self.option_list)

#-------------------------------------------------------------------------
#
# Class handling options for plugins 
#
#-------------------------------------------------------------------------
class OptionHandler(object):
    """
    Implements handling of the options for the plugins.
    """

    def __init__(self,module_name, options_dict,person_id=None):
        self.module_name = module_name
        self.default_options_dict = options_dict.copy()
        self.options_dict = options_dict

        # Retrieve our options from whole collection
        self.init_subclass()
        self.option_list_collection = self.collection_class(self.filename)
        self.init_common()
        self.saved_option_list = self.option_list_collection.get_option_list(module_name)
        self.person_id = person_id

        # Whatever was found should override the defaults
        if self.saved_option_list:
            self.set_options()
        else:
            # If nothing was found, set up the option list 
            self.saved_option_list = self.list_class()
            self.option_list_collection.set_option_list(module_name,
                                                        self.saved_option_list)

    def init_subclass(self):
        self.collection_class = OptionListCollection
        self.list_class = OptionList
        self.filename = None

    def init_common(self):
        pass

    def set_options(self):
        """
        Set options to be used in this plugin according to the passed
        options dictionary.
        
        Dictionary values are all strings, since they were read from XML.
        Here we need to convert them to the needed types. We use default
        values to determine the type.
        """
        # First we set options_dict values based on the saved options
        options = self.saved_option_list.get_options()
        bad_opts = []
        for option_name, option_data in options.iteritems():
            if option_name not in self.options_dict:
                print "Option %s is present in the %s but is not known "\
                      "to the module." % (option_name,
                                          self.option_list_collection.filename)
                print "Ignoring..."
                bad_opts.append(option_name)
                continue
            try:
                converter = Utils.get_type_converter(self.options_dict[option_name])
                self.options_dict[option_name] = converter(option_data)
            except ValueError:
                pass
            except TypeError:
                pass

        for option_name in bad_opts:
            options.pop(option_name)

        # Then we set common options from whatever was found
        self.set_common_options()

    def set_common_options(self):
        pass

    def save_options(self):
        """
        Saves options to file.
        
        We need to only store non-default options. Therefore, we remove all
        options whose values are the defaults prior to saving.
        """

        # First we save options from options_dict
        for option_name, option_data in self.options_dict.iteritems():
            if option_data == self.default_options_dict[option_name]:
                self.saved_option_list.remove_option(option_name)
            else:
                self.saved_option_list.set_option(option_name,self.options_dict[option_name])

        # Handle common options
        self.save_common_options()

        # Finally, save the whole collection into file
        self.option_list_collection.save()

    def save_common_options(self):
        pass

    def get_person_id(self):
        return self.person_id

    def set_person_id(self,val):
        self.person_id = val

#------------------------------------------------------------------------
#
# Base Options class
#
#------------------------------------------------------------------------
class Options(object):

    """
    Defines options and provides handling interface.
    
    This is a base Options class for the modules. All modules, options
    classes should derive from it.
    """

    def __init__(self, name,person_id=None):
        """
        Initialize the class, performing usual house-keeping tasks.
        Subclasses MUST call this in their __init__() method.
        
        Modules that need custom options need to override this method.
        Two dictionaries allow the addition of custom options: 

            self.options_dict
                This is a dictionary whose keys are option names
                and values are the default option values.

            self.options_help
                This is a dictionary whose keys are option names
                and values are 3- or 4- lists or tuples:
                    ('=example','Short description',VALUES,DO_PREPEND)
                The VALUES is either a single string (in that case
                the DO_PREPEND does not matter) or a list/tuple of
                strings to list. In that case, if DO_PREPEND evaluates
                as True then each string will be preneded with the ordinal
                number when help is printed on the command line.

        NOTE:   Both dictionaries must have identical keys.
        """
        self.name = name
        self.person_id = person_id
        self.options_dict = {}
        self.options_help = {}
        self.handler = None
        
    def load_previous_values(self):
        """
        Modifies all options to have the value they were last used as. Call this
        function after all options have been added.
        """
        self.handler = OptionHandler(self.name,self.options_dict,self.person_id)

    def add_user_options(self,dialog):
        """
        Set up UI controls (widgets) for the options specific for this modul.

        This method MUST be overridden by modules that define new options.
        The single argument 'dialog' is the Report.ReportDialog instance.
        Any attribute of the dialog is available.
        
        After the widgets are defined, they MUST be added to the dialog
        using the following call:
                dialog.add_options(LABEL,widget)
        
        NOTE:   To really have any effect besides looking pretty, each widget
                set up here must be also parsed in the parse_user_options()
                method below.
        """
        pass

    def parse_user_options(self,dialog):
        """
        Parses UI controls (widgets) for the options specific for this module.

        This method MUST be overridden by modules that define new options.
        The single argument 'dialog' is the Report.ReportDialog instance.
        Any attribute of the dialog is available.
        
        After obtaining values from the widgets, they MUST be used to set the
        appropriate options_dict values. Otherwise the values will not have
        any user-visible effect.
        
        NOTE:   Any widget parsed here MUST be defined and added to the dialog
                in the add_user_options() method above.
        """
        pass