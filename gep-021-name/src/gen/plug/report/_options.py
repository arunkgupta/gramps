#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2007  Donald N. Allingham
# Copyright (C) 2008       Gary Burton
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
# $Id: _ReportOptions.py 13346 2009-10-08 01:12:51Z dsblank $

# Written by Alex Roitman

"""
Report option handling, including saving and parsing.
"""

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
import os
import copy
from xml.sax.saxutils import escape

def escxml(d):
    return escape(d, { '"' : '&quot;' } )

#-------------------------------------------------------------------------
#
# SAX interface
#
#-------------------------------------------------------------------------
try:
    from xml.sax import make_parser, SAXParseException
except:
    from _xmlplus.sax import make_parser, SAXParseException

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import config
from gen.plug.docgen import PAPER_PORTRAIT
from gen.plug import _options
from gui.plug import GuiMenuOptions

#-------------------------------------------------------------------------
#
# List of options for a single report
#
#-------------------------------------------------------------------------
class OptionList(_options.OptionList):
    """
    Implements a set of options to parse and store for a given report.
    """

    def __init__(self):
        _options.OptionList.__init__(self)
        self.style_name = None
        self.paper_metric = None
        self.paper_name = None
        self.orientation = None
        self.custom_paper_size = [29.7, 21.0]
        self.margins = [2.54, 2.54, 2.54, 2.54]
        self.format_name = None
        self.css_filename = None
    
    def set_style_name(self, style_name):
        """
        Set the style name for the OptionList.
        @param style_name: name of the style to set.
        @type style_name: str
        """
        self.style_name = style_name

    def get_style_name(self):
        """
        Return the style name of the OptionList.
        @returns: string representing the style name
        @rtype: str
        """
        return self.style_name

    def set_paper_metric(self, paper_metric):
        """
        Set the paper metric for the OptionList.
        @param paper_metric: whether to use metric.
        @type paper_name: boolean
        """
        self.paper_metric = paper_metric

    def get_paper_metric(self):
        """
        Return the paper metric of the OptionList.
        @returns: returns whether to use metric
        @rtype: boolean
        """
        return self.paper_metric

    def set_paper_name(self, paper_name):
        """
        Set the paper name for the OptionList.
        @param paper_name: name of the paper to set.
        @type paper_name: str
        """
        self.paper_name = paper_name

    def get_paper_name(self):
        """
        Return the paper name of the OptionList.
        @returns: returns the paper name
        @rtype: str
        """
        return self.paper_name

    def set_orientation(self, orientation):
        """
        Set the orientation for the OptionList.
        @param orientation: orientation to set. Possible values are
            PAPER_LANDSCAPE or PAPER_PORTRAIT
        @type orientation: int
        """
        self.orientation = orientation

    def get_orientation(self):
        """
        Return the orientation for the OptionList.
        @returns: returns the selected orientation. Valid values are
            PAPER_LANDSCAPE or PAPER_PORTRAIT
        @rtype: int
        """
        return self.orientation

    def set_custom_paper_size(self, paper_size):
        """
        Set the custom paper size for the OptionList.
        @param paper_size: paper size to set in cm.
        @type paper_size: [float, float]
        """
        self.custom_paper_size = paper_size

    def get_custom_paper_size(self):
        """
        Return the custom paper size for the OptionList.
        @returns: returns the custom paper size in cm
        @rtype: [float, float]
        """
        return self.custom_paper_size

    def set_margins(self, margins):
        """
        Set the margins for the OptionList.
        @param margins: margins to set. Possible values are floats in cm
        @type margins: [float, float, float, float]
        """
        self.margins = copy.copy(margins)

    def get_margins(self):
        """
        Return the margins for the OptionList.
        @returns margins: returns the margins, floats in cm
        @rtype margins: [float, float, float, float]
        """
        return copy.copy(self.margins)

    def set_margin(self, pos, value):
        """
        Set a margin for the OptionList.
        @param pos: Position of margin [left, right, top, bottom]
        @param value: floating point in cm
        @type pos: int
        @type value: float
        """
        self.margins[pos] = value

    def get_margin(self, pos):
        """
        Return a margin for the OptionList.
        @param pos: Position of margin [left, right, top, bottom]
        @type pos: int
        @returns: float cm of margin
        @rtype: float
        """
        return self.margins[pos]

    def set_css_filename(self, css_filename):
        """
        Set the template name for the OptionList.
        @param template_name: name of the template to set.
        @type template_name: str
        """
        self.css_filename = css_filename

    def get_css_filename(self):
        """
        Return the template name of the OptionList.
        @returns: template name
        @rtype: str
        """
        return self.css_filename

    def set_format_name(self, format_name):
        """
        Set the format name for the OptionList.
        @param format_name: name of the format to set.
        @type format_name: str
        """
        self.format_name = format_name

    def get_format_name(self):
        """
        Return the format name of the OptionList.
        @returns: returns the format name
        @rtype: str
        """
        return self.format_name

