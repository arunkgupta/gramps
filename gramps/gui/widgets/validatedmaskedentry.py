#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007-2008  Zsolt Foldvari
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

__all__ = ["MaskedEntry", "ValidatableMaskedEntry"]

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
from gramps.gen.ggettext import gettext as _
import string

import logging
_LOG = logging.getLogger(".widgets.validatedmaskedentry")

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GdkPixbuf
from gi.repository import Pango

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from gramps.gen.errors import MaskError, ValidationError, WindowActiveError
from .undoableentry import UndoableEntry

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
# STOCK_INFO was added only in Gtk 2.8
try:
    INFO_ICON = Gtk.STOCK_INFO
except AttributeError:
    INFO_ICON = Gtk.STOCK_DIALOG_INFO

#============================================================================
#
# MaskedEntry and ValidatableMaskedEntry copied and merged from the Kiwi
# project's ValidatableProxyWidgetMixin, KiwiEntry and ProxyEntry.
#
# http://www.async.com.br/projects/kiwi
#
#============================================================================

class FadeOut(GObject.GObject):
    """I am a helper class to draw the fading effect of the background
    Call my methods start() and stop() to control the fading.
    """
    __gsignals__ = {
        'done': (GObject.SignalFlags.RUN_FIRST, 
                 None, 
                 ()), 
        'color-changed': (GObject.SignalFlags.RUN_FIRST, 
                          None, 
                          (Gdk.Color, )), 
    }
    
    # How long time it'll take before we start (in ms)
    COMPLAIN_DELAY = 500

    MERGE_COLORS_DELAY = 100

    def __init__(self, widget, err_color = "#ffd5d5"):
        GObject.GObject.__init__(self)
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
        ##_LOG.debug('_merge_colors: %s -> %s' % (src_color, dst_color))

        rs, gs, bs = src_color.red, src_color.green, src_color.blue
        rd, gd, bd = dst_color.red, dst_color.green, dst_color.blue
        rinc = (rd - rs) / float(steps)
        ginc = (gd - gs) / float(steps)
        binc = (bd - bs) / float(steps)
        for dummy in xrange(steps):
            rs += rinc
            gs += ginc
            bs += binc
            col = Gdk.color_parse("#%02X%02X%02X" % (int(rs) >> 8, 
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
            ##_LOG.debug('_start_merging: Already running')
            return

        ##_LOG.debug('_start_merging: Starting')
        func = self._merge_colors(self._start_color, 
                                  Gdk.color_parse(self.ERROR_COLOR)).next
        self._background_timeout_id = (
            GObject.timeout_add(FadeOut.MERGE_COLORS_DELAY, func))
        self._countdown_timeout_id = -1

    def start(self, color):
        """Schedules a start of the countdown.
        @param color: initial background color
        @returns: True if we could start, False if was already in progress
        """
        if self._background_timeout_id != -1:
            ##_LOG.debug('start: Background change already running')
            return False
        if self._countdown_timeout_id != -1:
            ##_LOG.debug('start: Countdown already running')
            return False
        if self._done:
            ##_LOG.debug('start: Not running, already set')
            return False

        self._start_color = color
        ##_LOG.debug('start: Scheduling')
        self._countdown_timeout_id = GObject.timeout_add(
            FadeOut.COMPLAIN_DELAY, self._start_merging)

        return True

    def stop(self):
        """Stops the fadeout and restores the background color"""
        ##_LOG.debug('Stopping')
        if self._background_timeout_id != -1:
            GObject.source_remove(self._background_timeout_id)
            self._background_timeout_id = -1
        if self._countdown_timeout_id != -1:
            GObject.source_remove(self._countdown_timeout_id)
            self._countdown_timeout_id = -1

        self._widget.update_background(self._start_color)
        self._done = False

class Tooltip(Gtk.Window):
    """Tooltip for the Icon in the MaskedEntry"""
    
    DEFAULT_DELAY = 500
    BORDER_WIDTH = 4

    def __init__(self, widget):
        GObject.GObject.__init__(self, type=Gtk.WindowType.POPUP)
        # from gtktooltips.c:gtk_tooltips_force_window
        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_name("gtk-tooltips")
        self.set_border_width(Tooltip.BORDER_WIDTH)
        #TODO GTK3: this signal no longer exists. Convert to draw
        self.connect('draw', self._on__draw_event)

        self._label = Gtk.Label()
        self.add(self._label)
        self._show_timeout_id = -1

    # from gtktooltips.c:gtk_tooltips_draw_tips
    def _calculate_pos(self, widget):
        screen = widget.get_screen()

        greq = Gtk.Requisition()
        greq = self.size_request()
        w = greq.width
        h = greq.height

        _, x, y = widget.get_window().get_origin()

        # TODO GTK3 No longer WidgetFlags!
        #if widget.get_state_flags() & Gtk.WidgetFlags.NO_WINDOW:
        x += widget.get_allocation().width
        y += widget.get_allocation().height

        x = screen.get_root_window().get_pointer()[1]
        #TODO GTK3, how: x = screen.get_window().get_device_position()[0]
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

        if ((y + h + widget.get_allocation().height + Tooltip.BORDER_WIDTH) >
            monitor.y + monitor.height):
            y -= h + Tooltip.BORDER_WIDTH
        else:
            y += widget.get_allocation().height + Tooltip.BORDER_WIDTH

        return x, y

    # from gtktooltips.c:gtk_tooltips_paint_window
    def _on__draw_event(self, window, cairo_context):
        #GTK3 TODO, paint_flat_box deprecated !!
        greq = self.size_request()
        w = greq.width
        h = greq.height
        Gtk.render_frame(window.get_style_context(), cairo_context,
            0,0,w,h)
        #window.get_style().paint_flat_box(window.window, 
        #                            Gtk.StateType.NORMAL, Gtk.ShadowType.OUT, 
        #                            None, window, "tooltip", 
        #                            0, 0, w, h)
        return False

    def _real_display(self, widget):
        x, y = self._calculate_pos(widget)

        self.move(x, y)
        self.show_all()

    # Public API

    def set_text(self, text):
        self._label.set_text(text)

    def hide(self):
        Gtk.Window.hide(self)
        GObject.source_remove(self._show_timeout_id)
        self._show_timeout_id = -1

    def display(self, widget):
        if not self._label.get_text():
            return

        if self._show_timeout_id != -1:
            return

        self._show_timeout_id = GObject.timeout_add(Tooltip.DEFAULT_DELAY, 
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
        if not isinstance(entry, Gtk.Entry):
            raise TypeError("entry must be a Gtk.Entry")
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
        @param pixbuf: a GdkPixbuf.Pixbuf or None
        """
        entry = self._entry
        if not isinstance(entry.get_toplevel(), Gtk.Window):
            # For widgets in SlaveViews, wait until they're attached
            # to something visible, then set the pixbuf
            entry.connect_object('realize', self.set_pixbuf, pixbuf)
            return

        if pixbuf:
            if not isinstance(pixbuf, GdkPixbuf.Pixbuf):
                raise TypeError("pixbuf must be a GdkPixbuf")
        else:
            # Turning off the icon should also restore the background
            entry.override_background_color(Gtk.StateType.NORMAL, None)
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
        if not entry.get_realized():
            entry.realize()

        # Hack: Save a reference to the text area, now when its created
        self._text_area = entry.get_window().get_children()[0]
        self._text_area_pos = self._text_area.get_position()

        # PyGTK should allow default values for most of the values here.
        attr = Gdk.WindowAttr()
        attr.width = self._pixw
        attr.height = self._pixh
        attr.x = 0
        attr.y = 0
        attr.cursor = Gdk.Cursor.new_for_display(
                                entry.get_display(), Gdk.CursorType.LEFT_PTR)
        #attr.wmclass_name=''
        #attr.wmclass_class=''
        attr.override_redirect=True
        attr.event_mask = (Gdk.EventMask.ENTER_NOTIFY_MASK |
                              Gdk.EventMask.LEAVE_NOTIFY_MASK)
        # GTK3 We can we not set title?
        #attr.title = 'icon window'
        attr.wclass = Gdk.WindowWindowClass.INPUT_OUTPUT
        attr.window_type = Gdk.WindowType.CHILD
        attr.visual = entry.get_visual()
        attrmask = (
                #Gdk.WindowAttributesType.TITLE |
                Gdk.WindowAttributesType.X |
                Gdk.WindowAttributesType.Y |
                Gdk.WindowAttributesType.CURSOR |
                Gdk.WindowAttributesType.VISUAL |
                Gdk.WindowAttributesType.NOREDIR
                )
        #the window containing the icon image
        self._icon_win = Gdk.Window(entry.get_window(),
                         attr,
                         attrmask)
##                             Gdk.WindowType.CHILD, 
##                             (Gdk.EventMask.ENTER_NOTIFY_MASK |
##                              Gdk.EventMask.LEAVE_NOTIFY_MASK), 
##                             Gdk.WindowWindowClass.INPUT_OUTPUT, 
##                             title='icon window', 
##                             x=0, y=0, 
##                             visual=entry.get_visual(),
##                             #TODO GTK3: is there alternative for:
##                             #colormap=entry.get_colormap(), 
##                             cursor=Gdk.Cursor.new_for_display(
##                                entry.get_display(), Gdk.CursorType.LEFT_PTR), 
##                             wmclass_name='',
##                             wmclass_class='', override_redirect=True)
        self._icon_win.set_user_data(entry)
        #win.set_background(entry.get_style().base[entry.get_state()])
        self._constructed = True

    def deconstruct(self):
        if self._icon_win:
            self._icon_win.set_user_data(None)
            # Destroy not needed, called by the GC.
            # TODO GTK3: we see error:  Gdk-WARNING **: losing last reference to undestroyed window
            # TODO Investigate
            self._icon_win = None

    def update_background(self, color):
        if self._locked:
            return
        if not self._icon_win:
            return

        self.draw_pixbuf()
        
        maxvalcol = 65535.
        if color:
            red = int(color.red/ maxvalcol*255)
            green = int(color.green/ maxvalcol*255)
            blue = int(color.blue/ maxvalcol*255)
            rgba = Gdk.RGBA()
            Gdk.RGBA.parse(rgba, 'rgb(%f,%f,%f)'%(red, green, blue))
            self._entry.override_background_color(Gtk.StateFlags.NORMAL, rgba)
            #GTK 3: workaround, background not changing in themes, use symbolic
            self._entry.override_symbolic_color('bg_color', rgba)
            self._entry.override_symbolic_color('theme_bg_color', rgba)
        else:
            self._entry.override_background_color(Gtk.StateFlags.NORMAL, None)
            self._entry.override_symbolic_color('bg_color', None)
            self._entry.override_symbolic_color('theme_bg_color', None)


    def get_background(self):
        """ Return default background color as a Gdk.Color """
        backcol = self._entry.get_style_context().get_background_color(Gtk.StateType.NORMAL)
        bcol= Gdk.Color.parse('#fff')[1]
        bcol.red = int(backcol.red * 65535)
        bcol.green = int(backcol.green * 65535)
        bcol.blue = int(backcol.blue * 65535)
        return bcol

    def resize_windows(self):
        if not self._pixbuf:
            return

        icony = iconx = 0

        # Make space for the icon, both windows
        # GTK 3 gives for entry the sizes for the entire editor
        geom =self._text_area.get_geometry()
        origx = geom[0]
        origy = geom[1]
        origw = geom[2]
        origh = geom[3]
        textw = origw
        texth = origh
        textw = textw - self._pixw - (iconx + icony)

        if self._pos == Gtk.PositionType.LEFT:
            textx, texty = self._text_area_pos
            textx += iconx + self._pixw

            # FIXME: Why is this needed. Focus padding?
            #        The text jumps without this
            textw -= 2
            self._text_area.move_resize(textx, texty, textw, texth)
            self._recompute()
        elif self._pos == Gtk.PositionType.RIGHT:
            self._text_area.resize(textw, texth)
            iconx += textw

        icon_win = self._icon_win
        # XXX: Why?
        if not icon_win:
            return

        # If the size of the window is large enough, resize and move it
        # Otherwise just move it to the right side of the entry
        if (icon_win.get_width(), icon_win.get_height()) != (self._pixw, self._pixh):
            icon_win.move_resize(origx + origw - self._pixw, icony + origy, 100, 100)
            icon_win.move_resize(origx + origw - self._pixw, icony + origy, self._pixw, self._pixh)
        else:
            icon_win.move(origx + origw - self._pixw, icony + origy)

    def draw_pixbuf(self):
        if not self._pixbuf:
            return

        win = self._icon_win
        # XXX: Why?
        if not win:
            return

        # Draw background first - not needed with cairo!
        ##color = self._entry.get_style_context().get_background_color(
        ##                                    self._entry.get_state())

        # If sensitive draw the icon, regardless of the window emitting the
        # event since makes it a bit smoother on resize
        if self._entry.get_sensitive():
            #GTK 3: we use cairo to draw the pixbuf
            cairo_t = Gdk.cairo_create(win)
            Gdk.cairo_set_source_pixbuf(cairo_t, self._pixbuf, 0, 0)
            cairo_t.new_path()
            cairo_t.move_to (0, 0);
            cairo_t.rel_line_to (win.get_width(), 0);
            cairo_t.rel_line_to (0, win.get_height());
            cairo_t.rel_line_to (-win.get_width(), 0);
            cairo_t.close_path ();
            cairo_t.fill()

    def _update_position(self):
        if self._entry.get_property('xalign') > 0.5:
            self._pos = Gtk.PositionType.LEFT
        else:
            self._pos = Gtk.PositionType.RIGHT

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

# Todo list: Other useful Masks
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

class MaskedEntry(UndoableEntry):
    """
    The MaskedEntry is an Entry subclass with additional features.

    Additional features:
      - Mask, force the input to meet certain requirements
      - IconEntry, allows you to have an icon inside the entry
      - convenience functions for completion
    
    Note: Gramps does not use the mask feature at the moment, so that code
          path is not tested
    """
    __gtype_name__ = 'MaskedEntry'

    def __init__(self):
        UndoableEntry.__init__(self)

        # connect in UndoableEntry:
        #self.connect('insert-text', self._on_insert_text)
        #self.connect('delete-text', self._on_delete_text)
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
        self.in_do_draw = False

    # Virtual methods, note do_size_alloc needs gtk 2.9 +
    def do_size_allocate(self, allocation):
        Gtk.Entry.do_size_allocate(self, allocation)

        if self.get_realized():
            self._icon.resize_windows()

    def do_draw(self, cairo_t):
        Gtk.Entry.do_draw(self, cairo_t)

        if Gtk.cairo_should_draw_window(cairo_t, self.get_window()):
            self._icon.draw_pixbuf()

    def do_realize(self):
        Gtk.Entry.do_realize(self)
        self._icon.construct()

    def do_unrealize(self):
        self._icon.deconstruct()
        Gtk.Entry.do_unrealize(self)

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
            self.modify_font(Pango.FontDescription("sans"))
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
        self.modify_font(Pango.FontDescription("monospace"))

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
        completion.set_match_func(match_func, None)

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

        completion = Gtk.EntryCompletion()
        self.set_completion(completion)
        return completion

    def get_completion(self):
        return self._completion

    def set_completion(self, completion):
        Gtk.Entry.set_completion(self, completion)
        # FIXME objects not supported yet, should it be at all?
        #completion.set_model(Gtk.ListStore(str, object))
        completion.set_model(Gtk.ListStore(GObject.TYPE_STRING))
        completion.set_text_column(0)
        #completion.connect("match-selected", 
                           #self._on_completion__match_selected)

        self._completion = Gtk.Entry.get_completion(self)
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

    def _completion_normal_match_func(self, completion, key, iter, data=None):
        model = completion.get_model()
        if not len(model):
            return

        content = model[iter][COL_TEXT].lower()
        return key.lower() in content

    def _on_completion__match_selected(self, completion, model, iter, data=None):
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
                Gdk.beep()
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
                    GObject.idle_add(self.set_position, pos)
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
        GObject.idle_add(self.set_position, new_pos)

        # If the field is full, jump to the next field
        if len(self.get_field_text(field)) == self.get_field_length(field)-1:
            GObject.idle_add(self.set_field, field+1, True)
            self.set_field(field+1)

        return new_pos, new_text

    # Callbacks
    def _on_insert_text(self, editable, new, length, position):
        if self._block_insert:
            return
        if not self._mask:
            UndoableEntry._on_insert_text(self, editable, new, length, position)
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
        ### mask not used in Gramps, following should work though
        ##UndoableEntry._on_delete_text(self, editable, 0, -1)
        self._block_changed = False

        self._really_insert_text(text, 0)
        ### mask not used in Gramps, following should work though
        ##UndoableEntry._on_insert_text(self, editable, text, len(text),0)

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
        if self._block_delete:
            return
        if not self._mask:
            UndoableEntry._on_delete_text(self, editable, start, end)
            return

        self.stop_emission('delete-text')

        pos = self.get_position()
        # Trying to delete an static char. Delete the char before that
        if (0 < start < len(self._mask_validators)
            and not isinstance(self._mask_validators[start], int)
            and pos != start):
            self._on_delete_text(editable, start-1, start)
            ### mask not used in Gramps, following should work though
            ##UndoableEntry._on_delete_text(self, editable, start-1, start)
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
        ### mask not used in Gramps, following should work though
        ##UndoableEntry._on_delete_text(self, editable, 0, -1)
        self._block_changed = False
        self._really_insert_text(new_text, 0)
        ### mask not used in Gramps, following should work though
        ##UndoableEntry._on_insert_text(self, editable, text, len(text),0)

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

        if (direction == Gtk.DIR_TAB_FORWARD or
            direction == Gtk.DIR_DOWN):
            inc = 1
        if (direction == Gtk.DIR_TAB_BACKWARD or
            direction == Gtk.DIR_UP):
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
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            self._selecting = True
        elif event.type == Gdk.EventType.BUTTON_RELEASE and event.button == 1:
            self._selecting = True

    # IconEntry

    def set_tooltip(self, text):
        self._icon.set_tooltip(text)

    def set_pixbuf(self, pixbuf):
        self._icon.set_pixbuf(pixbuf)

    def set_stock(self, stock_name):
        pixbuf = self.render_icon(stock_name, Gtk.IconSize.MENU)
        self._icon.set_pixbuf(pixbuf)

    def update_background(self, color):
        self._icon.update_background(color)

    def get_background(self):
        return self._icon.get_background()

    def get_icon_window(self):
        return self._icon.get_icon_window()

    # Gtk.EntryCompletion convenience function
    
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

#number = (int, float, long)

VALIDATION_ICON_WIDTH = 16
MANDATORY_ICON = INFO_ICON
ERROR_ICON = Gtk.STOCK_STOP

class ValidatableMaskedEntry(MaskedEntry):
    """It extends the MaskedEntry with validation feature.

    Merged from Kiwi's ValidatableProxyWidgetMixin and ProxyEntry.
    To provide custom validation connect to the 'validate' signal
    of the instance.
    """

    __gtype_name__ = 'ValidatableMaskedEntry'

    __gsignals__ = {
        'content-changed': (GObject.SignalFlags.RUN_FIRST, 
                            None, 
                            ()), 
        'validation-changed': (GObject.SignalFlags.RUN_FIRST, 
                               None, 
                               (GObject.TYPE_BOOLEAN, )), 
        'validate': (GObject.SignalFlags.RUN_LAST, 
                     GObject.TYPE_PYOBJECT, 
                     (GObject.TYPE_PYOBJECT, )), 
        'changed': 'override', 
    }

    __gproperties__ = {
        'data-type': (GObject.TYPE_PYOBJECT, 
                       'Data Type of the widget', 
                       'Type object', 
                       GObject.PARAM_READWRITE), 
        'mandatory': (GObject.TYPE_BOOLEAN, 
                      'Mandatory', 
                      'Mandatory', 
                      False, 
                      GObject.PARAM_READWRITE), 
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
            ##_LOG.debug('Read %r for %s' %  (data, self.model_attribute))

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

        ##_LOG.debug('Setting state for %s to VALID' % self.model_attribute)
        self._set_valid_state(True)

        self._fade.stop()
        self.set_pixbuf(None)

    def set_invalid(self, text=None, fade=True):
        """Change the validation state to invalid.
        @param text: text of tooltip of None
        @param fade: if we should fade the background
        """
        ##_LOG.debug('Setting state for %s to INVALID' % self.model_attribute)

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
            _LOG.error('There must be only one instance of "%s"'
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
            self.update_background(Gdk.color_parse(self._fade.ERROR_COLOR))
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

        class SignalContainer(object):
            pass
        c = SignalContainer()
        c.signal_id = self._fade.connect('done', done, c)

        if self._fade.start(self.get_background()):
            self.set_pixbuf(None)

    def set_blank(self):
        """Change the validation state to blank state, this only applies
        for mandatory widgets, draw an icon and set a tooltip"""

        ##_LOG.debug('Setting state for %s to BLANK' % self.model_attribute)

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


def main(args):
    from gramps.gen.datehandler import parser
    
    def on_validate(widget, text):
        myDate = parser.parse(text)
        if not myDate.is_regular():
            # used on AgeOnDateGramplet
            return ValidationError(_("'%s' is not a valid date value"))
        
    win = Gtk.Window()
    win.set_title('ValidatableMaskedEntry test window')
    win.set_position(Gtk.WindowPosition.CENTER)
    def cb(window, event):
        Gtk.main_quit()
    win.connect('delete-event', cb)

    vbox = Gtk.VBox()
    win.add(vbox)
    
    label = Gtk.Label(label='Pre-filled entry validated against the given list:')
    vbox.pack_start(label, True, True, 0)
    
    widget1 = ValidatableMaskedEntry(str)
    widget1.set_completion_mode(inline=True, popup=False)
    widget1.set_default_error_msg("'%s' is not a default Event")
    #widget1.set_default_error_msg(widget1)
    widget1.prefill(('Birth', 'Death', 'Conseption'))
    #widget1.set_exact_completion(True)
    vbox.pack_start(widget1, True, False, 0)
    
    label = Gtk.Label(label='Mandatory masked entry validated against user function:')
    vbox.pack_start(label, True, True, 0)
    
    #widget2 = ValidatableMaskedEntry(str, "#e0e0e0", error_icon=None)
    widget2 = ValidatableMaskedEntry()
    widget2.set_mask('00/00/0000')
    widget2.connect('validate', on_validate)
    widget2.mandatory = True
    vbox.pack_start(widget2, True, False, 0)
    
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    import sys
    # fall back to root logger for testing
    _LOG = logging
    sys.exit(main(sys.argv))
