# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2006  Donald N. Allingham
# Copyright (C) 2008       Gary Burton
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
from gen.ggettext import gettext as _
import urlparse
import os
import sys
import cPickle as pickle
import urllib
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
from gui.utils import open_file_with_default_application
from gui.views.listview import ListView
from gui.views.treemodels import MediaModel
import ThumbNails
import const
import constfunc
import config
import Utils
import Bookmarks
import gen.mime
import gen.lib
from gui.editors import EditMedia, DeleteMediaQuery
import Errors
from Filters.SideBar import MediaSidebarFilter
from DdTargets import DdTargets
from gen.plug import CATEGORY_QR_MEDIA

#-------------------------------------------------------------------------
#
# MediaView
#
#-------------------------------------------------------------------------
class MediaView(ListView):
    """
    Provide the Media View interface on the GRAMPS main window. This allows
    people to manage all media items in their database. This is very similar
    to the other list based views, with the exception that it also has a
    thumbnail image at the top of the view that must be updated when the
    selection changes or when the selected media object changes.
    """
    COL_TITLE = 0
    COL_ID = 1
    COL_TYPE = 2
    COL_PATH = 3
    COL_CHAN = 4
    COL_DATE = 5
    #name of the columns
    COLUMN_NAMES = [
        _('Title'), 
        _('ID'), 
        _('Type'), 
        _('Path'), 
        _('Last Changed'), 
        _('Date'), 
        ]
    # default setting with visible columns, order of the col, and their size
    CONFIGSETTINGS = (
        ('columns.visible', [COL_TITLE, COL_ID, COL_TYPE, COL_PATH,
                             COL_DATE]),
        ('columns.rank', [COL_TITLE, COL_ID, COL_TYPE, COL_PATH,
                           COL_DATE, COL_CHAN]),
        ('columns.size', [200, 75, 100, 200, 150, 150])
        )    
    
    ADD_MSG     = _("Add a new media object")
    EDIT_MSG    = _("Edit the selected media object")
    DEL_MSG     = _("Delete the selected media object")
    FILTER_TYPE = 'MediaObject'
    QR_CATEGORY = CATEGORY_QR_MEDIA

    _DND_TYPE = DdTargets.URI_LIST
    
    def __init__(self, dbstate, uistate, nav_group=0):

        signal_map = {
            'media-add'     : self.row_add, 
            'media-update'  : self.row_update, 
            'media-delete'  : self.row_delete, 
            'media-rebuild' : self.object_build,
            }

        ListView.__init__(
            self, _('Media'), dbstate, uistate, 
            MediaView.COLUMN_NAMES, len(MediaView.COLUMN_NAMES), 
            MediaModel, 
            signal_map, dbstate.db.get_media_bookmarks(), 
            Bookmarks.MediaBookmarks, nav_group,
            filter_class=MediaSidebarFilter,
            multiple=True)

        self.func_list = {
            '<CONTROL>J' : self.jump, 
            '<CONTROL>BackSpace' : self.key_delete, 
            }

        config.connect("interface.filter", 
                          self.filter_toggle)

    def navigation_type(self):
        return 'Media'

    def _set_dnd(self):
        """
        Set up drag-n-drop. The source and destination are set by calling .target()
        on the _DND_TYPE. Obviously, this means that there must be a _DND_TYPE
        variable defined that points to an entry in DdTargets.
        """

        dnd_types = [ self._DND_TYPE.target() ]

        self.list.drag_dest_set(gtk.DEST_DEFAULT_MOTION|gtk.DEST_DEFAULT_DROP, 
                                dnd_types, 
                                gtk.gdk.ACTION_MOVE|gtk.gdk.ACTION_COPY)
        self.list.drag_source_set(gtk.gdk.BUTTON1_MASK, 
                                  [self._DND_TYPE.target()], 
                                  gtk.gdk.ACTION_COPY)
        #connected in listview already
        #self.list.connect('drag_data_get', self.drag_data_get)
        self.list.connect('drag_data_received', self.drag_data_received)

    def drag_data_get(self, widget, context, sel_data, info, time):
        """
        Provide the drag_data_get function, which passes a tuple consisting of:

           1) Drag type defined by the .drag_type field specified by the value
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
        Return the type of DND targets that this view will accept. For Media 
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
        The only data we accept on mediaview is dropping a file, so URI_LIST. 
        We assume this is what we obtain
        """
        if not sel_data:
            return
        #modern file managers provide URI_LIST. For Windows split sel_data.data
        if constfunc.win():
            files = sel_data.data.split('\n')
        else:
            files =  sel_data.get_uris()
        for file in files:
            clean_string = Utils.fix_encoding(
                            file.replace('\0',' ').replace("\r", " ").strip())
            protocol, site, mfile, j, k, l = urlparse.urlparse(clean_string)
            if protocol == "file":
                name = unicode(urllib.url2pathname(
                                mfile.encode(sys.getfilesystemencoding())))
                mime = gen.mime.get_type(name)
                if not gen.mime.is_valid_type(mime):
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
        ListView.define_actions(self)

        self._add_action('FilterEdit', None, _('Media Filter Editor'), 
                         callback=self.filter_editor)
        self._add_action('OpenMedia', 'gramps-viewmedia', _('View'), 
                         tip=_("View in the default viewer"), 
                         callback=self.view_media)
        self._add_action('OpenContainingFolder', None, 
                         _('Open Containing _Folder'), 
                         tip=_("Open the folder containing the media file"), 
                         callback=self.open_containing_folder)

        self._add_action('QuickReport', None, _("Quick View"), None, None, None)
        self._add_action('Dummy', None, '  ', None, None, self.dummy_report)
                        
    def view_media(self, obj):
        """
        Launch external viewers for the selected objects.
        """
        for handle in self.selected_handles():
            ref_obj = self.dbstate.db.get_object_from_handle(handle)
            mpath = Utils.media_path_full(self.dbstate.db, ref_obj.get_path())
            open_file_with_default_application(mpath)

    def open_containing_folder(self, obj):
        """
        Launch external viewers for the selected objects.
        """
        for handle in self.selected_handles():
            ref_obj = self.dbstate.db.get_object_from_handle(handle)
            mpath = Utils.media_path_full(self.dbstate.db, ref_obj.get_path())
            if mpath:
                mfolder, mfile = os.path.split(mpath)
                open_file_with_default_application(mfolder)

    def get_stock(self):
        """
        Return the icon for this view
        """
        return 'gramps-media'

    def build_widget(self):
        """
        Builds the View from GTK components
        """
        base = ListView.build_widget(self)
        vbox = gtk.VBox()
        vbox.set_border_width(0)
        vbox.set_spacing(4)

        self.image = gtk.Image()
        self.image.set_size_request(int(const.THUMBSCALE), 
                                    int(const.THUMBSCALE))
        ebox = gtk.EventBox()
        ebox.add(self.image)
        ebox.connect('button-press-event', self.button_press_event)
        ebox.set_tooltip_text(
            _('Double click image to view in an external viewer'))
        vbox.pack_start(ebox, False)
        vbox.pack_start(base, True)

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
        ListView.row_update(self, obj)
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
        else:
            obj = self.dbstate.db.get_object_from_handle(handle)
            pix = ThumbNails.get_thumbnail_image(
                        Utils.media_path_full(self.dbstate.db, obj.get_path()))
            self.image.set_from_pixbuf(pix)

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
              <menuitem action="FilterEdit"/>
            </menu>
            <menu action="BookMenu">
              <placeholder name="AddEditBook">
                <menuitem action="AddBook"/>
                <menuitem action="EditBook"/>
              </placeholder>
            </menu>
            <menu action="GoMenu">
              <placeholder name="CommonGo">
                <menuitem action="Back"/>
                <menuitem action="Forward"/>
                <separator/>
              </placeholder>
            </menu>
          </menubar>
          <toolbar name="ToolBar">
            <placeholder name="CommonNavigation">
              <toolitem action="Back"/>  
              <toolitem action="Forward"/>  
            </placeholder>
            <placeholder name="CommonEdit">
              <toolitem action="Add"/>
              <toolitem action="Edit"/>
              <toolitem action="Remove"/>
            </placeholder>
            <separator/>
            <toolitem action="OpenMedia"/>
          </toolbar>
          <popup name="Popup">
            <menuitem action="Back"/>
            <menuitem action="Forward"/>
            <separator/>
            <menuitem action="OpenMedia"/>
            <menuitem action="OpenContainingFolder"/>
            <separator/>
            <menuitem action="Add"/>
            <menuitem action="Edit"/>
            <menuitem action="Remove"/>
            <separator/>
            <menu name="QuickReport" action="QuickReport">
              <menuitem action="Dummy"/>
            </menu>
          </popup>
        </ui>'''

    def dummy_report(self, obj):
        """ For the xml UI definition of popup to work, the submenu 
            Quick Report must have an entry in the xml
            As this submenu will be dynamically built, we offer a dummy action
        """
        pass

    def add(self, obj):
        """Add a new media object to the media list"""
        try:
            EditMedia(self.dbstate, self.uistate, [], gen.lib.MediaObject())
        except Errors.WindowActiveError:
            pass

    def remove(self, obj):
        self.remove_selected_objects()

    def remove_object_from_handle(self, handle):
        """
        Remove the selected objects from the database after getting
        user verification.
        """
        the_lists = Utils.get_media_referents(handle, self.dbstate.db)
        object = self.dbstate.db.get_object_from_handle(handle)
        query = DeleteMediaQuery(self.dbstate, self.uistate, handle, the_lists)
        is_used = any(the_lists)
        return (query, is_used, object)

    def edit(self, obj):
        """
        Edit the selected objects in the EditMedia dialog
        """
        for handle in self.selected_handles():
            object = self.dbstate.db.get_object_from_handle(handle)
            try:
                EditMedia(self.dbstate, self.uistate, [], object)
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
