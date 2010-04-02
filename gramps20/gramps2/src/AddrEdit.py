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

"""
The AddrEdit module provides the AddressEditor class. This provides a
mechanism for the user to edit address information.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _
import gc

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk.glade

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import GrampsDisplay
import const
import Utils
import Date
import RelLib
import Sources
import DateEdit
import Spell

from WindowUtils import GladeIf

#-------------------------------------------------------------------------
#
# AddressEditor class
#
#-------------------------------------------------------------------------
class AddressEditor:
    """
    Displays a dialog that allows the user to edit an address.
    """
    def __init__(self,parent,addr,callback,parent_window=None):
        """
        Displays the dialog box.

        parent - The class that called the Address editor.
        addr - The address that is to be edited
        """

        self.parent = parent
        if addr:
            if self.parent.child_windows.has_key(addr):
                self.parent.child_windows[addr].present(None)
                return
            else:
                self.win_key = addr
        else:
            self.win_key = self
        self.db = self.parent.db
        self.addr = addr
        self.callback = callback
        self.child_windows = {}

        # Get the important widgets from the glade description
        self.top = gtk.glade.XML(const.dialogFile, "addr_edit","gramps")
        self.gladeif = GladeIf(self.top)
        
        self.window = self.top.get_widget("addr_edit")
        self.addr_start = self.top.get_widget("address_start")
        self.addr_start.set_editable(not self.db.readonly)
        self.street = self.top.get_widget("street")
        self.street.set_editable(not self.db.readonly)
        self.city = self.top.get_widget("city")
        self.city.set_editable(not self.db.readonly)
        self.state = self.top.get_widget("state")
        self.state.set_editable(not self.db.readonly)
        self.country = self.top.get_widget("country")
        self.country.set_editable(not self.db.readonly)
        self.postal = self.top.get_widget("postal")
        self.postal.set_editable(not self.db.readonly)
        self.phone = self.top.get_widget("phone")
        self.phone.set_editable(not self.db.readonly)
        self.note_field = self.top.get_widget("addr_note")
        self.note_field.set_editable(not self.db.readonly)
        self.spell = Spell.Spell(self.note_field)
        self.priv = self.top.get_widget("priv")
        self.priv.set_sensitive(not self.db.readonly)
        self.slist = self.top.get_widget("slist")
        self.sources_label = self.top.get_widget("sourcesAddr")
        self.notes_label = self.top.get_widget("noteAddr")
        self.flowed = self.top.get_widget("addr_flowed")
        self.flowed.set_sensitive(not self.db.readonly)
        self.preform = self.top.get_widget("addr_preform")
        self.preform.set_sensitive(not self.db.readonly)

        title_label = self.top.get_widget("title")

        Utils.set_titles(self.window,title_label,_('Address Editor'))

        if self.addr:
            self.srcreflist = self.addr.get_source_references()
            self.addr_date_obj = Date.Date(self.addr.get_date_object())
            self.addr_start.set_text(self.addr.get_date())
            self.street.set_text(self.addr.get_street())
            self.city.set_text(self.addr.get_city())
            self.state.set_text(self.addr.get_state())
            self.country.set_text(self.addr.get_country())
            self.postal.set_text(self.addr.get_postal_code())
            self.phone.set_text(self.addr.get_phone())
            self.priv.set_active(self.addr.get_privacy())
            if self.addr.get_note():
                self.note_field.get_buffer().set_text(self.addr.get_note())
                Utils.bold_label(self.notes_label)
                if addr.get_note_format() == 1:
                    self.preform.set_active(1)
                    self.note_field.set_wrap_mode(gtk.WRAP_NONE)
                else:
                    self.flowed.set_active(1)
                    self.note_field.set_wrap_mode(gtk.WRAP_WORD)
        else:
            self.addr_date_obj = Date.Date()
            self.srcreflist = []

        self.sourcetab = Sources.SourceTab(
            self.srcreflist, self, self.top, self.window, self.slist,
            self.top.get_widget('add_src'), self.top.get_widget('edit_src'),
            self.top.get_widget('del_src'), self.db.readonly)

        date_stat = self.top.get_widget("date_stat")
        date_stat.set_sensitive(not self.db.readonly)
        self.date_check = DateEdit.DateEdit(
            self.addr_date_obj, self.addr_start, date_stat, self.window)

        self.gladeif.connect('addr_edit','delete_event',self.on_delete_event)
        self.gladeif.connect('button122','clicked',self.close)
        self.gladeif.connect('button121','clicked',self.ok_clicked)
        okbtn = self.top.get_widget('button121')
        okbtn.set_sensitive(not self.db.readonly)
        self.gladeif.connect('button129','clicked',self.on_help_clicked)
        self.gladeif.connect('notebook2','switch_page',self.on_switch_page)
        self.gladeif.connect('addr_preform','toggled',self.format_toggled)

        if parent_window:
            self.window.set_transient_for(parent_window)
        self.add_itself_to_menu()
        self.window.show()

    def on_delete_event(self,obj,b):
        self.close_child_windows()
        self.remove_itself_from_menu()
        self.gladeif.close()
        gc.collect()

    def close(self,obj):
        self.close_child_windows()
        self.remove_itself_from_menu()
        self.gladeif.close()
        self.window.destroy()
        gc.collect()

    def close_child_windows(self):
        for child_window in self.child_windows.values():
            child_window.close(None)
        self.child_windows = {}

    def add_itself_to_menu(self):
        self.parent.child_windows[self.win_key] = self
        label = _('Address')
        self.parent_menu_item = gtk.MenuItem(label)
        self.parent_menu_item.set_submenu(gtk.Menu())
        self.parent_menu_item.show()
        self.parent.winsmenu.append(self.parent_menu_item)
        self.winsmenu = self.parent_menu_item.get_submenu()
        self.menu_item = gtk.MenuItem(_('Address Editor'))
        self.menu_item.connect("activate",self.present)
        self.menu_item.show()
        self.winsmenu.append(self.menu_item)

    def remove_itself_from_menu(self):
        del self.parent.child_windows[self.win_key]
        self.menu_item.destroy()
        self.winsmenu.destroy()
        self.parent_menu_item.destroy()

    def present(self,obj):
        self.window.present()

    def on_help_clicked(self,obj):
        """Display the relevant portion of GRAMPS manual"""
        GrampsDisplay.help('adv-ad')

    def ok_clicked(self,obj):
        """
        Called when the OK button is pressed. Gets data from the
        form and updates the Address data structure.
        """
        date_obj = self.addr_date_obj
        street = unicode(self.street.get_text())
        city = unicode(self.city.get_text())
        state = unicode(self.state.get_text())
        country = unicode(self.country.get_text())
        phone = unicode(self.phone.get_text())
        postal = unicode(self.postal.get_text())
        b = self.note_field.get_buffer()
        note = unicode(b.get_text(b.get_start_iter(),b.get_end_iter(),False))
        format = self.preform.get_active()
        priv = self.priv.get_active()
        
        if self.addr == None:
            self.addr = RelLib.Address()
            self.parent.plist.append(self.addr)
        self.addr.set_source_reference_list(self.srcreflist)

        self.update(date_obj,street,city,state,country,postal,phone,note,format,priv)
        self.callback(self.addr)
        self.close(obj)

    def format_toggled(self,junk):
        if self.preform.get_active():
            self.note_field.set_wrap_mode(gtk.WRAP_NONE)
        else:
            self.note_field.set_wrap_mode(gtk.WRAP_WORD)

    def check(self,get,set,data):
        """Compares a data item, updates if necessary, and sets the
        parents lists_changed flag"""
        if get() != data:
            set(data)
            self.parent.lists_changed = 1
            
    def update(self,date_obj,street,city,state,country,postal,phone,note,format,priv):
        """Compares the data items, and updates if necessary"""

        if not self.addr.get_date_object().is_equal(date_obj):
            self.addr.set_date_object(date_obj)
            self.parent.lists_changed = 1
        
        self.check(self.addr.get_street,self.addr.set_street,street)
        self.check(self.addr.get_country,self.addr.set_country,country)
        self.check(self.addr.get_city,self.addr.set_city,city)
        self.check(self.addr.get_state,self.addr.set_state,state)
        self.check(self.addr.get_postal_code,self.addr.set_postal_code,postal)
        self.check(self.addr.get_phone,self.addr.set_phone,phone)
        self.check(self.addr.get_note,self.addr.set_note,note)
        self.check(self.addr.get_note_format,self.addr.set_note_format,format)
        self.check(self.addr.get_privacy,self.addr.set_privacy,priv)

    def on_switch_page(self,obj,a,page):
        buf = self.note_field.get_buffer()
        text = unicode(buf.get_text(buf.get_start_iter(),buf.get_end_iter(),False))
        if text:
            Utils.bold_label(self.notes_label)
        else:
            Utils.unbold_label(self.notes_label)
