#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2007  Donald N. Allingham
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

# $Id:PageView.py 9912 2008-01-22 09:17:46Z acraphae $

"""
Provide the base classes for GRAMPS' DataView classes
"""

#----------------------------------------------------------------
#
# python modules
#
#----------------------------------------------------------------
import cPickle as pickle
import time
import logging

_LOG = logging.getLogger('.pageview')

#----------------------------------------------------------------
#
# gtk
#
#----------------------------------------------------------------
import gtk
import pango

#----------------------------------------------------------------
#
# GRAMPS 
#
#----------------------------------------------------------------
import Config
import TreeTips
import Bookmarks
import Errors
from Filters import SearchBar
import Utils
from gui.utils import add_menuitem
import const
from widgets.menutoolbuttonaction import MenuToolButtonAction

from TransUtils import sgettext as _
from QuestionDialog import QuestionDialog, QuestionDialog2

NAVIGATION_NONE   = -1
NAVIGATION_PERSON = 0

#------------------------------------------------------------------------------
#
# PageView
#
#------------------------------------------------------------------------------
class PageView(object):
    """
    The PageView class is the base class for all Data Views in GRAMPS.  All 
    Views should derive from this class. The ViewManager understands the public
    interface of this class
    """
    
    def __init__(self, title, dbstate, uistate):
        self.title = title
        self.dbstate = dbstate
        self.uistate = uistate
        self.action_list = []
        self.action_toggle_list = []
        self.action_toolmenu_list = []
        self.action_toolmenu = {} #easy access to toolmenuaction and proxies
        self.action_group = None
        self.additional_action_groups = []
        self.additional_uis = []
        self.widget = None
        self.model = None
        self.ui_def = '<ui></ui>'
        self.dbstate.connect('no-database', self.disable_action_group)
        self.dbstate.connect('database-changed', self.enable_action_group)
        self.dirty = True
        self.active = False
        self.handle_col = 0
        self.selection = None
        self.func_list = {}

    def call_function(self, key):
        """
        Calls the function associated with the key value
        """
        self.func_list.get(key)()

    def post(self):
        pass
    
    def set_active(self):
        """
        Called with the PageView is set as active. If the page is "dirty",
        then we rebuild the data.
        """
        self.active = True
        if self.dirty:
            self.uistate.set_busy_cursor(True)
            self.build_tree()
            self.uistate.set_busy_cursor(False)
            
    def set_inactive(self):
        """
        Marks page as being active (currently displayed)
        """
        self.active = False

    def build_tree(self):
        """
        Rebuilds the current display. This must be overridden by the derived
        class.
        """
        raise NotImplementedError

    def navigation_type(self):
        """
        Indictates the navigation type. Currently, we only support navigation
        for views that are Person centric.
        """
        return NAVIGATION_NONE
    
    def ui_definition(self):
        """
        returns the XML UI definition for the UIManager
        """
        return self.ui_def

    def additional_ui_definitions(self):
        """
        Return any additional interfaces for the UIManager that the view
        needs to define.
        """
        return self.additional_uis

    def disable_action_group(self):
        """
        Turns off the visibility of the View's action group, if defined
        """
        if self.action_group:
            self.action_group.set_visible(False)

    def enable_action_group(self, obj):
        """
        Turns on the visibility of the View's action group, if defined
        """
        if self.action_group:
            self.action_group.set_visible(True)

    def get_stock(self):
        """
        Return image associated with the view, which is used for the 
        icon for the button.
        """
        return gtk.STOCK_MISSING_IMAGE
        
    def get_title(self):
        """
        Return the title of the view. This is used to define the text for the
        button, and for the tab label.
        """
        return self.title

    def get_display(self):
        """
        Builds the graphical display, returning the top level widget.
        """
        if not self.widget:
            self.widget = self.build_widget()
        return self.widget

    def build_widget(self):
        """
        Builds the container widget for the interface. Must be overridden by the
        the base class. Returns a gtk container widget.
        """
        raise NotImplementedError

    def define_actions(self):
        """
        Defines the UIManager actions. Called by the ViewManager to set up the
        View. The user typically defines self.action_list and 
        self.action_toggle_list in this function. 

        Derived classes must override this function.
        """
        raise NotImplementedError

    def __build_action_group(self):
        """
        Create an UIManager ActionGroup from the values in self.action_list
        and self.action_toggle_list. The user should define these in 
        self.define_actions
        """
        self.action_group = gtk.ActionGroup(self.title)
        if len(self.action_list) > 0:
            self.action_group.add_actions(self.action_list)
        if len(self.action_toggle_list) > 0:
            self.action_group.add_toggle_actions(self.action_toggle_list)
        for action_toolmenu in self.action_toolmenu_list:
            self.action_toolmenu[action_toolmenu[0]] = \
                    MenuToolButtonAction(action_toolmenu[0], #unique name
                                         action_toolmenu[1], #label
                                         action_toolmenu[2], #tooltip
                                         action_toolmenu[3], #callback
                                         action_toolmenu[4]  #arrow tooltip
                                        )
            self.action_group.add_action(
                                    self.action_toolmenu[action_toolmenu[0]])

    def _add_action(self, name, stock_icon, label, accel=None, tip=None, 
                   callback=None):
        """
        Add an action to the action list for the current view. 
        """
        self.action_list.append((name, stock_icon, label, accel, tip, 
                                 callback))

    def _add_toggle_action(self, name, stock_icon, label, accel=None, 
                           tip=None, callback=None, value=False):
        """
        Add a toggle action to the action list for the current view. 
        """
        self.action_toggle_list.append((name, stock_icon, label, accel, 
                                        tip, callback, value))
    
    def _add_toolmenu_action(self, name, label, tooltip, callback, 
                             arrowtooltip):
        self.action_toolmenu_list.append((name, label, tooltip, callback,
                                          arrowtooltip))

    def get_actions(self):
        """
        Return the actions that should be used for the view. This includes the
        standard action group (which handles the main toolbar), along with 
        additional action groups.

        If the action group is not defined, we build it the first time. This 
        allows us to delay the intialization until it is really needed.

        The ViewManager uses this function to extract the actions to install 
        into the UIManager.
        """
        if not self.action_group:
            self.__build_action_group()
        return [self.action_group] + self.additional_action_groups

    def _add_action_group(self, group):
        """
        Allows additional action groups to be added to the view. 
        """
        self.additional_action_groups.append(group)

    def change_page(self):
        """
        Called when the page changes.
        """
        self.uistate.clear_filter_results()

    def edit(self, obj):
        """
        Template function to allow the editing of the selected object
        """
        raise NotImplementedError

    def remove(self, handle):
        """
        Template function to allow the removal of an object by its handle
        """
        raise NotImplementedError

    def remove_selected_objects(self):
        """
        Function to remove selected objects
        """
        prompt = True
        if len(self.selected_handles()) > 1:
            q = QuestionDialog2(
                _("Remove selected items?"),
                _("More than one item has been selected for deletion. "
                  "Ask before deleting each one?"),
                _("Yes"),
                _("No"))
            prompt = q.run()
            
        if not prompt:
            self.uistate.set_busy_cursor(1)

        for handle in self.selected_handles():
            (query, is_used, object) = self.remove_object_from_handle(handle)
            if prompt:
                if is_used:
                    msg = _('This item is currently being used. '
                            'Deleting it will remove it from the database and '
                            'from all other items that reference it.')
                else:
                    msg = _('Deleting item will remove it from the database.')
                
                msg = "%s %s" % (msg, Utils.data_recover_msg)
                #descr = object.get_description()
                #if descr == "":
                descr = object.get_gramps_id()
                self.uistate.set_busy_cursor(1)
                QuestionDialog(_('Delete %s?') % descr, msg,
                               _('_Delete Item'), query.query_response)
                self.uistate.set_busy_cursor(0)
            else:
                query.query_response()

        if not prompt:
            self.uistate.set_busy_cursor(0)

    def remove_object_from_handle(self, handle):
        """
        Template function to allow the removal of an object by its handle
        """
        raise NotImplementedError

    def add(self, obj):
        """
        Template function to allow the adding of a new object
        """
        raise NotImplementedError
    
    def _key_press(self, obj, event):
        #act if no modifier, and allow Num Lock as MOD2_MASK
        if not event.state or event.state  in (gtk.gdk.MOD2_MASK, ):
            if event.keyval in (gtk.keysyms.Return, gtk.keysyms.KP_Enter):
                self.edit(obj)
                return True
        return False

    def blist(self, store, path, node, sel_list):
        handle = store.get_value(node, self.handle_col)
        sel_list.append(handle)

    def selected_handles(self):
        mlist = []
        self.selection.selected_foreach(self.blist, mlist)
        return mlist

    def first_selected(self):
        mlist = []
        self.selection.selected_foreach(self.blist, mlist)
        if mlist:
            return mlist[0]
        else:
            return None

    def on_delete(self):
        """
        Method called on shutdown. Data views should put code here
        that should be called when quiting the main application.
        """
        pass

