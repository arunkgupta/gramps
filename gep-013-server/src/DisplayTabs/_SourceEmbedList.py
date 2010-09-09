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
from _SourceRefModel import SourceRefModel
from _EmbeddedList import EmbeddedList

#-------------------------------------------------------------------------
#
# SourceEmbedList
#
#-------------------------------------------------------------------------
class SourceEmbedList(EmbeddedList):

    _HANDLE_COL = 4
    _DND_TYPE = DdTargets.SOURCEREF
    _DND_EXTRA = DdTargets.SOURCE_LINK
        
    _MSG = {
        'add'   : _('Create and add a new source'),
        'del'   : _('Remove the existing source'),
        'edit'  : _('Edit the selected source'),
        'share' : _('Add an existing source'),
        'up'    : _('Move the selected source upwards'),
        'down'  : _('Move the selected source downwards'),
        }

    #index = column in model. Value =
    #  (name, sortcol in model, width, markup/text, weigth_col
    _column_names = [
        (_('ID'),     0, 75, 0, -1), 
        (_('Title'),  1, 200, 0, -1), 
        (_('Author'), 2, 125, 0, -1), 
        (_('Page'),   3, 100, 0, -1), 
        ]
    
    def __init__(self, dbstate, uistate, track, obj):
        self.obj = obj
        EmbeddedList.__init__(self, dbstate, uistate, track, _('_Sources'), 
                              SourceRefModel, share_button=True, 
                              move_buttons=True)

    def get_icon_name(self):
        return 'gramps-source'

    def get_data(self):
        return self.obj.get_source_references()

    def column_order(self):
        return ((1, 0), (1, 1), (1, 2), (1, 3))

    def add_button_clicked(self, obj):
        try:
            from Editors import EditSourceRef
            
            sref = gen.lib.SourceRef()
            src = gen.lib.Source()
            EditSourceRef(
                self.dbstate,
                self.uistate,
                self.track, 
                src,
                sref,
                self.object_added)
        except Errors.WindowActiveError:
            pass

    def share_button_clicked(self, obj):
        from Selectors import selector_factory
        SelectSource = selector_factory('Source')

        sel = SelectSource(self.dbstate,self.uistate,self.track)
        src = sel.run()
        if src:
            try:
                from Editors import EditSourceRef
                
                ref = gen.lib.SourceRef()
                EditSourceRef(self.dbstate,
                              self.uistate,
                              self.track, 
                              src,
                              ref,
                              self.object_added)
                
            except Errors.WindowActiveError:
                pass

    def edit_button_clicked(self, obj):
        sref = self.get_selected()
        if sref:
            src = self.dbstate.db.get_source_from_handle(sref.ref)

            try:
                from Editors import EditSourceRef
                
                EditSourceRef(self.dbstate, self.uistate, self.track, 
                              src, sref, self.object_edited)
            except Errors.WindowActiveError:
                from QuestionDialog import WarningDialog
                WarningDialog(
                    _("Cannot edit this reference"),
                    _("This source reference cannot be edited at this time. "
                      "Either the associated source is already being edited "
                      "or another source reference that is associated with "
                      "the same source is being edited.\n\nTo edit this "
                      "source reference, you need to close the source.")
                    )

    def object_added(self, reference, primary):
        reference.ref = primary.handle
        self.get_data().append(reference)
        self.changed = True
        self.rebuild()

    def object_edited(self, refererence, primary):
        self.changed = True
        self.rebuild()

    def handle_extra_type(self, objtype, obj):
        sref = gen.lib.SourceRef()
        src = self.dbstate.db.get_source_from_handle(obj)
        try:
            from Editors import EditSourceRef
            
            EditSourceRef(self.dbstate, self.uistate, self.track, 
                          src, sref, self.object_added)
        except Errors.WindowActiveError:
            pass
