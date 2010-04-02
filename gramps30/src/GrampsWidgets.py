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

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import cgi
import os
import cPickle as pickle
from gettext import gettext as _
import string

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".GrampsWidget")

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gobject
import gtk
import gtk.glade
import pango

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
import AutoComp
import DateEdit
import const
import Config
from Errors import MaskError, ValidationError, WindowActiveError
from DdTargets import DdTargets

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------


# STOCK_INFO was added only in Gtk 2.8
try:
    INFO_ICON = gtk.STOCK_INFO
except:
    INFO_ICON = gtk.STOCK_DIALOG_INFO

# Enabling custom widgets to be included in Glade
def get_custom_handler(glade, function_name, widget_name, 
                       str1, str2, int1, int2):
    if function_name == 'ValidatableMaskedEntry':
        return ValidatableMaskedEntry()

gtk.glade.set_custom_handler(get_custom_handler)


hand_cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
def realize_cb(widget):
    widget.window.set_cursor(hand_cursor)

class ExpandCollapseArrow(gtk.EventBox):
    """
        Arrow to be used for expand/collapse of sections.
        Note: shadow does not work, we indicate action with realize_cb
    """
    def __init__(self, collapsed, onbuttonpress, pair):
        """
        Constructor for the ExpandCollapseArrow class.

        @param collapsed: True if arrow must be shown collapsed, 
                        False otherwise
        @type collapsed: bool
        @param onbuttonpress: The callback function for button press
        @type onbuttonpress:  callback
        @param pair: user param for onbuttonpress function
        """
        gtk.EventBox.__init__(self)
        self.tooltips = gtk.Tooltips()
        if collapsed :
            self.arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_OUT)
            self.tooltips.set_tip(self, _("Expand this section"))
        else:
            self.arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_OUT)
            self.tooltips.set_tip(self, _("Collapse this section"))

        self.add(self.arrow)
        self.connect('button-press-event', onbuttonpress, pair)
        self.connect('realize', realize_cb)

class LinkLabel(gtk.EventBox):

    def __init__(self, label, func, handle, decoration='underline="single"'):
        gtk.EventBox.__init__(self)
        self.orig_text = cgi.escape(label[0])
        self.gender = label[1]
        self.tooltips = gtk.Tooltips()
        self.decoration = decoration
        text = '<span %s>%s</span>' % (self.decoration, self.orig_text)

        if func:
            msg = _('Click to make the active person\n'
                    'Right click to display the edit menu')
            if not Config.get(Config.RELEDITBTN):
                msg += "\n" + _('Edit icons can be enabled in the Preferences dialog')

            self.tooltips.set_tip(self, msg)
        
        self.label = gtk.Label(text)
        self.label.set_use_markup(True)
        self.label.set_alignment(0, 0.5)

        hbox = gtk.HBox()
        hbox.pack_start(self.label, False, False, 0)
        if label[1]:
            hbox.pack_start(GenderLabel(label[1]), False, False, 0)
            hbox.set_spacing(4)
        self.add(hbox)

        if func:
            self.connect('button-press-event', func, handle)
            self.connect('enter-notify-event', self.enter_text, handle)
            self.connect('leave-notify-event', self.leave_text, handle)
            self.connect('realize', realize_cb)

    def set_padding(self, x, y):
        self.label.set_padding(x, y)
        
    def enter_text(self, obj, event, handle):
        text = '<span foreground="blue" %s>%s</span>' % (self.decoration, self.orig_text)
        self.label.set_text(text)
        self.label.set_use_markup(True)

    def leave_text(self, obj, event, handle):
        text = '<span %s>%s</span>' % (self.decoration, self.orig_text)
        self.label.set_text(text)
        self.label.set_use_markup(True)

class IconButton(gtk.Button):

    def __init__(self, func, handle, icon=gtk.STOCK_EDIT, 
                 size=gtk.ICON_SIZE_MENU):
        gtk.Button.__init__(self)
        image = gtk.Image()
        image.set_from_stock(icon, size)
        image.show()
        self.add(image)
        self.set_relief(gtk.RELIEF_NONE)
        self.show()

        if func:
            self.connect('button-press-event', func, handle)
            self.connect('key-press-event', func, handle)

class WarnButton(gtk.Button):
    def __init__(self):
        gtk.Button.__init__(self)

        image = gtk.Image()
        image.set_from_stock(INFO_ICON, gtk.ICON_SIZE_MENU)
        image.show()
        self.add(image)

        self.set_relief(gtk.RELIEF_NONE)
        self.show()
        self.func = None
        self.hide()

    def on_clicked(self, func):
        self.connect('button-press-event', self._button_press)
        self.func = func

    def _button_press(self, obj, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            self.func(obj)

class SimpleButton(gtk.Button):

    def __init__(self, image, func):
        gtk.Button.__init__(self)
        self.set_relief(gtk.RELIEF_NONE)
        self.add(gtk.image_new_from_stock(image, gtk.ICON_SIZE_BUTTON))
        self.connect('clicked', func)
        self.show()
        
class LinkBox(gtk.HBox):

    def __init__(self, link, button):
        gtk.HBox.__init__(self)
        self.set_spacing(6)
        self.pack_start(link, False)
        if button:
            self.pack_start(button, False)
        self.show()

class EditLabel(gtk.HBox):
    def __init__(self, text):
        gtk.HBox.__init__(self)
        label = BasicLabel(text)
        self.pack_start(label, False)
        self.pack_start(gtk.image_new_from_stock(gtk.STOCK_EDIT, 
                                                 gtk.ICON_SIZE_MENU), False)
        self.set_spacing(4)
        self.show_all()

class BasicLabel(gtk.Label):

    def __init__(self, text):
        gtk.Label.__init__(self, text)
        self.set_alignment(0, 0.5)
        self.show()

class GenderLabel(gtk.Label):

    def __init__(self, text):
        gtk.Label.__init__(self, text)
        self.set_alignment(0, 0.5)
        if os.sys.platform == "win32":
            pangoFont = pango.FontDescription('Arial')
            self.modify_font(pangoFont)
        self.show()

class MarkupLabel(gtk.Label):

    def __init__(self, text):
        gtk.Label.__init__(self, text)
        self.set_alignment(0, 0.5)
        self.set_use_markup(True)
        self.show_all()

class DualMarkupLabel(gtk.HBox):

    def __init__(self, text, alt):
        gtk.HBox.__init__(self)
        label = gtk.Label(text)
        label.set_alignment(0, 0.5)
        label.set_use_markup(True)

        self.pack_start(label, False, False, 0)
        b = GenderLabel(alt)
        b.set_use_markup(True)
        self.pack_start(b, False, False, 4)
        self.show()
        
class IntEdit(gtk.Entry):
    """An gtk.Edit widget that only allows integers."""
    
    def __init__(self):
        gtk.Entry.__init__(self)

        self._signal = self.connect("insert_text", self.insert_cb)

    def insert_cb(self, widget, text, length, *args):        
        # if you don't do this, garbage comes in with text
        text = text[:length]
        pos = widget.get_position()
        # stop default emission
        widget.emit_stop_by_name("insert_text")
        gobject.idle_add(self.insert, widget, text, pos)

    def insert(self, widget, text, pos):
        if len(text) > 0 and text.isdigit():            
            # the next three lines set up the text. this is done because we
            # can't use insert_text(): it always inserts at position zero.
            orig_text = widget.get_text()            
            new_text = orig_text[:pos] + text + orig_text[pos:]
            # avoid recursive calls triggered by set_text
            widget.handler_block(self._signal)
            # replace the text with some new text
            widget.set_text(new_text)
            widget.handler_unblock(self._signal)
            # set the correct position in the widget
            widget.set_position(pos + len(text))

class TypeCellRenderer(gtk.CellRendererCombo):

    def __init__(self, values):
        gtk.CellRendererCombo.__init__(self)

        model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_INT)
        for key in values:
            model.append(row=[values[key], key])
        self.set_property('editable', True)
        self.set_property('model', model)
        self.set_property('text-column', 0)

class PrivacyButton:

    def __init__(self, button, obj, readonly=False):
        self.button = button
        self.button.connect('toggled', self._on_toggle)
        self.tooltips = gtk.Tooltips()
        self.obj = obj
        self.set_active(obj.get_privacy())
        self.button.set_sensitive(not readonly)

    def set_sensitive(self, val):
        self.button.set_sensitive(val)

    def set_active(self, val):
        self.button.set_active(val)
        self._on_toggle(self.button)

    def get_active(self):
        return self.button.get_active()

    def _on_toggle(self, obj):
        child = obj.child
        if child:
            obj.remove(child)
        image = gtk.Image()
        if obj.get_active():
#            image.set_from_icon_name('stock_lock', gtk.ICON_SIZE_MENU)
            image.set_from_stock('gramps-lock', gtk.ICON_SIZE_MENU)
            self.tooltips.set_tip(obj, _('Record is private'))
            self.obj.set_privacy(True)
        else:
#            image.set_from_icon_name('stock_lock-open', gtk.ICON_SIZE_MENU)
            image.set_from_stock('gramps-unlock', gtk.ICON_SIZE_MENU)
            self.tooltips.set_tip(obj, _('Record is public'))
            self.obj.set_privacy(False)
        image.show()
        obj.add(image)

class MonitoredCheckbox:

    def __init__(self, obj, button, set_val, get_val, on_toggle=None, readonly = False):
        self.button = button
        self.button.connect('toggled', self._on_toggle)
        self.on_toggle = on_toggle
        self.obj = obj
        self.set_val = set_val
        self.get_val = get_val
        self.button.set_active(get_val())
        self.button.set_sensitive(not readonly)

    def _on_toggle(self, obj):
        self.set_val(obj.get_active())
        if self.on_toggle:
            self.on_toggle(self.get_val())
        
