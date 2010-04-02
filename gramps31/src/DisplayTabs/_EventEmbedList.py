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
# Python classes
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS classes
#
#-------------------------------------------------------------------------
import gen.lib
import Errors
from DdTargets import DdTargets
from _EmbeddedList import EmbeddedList
from _EventRefModel import EventRefModel

#-------------------------------------------------------------------------
#
# EventEmbedList
#
#-------------------------------------------------------------------------
class EventEmbedList(EmbeddedList):

    _HANDLE_COL = 7
    _DND_TYPE   = DdTargets.EVENTREF
    _DND_EXTRA  = DdTargets.EVENT

    _MSG = {
        'add'   : _('Add a new event'),
        'del'   : _('Remove the selected event'),
        'edit'  : _('Edit the selected event'),
        'share' : _('Share an existing event'),
        'up'    : _('Move the selected event upwards'),
        'down'  : _('Move the selected event downwards'),
        }

    _column_names = [
        (_('Type'), 0, 100), 
        (_('Description'), 1, 175), 
        (_('ID'), 2, 60), 
        (_('Date'), 6, 150), 
        (_('Place'), 4, 140), 
        (_('Role'), 5, 80),
        ]
    
    def __init__(self, dbstate, uistate, track, obj):
        self.obj = obj
        EmbeddedList.__init__(self, dbstate, uistate, track, _('_Events'), 
                              EventRefModel, share_button=True, 
                              move_buttons=True)

    def get_ref_editor(self):
        from Editors import EditFamilyEventRef
        return EditFamilyEventRef

    def get_icon_name(self):
        return 'gramps-event'

    def get_data(self):
        return self.obj.get_event_ref_list()

    def column_order(self):
        return ((1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5))

    def default_type(self):
        return gen.lib.EventType(gen.lib.EventType.MARRIAGE)

    def default_role(self):
        return gen.lib.EventRoleType(gen.lib.EventRoleType.FAMILY)

    def add_button_clicked(self, obj):
        try:
            ref = gen.lib.EventRef()
            event = gen.lib.Event()
            ref.set_role(self.default_role())
            event.set_type(self.default_type())
            self.get_ref_editor()(
                self.dbstate, self.uistate, self.track,
                event, ref, self.object_added)
        except Errors.WindowActiveError:
            pass

    def share_button_clicked(self, obj):
        from Selectors import selector_factory
        SelectEvent = selector_factory('Event')

        sel = SelectEvent(self.dbstate,self.uistate,self.track)
        event = sel.run()
        if event:
            try:
                ref = gen.lib.EventRef()
                ref.set_role(self.default_role())
                self.get_ref_editor()(
                    self.dbstate, self.uistate, self.track,
                    event, ref, self.object_added)
            except Errors.WindowActiveError:
                pass

    def edit_button_clicked(self, obj):
        ref = self.get_selected()
        if ref:
            event = self.dbstate.db.get_event_from_handle(ref.ref)
            try:
                self.get_ref_editor()(
                    self.dbstate, self.uistate, self.track,
                    event, ref, self.object_edited)
            except Errors.WindowActiveError:
                from QuestionDialog import WarningDialog
                WarningDialog(
                    _("Cannot edit this reference"),
                    _("This event reference cannot be edited at this time. "
                      "Either the associated event is already being edited "
                      "or another event reference that is associated with "
                      "the same event is being edited.\n\nTo edit this event "
                      "reference, you need to close the event.")
                    )

    def object_added(self, reference, primary):
        reference.ref = primary.handle
        self.get_data().append(reference)
        self.changed = True
        self.rebuild()

    def object_edited(self, ref, event):
        self.changed = True
        self.rebuild()

    def _handle_drag(self, row, obj):
        """
        An event reference that is from a drag and drop has
        an unknown event reference role
        """
        from gen.lib import EventRoleType
        
        obj.set_role((EventRoleType.UNKNOWN,''))
        EmbeddedList._handle_drag(self, row, obj)

        event = self.dbstate.db.get_event_from_handle(obj.ref)
        try:
            self.get_ref_editor()(self.dbstate, self.uistate, self.track,
                                  event, obj, self.object_edited)
        except Errors.WindowActiveError:
            from QuestionDialog import WarningDialog
            WarningDialog(
                    _("Cannot edit this reference"),
                    _("This event reference cannot be edited at this time. "
                      "Either the associated event is already being edited "
                      "or another event reference that is associated with "
                      "the same event is being edited.\n\nTo edit this event "
                      "reference, you need to close the event.")
                    )

    def handle_extra_type(self, objtype, obj):
        try:
            ref = gen.lib.EventRef()
            event = self.dbstate.db.get_event_from_handle(obj)
            ref.set_role(self.default_role())
            self.get_ref_editor()(
                self.dbstate, self.uistate, self.track,
                event, ref, self.object_added)
        except Errors.WindowActiveError:
            pass

