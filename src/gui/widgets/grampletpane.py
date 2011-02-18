#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2011 Nick Hall
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
GrampletView interface.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import gtk
import pango
import time
import os
from gen.ggettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import Errors
import const
from gui.editors import EditPerson, EditFamily
import ManagedWindow
import ConfigParser
from gui.utils import add_menuitem
from QuickReports import run_quick_report_by_name
import GrampsDisplay
from glade import Glade
from gui.pluginmanager import GuiPluginManager
from gui.widgets.undoablebuffer import UndoableBuffer

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = const.URL_MANUAL_PAGE + '_-_Gramplets'

#-------------------------------------------------------------------------
#
# Globals
#
#-------------------------------------------------------------------------
PLUGMAN = GuiPluginManager.get_instance()
NL = "\n" 

def AVAILABLE_GRAMPLETS():
    return [gplug.id for gplug in PLUGMAN.get_reg_gramplets()]

def GET_AVAILABLE_GRAMPLETS(name):
    for gplug in PLUGMAN.get_reg_gramplets():
        if gplug.id == name:
            return {
                "name":    gplug.id,
                "tname":   gplug.name,
                "version": gplug.version,
                "height":  gplug.height,
                "expand":  gplug.expand, 
                "title":   gplug.gramplet_title,
                "content": gplug.gramplet,
                "detached_width": gplug.detached_width,
                "detached_height": gplug.detached_height,
                "state":   "maximized",
                "gramps":  "0.0.0",
                "column":  -1, 
                "row":     -1,
                "page":     0,
                "data":    [],
                "help_url": gplug.help_url,
                }
    return None

def parse_tag_attr(text):
    """
    Function used to parse markup.
    """
    text = text.strip()
    parts = text.split(" ", 1)
    attrs = {}
    if len(parts) == 2:
        attr_values = parts[1].split(" ") # "name=value name=value"
        for av in attr_values:
            attribute, value = av.split("=", 1)
            value = value.strip()
            # trim off quotes:
            if value[0] == value[-1] and value[0] in ['"', "'"]:
                value = value[1:-1]
            attrs[attribute.strip().lower()] = value
    return [parts[0].upper(), attrs]

def get_gramplet_opts(name, opts):
    """
    Lookup the options for a given gramplet name and update
    the options with provided dictionary, opts.
    """
    if name in AVAILABLE_GRAMPLETS():
        data = GET_AVAILABLE_GRAMPLETS(name)
        my_data = data.copy()
        my_data.update(opts)
        return my_data
    else:
        print ("Unknown gramplet name: '%s'" % name)
        return {}

def get_gramplet_options_by_name(name):
    """
    Get options by gramplet name.
    """
    if name in AVAILABLE_GRAMPLETS():
        return GET_AVAILABLE_GRAMPLETS(name).copy()
    else:
        print ("Unknown gramplet name: '%s'" % name)
        return None

def get_gramplet_options_by_tname(name):
    """
    get options by translated name.
    """
    for key in AVAILABLE_GRAMPLETS():
        if GET_AVAILABLE_GRAMPLETS(key)["tname"] == name:
            return GET_AVAILABLE_GRAMPLETS(key).copy()
    print ("Unknown gramplet name: '%s'" % name)
    return None

def make_requested_gramplet(gui_class, pane, opts, dbstate, uistate):
    """
    Make a GUI gramplet given its name.
    """
    name = opts["name"]
    if name in AVAILABLE_GRAMPLETS():
        gui = gui_class(pane, dbstate, uistate, **opts)
        if opts.get("content", None):
            pdata = PLUGMAN.get_plugin(name)
            module = PLUGMAN.load_plugin(pdata)
            if module:
                getattr(module, opts["content"])(gui)
            else:
                print "Error loading gramplet '%s': skipping content" % name
        return gui
    return None

def logical_true(value):
    """
    Used for converting text file values to booleans.
    """
    return value in ["True", True, 1, "1"]

class LinkTag(gtk.TextTag):
    """
    Class for keeping track of link data.
    """
    lid = 0
    def __init__(self, buffer):
        LinkTag.lid += 1
        gtk.TextTag.__init__(self, str(LinkTag.lid))
        tag_table = buffer.get_tag_table()
        self.set_property('foreground', "blue")
        #self.set_property('underline', pango.UNDERLINE_SINGLE)
        try:
            tag_table.add(self)
        except ValueError: # tag is already in tag table
            pass

class GrampletWindow(ManagedWindow.ManagedWindow):
    """
    Class for showing a detached gramplet.
    """
    def __init__(self, gramplet):
        """
        Constructs the window, and loads the GUI gramplet.
        """
        self.title = gramplet.title + " " + _("Gramplet")
        self.gramplet = gramplet
        self.gramplet.detached_window = self
        # Keep track of what state it was in:
        self.docked_state = gramplet.gstate
        # Now detach it
        self.gramplet.set_state("detached") 
        ManagedWindow.ManagedWindow.__init__(self, gramplet.uistate, [],
                                             self.title)
        self.set_window(gtk.Dialog("", gramplet.uistate.window,
                                   gtk.DIALOG_DESTROY_WITH_PARENT,
                                   (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)),
                        None, self.title)
        self.window.set_size_request(gramplet.detached_width,
                                     gramplet.detached_height)
        self.window.add_button(gtk.STOCK_HELP, gtk.RESPONSE_HELP)
        # add gramplet:
        if self.gramplet.pui:
            self.gramplet.pui.active = True
        self.gramplet.mainframe.reparent(self.window.vbox)
        self.window.connect('response', self.handle_response)
        self.show()
        # After we show, then we hide:
        self.gramplet.gvclose.hide()
        self.gramplet.gvstate.hide()
        self.gramplet.gvproperties.hide()
        if self.gramplet.titlelabel_entry:
            self.gramplet.titlelabel_entry.hide()
        if self.gramplet.pui:
            for widget in self.gramplet.pui.hidden_widgets():
                widget.hide()

    def handle_response(self, object, response):
        """
        Callback for taking care of button clicks.
        """
        if response in [gtk.RESPONSE_CLOSE, gtk.STOCK_CLOSE]:
            self.close()
        elif response == gtk.RESPONSE_HELP:
            # translated name:
            if self.gramplet.help_url:
                if self.gramplet.help_url.startswith("http://"):
                    GrampsDisplay.url(self.gramplet.help_url)
                else:
                    GrampsDisplay.help(self.gramplet.help_url)
            else:
                GrampsDisplay.help(WIKI_HELP_PAGE, 
                                   self.gramplet.tname.replace(" ", "_"))
        
    def build_menu_names(self, obj):
        """
        Part of the GRAMPS window interface.
        """
        return (self.title, 'Gramplet')

    def get_title(self):
        """
        Returns the window title.
        """
        return self.title

    def close(self, *args):
        """
        Dock the detached GrampletWindow back in the column from where it came.
        """
        self.gramplet.detached_window = None
        self.gramplet.pane.detached_gramplets.remove(self.gramplet)
        if self.docked_state == "minimized":
            self.gramplet.set_state("minimized")
        else:
            self.gramplet.set_state("maximized")
        pane = self.gramplet.pane
        col = self.gramplet.column
        stack = []
        for gframe in pane.columns[col]:
            gramplet = pane.frame_map[str(gframe)]
            if gramplet.row > self.gramplet.row:
                pane.columns[col].remove(gframe)
                stack.append(gframe)
        expand = self.gramplet.gstate == "maximized" and self.gramplet.expand
        column = pane.columns[col]
        parent = self.gramplet.pane.get_column_frame(self.gramplet.column)
        self.gramplet.mainframe.reparent(parent)
        if self.gramplet.pui:
            self.gramplet.pui.active = self.gramplet.pane.pageview.active
        for gframe in stack:
            gramplet = pane.frame_map[str(gframe)]
            expand = gramplet.gstate == "maximized" and gramplet.expand
            pane.columns[col].pack_start(gframe, expand=expand)
        # Now make sure they all have the correct expand:
        for gframe in pane.columns[col]:
            gramplet = pane.frame_map[str(gframe)]
            expand, fill, padding, pack = column.query_child_packing(gramplet.mainframe)
            expand = gramplet.gstate == "maximized" and gramplet.expand
            column.set_child_packing(gramplet.mainframe, expand, fill, padding, pack)
        self.gramplet.gvclose.show()
        self.gramplet.gvstate.show()
        self.gramplet.gvproperties.show()
        ManagedWindow.ManagedWindow.close(self, *args)