class MonitoredEntry:

    def __init__(self, obj, set_val, get_val, read_only=False, 
                 autolist=None, changed=None):
        self.obj = obj
        self.set_val = set_val
        self.get_val = get_val
        self.changed = changed

        if get_val():
            self.obj.set_text(get_val())
        self.obj.connect('changed', self._on_change)
        self.obj.set_editable(not read_only)

        if autolist:
            AutoComp.fill_entry(obj, autolist)

    def reinit(self, set_val, get_val):
        self.set_val = set_val
        self.get_val = get_val
        self.update()

    def set_text(self, text):
        self.obj.set_text(text)
        
    def connect(self, signal, callback, *data):
        self.obj.connect(signal, callback, *data)

    def _on_change(self, obj):
        self.set_val(unicode(obj.get_text()))
        if self.changed:
            self.changed(obj)

    def force_value(self, value):
        self.obj.set_text(value)

    def get_value(self, value):
        return unicode(self.obj.get_text())

    def enable(self, value):
        self.obj.set_sensitive(value)
        self.obj.set_editable(value)

    def grab_focus(self):
        self.obj.grab_focus()

    def update(self):
        if self.get_val() is not None:
            self.obj.set_text(self.get_val())

class MonitoredSpinButton:
    """
    Class for signal handling of spinbuttons.
    (Code is a modified copy of MonitoredEntry)
    """

    def __init__(self, obj, set_val, get_val, read_only=False,
                 autolist=None, changed=None):
        """
        @param obj: widget to be monitored
        @type obj: gtk.SpinButton
        @param set_val: callback to be called when obj is changed
        @param get_val: callback to be called to retrieve value for obj
        @param read_only: If SpinButton is read only.
        """
        
        self.obj = obj
        self.set_val = set_val
        self.get_val = get_val
        self.changed = changed

        if get_val():
            self.obj.set_value(get_val())
        self.obj.connect('value-changed', self._on_change)
        self.obj.set_editable(not read_only)

        if autolist:
            AutoComp.fill_entry(obj,autolist)

    def reinit(self, set_val, get_val):
        """
        Reinitialize class with the specified callback functions.

        @param set_val: callback to be called when SpinButton is changed
        @param get_val: callback to be called to retrieve value for SpinButton
        """
        
        self.set_val = set_val
        self.get_val = get_val
        self.update()

    def set_value(self, value):
        """
        Set the value of the monitored widget to the specified value.

        @param value: Value to be set.
        """
        
        self.obj.set_value(value)
        
    def connect(self, signal, callback):
        """
        Connect the signal of monitored widget to the specified callback.

        @param signal: Signal prototype for which a connection should be set up.
        @param callback: Callback function to be called when signal is emitted.
        """
        
        self.obj.connect(signal, callback)

    def _on_change(self, obj):
        """
        Event handler to be called when the monitored widget is changed.

        @param obj: Widget that has been changed.
        @type obj: gtk.SpinButton
        """
        
        self.set_val(obj.get_value())
        if self.changed:
            self.changed(obj)

    def force_value(self, value):
        """
        Set the value of the monitored widget to the specified value.

        @param value: Value to be set.
        """
        
        self.obj.set_value(value)

    def get_value(self):
        """
        Get the current value of the monitored widget.

        @returns: Current value of monitored widget.
        """

        return self.obj.get_value()

    def enable(self, value):
        """
        Change the property editable and sensitive of the monitored widget to value.

        @param value: If widget should be editable or deactivated.
        @type value: bool
        """
        
        self.obj.set_sensitive(value)
        self.obj.set_editable(value)

    def grab_focus(self):
        """
        Assign the keyboard focus to the monitored widget.
        """
        
        self.obj.grab_focus()

    def update(self):
        """
        Updates value of monitored SpinButton with the value returned by the get_val callback.
        """
        
        if self.get_val():
            self.obj.set_value(self.get_val())

class MonitoredText:

    def __init__(self, obj, set_val, get_val, read_only=False):
        self.buf = obj.get_buffer()
        self.set_val = set_val
        self.get_val = get_val

        if get_val():
            self.buf.set_text(get_val())
        self.buf.connect('changed', self.on_change)
        obj.set_editable(not read_only)

    def on_change(self, obj):
        s, e = self.buf.get_bounds()
        self.set_val(unicode(self.buf.get_text(s, e, False)))

class MonitoredType:

    def __init__(self, obj, set_val, get_val, mapping, custom, readonly=False, 
                 custom_values=None):
        self.set_val = set_val
        self.get_val = get_val

        self.obj = obj

        val = get_val()
        if val:
            default = val[0]
        else:
            default = None

        self.sel = AutoComp.StandardCustomSelector(
            mapping, obj, custom, default, additional=custom_values)

        self.set_val(self.sel.get_values())
        self.obj.set_sensitive(not readonly)
        self.obj.connect('changed', self.on_change)

    def reinit(self, set_val, get_val):
        self.set_val = set_val
        self.get_val = get_val
        self.update()

    def update(self):
        if self.get_val():
            self.sel.set_values(self.get_val())

    def on_change(self, obj):
        self.set_val(self.sel.get_values())

class MonitoredDataType:
    

    def __init__(self, obj, set_val, get_val, readonly=False, 
                 custom_values=None, ignore_values=None):
        """
        Constructor for the MonitoredDataType class.

        @param obj: Existing ComboBoxEntry widget to use.
        @type obj: gtk.ComboBoxEntry
        @param set_val: The function that sets value of the type in the object
        @type set_val:  method
        @param get_val: The function that gets value of the type in the object.
            This returns a GrampsType, of which get_map returns all possible types
        @type get_val:  method
        @param custom_values: Extra values to show in the combobox. These can be
            text of custom type, tuple with type info or GrampsType class
        @type : list of str, tuple or GrampsType
        @ignore_values: list of values not to show in the combobox. If the result
            of get_val is in these, it is not ignored
        @type : list of int 
        """
        self.set_val = set_val
        self.get_val = get_val

        self.obj = obj

        val = get_val()

        if val:
            default = int(val)
        else:
            default = None
            
        map = get_val().get_map().copy()
        if ignore_values :
            for key in map.keys():
                try :
                    i = ignore_values.index(key)
                except ValueError:
                    i = None
                if (not i==None) and (not ignore_values[i] == default) :
                    del map[key]

        self.sel = AutoComp.StandardCustomSelector(
            map, 
            obj, 
            get_val().get_custom(), 
            default, 
            additional=custom_values)

        self.sel.set_values((int(get_val()), str(get_val())))
        self.obj.set_sensitive(not readonly)
        self.obj.connect('changed', self.on_change)

    def reinit(self, set_val, get_val):
        self.set_val = set_val
        self.get_val = get_val
        self.update()

    def fix_value(self, value):
        if value[0] == self.get_val().get_custom():
            return value
        else:
            return (value[0], '')

    def update(self):
        val = self.get_val()
        if type(val) == tuple :
            self.sel.set_values(val)
        else:
            self.sel.set_values((int(val), str(val)))

    def on_change(self, obj):
        value = self.fix_value(self.sel.get_values())
        self.set_val(value)

class MonitoredMenu:

    def __init__(self, obj, set_val, get_val, mapping, 
                 readonly=False, changed=None):
        self.set_val = set_val
        self.get_val = get_val

        self.changed = changed
        self.obj = obj

        self.change_menu(mapping)
        self.obj.connect('changed', self.on_change)
        self.obj.set_sensitive(not readonly)

    def force(self, value):
        self.obj.set_active(value)

    def change_menu(self, mapping):
        self.data = {}
        self.model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_INT)
        index = 0
        for t, v in mapping:
            self.model.append(row=[t, v])
            self.data[v] = index
            index += 1
        self.obj.set_model(self.model)
        self.obj.set_active(self.data.get(self.get_val(), 0))

    def on_change(self, obj):
        self.set_val(self.model.get_value(obj.get_active_iter(), 1))
        if self.changed:
            self.changed()

class MonitoredStrMenu:

    def __init__(self, obj, set_val, get_val, mapping, readonly=False):
        self.set_val = set_val
        self.get_val = get_val

        self.obj = obj
        self.model = gtk.ListStore(gobject.TYPE_STRING)
        
        if len(mapping) > 20:
            self.obj.set_wrap_width(3)

        self.model.append(row=[''])
        index = 0
        self.data = ['']

        default = get_val()
        active = 0
        
        for t, v in mapping:
            self.model.append(row=[v])
            self.data.append(t)
            index += 1
            if t == default:
                active = index
            
        self.obj.set_model(self.model)
        self.obj.set_active(active)
        self.obj.connect('changed', self.on_change)
        self.obj.set_sensitive(not readonly)

    def on_change(self, obj):
        self.set_val(self.data[obj.get_active()])

class MonitoredDate:

    def __init__(self, field, button, value, uistate, track, readonly=False):
        self.date = value
        self.date_check = DateEdit.DateEdit(
            self.date, field, button, uistate, track)
        field.set_editable(not readonly)
        button.set_sensitive(not readonly)