#-------------------------------------------------------------------------
#
# Collection of option lists
#
#-------------------------------------------------------------------------
class OptionListCollection(_options.OptionListCollection):
    """
    Implements a collection of option lists.
    """
    def __init__(self, filename):
        _options.OptionListCollection.__init__(self, filename)

    def init_common(self):
        # Default values for common options
        self.default_style_name = "default"
        self.default_paper_metric = config.get('preferences.paper-metric')
        self.default_paper_name = config.get('preferences.paper-preference')
        self.default_orientation = PAPER_PORTRAIT
        self.default_css_filename = ""
        self.default_custom_paper_size = [29.7, 21.0]
        self.default_margins = [2.54, 2.54, 2.54, 2.54]
        self.default_format_name = 'print'

        self.last_paper_metric = self.default_paper_metric
        self.last_paper_name = self.default_paper_name
        self.last_orientation = self.default_orientation
        self.last_custom_paper_size = copy.copy(self.default_custom_paper_size)
        self.last_margins = copy.copy(self.default_margins)
        self.last_css_filename = self.default_css_filename
        self.last_format_name = self.default_format_name
        self.option_list_map = {}

    def set_last_paper_metric(self, paper_metric):
        """
        Set the last paper metric used for the any report in this collection.
        @param paper_metric: whether to use metric.
        @type paper_name: boolean
        """
        self.last_paper_metric = paper_metric

    def get_last_paper_metric(self):
        """
        Return the last paper metric used for the any report in this collection.
        @returns: returns whether or not to use metric
        @rtype: boolean
        """
        return self.last_paper_metric

    def set_last_paper_name(self, paper_name):
        """
        Set the last paper name used for the any report in this collection.
        @param paper_name: name of the paper to set.
        @type paper_name: str
        """
        self.last_paper_name = paper_name

    def get_last_paper_name(self):
        """
        Return the last paper name used for the any report in this collection.
        @returns: returns the name of the paper
        @rtype: str
        """
        return self.last_paper_name

    def set_last_orientation(self, orientation):
        """
        Set the last orientation used for the any report in this collection.
        @param orientation: orientation to set.
        @type orientation: int
        """
        self.last_orientation = orientation

    def get_last_orientation(self):
        """
        Return the last orientation used for the any report in this
        collection.
        @returns: last orientation used
        @rtype: int
        """
        return self.last_orientation

    def set_last_custom_paper_size(self, custom_paper_size):
        """
        Set the last custom paper size used for the any report in this collection.
        @param custom_paper_size: size to set in cm (width, height)
        @type margins: [float, float]
        """
        self.last_custom_paper_size = copy.copy(custom_paper_size)

    def get_last_custom_paper_size(self):
        """
        Return the last custom paper size used for the any report in this
        collection.
        @returns: list of last custom paper size used in cm (width, height)
        @rtype: [float, float]
        """
        return copy.copy(self.last_custom_paper_size)

    def set_last_margins(self, margins):
        """
        Set the last margins used for the any report in this collection.
        @param margins: margins to set in cm (left, right, top, bottom)
        @type margins: [float, float, float, float]
        """
        self.last_margins = copy.copy(margins)

    def get_last_margins(self):
        """
        Return the last margins used for the any report in this
        collection.
        @returns: list of last margins used in cm (left, right, top, bottom)
        @rtype: [float, float, float, float]
        """
        return copy.copy(self.last_margins)

    def set_last_margin(self, pos, value):
        """
        Set the last margin used for the any report in this collection.
        @param pos: pos to set (0-4) (left, right, top, bottom)
        @type pos: int
        @param value: value to set the margin to in cm
        @type value: float
        """
        self.last_margins[pos] = value

    def get_last_margin(self, pos):
        """
        Return the last margins used for the any report in this
        collection.
        @param pos: position in margins list
        @type pos: int
        @returns: last margin used in pos
        @rtype: float
        """
        return self.last_margins[pos]

    def set_last_css_filename(self, css_filename):
        """
        Set the last css used for the any report in this collection.

        css_filename: name of the style to set.
        """
        self.last_css_name = css_filename

    def get_last_css_filename(self):
        """
        Return the last template used for the any report in this collection.
        """
        return self.last_css_filename

    def set_last_format_name(self, format_name):
        """
        Set the last format used for the any report in this collection.
        
        format_name: name of the format to set.
        """
        self.last_format_name = format_name

    def get_last_format_name(self):
        """
        Return the last format used for the any report in this collection.
        """
        return self.last_format_name

    def write_common(self, f):
        f.write('<last-common>\n')
        if self.get_last_paper_metric() != self.default_paper_metric:
            f.write('  <metric value="%d"/>\n' % self.get_last_paper_metric() )
        if self.get_last_custom_paper_size() != self.default_custom_paper_size:
            size = self.get_last_custom_paper_size()
            f.write('  <size value="%f %f"/>\n' % (size[0], size[1]) )
        if self.get_last_paper_name() != self.default_paper_name:
            f.write('  <paper name="%s"/>\n' % escxml(self.get_last_paper_name()) )
        if self.get_last_css_filename() != self.default_css_filename:
            f.write('  <css name="%s"/>\n' % escxml(self.get_last_css_filename()) )
        if self.get_last_format_name() != self.default_format_name:
            f.write('  <format name="%s"/>\n' % escxml(self.get_last_format_name()) )
        if self.get_last_orientation() != self.default_orientation:
            f.write('  <orientation value="%d"/>\n' % self.get_last_orientation() )
        f.write('</last-common>\n')

    def write_module_common(self, f, option_list):
        if option_list.get_style_name() \
               and option_list.get_style_name() != self.default_style_name:
            f.write('  <style name="%s"/>\n' % escxml(option_list.get_style_name()) )
        if option_list.get_paper_metric() \
               and option_list.get_paper_metric() != self.default_paper_metric:
            f.write('  <metric value="%d"/>\n' % option_list.get_paper_metric() )
        if option_list.get_custom_paper_size() \
                and option_list.get_custom_paper_size() != self.default_custom_paper_size:
            size = self.get_last_custom_paper_size()
            f.write('  <size value="%f %f"/>\n' % (size[0], size[1]) )
        if option_list.get_paper_name() \
               and option_list.get_paper_name() != self.default_paper_name:
            f.write('  <paper name="%s"/>\n' % escxml(option_list.get_paper_name()) )
        if option_list.get_css_filename() \
               and option_list.get_css_filename() != self.default_css_filename:
            f.write('  <css name="%s"/>\n' % escxml(option_list.get_css_filename()))
        if option_list.get_format_name() \
               and option_list.get_format_name() != self.default_format_name:
            f.write('  <format name="%s"/>\n' % escxml(option_list.get_format_name()) )
        if option_list.get_orientation() \
               and option_list.get_orientation() != self.default_orientation:
            f.write('  <orientation value="%d"/>\n' % option_list.get_orientation() )
        if option_list.get_margins() \
               and option_list.get_margins() != self.default_margins:
            margins = option_list.get_margins()
            for pos in range(len(margins)): 
                f.write('  <margin number="%s" value="%f"/>\n' % (pos, margins[pos]))

    def parse(self):
        """
        Loads the OptionList from the associated file, if it exists.
        """
        try:
            if os.path.isfile(self.filename):
                p = make_parser()
                p.setContentHandler(OptionParser(self))
                the_file = open(self.filename)
                p.parse(the_file)
                the_file.close()
        except (IOError, OSError, SAXParseException):
            pass