#------------------------------------------------------------------------

class GuiGramplet(object):
    """
    Class that handles the GUI representation of a Gramplet.
    """
    def __init__(self, pane, dbstate, uistate, title, **kwargs):
        """
        Internal constructor for GUI portion of a gramplet.
        """
        self.pane = pane
        self.view = pane.pageview
        self.dbstate = dbstate
        self.uistate = uistate
        self.title = title
        self.detached_window = None
        self.force_update = False
        self._tags = []
        ########## Set defaults
        self.gname = kwargs.get("name", "Unnamed Gramplet")
        self.tname = kwargs.get("tname", "Unnamed Gramplet")
        self.version = kwargs.get("version", "0.0.0")
        self.gramps = kwargs.get("gramps", "0.0.0")
        self.expand = logical_true(kwargs.get("expand", False))
        self.height = int(kwargs.get("height", 200))
        self.width = int(kwargs.get("width", 375))
        self.column = int(kwargs.get("column", -1))
        self.detached_height = int(kwargs.get("detached_height", 300))
        self.detached_width = int(kwargs.get("detached_width", 400))
        self.row = int(kwargs.get("row", -1))
        self.page = int(kwargs.get("page", -1))
        self.gstate = kwargs.get("state", "maximized")
        self.data = kwargs.get("data", [])
        self.help_url = kwargs.get("help_url", WIKI_HELP_PAGE)
        ##########
        self.use_markup = False
        self.pui = None # user code
        self.tooltips_text = None

        self.link_cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
        self.standard_cursor = gtk.gdk.Cursor(gtk.gdk.XTERM)

        self.scrolledwindow = None
        self.textview = None
        self.buffer = None

    def set_tooltip(self, tip):
        self.tooltips_text = tip
        self.scrolledwindow.set_tooltip_text(tip)
        
    def undo(self):
        self.buffer.undo()
        self.text_length = len(self.get_text())

    def redo(self):
        self.buffer.redo()
        self.text_length = len(self.get_text())

    def on_key_press_event(self, widget, event):
        """Signal handler.
        
        Handle formatting shortcuts.
        
        """
        if ((gtk.gdk.keyval_name(event.keyval) == 'Z') and
            (event.state & gtk.gdk.CONTROL_MASK) and 
            (event.state & gtk.gdk.SHIFT_MASK)):
            self.redo()
            return True
        elif ((gtk.gdk.keyval_name(event.keyval) == 'z') and
              (event.state & gtk.gdk.CONTROL_MASK)):
            self.undo()
            return True

        return False

    def append_text(self, text, scroll_to="end"):
        enditer = self.buffer.get_end_iter()
        start = self.buffer.create_mark(None, enditer, True)
        self.buffer.insert(enditer, text)
        self.text_length += len(text)
        if scroll_to == "end":
            enditer = self.buffer.get_end_iter()
            end = self.buffer.create_mark(None, enditer, True)
            self.textview.scroll_to_mark(end, 0.0, True, 0, 0)
        elif scroll_to == "start": # beginning of this append
            self.textview.scroll_to_mark(start, 0.0, True, 0, 0)
        elif scroll_to == "begin": # beginning of the buffer
            begin_iter = self.buffer.get_start_iter()
            begin = self.buffer.create_mark(None, begin_iter, True)
            self.textview.scroll_to_mark(begin, 0.0, True, 0, 0)
        else:
            raise AttributeError, ("no such cursor position: '%s'" % scroll_to)

    def clear_text(self):
        self.buffer.set_text('')
        self.text_length = 0

    def get_text(self):
        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        return self.buffer.get_text(start, end)

    def insert_text(self, text):
        self.buffer.insert_at_cursor(text)
        self.text_length += len(text)

    def len_text(self, text):
        i = 0
        r = 0
        while i < len(text):
            if ord(text[i]) > 126:
                t = 0
                while i < len(text) and ord(text[i]) > 126:
                    i += 1
                    t += 1
                r += t/2
            elif text[i] == "\\":
                r += 1
                i += 2
            else:
                r += 1
                i += 1
        return r

    def render_text(self, text):
        markup_pos = {"B": [], "I": [], "U": [], "A": [], "TT": []}
        retval = ""
        i = 0
        r = 0
        tag = ""
        while i < len(text):
            if text[i:i+2] == "</":
                # start of ending tag
                stop = text[i:].find(">")
                if stop < 0:
                    retval += text[i]
                    r += 1
                    i += 1
                else:
                    markup = text[i+2:i+stop].upper() # close tag
                    markup_pos[markup][-1].append(r)
                    i += stop + 1
            elif text[i] == "<":
                # start of start tag
                stop = text[i:].find(">")
                if stop < 0:
                    retval += text[i]
                    r += 1
                    i += 1
                else:
                    markup, attr = parse_tag_attr(text[i+1:i+stop])
                    markup_pos[markup].append([r, attr])
                    i += stop + 1
            elif text[i] == "\\":
                retval += text[i+1]
                r += 1
                i += 2
            elif ord(text[i]) > 126:
                while ord(text[i]) > 126:
                    retval += text[i]
                    i += 1
                r += 1
            else:
                retval += text[i]
                r += 1
                i += 1
        offset = self.text_length 
        self.append_text(retval)
        for items in markup_pos["TT"]:
            if len(items) == 3:
                (a, attributes, b) = items
                start = self.buffer.get_iter_at_offset(a + offset)
                stop = self.buffer.get_iter_at_offset(b + offset)
                self.buffer.apply_tag_by_name("fixed", start, stop)
        for items in markup_pos["B"]:
            if len(items) == 3:
                (a, attributes, b) = items
                start = self.buffer.get_iter_at_offset(a + offset)
                stop = self.buffer.get_iter_at_offset(b + offset)
                self.buffer.apply_tag_by_name("bold", start, stop)
        for items in markup_pos["I"]:
            if len(items) == 3:
                (a, attributes, b) = items
                start = self.buffer.get_iter_at_offset(a + offset)
                stop = self.buffer.get_iter_at_offset(b + offset)
                self.buffer.apply_tag_by_name("italic", start, stop)
        for items in markup_pos["U"]:
            if len(items) == 3:
                (a, attributes, b) = items
                start = self.buffer.get_iter_at_offset(a + offset)
                stop = self.buffer.get_iter_at_offset(b + offset)
                self.buffer.apply_tag_by_name("underline", start, stop)
        for items in markup_pos["A"]:
            if len(items) == 3:
                (a, attributes, b) = items
                start = self.buffer.get_iter_at_offset(a + offset)
                stop = self.buffer.get_iter_at_offset(b + offset)
                if "href" in attributes:
                    url = attributes["href"]
                    self.link_region(start, stop, "URL", url) # tooltip?
                elif "wiki" in attributes:
                    url = attributes["wiki"]
                    self.link_region(start, stop, "WIKI", url) # tooltip?
                else:
                    print "warning: no url on link: '%s'" % text[start, stop]

    def link_region(self, start, stop, link_type, url):
        link_data = (LinkTag(self.buffer), link_type, url, url)
        self._tags.append(link_data)
        self.buffer.apply_tag(link_data[0], start, stop)

    def set_use_markup(self, value):
        if self.use_markup == value: return
        self.use_markup = value
        if value:
            self.buffer.create_tag("bold", weight=pango.WEIGHT_HEAVY)
            self.buffer.create_tag("italic", style=pango.STYLE_ITALIC)
            self.buffer.create_tag("underline",
                                            underline=pango.UNDERLINE_SINGLE)
            self.buffer.create_tag("fixed", font="monospace")
        else:
            tag_table = self.buffer.get_tag_table()
            tag_table.foreach(lambda tag, data: tag_table.remove(tag))

    def set_text(self, text, scroll_to='start'):
        self.buffer.set_text('')
        self.text_length = 0
        self.append_text(text, scroll_to)
        self.buffer.reset()

    def get_container_widget(self):
        raise NotImplementedError

    def make_gui_options(self):
        if not self.pui: return
        # BEGIN WORKAROUND: 
        # This is necessary because gtk doesn't redisplay these widgets
        # correctly so we replace them with new ones
        self.pui.save_options()
        self.pui.update_options = {}
        self.pui.option_order = []
        self.pui.build_options()
        # END WORKAROUND
        if len(self.pui.option_order) == 0: return
        frame = gtk.Frame()
        topbox = gtk.VBox(False)
        hbox = gtk.HBox(False, 5)
        labels = gtk.VBox(True)
        options = gtk.VBox(True)
        hbox.pack_start(labels, False)
        hbox.pack_start(options, True)
        topbox.pack_start(hbox, False, False)
        for item in self.pui.option_order:
            label = gtk.Label(item + ":")
            label.set_alignment(1.0, 0.5)
            labels.pack_start(label)
            options.pack_start(self.pui.option_dict[item][0]) # widget
        save_button = gtk.Button(stock=gtk.STOCK_SAVE)
        topbox.pack_end(save_button, False, False)
        save_button.connect('clicked', self.pui.save_update_options)
        frame.add(topbox)
        frame.show_all()
        return frame

    def link(self, text, link_type, data, size=None, tooltip=None):
        buffer = self.buffer
        iter = buffer.get_end_iter()
        offset = buffer.get_char_count()
        self.append_text(text)
        start = buffer.get_iter_at_offset(offset)
        end = buffer.get_end_iter()
        link_data = (LinkTag(buffer), link_type, data, tooltip)
        if size:
            link_data[0].set_property("size-points", size)
        self._tags.append(link_data)
        buffer.apply_tag(link_data[0], start, end)

    def on_motion(self, view, event):
        buffer_location = view.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT, 
                                                       int(event.x), 
                                                       int(event.y))
        iter = view.get_iter_at_location(*buffer_location)
        cursor = self.standard_cursor
        ttip = None
        for (tag, link_type, handle, tooltip) in self._tags:
            if iter.has_tag(tag):
                tag.set_property('underline', pango.UNDERLINE_SINGLE)
                cursor = self.link_cursor
                ttip = tooltip
            else:
                tag.set_property('underline', pango.UNDERLINE_NONE)
        view.get_window(gtk.TEXT_WINDOW_TEXT).set_cursor(cursor)
        if ttip:
            self.scrolledwindow.set_tooltip_text(ttip)
        elif self.tooltips_text:
            self.scrolledwindow.set_tooltip_text(self.tooltips_text)
        return False # handle event further, if necessary

    def on_button_press(self, view, event):
        # pylint: disable-msg=W0212
        buffer_location = view.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT, 
                                                       int(event.x), 
                                                       int(event.y))
        iter = view.get_iter_at_location(*buffer_location)
        for (tag, link_type, handle, tooltip) in self._tags:
            if iter.has_tag(tag):
                if link_type == 'Person':
                    person = self.dbstate.db.get_person_from_handle(handle)
                    if person is not None:
                        if event.button == 1: # left mouse
                            if event.type == gtk.gdk._2BUTTON_PRESS: # double
                                try:
                                    EditPerson(self.dbstate, 
                                               self.uistate, 
                                               [], person)
                                    return True # handled event
                                except Errors.WindowActiveError:
                                    pass
                            elif event.type == gtk.gdk.BUTTON_PRESS: # single
                                self.uistate.set_active(handle, 'Person')
                                return True # handled event
                        elif event.button == 3: # right mouse
                            #FIXME: add a popup menu with options
                            try:
                                EditPerson(self.dbstate, 
                                           self.uistate, 
                                           [], person)
                                return True # handled event
                            except Errors.WindowActiveError:
                                pass
                elif link_type == 'Surname':
                    if event.button == 1: # left mouse
                        if event.type == gtk.gdk._2BUTTON_PRESS: # double
                            run_quick_report_by_name(self.dbstate, 
                                                     self.uistate, 
                                                     'samesurnames', 
                                                     handle)
                    return True
                elif link_type == 'Given':
                    if event.button == 1: # left mouse
                        if event.type == gtk.gdk._2BUTTON_PRESS: # double
                            run_quick_report_by_name(self.dbstate, 
                                                     self.uistate, 
                                                     'samegivens_misc', 
                                                     handle)
                    return True
                elif link_type == 'Filter':
                    if event.button == 1: # left mouse
                        if event.type == gtk.gdk._2BUTTON_PRESS: # double
                            run_quick_report_by_name(self.dbstate, 
                                                     self.uistate, 
                                                     'filterbyname', 
                                                     handle)
                    return True
                elif link_type == 'URL':
                    if event.button == 1: # left mouse
                        GrampsDisplay.url(handle)
                    return True
                elif link_type == 'WIKI':
                    if event.button == 1: # left mouse
                        handle = handle.replace(" ", "_")
                        if "#" in handle:
                            page, section = handle.split("#", 1)
                            GrampsDisplay.help(page, section)
                        else:
                            GrampsDisplay.help(handle)
                    return True
                elif link_type == 'Family':
                    family = self.dbstate.db.get_family_from_handle(handle)
                    if family is not None:
                        if event.button == 1: # left mouse
                            if event.type == gtk.gdk._2BUTTON_PRESS: # double
                                try:
                                    EditFamily(self.dbstate, 
                                               self.uistate, 
                                               [], family)
                                    return True # handled event
                                except Errors.WindowActiveError:
                                    pass
                        elif event.button == 3: # right mouse
                            #FIXME: add a popup menu with options
                            try:
                                EditFamily(self.dbstate, 
                                           self.uistate, 
                                           [], family)
                                return True # handled event
                            except Errors.WindowActiveError:
                                pass
                elif link_type == 'PersonList':
                    if event.button == 1: # left mouse
                        if event.type == gtk.gdk._2BUTTON_PRESS: # double
                            run_quick_report_by_name(self.dbstate, 
                                                     self.uistate, 
                                                     'filterbyname', 
                                                     'list of people',
                                                     handles=handle)
                    return True
                elif link_type == 'Attribute':
                    if event.button == 1: # left mouse
                        if event.type == gtk.gdk._2BUTTON_PRESS: # double
                            run_quick_report_by_name(self.dbstate, 
                                                     self.uistate, 
                                                     'attribute_match', 
                                                     handle)
                    return True
        return False # did not handle event