class ObjEntry:
    """
    Handles the selection of a existing or new Object. Supports Drag and Drop
    to select the object.
    This is the base class to create a real entry
    """
    def __init__(self, dbstate, uistate, track, label, set_val, 
                 get_val, add_edt, share):
        """Pass the dbstate and uistate and present track.
            label is a gtk.Label that shows the persent value
            set_val is function that is called when handle changes, use it
                to update the calling module
            get_val is function that is called to obtain handle from calling
                module
            share is the gtk.Button to call the object selector or del connect
            add_edt is the gtk.Button with add or edit value. Pass None if 
                this button should not be present.
        """
        self.label = label
        self.add_edt = add_edt
        self.share = share
        self.dbstate = dbstate
        self.db = dbstate.db
        self.get_val = get_val
        self.set_val = set_val
        self.uistate = uistate
        self.track = track
        self.tooltips = gtk.Tooltips()
        
        #connect drag and drop
        self._init_dnd()
        #set the object specific code
        self._init_object()

        #check if valid object:
        handle = self.get_val()
        if handle:
            obj = self.get_from_handle(handle)
            if not obj:
                #invalid val, set it to None
                self.set_val(None)
        if self.get_val():
            self.set_button(True)
            obj = self.get_from_handle(self.get_val())
            name = self.get_label(obj)
        else:
            name = u""
            self.set_button(False)

        if self.db.readonly:
            if self.add_edt is not None:
                self.add_edt.set_sensitive(False)
            self.share.set_sensitive(False)
        else:
            if self.add_edt is not None:
                self.add_edt.set_sensitive(True)
            self.share.set_sensitive(True)

        if self.add_edt is not None:
            self.add_edt.connect('clicked', self.add_edt_clicked)
        self.share.connect('clicked', self.share_clicked)
        
        if not self.db.readonly and not name:
            if self.add_edt is None:
                self.label.set_text(self.EMPTY_TEXT_RED)
            else:
                self.label.set_text(self.EMPTY_TEXT)
            self.label.set_use_markup(True)
        else:
            self.label.set_text(name)

    def _init_dnd(self):
        """inheriting objects must set this
        """
        pass

    def _init_object(self):
        """inheriting objects can use this to set extra variables
        """
        pass

    def get_from_handle(self, handle):
        """ return the object given the hande
            inheriting objects must set this
        """
        pass

    def get_label(self, object):
        """ return the label
            inheriting objects must set this
        """
        pass

    def after_edit(self, obj):
        name = self.get_label(obj)
        self.label.set_text(name)

    def add_edt_clicked(self, obj):
        """ if value, edit, if no value, call editor on new object
        """
        if self.get_val():
            obj = self.get_from_handle(self.get_val())
            self.call_editor(obj)
        else:
            self.call_editor()

    def call_editor(self, obj):
        """inheriting objects must set this
        """
        pass

    def call_selector(self):
        """inheriting objects must set this
        """
        pass

    def drag_data_received(self, widget, context, x, y, selection, info, time):
        (drag_type, idval, obj, val) = pickle.loads(selection.data)
        
        data = self.db.get_place_from_handle(obj)
        self.obj_added(data)
        
    def obj_added(self, data):
        """ callback from adding an object to the entry"""
        self.set_val(data.handle)
        self.label.set_text(self.get_label(data))
        self.set_button(True)

    def share_clicked(self, obj):
        """ if value, delete connect, in no value, select existing object
        """
        if self.get_val():
            self.set_val(None)
            self.label.set_text(self.EMPTY_TEXT)
            self.label.set_use_markup(True)
            self.set_button(False)
        else:
            select = self.call_selector()
            obj = select.run()
            if obj:
                self.obj_added(obj)

    def set_button(self, use_add):
        """ This sets the correct image to the two buttons.
            If False: select icon and add icon
            If True:  remove icon and edit icon
        """
        if self.add_edt is not None:
            for i in self.add_edt.get_children():
                self.add_edt.remove(i)
        for i in self.share.get_children():
            self.share.remove(i)

        if use_add:
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)
            image.show()
            self.share.add(image)
            self.tooltips.set_tip(self.share, self.DEL_STR)
            if self.add_edt is not None:
                image = gtk.Image()
                image.set_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON)
                image.show()
                self.add_edt.add(image)
                self.tooltips.set_tip(self.add_edt, self.EDIT_STR)
        else:
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON)
            image.show()
            self.share.add(image)
            self.tooltips.set_tip(self.share, self.SHARE_STR)
            if self.add_edt is not None:
                image = gtk.Image()
                image.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
                image.show()
                self.add_edt.add(image)
                self.tooltips.set_tip(self.add_edt, self.ADD_STR)

class PlaceEntry(ObjEntry):
    """
    Handles the selection of a existing or new Place. Supports Drag and Drop
    to select a place.
    """
    EMPTY_TEXT = "<i>%s</i>" % _('To select a place, use drag-and-drop '
                                 'or use the buttons')
    EMPTY_TEXT_RED = "<i>%s</i>" % _('No place given, click button to select one')
    EDIT_STR = _('Edit place')
    SHARE_STR = _('Select an existing place')
    ADD_STR = _('Add a new place')
    DEL_STR = _('Remove place')
    
    def __init__(self, dbstate, uistate, track, label, set_val, 
                 get_val, add_edt, share):
        ObjEntry.__init__(self, dbstate, uistate, track, label, set_val, 
                 get_val, add_edt, share)

    def _init_dnd(self):
        """connect drag and drop of places
        """
        self.label.drag_dest_set(gtk.DEST_DEFAULT_ALL, [DdTargets.PLACE_LINK.target()], 
                               gtk.gdk.ACTION_COPY)
        self.label.connect('drag_data_received', self.drag_data_received)

    def get_from_handle(self, handle):
        """ return the object given the hande
        """
        return self.db.get_place_from_handle(handle)

    def get_label(self, place):
        return "%s [%s]" % (place.get_title(), place.gramps_id)

    def call_editor(self, obj=None):
        from Editors import EditPlace

        if obj is None:
            from gen.lib import Place
            place = Place()
            func = self.obj_added
        else:
            place = obj
            func = self.after_edit
        try:
            EditPlace(self.dbstate, self.uistate, self.track, 
                      place, func)
        except WindowActiveError:
            pass

    def call_selector(self):
        from Selectors import selector_factory
        cls = selector_factory('Place')
        return cls(self.dbstate, self.uistate, self.track)

class MediaEntry(ObjEntry):
    """
    Handles the selection of a existing or new media. Supports Drag and Drop
    to select a media object.
    """
    EMPTY_TEXT = "<i>%s</i>" % _('To select a media object, use drag-and-drop '
                                 'or use the buttons')
    EMPTY_TEXT_RED = "<i>%s</i>" % _('No image given, click button to select one')
    EDIT_STR = _('Edit media object')
    SHARE_STR = _('Select an existing media object')
    ADD_STR = _('Add a new media object')
    DEL_STR = _('Remove media object')
    
    def __init__(self, dbstate, uistate, track, label, set_val, 
                 get_val, add_edt, share):
        ObjEntry.__init__(self, dbstate, uistate, track, label, set_val, 
                 get_val, add_edt, share)

    def _init_dnd(self):
        """connect drag and drop of places
        """
        self.label.drag_dest_set(gtk.DEST_DEFAULT_ALL, [DdTargets.MEDIAOBJ.target()], 
                               gtk.gdk.ACTION_COPY)
        self.label.connect('drag_data_received', self.drag_data_received)

    def get_from_handle(self, handle):
        """ return the object given the hande
        """
        return self.db.get_object_from_handle(handle)

    def get_label(self, object):
        return "%s [%s]" % (object.get_description(), object.gramps_id)

    def call_editor(self, obj=None):
        from Editors import EditMedia

        if obj is None:
            from gen.lib import MediaObject
            object = MediaObject()
            func = self.obj_added
        else:
            object = obj
            func = self.after_edit
        try:
            EditMedia(self.dbstate, self.uistate, self.track, 
                      object, func)
        except WindowActiveError:
            pass

    def call_selector(self):
        from Selectors import selector_factory
        cls = selector_factory('MediaObject')
        return cls(self.dbstate, self.uistate, self.track)
    
class NoteEntry(ObjEntry):
    """
    Handles the selection of a existing or new Note. Supports Drag and Drop
    to select a Note.
        """
    EMPTY_TEXT = "<i>%s</i>" % _('To select a note, use drag-and-drop '
                                 'or use the buttons')
    EMPTY_TEXT_RED = "<i>%s</i>" % _('No note given, click button to select one')
    EDIT_STR = _('Edit Note')
    SHARE_STR = _('Select an existing note')
    ADD_STR = _('Add a new note')
    DEL_STR = _('Remove note')
    
    def __init__(self, dbstate, uistate, track, label, set_val, 
                 get_val, add_edt, share):
        ObjEntry.__init__(self, dbstate, uistate, track, label, set_val, 
                 get_val, add_edt, share)
        self.notetype = None

    def set_notetype(self, type):
        """ set a notetype to use in new notes
        """
        self.notetype = type

    def get_notetype(self):
        """ return the set notetype
        """
        return self.notetype

    def _init_dnd(self):
        """connect drag and drop of places
        """
        self.label.drag_dest_set(gtk.DEST_DEFAULT_ALL, [DdTargets.NOTE_LINK.target()], 
                               gtk.gdk.ACTION_COPY)
        self.label.connect('drag_data_received', self.drag_data_received)

    def get_from_handle(self, handle):
        """ return the object given the hande
        """
        return self.db.get_note_from_handle(handle)

    def get_label(self, note):
        txt = " ".join(note.get(markup=False).split())
        if len(txt) > 35:
            txt = txt[:35]+"..."
        else:
            txt = txt
        return "%s [%s]" % (txt, note.gramps_id)

    def call_editor(self, obj=None):
        from Editors import EditNote

        if obj is None:
            from gen.lib import Note
            note = Note()
            note.set_type(self.get_notetype())
            func = self.obj_added
        else:
            note = obj
            func = self.after_edit
        try:
            EditNote(self.dbstate, self.uistate, self.track, 
                         note, func)
        except WindowActiveError:
            pass

    def call_selector(self):
        from Selectors import selector_factory
        cls = selector_factory('Note')
        return cls(self.dbstate, self.uistate, self.track)

