#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2005  Donald N. Allingham
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
Date editing module for GRAMPS. 

The DateEdit.DateEdit provides visual feedback to the user via a pixamp
to indicate if the assocated GtkEntry box contains a valid date. Green
means complete and regular date. Yellow means a valid, but not a regular date.
Red means that the date is not valid, and will be viewed as a text string
instead of a date.

The DateEdit.DateEditor provides a dialog in which the date can be 
unambiguously built using UI controls such as menus and spin buttons.
"""

__author__ = "Donald N. Allingham"
__version__ = "$Revision$"

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _
import gc

#-------------------------------------------------------------------------
#
# GNOME modules
#
#-------------------------------------------------------------------------
import gtk
import gtk.gdk
import gtk.glade

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import Date
import DateHandler
import const
import Utils
import GrampsDisplay

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
MOD_TEXT = ( 
    (Date.MOD_NONE       , _('Regular')),
    (Date.MOD_BEFORE     , _('Before')),
    (Date.MOD_AFTER      , _('After')),
    (Date.MOD_ABOUT      , _('About')),
    (Date.MOD_RANGE      , _('Range')),
    (Date.MOD_SPAN       , _('Span')),
    (Date.MOD_TEXTONLY   , _('Text only')) )

QUAL_TEXT = (
    (Date.QUAL_NONE,       _('Regular')), 
    (Date.QUAL_ESTIMATED,  _('Estimated')), 
    (Date.QUAL_CALCULATED, _('Calculated')) )

CAL_TO_MONTHS_NAMES = { 
    Date.CAL_GREGORIAN  : DateHandler.displayer._MONS,
    Date.CAL_JULIAN     : DateHandler.displayer._MONS,
    Date.CAL_HEBREW     : DateHandler.displayer._hebrew,
    Date.CAL_FRENCH     : DateHandler.displayer._french,
    Date.CAL_PERSIAN    : DateHandler.displayer._persian,
    Date.CAL_ISLAMIC    : DateHandler.displayer._islamic }

#-------------------------------------------------------------------------
#
# DateEdit
#
#-------------------------------------------------------------------------
class DateEdit:
    """Class that associates a pixmap with a text widget, providing visual
    feedback that indicates if the text widget contains a valid date"""

    good = gtk.gdk.pixbuf_new_from_file(const.good_xpm)
    bad = gtk.gdk.pixbuf_new_from_file(const.bad_xpm)
    caution = gtk.gdk.pixbuf_new_from_file(const.caution_xpm)
    
    def __init__(self,date_obj,text_obj,button_obj,parent_window=None):
        """
        Creates a connection between the date_obj, text_obj and the pixmap_obj.
        Assigns callbacks to parse and change date when the text
        in text_obj is changed, and to invoke Date Editor when the LED
        button_obj is pressed. 
        """

        self.date_obj = date_obj
        self.text_obj = text_obj
        self.button_obj = button_obj
        self.parent_window = parent_window

        self.pixmap_obj = button_obj.get_child()
        
        self.text_obj.connect('focus-out-event',self.parse_and_check)
        self.button_obj.connect('clicked',self.invoke_date_editor)
        
        self.text = unicode(self.text_obj.get_text())
        self.check()

    def check(self):
        """
        Check current date object and display LED indicating the validity.
        """
        if self.date_obj.get_modifier() == Date.MOD_TEXTONLY:
            self.pixmap_obj.set_from_pixbuf(self.pixmap_obj.render_icon(gtk.STOCK_DIALOG_ERROR,gtk.ICON_SIZE_MENU))
        elif self.date_obj.is_regular():
            self.pixmap_obj.set_from_pixbuf(self.pixmap_obj.render_icon(gtk.STOCK_YES,gtk.ICON_SIZE_MENU))
        else:
            self.pixmap_obj.set_from_pixbuf(self.pixmap_obj.render_icon(gtk.STOCK_DIALOG_WARNING,gtk.ICON_SIZE_MENU))
        
    def parse_and_check(self,obj,val):
        """
        Called with the text box loses focus. Parses the text and calls 
        the check() method ONLY if the text has changed.
        """

        text = unicode(self.text_obj.get_text())
        if text != self.text:
            self.text = text
            self.date_obj.copy(DateHandler.parser.parse(text))
            self.text_obj.set_text(DateHandler.displayer.display(self.date_obj))
            self.check()

    def invoke_date_editor(self,obj):
        """
        Invokes Date Editor dialog when the user clicks the LED button.
        If date was in fact built, sets the date_obj to the newly built
        date.
        """
        date_dialog = DateEditorDialog(self.date_obj,self.parent_window)
        the_date = date_dialog.return_date
        self.update_after_editor(the_date)

    def update_after_editor(self,date_obj):
        """
        Update text field and LED button to reflect the given date instance.
        """
        if date_obj:
            self.date_obj.copy(date_obj)
            self.text_obj.set_text(DateHandler.displayer.display(self.date_obj))
            self.check()
        
#-------------------------------------------------------------------------
#
# DateEditorDialog
#
#-------------------------------------------------------------------------
class DateEditorDialog:
    """
    Dialog allowing to build the date precisely, to correct possible 
    limitations of parsing and/or underlying structure of Date.
    """

    def __init__(self,date,parent_window=None):
        """
        Initiate and display the dialog.
        """

        # Create self.date as a copy of the given Date object.
        self.date = Date.Date(date)

        self.top = gtk.glade.XML(const.dialogFile, "date_edit","gramps" )
        self.top_window = self.top.get_widget('date_edit')
        self.top_window.hide()
        title = self.top.get_widget('title')
        Utils.set_titles(self.top_window,title,_('Date selection'))

        self.calendar_box = self.top.get_widget('calendar_box')
        for name in Date.Date.ui_calendar_names:
            self.calendar_box.append_text(name)
        self.calendar_box.set_active(self.date.get_calendar())
        self.calendar_box.connect('changed',self.switch_calendar)

        self.quality_box = self.top.get_widget('quality_box')
        for item_number in range(len(QUAL_TEXT)):
            self.quality_box.append_text(QUAL_TEXT[item_number][1])
            if self.date.get_quality() == QUAL_TEXT[item_number][0]:
                self.quality_box.set_active(item_number)

        self.type_box = self.top.get_widget('type_box')
        for item_number in range(len(MOD_TEXT)):
            self.type_box.append_text(MOD_TEXT[item_number][1])
            if self.date.get_modifier() == MOD_TEXT[item_number][0]:
                self.type_box.set_active(item_number)
        self.type_box.connect('changed',self.switch_type)

        self.start_month_box = self.top.get_widget('start_month_box')
        self.stop_month_box = self.top.get_widget('stop_month_box')
        month_names = CAL_TO_MONTHS_NAMES[self.date.get_calendar()]
        for name in month_names:
            self.start_month_box.append_text(name)
            self.stop_month_box.append_text(name)
        self.start_month_box.set_active(self.date.get_month())
        self.stop_month_box.set_active(self.date.get_stop_month())
        
        self.start_day = self.top.get_widget('start_day')
        self.start_day.set_value(self.date.get_day())
        self.start_year = self.top.get_widget('start_year')
        self.start_year.set_value(self.date.get_year())

        self.stop_day = self.top.get_widget('stop_day')
        self.stop_day.set_value(self.date.get_stop_day())
        self.stop_year = self.top.get_widget('stop_year')
        self.stop_year.set_value(self.date.get_stop_year())
        
        # Disable second date controls if not compound date
        if not self.date.is_compound():
            self.stop_day.set_sensitive(0)
            self.stop_month_box.set_sensitive(0)
            self.stop_year.set_sensitive(0)

        # Disable the rest of controls if a text-only date
        if self.date.get_modifier() == Date.MOD_TEXTONLY:
            self.start_day.set_sensitive(0)
            self.start_month_box.set_sensitive(0)
            self.start_year.set_sensitive(0)
            self.calendar_box.set_sensitive(0)
            self.quality_box.set_sensitive(0)

        self.text_entry = self.top.get_widget('date_text_entry')
        self.text_entry.set_text(self.date.get_text())
        
        # The dialog is modal -- since dates don't have names, we don't
        # want to have several open dialogs, since then the user will
        # loose track of which is which. Much like opening files.
        if parent_window:
            self.top_window.set_transient_for(parent_window)
        
        self.return_date = None
        while 1:
            response = self.top_window.run()
            if response == gtk.RESPONSE_HELP:
                GrampsDisplay.help('adv-dates')

            elif response == gtk.RESPONSE_OK:
                (the_quality,the_modifier,the_calendar,the_value,the_text) = \
                                        self.build_date_from_ui()
                self.return_date = Date.Date(self.date)
                self.return_date.set(
                    quality=the_quality,
                    modifier=the_modifier,
                    calendar=the_calendar,
                    value=the_value,
                    text=the_text)
                break
            else:
                break
        self.top_window.destroy()
        gc.collect()

    def build_date_from_ui(self):
        """
        Collect information from the UI controls and return 
        5-tuple of (quality,modifier,calendar,value,text) 
        """
        # It is important to not set date based on these controls. 
        # For example, changing the caledar makes the date inconsistent
        # until the callback of the calendar menu is finished. 
        # We need to be able to use this function from that callback,
        # so here we just report on the state of all widgets, without
        # actually modifying the date yet.
        
        modifier = MOD_TEXT[self.type_box.get_active()][0]
        text = self.text_entry.get_text()

        if modifier == Date.MOD_TEXTONLY:
            return (Date.QUAL_NONE,Date.MOD_TEXTONLY,Date.CAL_GREGORIAN,
                                            Date.EMPTY,text)

        quality = QUAL_TEXT[self.quality_box.get_active()][0]

        if modifier in (Date.MOD_RANGE,Date.MOD_SPAN):
            value = (
                self.start_day.get_value_as_int(),
                self.start_month_box.get_active(),
                self.start_year.get_value_as_int(),
                False,
                self.stop_day.get_value_as_int(),
                self.stop_month_box.get_active(),
                self.stop_year.get_value_as_int(),
                False)
        else:
            value = (
                self.start_day.get_value_as_int(),
                self.start_month_box.get_active(),
                self.start_year.get_value_as_int(),
                False)
        calendar = self.calendar_box.get_active()
        return (quality,modifier,calendar,value,text)

    def switch_type(self,obj):
        """
        Disable/enable various date controls depending on the date 
        type selected via the menu.
        """

        the_modifier = MOD_TEXT[self.type_box.get_active()][0]
        
        # Disable/enable second date controls based on whether
        # the type allows compound dates
        if the_modifier in (Date.MOD_RANGE,Date.MOD_SPAN):
            stop_date_sensitivity = 1
        else:
            stop_date_sensitivity = 0
        self.stop_day.set_sensitive(stop_date_sensitivity)
        self.stop_month_box.set_sensitive(stop_date_sensitivity)
        self.stop_year.set_sensitive(stop_date_sensitivity)

        # Disable/enable the rest of the controls if the type is text-only.
        date_sensitivity = not the_modifier == Date.MOD_TEXTONLY
        self.start_day.set_sensitive(date_sensitivity)
        self.start_month_box.set_sensitive(date_sensitivity)
        self.start_year.set_sensitive(date_sensitivity)
        self.calendar_box.set_sensitive(date_sensitivity)
        self.quality_box.set_sensitive(date_sensitivity)

    def switch_calendar(self,obj):
        """
        Change month names and convert the date based on the calendar 
        selected via the menu.
        """
        
        old_cal = self.date.get_calendar()
        new_cal = self.calendar_box.get_active()

        (the_quality,the_modifier,the_calendar,the_value,the_text) = \
                                        self.build_date_from_ui()
        self.date.set(
                quality=the_quality,
                modifier=the_modifier,
                calendar=old_cal,
                value=the_value,
                text=the_text)

        self.date.convert_calendar(new_cal)
        
        self.start_month_box.get_model().clear()
        self.stop_month_box.get_model().clear()
        month_names = CAL_TO_MONTHS_NAMES[new_cal]
        for name in month_names:
            self.start_month_box.append_text(name)
            self.stop_month_box.append_text(name)

        self.start_day.set_value(self.date.get_day())
        self.start_month_box.set_active(self.date.get_month())
        self.start_year.set_value(self.date.get_year())
        self.stop_day.set_value(self.date.get_stop_day())
        self.stop_month_box.set_active(self.date.get_stop_month())
        self.stop_year.set_value(self.date.get_stop_year())
