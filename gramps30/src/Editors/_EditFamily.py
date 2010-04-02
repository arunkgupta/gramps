#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
#               2009       Gary Burton
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
# python modules
#
#-------------------------------------------------------------------------
from bsddb import db as bsddb_db
from gettext import gettext as _
from DdTargets import DdTargets
import pickle
#-------------------------------------------------------------------------
#
# enable logging for error handling
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".")

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk
from gtk import glade
from gtk import gdk

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import Utils
import const
import Config
from BasicUtils import name_displayer
import gen.lib
import Errors
import DateHandler

from Editors import EditPrimary
from ReportBase import ReportUtils
from DisplayTabs import (EmbeddedList, EventEmbedList, SourceEmbedList, 
                         FamilyAttrEmbedList, NoteTab, GalleryTab, 
                         FamilyLdsEmbedList, ChildModel)
from GrampsWidgets import (PrivacyButton, MonitoredEntry, MonitoredDataType, 
                           IconButton, LinkBox, BasicLabel)
from ReportBase import CATEGORY_QR_FAMILY
from QuestionDialog import (ErrorDialog, RunDatabaseRepair, WarningDialog,
                            MessageHideDialog)

from Selectors import selector_factory
SelectPerson = selector_factory('Person')

_RETURN = gdk.keyval_from_name("Return")
_KP_ENTER = gdk.keyval_from_name("KP_Enter")
_LEFT_BUTTON = 1
_RIGHT_BUTTON = 3