class GridGramplet(GuiGramplet):
    """
    Class that handles the plugin interfaces for the GrampletView.
    """
    TARGET_TYPE_FRAME = 80
    LOCAL_DRAG_TYPE   = 'GRAMPLET'
    LOCAL_DRAG_TARGET = (LOCAL_DRAG_TYPE, 0, TARGET_TYPE_FRAME)
    def __init__(self, pane, dbstate, uistate, title, **kwargs):
        """
        Internal constructor for GUI portion of a gramplet.
        """
        GuiGramplet.__init__(self, pane, dbstate, uistate, title,
                             **kwargs)

        self.xml = Glade()
        self.gvwin = self.xml.toplevel
        self.mainframe = self.xml.get_object('gvgramplet')
        self.gvwin.remove(self.mainframe)

        self.textview = self.xml.get_object('gvtextview')
        self.buffer = UndoableBuffer()
        self.text_length = 0
        self.textview.set_buffer(self.buffer)
        self.textview.connect("key-press-event", self.on_key_press_event)
        #self.buffer = self.textview.get_buffer()
        self.scrolledwindow = self.xml.get_object('gvscrolledwindow')
        self.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC,
                                       gtk.POLICY_AUTOMATIC)
        self.vboxtop = self.xml.get_object('vboxtop')
        self.titlelabel = self.xml.get_object('gvtitle')
        self.titlelabel.get_children()[0].set_text("<b><i>%s</i></b>" %
                                                                     self.title)
        self.titlelabel.get_children()[0].set_use_markup(True)
        self.titlelabel.connect("clicked", self.edit_title)
        self.titlelabel_entry = None
        self.gvclose = self.xml.get_object('gvclose')
        self.gvclose.connect('clicked', self.close)
        self.gvstate = self.xml.get_object('gvstate')
        self.gvstate.connect('clicked', self.change_state)
        self.gvproperties = self.xml.get_object('gvproperties')
        self.gvproperties.connect('clicked', self.set_properties)
        self.xml.get_object('gvcloseimage').set_from_stock(gtk.STOCK_CLOSE,
                                                           gtk.ICON_SIZE_MENU)
        self.xml.get_object('gvstateimage').set_from_stock(gtk.STOCK_REMOVE,
                                                           gtk.ICON_SIZE_MENU)
        self.xml.get_object('gvpropertiesimage').set_from_stock(gtk.STOCK_PROPERTIES,
                                                                gtk.ICON_SIZE_MENU)

        # source:
        drag = self.gvproperties
        drag.drag_source_set(gtk.gdk.BUTTON1_MASK,
                             [GridGramplet.LOCAL_DRAG_TARGET],
                             gtk.gdk.ACTION_COPY)

        # default tooltip
        msg = _("Drag Properties Button to move and click it for setup")
        if not self.tooltips_text:
            self.set_tooltip(msg)

    def edit_title(self, widget):
        """
        Edit the the title in the GUI.
        """
        parent = widget.get_parent()
        widget.hide()
        if self.titlelabel_entry is None:
            self.titlelabel_entry = gtk.Entry()
            parent = widget.get_parent()
            parent.pack_end(self.titlelabel_entry)
            self.titlelabel_entry.connect("focus-out-event",
                                          self.edit_title_done)
            self.titlelabel_entry.connect("activate", self.edit_title_done)
            self.titlelabel_entry.connect("key-press-event",
                                          self.edit_title_keypress)
        self.titlelabel_entry.set_text(widget.get_children()[0].get_text())
        self.titlelabel_entry.show()
        self.titlelabel_entry.grab_focus()
        return True

    def edit_title_keypress(self, widget, event):
        """
        Edit the title, handle escape.
        """
        if event.type == gtk.gdk.KEY_PRESS:
            if event.keyval == gtk.keysyms.Escape:
                self.titlelabel.show()
                widget.hide()

    def edit_title_done(self, widget, event=None):
        """
        Edit title in GUI, finishing callback.
        """
        result = self.set_title(widget.get_text())
        if result: # if ok to set title to that
            self.titlelabel.show()
            widget.hide()
        return False # Return False for gtk requirement

    def close(self, *obj):
        """
        Remove (delete) the gramplet from view. 
        """
        if self.gstate == "detached":
            return
        self.gstate = "closed"
        self.pane.closed_gramplets.append(self)
        self.mainframe.get_parent().remove(self.mainframe)

    def detach(self):
        """
        Detach the gramplet from the GrampletView, and open in own window.
        """
        # hide buttons:
        #self.set_state("detached") 
        self.pane.detached_gramplets.append(self)
        # make a window, and attach it there
        self.detached_window = GrampletWindow(self)

    def set_state(self, state):
        """
        Set the state of a gramplet.
        """
        oldstate = self.gstate
        self.gstate = state
        if state == "minimized":
            self.scrolledwindow.hide()
            self.xml.get_object('gvstateimage').set_from_stock(gtk.STOCK_ADD,
                                                            gtk.ICON_SIZE_MENU)
            column = self.mainframe.get_parent() # column
            expand, fill, padding, pack = column.query_child_packing(self.mainframe)
            column.set_child_packing(self.mainframe, False, fill, padding, pack)
        else:
            self.scrolledwindow.show()
            self.xml.get_object('gvstateimage').set_from_stock(gtk.STOCK_REMOVE,
                                                            gtk.ICON_SIZE_MENU)
            column = self.mainframe.get_parent() # column
            expand, fill, padding, pack = column.query_child_packing(self.mainframe)
            column.set_child_packing(self.mainframe,
                                     self.expand,
                                     fill,
                                     padding,
                                     pack)
            if self.pui and self.pui.dirty:
                self.pui.update()

    def change_state(self, obj):
        """
        Change the state of a gramplet.
        """
        if self.gstate == "detached":
            pass # don't change if detached
        else:
            if self.gstate == "maximized":
                self.set_state("minimized")
            else:
                self.set_state("maximized")
                
    def set_properties(self, obj):
        """
        Set the properties of a gramplet.
        """
        if self.gstate == "detached":
            pass
        else:
            self.detach()
        return
        self.expand = not self.expand
        if self.gstate == "maximized":
            column = self.mainframe.get_parent() # column
            expand, fill, padding, pack = column.query_child_packing(self.mainframe)
            column.set_child_packing(self.mainframe, self.expand, fill,
                                     padding, pack)
    def get_source_widget(self):
        """
        Hack to allow us to send this object to the drop_widget
        method as a context.
        """
        return self.gvproperties

    def get_container_widget(self):
        return self.scrolledwindow

    def get_title(self):
        return self.title

    def set_height(self, height):
        self.height = height
        self.scrolledwindow.set_size_request(-1, self.height)
        self.set_state(self.gstate)

    def get_height(self):
        return self.height

    def get_detached_height(self):
        return self.detached_height

    def get_detached_width(self):
        return self.detached_width

    def set_detached_height(self, height):
        self.detached_height = height

    def set_detached_width(self, width):
        self.detached_width = width

    def get_expand(self):
        return self.expand

    def set_expand(self, value):
        self.expand = value
        self.scrolledwindow.set_size_request(-1, self.height)
        self.set_state(self.gstate)

    def set_title(self, new_title):
        # can't do it if already titled that way
        if self.title == new_title: return True
        if new_title in self.pane.gramplet_map: return False
        del self.pane.gramplet_map[self.title] 
        self.title = new_title
        if self.detached_window:
            self.detached_window.window.set_title("%s %s - Gramps" % 
                                                  (new_title, _("Gramplet")))
        self.pane.gramplet_map[self.title] = self
        self.titlelabel.get_children()[0].set_text("<b><i>%s</i></b>" %
                                                                     self.title)
        self.titlelabel.get_children()[0].set_use_markup(True)
        return True
        