class Statusbar(gtk.HBox):
    """Custom Statusbar with flexible number of "bars".
    
    Statusbar can have any number of fields included, each identified
    by it's own bar id. It has by default one field with id = 0. This
    defult field is used when no bar id is given in the relevant (push, pop, 
    etc.) methods, thus Statusbar behaves as a single gtk.Statusbar.
    
    To add a new field use the "insert" method. Using the received bar id
    one can push, pop and remove messages to/from this newly inserted field.
    
    """
    __gtype_name__ = 'Statusbar'

    ##__gsignals__ = {
        ##'text-popped': , 
        ##'text-pushed': , 
    ##}

    __gproperties__ = {
        'has-resize-grip': (gobject.TYPE_BOOLEAN, 
                            'Resize grip', 
                            'Whether resize grip is visible', 
                            True, 
                            gobject.PARAM_READWRITE), 
    }
    
    def __init__(self, min_width=30):
        gtk.HBox.__init__(self)
        
        # initialize pixel/character scale
        pl = pango.Layout(self.get_pango_context())
        pl.set_text("M")
        (self._char_width, h) = pl.get_pixel_size()
        
        # initialize property values
        self.__has_resize_grip = True
        
        # create the main statusbar with id #0
        main_bar = gtk.Statusbar()
        main_bar.set_size_request(min_width*self._char_width, -1)
        main_bar.show()
        self.pack_start(main_bar)
        self._bars = {0: main_bar}
        self._set_resize_grip()

    # Virtual methods

    def do_get_property(self, prop):
        """Return the gproperty's value.
        """
        if prop.name == 'has-resize-grip':
            return self.__has_resize_grip
        else:
            raise AttributeError, 'unknown property %s' % prop.name

    def do_set_property(self, prop, value):
        """Set the property of writable properties.
        """
        if prop.name == 'has-resize-grip':
            self.__has_resize_grip = value
            self._set_resize_grip()
        else:
            raise AttributeError, 'unknown or read only property %s' % prop.name

    # Private
    
    def _set_resize_grip(self):
        """Set the resize grip for the statusbar.
        
        Resize grip is disabled for all statusbars except the last one, 
        which is set according to the "has-resize-grip" propery.
        
        """
        for bar in self.get_children():
            bar.set_has_resize_grip(False)
        
        bar.set_has_resize_grip(self.get_property('has-resize-grip'))

    def _set_packing(self):
        """Set packing style of the statusbars.
        
        All bars are packed with "expand"=True, "fill"=True parameters, 
        except the last one, which is packed with "expand"=False, "fill"=False.
        
        """
        for bar in self.get_children():
            self.set_child_packing(bar, True, True, 0, gtk.PACK_START)
            
        self.set_child_packing(bar, False, False, 0, gtk.PACK_START)

    def _get_next_id(self):
        """Get next unused statusbar id.
        """
        id = 1
        while id in self._bars.keys():
            id = id + 1
            
        return id

    # Public API
    
    def insert(self, index=-1, min_width=30, ralign=False):
        """Insert a new statusbar.
        
        Create a new statusbar and insert it at the given index. Index starts
        from '0'. If index is negative the new statusbar is appended.
        The new bar_id is returned.
        
        """
        new_bar = gtk.Statusbar()
        new_bar.set_size_request(min_width*self._char_width, -1)
        new_bar.show()
        self.pack_start(new_bar)
        self.reorder_child(new_bar, index)
        self._set_resize_grip()
        self._set_packing()
        
        if ralign:
            label = new_bar.get_children()[0].get_children()[0]
            label.set_alignment(xalign=1.0, yalign=0.5)        
        
        new_bar_id = self._get_next_id()
        self._bars[new_bar_id] = new_bar
        
        return new_bar_id
    
    def get_context_id(self, context_description, bar_id=0):
        """Return a new or existing context identifier.
        
        The target statusbar is identified by bar_id created when statusbar
        was added.
        Existence of the bar_id is not checked as giving a wrong id is
        programming fault.
        
        """
        return self._bars[bar_id].get_context_id(context_description)

    def push(self, context_id, text, bar_id=0):
        """Push message onto a statusbar's stack.
        
        The target statusbar is identified by bar_id created when statusbar
        was added.
        Existence of the bar_id is not checked as giving a wrong id is
        programming fault.
        
        """
        return self._bars[bar_id].push(context_id, text)

    def pop(self, context_id, bar_id=0):
        """Remove the top message from a statusbar's stack.
        
        The target statusbar is identified by bar_id created when statusbar
        was added.
        Existence of the bar_id is not checked as giving a wrong id is
        programming fault.
        
        """
        self._bars[bar_id].pop(context_id)

    def remove(self, context_id, message_id, bar_id=0):
        """Remove the message with the specified message_id.
        
        Remove the message with the specified message_id and context_id
        from the statusbar's stack, which is identified by bar_id.
        Existence of the bar_id is not checked as giving a wrong id is
        programming fault.
        
        """
        self._bars[bar_id].remove(context_id, message_id)
    
    def set_has_resize_grip(self, setting):
        """Mirror gtk.Statusbar functionaliy.
        """
        self.set_property('has-resize-grip', setting)
    
    def get_has_resize_grip(self):
        """Mirror gtk.Statusbar functionaliy.
        """
        return self.get_property('has-resize-grip')

#============================================================================
#
# MaskedEntry and ValidatableMaskedEntry copied and merged from the Kiwi
# project's ValidatableProxyWidgetMixin, KiwiEntry and ProxyEntry.
#
# http://www.async.com.br/projects/kiwi
#
#============================================================================

class FadeOut(gobject.GObject):
    """I am a helper class to draw the fading effect of the background
    Call my methods start() and stop() to control the fading.
    """
    __gsignals__ = {
        'done': (gobject.SIGNAL_RUN_FIRST, 
                 gobject.TYPE_NONE, 
                 ()), 
        'color-changed': (gobject.SIGNAL_RUN_FIRST, 
                          gobject.TYPE_NONE, 
                          (gtk.gdk.Color, )), 
    }
    
    # How long time it'll take before we start (in ms)
    COMPLAIN_DELAY = 500

    MERGE_COLORS_DELAY = 100

    def __init__(self, widget, err_color = "#ffd5d5"):
        gobject.GObject.__init__(self)
        self.ERROR_COLOR = err_color
        self._widget = widget
        self._start_color = None
        self._background_timeout_id = -1
        self._countdown_timeout_id = -1
        self._done = False

    def _merge_colors(self, src_color, dst_color, steps=10):
        """
        Change the background of widget from src_color to dst_color
        in the number of steps specified
        """
        ##log.debug('_merge_colors: %s -> %s' % (src_color, dst_color))

        rs, gs, bs = src_color.red, src_color.green, src_color.blue
        rd, gd, bd = dst_color.red, dst_color.green, dst_color.blue
        rinc = (rd - rs) / float(steps)
        ginc = (gd - gs) / float(steps)
        binc = (bd - bs) / float(steps)
        for dummy in xrange(steps):
            rs += rinc
            gs += ginc
            bs += binc
            col = gtk.gdk.color_parse("#%02X%02X%02X" % (int(rs) >> 8, 
                                                         int(gs) >> 8, 
                                                         int(bs) >> 8))
            self.emit('color-changed', col)
            yield True

        self.emit('done')
        self._background_timeout_id = -1
        self._done = True
        yield False

    def _start_merging(self):
        # If we changed during the delay
        if self._background_timeout_id != -1:
            ##log.debug('_start_merging: Already running')
            return

        ##log.debug('_start_merging: Starting')
        func = self._merge_colors(self._start_color, 
                                  gtk.gdk.color_parse(self.ERROR_COLOR)).next
        self._background_timeout_id = (
            gobject.timeout_add(FadeOut.MERGE_COLORS_DELAY, func))
        self._countdown_timeout_id = -1

    def start(self, color):
        """Schedules a start of the countdown.
        @param color: initial background color
        @returns: True if we could start, False if was already in progress
        """
        if self._background_timeout_id != -1:
            ##log.debug('start: Background change already running')
            return False
        if self._countdown_timeout_id != -1:
            ##log.debug('start: Countdown already running')
            return False
        if self._done:
            ##log.debug('start: Not running, already set')
            return False

        self._start_color = color
        ##log.debug('start: Scheduling')
        self._countdown_timeout_id = gobject.timeout_add(
            FadeOut.COMPLAIN_DELAY, self._start_merging)

        return True

    def stop(self):
        """Stops the fadeout and restores the background color"""
        ##log.debug('Stopping')
        if self._background_timeout_id != -1:
            gobject.source_remove(self._background_timeout_id)
            self._background_timeout_id = -1
        if self._countdown_timeout_id != -1:
            gobject.source_remove(self._countdown_timeout_id)
            self._countdown_timeout_id = -1

        self._widget.update_background(self._start_color)
        self._done = False

if gtk.pygtk_version < (2, 8, 0):
    gobject.type_register(FadeOut)

class Tooltip(gtk.Window):
    """Tooltip for the Icon in the MaskedEntry"""
    
    DEFAULT_DELAY = 500
    BORDER_WIDTH = 4

    def __init__(self, widget):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        # from gtktooltips.c:gtk_tooltips_force_window
        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_name("gtk-tooltips")
        self.set_border_width(Tooltip.BORDER_WIDTH)
        self.connect('expose-event', self._on__expose_event)

        self._label = gtk.Label()
        self.add(self._label)
        self._show_timeout_id = -1

    # from gtktooltips.c:gtk_tooltips_draw_tips
    def _calculate_pos(self, widget):
        screen = widget.get_screen()

        w, h = self.size_request()

        x, y = widget.window.get_origin()

        if widget.flags() & gtk.NO_WINDOW:
            x += widget.allocation.x
            y += widget.allocation.y

        x = screen.get_root_window().get_pointer()[0]
        x -= (w / 2 + Tooltip.BORDER_WIDTH)

        pointer_screen, px, py, _ = screen.get_display().get_pointer()
        if pointer_screen != screen:
            px = x
            py = y

        monitor_num = screen.get_monitor_at_point(px, py)
        monitor = screen.get_monitor_geometry(monitor_num)

        if (x + w) > monitor.x + monitor.width:
            x -= (x + w) - (monitor.x + monitor.width);
        elif x < monitor.x:
            x = monitor.x

        if ((y + h + widget.allocation.height + Tooltip.BORDER_WIDTH) >
            monitor.y + monitor.height):
            y = y - h - Tooltip.BORDER_WIDTH
        else:
            y = y + widget.allocation.height + Tooltip.BORDER_WIDTH

        return x, y

    # from gtktooltips.c:gtk_tooltips_paint_window
    def _on__expose_event(self, window, event):
        w, h = window.size_request()
        window.style.paint_flat_box(window.window, 
                                    gtk.STATE_NORMAL, gtk.SHADOW_OUT, 
                                    None, window, "tooltip", 
                                    0, 0, w, h)
        return False

    def _real_display(self, widget):
        x, y = self._calculate_pos(widget)

        self.move(x, y)
        self.show_all()

    # Public API

    def set_text(self, text):
        self._label.set_text(text)

    def hide(self):
        gtk.Window.hide(self)
        gobject.source_remove(self._show_timeout_id)
        self._show_timeout_id = -1

    def display(self, widget):
        if not self._label.get_text():
            return

        if self._show_timeout_id != -1:
            return

        self._show_timeout_id = gobject.timeout_add(Tooltip.DEFAULT_DELAY, 
                                                    self._real_display, 
                                                    widget)