class ChildEmbedList(EmbeddedList):
    """
    The child embed list is specific to the Edit Family dialog, so it
    is contained here instead of in DisplayTabs.
    """

    _HANDLE_COL = 10
    _DND_TYPE = DdTargets.PERSON_LINK

    _MSG = {
        'add'   : _('Create a new person and add the child to the family'),
        'del'   : _('Remove the child from the family'),
        'edit'  : _('Edit the child reference'),
        'share' : _('Add an existing person as a child of the family'),
        'up'	: _('Move the child up in the childrens list'),
        'down'	: _('Move the child down in the childrens list'),
        }

    _column_names = [
        (_('#'),0) ,
        (_('ID'),1) ,
        (_('Name'),11),
        (_('Gender'),3),
        (_('Paternal'),4),
        (_('Maternal'),5),
        (_('Birth Date'),12),
        (_('Death Date'),13),
        (_('Birth Place'),8),
        (_('Death Place'),9),
        ]
    
    def __init__(self, dbstate, uistate, track, family):
        """
        Create the object, storing the passed family value
        """
        self.family = family
        EmbeddedList.__init__(self, dbstate, uistate, track, _('Chil_dren'), 
                              ChildModel, share_button=True, move_buttons=True)

    def get_popup_menu_items(self):
        return [
            (False, True,  (gtk.STOCK_EDIT, _('Edit child')), 
                                            self.edit_child_button_clicked),
            (True, True, gtk.STOCK_ADD, self.add_button_clicked),
            (True, False, _('Add an existing child'), 
                                            self.share_button_clicked),
            (False, True,  (gtk.STOCK_EDIT, _('Edit relationship')), 
                                            self.edit_button_clicked),
            (True, True, gtk.STOCK_REMOVE, self.del_button_clicked),
            ]

    def get_middle_click(self):
        return self.edit_child_button_clicked

    def find_index(self, obj):
        """
        returns the index of the object within the associated data
        """
        reflist = [ref.ref for ref in self.family.get_child_ref_list()]
        return reflist.index(obj)

    def _find_row(self, x, y):
        row = self.tree.get_path_at_pos(x, y)
        if row == None:
            return len(self.family.get_child_ref_list())
        else:
            return row[0][0]

    def _handle_drag(self, row, obj):
        self.family.get_child_ref_list().insert(row, obj)
        self.changed = True
        self.rebuild()

    def _move(self, row_from, row_to, obj):
        dlist = self.family.get_child_ref_list()
        if row_from < row_to:
            dlist.insert(row_to, obj)
            del dlist[row_from]
        else:
            del dlist[row_from]
            dlist.insert(row_to-1, obj)
        self.changed = True
        self.rebuild()

    def build_columns(self):
        """
        We can't use the default build_columns in the base class, because
        we are using the custom TypeCellRenderer to handle father parent
        relationships. The Paternal and Maternal columns (columns 4 and 5)
        use this.
        """
        for column in self.columns:
            self.tree.remove_column(column)
        self.columns = []

        for pair in self.column_order():
            if not pair[0]:
                continue
            name = self._column_names[pair[1]][0]
            render = gtk.CellRendererText()
            column = gtk.TreeViewColumn(name, render, markup=pair[1])
            column.set_min_width(50)

            column.set_resizable(True)
            column.set_sort_column_id(self._column_names[pair[1]][1])
            self.columns.append(column)
            self.tree.append_column(column)

    def get_icon_name(self):
        return 'gramps-family'

    def is_empty(self):
        """
        The list is considered empty if the child list is empty.
        """
        return len(self.family.get_child_ref_list()) == 0

    def get_data(self):
        """
        Normally, get_data returns a list. However, we return family
        object here instead.
        """
        return self.family

    def column_order(self):
        return [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), 
                (0, 8), (0, 9)]

    def add_button_clicked(self, obj):
        from Editors import EditPerson
        person = gen.lib.Person()
        autoname = Config.get(Config.SURNAME_GUESSING)
        #_("Father's surname"), 
        #_("None"), 
        #_("Combination of mother's and father's surname"), 
        #_("Icelandic style"), 
        if autoname == 0:
            name = self.north_american()
        elif autoname == 2:
            name = self.latin_american()
        else:
            name = self.no_name()
        person.get_primary_name().set_surname(name[1])
        person.get_primary_name().set_surname_prefix(name[0])

        EditPerson(self.dbstate, self.uistate, self.track, person,
                   self.new_child_added)

    def new_child_added(self, person):
        ref = gen.lib.ChildRef()
        ref.ref = person.get_handle()
        self.family.add_child_ref(ref)
        self.rebuild()
        self.call_edit_childref(ref.ref)

    def child_ref_edited(self, person):
        self.rebuild()

    def share_button_clicked(self, obj):
        # it only makes sense to skip those who are already in the family
        skip_list = [self.family.get_father_handle(), \
                     self.family.get_mother_handle()] + \
                    [x.ref for x in self.family.get_child_ref_list() ]

        sel = SelectPerson(self.dbstate, self.uistate, self.track,
                           _("Select Child"), skip=skip_list)
        person = sel.run()
        
        if person:
            ref = gen.lib.ChildRef()
            ref.ref = person.get_handle()
            self.family.add_child_ref(ref)
            self.rebuild()
            self.call_edit_childref(ref.ref)

    def run(self, skip):
        skip_list = [ x for x in skip if x]
        SelectPerson(self.dbstate, self.uistate, self.track,
                     _("Select Child"), skip=skip_list)

    def del_button_clicked(self, obj):
        handle = self.get_selected()
        if handle:
            for ref in self.family.get_child_ref_list():
                if ref.ref == handle:
                    self.family.remove_child_ref(ref)
            self.rebuild()

    def edit_button_clicked(self, obj):
        handle = self.get_selected()
        if handle:
            self.call_edit_childref(handle)

    def call_edit_childref(self, handle):
        from Editors import EditChildRef

        for ref in self.family.get_child_ref_list():
            if ref.ref == handle:
                p = self.dbstate.db.get_person_from_handle(handle)
                n = name_displayer.display(p)
                try:
                    EditChildRef(n, self.dbstate, self.uistate, self.track,
                                 ref, self.child_ref_edited)
                except Errors.WindowActiveError:
                    pass
                break

    def edit_child_button_clicked(self, obj):
        handle = self.get_selected()
        if handle:
            from Editors import EditPerson

            for ref in self.family.get_child_ref_list():
                if ref.ref == handle:
                    p = self.dbstate.db.get_person_from_handle(handle)
                    try:
                        EditPerson(self.dbstate, self.uistate, self.track,
                               p, self.child_ref_edited)
                    except Errors.WindowActiveError:
                        pass
                    break
    
    def up_button_clicked(self, obj):
        handle = self.get_selected()
        if handle:
            pos = self.find_index(handle)
            if pos > 0 :
                self._move_up(pos,self.family.get_child_ref_list()[pos], 
                              selmethod=self.family.get_child_ref_list)
                
    def down_button_clicked(self, obj):
        ref = self.get_selected()
        if ref:
            pos = self.find_index(ref)
            if pos >=0 and pos < len(self.family.get_child_ref_list())-1:
                self._move_down(pos,self.family.get_child_ref_list()[pos], 
                                selmethod=self.family.get_child_ref_list)
    

    def drag_data_received(self, widget, context, x, y, sel_data, info, time):
        """
        Handle the standard gtk interface for drag_data_received.

        If the selection data is define, extract the value from sel_data.data,
        and decide if this is a move or a reorder.
        """
        if sel_data and sel_data.data:
            (mytype, selfid, obj, row_from) = pickle.loads(sel_data.data)

            # make sure this is the correct DND type for this object
            if mytype == self._DND_TYPE.drag_type:
                
                # determine the destination row
                row = self._find_row(x, y)

                # if the is same object, we have a move, otherwise,
                # it is a standard drag-n-drop
                
                if id(self) == selfid:
                    obj = self.get_data().get_child_ref_list()[row_from]
                    self._move(row_from, row, obj)
                else:
                    handle = obj
                    obj = gen.lib.ChildRef()
                    obj.ref = handle
                    self._handle_drag(row, obj)
                self.rebuild()
            elif self._DND_EXTRA and mytype == self._DND_EXTRA.drag_type:
                self.handle_extra_type(mytype, obj)

    def north_american(self):
        father_handle = self.family.get_father_handle()
        if father_handle:
            father = self.dbstate.db.get_person_from_handle(father_handle)
            pname = father.get_primary_name()
            return (pname.get_surname_prefix(), pname.get_surname())
        return ("","")

    def no_name(self):
        return ("","")

    def latin_american(self):
        if self.family:
            father_handle = self.family.get_father_handle()
            mother_handle = self.family.get_mother_handle()
            if not father_handle or not mother_handle:
                return ("","")
            father = self.dbstate.db.get_person_from_handle(father_handle)
            mother = self.dbstate.db.get_person_from_handle(mother_handle)
            if not father or not mother:
                return ("","")
            fsn = father.get_primary_name().get_surname()
            msn = mother.get_primary_name().get_surname()
            try:
                return ("", "%s %s" % (fsn.split()[0], msn.split()[0]))
            except:
                return ("", "")
        else:
            return ("", "")