class GrampletPane(gtk.ScrolledWindow):
    def __init__(self, configfile, pageview, dbstate, uistate, **kwargs):
        self._config = Configuration(self)
        gtk.ScrolledWindow.__init__(self)
        self.configfile = os.path.join(const.VERSION_DIR, "%s.ini" % configfile)
        # default for new user; may be overridden in config:
        self.column_count = kwargs.get("column_count", 2) 
        # width of window, if sidebar; may be overridden in config:
        self.pane_position = kwargs.get("pane_position", -1) 
        self.pane_orientation = kwargs.get("pane_orientation", "horizontal") 
        self.splitview = kwargs.get("splitview", None) 
        self.default_gramplets = kwargs.get("default_gramplets", 
                ["Top Surnames Gramplet", "Welcome Gramplet"])
        self.dbstate = dbstate
        self.uistate = uistate
        self.pageview = pageview
        self.pane = self
        self._popup_xy = None
        user_gramplets = self.load_gramplets()
        # build the GUI:
        msg = _("Right click to add gramplets")
        self.set_tooltip_text(msg)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.hbox = gtk.HBox(homogeneous=True)
        # Set up drag and drop
        self.drag_dest_set(gtk.DEST_DEFAULT_MOTION |
                            gtk.DEST_DEFAULT_HIGHLIGHT |
                            gtk.DEST_DEFAULT_DROP,
                            [('GRAMPLET', 0, 80)],
                            gtk.gdk.ACTION_COPY)
        self.connect('drag_drop', self.drop_widget)
        self.connect('button-press-event', self._button_press)

        self.add_with_viewport(self.hbox)
        # Create the columns:
        self.columns = []
        for i in range(self.column_count):
            self.columns.append(gtk.VBox())
            self.hbox.pack_start(self.columns[-1], expand=True)
        # Load the gramplets
        self.gramplet_map = {} # title->gramplet
        self.frame_map = {} # frame->gramplet
        self.detached_gramplets = [] # list of detached gramplets
        self.closed_gramplets = []   # list of closed gramplets
        self.closed_opts = []      # list of closed options from ini file
        # get the user's gramplets from ~/.gramps/gramplets.ini
        # Load the user's gramplets:
        for (name, opts) in user_gramplets:
            all_opts = get_gramplet_opts(name, opts)
            if "title" not in all_opts:
                all_opts["title"] = "Untitled Gramplet"
            if "state" not in all_opts:
                all_opts["state"] = "maximized"
            # uniqify titles:
            unique = all_opts["title"]
            cnt = 1
            while unique in self.gramplet_map:
                unique = all_opts["title"] + ("-%d" % cnt)
                cnt += 1
            all_opts["title"] = unique
            if all_opts["state"] == "closed":
                self.gramplet_map[all_opts["title"]] = None # save closed name
                self.closed_opts.append(all_opts)
                continue
            g = make_requested_gramplet(GridGramplet, self, all_opts,
                                        self.dbstate, self.uistate)
            if g:
                self.gramplet_map[all_opts["title"]] = g
                self.frame_map[str(g.mainframe)] = g
            else:
                print "Can't make gramplet of type '%s'." % name
        self.place_gramplets()

    def show_all(self):
        """
        This seems to be necessary to hide the hidden 
        parts of a collapsed gramplet on main view.
        """
        super(GrampletPane, self).show_all()
        for gramplet in self.gramplet_map.values():
            if gramplet.gstate == "minimized":
                gramplet.set_state("minimized")

    def set_state_all(self):
        """
        This seems to be necessary to hide the hidden
        parts of a collapsed gramplet on sidebars.
        """
        for gramplet in self.gramplet_map.values():
            if gramplet.gstate in ["minimized", "maximized"]:
                gramplet.set_state(gramplet.gstate)

    def get_column_frame(self, column_num):
        if column_num < len(self.columns):
            return self.columns[column_num]
        else:
            return self.columns[-1] # it was too big, so select largest

    def clear_gramplets(self):
        """
        Detach all of the mainframe gramplets from the columns.
        """
        gramplets = (g for g in self.gramplet_map.itervalues() 
                        if g is not None)
        for gramplet in gramplets:
            if (gramplet.gstate == "detached" or gramplet.gstate == "closed"):
                continue
            column = gramplet.mainframe.get_parent()
            if column:
                column.remove(gramplet.mainframe)

    def place_gramplets(self, recolumn=False):
        """
        Place the gramplet mainframes in the columns.
        """
        gramplets = [g for g in self.gramplet_map.itervalues() 
                        if g is not None]
        # put the gramplets where they go:
        # sort by row
        gramplets.sort(key=lambda x: x.row)
        rows = [0] * max(self.column_count, 1)
        for cnt, gramplet in enumerate(gramplets):
            # see if the user wants this in a particular location:
            # and if there are that many columns
            if gramplet.column >= 0 and gramplet.column < self.column_count:
                pos = gramplet.column
            else:
                # else, spread them out:
                pos = cnt % self.column_count
            gramplet.column = pos
            gramplet.row = rows[gramplet.column]
            rows[gramplet.column] += 1
            if recolumn and (gramplet.gstate == "detached" or
                             gramplet.gstate == "closed"):
                continue
            if gramplet.gstate == "minimized":
                self.columns[pos].pack_start(gramplet.mainframe, expand=False)
            else:
                self.columns[pos].pack_start(gramplet.mainframe,
                                             expand=gramplet.expand)
            # set height on gramplet.scrolledwindow here:
            gramplet.scrolledwindow.set_size_request(-1, gramplet.height)
            # Can't minimize here, because GRAMPS calls show_all later:
            #if gramplet.gstate == "minimized": # starts max, change to min it
            #    gramplet.set_state("minimized") # minimize it
            # set minimized is called in page subclass hack (above)
            if gramplet.gstate == "detached":
                gramplet.detach() 
            elif gramplet.gstate == "closed":
                gramplet.close() 

    def load_gramplets(self):
        retval = []
        filename = self.configfile
        if filename and os.path.exists(filename):
            cp = ConfigParser.ConfigParser()
            cp.read(filename)
            for sec in cp.sections():
                if sec == "Gramplet View Options":
                    if "column_count" in cp.options(sec):
                        self.column_count = int(cp.get(sec, "column_count"))
                    if "pane_position" in cp.options(sec):
                        self.pane_position = int(cp.get(sec, "pane_position"))
                    if "pane_orientation" in cp.options(sec):
                        self.pane_orientation = cp.get(sec, "pane_orientation")
                else:
                    data = {"title": sec}
                    for opt in cp.options(sec):
                        if opt.startswith("data["):
                            temp = data.get("data", {})
                            #temp.append(cp.get(sec, opt).strip())
                            pos = int(opt[5:-1])
                            temp[pos] = cp.get(sec, opt).strip()
                            data["data"] = temp
                        else:
                            data[opt] = cp.get(sec, opt).strip()
                    if "data" in data:
                        data["data"] = [data["data"][key]
                                        for key in sorted(data["data"].keys())]
                    if "name" not in data:
                        data["name"] = "Unnamed Gramplet"
                        data["tname"] = _("Unnamed Gramplet")
                    retval.append((data["name"], data)) # name, opts
        else:
            # give defaults as currently known
            for name in self.default_gramplets:
                if name in AVAILABLE_GRAMPLETS():
                    retval.append((name, GET_AVAILABLE_GRAMPLETS(name)))
        return retval

    def save(self):
        if len(self.frame_map) + len(self.detached_gramplets) == 0:
            return # something is the matter
        filename = self.configfile
        try:
            fp = open(filename, "w")
        except IOError:
            print "Failed writing '%s'; gramplets not saved" % filename
            return
        fp.write(";; Gramps gramplets file" + NL)
        fp.write((";; Automatically created at %s" %
                                 time.strftime("%Y/%m/%d %H:%M:%S")) + NL + NL)
        fp.write("[Gramplet View Options]" + NL)
        fp.write(("column_count=%d" + NL) % self.column_count)
        fp.write(("pane_position=%d" + NL) % self.pane_position)
        fp.write(("pane_orientation=%s" + NL) % self.pane_orientation)
        fp.write(NL) 
        # showing gramplets:
        for col in range(self.column_count):
            row = 0
            for gframe in self.columns[col]:
                gramplet = self.frame_map[str(gframe)]
                opts = get_gramplet_options_by_name(gramplet.gname)
                if opts is not None:
                    base_opts = opts.copy()
                    for key in base_opts:
                        if key in gramplet.__dict__:
                            base_opts[key] = gramplet.__dict__[key]
                    fp.write(("[%s]" + NL) % gramplet.title)
                    for key in base_opts:
                        if key == "content": continue
                        elif key == "title": continue
                        elif key == "column": continue
                        elif key == "row": continue
                        elif key == "version": continue # code, don't save
                        elif key == "gramps": continue # code, don't save
                        elif key == "data":
                            if not isinstance(base_opts["data"], (list, tuple)):
                                fp.write(("data[0]=%s" + NL) %
                                                              base_opts["data"])
                            else:
                                cnt = 0
                                for item in base_opts["data"]:
                                    fp.write(("data[%d]=%s" + NL) % (cnt, item))
                                    cnt += 1
                        else:
                            fp.write(("%s=%s" + NL)% (key, base_opts[key]))
                    fp.write(("column=%d" + NL) % col)
                    fp.write(("row=%d" + NL) % row)
                    fp.write(NL)
                row += 1
        for gramplet in self.detached_gramplets:
            opts = get_gramplet_options_by_name(gramplet.gname)
            if opts is not None:
                base_opts = opts.copy()
                for key in base_opts:
                    if key in gramplet.__dict__:
                        base_opts[key] = gramplet.__dict__[key]
                fp.write(("[%s]" + NL) % gramplet.title)
                for key in base_opts:
                    if key == "content": continue
                    elif key == "title": continue
                    elif key == "data":
                        if not isinstance(base_opts["data"], (list, tuple)):
                            fp.write(("data[0]=%s" + NL) % base_opts["data"])
                        else:
                            cnt = 0
                            for item in base_opts["data"]:
                                fp.write(("data[%d]=%s" + NL) % (cnt, item))
                                cnt += 1
                    else:
                        fp.write(("%s=%s" + NL)% (key, base_opts[key]))
                fp.write(NL)
        fp.close()

    def drop_widget(self, source, context, x, y, timedata):
        """
        This is the destination method for handling drag and drop
        of a gramplet onto the main scrolled window.
        """
        button = context.get_source_widget()
        hbox = button.get_parent()
        mframe = hbox.get_parent()
        mainframe = mframe.get_parent() # actually a vbox
        rect = source.get_allocation()
        sx, sy = rect.width, rect.height
        # first, find column:
        col = 0
        for i in range(len(self.columns)):
            if x < (sx/len(self.columns) * (i + 1)): 
                col = i
                break
        fromcol = mainframe.get_parent()
        if fromcol:
            fromcol.remove(mainframe)
        # now find where to insert in column:
        stack = []
        current_row = 0
        for gframe in self.columns[col]:
            gramplet = self.frame_map[str(gframe)]
            gramplet.row = current_row
            current_row += 1
            rect = gframe.get_allocation()
            if y < (rect.y + 15): # starts at 0, this allows insert before
                self.columns[col].remove(gframe)
                stack.append(gframe)
        maingramplet = self.frame_map.get(str(mainframe), None)
        maingramplet.column = col
        maingramplet.row = current_row
        current_row += 1
        expand = maingramplet.gstate == "maximized" and maingramplet.expand
        self.columns[col].pack_start(mainframe, expand=expand)
        for gframe in stack:
            gramplet = self.frame_map[str(gframe)]
            gramplet.row = current_row
            current_row += 1
            expand = gramplet.gstate == "maximized" and gramplet.expand
            self.columns[col].pack_start(gframe, expand=expand)
        return True

    def set_columns(self, num):
        if num < 1:
            num = 1
        # clear the gramplets:
        self.clear_gramplets()
        # clear the columns:
        for column in self.columns:
            frame = column.get_parent()
            frame.remove(column)
            del column
        # create the new ones:
        self.column_count = num
        self.columns = []
        for i in range(self.column_count):
            self.columns.append(gtk.VBox())
            self.columns[-1].show()
            self.hbox.pack_start(self.columns[-1], expand=True)
        # place the gramplets back in the new columns
        self.place_gramplets(recolumn=True)
        self.show()

    def restore_gramplet(self, obj):
        name = obj.get_child().get_label()
        ############### First kind: from current session
        for gramplet in self.closed_gramplets:
            if gramplet.title == name:
                #gramplet.gstate = "maximized"
                self.closed_gramplets.remove(gramplet)
                if self._popup_xy is not None:
                    self.drop_widget(self, gramplet, 
                                     self._popup_xy[0], self._popup_xy[1], 0)
                else:
                    self.drop_widget(self, gramplet, 0, 0, 0)
                gramplet.set_state("maximized")
                return
        ################ Second kind: from options
        for opts in self.closed_opts:
            if opts["title"] == name:
                self.closed_opts.remove(opts)
                g = make_requested_gramplet(GridGramplet, self, opts,
                                            self.dbstate, self.uistate)
                if g:
                    self.gramplet_map[opts["title"]] = g
                    self.frame_map[str(g.mainframe)] = g
                else:
                    print "Can't make gramplet of type '%s'." % name
        if g:
            gramplet = g
            gramplet.gstate = "maximized"
            if gramplet.column >= 0 and gramplet.column < len(self.columns):
                pos = gramplet.column
            else:
                pos = 0
            self.columns[pos].pack_start(gramplet.mainframe,
                                         expand=gramplet.expand)
            # set height on gramplet.scrolledwindow here:
            gramplet.scrolledwindow.set_size_request(-1, gramplet.height)
            ## now drop it in right place
            if self._popup_xy is not None:
                self.drop_widget(self, gramplet, 
                                 self._popup_xy[0], self._popup_xy[1], 0)
            else:
                self.drop_widget(self, gramplet, 0, 0, 0)

    def add_gramplet(self, obj):
        tname = obj.get_child().get_label()
        all_opts = get_gramplet_options_by_tname(tname)
        name = all_opts["name"]
        if all_opts is None:
            print "Unknown gramplet type: '%s'; bad gramplets.ini file?" % name
            return
        if "title" not in all_opts:
            all_opts["title"] = "Untitled Gramplet"
        # uniqify titles:
        unique = all_opts["title"]
        cnt = 1
        while unique in self.gramplet_map:
            unique = all_opts["title"] + ("-%d" % cnt)
            cnt += 1
        all_opts["title"] = unique
        if all_opts["title"] not in self.gramplet_map:
            g = make_requested_gramplet(GridGramplet, self, all_opts, 
                                        self.dbstate, self.uistate)
        if g:
            self.gramplet_map[all_opts["title"]] = g
            self.frame_map[str(g.mainframe)] = g
            gramplet = g
            if gramplet.column >= 0 and gramplet.column < len(self.columns):
                pos = gramplet.column
            else:
                pos = 0
            self.columns[pos].pack_start(gramplet.mainframe,
                                         expand=gramplet.expand)
            # set height on gramplet.scrolledwindow here:
            gramplet.scrolledwindow.set_size_request(-1, gramplet.height)
            ## now drop it in right place
            if self._popup_xy is not None:
                self.drop_widget(self, gramplet, 
                                 self._popup_xy[0], self._popup_xy[1], 0)
            else:
                self.drop_widget(self, gramplet, 0, 0, 0)
            if gramplet.pui:
                gramplet.pui.active = True
                gramplet.pui.update()
        else:
            print "Can't make gramplet of type '%s'." % name

    def _button_press(self, obj, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            self._popup_xy = (event.x, event.y)
            uiman = self.uistate.uimanager
            ag_menu = uiman.get_widget('/GrampletPopup/AddGramplet')
            if ag_menu:
                qr_menu = ag_menu.get_submenu()
                qr_menu = gtk.Menu()
                names = [GET_AVAILABLE_GRAMPLETS(key)["tname"] for key 
                         in AVAILABLE_GRAMPLETS()]
                names.sort()
                for name in names:
                    add_menuitem(qr_menu, name, None, self.add_gramplet)
                ag_menu.set_submenu(qr_menu)
            rg_menu = uiman.get_widget('/GrampletPopup/RestoreGramplet')
            if rg_menu:
                qr_menu = rg_menu.get_submenu()
                if qr_menu is not None:
                    rg_menu.remove_submenu()
                names = [gramplet.title for gramplet in self.closed_gramplets]
                names.extend(opts["title"] for opts in self.closed_opts)
                names.sort()
                if len(names) > 0:
                    qr_menu = gtk.Menu()
                    for name in names:
                        add_menuitem(qr_menu, name, None, self.restore_gramplet)
                    rg_menu.set_submenu(qr_menu)
            menu = uiman.get_widget('/GrampletPopup')
            if menu:
                menu.popup(None, None, None, 1, event.time)
                return True
        return False

    def set_inactive(self):
        for title in self.gramplet_map:
            if self.gramplet_map[title].pui:
                if self.gramplet_map[title].gstate != "detached":
                    self.gramplet_map[title].pui.active = False

    def set_active(self):
        for title in self.gramplet_map:
            if self.gramplet_map[title].pui:
                self.gramplet_map[title].pui.active = True
                if self.gramplet_map[title].pui.dirty:
                    if self.gramplet_map[title].gstate == "maximized":
                        self.gramplet_map[title].pui.update()

    def on_delete(self):
        gramplets = (g for g in self.gramplet_map.itervalues() 
                        if g is not None)
        for gramplet in gramplets:
            # this is the only place where the gui runs user code directly
            if gramplet.pui:
                gramplet.pui.on_save()
        self.save()

    def can_configure(self):
        """
        See :class:`~gui.views.pageview.PageView 
        :return: bool
        """
        return True

    def _get_configure_page_funcs(self):
        """
        Return a list of functions that create gtk elements to use in the 
        notebook pages of the Configure dialog
        
        :return: list of functions
        """
        def generate_pages():
            return [self.config_panel] + \
                [self.build_panel(gramplet) for gramplet in 
                 sorted(self.gramplet_map.values(), key=lambda g: g.title) 
                 if gramplet.gstate != "closed"]
        return generate_pages
 
    def get_columns(self):
        return self.column_count

    def config_panel(self, configdialog):
        """
        Function that builds the widget in the configuration dialog
        """
        table = gtk.Table(3, 2)
        table.set_border_width(12)
        table.set_col_spacings(6)
        table.set_row_spacings(6)

        self._config.register('Gramplet View Options.column_count',
                              int,
                              self.get_columns, # pane
                              self.set_columns) # pane

        configdialog.add_pos_int_entry(table, 
                 _('Number of Columns'), 
                 0, 
                'Gramplet View Options.column_count',
                self._config.set,
                config=self._config)
        return _('Gramplet Layout'), table
 
    def build_panel(self, gramplet):
        self._config.register("%s.title" % gramplet.title, 
                              str, gramplet.get_title, gramplet.set_title)
        self._config.register("%s.height" % gramplet.title, 
                              int, gramplet.get_height, gramplet.set_height)
        self._config.register("%s.detached_height" % gramplet.title, 
                              int, gramplet.get_detached_height,
                              gramplet.set_detached_height)
        self._config.register("%s.detached_width" % gramplet.title, 
                              int, gramplet.get_detached_width,
                              gramplet.set_detached_width)
        self._config.register("%s.expand" % gramplet.title, 
                              bool, gramplet.get_expand, gramplet.set_expand)
        def gramplet_panel(configdialog):
            configdialog.window.set_size_request(500, -1)
            table = gtk.Table(3, 2)
            table.set_border_width(12)
            table.set_col_spacings(6)
            table.set_row_spacings(6)
            # Title:
            configdialog.add_entry(table, 
                _('Title'), 
                0, 
                "%s.title" % gramplet.title,
                self._config.set,
                config=self._config)
            # Expand to max height
            configdialog.add_checkbox(table, 
                _("Use maximum height available"), 
                1, 
                "%s.expand" % gramplet.title, 
                config=self._config)
            # Height
            configdialog.add_pos_int_entry(table, 
                _('Height if not maximized'), 
                2, 
                "%s.height" % gramplet.title,
                self._config.set,
                config=self._config)
            # Detached height
            configdialog.add_pos_int_entry(table, 
                _('Detached width'), 
                3, 
                "%s.detached_width" % gramplet.title,
                self._config.set,
                config=self._config)
            # Detached width
            configdialog.add_pos_int_entry(table, 
                _('Detached height'), 
                4, 
                "%s.detached_height" % gramplet.title,
                self._config.set,
                config=self._config)
            # Options:
            options = gramplet.make_gui_options()
            if options:
                table.attach(options, 1, 4, 5, 6, yoptions=0)
            return gramplet.title, table
        return gramplet_panel

class Configuration(object):
    """
    A config wrapper to redirect set/get to GrampletPane.
    """
    def __init__(self, pane):
        self.pane = pane
        self.data = {}

    def get(self, key):
        vtype, getter, setter = self.data[key]
        return getter()

    def set(self, widget, key):
        """
        Hooked to signal, it is widget, key.
        Hooked to config, it is key, widget
        """
        if key not in self.data:
            widget, key = key, widget
        vtype, getter, setter = self.data[key]
        if type(widget) == vtype:
            setter(widget)
        else:
            try:
                value = vtype(widget.get_text())
            except:
                return
            setter(value)

    def register(self, key, vtype, getter, setter):
        """
        register a key with type, getter, and setter methods.
        """
        self.data[key] = (vtype, getter, setter)