class BookMarkView(PageView):

    def __init__(self, title, state, uistate, bookmarks, bm_type):
        PageView.__init__(self, title, state, uistate)
        self.bm_type = bm_type
        self.setup_bookmarks(bookmarks)

    def goto_handle(self, obj):
        raise NotImplementedError

    def setup_bookmarks(self, bookmarks):
        self.bookmarks = self.bm_type(
            self.dbstate, self.uistate, bookmarks, self.goto_handle)

    def add_bookmark(self, obj):
        from BasicUtils import name_displayer
        
        if self.dbstate.active:
            self.bookmarks.add(self.dbstate.active.get_handle())
            name = name_displayer.display(self.dbstate.active)
            self.uistate.push_message(self.dbstate, 
                                      _("%s has been bookmarked") % name)
        else:
            from QuestionDialog import WarningDialog
            WarningDialog(
                _("Could Not Set a Bookmark"), 
                _("A bookmark could not be set because "
                  "no one was selected."))

    def set_active(self):
        PageView.set_active(self)
        self.bookmarks.display()

    def set_inactive(self):
        PageView.set_inactive(self)
        self.bookmarks.undisplay()

    def edit_bookmarks(self, obj):
        self.bookmarks.edit()

    def enable_action_group(self, obj):
        PageView.enable_action_group(self, obj)

    def disable_action_group(self):
        PageView.disable_action_group(self)

    def define_actions(self):
        self.book_action = gtk.ActionGroup(self.title + '/Bookmark')
        self.book_action.add_actions([
            ('AddBook', 'gramps-bookmark-new', _('_Add Bookmark'), 
             '<control>d', None, self.add_bookmark), 
            ('EditBook', 'gramps-bookmark-edit', 
             _("%(title)s...") % {'title': _("Organize Bookmarks")}, 
             '<shift><control>b', None, 
             self.edit_bookmarks), 
            ])

        self._add_action_group(self.book_action)

