# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2006  Donald N. Allingham
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
Media View.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _
import urlparse
import os
import cPickle as pickle

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
import PageView
import DisplayModels
import ThumbNails
import const
import Config
import Utils
import Bookmarks
import Mime
import gen.lib

from Editors import EditMedia, DeleteMediaQuery
import Errors
from QuestionDialog import QuestionDialog, ErrorDialog
from Filters.SideBar import MediaSidebarFilter
from DdTargets import DdTargets


#-------------------------------------------------------------------------
#
# MediaView
#
#-------------------------------------------------------------------------
class MediaView(PageView.ListView):
    """
    Provide the Media View interface on the GRAMPS main window. This allows
    people to manage all media items in their database. This is very similar
    to the other list based views, with the exeception that it also has a
    thumbnail image at the top of the view that must be updated when the
    selection changes or when the selected media object changes.
    """
    
    COLUMN_NAMES = [
        _('Title'), 
        _('ID'), 
        _('Type'), 
        _('Path'), 
        _('Last Changed'), 
        _('Date'), 
        ]
    
    ADD_MSG     = _("Add a new media object")
    EDIT_MSG    = _("Edit the selected media object")
    DEL_MSG     = _("Delete the selected media object")
    FILTER_TYPE = 'MediaObject'

    _DND_TYPE = DdTargets.URI_LIST
    
    def __init__(self, dbstate, uistate):

        signal_map = {
            'media-add'     : self.row_add, 
            'media-update'  : self.row_update, 
            'media-delete'  : self.row_delete, 
            'media-rebuild' : self.object_build,
            }

        PageView.ListView.__init__(
            self, _('Media'), dbstate, uistate, 
            MediaView.COLUMN_NAMES, len(MediaView.COLUMN_NAMES), 
            DisplayModels.MediaModel, 
            signal_map, dbstate.db.get_media_bookmarks(), 
            Bookmarks.MediaBookmarks, filter_class=MediaSidebarFilter)

        self.func_list = {
            '<CONTROL>J' : self.jump, 
            '<CONTROL>BackSpace' : self.key_delete, 
            }

        Config.client.notify_add("/apps/gramps/interface/filter", 
                                 self.filter_toggle)

    def _set_dnd(self):
        """
        Set up drag-n-drop. The source and destionation are set by calling .target()
        on the _DND_TYPE. Obviously, this means that there must be a _DND_TYPE
        variable defined that points to an entry in DdTargets.
        """

        dnd_types = [ self._DND_TYPE.target() ]

        self.list.drag_dest_set(gtk.DEST_DEFAULT_ALL, dnd_types, 
                                gtk.gdk.ACTION_COPY)
        self.list.drag_source_set(gtk.gdk.BUTTON1_MASK, 
                                  [self._DND_TYPE.target()], 
                                  gtk.gdk.ACTION_COPY)
        self.list.connect('drag_data_get', self.drag_data_get)
        self.list.connect('drag_data_received', self.drag_data_received)

    def drag_data_get(self, widget, context, sel_data, info, time):
        """
        Provide the drag_data_get function, which passes a tuple consisting of:

           1) Drag type defined by the .drag_type field specfied by the value
              assigned to _DND_TYPE
           2) The id value of this object, used for the purpose of determining
              the source of the object. If the source of the object is the same
              as the object, we are doing a reorder instead of a normal drag
              and drop
           3) Pickled data. The pickled version of the selected object
           4) Source row. Used for a reorder to determine the original position
              of the object
        """

        selected_ids = self.selected_handles()
        if selected_ids:
            data = (self.drag_info().drag_type, id(self), selected_ids[0], 0)
            sel_data.set(sel_data.target, 8, pickle.dumps(data))

    def drag_info(self):
        """
        Return the type of DND targetst that this view will accept. For Media 
        View, we will accept media objects.
        """
        return DdTargets.MEDIAOBJ

    def find_index(self, obj):
        """
        returns the index of the object within the associated data
        """
        return self.model.indexlist[obj]

    def drag_data_received(self, widget, context, x, y, sel_data, info, time):
        """
        Handle the standard gtk interface for drag_data_received.

        If the selection data is define, extract the value from sel_data.data, 
        and decide if this is a move or a reorder.
        """
        if sel_data and sel_data.data:
            cleaned_string = sel_data.data.replace('\0', ' ')
            cleaned_string = cleaned_string.replace("\r", " ").strip()
            data_list = Utils.fix_encoding(cleaned_string).split('\n')
            for d in [item.strip() for item in data_list]:
                protocol, site, mfile, j, k, l = urlparse.urlparse(d)
                if protocol == "file":
                    name = Utils.fix_encoding(mfile)
                    mime = Mime.get_type(name)
                    if not Mime.is_valid_type(mime):
                        return
                    photo = gen.lib.MediaObject()
                    photo.set_path(name)
                    photo.set_mime_type(mime)
                    basename = os.path.basename(name)
                    (root, ext) = os.path.splitext(basename)
                    photo.set_description(root)
                    trans = self.dbstate.db.transaction_begin()
                    self.dbstate.db.add_object(photo, trans)
                    self.dbstate.db.transaction_commit(trans, 
                                                       _("Drag Media Object"))
        widget.emit_stop_by_name('drag_data_received')
                
    def get_bookmarks(self):
        """
        Return the booksmarks associated with this view
        """
        return self.dbstate.db.get_media_bookmarks()

    def define_actions(self):
        """
        Defines the UIManager actions specific to Media View. We need to make
        sure that the common List View actions are defined as well, so we
        call the parent function.
        """
        PageView.ListView.define_actions(self)

        self._add_action('ColumnEdit', gtk.STOCK_PROPERTIES, 
                         _('_Column Editor'), callback=self._column_editor)
        self._add_action('FilterEdit', None, _('Media Filter Editor'), 
                         callback=self.filter_editor)
        self._add_action('OpenMedia', 'gramps-viewmedia', _('View'), 
                         tip=_("View in the default viewer"), 
                         callback=self.view_media)
                        
    def view_media(self, obj):
        """
        Launch external viewers based of mime types for the selected objects.
        """
        mlist = []
        self.selection.selected_foreach(self.blist, mlist)

        for handle in mlist:
            ref_obj = self.dbstate.db.get_object_from_handle(handle)
            mime_type = ref_obj.get_mime_type()
            app = Mime.get_application(mime_type)
            if app:
                Utils.launch(app[0], Utils.media_path_full(self.dbstate.db, 
                                                           ref_obj.get_path()))
            else:
                ErrorDialog(_("Cannot view %s") % ref_obj.get_path(), 
                            _("GRAMPS cannot find an application that can view "
                              "a file type of %s.") % mime_type)

    def _column_editor(self, obj):
        """
        Start the column editor dialog
        """
        import ColumnOrder

        ColumnOrder.ColumnOrder(
            _('Select Media Columns'), 
            self.uistate, 
            self.dbstate.db.get_media_column_order(), 
            MediaView.COLUMN_NAMES, 
            self.set_column_order)

    def set_column_order(self, clist):
        """
        Saves the column order to the database
        """
        self.dbstate.db.set_media_column_order(clist)
        self.build_columns()

    def column_order(self):
        """
        Get the column order from the database
        """
        return self.dbstate.db.get_media_column_order()

    def get_stock(self):
        """
        Return the icon for this view
        """
        return 'gramps-media'

    def build_widget(self):
        """
        Builds the View from GTK components
        """
        base = PageView.ListView.build_widget(self)
        vbox = gtk.VBox()
        vbox.set_border_width(0)
        vbox.set_spacing(4)

        self.image = gtk.Image()
        self.image.set_size_request(int(const.THUMBSCALE), 
                                    int(const.THUMBSCALE))
        ebox = gtk.EventBox()
        ebox.add(self.image)
        ebox.connect('button-press-event', self.button_press_event)
        vbox.pack_start(ebox, False)
        vbox.pack_start(base, True)

        self.ttips = gtk.Tooltips()
        self.ttips.set_tip(
            ebox, _('Double click image to view in an external viewer'))

        self.selection.connect('changed', self.row_change)
        self._set_dnd()
        return vbox

    def button_press_event(self, obj, event):
        """
        Event handler that catches a double click, and and launches a viewer for
        the selected object.
        """
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.view_media(obj)

    def row_update(self, obj):
        """
        Update the data in the row. we override this because the Media View adds
        additional functionality to the normal List View. The Media View may 
        have to update the thumbnail image. So, we call the parent task to 
        handle the normal operation, then call row_change to make sure that 
        the thumbnail is updated properly if needed.
        """
        PageView.ListView.row_update(self, obj)
        if self.active:
            self.row_change(obj)

    def row_change(self, obj):
        """
        Update the thumbnail on a row change. If nothing is selected, clear
        the thumbnail image.
        """
        handle = self.first_selected()
        if not handle:
            self.image.clear()
            self.ttips.disable()
        else:
            obj = self.dbstate.db.get_object_from_handle(handle)
            pix = ThumbNails.get_thumbnail_image(
                        Utils.media_path_full(self.dbstate.db, obj.get_path()))
            self.image.set_from_pixbuf(pix)
            self.ttips.enable()
    
    def ui_definition(self):
        """
        Return the UIManager XML description of the menus
        """
        return '''<ui>
          <menubar name="MenuBar">
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
            <menu action="BookMenu">
              <placeholder name="AddEditBook">
                <menuitem action="AddBook"/>
                <menuitem action="EditBook"/>
              </placeholder>
            </menu>
          </menubar>
          <toolbar name="ToolBar">
            <placeholder name="CommonEdit">
              <toolitem action="Add"/>
              <toolitem action="Edit"/>
              <toolitem action="Remove"/>
            </placeholder>
            <separator/>
            <toolitem action="OpenMedia"/>
          </toolbar>
          <popup name="Popup">
            <menuitem action="Add"/>
            <menuitem action="Edit"/>
            <menuitem action="OpenMedia"/>
            <menuitem action="Remove"/>
          </popup>
        </ui>'''

    def add(self, obj):
        """Add a new media object to the media list"""
        try:
            EditMedia(self.dbstate, self.uistate, [], gen.lib.MediaObject())
        except Errors.WindowActiveError:
            pass

    def remove(self, obj):
        """
        Remove the selected object from the database after getting
        user verification.
        """
        handle = self.first_selected()
        if not handle:
            return
        the_lists = Utils.get_media_referents(handle, self.dbstate.db)

        ans = DeleteMediaQuery(self.dbstate, self.uistate, handle, the_lists)
        if filter(None, the_lists): # quick test for non-emptiness
            msg = _('This media object is currently being used. '
                    'If you delete this object, it will be removed from '
                    'the database and from all records that reference it.')
        else:
            msg = _('Deleting media object will remove it from the database.')

        msg = "%s %s" % (msg, Utils.data_recover_msg)
        self.uistate.set_busy_cursor(1)
        QuestionDialog(_('Delete Media Object?'), msg, 
                      _('_Delete Media Object'), ans.query_response)
        self.uistate.set_busy_cursor(0)

    def edit(self, obj):
        """
        Edit the selected object in the EditMedia dialog
        """
        handle = self.first_selected()
        if not handle:
            return
        
        obj = self.dbstate.db.get_object_from_handle(handle)
        try:
            EditMedia(self.dbstate, self.uistate, [], obj)
        except Errors.WindowActiveError:
            pass

    def get_handle_from_gramps_id(self, gid):
        """
        returns the handle of the specified object
        """
        obj = self.dbstate.db.get_object_from_gramps_id(gid)
        if obj:
            return obj.get_handle()
        else:
            return None
