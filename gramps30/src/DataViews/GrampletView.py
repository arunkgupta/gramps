#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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
# gtk modules
#
#-------------------------------------------------------------------------
import gtk
from gtk import glade
import gobject
import pango

import traceback
import time
import types
import os
from gettext import gettext as _

import Errors
import const
import PageView
import ManagedWindow
import ConfigParser
import Utils
from QuickReports import run_quick_report_by_name
import GrampsDisplay

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = 'Gramps_3.0_Wiki_Manual_-_Gramplets'

#-------------------------------------------------------------------------
#
# Globals
#
#-------------------------------------------------------------------------
AVAILABLE_GRAMPLETS = {}
GRAMPLET_FILENAME = os.path.join(const.HOME_DIR,"gramplets.ini")
NL = "\n" 

debug = False

def register_gramplet(data_dict):
    global AVAILABLE_GRAMPLETS
    base_opts = {"name":"Unnamed Gramplet",
                 "tname": _("Unnamed Gramplet"),
                 "state":"maximized",
                 "column": -1, "row": -1,
                 "data": []}
    base_opts.update(data_dict)
    AVAILABLE_GRAMPLETS[base_opts["name"]] = base_opts

def register(**data):
    if "type" in data:
        if data["type"].lower() == "gramplet":
            register_gramplet(data)
        else:
            print ("Unknown plugin type: '%s'" % data["type"])
    else:
        print ("Plugin did not define type.")

def get_gramplet_opts(name, opts):
    if name in AVAILABLE_GRAMPLETS:
        data = AVAILABLE_GRAMPLETS[name]
        my_data = data.copy()
        my_data.update(opts)
        return my_data
    else:
        print ("Unknown gramplet name: '%s'" % name)
        return {}

def get_gramplet_options_by_name(name):
    if debug: print "name:", name
    if name in AVAILABLE_GRAMPLETS:
        return AVAILABLE_GRAMPLETS[name].copy()
    else:
        print ("Unknown gramplet name: '%s'" % name)
        return None

def get_gramplet_options_by_tname(name):
    if debug: print "name:", name
    for key in AVAILABLE_GRAMPLETS:
        if AVAILABLE_GRAMPLETS[key]["tname"] == name:
            return AVAILABLE_GRAMPLETS[key].copy()
    print ("Unknown gramplet name: '%s'" % name)
    return None

def make_requested_gramplet(viewpage, name, opts, dbstate, uistate):
    if name in AVAILABLE_GRAMPLETS:
        gui = GuiGramplet(viewpage, dbstate, uistate, **opts)
        if opts.get("content", None):
            opts["content"](gui)
        # now that we have user code, set the tooltips
        msg = None
        if gui.pui:
            msg = gui.pui.tooltip
        if msg == None:
            msg = _("Drag Properties Button to move and click it for setup")
        if msg:
            gui.tooltips = gtk.Tooltips()
            gui.tooltips.set_tip(gui.scrolledwindow, msg)
            gui.tooltips_text = msg
        gui.gvoptions.hide()
        return gui
    return None

class LinkTag(gtk.TextTag):
    lid = 0
    def __init__(self, buffer):
        LinkTag.lid += 1
        gtk.TextTag.__init__(self, str(LinkTag.lid))
        tag_table = buffer.get_tag_table()
        self.set_property('foreground', "blue")
        #self.set_property('underline', pango.UNDERLINE_SINGLE)
        tag_table.add(self)

class GrampletWindow(ManagedWindow.ManagedWindow):
    def __init__(self, gramplet):
        self.title = gramplet.title + " " + _("Gramplet")
        self.gramplet = gramplet
        ManagedWindow.ManagedWindow.__init__(self, gramplet.uistate, [], gramplet)
        self.set_window(gtk.Dialog("",gramplet.uistate.window,
                                   gtk.DIALOG_DESTROY_WITH_PARENT,
                                   (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)),
                        None, self.title)
        self.window.set_size_request(gramplet.detached_width,
                                     gramplet.detached_height)
        self.window.add_button(gtk.STOCK_HELP, gtk.RESPONSE_HELP)
        # add gramplet:
        self.gramplet.mainframe.reparent(self.window.vbox)
        self.window.connect('response', self.handle_response)
        self.window.show()

    def handle_response(self, object, response):
        if response in [gtk.RESPONSE_CLOSE, gtk.STOCK_CLOSE]:
            self.close()
        elif response == gtk.RESPONSE_HELP:
            # translated name:
            GrampsDisplay.help('gramplet', WIKI_HELP_PAGE, 
                               self.gramplet.tname.replace(" ", "_"))
        
    def build_menu_names(self, obj):
        return (self.title, 'Gramplet')

    def get_title(self):
        return self.title

    def close(self, *args):
        """
        Closes the detached GrampletWindow.
        """
        self.gramplet.gvoptions.hide()
        self.gramplet.viewpage.detached_gramplets.remove(self.gramplet)
        self.gramplet.state = "maximized"
        parent = self.gramplet.viewpage.get_column_frame(self.gramplet.column)
        self.gramplet.mainframe.reparent(parent)
        expand,fill,padding,pack =  parent.query_child_packing(self.gramplet.mainframe)
        parent.set_child_packing(self.gramplet.mainframe,
                                 self.gramplet.expand,
                                 fill,
                                 padding,
                                 pack)
        self.gramplet.gvclose.show()
        self.gramplet.gvstate.show()
        self.gramplet.gvproperties.show()
        ManagedWindow.ManagedWindow.close(self, *args)