#----------------------------------------------------------------
#
# PersonNavView
#
#----------------------------------------------------------------
class PersonNavView(BookMarkView):

    def __init__(self, title, dbstate, uistate, callback=None):
        BookMarkView.__init__(self, title, dbstate, uistate, 
                              dbstate.db.get_bookmarks(), 
                              Bookmarks.Bookmarks)

    def navigation_type(self):
        return NAVIGATION_PERSON

    def define_actions(self):
        # add the Forward action group to handle the Forward button

        BookMarkView.define_actions(self)

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
        self._add_action('FilterEdit',  None, _('Person Filter Editor'), 
                        callback=self.filter_editor)

        self.other_action = gtk.ActionGroup(self.title + '/PersonOther')
        self.other_action.add_actions([
                ('SetActive', gtk.STOCK_HOME, _("Set _Home Person"), None, 
                 None, self.set_default_person), 
                ])

        self._add_action_group(self.back_action)
        self._add_action_group(self.fwd_action)
        self._add_action_group(self.other_action)

    def disable_action_group(self):
        """
        Normally, this would not be overridden from the base class. However, 
        in this case, we have additional action groups that need to be
        handled correctly.
        """
        BookMarkView.disable_action_group(self)
        
        self.fwd_action.set_visible(False)
        self.back_action.set_visible(False)

    def enable_action_group(self, obj):
        """
        Normally, this would not be overridden from the base class. However, 
        in this case, we have additional action groups that need to be
        handled correctly.
        """
        BookMarkView.enable_action_group(self, obj)
        
        self.fwd_action.set_visible(True)
        self.back_action.set_visible(True)
        hobj = self.uistate.phistory
        self.fwd_action.set_sensitive(not hobj.at_end())
        self.back_action.set_sensitive(not hobj.at_front())

    def set_default_person(self, obj):
        active = self.dbstate.active
        if active:
            self.dbstate.db.set_default_person_handle(active.get_handle())

    def home(self, obj):
        defperson = self.dbstate.db.get_default_person()
        if defperson:
            self.dbstate.change_active_person(defperson)

    def jump(self):
        dialog = gtk.Dialog(_('Jump to by GRAMPS ID'), None, 
                            gtk.DIALOG_NO_SEPARATOR)
        dialog.set_border_width(12)
        label = gtk.Label('<span weight="bold" size="larger">%s</span>' % 
                          _('Jump to by GRAMPS ID'))
        label.set_use_markup(True)
        dialog.vbox.add(label)
        dialog.vbox.set_spacing(10)
        dialog.vbox.set_border_width(12)
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("%s: " % _('ID')), False)
        text = gtk.Entry()
        text.set_activates_default(True)
        hbox.pack_start(text, False)
        dialog.vbox.pack_start(hbox, False)
        dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
                           gtk.STOCK_JUMP_TO, gtk.RESPONSE_OK)
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.vbox.show_all()
        
        if dialog.run() == gtk.RESPONSE_OK:
            gid = text.get_text()
            person = self.dbstate.db.get_person_from_gramps_id(gid)
            if person:
                self.dbstate.change_active_person(person)
            else:
                self.uistate.push_message(
                    self.dbstate, 
                    _("Error: %s is not a valid GRAMPS ID") % gid)
        dialog.destroy()

    def filter_editor(self, obj):
        from FilterEditor import FilterEditor

        try:
            FilterEditor('Person', const.CUSTOM_FILTERS, 
                         self.dbstate, self.uistate)
        except Errors.WindowActiveError:
            return

    def fwd_clicked(self, obj, step=1):
        hobj = self.uistate.phistory
        hobj.lock = True
        if not hobj.at_end():
            try:
                handle = hobj.forward()
                self.dbstate.change_active_handle(handle)
                self.uistate.modify_statusbar(self.dbstate)
                hobj.mhistory.append(hobj.history[hobj.index])
                self.fwd_action.set_sensitive(not hobj.at_end())
                self.back_action.set_sensitive(True)
            except:
                hobj.clear()
                self.fwd_action.set_sensitive(False)
                self.back_action.set_sensitive(False)
        else:
            self.fwd_action.set_sensitive(False)
            self.back_action.set_sensitive(True)
        hobj.lock = False

    def back_clicked(self, obj, step=1):
        hobj = self.uistate.phistory
        hobj.lock = True
        if not hobj.at_front():
            try:
                handle = hobj.back()
                self.active = self.dbstate.db.get_person_from_handle(handle)
                self.uistate.modify_statusbar(self.dbstate)
                self.dbstate.change_active_handle(handle)
                hobj.mhistory.append(hobj.history[hobj.index])
                self.back_action.set_sensitive(not hobj.at_front())
                self.fwd_action.set_sensitive(True)
            except:
                hobj.clear()
                self.fwd_action.set_sensitive(False)
                self.back_action.set_sensitive(False)
        else:
            self.back_action.set_sensitive(False)
            self.fwd_action.set_sensitive(True)
        hobj.lock = False
        
    def handle_history(self, handle):
        """
        Updates the person history information
        It will push the person at the end of the history if that person is
        not present person
        """
        hobj = self.uistate.phistory
        if handle and not hobj.lock and not (handle == hobj.present()):
            hobj.push(handle)
            self.fwd_action.set_sensitive(not hobj.at_end())
            self.back_action.set_sensitive(not hobj.at_front())

    def change_page(self):
        hobj = self.uistate.phistory
        self.fwd_action.set_sensitive(not hobj.at_end())
        self.back_action.set_sensitive(not hobj.at_front())
        self.other_action.set_sensitive(not self.dbstate.db.readonly)