#-------------------------------------------------------------------------
#
# OptionParser
#
#-------------------------------------------------------------------------
class OptionParser(_options.OptionParser):
    """
    SAX parsing class for the OptionListCollection XML file.
    """
    
    def __init__(self, collection):
        """
        Create a OptionParser class that populates the passed collection.

        collection:   BookList to be loaded from the file.
        """
        _options.OptionParser.__init__(self, collection)
        self.common = False
        self.list_class = OptionList

    def startElement(self, tag, attrs):
        """
        Overridden class that handles the start of a XML element
        """
        # First we try report-specific tags
        if tag == "last-common":
            self.common = True
        elif tag == "style":
            self.option_list.set_style_name(attrs['name'])
        elif tag == "paper":
            if self.common:
                self.collection.set_last_paper_name(attrs['name'])
            else:
                self.option_list.set_paper_name(attrs['name'])
        elif tag == "css":
            if self.common:
                self.collection.set_last_css_filename(attrs['name'])
            else:
                self.option_list.set_css_filename(attrs['name'])
        elif tag == "format":
            if self.common:
                self.collection.set_last_format_name(attrs['name'])
            else:
                self.option_list.set_format_name(attrs['name'])
        elif tag == "orientation":
            if self.common:
                self.collection.set_last_orientation(int(attrs['value']))
            else:
                self.option_list.set_orientation(int(attrs['value']))
        elif tag == "metric":
            if self.common:
                self.collection.set_last_paper_metric(int(attrs['value']))
            else:
                self.option_list.set_paper_metric(int(attrs['value']))
        elif tag == "size":
            width, height = attrs['value'].split()
            width = float(width)
            height = float(height)
            if self.common:
                self.collection.set_last_custom_paper_size([width, height])
            else:
                self.option_list.set_custom_paper_size([width, height])

        elif tag == "margin":
            pos, value = int(attrs['number']), float(attrs['value'])
            if self.common:
                self.collection.set_last_margin(pos, value)
            else:
                self.option_list.set_margin(pos, value)
        else:
            # Tag is not report-specific, so we let the base class handle it.
            _options.OptionParser.startElement(self, tag, attrs)

    def endElement(self, tag):
        "Overridden class that handles the end of a XML element"
        # First we try report-specific tags
        if tag == "last-common":
            self.common = False
        else:
            # Tag is not report-specific, so we let the base class handle it.
            _options.OptionParser.endElement(self, tag)
            