# This is tricky and contains quite a few hacks:
# An entry contains 2 GdkWindows, one for the background and one for
# the text area. The normal one, on which the (normally white) background
# is drawn can be accessed through entry.window (after realization)
# The other window is the one where the cursor and the text is drawn upon, 
# it's refered to as "text area" inside the GtkEntry code and it is called
# the same here. It can only be accessed through window.get_children()[0], 
# since it's considered private to the entry.
#
# +-------------------------------------+
# |                 (1)                 |  (1) parent widget (grey)
# |+----------------(2)----------------+|
# || |-- /-\  |                        ||  (2) entry.window (white)
# || |-  | |  |(4)  (3)                ||
# || |   \-/  |                        ||  (3) text area (transparent)
# |+-----------------------------------+|
# |-------------------------------------|  (4) cursor, black
# |                                     |
# +-------------------------------------|
#
# So, now we want to put an icon in the edge:
# An earlier approached by Lorzeno drew the icon directly on the text area, 
# which is not desired since if the text is using the whole width of the
# entry the icon will be drawn on top of the text.
# Now what we want to do is to resize the text area and create a
# new window upon which we can draw the icon.
#
# +-------------------------------------+
# |                                     |  (5) icon window
# |+----------------------------++-----+|
# || |-- /-\  |                 ||     ||
# || |-  | |  |                 || (5) ||
# || |   \-/  |                 ||     ||
# |+----------------------------++-----+|
# |-------------------------------------|
# |                                     |
# +-------------------------------------+
#
# When resizing the text area the cursor and text is not moved into the
# correct position, it'll still be off by the width of the icon window
# To fix this we need to call a private function, gtk_entry_recompute, 
# a workaround is to call set_visiblity() which calls recompute()
# internally.
#

class IconEntry(object):
    """
    Helper object for rendering an icon in a GtkEntry
    """

    def __init__(self, entry):
        if not isinstance(entry, gtk.Entry):
            raise TypeError("entry must be a gtk.Entry")
        self._constructed = False
        self._pixbuf = None
        self._pixw = 1
        self._pixh = 1
        self._text_area = None
        self._text_area_pos = (0, 0)
        self._icon_win = None
        self._entry = entry
        self._tooltip = Tooltip(self)
        self._locked = False
        entry.connect('enter-notify-event', 
                      self._on_entry__enter_notify_event)
        entry.connect('leave-notify-event', 
                      self._on_entry__leave_notify_event)
        entry.connect('notify::xalign', 
                      self._on_entry__notify_xalign)
        self._update_position()

    def _on_entry__notify_xalign(self, entry, pspec):
        self._update_position()

    def _on_entry__enter_notify_event(self, entry, event):
        icon_win = self.get_icon_window()
        if event.window != icon_win:
            return

        self._tooltip.display(entry)

    def _on_entry__leave_notify_event(self, entry, event):
        if event.window != self.get_icon_window():
            return

        self._tooltip.hide()

    def set_tooltip(self, text):
        self._tooltip.set_text(text)

    def get_icon_window(self):
        return self._icon_win

    def set_pixbuf(self, pixbuf):
        """
        @param pixbuf: a gdk.Pixbuf or None
        """
        entry = self._entry
        if not isinstance(entry.get_toplevel(), gtk.Window):
            # For widgets in SlaveViews, wait until they're attached
            # to something visible, then set the pixbuf
            entry.connect_object('realize', self.set_pixbuf, pixbuf)
            return

        if pixbuf:
            if not isinstance(pixbuf, gtk.gdk.Pixbuf):
                raise TypeError("pixbuf must be a GdkPixbuf")
        else:
            # Turning of the icon should also restore the background
            entry.modify_base(gtk.STATE_NORMAL, None)
            if not self._pixbuf:
                return
        self._pixbuf = pixbuf

        if pixbuf:
            self._pixw = pixbuf.get_width()
            self._pixh = pixbuf.get_height()
        else:
            self._pixw = self._pixh = 0

        win = self._icon_win
        if not win:
            self.construct()
            win = self._icon_win

        self.resize_windows()

        # XXX: Why?
        if win:
            if not pixbuf:
                win.hide()
            else:
                win.show()

        self._recompute()
        entry.queue_draw()

    def construct(self):
        if self._constructed:
            return

        entry = self._entry
        if not entry.flags() & gtk.REALIZED:
            entry.realize()

        # Hack: Save a reference to the text area, now when its created
        self._text_area = entry.window.get_children()[0]
        self._text_area_pos = self._text_area.get_position()

        # PyGTK should allow default values for most of the values here.
        win = gtk.gdk.Window(entry.window, 
                             self._pixw, self._pixh, 
                             gtk.gdk.WINDOW_CHILD, 
                             (gtk.gdk.ENTER_NOTIFY_MASK |
                              gtk.gdk.LEAVE_NOTIFY_MASK), 
                             gtk.gdk.INPUT_OUTPUT, 
                             'icon window', 
                             0, 0, 
                             entry.get_visual(), 
                             entry.get_colormap(), 
                             gtk.gdk.Cursor(entry.get_display(), gtk.gdk.LEFT_PTR), 
                             '', '', True)
        self._icon_win = win
        win.set_user_data(entry)
        win.set_background(entry.style.base[entry.state])
        self._constructed = True

    def deconstruct(self):
        if self._icon_win:
            # This is broken on PyGTK 2.6.x
            try:
                self._icon_win.set_user_data(None)
            except:
                pass
            # Destroy not needed, called by the GC.
            self._icon_win = None

    def update_background(self, color):
        if self._locked:
            return
        if not self._icon_win:
            return

        self._entry.modify_base(gtk.STATE_NORMAL, color)

        self.draw_pixbuf()

    def get_background(self):
        return self._entry.style.base[gtk.STATE_NORMAL]

    def resize_windows(self):
        if not self._pixbuf:
            return

        icony = iconx = 4

        # Make space for the icon, both windows
        winw = self._entry.window.get_size()[0]
        textw, texth = self._text_area.get_size()
        textw = winw - self._pixw - (iconx + icony)

        if self._pos == gtk.POS_LEFT:
            textx, texty = self._text_area_pos
            textx += iconx + self._pixw

            # FIXME: Why is this needed. Focus padding?
            #        The text jumps without this
            textw -= 2
            self._text_area.move_resize(textx, texty, textw, texth)
            self._recompute()
        elif self._pos == gtk.POS_RIGHT:
            self._text_area.resize(textw, texth)
            iconx += textw

        icon_win = self._icon_win
        # XXX: Why?
        if not icon_win:
            return

        # If the size of the window is large enough, resize and move it
        # Otherwise just move it to the right side of the entry
        if icon_win.get_size() != (self._pixw, self._pixh):
            icon_win.move_resize(iconx, icony, self._pixw, self._pixh)
        else:
            icon_win.move(iconx, icony)

    def draw_pixbuf(self):
        if not self._pixbuf:
            return

        win = self._icon_win
        # XXX: Why?
        if not win:
            return

        # Draw background first
        color = self._entry.style.base_gc[self._entry.state]
        win.draw_rectangle(color, True, 
                           0, 0, self._pixw, self._pixh)

        # If sensitive draw the icon, regardless of the window emitting the
        # event since makes it a bit smoother on resize
        if self._entry.flags() & gtk.SENSITIVE:
            win.draw_pixbuf(None, self._pixbuf, 0, 0, 0, 0, 
                            self._pixw, self._pixh)

    def _update_position(self):
        if self._entry.get_property('xalign') > 0.5:
            self._pos = gtk.POS_LEFT
        else:
            self._pos = gtk.POS_RIGHT

    def _recompute(self):
        # Protect against re-entrancy when inserting text, happens in DateEntry
        if self._locked:
            return

        self._locked = True

        # Hack: This triggers a .recompute() which is private
        visibility = self._entry.get_visibility()
        self._entry.set_visibility(not visibility)
        self._entry.set_visibility(visibility)

        # Another option would be to call insert_text, however it
        # emits the signal ::changed which is not desirable.
        #self._entry.insert_text('')
        
        self._locked = False


(DIRECTION_LEFT, DIRECTION_RIGHT) = (1, -1)

(INPUT_ASCII_LETTER, 
 INPUT_ALPHA, 
 INPUT_ALPHANUMERIC, 
 INPUT_DIGIT) = range(4)

INPUT_FORMATS = {
    '0': INPUT_DIGIT, 
    'L': INPUT_ASCII_LETTER, 
    'A': INPUT_ALPHANUMERIC, 
    'a': INPUT_ALPHANUMERIC, 
    '&': INPUT_ALPHA, 
    }

# Todo list: Other usefull Masks
#  9 - Digit, optional
#  ? - Ascii letter, optional
#  C - Alpha, optional

INPUT_CHAR_MAP = {
    INPUT_ASCII_LETTER:     lambda text: text in string.ascii_letters, 
    INPUT_ALPHA:            unicode.isalpha, 
    INPUT_ALPHANUMERIC:     unicode.isalnum, 
    INPUT_DIGIT:            unicode.isdigit, 
    }

(COL_TEXT, 
 COL_OBJECT) = range(2)

