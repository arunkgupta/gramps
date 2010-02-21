#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009  Douglas S. Blank <doug.blank@gmail.com>
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

import types
from gen.ggettext import gettext as _

class Gramplet(object):
    """
    Base class for non-graphical gramplet code.
    """
    def __init__(self, gui, nav_group=0):
        """
        Internal constructor for non-graphical gramplets.
        """
        self._idle_id = 0
        self.track = []
        self.active = False
        self.dirty = True
        self._pause = False
        self._generator = None
        self._need_to_update = False
        self.option_dict = {}
        self._signal = {}
        self.option_order = []
        # links to each other:
        self.gui = gui   # plugin gramplet has link to gui
        gui.pui = self   # gui has link to plugin ui
        self.nav_group = nav_group
        self.dbstate = gui.dbstate
        self.uistate = gui.uistate
        self.init()
        self.on_load()
        self.build_options()
        self.connect(self.dbstate, "database-changed", self._db_changed)
        self.connect(self.gui.textview, "button-press-event", 
                     self.gui.on_button_press) 
        self.connect(self.gui.textview, "motion-notify-event", 
                     self.gui.on_motion)
        self.connect_signal('Person', self._active_changed)
        
        active_person = self.get_active('Person')
        if active_person: # already changed
            self._db_changed(self.dbstate.db)
            self._active_changed(active_person)
        self.post_init()

    def connect_signal(self, nav_type, method):
        """
        Connect the given method to the active-changed signal for the
        navigation type requested. 
        """
        self.uistate.register(nav_type, self.nav_group)
        history = self.uistate.get_history(nav_type, self.nav_group)
        self.connect(history, "active-changed", method)

    def init(self): # once, constructor
        """
        External constructor for developers to put their initialization
        code. Designed to be overridden.
        """
        pass

    def post_init(self):
        pass

    def build_options(self):
        """
        External constructor for developers to put code for building
        options.
        """
        pass

    def main(self): # return false finishes
        """
        The main place for the gramplet's code. This is a generator.
        Generator which will be run in the background, through update().
        """
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
        return

    def get_active(self, nav_type):
        """
        Return the handle of the active object for the given navigation type.
        """
        return self.uistate.get_active(nav_type, self.nav_group)

    def get_active_object(self, nav_type):
        """
        Return the object of the active handle for the given navigation type.
        Assumes nav_type is one of the codes of Db.get_by_name.
        """
        handle = self.uistate.get_active(nav_type, self.nav_group)
        if nav_type in self.dbstate.db.get_table_names() and handle:
            return self.dbstate.db.get_from_name_and_handle(nav_type, handle)
        return None

    def set_active(self, nav_type, handle):
        """
        Change the handle of the active object for the given navigation type.
        """
        self.uistate.set_active(handle, nav_type, self.nav_group)

    def active_changed(self, handle):
        """
        Developers should put their code that occurs when the active
        person is changed.
        """
        pass

    def _active_changed(self, handle):
        """
        Private code that updates the GUI when active_person is changed.
        """
        self.active_changed(handle)

    def db_changed(self):
        """
        Method executed when the database is changed. 
        """
        pass

    def link(self, text, link_type, data, size=None, tooltip=None):
        """
        Creates a clickable link in the textview area.
        """
        self.gui.link(text, link_type, data, size, tooltip)

    # Shortcuts to the gui functionality:

    def set_tooltip(self, tip):
        """
        Sets the tooltip for this gramplet.
        """
        self.gui.tooltip = tip

    def get_text(self):
        """
        Returns the current text of the textview.
        """
        return self.gui.get_text()
        
    def insert_text(self, text):
        """
        Insert the given text in the textview at the cursor.
        """
        self.gui.insert_text(text)

    def render_text(self, text):
        """
        Render the given text, given that set_use_markup is on.
        """
        self.gui.render_text(text)

    def clear_text(self):
        """
        Clear all of the text from the textview.
        """
        self.gui.clear_text()
        
    def set_text(self, text, scroll_to='start'):
        """
        Clear and set the text to the given text. Additionally, move the
        cursor to the position given. Positions are: 
           'start': start of textview
           'end': end of textview
           'begin': begin of line, before setting the text.
        """
        self.gui.set_text(text, scroll_to)

    def append_text(self, text, scroll_to="end"):
        """
        Append the text to the textview. Additionally, move the
        cursor to the position given. Positions are: 
           'start': start of textview
           'end': end of textview
           'begin': begin of line, before setting the text.
        """
        self.gui.append_text(text, scroll_to)

    def set_use_markup(self, value):
        """
        Allows the use of render_text to show markup.
        """
        self.gui.set_use_markup(value)

    def set_wrap(self, value):
        """
        Set the textview to wrap or not.
        """
        import gtk
        self.gui.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, 
                                           gtk.POLICY_AUTOMATIC)
        # gtk.WRAP_NONE, gtk.WRAP_CHAR, gtk.WRAP_WORD or gtk.WRAP_WORD_CHAR.
        if value in [True, 1]:
            self.gui.textview.set_wrap_mode(gtk.WRAP_WORD)
        elif value in [False, 0, None]:
            self.gui.textview.set_wrap_mode(gtk.WRAP_NONE)
        elif value in ["char"]:
            self.gui.textview.set_wrap_mode(gtk.WRAP_CHAR)
        elif value in ["word char"]:
            self.gui.textview.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        else:
            raise Exception("Unknown wrap mode: '%s': use 0,1,'char' or 'word char')" % value)

    def no_wrap(self):
        """
        The view in gramplet should not wrap. DEPRICATED: use set_wrap instead.
        """
        self.set_wrap(False)

    # Other functions of the gramplet:

    def load_data_to_text(self, pos=0):
        """
        Load information from the data portion of the saved
        Gramplet to the textview.
        """
        if len(self.gui.data) >= pos + 1:
            text = self.gui.data[pos]
            text = text.replace("\\n", chr(10))
            self.set_text(text, 'end')

    def save_text_to_data(self):
        """
        Save the textview to the data portion of a saved gramplet.
        """
        text = self.get_text()
        text = text.replace(chr(10), "\\n")
        self.gui.data.append(text)

    def update(self, *args):
        """
        The main interface for running the main method.
        """
        import gobject
        if ((not self.active or 
             self.gui.state in ["closed", "minimized"] or 
             not self.dbstate.open) and 
            not self.gui.force_update): 
            self.dirty = True
            #print "  %s is not active" % self.gui.title
            return
        #print "     %s is UPDATING" % self.gui.title
        self.dirty = False
        self.uistate.push_message(self.dbstate,
                _("Gramplet %s is running") % self.gui.title)
        if self._idle_id != 0:
            self.interrupt()
        self._generator = self.main()
        self._pause = False
        self._idle_id = gobject.idle_add(self._updater, 
                                         priority=gobject.PRIORITY_LOW - 10)

    def _updater(self):
        """
        Runs the generator.
        """
        if not isinstance(self._generator, types.GeneratorType):
            self._idle_id = 0
            self.uistate.push_message(self.dbstate,
                _("Gramplet %s updated") % self.gui.title)
            return False
        try:
            retval = self._generator.next()
            if not retval:
                self._idle_id = 0
            if self._pause:
                self.uistate.push_message(self.dbstate,
                   _("Gramplet %s updated") % self.gui.title)
                return False
            return retval
        except StopIteration:
            self._idle_id = 0
            self.uistate.push_message(self.dbstate,
                _("Gramplet %s updated") % self.gui.title)
            return False
        except Exception, e:
            import traceback
            print "Gramplet gave an error"
            traceback.print_exc()
            print "Continuing after gramplet error..."
            self._idle_id = 0
            self.uistate.push_message(self.dbstate,
                _("Gramplet %s caused an error") % self.gui.title)
            return False

    def pause(self, *args):
        """
        Pause the main method.
        """
        self._pause = True

    def resume(self, *args):
        """
        Resume the main method that has previously paused.
        """
        import gobject
        self._pause = False
        self._idle_id = gobject.idle_add(self._updater, 
                                         priority=gobject.PRIORITY_LOW - 10)

    def update_all(self, *args):
        """
        Force the main loop to run right now (as opposed to running in background).
        """
        self._generator = self.main()
        if isinstance(self._generator, types.GeneratorType):
            for step in self._generator:
                pass

    def interrupt(self, *args):
        """
        Force the generator to stop running.
        """
        import gobject
        self._pause = True
        if self._idle_id == 0:
            gobject.source_remove(self._idle_id)
            self._idle_id = 0

    def _db_changed(self, db):
        """
        Internal method for handling items that should happen when the
        database changes. This will push a message to the GUI status bar.
        """
        self.dbstate.db = db
        self.gui.dbstate.db = db
        self.db_changed()
        self.update()

    def get_option_widget(self, label):
        """
        Retrieve an option's widget by its label text.
        """
        return self.option_dict[label][0]

    def get_option(self, label):
        """
        Retireve an option by its label text.
        """
        return self.option_dict[label][1]

    def add_option(self, option):
        """
        Add an option to the GUI gramplet.
        """
        from PluginUtils import make_gui_option
        widget, label = make_gui_option(
            option, self.dbstate, self.uistate, self.track)
        self.option_dict.update({option.get_label(): [widget, option]})
        self.option_order.append(option.get_label())

    def save_update_options(self, obj):
        """
        Save a gramplet's options to file.
        """
        self.save_options()
        self.update()

    def save_options(self):
        pass

    def connect(self, signal_obj, signal, method):
        id = signal_obj.connect(signal, method)
        self._signal[signal] = (id, signal_obj)

    def disconnect(self, signal):
        if signal in self._signal:
            (id, signal_obj) = self._signal[signal]
            signal_obj.disconnect(id)
        else:
            raise AttributeError("unknown signal: '%s'" % signal)