#------------------------------------------------------------------------
#
# Empty class to keep the BaseDoc-targeted format happy
# Yes, this is a hack. Find some other way to pass around documents so that
# we don't have to handle them for reports that don't use documents (web)
#
#------------------------------------------------------------------------
class EmptyDoc(object):
    def init(self):
        pass

    def set_creator(self, creator):
        pass
    
    def open(self, filename):
        pass
    
    def close(self):
        pass

#-------------------------------------------------------------------------
#
# Class handling options for plugins 
#
#-------------------------------------------------------------------------
class OptionHandler(_options.OptionHandler):
    """
    Implements handling of the options for the plugins.
    """
    def __init__(self, module_name, options_dict):
        _options.OptionHandler.__init__(self, module_name, options_dict, None)

    def init_subclass(self):
        self.collection_class = OptionListCollection
        self.list_class = OptionList
        self.filename = const.REPORT_OPTIONS

    def init_common(self):
        """
        Specific initialization for reports.
        """
        # These are needed for running reports.
        # We will not need to save/retrieve them, just keep around.
        self.doc = EmptyDoc() # Nasty hack. Text reports replace this
        self.output = None

        # Retrieve our options from whole collection
        self.style_name = self.option_list_collection.default_style_name
        self.paper_metric = self.option_list_collection.get_last_paper_metric()
        self.paper_name = self.option_list_collection.get_last_paper_name()
        self.orientation = self.option_list_collection.get_last_orientation()
        self.custom_paper_size = self.option_list_collection.get_last_custom_paper_size()
        self.css_filename = self.option_list_collection.get_last_css_filename()
        self.margins = self.option_list_collection.get_last_margins()
        self.format_name = self.option_list_collection.get_last_format_name()

    def set_common_options(self):
        if self.saved_option_list.get_style_name():
            self.style_name = self.saved_option_list.get_style_name()
        if self.saved_option_list.get_orientation():
            self.orientation = self.saved_option_list.get_orientation()
        if self.saved_option_list.get_custom_paper_size():
            self.custom_paper_size = self.saved_option_list.get_custom_paper_size()
        if self.saved_option_list.get_margins():
            self.margins = self.saved_option_list.get_margins()
        if self.saved_option_list.get_css_filename():
            self.css_filename = self.saved_option_list.get_css_filename()
        if self.saved_option_list.get_paper_metric():
            self.paper_metric = self.saved_option_list.get_paper_metric()
        if self.saved_option_list.get_paper_name():
            self.paper_name = self.saved_option_list.get_paper_name()
        if self.saved_option_list.get_format_name():
            self.format_name = self.saved_option_list.get_format_name()

    def save_common_options(self):
        # First we save common options
        self.saved_option_list.set_style_name(self.style_name)
        self.saved_option_list.set_orientation(self.orientation)
        self.saved_option_list.set_custom_paper_size(self.custom_paper_size)
        self.saved_option_list.set_margins(self.margins)
        self.saved_option_list.set_paper_metric(self.paper_metric)
        self.saved_option_list.set_paper_name(self.paper_name)
        self.saved_option_list.set_css_filename(self.css_filename)
        self.saved_option_list.set_format_name(self.format_name)
        self.option_list_collection.set_option_list(self.module_name,
                                                    self.saved_option_list)

        # Then save last-common options from the current selection
        self.option_list_collection.set_last_orientation(self.orientation)
        self.option_list_collection.set_last_custom_paper_size(self.custom_paper_size)
        self.option_list_collection.set_last_margins(self.margins)
        self.option_list_collection.set_last_paper_metric(self.paper_metric)
        self.option_list_collection.set_last_paper_name(self.paper_name)
        self.option_list_collection.set_last_css_filename(self.css_filename)
        self.option_list_collection.set_last_format_name(self.format_name)

    def get_stylesheet_savefile(self):
        """Where to save user defined styles for this report."""
        filename = "%s.xml" % self.module_name
        return os.path.join(const.HOME_DIR, filename) 

    def get_default_stylesheet_name(self):
        return self.style_name

    def set_default_stylesheet_name(self, style_name):
        self.style_name = style_name

    def get_format_name(self):
        return self.format_name

    def set_format_name(self, format_name):
        self.format_name = format_name

    def get_paper_metric(self):
        return self.paper_metric

    def set_paper_metric(self, paper_metric):
        self.paper_metric = paper_metric

    def get_paper_name(self):
        return self.paper_name

    def set_paper_name(self, paper_name):
        self.paper_name = paper_name

    def get_paper(self):
        """
        This method is for temporary storage, not for saving/restoring.
        """
        return self.paper

    def set_paper(self, paper):
        """
        This method is for temporary storage, not for saving/restoring.
        """
        self.paper = paper

    def get_css_filename(self):
        return self.css_filename

    def set_css_filename(self, css_filename):
        self.css_filename = css_filename

    def get_orientation(self):
        return self.orientation

    def set_orientation(self, orientation):
        self.orientation = orientation

    def get_custom_paper_size(self):
        return copy.copy(self.custom_paper_size)

    def set_custom_paper_size(self, custom_paper_size):
        self.custom_paper_size = copy.copy(custom_paper_size)

    def get_margins(self):
        return copy.copy(self.margins)

    def set_margins(self,margins):
        self.margins = copy.copy(margins)