class MaskedEntry(gtk.Entry):
    """
    The MaskedEntry is an Entry subclass with additional features.

    Additional features:
      - Mask, force the input to meet certain requirements
      - IconEntry, allows you to have an icon inside the entry
      - convenience functions for completion
    """
    __gtype_name__ = 'MaskedEntry'

    def __init__(self):
        gtk.Entry.__init__(self)

        self.connect('insert-text', self._on_insert_text)
        self.connect('delete-text', self._on_delete_text)
        self.connect_after('grab-focus', self._after_grab_focus)

        self.connect('changed', self._on_changed)

        self.connect('focus', self._on_focus)
        self.connect('focus-out-event', self._on_focus_out_event)
        self.connect('move-cursor', self._on_move_cursor)
        self.connect('button-press-event', self._on_button_press_event)
        self.connect('notify::cursor-position', 
                     self._on_notify_cursor_position)

        self._completion = None
        self._exact_completion = False
        self._block_changed = False
        self._icon = IconEntry(self)

        # List of validators
        #  str -> static characters
        #  int -> dynamic, according to constants above
        self._mask_validators = []
        self._mask = None
        # Fields defined by mask
        # each item is a tuble, containing the begining and the end of the
        # field in the text
        self._mask_fields = []
        self._current_field = -1
        self._pos = 0
        self._selecting = False

        self._block_insert = False
        self._block_delete = False

    # Virtual methods, note do_size_alloc needs gtk 2.9 +
    def do_size_allocate(self, allocation):
        gtk.Entry.do_size_allocate(self, allocation)

        if self.flags() & gtk.REALIZED:
            self._icon.resize_windows()

    def do_expose_event(self, event):
        gtk.Entry.do_expose_event(self, event)

        if event.window == self.window:
            self._icon.draw_pixbuf()

    def do_realize(self):
        gtk.Entry.do_realize(self)
        self._icon.construct()

    def do_unrealize(self):
        self._icon.deconstruct()
        gtk.Entry.do_unrealize(self)

    # Mask & Fields

    def set_mask(self, mask):
        """
        Set the mask of the Entry.
        
        Supported format characters are:
          - '0' digit
          - 'L' ascii letter (a-z and A-Z)
          - '&' alphabet, honors the locale
          - 'a' alphanumeric, honors the locale
          - 'A' alphanumeric, honors the locale

        This is similar to MaskedTextBox: 
        U{http://msdn2.microsoft.com/en-us/library/system.windows.forms.maskedtextbox.mask(VS.80).aspx}

        Example mask for a ISO-8601 date
        >>> entry.set_mask('0000-00-00')

        @param mask: the mask to set
        """
        if not mask:
            self.modify_font(pango.FontDescription("sans"))
            self._mask = mask
            return

        # First, reset
        self._mask_validators = []
        self._mask_fields = []
        self._current_field = -1

        mask = unicode(mask)
        input_length = len(mask)
        lenght = 0
        pos = 0
        field_begin = 0
        field_end = 0
        while True:
            if pos >= input_length:
                break
            if mask[pos] in INPUT_FORMATS:
                self._mask_validators += [INPUT_FORMATS[mask[pos]]]
                field_end += 1
            else:
                self._mask_validators.append(mask[pos])
                if field_begin != field_end:
                    self._mask_fields.append((field_begin, field_end))
                field_end += 1
                field_begin = field_end
            pos += 1

        self._mask_fields.append((field_begin, field_end))
        self.modify_font(pango.FontDescription("monospace"))

        self._really_delete_text(0, -1)
        self._insert_mask(0, input_length)
        self._mask = mask

    def get_mask(self):
        """
        @returns: the mask
        """
        return self._mask

    def get_field_text(self, field):
        if not self._mask:
            raise MaskError("a mask must be set before calling get_field_text")
        #assert self._mask
        text = self.get_text()
        start, end = self._mask_fields[field]
        return text[start: end].strip()

    def get_fields(self):
        """
        Get the fields assosiated with the entry.
        A field is dynamic content separated by static.
        For example, the format string 000-000 has two fields
        separated by a dash.
        if a field is empty it'll return an empty string
        otherwise it'll include the content

        @returns: fields
        @rtype: list of strings
        """
        if not self._mask:
            raise MaskError("a mask must be set before calling get_fields")
        #assert self._mask

        fields = []

        text = unicode(self.get_text())
        for start, end in self._mask_fields:
            fields.append(text[start:end].strip())

        return fields

    def get_empty_mask(self, start=None, end=None):
        """
        Get the empty mask between start and end

        @param start:
        @param end:
        @returns: mask
        @rtype: string
        """

        if start is None:
            start = 0
        if end is None:
            end = len(self._mask_validators)

        s = ''
        for validator in self._mask_validators[start:end]:
            if isinstance(validator, int):
                s += ' '
            elif isinstance(validator, unicode):
                s += validator
            else:
                raise AssertionError
        return s

    def get_field_pos(self, field):
        """
        Get the position at the specified field.
        """
        if field >= len(self._mask_fields):
            return None

        start, end = self._mask_fields[field]

        return start

    def _get_field_ideal_pos(self, field):
        start, end = self._mask_fields[field]
        text = self.get_field_text(field)
        pos = start+len(text)
        return pos

    def get_field(self):
        if self._current_field >= 0:
            return self._current_field
        else:
            return None

    def set_field(self, field, select=False):
        if field >= len(self._mask_fields):
            return

        pos = self._get_field_ideal_pos(field)
        self.set_position(pos)

        if select:
            field_text = self.get_field_text(field)
            start, end = self._mask_fields[field]
            self.select_region(start, pos)

        self._current_field = field

    def get_field_length(self, field):
        if 0 <= field < len(self._mask_fields):
            start, end = self._mask_fields[field]
            return end - start

    def _shift_text(self, start, end, direction=DIRECTION_LEFT, 
                    positions=1):
        """
        Shift the text, to the right or left, n positions. Note that this
        does not change the entry text. It returns the shifted text.

        @param start:
        @param end:
        @param direction:   DIRECTION_LEFT or DIRECTION_RIGHT
        @param positions:   the number of positions to shift.

        @return:        returns the text between start and end, shifted to
                        the direction provided.
        """
        text = self.get_text()
        new_text = ''
        validators = self._mask_validators

        if direction == DIRECTION_LEFT:
            i = start
        else:
            i = end - 1

        # When shifting a text, we wanna keep the static chars where they
        # are, and move the non-static chars to the right position.
        while start <= i < end:
            if isinstance(validators[i], int):
                # Non-static char shoud be here. Get the next one (depending
                # on the direction, and the number of positions to skip.)
                #
                # When shifting left, the next char will be on the right, 
                # so, it will be appended, to the new text.
                # Otherwise, when shifting right, the char will be
                # prepended.
                next_pos = self._get_next_non_static_char_pos(i, direction, 
                                                              positions-1)

                # If its outside the bounds of the region, ignore it.
                if not start <= next_pos <= end:
                    next_pos = None

                if next_pos is not None:
                    if direction == DIRECTION_LEFT:
                        new_text = new_text + text[next_pos]
                    else:
                        new_text = text[next_pos] + new_text
                else:
                    if direction == DIRECTION_LEFT:
                        new_text = new_text + ' '
                    else:
                        new_text = ' ' + new_text

            else:
                # Keep the static char where it is.
                if direction == DIRECTION_LEFT:
                    new_text = new_text + text[i]
                else:
                    new_text = text[i] + new_text
            i += direction

        return new_text

    def _get_next_non_static_char_pos(self, pos, direction=DIRECTION_LEFT, 
                                      skip=0):
        """
        Get next non-static char position, skiping some chars, if necessary.
        @param skip:        skip first n chars
        @param direction:   direction of the search.
        """
        text = self.get_text()
        validators = self._mask_validators
        i = pos+direction+skip
        while 0 <= i < len(text):
            if isinstance(validators[i], int):
                return i
            i += direction

        return None

    def _get_field_at_pos(self, pos, dir=None):
        """
        Return the field index at position pos.
        """
        for p in self._mask_fields:
            if p[0] <= pos <= p[1]:
                return self._mask_fields.index(p)

        return None

    def set_exact_completion(self, value):
        """
        Enable exact entry completion.
        Exact means it needs to start with the value typed
        and the case needs to be correct.

        @param value: enable exact completion
        @type value:  boolean
        """

        self._exact_completion = value
        if value:
            match_func = self._completion_exact_match_func
        else:
            match_func = self._completion_normal_match_func
        completion = self._get_completion()
        completion.set_match_func(match_func)

    def is_empty(self):
        text = self.get_text()
        if self._mask:
            empty = self.get_empty_mask()
        else:
            empty = ''

        return text == empty

    # Private

    def _really_delete_text(self, start, end):
        # A variant of delete_text() that never is blocked by us
        self._block_delete = True
        self.delete_text(start, end)
        self._block_delete = False

    def _really_insert_text(self, text, position):
        # A variant of insert_text() that never is blocked by us
        self._block_insert = True
        self.insert_text(text, position)
        self._block_insert = False

    def _insert_mask(self, start, end):
        text = self.get_empty_mask(start, end)
        self._really_insert_text(text, position=start)

    def _confirms_to_mask(self, position, text):
        validators = self._mask_validators
        if position < 0 or position >= len(validators):
            return False

        validator = validators[position]
        if isinstance(validator, int):
            if not INPUT_CHAR_MAP[validator](text):
                return False
        if isinstance(validator, unicode):
            if validator == text:
                return True
            return False

        return True

    def _get_completion(self):
        # Check so we have completion enabled, not this does not
        # depend on the property, the user can manually override it, 
        # as long as there is a completion object set
        completion = self.get_completion()
        if completion:
            return completion

        completion = gtk.EntryCompletion()
        self.set_completion(completion)
        return completion

    def get_completion(self):
        return self._completion

    def set_completion(self, completion):
        gtk.Entry.set_completion(self, completion)
        # FIXME objects not supported yet, should it be at all?
        #completion.set_model(gtk.ListStore(str, object))
        completion.set_model(gtk.ListStore(gobject.TYPE_STRING))
        completion.set_text_column(0)
        #completion.connect("match-selected", 
                           #self._on_completion__match_selected)

        self._completion = gtk.Entry.get_completion(self)
        self.set_exact_completion(self._exact_completion)
        return

    def set_completion_mode(self, popup=None, inline=None):
        """
        Set the way how completion is presented.
        
        @param popup: enable completion in popup window
        @type popup: boolean
        @param inline: enable inline completion
        @type inline: boolean
        """
        completion = self._get_completion()
        if popup is not None:
            completion.set_popup_completion(popup)
        if inline is not None:
            completion.set_inline_completion(inline)
            
    def _completion_exact_match_func(self, completion, key, iter):
        model = completion.get_model()
        if not len(model):
            return

        content = model[iter][COL_TEXT]
        return content.startswith(self.get_text())

    def _completion_normal_match_func(self, completion, key, iter):
        model = completion.get_model()
        if not len(model):
            return

        content = model[iter][COL_TEXT].lower()
        return key.lower() in content

    def _on_completion__match_selected(self, completion, model, iter):
        if not len(model):
            return

        # this updates current_object and triggers content-changed
        self.set_text(model[iter][COL_TEXT])
        self.set_position(-1)
        # FIXME: Enable this at some point
        #self.activate()

    def _appers_later(self, char, start):
        """
        Check if a char appers later on the mask. If it does, return
        the field it appers at. returns False otherwise.
        """
        validators = self._mask_validators
        i = start
        while i < len(validators):
            if self._mask_validators[i] == char:
                field = self._get_field_at_pos(i)
                if field is None:
                    return False

                return field

            i += 1

        return False

    def _can_insert_at_pos(self, new, pos):
        """
        Check if a chararcter can be inserted at some position

        @param new: The char that wants to be inserted.
        @param pos: The position where it wants to be inserted.

        @return: Returns None if it can be inserted. If it cannot be, 
                 return the next position where it can be successfuly
                 inserted.
        """
        validators = self._mask_validators

        # Do not let insert if the field is full
        field = self._get_field_at_pos(pos)
        if field is not None:
            text = self.get_field_text(field)
            length = self.get_field_length(field)
            if len(text) == length:
                gtk.gdk.beep()
                return pos

        # If the char confirms to the mask, but is a static char, return the
        # position after that static char.
        if (self._confirms_to_mask(pos, new) and
            not isinstance(validators[pos], int)):
            return pos+1

        # If does not confirms to mask:
        #  - Check if the char the user just tried to enter appers later.
        #  - If it does, Jump to the start of the field after that
        if not self._confirms_to_mask(pos, new):
            field = self._appers_later(new, pos)
            if field is not False:
                pos = self.get_field_pos(field+1)
                if pos is not None:
                    gobject.idle_add(self.set_position, pos)
            return pos

        return None