class FastMaleFilter:

    def __init__(self, db):
        self.db = db

    def match(self, handle, db):
        value = self.db.get_raw_person_data(handle)
        return value[2] == gen.lib.Person.MALE

class FastFemaleFilter:

    def __init__(self, db):
        self.db = db

    def match(self, handle, db):
        value = self.db.get_raw_person_data(handle)
        return value[2] == gen.lib.Person.FEMALE

#-------------------------------------------------------------------------
#
# EditFamily
#
#-------------------------------------------------------------------------
class EditFamily(EditPrimary):

    QR_CATEGORY = CATEGORY_QR_FAMILY
    
    def __init__(self, dbstate, uistate, track, family):
        
        self.tooltips = gtk.Tooltips()
        EditPrimary.__init__(self, dbstate, uistate, track,
                             family, dbstate.db.get_family_from_handle,
                             dbstate.db.get_family_from_gramps_id)

        # look for the scenerio of a child and no parents on a new
        # family
        
        if self.added and self.obj.get_father_handle() == None and \
               self.obj.get_mother_handle() == None and \
               len(self.obj.get_child_ref_list()) == 1:
            self.add_parent = True
            if not Config.get(Config.FAMILY_WARN):
                for i in self.hidden:
                    i.set_sensitive(False)

                MessageHideDialog(
                    _("Adding parents to a person"),
                    _("It is possible to accidentally create multiple "
                      "families with the same parents. To help avoid "
                      "this problem, only the buttons to select parents "
                      "are available when you create a new family. The "
                      "remaining fields will become available after you "
                      "attempt to select a parent."),
                    Config.FAMILY_WARN)
        else:
            self.add_parent = False

    def empty_object(self):
        return gen.lib.Family()

    def _local_init(self):
        self.build_interface()

        self.mname  = None
        self.fname  = None

        self._add_db_signal('family-update', self.check_for_family_change)
        self._add_db_signal('family-delete', self.check_for_close)

        # Add a signal pick up changes to events, bug #1329
        self._add_db_signal('event-update', self.event_updated)
        
        self.added = self.obj.handle == None
        if self.added:
            self.obj.handle = Utils.create_id()
            
        self.load_data()

    def check_for_close(self, handles):
        if self.obj.get_handle() in handles:
            self._do_close()

    def check_for_family_change(self, handles):

        # check to see if the handle matches the current object
        if self.obj.get_handle() in handles:

            self.obj = self.dbstate.db.get_family_from_handle(self.obj.get_handle())
            self.reload_people()
            self.event_embed.rebuild()
            self.source_embed.rebuild()
            self.attr_embed.data = self.obj.get_attribute_list()
            self.attr_embed.rebuild()
            self.lds_embed.data = self.obj.get_lds_ord_list()
            self.lds_embed.rebuild()

            WarningDialog(
                _("Family has changed"),
                _("The family you are editing has changed. To make sure that the "
                  "database is not corrupted, GRAMPS has updated the family to "
                  "reflect these changes. Any edits you have made may have been lost."))

    def event_updated(self, obj):
        self.load_data()

    def reload_people(self):
        fhandle = self.obj.get_father_handle()
        self.update_father(fhandle)

        mhandle = self.obj.get_mother_handle()
        self.update_mother(mhandle)
        self.child_list.rebuild()

    def get_menu_title(self):
        if self.obj.get_handle():
            dialog_title = Utils.family_name(self.obj, self.db, _("New Family"))
            dialog_title = _("Family") + ': ' + dialog_title
        else:
            dialog_title = _("New Family")
        return dialog_title

    def build_menu_names(self, family):
        return (_('Edit Family'), self.get_menu_title())

    def build_interface(self):

        self.top = glade.XML(const.GLADE_FILE, "family_editor", "gramps")

        self.set_window(self.top.get_widget("family_editor"), None, self.get_menu_title())

        # restore window size
        width = Config.get(Config.FAMILY_WIDTH)
        height = Config.get(Config.FAMILY_HEIGHT)
        self.window.set_default_size(width, height)

        self.fbirth  = self.top.get_widget('fbirth')
        self.fdeath  = self.top.get_widget('fdeath')
        self.fbirth_label = self.top.get_widget('label578')
        self.fdeath_label = self.top.get_widget('label579')
        
        self.mbirth  = self.top.get_widget('mbirth')
        self.mdeath  = self.top.get_widget('mdeath')
        self.mbirth_label = self.top.get_widget('label567')
        self.mdeath_label = self.top.get_widget('label568')

        self.mbutton = self.top.get_widget('mbutton')
        self.mbutton2 = self.top.get_widget('mbutton2')
        self.fbutton = self.top.get_widget('fbutton')
        self.fbutton2 = self.top.get_widget('fbutton2')

        self.tooltips.set_tip(self.mbutton2,
                              _("Add a new person as the mother"))
        self.tooltips.set_tip(self.fbutton2,
                              _("Add a new person as the father"))

        self.mbox    = self.top.get_widget('mbox')
        self.fbox    = self.top.get_widget('fbox')
        
        #allow for a context menu
        self.set_contexteventbox(self.top.get_widget("eventboxtop"))

    def _connect_signals(self):
        self.define_ok_button(self.top.get_widget('ok'), self.save)
        self.define_cancel_button(self.top.get_widget('cancel'))

    def _can_be_replaced(self):
        pass

    def _setup_fields(self):
        
        self.private = PrivacyButton(
            self.top.get_widget('private'),
            self.obj,
            self.db.readonly)

        self.gid = MonitoredEntry(
            self.top.get_widget('gid'),
            self.obj.set_gramps_id,
            self.obj.get_gramps_id,
            self.db.readonly)
        
        self.marker = MonitoredDataType(
            self.top.get_widget('marker'), 
            self.obj.set_marker, 
            self.obj.get_marker, 
            self.db.readonly,
            self.db.get_marker_types(),
            )

        self.data_type = MonitoredDataType(
            self.top.get_widget('marriage_type'),
            self.obj.set_relationship,
            self.obj.get_relationship,
            self.db.readonly,
            self.db.get_family_relation_types(),
            )

    def load_data(self):
        fhandle = self.obj.get_father_handle()
        self.update_father(fhandle)

        mhandle = self.obj.get_mother_handle()
        self.update_mother(mhandle)

        self.phandles = [mhandle, fhandle] + \
                        [ x.ref for x in self.obj.get_child_ref_list()]
        
        self.phandles = [handle for handle in self.phandles if handle]

        self.mbutton.connect('clicked', self.mother_clicked)
        self.mbutton2.connect('clicked', self.add_mother_clicked)
        self.fbutton.connect('clicked', self.father_clicked)
        self.fbutton2.connect('clicked', self.add_father_clicked)

    def _create_tabbed_pages(self):

        notebook = gtk.Notebook()

        self.child_list = self._add_tab(
            notebook,
            ChildEmbedList(self.dbstate,self.uistate, self.track, self.obj))
        
        self.event_embed = EventEmbedList(self.dbstate, self.uistate, 
                                          self.track,self.obj)
        self.event_list = self._add_tab(notebook, self.event_embed)
            
        self.source_embed = SourceEmbedList(self.dbstate, self.uistate, 
                                            self.track, self.obj)
        self.src_list = self._add_tab(notebook, self.source_embed)
            
        self.attr_embed = FamilyAttrEmbedList(self.dbstate, self.uistate, 
                                              self.track,
                                              self.obj.get_attribute_list())
        self.attr_list = self._add_tab(notebook, self.attr_embed)
            
        self.note_tab = self._add_tab(
            notebook,
            NoteTab(self.dbstate, self.uistate, self.track,
                    self.obj.get_note_list(), self.get_menu_title(),
                    notetype=gen.lib.NoteType.FAMILY))
            
        self.gallery_tab = self._add_tab(
            notebook,
            GalleryTab(self.dbstate, self.uistate, self.track,
                       self.obj.get_media_list()))

        self.lds_embed = FamilyLdsEmbedList(self.dbstate, self.uistate, 
                                            self.track,
                                            self.obj.get_lds_ord_list())
        self.lds_list = self._add_tab(notebook, self.lds_embed)

        self._setup_notebook_tabs( notebook)
        notebook.show_all()

        self.hidden = (notebook, self.top.get_widget('info'))
        self.top.get_widget('vbox').pack_start(notebook, True)

    def update_father(self, handle):
        self.load_parent(handle, self.fbox, self.fbirth, self.fbirth_label,
                         self.fdeath, self.fdeath_label, self.fbutton,
                         self.fbutton2,
                         _("Select a person as the father"),
                         _("Remove the person as the father"))

    def update_mother(self, handle):
        self.load_parent(handle, self.mbox, self.mbirth, self.mbirth_label,
                         self.mdeath, self.mdeath_label, self.mbutton,
                         self.mbutton2,
                         _("Select a person as the mother"),
                         _("Remove the person as the mother"))

    def add_mother_clicked(self, obj):
        from Editors import EditPerson
        person = gen.lib.Person()
        person.set_gender(gen.lib.Person.FEMALE)
        autoname = Config.get(Config.SURNAME_GUESSING)
        #_("Father's surname"), 
        #_("None"), 
        #_("Combination of mother's and father's surname"), 
        #_("Icelandic style"), 
        if autoname == 2:
            name = self.latin_american_child("mother")
        else:
            name = self.no_name()
        person.get_primary_name().set_surname(name[1])
        person.get_primary_name().set_surname_prefix(name[0])
        EditPerson(self.dbstate, self.uistate, self.track, person,
                   self.new_mother_added)

    def add_father_clicked(self, obj):
        from Editors import EditPerson
        person = gen.lib.Person()
        person.set_gender(gen.lib.Person.MALE)
        autoname = Config.get(Config.SURNAME_GUESSING)
        #_("Father's surname"), 
        #_("None"), 
        #_("Combination of mother's and father's surname"), 
        #_("Icelandic style"), 
        if autoname == 0:
            name = self.north_american_child()
        elif autoname == 2:
            name = self.latin_american_child("father")
        else:
            name = self.no_name()
        person.get_primary_name().set_surname(name[1])
        person.get_primary_name().set_surname_prefix(name[0])
        EditPerson(self.dbstate, self.uistate, self.track,
                   person, self.new_father_added)

    def new_mother_added(self, person):
        for i in self.hidden:
            i.set_sensitive(True)
        self.obj.set_mother_handle(person.handle) 
        self.update_mother(person.handle)

    def new_father_added(self, person):
        for i in self.hidden:
            i.set_sensitive(True)
        self.obj.set_father_handle(person.handle) 
        self.update_father(person.handle)

    def mother_clicked(self, obj):
        for i in self.hidden:
            i.set_sensitive(True)

        handle = self.obj.get_mother_handle()

        if handle:
            self.obj.set_mother_handle(None)
            self.update_mother(None)
        else:
            data_filter = FastFemaleFilter(self.dbstate.db)
            sel = SelectPerson(self.dbstate, self.uistate, self.track,
                               _("Select Mother"),
                               filter=data_filter,
                               skip=[x.ref for x in self.obj.get_child_ref_list()])
            person = sel.run()

            if person:
                self.check_for_existing_family(self.obj.get_father_handle(),
                                               person.handle,
                                               self.obj.handle)

                self.obj.set_mother_handle(person.handle) 
                self.update_mother(person.handle)

    def on_change_father(self, selector_window, obj):
        if  obj.__class__ == gen.lib.Person:
            try:
                person = obj
                self.obj.set_father_handle(person.get_handle()) 
                self.update_father(person.get_handle())                    
            except:
                log.warn("Failed to update father: \n"
                         "obj returned from selector was: %s\n"
                         % (repr(obj),))                
                raise
            
        else:
            log.warn(
                "Object selector returned obj.__class__ = %s, it should "
                "have been of type %s." % (obj.__class__.__name__,
                                           gen.lib.Person.__name__))
            
        selector_window.close()

    def father_clicked(self, obj):
        for i in self.hidden:
            i.set_sensitive(True)

        handle = self.obj.get_father_handle()
        if handle:
            self.obj.set_father_handle(None)
            self.update_father(None)
        else:
            data_filter = FastMaleFilter(self.dbstate.db)
            sel = SelectPerson(self.dbstate, self.uistate, self.track,
                               _("Select Father"),
                               filter=data_filter,
                               skip=[x.ref for x in self.obj.get_child_ref_list()])
            person = sel.run()

            if person:

                self.check_for_existing_family(person.handle,
                                               self.obj.get_mother_handle(),
                                               self.obj.handle)
            
                self.obj.set_father_handle(person.handle) 
                self.update_father(person.handle)

    def check_for_existing_family(self, father_handle, mother_handle,
                                  family_handle):

        if father_handle:
            father = self.dbstate.db.get_person_from_handle(father_handle)
            ffam = set(father.get_family_handle_list())
            if mother_handle:
                mother = self.dbstate.db.get_person_from_handle(mother_handle)
                mfam = set(mother.get_family_handle_list())
                common = list(mfam.intersection(ffam))
                if len(common) > 0:
                    if self.add_parent or self.obj.handle not in common:
                        WarningDialog(
                            _('Duplicate Family'),
                            _('A family with these parents already exists '
                              'in the database. If you save, you will create '
                              'a duplicate family. It is recommended that '
                              'you cancel the editing of this window, and '
                              'select the existing family'))

    def edit_person(self, obj, event, handle):
        if button_activated(event, _LEFT_BUTTON):
            from _EditPerson import EditPerson
            try:
                person = self.db.get_person_from_handle(handle)
                EditPerson(self.dbstate, self.uistate,
                           self.track, person)
            except Errors.WindowActiveError:
                pass

    def load_parent(self, handle, box, birth_obj, birth_label, death_obj,
                    death_label, btn_obj, btn2_obj, add_msg, del_msg):

        is_used = handle != None

        for i in box.get_children():
            box.remove(i)

        try:
            btn_obj.remove(btn_obj.get_children()[0])
        except IndexError:
            pass
        
        if is_used:
            btn2_obj.hide()
            db = self.db
            person = db.get_person_from_handle(handle)
            name = "%s [%s]" % (name_displayer.display(person),
                                person.gramps_id)
            birth = ReportUtils.get_birth_or_fallback(db, person)
            if birth and birth.get_type() == gen.lib.EventType.BAPTISM:
                birth_label.set_label(_("Baptism:"))

            death = ReportUtils.get_death_or_fallback(db, person)
            if death and death.get_type() == gen.lib.EventType.BURIAL:
                death_label.set_label(_("Burial:"))

            del_image = gtk.Image()
            del_image.show()
            del_image.set_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)
            self.tooltips.set_tip(btn_obj, del_msg)
            btn_obj.add(del_image)

            edit_btn = IconButton(self.edit_person, person.handle)
            self.tooltips.set_tip(edit_btn, _('Edit %s') % name)

            box.pack_start(LinkBox(
                BasicLabel(name),
                edit_btn)
                )
        else:
            btn2_obj.show()
            name = ""
            birth = None
            death = None

            add_image = gtk.Image()
            add_image.show()
            add_image.set_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON)
            self.tooltips.set_tip(btn_obj, add_msg)
            btn_obj.add(add_image)

        if birth:
            birth_str = DateHandler.displayer.display(birth.get_date_object())
            birth_obj.set_text(birth_str)

        if death:
            death_str = DateHandler.displayer.display(death.get_date_object())
            death_obj.set_text(death_str)

    def fix_parent_handles(self, orig_handle, new_handle, trans):
        if orig_handle != new_handle:
            if orig_handle:
                person = self.db.get_person_from_handle(orig_handle)
                person.family_list.remove(self.obj.handle)
                self.db.commit_person(person, trans)
            if new_handle:
                person = self.db.get_person_from_handle(new_handle)
                if self.obj.handle not in person.family_list:
                    person.family_list.append(self.obj.handle)
                self.db.commit_person(person, trans)

    def object_is_empty(self):
        return self.obj.get_father_handle() == None and \
               self.obj.get_mother_handle() == None and \
               len(self.obj.get_child_ref_list()) == 0
            
    def save(self, *obj):
        try:
            self.__do_save()
        except bsddb_db.DBRunRecoveryError, msg:
            RunDatabaseRepair(msg[1])

    def __do_save(self):
        self.ok_button.set_sensitive(False)

        if not self.added:
            original = self.db.get_family_from_handle(self.obj.handle)
        else:
            original = None

        # do some basic checks

        child_list = [ ref.ref for ref in self.obj.get_child_ref_list() ]

        if self.obj.get_father_handle() in child_list:

            father = self.db.get_person_from_handle(self.obj.get_father_handle())
            name = "%s [%s]" % (name_displayer.display(father),
                                father.gramps_id)
            ErrorDialog(_("A father cannot be his own child"),
                                       _("%s is listed as both the father and child "
                                         "of the family.") % name)
            self.ok_button.set_sensitive(True)
            return
        elif self.obj.get_mother_handle() in child_list:

            mother = self.db.get_person_from_handle(self.obj.get_mother_handle())
            name = "%s [%s]" % (name_displayer.display(mother),
                                mother.gramps_id)
            ErrorDialog(_("A mother cannot be her own child"),
                                       _("%s is listed as both the mother and child "
                                         "of the family.") % name)
            self.ok_button.set_sensitive(True)
            return

        if not original and self.object_is_empty():
            ErrorDialog(
                _("Cannot save family"),
                _("No data exists for this family. "
                  "Please enter data or cancel the edit."))
            self.ok_button.set_sensitive(True)
            return
        
        (uses_dupe_id, id) = self._uses_duplicate_id()
        if uses_dupe_id:
            msg1 = _("Cannot save family. ID already exists.")
            msg2 = _("You have attempted to use the existing GRAMPS ID with "
                         "value %(id)s. This value is already used. Please "
                         "enter a different ID or leave "
                         "blank to get the next available ID value.") % {
                         'id' : id}
            ErrorDialog(msg1, msg2)
            self.ok_button.set_sensitive(True)
            return

        # We disconnect the callbacks to all signals we connected earlier.
        # This prevents the signals originating in any of the following
        # commits from being caught by us again.
        for key in self.signal_keys:
            self.db.disconnect(key)
        self.signal_keys = []
            
        if not original and not self.object_is_empty():
            trans = self.db.transaction_begin()

            # find the father, add the family handle to the father
            handle = self.obj.get_father_handle()
            if handle:
                parent = self.db.get_person_from_handle(handle)
                parent.add_family_handle(self.obj.handle)
                self.db.commit_person(parent, trans)

            # find the mother, add the family handle to the mother
            handle = self.obj.get_mother_handle()
            if handle:
                parent = self.db.get_person_from_handle(handle)
                parent.add_family_handle(self.obj.handle)
                self.db.commit_person(parent, trans)
                
            # for each child, add the family handle to the child
            for ref in self.obj.get_child_ref_list():
                child = self.db.get_person_from_handle(ref.ref)
                # fix - relationships need to be extracted from the list
                child.add_parent_family_handle(self.obj.handle)
                self.db.commit_person(child, trans)

            self.db.add_family(self.obj, trans)
            self.db.transaction_commit(trans, _("Add Family"))
        elif cmp(original.serialize(),self.obj.serialize()):

            trans = self.db.transaction_begin()

            self.fix_parent_handles(original.get_father_handle(),
                                    self.obj.get_father_handle(), trans)
            self.fix_parent_handles(original.get_mother_handle(),
                                    self.obj.get_mother_handle(), trans)

            orig_set = set(original.get_child_ref_list())
            new_set = set(self.obj.get_child_ref_list())

            # remove the family from children which have been removed
            for ref in orig_set.difference(new_set):
                person = self.db.get_person_from_handle(ref.ref)
                person.remove_parent_family_handle(self.obj.handle)
                self.db.commit_person(person, trans)
            
            # add the family to children which have been added
            for ref in new_set.difference(orig_set):
                person = self.db.get_person_from_handle(ref.ref)
                person.add_parent_family_handle(self.obj.handle)
                self.db.commit_person(person, trans)

            if self.object_is_empty():
                self.db.remove_family(self.obj.handle, trans)
            else:
                if not self.obj.get_gramps_id():
                    self.obj.set_gramps_id(self.db.find_next_family_gramps_id())
                self.db.commit_family(self.obj, trans)
            self.db.transaction_commit(trans, _("Edit Family"))

        self._do_close()

    def _cleanup_on_exit(self):
        (width, height) = self.window.get_size()
        Config.set(Config.FAMILY_WIDTH, width)
        Config.set(Config.FAMILY_HEIGHT, height)
        Config.sync()

    def no_name(self):
        """
        Default surname guess.
        """
        return ("","")

    def north_american_child(self):
        """
        If SURNAME_GUESSING is north american, then find a child
        and return their name for the father.
        """
        # for each child, find one with a last name
        for ref in self.obj.get_child_ref_list():
            child = self.db.get_person_from_handle(ref.ref)
            if child:
                pname = child.get_primary_name()
                return (pname.get_surname_prefix(), pname.get_surname())
        return ("", "")

    def latin_american_child(self, parent):
        """
        If SURNAME_GUESSING is latin american, then find a child
        and return their name for the father or mother.

        parent = "mother" | "father"
        """
        # for each child, find one with a last name
        for ref in self.obj.get_child_ref_list():
            child = self.db.get_person_from_handle(ref.ref)
            if child:
                pname = child.get_primary_name()
                prefix, surname = (pname.get_surname_prefix(),
                                   pname.get_surname())
                if " " in surname:
                    fsn, msn = surname.split(" ", 1)
                else:
                    fsn, msn = surname, surname
                if parent == "father":
                    return prefix, fsn
                elif parent == "mother":    
                    return prefix, msn
                else:    
                    return ("", "")
        return ("", "")

def button_activated(event, mouse_button):
    if (event.type == gtk.gdk.BUTTON_PRESS and \
        event.button == mouse_button) or \
       (event.type == gtk.gdk.KEY_PRESS and \
        event.keyval in (_RETURN, _KP_ENTER)):
        return True
    else:
        return False