#------------------------------------------------------------------------

class Gramplet(object):
    def __init__(self, gui):
        self._idle_id = 0
        self._generator = None
        self._need_to_update = False
        self._tags = []
        self.option_dict = {}
        self.tooltip = None
        self.link_cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
        self.standard_cursor = gtk.gdk.Cursor(gtk.gdk.XTERM)
        # links to each other:
        self.gui = gui   # plugin gramplet has link to gui
        gui.pui = self   # gui has link to plugin ui
        self.dbstate = gui.dbstate
        self.init()
        self.on_load()
        self.dbstate.connect('database-changed', self._db_changed)
        self.dbstate.connect('active-changed', self.active_changed)
        self.gui.textview.connect('button-press-event', 
                                  self.on_button_press) 
        self.gui.textview.connect('motion-notify-event', 
                                  self.on_motion)
        # Add options to section on detached view
        # FIXME: too many options will expand section: need scrollable area
        for item in self.option_dict:
            self.gui.option_vbox.add(gtk.Label(item))
        if self.dbstate.active: # already changed
            self._db_changed(self.dbstate.db)
            self.active_changed(self.dbstate.active.handle)

    def init(self): # once, constructor
        pass

    def main(self): # return false finishes
        """
        Generator which will be run in the background.
        """
        if debug: print "%s dummy" % self.gui.title
        yield False

    def on_load(self):
        """
        Gramplets should override this to take care of loading previously
        their special data.
        """
        pass

    def on_save(self):
        """
        Gramplets should override this to take care of saving their
        special data.
        """
        if debug: print ("on_save: '%s'" % self.gui.title)
        return

    def active_changed(self, handle):
        pass

    def db_changed(self):
        if debug: print "%s is connecting" % self.gui.title
        pass

    def link(self, text, link_type, data, size=None, tooltip=None):
        buffer = self.gui.buffer
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

    # Shortcuts to the gui functionality:

    def get_text(self):
        return self.gui.get_text()
        
    def insert_text(self, text):
        self.gui.insert_text(text)

    def render_text(self, text):
        self.gui.render_text(text)

    def clear_text(self):
        self.gui.clear_text()
        
    def set_text(self, text, scroll_to='start'):
        self.gui.set_text(text, scroll_to)

    def append_text(self, text, scroll_to="end"):
        self.gui.append_text(text, scroll_to)

    def render_text(self, text):
        self.gui.render_text(text)

    def set_use_markup(self, value):
        self.gui.set_use_markup(value)

    def no_wrap(self):
        """
        The view in gramplet should not wrap.
        """
        self.gui.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, 
                                           gtk.POLICY_AUTOMATIC)
        self.gui.textview.set_wrap_mode(gtk.WRAP_NONE)

    # Other functions of the gramplet:

    def load_data_to_text(self, pos=0):
        if len(self.gui.data) >= pos + 1:
            text = self.gui.data[pos]
            text = text.replace("\\n", chr(10))
            self.set_text(text, 'end')

    def save_text_to_data(self):
        text = self.get_text()
        text = text.replace(chr(10), "\\n")
        self.gui.data.append(text)

    def update(self, *args):
        if self._idle_id != 0:
            if debug: print "%s interrupt!" % self.gui.title
            self.interrupt()
        if debug: print "%s creating generator" % self.gui.title
        self._generator = self.main()
        if debug: print "%s adding to gobject" % self.gui.title
        self._idle_id = gobject.idle_add(self._updater, 
                                         priority=gobject.PRIORITY_LOW - 10)

    def interrupt(self):
        """
        Force the generator to stop running.
        """
        if self._idle_id == 0:
            if debug: print "%s removing from gobject" % self.gui.title
            gobject.source_remove(self._idle_id)
            self._idle_id = 0

    def _db_changed(self, db):
        if debug: print "%s is _connecting" % self.gui.title
        self.dbstate.db = db
        self.gui.dbstate.db = db
        self.db_changed()
        self.update()

    def _updater(self):
        """
        Runs the generator.
        """
        if debug: print "%s _updater" % self.gui.title
        if type(self._generator) != types.GeneratorType:
            self._idle_id = 0
            return False
        try:
            retval = self._generator.next()
            if not retval:
                self._idle_id = 0
            return retval
        except StopIteration:
            self._idle_id = 0
            return False
        except Exception, e:
            print "Gramplet gave an error"
            traceback.print_exc()
            print "Continuing after gramplet error..."
            self._idle_id = 0
            return False

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
        if self.gui.tooltips:
            if ttip:
                self.gui.tooltips.set_tip(self.gui.scrolledwindow, 
                                          ttip)
            else:
                self.gui.tooltips.set_tip(self.gui.scrolledwindow, 
                                          self.gui.tooltips_text)
        return False # handle event further, if necessary

    def on_button_press(self, view, event):
        buffer_location = view.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT, 
                                                       int(event.x), 
                                                       int(event.y))
        iter = view.get_iter_at_location(*buffer_location)
        for (tag, link_type, handle, tooltip) in self._tags:
            if iter.has_tag(tag):
                if link_type == 'Person':
                    person = self.dbstate.db.get_person_from_handle(handle)
                    if person != None:
                        if event.button == 1: # left mouse
                            if event.type == gtk.gdk._2BUTTON_PRESS: # double
                                try:
                                    from Editors import EditPerson
                                    EditPerson(self.gui.dbstate, 
                                               self.gui.uistate, 
                                               [], person)
                                    return True # handled event
                                except Errors.WindowActiveError:
                                    pass
                            elif event.type == gtk.gdk.BUTTON_PRESS: # single click
                                self.gui.dbstate.change_active_person(person)
                                return True # handled event
                        elif event.button == 3: # right mouse
                            #FIXME: add a popup menu with options
                            try:
                                from Editors import EditPerson
                                EditPerson(self.gui.dbstate, 
                                           self.gui.uistate, 
                                           [], person)
                                return True # handled event
                            except Errors.WindowActiveError:
                                pass
                elif link_type == 'Surname':
                    if event.button == 1: # left mouse
                        if event.type == gtk.gdk._2BUTTON_PRESS: # double
                            run_quick_report_by_name(self.gui.dbstate, 
                                                     self.gui.uistate, 
                                                     'samesurnames', 
                                                     handle)
                    return True
                elif link_type == 'Filter':
                    if event.button == 1: # left mouse
                        if event.type == gtk.gdk._2BUTTON_PRESS: # double
                            run_quick_report_by_name(self.gui.dbstate, 
                                                     self.gui.uistate, 
                                                     'filterbyname', 
                                                     handle)
                    return True
                elif link_type == 'PersonList':
                    if event.button == 1: # left mouse
                        if event.type == gtk.gdk._2BUTTON_PRESS: # double
                            run_quick_report_by_name(self.gui.dbstate, 
                                                     self.gui.uistate, 
                                                     'filterbyname', 
                                                     'list of people',
                                                     handles=handle)
                    return True
        return False # did not handle event

    def set_options(self, option_dict):
        self.option_dict = option_dict
        