#   When inserting new text, supose, the entry, at some time is like this, 
#   ahd the user presses '0', for instance:
#   --------------------------------
#   | ( 1 2 )   3 4 5   - 6 7 8 9  |
#   --------------------------------
#              ^ ^     ^
#              S P     E
#
#   S - start of the field (start)
#   E - end of the field (end)
#   P - pos - where the new text is being inserted. (pos)
#
#   So, the new text will be:
#
#     the old text, from 0 until P
#   + the new text
#   + the old text, from P until the end of the field, shifted to the
#     right
#   + the old text, from the end of the field, to the end of the text.
#
#   After inserting, the text will be this:
#   --------------------------------
#   | ( 1 2 )   3 0 4 5 - 6 7 8 9  |
#   --------------------------------
#              ^   ^   ^
#              S   P   E
#

    def _insert_at_pos(self, text, new, pos):
        """
        Inserts the character at the give position in text. Note that the
        insertion won't be applied to the entry, but to the text provided.

        @param text:    Text that it will be inserted into.
        @param new:     New text to insert.
        @param pos:     Positon to insert at

        @return:    Returns a tuple, with the position after the insetion
                    and the new text.
        """
        field = self._get_field_at_pos(pos)
        length = len(new)
        new_pos = pos
        start, end = self._mask_fields[field]

        # Shift Right
        new_text = (text[:pos] + new +
                    self._shift_text(pos, end, DIRECTION_RIGHT)[1:] +
                    text[end:])

        # Overwrite Right
#        new_text = (text[:pos] + new +
#                    text[pos+length:end]+
#                    text[end:])
        new_pos = pos+1
        gobject.idle_add(self.set_position, new_pos)

        # If the field is full, jump to the next field
        if len(self.get_field_text(field)) == self.get_field_length(field)-1:
            gobject.idle_add(self.set_field, field+1, True)
            self.set_field(field+1)

        return new_pos, new_text

    # Callbacks
    def _on_insert_text(self, editable, new, length, position):
        if not self._mask or self._block_insert:
            return
        new = unicode(new)
        pos = self.get_position()

        self.stop_emission('insert-text')

        text = self.get_text()
        # Insert one char at a time
        for c in new:
            _pos = self._can_insert_at_pos(c, pos)
            if _pos is None:
                pos, text = self._insert_at_pos(text, c, pos)
            else:
                pos = _pos

        # Change the text with the new text.
        self._block_changed = True
        self._really_delete_text(0, -1)
        self._block_changed = False

        self._really_insert_text(text, 0)

#   When deleting some text, supose, the entry, at some time is like this:
#   --------------------------------
#   | ( 1 2 )   3 4 5 6 - 7 8 9 0  |
#   --------------------------------
#              ^ ^ ^   ^
#              S s e   E
#
#   S - start of the field (_start)
#   E - end of the field (_end)
#   s - start of the text being deleted (start)
#   e - end of the text being deleted (end)
#
#   end - start -> the number of characters being deleted.
#
#   So, the new text will be:
#
#     the old text, from 0 until the start of the text being deleted.
#   + the old text, from the start of where the text is being deleted, until
#     the end of the field, shifted to the left, end-start positions
#   + the old text, from the end of the field, to the end of the text.
#
#   So, after the text is deleted, the entry will look like this:
#
#   --------------------------------
#   | ( 1 2 )   3 5 6   - 7 8 9 0  |
#   --------------------------------
#                ^
#                P
#
#   P = the position of the cursor after the deletion, witch is equal to
#   start (s at the previous ilustration)

    def _on_delete_text(self, editable, start, end):
        if not self._mask or self._block_delete:
            return

        self.stop_emission('delete-text')

        pos = self.get_position()
        # Trying to delete an static char. Delete the char before that
        if (0 < start < len(self._mask_validators)
            and not isinstance(self._mask_validators[start], int)
            and pos != start):
            self._on_delete_text(editable, start-1, start)
            return

        field = self._get_field_at_pos(end-1)
        # Outside a field. Cannot delete.
        if field is None:
            self.set_position(end-1)
            return
        _start, _end = self._mask_fields[field]

        # Deleting from outside the bounds of the field.
        if start < _start or end > _end:
            _start, _end = start, end

        # Change the text
        text = self.get_text()

        # Shift Left
        new_text = (text[:start] +
                    self._shift_text(start, _end, DIRECTION_LEFT, 
                                     end-start) +
                    text[_end:])

        # Overwrite Left
#        empty_mask = self.get_empty_mask()
#        new_text = (text[:_start] +
#                    text[_start:start] +
#                    empty_mask[start:start+(end-start)] +
#                    text[start+(end-start):_end] +
#                    text[_end:])

        new_pos = start

        self._block_changed = True
        self._really_delete_text(0, -1)
        self._block_changed = False
        self._really_insert_text(new_text, 0)

        # Position the cursor on the right place.
        self.set_position(new_pos)

        if self.is_empty():
            pos = self.get_field_pos(0)
            self.set_position(pos)

    def _after_grab_focus(self, widget):
        # The text is selectet in grab-focus, so this needs to be done after
        # that:
        if self.is_empty():
            if self._mask:
                self.set_field(0)
            else:
                self.set_position(0)

    def _on_focus(self, widget, direction):
        if not self._mask:
            return

        if (direction == gtk.DIR_TAB_FORWARD or
            direction == gtk.DIR_DOWN):
            inc = 1
        if (direction == gtk.DIR_TAB_BACKWARD or
            direction == gtk.DIR_UP):
            inc = -1

        field = self._current_field

        field += inc
        # Leaving the entry
        if field == len(self._mask_fields) or field == -1:
            self.select_region(0, 0)
            self._current_field = -1
            return False

        if field < 0:
            field = len(self._mask_fields)-1

        # grab_focus changes the selection, so we need to grab_focus before
        # making the selection.
        self.grab_focus()
        self.set_field(field, select=True)

        return True

    def _on_notify_cursor_position(self, widget, pspec):
        if not self._mask:
            return

        if not self.is_focus():
            return

        if self._selecting:
            return

        pos = self.get_position()
        field = self._get_field_at_pos(pos)

        if pos == 0:
            self.set_position(self.get_field_pos(0))
            return

        text = self.get_text()
        field = self._get_field_at_pos(pos)

        # Humm, the pos is not inside any field. Get the next pos inside
        # some field, depending on the direction that the cursor is
        # moving
        diff = pos - self._pos
        _field = field
        while _field is None and (len(text) > pos > 0) and diff:
            pos += diff
            _field = self._get_field_at_pos(pos)
            self._pos = pos

        if field is None:
            self.set_position(self._pos)
        else:
            self._current_field = field
            self._pos = pos

    def _on_changed(self, widget):
        if self._block_changed:
            self.stop_emission('changed')

    def _on_focus_out_event(self, widget, event):
        if not self._mask:
            return

        self._current_field = -1

    def _on_move_cursor(self, entry, step, count, extend_selection):
        self._selecting = extend_selection

    def _on_button_press_event(self, entry, event ):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            self._selecting = True
        elif event.type == gtk.gdk.BUTTON_RELEASE and event.button == 1:
            self._selecting = True

    # IconEntry

    def set_tooltip(self, text):
        self._icon.set_tooltip(text)

    def set_pixbuf(self, pixbuf):
        self._icon.set_pixbuf(pixbuf)

    def set_stock(self, stock_name):
        pixbuf = self.render_icon(stock_name, gtk.ICON_SIZE_MENU)
        self._icon.set_pixbuf(pixbuf)

    def update_background(self, color):
        self._icon.update_background(color)

    def get_background(self):
        return self._icon.get_background()

    def get_icon_window(self):
        return self._icon.get_icon_window()

    # gtk.EntryCompletion convenience function
    
    def prefill(self, itemdata, sort=False):
        if not isinstance(itemdata, (list, tuple)):
            raise TypeError("'data' parameter must be a list or tuple of item "
                            "descriptions, found %s") % type(itemdata)

        completion = self._get_completion()
        model = completion.get_model()

        if len(itemdata) == 0:
            model.clear()
            return

        values = {}
        if sort:
            itemdata.sort()

        for item in itemdata:
            if item in values:
                raise KeyError("Tried to insert duplicate value "
                                   "%r into the entry" % item)
            else:
                values[item] = None

            model.append((item, ))