#----------------------------------------------------------------
#
# ListView
#
#----------------------------------------------------------------
class ListView(BookMarkView):

    ADD_MSG = ""
    EDIT_MSG = ""
    DEL_MSG = ""
    QR_CATEGORY = -1

    def __init__(self, title, dbstate, uistate, columns, handle_col, 
                 make_model, signal_map, get_bookmarks, bm_type, 
                 multiple=False, filter_class=None):

        BookMarkView.__init__(self, title, dbstate, uistate, 
                              get_bookmarks, bm_type)

        self.filter_class = filter_class
        self.renderer = gtk.CellRendererText()
        self.renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        self.sort_col = 0
        self.sort_order = gtk.SORT_ASCENDING
        self.columns = []
        self.colinfo = columns
        self.handle_col = handle_col
        self.make_model = make_model
        self.model = None
        self.signal_map = signal_map
        self.multiple_selection = multiple
        self.generic_filter = None
        dbstate.connect('database-changed', self.change_db)

    def build_filter_container(self, box, filter_class):
        self.filter_sidebar = filter_class(self.dbstate, self.uistate, 
                                           self.filter_clicked)
        self.filter_pane = self.filter_sidebar.get_widget()

        hpaned = gtk.HBox()
        hpaned.pack_start(self.vbox, True, True)
        hpaned.pack_end(self.filter_pane, False, False)
        self.filter_toggle(None, None, None, None)
        return hpaned

    def filter_toggle(self, client, cnxn_id, entry, data):
        if Config.get(Config.FILTER):
            self.search_bar.hide()
            self.filter_pane.show()
        else:
            self.search_bar.show()
            self.filter_pane.hide()

    def post(self):
        if self.filter_class:
            if Config.get(Config.FILTER):
                self.search_bar.hide()
                self.filter_pane.show()
            else:
                self.search_bar.show()
                self.filter_pane.hide()

    def filter_clicked(self):
        self.generic_filter = self.filter_sidebar.get_filter()
        self.build_tree()

    def add_bookmark(self, obj):
        mlist = []
        self.selection.selected_foreach(self.blist, mlist)

        if mlist:
            self.bookmarks.add(mlist[0])
        else:
            from QuestionDialog import WarningDialog
            WarningDialog(
                _("Could Not Set a Bookmark"), 
                _("A bookmark could not be set because "
                  "nothing was selected."))

    def jump(self):
        dialog = gtk.Dialog(_('Jump to by GRAMPS ID'), None, 
                            gtk.DIALOG_NO_SEPARATOR)
        dialog.set_border_width(12)
        label = gtk.Label('<span weight="bold" size="larger">%s</span>' % 
                          _('Jump to by GRAMPS ID'))
        label.set_use_markup(True)
        dialog.vbox.add(label)
        dialog.vbox.set_spacing(10)
        dialog.vbox.set_border_width(12)
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("%s: " % _('ID')), False)
        text = gtk.Entry()
        text.set_activates_default(True)
        hbox.pack_start(text, False)
        dialog.vbox.pack_start(hbox, False)
        dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
                           gtk.STOCK_JUMP_TO, gtk.RESPONSE_OK)
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.vbox.show_all()
        
        if dialog.run() == gtk.RESPONSE_OK:
            gid = text.get_text()
            handle = self.get_handle_from_gramps_id(gid)
            if handle:
                self.goto_handle(handle)
            else:
                self.uistate.push_message(
                    self.dbstate, 
                    _("Error: %s is not a valid GRAMPS ID") % gid)
        dialog.destroy()

    def drag_info(self):
        return None

    def drag_begin(self, widget, context):
        widget.drag_source_set_icon_stock(self.get_stock())
        return True

    def column_order(self):
        """
        Must be set by children. The method that obtains the column order
        to be used. Format: see ColumnOrder.
        """
        raise NotImplementedError

    def column_ord_setfunc(self, clist):
        """
        Must be set by children. The method that stores the column order
        given by clist (result of ColumnOrder class).
        """
        raise NotImplementedError

    def set_column_order(self, clist):
        """
        change the order of the columns to that given in clist
        """
        self.column_ord_setfunc(clist)
        #now we need to rebuild the model so it contains correct column info
        self.dirty = True
        #make sure we sort on first column. We have no idea where the 
        # column that was sorted on before is situated now. 
        self.sort_col = 0
        self.sort_order = gtk.SORT_ASCENDING
        self.setup_filter()
        self.build_tree()
 
    def build_widget(self):
        """
        Builds the interface and returns a gtk.Container type that
        contains the interface. This containter will be inserted into
        a gtk.Notebook page.
        """
        self.vbox = gtk.VBox()
        self.vbox.set_border_width(4)
        self.vbox.set_spacing(4)
        
        self.search_bar = SearchBar(self.dbstate, self.uistate, 
                                    self.search_build_tree)
        filter_box = self.search_bar.build()

        self.list = gtk.TreeView()
        self.list.set_rules_hint(True)
        self.list.set_headers_visible(True)
        self.list.set_headers_clickable(True)
        self.list.set_fixed_height_mode(True)
        self.list.connect('button-press-event', self._button_press)
        self.list.connect('key-press-event', self._key_press)
        if self.drag_info():
            self.list.connect('drag_data_get', self.drag_data_get)
            self.list.connect('drag_begin', self.drag_begin)

        scrollwindow = gtk.ScrolledWindow()
        scrollwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwindow.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scrollwindow.add(self.list)

        self.vbox.pack_start(filter_box, False)
        self.vbox.pack_start(scrollwindow, True)

        self.renderer = gtk.CellRendererText()
        self.renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        self.inactive = False

        self.columns = []
        self.build_columns()
        self.selection = self.list.get_selection()
        if self.multiple_selection:
            self.selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.selection.connect('changed', self.row_changed)

        self.setup_filter()

        if self.filter_class:
            return self.build_filter_container(self.vbox, self.filter_class)
        else:
            return self.vbox
    
    def search_build_tree(self):
        self.build_tree()

    def row_changed(self, obj):
        """Called with a row is changed. Check the selected objects from
        the person_tree to get the IDs of the selected objects. Set the
        active person to the first person in the list. If no one is
        selected, set the active person to None"""

        if self.drag_info():
            selected_ids = self.selected_handles()

            if len(selected_ids) == 1:
                self.list.drag_source_set(gtk.gdk.BUTTON1_MASK, 
                                          [self.drag_info().target()], 
                                          gtk.gdk.ACTION_COPY)
        
    def drag_data_get(self, widget, context, sel_data, info, time):
        selected_ids = self.selected_handles()

        if selected_ids:
            data = (self.drag_info().drag_type, id(self), selected_ids[0], 0)
            sel_data.set(sel_data.target, 8 , pickle.dumps(data))
        return True

    def setup_filter(self):
        """Build the default filters and add them to the filter menu."""
        cols = []
        for pair in [pair for pair in self.column_order() if pair[0]]:
            cols.append((self.colinfo[pair[1]], pair[1]))
        self.search_bar.setup_filter(cols)

    def goto_handle(self, handle):
        if not handle or self.inactive:
            return

        # mark inactive to prevent recursion
        self.inactive = True

        # select the handle in the view
        try:
            path = self.model.on_get_path(handle)
            self.selection.unselect_all()
            self.selection.select_path(path)
            self.list.scroll_to_cell(path, None, 1, 0.5, 0)
        except KeyError:
            self.selection.unselect_all()

        # disable the inactive flag
        self.inactive = False

    def __display_column_sort(self):
        for i in xrange(len(self.columns)):
            enable_sort_flag = (i==self.sort_col)
            self.columns[i].set_sort_indicator(enable_sort_flag)
        self.columns[self.sort_col].set_sort_order(self.sort_order)

    def column_clicked(self, obj, data):
        cput = time.clock()
        same_col = False
        if self.sort_col != data:
            order = gtk.SORT_ASCENDING
        else:
            same_col = True
            if (self.columns[data].get_sort_order() == gtk.SORT_DESCENDING
                or not self.columns[data].get_sort_indicator()):
                order = gtk.SORT_ASCENDING
            else:
                order = gtk.SORT_DESCENDING

        self.sort_col = data
        self.sort_order = order
        handle = self.first_selected()

        if Config.get(Config.FILTER):
            search = (True, self.generic_filter)
        else:
            search = (False, self.search_bar.get_value())

        if same_col:
            self.model.reverse_order()
        else:
            self.model = self.make_model(self.dbstate.db, self.sort_col, 
                                         self.sort_order, 
                                         search=search, 
                                         sort_map=self.column_order())
        
        self.list.set_model(self.model)
        self.__display_column_sort()

        if handle:
            self.goto_handle(handle)

        # set the search column to be the sorted column
        search_col = self.column_order()[data][1]
        self.list.set_search_column(search_col)
        _LOG.debug('   ' + self.__class__.__name__ + ' column_clicked ' +
                    str(time.clock() - cput) + ' sec')

    def build_columns(self):
        for column in self.columns:
            self.list.remove_column(column)
            
        self.columns = []

        index = 0
        for pair in [pair for pair in self.column_order() if pair[0]]:
            name = self.colinfo[pair[1]]

            if self.model and 'marker_color_column' in self.model.__dict__:
                mcol = self.model.marker_color_column
                column = gtk.TreeViewColumn(name, self.renderer, text=pair[1], 
                                            foreground=mcol)
            else:
                column = gtk.TreeViewColumn(name, self.renderer, text=pair[1])
                
            column.connect('clicked', self.column_clicked, index)
            column.set_resizable(True)
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            column.set_fixed_width(pair[2])
            column.set_clickable(True)
            self.columns.append(column)
            self.list.append_column(column)
            index += 1

    def build_tree(self):
        if self.active:
            cput = time.clock()
            if Config.get(Config.FILTER):
                filter_info = (True, self.generic_filter)
            else:
                filter_info = (False, self.search_bar.get_value())

            if self.dirty or self.model is None \
                    or not self.model.node_map.full_srtkey_hndl_map():
                self.model = self.make_model(self.dbstate.db, self.sort_col, 
                                             search=filter_info,
                                             sort_map=self.column_order())
            else:
                #the entire data to show is already in memory.
                #run only the part that determines what to show
                self.list.set_model(None)
                self.model.set_search(filter_info)
                self.model.rebuild_data()
            
            self.build_columns()
            self.list.set_model(self.model)
            self.__display_column_sort()

            if const.USE_TIPS and self.model.tooltip_column is not None:
                self.tooltips = TreeTips.TreeTips(
                    self.list, self.model.tooltip_column, True)
            self.dirty = False
            self.uistate.show_filter_results(self.dbstate, 
                                             self.model.displayed(), 
                                             self.model.total())
            _LOG.debug(self.__class__.__name__ + ' build_tree ' +
                    str(time.clock() - cput) + ' sec')
            
        else:
            self.dirty = True

    def object_build(self):
        """callback, for if tree must be rebuilt and bookmarks redrawn
        """
        self.dirty = True
        if self.active:
            self.bookmarks.redraw()
        self.build_tree()
        
    def filter_toggle_action(self, obj):
        if obj.get_active():
            self.search_bar.hide()
            self.filter_pane.show()
            active = True
        else:
            self.search_bar.show()
            self.filter_pane.hide()
            active = False
        Config.set(Config.FILTER, active)
        self.build_tree()

    def filter_editor(self, obj):
        from FilterEditor import FilterEditor

        try:
            FilterEditor(self.FILTER_TYPE , const.CUSTOM_FILTERS, 
                         self.dbstate, self.uistate)
        except Errors.WindowActiveError:
            return

    def change_db(self, db):
        for sig in self.signal_map:
            db.connect(sig, self.signal_map[sig])
        self.bookmarks.update_bookmarks(self.get_bookmarks())
        if self.active:
            #force rebuild of the model on build of tree
            self.dirty = True
            self.build_tree()
            self.bookmarks.redraw()
        else:
            self.dirty = True

    def row_add(self, handle_list):
        if self.active:
            cput = time.clock()
            for handle in handle_list:
                self.model.add_row_by_handle(handle)
            _LOG.debug('   ' + self.__class__.__name__ + ' row_add ' +
                    str(time.clock() - cput) + ' sec')
            self.uistate.show_filter_results(self.dbstate, 
                                             self.model.displayed(), 
                                             self.model.total())
        else:
            self.dirty = True

    def row_update(self, handle_list):
        if self.model:
            self.model.prev_handle = None
        if self.active:
            cput = time.clock()
            for handle in handle_list:
                self.model.update_row_by_handle(handle)
            _LOG.debug('   ' + self.__class__.__name__ + ' row_update ' +
                    str(time.clock() - cput) + ' sec')
        else:
            self.dirty = True

    def row_delete(self, handle_list):
        if self.active:
            cput = time.clock()
            for handle in handle_list:
                self.model.delete_row_by_handle(handle)
            _LOG.debug('   '  + self.__class__.__name__ + ' row_delete ' +
                    str(time.clock() - cput) + ' sec')
            self.uistate.show_filter_results(self.dbstate, 
                                             self.model.displayed(), 
                                             self.model.total())
        else:
            self.dirty = True

    def define_actions(self):
        """
        Required define_actions function for PageView. Builds the action
        group information required. We extend beyond the normal here, 
        since we want to have more than one action group for the PersonView.
        Most PageViews really won't care about this.
        """
        
        BookMarkView.define_actions(self)

        self.edit_action = gtk.ActionGroup(self.title + '/ChangeOrder')
        self.edit_action.add_actions([
                ('Add', gtk.STOCK_ADD, _("_Add..."), "<control>Insert", 
		 self.ADD_MSG, self.add), 
                ('Remove', gtk.STOCK_REMOVE, _("_Remove"), "<control>Delete", 
		 self.DEL_MSG, self.remove), 
                ('ExportTab', None, _('Export View...'), None, None, self.export), 
                ])

        self._add_action_group(self.edit_action)

        self._add_action('Edit', gtk.STOCK_EDIT, _("action|_Edit..."), 
                         accel="<control>Return", 
                         tip=self.EDIT_MSG, 
                         callback=self.edit)
        
        self._add_toggle_action('Filter', None, _('_Filter'), 
                                callback=self.filter_toggle_action)

    def _column_editor(self, obj):
        """
        Causes the View to display a column editor. This should be overridden
        by any class that provides columns (such as a list based view)
        """
        raise NotImplemented

    def _button_press(self, obj, event):
        if not self.dbstate.open:
            return False
        from QuickReports import create_quickreport_menu
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            self.edit(obj)
            return True
        elif event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            menu = self.uistate.uimanager.get_widget('/Popup')
            #construct quick reports if needed
            if menu and self.QR_CATEGORY > -1 :
                qr_menu = self.uistate.uimanager.\
                            get_widget('/Popup/QuickReport').get_submenu()
                if qr_menu :
                    self.uistate.uimanager.\
                            get_widget('/Popup/QuickReport').remove_submenu()
                reportactions = []
                if menu and self.dbstate.active:
                    (ui, reportactions) = create_quickreport_menu(
                                            self.QR_CATEGORY, 
                                            self.dbstate, 
                                            self.uistate,
                                            self.first_selected())
                if len(reportactions) > 1 :
                    qr_menu = gtk.Menu()
                    for action in reportactions[1:] :
                        add_menuitem(qr_menu, action[2], None, action[5])
                    self.uistate.uimanager.get_widget('/Popup/QuickReport').\
                            set_submenu(qr_menu)
            if menu:
                menu.popup(None, None, None, event.button, event.time)
                return True
            
        return False
    
    def _key_press(self, obj, event):
        if not self.dbstate.open:
            return False
        if not event.state or event.state  in (gtk.gdk.MOD2_MASK, ):
            if event.keyval in (gtk.keysyms.Return, gtk.keysyms.KP_Enter):
                self.edit(obj)
                return True
        return False

    def change_page(self):
        if self.model:
            self.uistate.show_filter_results(self.dbstate, 
                                             self.model.displayed(), 
                                             self.model.total())
        self.edit_action.set_sensitive(not self.dbstate.db.readonly)

    def key_delete(self):
        self.remove(None)

    def export(self, obj):
        chooser = gtk.FileChooserDialog(
            _("Export View as Spreadsheet"), 
            self.uistate.window, 
            gtk.FILE_CHOOSER_ACTION_SAVE, 
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
             gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        chooser.set_do_overwrite_confirmation(True)

        combobox = gtk.combo_box_new_text()
        label = gtk.Label(_("Format:"))
        label.set_alignment(1.0, 0.5)
        box = gtk.HBox()
        box.pack_start(label, True, True, padding=12)
        box.pack_start(combobox, False, False)
        combobox.append_text(_('CSV'))
        combobox.append_text(_('Open Document Spreadsheet'))
        combobox.set_active(0)
        box.show_all()
        chooser.set_extra_widget(box)

        while True:
            value = chooser.run()
            fn = chooser.get_filename()
            fl = combobox.get_active()
            if value == gtk.RESPONSE_OK:
                if fn:
                    chooser.destroy()
                    break
            else:
                chooser.destroy()
                return
        self.write_tabbed_file(fn, fl)

    def write_tabbed_file(self, name, type):
        """
        Write a tabbed file to the specified name. 
        
        The output file type is determined by the type variable.
        """
        from docgen import CSVTab, ODSTab
        ofile = None
        data_cols = [pair[1] for pair in self.column_order() if pair[0]]

        column_names = [self.colinfo[i] for i in data_cols]
        if type == 0:
            ofile = CSVTab(len(column_names))                        
        else:
            ofile = ODSTab(len(column_names))
        
        ofile.open(name)
        ofile.start_page()
        ofile.start_row()
        for name in column_names:
            ofile.write_cell(name)
        ofile.end_row()

        for row in self.model:
            ofile.start_row()
            for index in data_cols:
                ofile.write_cell(row[index])
            ofile.end_row()
        ofile.end_page()
        ofile.close()
            