#------------------------------------------------------------------------
#
# Base Options class
#
#------------------------------------------------------------------------
class ReportOptions(_options.Options):

    """
    Defines options and provides handling interface.
    
    This is a base Options class for the reports. All reports, options
    classes should derive from it.
    """
    def __init__(self, name, dbase):
        """
        Initialize the class, performing usual house-keeping tasks.
        Subclasses MUST call this in their __init__() method.
        """
        self.name = name
        self.options_dict = {}
        self.options_help = {}
        self.handler = None
        
    def load_previous_values(self):
        self.handler = OptionHandler(self.name, self.options_dict)

    def make_default_style(self, default_style):
        """
        Defines default style for this report.
        
        This method MUST be overridden by reports that use the
        user-adjustable paragraph styles.

        NOTE:   Unique names MUST be used for all style names, otherwise the
                styles will collide when making a book with duplicate style
                names. A rule of safety is to prepend style name with the
                acronym based on report name. The following acronyms are
                already taken:
                    AC-     Ancestor Chart
                    AC2-    Ancestor Chart 2 (Wall Chart)
                    AHN-    Ahnentafel Report
                    AR-     Comprehensive Ancestors report
                    CBT-    Custom Book Text
                    DG-     Descendant Graph
                    DR-     Descendant Report
                    DAR-    Detailed Ancestral Report
                    DDR-    Detailed Descendant Report
                    FGR-    Family Group Report
                    FC-     Fan Chart
                    FTA-    FTM Style Ancestral report
                    FTD-    FTM Style Descendant report
                    IDS-    Individual Complete Report
                    IVS-    Individual Summary Report
                    PLC-    Place Report
                    SBT-    Simple Boot Title
                    TLG-    Timeline Graph
        """
        pass

    def get_document(self):
        """
        Return document instance.
        
        This method MUST NOT be overridden by subclasses.
        """
        return self.handler.doc

    def set_document(self, val):
        """
        Set document to a given instance.
        
        This method MUST NOT be overridden by subclasses.
        """
        self.handler.doc = val

    def get_output(self):
        """
        Return document output destination.
        
        This method MUST NOT be overridden by subclasses.
        """
        return self.handler.output

    def set_output(self, val):
        """
        Set output destination to a given string.
        
        This method MUST NOT be overridden by subclasses.
        """
        self.handler.output = val

#-------------------------------------------------------------------------
#
# MenuReportOptions
#
#-------------------------------------------------------------------------
class MenuReportOptions(GuiMenuOptions, ReportOptions):
    """

    The MenuReportOptions class implements the ReportOptions
    functionality in a generic way so that the user does not need to
    be concerned with the graphical representation of the options.
    
    The user should inherit the MenuReportOptions class and override the 
    add_menu_options function. The user can add options to the menu and the 
    MenuReportOptions class will worry about setting up the GUI.

    """
    def __init__(self, name, dbase):
        ReportOptions.__init__(self, name, dbase)
        GuiMenuOptions.__init__(self)
        
    def load_previous_values(self):
        ReportOptions.load_previous_values(self)
        # Pass the loaded values to the menu options so they will be displayed 
        # properly.
        for optname in self.options_dict:
            menu_option = self.menu.get_option_by_name(optname)
            if menu_option:
                menu_option.set_value(self.options_dict[optname])