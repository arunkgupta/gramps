#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
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

# $Id:AutoComp.py 9912 2008-01-22 09:17:46Z acraphae $

"""
Provide autocompletion functionality.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import locale

#-------------------------------------------------------------------------
#
# GNOME modules
#
#-------------------------------------------------------------------------
import gtk
import gobject

def fill_combo(combo, data_list):
    """
    Fill a combo box with completion data
    """
    store = gtk.ListStore(gobject.TYPE_STRING)

    for data in [ item for item in data_list if item ]:
        store.append(row=[data])
    
    combo.set_model(store)
    combo.set_text_column(0)
    completion = gtk.EntryCompletion()
    completion.set_model(store)
    completion.set_minimum_key_length(1)
    completion.set_text_column(0)
    combo.child.set_completion(completion)

def fill_entry(entry, data_list):
    """
    Fill a entry with completion data
    """
    store = gtk.ListStore(gobject.TYPE_STRING)

    for data in [ item for item in data_list if item ]:
        store.append(row=[data])
        
    completion = gtk.EntryCompletion()
    completion.set_model(store)
    completion.set_minimum_key_length(1)
    completion.set_text_column(0)
    entry.set_completion(completion)
    
#-------------------------------------------------------------------------
#
# StandardCustomSelector class
#
#-------------------------------------------------------------------------
class StandardCustomSelector:
    """
    This class provides an interface to selecting from the predefined
    options or entering custom string.

    The typical usage should be:
        type_sel = StandardCustomSelector(mapping,None,custom_key,active_key)
        whatever_table.attach(type_sel,...)
    or
        type_sel = StandardCustomSelector(mapping,cbe,custom_key,active_key)
    with the existing ComboBoxEntry cbe.

    To set up the combo box, specify the active key at creation time,
    or later (or with custom text) use:
        type_sel.set_values(i,s)

    and later, when or before the dialog is closed, do:
        (i,s) = type_sel.get_values()

    to obtain the tuple of (int,str) corresponding to the user selection.

    No selection will return (custom_key,'') if the custom key is given,
    or (None,'') if it is not given.

    The active_key determines the default selection that will be displayed
    upon widget creation. If omitted, the entry will be empty. If present,
    then no selection on the user's part will return the
    (active_key,mapping[active_key]) tuple.
        
    """
    def __init__(self, mapping, cbe=None, custom_key=None, active_key=None,
                 additional=None):
        """
        Constructor for the StandardCustomSelector class.

        @param cbe: Existing ComboBoxEntry widget to use.
        @type cbe: gtk.ComboBoxEntry
        @param mapping: The mapping between integer and string constants.
        @type mapping:  dict
        @param custom_key: The key corresponding to the custom string entry
        @type custom_key:  int
        @param active_key: The key for the entry to make active upon creation
        @type active_key:  int
        """

        # set variables
        self.mapping = mapping
        self.custom_key = custom_key
        self.active_key = active_key
        self.active_index = 0
        self.additional = additional
        
        # make model
        self.store = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING)

        # fill it up using mapping
        self.fill()

        # create combo box entry
        if cbe:
            self.selector = cbe
            self.selector.set_model(self.store)
            self.selector.set_text_column(1)
        else:
            self.selector = gtk.ComboBoxEntry(self.store, 1)
        if self.active_key != None:
            self.selector.set_active(self.active_index)

        # make autocompletion work
        completion = gtk.EntryCompletion()
        completion.set_model(self.store)
        completion.set_minimum_key_length(1)
        completion.set_text_column(1)
        self.selector.child.set_completion(completion)

    def fill(self):
        """
        Fill with data
        """
        keys = self.mapping.keys()
        keys.sort(self.by_value)
        index = 0
        for key in keys:
            if key != self.custom_key:
                self.store.append(row=[key, self.mapping[key]])
                if key == self.active_key:
                    self.active_index = index
                index = index + 1

        if self.additional:
            for event_type in self.additional:
                if type(event_type) == str or type(event_type) == unicode :
                    if event_type:
                        self.store.append(row=[self.custom_key, event_type])
                elif type(event_type) == tuple:
                    if event_type[1]:
                        self.store.append(row=[event_type[0], event_type[1]])
                else:
                    self.store.append(row=[int(event_type), str(event_type)])
                if key == self.active_key:
                    self.active_index = index
                index = index + 1

    def by_value(self, first, second):
        """
        Method for sorting keys based on the values.
        """
        fvalue = self.mapping[first]
        svalue = self.mapping[second]
        return locale.strcoll(fvalue, svalue)

    def get_values(self):
        """
        Get selected values.

        @return: Returns (int,str) tuple corresponding to the selection.
        @rtype: tuple
        """
        active_iter = self.selector.get_active_iter()
        if active_iter:
            int_val = self.store.get_value(active_iter, 0)
            str_val = self.store.get_value(active_iter, 1)
            if str_val != self.mapping[int_val]:
                str_val = self.selector.child.get_text().strip()
        else:
            int_val = self.custom_key
            str_val = self.selector.child.get_text().strip()
        if str_val in self.mapping.values():
            for key in self.mapping.keys():
                if str_val == self.mapping[key]:
                    int_val = key
                    break
        else:
            int_val = self.custom_key
        return (int_val, str_val)

    def set_values(self, val):
        """
        Set values according to given tuple.

        @param val: (int,str) tuple with the values to set.
        @type val: tuple
        """
        key, text = val
        if key in self.mapping.keys() and key != self.custom_key:
            self.store.foreach(self.set_int_value, key)
        elif self.custom_key != None:
            self.selector.child.set_text(text)
        else:
            print "StandardCustomSelector.set(): Option not available:", val

    def set_int_value(self, model, path, node, val):
        if model.get_value(node, 0) == val:
            self.selector.set_active_iter(node)
            return True
        return False