if gtk.pygtk_version < (2, 8, 0):
    gobject.type_register(MaskedEntry)

#number = (int, float, long)

VALIDATION_ICON_WIDTH = 16
MANDATORY_ICON = INFO_ICON
ERROR_ICON = gtk.STOCK_STOP

class ValidatableMaskedEntry(MaskedEntry):
    """It extends the MaskedEntry with validation feature.

    Merged from Kiwi's ValidatableProxyWidgetMixin and ProxyEntry.
    To provide custom validation connect to the 'validate' signal
    of the instance.
    """

    __gtype_name__ = 'ValidatableMaskedEntry'

    __gsignals__ = {
        'content-changed': (gobject.SIGNAL_RUN_FIRST, 
                            gobject.TYPE_NONE, 
                            ()), 
        'validation-changed': (gobject.SIGNAL_RUN_FIRST, 
                               gobject.TYPE_NONE, 
                               (gobject.TYPE_BOOLEAN, )), 
        'validate': (gobject.SIGNAL_RUN_LAST, 
                     gobject.TYPE_PYOBJECT, 
                     (gobject.TYPE_PYOBJECT, )), 
        'changed': 'override', 
    }

    __gproperties__ = {
        'data-type': (gobject.TYPE_PYOBJECT, 
                       'Data Type of the widget', 
                       'Type object', 
                       gobject.PARAM_READWRITE), 
        'mandatory': (gobject.TYPE_BOOLEAN, 
                      'Mandatory', 
                      'Mandatory', 
                      False, 
                      gobject.PARAM_READWRITE), 
    }
                            
    # FIXME put the data type support back
    #allowed_data_types = (basestring, datetime.date, datetime.time, 
                          #datetime.datetime, object) + number

    def __init__(self, data_type=None, err_color = "#ffd5d5", error_icon=ERROR_ICON):
        self.data_type = None
        self.mandatory = False
        self.error_icon = error_icon

        MaskedEntry.__init__(self)
        
        self._block_changed = False
        self._valid = True
        self._def_error_msg = None
        self._fade = FadeOut(self, err_color)
        self._fade.connect('color-changed', self._on_fadeout__color_changed)
        
        # FIXME put data type support back
        #self.set_property('data-type', data_type)

    # Virtual methods
    def do_changed(self):
        if self._block_changed:
            self.emit_stop_by_name('changed')
            return
        self.emit('content-changed')
        self.validate()

    def do_get_property(self, prop):
        """Return the gproperty's value."""
        
        if prop.name == 'data-type':
            return self.data_type
        elif prop.name == 'mandatory':
            return self.mandatory
        else:
            raise AttributeError, 'unknown property %s' % prop.name

    def do_set_property(self, prop, value):
        """Set the property of writable properties."""
        
        if prop.name == 'data-type':
            if value is None:
                self.data_type = value
                return
        
            # FIXME put the data type support back
            #if not issubclass(value, self.allowed_data_types):
                #raise TypeError(
                    #"%s only accept %s types, not %r"
                    #% (self, 
                       #' or '.join([t.__name__ for t in self.allowed_data_types]), 
                       #value))
            self.data_type = value
        elif prop.name == 'mandatory':
            self.mandatory = value
        else:
            raise AttributeError, 'unknown or read only property %s' % prop.name

    # Public API

    def set_default_error_msg(self, text):
        """
        Set default message for validation error.
        
        Default error message for an instance is useful when completion is
        used, because this case custom validation is not called.
                
        @param text: can contain one and only one '%s', where the actual value
        of the Entry will be inserted.
        @type text: str
        """
        if not isinstance(text, str):
            raise TypeError("text must be a string")
            
        self._def_error_msg = text
        
    def is_valid(self):
        """
        @returns: True if the widget is in validated state
        """
        return self._valid

    def validate(self, force=False):
        """Checks if the data is valid.
        Validates data-type and custom validation.

        @param force: if True, force validation
        @returns:     validated data or ValueUnset if it failed
        """

        # If we're not visible or sensitive return a blank value, except
        # when forcing the validation
        if not force and (not self.get_property('visible') or
                          not self.get_property('sensitive')):
            return None

        try:
            text = self.get_text()
            ##log.debug('Read %r for %s' %  (data, self.model_attribute))

            # check if we should draw the mandatory icon
            # this need to be done before any data conversion because we
            # we don't want to end drawing two icons
            if self.mandatory and self.is_empty():
                self.set_blank()
                return None
            else:
                if self._completion:
                    for row in self.get_completion().get_model():
                        if row[COL_TEXT] == text:
                            break
                    else:
                        if text:
                            raise ValidationError()
                else:
                    if not self.is_empty():
                        # this signal calls the custom validation method
                        # of the instance and gets the exception (if any).
                        error = self.emit("validate", text)
                        if error:
                            raise error

            self.set_valid()
            return text
        except ValidationError, e:
            self.set_invalid(str(e))
            return None

    def set_valid(self):
        """Change the validation state to valid, which will remove icons and
        reset the background color
        """

        ##log.debug('Setting state for %s to VALID' % self.model_attribute)
        self._set_valid_state(True)

        self._fade.stop()
        self.set_pixbuf(None)

    def set_invalid(self, text=None, fade=True):
        """Change the validation state to invalid.
        @param text: text of tooltip of None
        @param fade: if we should fade the background
        """
        ##log.debug('Setting state for %s to INVALID' % self.model_attribute)

        self._set_valid_state(False)

        generic_text = _("'%s' is not a valid value "
                         "for this field") % self.get_text()
        
        # If there is no error text, let's try with the default or
        # fall back to a generic one
        if not text:
            text = self._def_error_msg
        if not text:
            text = generic_text
            
        try:
            text.index('%s')
            text = text % self.get_text()
        except TypeError:
            # if text contains '%s' more than once
            log.error('There must be only one instance of "%s"'
                      ' in validation error message')
            # fall back to a generic one so the error icon still have a tooltip
            text = generic_text
        except ValueError:
            # if text does not contain '%s'
            pass

        self.set_tooltip(text)

        if not fade:
            if self.error_icon:
                self.set_stock(self.error_icon)
            self.update_background(gtk.gdk.color_parse(self._fade.ERROR_COLOR))
            return

        # When the fading animation is finished, set the error icon
        # We don't need to check if the state is valid, since stop()
        # (which removes this timeout) is called as soon as the user
        # types valid data.
        def done(fadeout, c):
            if self.error_icon:
                self.set_stock(self.error_icon)
            self.queue_draw()
            fadeout.disconnect(c.signal_id)

        class SignalContainer:
            pass
        c = SignalContainer()
        c.signal_id = self._fade.connect('done', done, c)

        if self._fade.start(self.get_background()):
            self.set_pixbuf(None)

    def set_blank(self):
        """Change the validation state to blank state, this only applies
        for mandatory widgets, draw an icon and set a tooltip"""

        ##log.debug('Setting state for %s to BLANK' % self.model_attribute)

        if self.mandatory:
            self.set_stock(MANDATORY_ICON)
            self.queue_draw()
            self.set_tooltip(_('This field is mandatory'))
            self._fade.stop()
            valid = False
        else:
            valid = True

        self._set_valid_state(valid)

    def set_text(self, text):
        """
        Set the text of the entry

        @param text:
        """

        # If content isn't empty set_text emitts changed twice.
        # Protect content-changed from being updated and issue
        # a manual emission afterwards
        self._block_changed = True
        MaskedEntry.set_text(self, text)
        self._block_changed = False
        self.emit('content-changed')

        self.set_position(-1)

    # Private

    def _set_valid_state(self, state):
        """Updates the validation state and emits a signal if it changed"""

        if self._valid == state:
            return

        self.emit('validation-changed', state)
        self._valid = state

    # Callbacks

    def _on_fadeout__color_changed(self, fadeout, color):
        self.update_background(color)

if gtk.pygtk_version < (2, 8, 0):
    gobject.type_register(ValidatableMaskedEntry)

def main(args):
    from DateHandler import parser
    
    def on_validate(widget, text):
        myDate = parser.parse(text)
        if not myDate.is_regular():
            return ValidationError("'%s' is not a valid date value")
        
    win = gtk.Window()
    win.set_title('ValidatableMaskedEntry test window')
    win.set_position(gtk.WIN_POS_CENTER)
    def cb(window, event):
        gtk.main_quit()
    win.connect('delete-event', cb)

    vbox = gtk.VBox()
    win.add(vbox)
    
    label = gtk.Label('Pre-filled entry validated against the given list:')
    vbox.pack_start(label)
    
    widget1 = ValidatableMaskedEntry(str)
    widget1.set_completion_mode(inline=True, popup=False)
    widget1.set_default_error_msg("'%s' is not a default Event")
    #widget1.set_default_error_msg(widget1)
    widget1.prefill(('Birth', 'Death', 'Conseption'))
    #widget1.set_exact_completion(True)
    vbox.pack_start(widget1, fill=False)
    
    label = gtk.Label('Mandatory masked entry validated against user function:')
    vbox.pack_start(label)
    
    #widget2 = ValidatableMaskedEntry(str, "#e0e0e0", error_icon=None)
    widget2 = ValidatableMaskedEntry()
    widget2.set_mask('00/00/0000')
    widget2.connect('validate', on_validate)
    widget2.mandatory = True
    vbox.pack_start(widget2, fill=False)
    
    # == Statusbar testing ====================================================
    statusbar = Statusbar()
    vbox.pack_end(statusbar, False)
    
    statusbar.push(1, "This is my statusbar...")
    
    my_statusbar = statusbar.insert(min_width=24)
    statusbar.push(1, "Testing status bar width", my_statusbar)
    
    yet_another_statusbar = statusbar.insert(1, 11)
    statusbar.push(1, "A short one", yet_another_statusbar)

    last_statusbar = statusbar.insert(min_width=41, ralign=True)
    statusbar.push(1, "The last statusbar has always fixed width", 
                   last_statusbar)
    
    # =========================================================================

    win.show_all()
    gtk.main()

if __name__ == '__main__':
    import sys
    # fall back to root logger for testing
    log = logging
    sys.exit(main(sys.argv))