def logical_true(value):
    return value in ["True", True, 1, "1"]

class GuiGramplet:
    """
    Class that handles the plugin interfaces for the GrampletView.
    """
    TARGET_TYPE_FRAME = 80
    LOCAL_DRAG_TYPE   = 'GRAMPLET'
    LOCAL_DRAG_TARGET = (LOCAL_DRAG_TYPE, 0, TARGET_TYPE_FRAME)
    def __init__(self, viewpage, dbstate, uistate, title, **kwargs):
        self.viewpage = viewpage
        self.dbstate = dbstate
        self.uistate = uistate
        self.title = title
        ########## Set defaults
        self.name = kwargs.get("name", "Unnamed Gramplet")
        self.tname = kwargs.get("tname", "Unnamed Gramplet")
        self.expand = logical_true(kwargs.get("expand", False))
        self.height = int(kwargs.get("height", 200))
        self.column = int(kwargs.get("column", -1))
        self.detached_height = int(kwargs.get("detached_height", 300))
        self.detached_width = int(kwargs.get("detached_width", 400))
        self.row = int(kwargs.get("row", -1))
        self.state = kwargs.get("state", "maximized")
        self.data = kwargs.get("data", [])
        ##########
        self.use_markup = False
        self.pui = None # user code
        self.tooltips = None
        self.tooltips_text = None
        self.xml = glade.XML(const.GLADE_FILE, 'gvgramplet', "gramps")
        self.mainframe = self.xml.get_widget('gvgramplet')
        self.gvoptions = self.xml.get_widget('gvoptions')
        self.option_vbox = self.xml.get_widget('option_vbox')
        self.textview = self.xml.get_widget('gvtextview')
        self.buffer = self.textview.get_buffer()
        self.scrolledwindow = self.xml.get_widget('gvscrolledwindow')
        self.titlelabel = self.xml.get_widget('gvtitle')
        self.titlelabel.set_text("<b><i>%s</i></b>" % self.title)
        self.titlelabel.set_use_markup(True)
        self.gvclose = self.xml.get_widget('gvclose')
        self.gvclose.connect('clicked', self.close)
        self.gvstate = self.xml.get_widget('gvstate')
        self.gvstate.connect('clicked', self.change_state)
        self.gvproperties = self.xml.get_widget('gvproperties')
        self.gvproperties.connect('clicked', self.set_properties)
        self.xml.get_widget('gvcloseimage').set_from_stock(gtk.STOCK_CLOSE,
                                                           gtk.ICON_SIZE_MENU)
        self.xml.get_widget('gvstateimage').set_from_stock(gtk.STOCK_REMOVE,
                                                           gtk.ICON_SIZE_MENU)
        self.xml.get_widget('gvpropertiesimage').set_from_stock(gtk.STOCK_PROPERTIES,
                                                                gtk.ICON_SIZE_MENU)

        # source:
        drag = self.gvproperties
        drag.drag_source_set(gtk.gdk.BUTTON1_MASK,
                             [GuiGramplet.LOCAL_DRAG_TARGET],
                             gtk.gdk.ACTION_COPY)

    def close(self, *obj):
        if self.state == "windowed":
            return
        self.state = "closed"
        self.viewpage.closed_gramplets.append(self)
        self.mainframe.get_parent().remove(self.mainframe)

    def detach(self):
        # hide buttons:
        self.set_state("maximized")
        self.gvclose.hide()
        self.gvstate.hide()
        self.gvproperties.hide()
        if self.pui and len(self.pui.option_dict) > 0:
            self.gvoptions.show()
        self.viewpage.detached_gramplets.append(self)
        # make a window, and attach it there
        self.detached_window = GrampletWindow(self)
        self.state = "windowed"

    def set_state(self, state):
        self.state = state
        if state == "minimized":
            self.scrolledwindow.hide()
            self.xml.get_widget('gvstateimage').set_from_stock(gtk.STOCK_ADD,
                                                               gtk.ICON_SIZE_MENU)
            column = self.mainframe.get_parent() # column
            expand,fill,padding,pack =  column.query_child_packing(self.mainframe)
            column.set_child_packing(self.mainframe,False,fill,padding,pack)

        else:
            self.scrolledwindow.show()
            self.xml.get_widget('gvstateimage').set_from_stock(gtk.STOCK_REMOVE,
                                                               gtk.ICON_SIZE_MENU)
            column = self.mainframe.get_parent() # column
            expand,fill,padding,pack =  column.query_child_packing(self.mainframe)
            column.set_child_packing(self.mainframe,
                                     self.expand,
                                     fill,
                                     padding,
                                     pack)

    def change_state(self, obj):
        if self.state == "windowed":
            pass # don't change if windowed
        else:
            if self.state == "maximized":
                self.set_state("minimized")
            else:
                self.set_state("maximized")
                
    def set_properties(self, obj):
        if self.state == "windowed":
            pass
        else:
            self.detach()
        return
        # FIXME: add control for expand AND detach
        self.expand = not self.expand
        if self.state == "maximized":
            column = self.mainframe.get_parent() # column
            expand,fill,padding,pack =  column.query_child_packing(self.mainframe)
            column.set_child_packing(self.mainframe,self.expand,fill,padding,pack)

    def append_text(self, text, scroll_to="end"):
        enditer = self.buffer.get_end_iter()
        start = self.buffer.create_mark(None, enditer, True)
        self.buffer.insert(enditer, text)
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

    def get_text(self):
        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        return self.buffer.get_text(start, end)

    def insert_text(self, text):
        self.buffer.insert_at_cursor(text)

    def render_text(self, text):
        markup_pos = {"B": [], "I": [], "U": []}
        retval = ""
        i = 0
        r = 0
        while i < len(text):
            if text[i] == "<":
                if text[i+1] == "/" and text[i+3] == ">":
                    markup = text[i+2].upper()
                    markup_pos[markup][-1].append(r)
                    i += 4
                elif text[i+2] == ">":
                    markup = text[i+1].upper()
                    markup_pos[markup].append([r])
                    i += 3
                else:
                    retval += text[i]
                    r += 1
                    i += 1
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
        offset = len(self.get_text())
        self.append_text(retval)
        for (a,b) in markup_pos["B"]:
            start = self.buffer.get_iter_at_offset(a + offset)
            stop = self.buffer.get_iter_at_offset(b + offset)
            self.buffer.apply_tag_by_name("bold", start, stop)
        for (a,b) in markup_pos["I"]:
            start = self.buffer.get_iter_at_offset(a + offset)
            stop = self.buffer.get_iter_at_offset(b + offset)
            self.buffer.apply_tag_by_name("italic", start, stop)
        for (a,b) in markup_pos["U"]:
            start = self.buffer.get_iter_at_offset(a + offset)
            stop = self.buffer.get_iter_at_offset(b + offset)
            self.buffer.apply_tag_by_name("underline", start, stop)

    def set_use_markup(self, value):
        if self.use_markup == value: return
        self.use_markup = value
        if value:
            self.buffer.create_tag("bold",weight=pango.WEIGHT_HEAVY)
            self.buffer.create_tag("italic",style=pango.STYLE_ITALIC)
            self.buffer.create_tag("underline",underline=pango.UNDERLINE_SINGLE)
        else:
            tag_table = self.buffer.get_tag_table()
            tag_table.foreach(lambda tag, data: tag_table.remove(tag))

    def set_text(self, text, scroll_to='start'):
        self.buffer.set_text('')
        self.append_text(text, scroll_to)

    def get_source_widget(self):
        """
        Hack to allow us to send this object to the drop_widget
        method as a context.
        """
        return self.gvproperties

