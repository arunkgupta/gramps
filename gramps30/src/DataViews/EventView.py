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

# $Id$

"""
Provide the event view.
"""

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import gen.lib
import PageView
import DisplayModels
import Utils
import Errors
import Bookmarks
import Config
from DdTargets import DdTargets
from QuestionDialog import QuestionDialog
from Editors import EditEvent, DelEventQuery
from Filters.SideBar import EventSidebarFilter
from ReportBase import CATEGORY_QR_EVENT

#-------------------------------------------------------------------------
#
# internationalization
#
#-------------------------------------------------------------------------
from gettext import gettext as _


#-------------------------------------------------------------------------
#
# EventView
#
#-------------------------------------------------------------------------
class EventView(PageView.ListView):
    """
    EventView class, derived from the ListView
    """
    COLUMN_NAMES = [
        _('Description'),
        _('ID'),
        _('Type'),
        _('Date'),
        _('Place'),
        _('Last Changed'),
        ]
    
    ADD_MSG     = _("Add a new event")
    EDIT_MSG    = _("Edit the selected event")
    DEL_MSG     = _("Delete the selected event")
    FILTER_TYPE = "Event"
    QR_CATEGORY = CATEGORY_QR_EVENT

    def __init__(self, dbstate, uistate):
        """
        Create the Event View
        """

        signal_map = {
            'event-add'     : self.row_add,
            'event-update'  : self.row_update,
            'event-delete'  : self.row_delete,
            'event-rebuild' : self.object_build,
            }

        self.func_list = {
            '<CONTROL>J' : self.jump,
            '<CONTROL>BackSpace' : self.key_delete,
            }

        PageView.ListView.__init__(
            self, _('Events'), dbstate, uistate,
            EventView.COLUMN_NAMES, len(EventView.COLUMN_NAMES), 
            DisplayModels.EventModel,
            signal_map, dbstate.db.get_event_bookmarks(),
            Bookmarks.EventBookmarks, filter_class=EventSidebarFilter)

        Config.client.notify_add("/apps/gramps/interface/filter",
                                 self.filter_toggle)

    def get_bookmarks(self):
        """
        Return the bookmark object
        """
        return self.dbstate.db.get_event_bookmarks()

    def drag_info(self):
        """
        Indicate that the drag type is an EVENT
        """
        return DdTargets.EVENT

    def column_order(self):
        """
        returns a tuple indicating the column order
        """
        return self.dbstate.db.get_event_column_order()

    def get_stock(self):
        """
        Use the gramps-event stock icon
        """
        return 'gramps-event'

    def ui_definition(self):
        """
        Defines the UI string for UIManager
        """
        return '''<ui>
          <menubar name="MenuBar">
            <menu action="BookMenu">
              <placeholder name="AddEditBook">
                <menuitem action="AddBook"/>
                <menuitem action="EditBook"/>
              </placeholder>
            </menu>
            <menu action="FileMenu">
              <placeholder name="LocalExport">
                <menuitem action="ExportTab"/>
              </placeholder>
            </menu>
            <menu action="EditMenu">
              <placeholder name="CommonEdit">
                <menuitem action="Add"/>
                <menuitem action="Edit"/>
                <menuitem action="Remove"/>
              </placeholder>
              <menuitem action="ColumnEdit"/>
              <menuitem action="FilterEdit"/>
            </menu>
          </menubar>
          <toolbar name="ToolBar">
            <placeholder name="CommonEdit">
              <toolitem action="Add"/>
              <toolitem action="Edit"/>
              <toolitem action="Remove"/>
            </placeholder>
          </toolbar>
          <popup name="Popup">
            <menuitem action="Add"/>
            <menuitem action="Edit"/>
            <menuitem action="Remove"/>
            <separator/>
            <menu name="QuickReport" action="QuickReport">
              <menuitem action="Dummy"/>
            </menu>
          </popup>
        </ui>'''

    def define_actions(self):
        PageView.ListView.define_actions(self)
        self._add_action('FilterEdit', None, _('Event Filter Editor'),
                        callback=self.filter_editor,)
        self._add_action('ColumnEdit', gtk.STOCK_PROPERTIES,
                         _('_Column Editor'), callback=self._column_editor,)
        self._add_action('QuickReport', None, 
                         _("Quick Report"), None, None, None)
        self._add_action('Dummy', None, 
                         '  ', None, None, self.dummy_report)

    def get_handle_from_gramps_id(self, gid):
        obj = self.dbstate.db.get_event_from_gramps_id(gid)
        if obj:
            return obj.get_handle()
        else:
            return None

    def _column_editor(self, obj):
        """
        returns a tuple indicating the column order
        """
        import ColumnOrder

        ColumnOrder.ColumnOrder(
            _('Select Event Columns'),
            self.uistate,
            self.dbstate.db.get_event_column_order(),
            EventView.COLUMN_NAMES,
            self.set_column_order)

    def set_column_order(self, clist):
        self.dbstate.db.set_event_column_order(clist)
        self.build_columns()

    def add(self, obj):
        try:
            EditEvent(self.dbstate, self.uistate, [], gen.lib.Event())
        except Errors.WindowActiveError:
            pass

    def remove(self, obj):
        for ehandle in self.selected_handles():
            db = self.dbstate.db
            person_list = [
                item[1] for item in
                self.dbstate.db.find_backlink_handles(ehandle,['Person']) ]

            family_list = [ 
                item[1] for item in
                self.dbstate.db.find_backlink_handles(ehandle,['Family']) ]
            
            event = db.get_event_from_handle(ehandle)

            ans = DelEventQuery(self.dbstate, self.uistate, event, 
                                person_list, family_list)

            if len(person_list) + len(family_list) > 0:
                msg = _('This event is currently being used. Deleting it '
                        'will remove it from the database and from all '
                        'people and families that reference it.')
            else:
                msg = _('Deleting event will remove it from the database.')
            
            msg = "%s %s" % (msg, Utils.data_recover_msg)
            descr = event.get_description()
            if descr == "":
                descr = event.get_gramps_id()
                
            self.uistate.set_busy_cursor(1)
            QuestionDialog(_('Delete %s?') % descr, msg,
                           _('_Delete Event'), ans.query_response)
            self.uistate.set_busy_cursor(0)

    def edit(self, obj):
        mlist = []
        self.selection.selected_foreach(self.blist, mlist)

        for handle in mlist:
            event = self.dbstate.db.get_event_from_handle(handle)
            try:
                EditEvent(self.dbstate, self.uistate, [], event)
            except Errors.WindowActiveError:
                pass

    def dummy_report(self, obj):
        """ For the xml UI definition of popup to work, the submenu 
            Quick Report must have an entry in the xml
            As this submenu will be dynamically built, we offer a dummy action
        """
        pass