class MyScrolledWindow(gtk.ScrolledWindow):
    def show_all(self):
        # first show them all:
        gtk.ScrolledWindow.show_all(self)
        # Hack to get around show_all that shows hidden items
        # do once, the first time showing
        if self.viewpage:
            gramplets = [g for g in self.viewpage.gramplet_map.values() if g != None]
            self.viewpage = None
            for gramplet in gramplets:
                gramplet.gvoptions.hide()
                if gramplet.state == "minimized":
                    gramplet.set_state("minimized")

class GrampletView(PageView.PersonNavView): 
    """
    GrampletView interface
    """

    def __init__(self, dbstate, uistate):
        """
        Create a GrampletView, with the current dbstate and uistate
        """
        PageView.PersonNavView.__init__(self, _('Gramplets'), dbstate, uistate)
        self._popup_xy = None

    def build_widget(self):
        """
        Builds the container widget for the interface. Must be overridden by the
        the base class. Returns a gtk container widget.
        """
        # load the user's gramplets and set columns, etc
        user_gramplets = self.load_gramplets()
        # build the GUI:
        frame = MyScrolledWindow()
        msg = _("Right click to add gramplets")
        self.tooltips = gtk.Tooltips()
        self.tooltips.set_tip(frame, msg)
        frame.viewpage = self
        frame.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.hbox = gtk.HBox(homogeneous=True)
        # Set up drag and drop
        frame.drag_dest_set(gtk.DEST_DEFAULT_MOTION |
                            gtk.DEST_DEFAULT_HIGHLIGHT |
                            gtk.DEST_DEFAULT_DROP,
                            [('GRAMPLET', 0, 80)],
                            gtk.gdk.ACTION_COPY)
        frame.connect('drag_drop', self.drop_widget)
        frame.connect('button-press-event', self._button_press)

        frame.add_with_viewport(self.hbox)
        # Create the columns:
        self.columns = []
        for i in range(self.column_count):
            self.columns.append(gtk.VBox())
            self.hbox.pack_start(self.columns[-1],expand=True)
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
            g = make_requested_gramplet(self, name, all_opts, 
                                      self.dbstate, self.uistate)
            if g:
                self.gramplet_map[all_opts["title"]] = g
                self.frame_map[str(g.mainframe)] = g
            else:
                print "Can't make gramplet of type '%s'." % name
        self.place_gramplets()
        return frame

    def get_column_frame(self, column_num):
        if column_num < len(self.columns):
            return self.columns[column_num]
        else:
            return self.columns[-1] # it was too big, so select largest

    def clear_gramplets(self):
        """
        Detach all of the mainframe gramplets from the columns.
        """
        gramplets = [g for g in self.gramplet_map.values() if g != None]
        for gramplet in gramplets:
            if (gramplet.state == "windowed" or gramplet.state == "closed"):
                continue
            column = gramplet.mainframe.get_parent()
            if column:
                column.remove(gramplet.mainframe)

    def place_gramplets(self, recolumn=False):
        """
        Place the gramplet mainframes in the columns.
        """
        gramplets = [g for g in self.gramplet_map.values() if g != None]
        # put the gramplets where they go:
        # sort by row
        gramplets.sort(lambda a, b: cmp(a.row, b.row))
        cnt = 0
        for gramplet in gramplets:
            # see if the user wants this in a particular location:
            # and if there are that many columns
            if gramplet.column >= 0 and gramplet.column < self.column_count:
                pos = gramplet.column
            else:
                # else, spread them out:
                pos = cnt % self.column_count
            gramplet.column = pos
            if recolumn and (gramplet.state == "windowed" or gramplet.state == "closed"):
                continue
            self.columns[pos].pack_start(gramplet.mainframe, expand=gramplet.expand)
            # set height on gramplet.scrolledwindow here:
            gramplet.scrolledwindow.set_size_request(-1, gramplet.height)
            # Can't minimize here, because GRAMPS calls show_all later:
            #if gramplet.state == "minimized": # starts max, change to min it
            #    gramplet.set_state("minimized") # minimize it
            # set minimized is called in page subclass hack (above)
            if gramplet.state == "windowed":
                gramplet.detach() 
            elif gramplet.state == "closed":
                gramplet.close() 
            cnt += 1

    def load_gramplets(self):
        self.column_count = 2 # default for new user
        retval = []
        filename = GRAMPLET_FILENAME
        if filename and os.path.exists(filename):
            cp = ConfigParser.ConfigParser()
            cp.read(filename)
            for sec in cp.sections():
                if sec == "Gramplet View Options":
                    if "column_count" in cp.options(sec):
                        self.column_count = int(cp.get(sec, "column_count"))
                else:
                    data = {"title": sec}
                    for opt in cp.options(sec):
                        if opt.startswith("data["):
                            temp = data.get("data", [])
                            temp.append(cp.get(sec, opt).strip())
                            data["data"] = temp
                        else:
                            data[opt] = cp.get(sec, opt).strip()
                    if "name" not in data:
                        data["name"] = "Unnamed Gramplet"
                        data["tname"]= _("Unnamed Gramplet")
                    retval.append((data["name"], data)) # name, opts
        else:
            # give defaults as currently known
            for name in ["Top Surnames Gramplet", "Welcome Gramplet"]:
                if name in AVAILABLE_GRAMPLETS:
                    retval.append((name, AVAILABLE_GRAMPLETS[name]))
        return retval

    def save(self, *args):
        if debug: print "saving"
        if len(self.frame_map.keys() + 
               self.detached_gramplets) == 0:
            return # something is the matter
        filename = GRAMPLET_FILENAME
        try:
            fp = open(filename, "w")
        except:
            print "Failed writing '%s'; gramplets not saved" % filename
            return
        fp.write(";; Gramps gramplets file" + NL)
        fp.write((";; Automatically created at %s" % time.strftime("%Y/%m/%d %H:%M:%S")) + NL + NL)
        fp.write("[Gramplet View Options]" + NL)
        fp.write(("column_count=%d" + NL + NL) % self.column_count)
        # showing gramplets:
        for col in range(self.column_count):
            row = 0
            for gframe in self.columns[col]:
                gramplet = self.frame_map[str(gframe)]
                opts = get_gramplet_options_by_name(gramplet.name)
                if opts != None:
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
                        elif key == "data":
                            if type(base_opts["data"]) not in [list, tuple]:
                                fp.write(("data[0]=%s" + NL) % base_opts["data"])
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
            opts = get_gramplet_options_by_name(gramplet.name)
            if opts != None:
                base_opts = opts.copy()
                for key in base_opts:
                    if key in gramplet.__dict__:
                        base_opts[key] = gramplet.__dict__[key]
                fp.write(("[%s]" + NL) % gramplet.title)
                for key in base_opts:
                    if key == "content": continue
                    elif key == "title": continue
                    elif key == "data":
                        if type(base_opts["data"]) not in [list, tuple]:
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
        for gframe in self.columns[col]:
            rect = gframe.get_allocation()
            if y < (rect.y + 15): # starts at 0, this allows insert before
                self.columns[col].remove(gframe)
                stack.append(gframe)
        maingramplet = self.frame_map.get(str(mainframe), None)
        maingramplet.column = col
        if maingramplet.state == "maximized":
            expand = maingramplet.expand
        else:
            expand = False
        self.columns[col].pack_start(mainframe, expand=expand)
        for gframe in stack:
            gramplet = self.frame_map[str(gframe)]
            if gramplet.state == "maximized":
                expand = gramplet.expand
            else:
                expand = False
            self.columns[col].pack_start(gframe, expand=expand)
        return True

    def define_actions(self):
        """
        Defines the UIManager actions. Called by the ViewManager to set up the
        View. The user typically defines self.action_list and 
        self.action_toggle_list in this function. 
        """
        self.action = gtk.ActionGroup(self.title + "/Gramplets")
        self.action.add_actions([('AddGramplet',gtk.STOCK_ADD,_("_Add a gramplet")),
                                 ('RestoreGramplet',None,_("_Undelete gramplet")),
                                 ('Columns1',None,_("Set Columns to _1"),
                                  None,None,
                                  lambda obj:self.set_columns(1)),
                                 ('Columns2',None,_("Set Columns to _2"),
                                  None,None,
                                  lambda obj:self.set_columns(2)),
                                 ('Columns3',None,_("Set Columns to _3"),
                                  None,None,
                                  lambda obj:self.set_columns(3)),
                                 ])
        self._add_action_group(self.action)
        # Back, Forward, Home
        self.fwd_action = gtk.ActionGroup(self.title + '/Forward')
        self.fwd_action.add_actions([
            ('Forward', gtk.STOCK_GO_FORWARD, _("_Forward"), 
             "<ALT>Right", _("Go to the next person in the history"), 
             self.fwd_clicked)
            ])

        # add the Backward action group to handle the Forward button
        self.back_action = gtk.ActionGroup(self.title + '/Backward')
        self.back_action.add_actions([
            ('Back', gtk.STOCK_GO_BACK, _("_Back"), 
             "<ALT>Left", _("Go to the previous person in the history"), 
             self.back_clicked)
            ])
        self._add_action('HomePerson', gtk.STOCK_HOME, _("_Home"), 
                         accel="<Alt>Home", 
                         tip=_("Go to the default person"), callback=self.home)
        self.other_action = gtk.ActionGroup(self.title + '/PersonOther')
        self.other_action.add_actions([
                ('SetActive', gtk.STOCK_HOME, _("Set _Home Person"), None, 
                 None, self.set_default_person), 
                ])
        self._add_action_group(self.back_action)
        self._add_action_group(self.fwd_action)
        self._add_action_group(self.other_action)

    def set_active(self):
        PageView.PersonNavView.set_active(self)
        self.key_active_changed = self.dbstate.connect('active-changed',
                                                       self.goto_active_person)
    
    def set_inactive(self):
        PageView.PersonNavView.set_inactive(self)
        self.dbstate.disconnect(self.key_active_changed)
        
    def goto_active_person(self, handle=None):
        self.dirty = True
        if handle:
            self.handle_history(handle)
        self.uistate.modify_statusbar(self.dbstate)

    def set_columns(self, num):
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
            self.hbox.pack_start(self.columns[-1],expand=True)
        # place the gramplets back in the new columns
        self.place_gramplets(recolumn=True)
        self.widget.show()

    def restore_gramplet(self, obj):
        name = obj.get_child().get_label()
        ############### First kind: from current session
        for gramplet in self.closed_gramplets:
            if gramplet.title == name:
                #gramplet.state = "maximized"
                self.closed_gramplets.remove(gramplet)
                if self._popup_xy != None:
                    self.drop_widget(self.widget, gramplet, 
                                     self._popup_xy[0], self._popup_xy[1], 0)
                else:
                    self.drop_widget(self.widget, gramplet, 0, 0, 0)
                gramplet.set_state("maximized")
                return
        ################ Second kind: from options
        for opts in self.closed_opts:
            if opts["title"] == name:
                self.closed_opts.remove(opts)
                g = make_requested_gramplet(self, opts["name"], opts, 
                                          self.dbstate, self.uistate)
                if g:
                    self.gramplet_map[opts["title"]] = g
                    self.frame_map[str(g.mainframe)] = g
                else:
                    print "Can't make gramplet of type '%s'." % name
        if g:
            gramplet = g
            gramplet.state = "maximized"
            if gramplet.column >= 0 and gramplet.column < len(self.columns):
                pos = gramplet.column
            else:
                pos = 0
            self.columns[pos].pack_start(gramplet.mainframe, expand=gramplet.expand)
            # set height on gramplet.scrolledwindow here:
            gramplet.scrolledwindow.set_size_request(-1, gramplet.height)
            ## now drop it in right place
            if self._popup_xy != None:
                self.drop_widget(self.widget, gramplet, 
                                 self._popup_xy[0], self._popup_xy[1], 0)
            else:
                self.drop_widget(self.widget, gramplet, 0, 0, 0)

    def add_gramplet(self, obj):
        tname = obj.get_child().get_label()
        all_opts = get_gramplet_options_by_tname(tname)
        name = all_opts["name"]
        if all_opts == None:
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
            g = make_requested_gramplet(self, name, all_opts, 
                                      self.dbstate, self.uistate)
        if g:
            self.gramplet_map[all_opts["title"]] = g
            self.frame_map[str(g.mainframe)] = g
            gramplet = g
            if gramplet.column >= 0 and gramplet.column < len(self.columns):
                pos = gramplet.column
            else:
                pos = 0
            self.columns[pos].pack_start(gramplet.mainframe, expand=gramplet.expand)
            # set height on gramplet.scrolledwindow here:
            gramplet.scrolledwindow.set_size_request(-1, gramplet.height)
            ## now drop it in right place
            if self._popup_xy != None:
                self.drop_widget(self.widget, gramplet, 
                                 self._popup_xy[0], self._popup_xy[1], 0)
            else:
                self.drop_widget(self.widget, gramplet, 0, 0, 0)
        else:
            print "Can't make gramplet of type '%s'." % name

    def get_stock(self):
        """
        Return image associated with the view, which is used for the 
        icon for the button.
        """
        return 'gramps-gramplet'
    
    def build_tree(self):
        return 

    def ui_definition(self):
        return """
        <ui>
          <menubar name="MenuBar">
            <menu action="GoMenu">
              <placeholder name="CommonGo">
                <menuitem action="Back"/>
                <menuitem action="Forward"/>
                <separator/>
                <menuitem action="HomePerson"/>
                <separator/>
              </placeholder>
            </menu>
            <menu action="ViewMenu">
              <menuitem action="Columns1"/>
              <menuitem action="Columns2"/>
              <menuitem action="Columns3"/>
            </menu>
          </menubar>
          <toolbar name="ToolBar">
            <placeholder name="CommonNavigation">
              <toolitem action="Back"/>  
              <toolitem action="Forward"/>  
              <toolitem action="HomePerson"/>
            </placeholder>
          </toolbar>
          <popup name="Popup">
            <menuitem action="AddGramplet"/>
            <menuitem action="RestoreGramplet"/>
            <separator/>
            <menuitem action="Columns1"/>
            <menuitem action="Columns2"/>
            <menuitem action="Columns3"/>
          </popup>
        </ui>
        """
        
    def _button_press(self, obj, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            self._popup_xy = (event.x, event.y)
            menu = self.uistate.uimanager.get_widget('/Popup')
            ag_menu = self.uistate.uimanager.get_widget('/Popup/AddGramplet')
            if ag_menu:
                qr_menu = ag_menu.get_submenu()
                if qr_menu == None:
                    qr_menu = gtk.Menu()
                    names = [AVAILABLE_GRAMPLETS[key]["tname"] for key 
                             in AVAILABLE_GRAMPLETS.keys()]
                    names.sort()
                    for name in names:
                        Utils.add_menuitem(qr_menu, name, 
                                           None, self.add_gramplet)
                    self.uistate.uimanager.get_widget('/Popup/AddGramplet').set_submenu(qr_menu)
            rg_menu = self.uistate.uimanager.get_widget('/Popup/RestoreGramplet')
            if rg_menu:
                qr_menu = rg_menu.get_submenu()
                if qr_menu != None:
                    rg_menu.remove_submenu()
                names = []
                for gramplet in self.closed_gramplets:
                    names.append(gramplet.title)
                for opts in self.closed_opts:
                    names.append(opts["title"])
                names.sort()
                if len(names) > 0:
                    qr_menu = gtk.Menu()
                    for name in names:
                        Utils.add_menuitem(qr_menu, name, 
                                           None, self.restore_gramplet)
                    self.uistate.uimanager.get_widget('/Popup/RestoreGramplet').set_submenu(qr_menu)
            if menu:
                menu.popup(None, None, None, event.button, event.time)
                return True
        return False

    def on_delete(self):
        gramplets = [g for g in self.gramplet_map.values() if g != None]
        for gramplet in gramplets:
            # this is the only place where the gui runs user code directly
            if gramplet.pui:
                gramplet.pui.on_save()
        self.save()
