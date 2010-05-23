#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2008  Donald N. Allingham
# Copyright (C) 2009  Douglas S. Blank
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

"""
Provide a simplified table creation interface
"""

import cgi
import copy
from gen.ggettext import gettext as _

import gen.lib
import Errors
import config
import DateHandler

def on_table_click(obj, table):
    """
    This is a workaround for a weird issue in Python. It occurs when a
    click occurs faster than gramps can respond, and the
    gobject.timeout_add ends up being called recursively. For some
    reason some of the methods are removed from the Table object
    making future calls invalid.
    """
    if hasattr(table, "_callback_leftclick"):
        return table.on_table_click(obj)

def on_table_doubleclick(obj, path, view_column, table):
    """
    This is a workaround for a weird issue in Python. It occurs when a
    double-click occurs faster than gramps can respond, and the
    gobject.timeout_add ends up being called recursively. For some
    reason some of the methods are removed from the Table object
    making future calls invalid.
    """
    if hasattr(table, "_callback_leftdouble"):
        return table.on_table_doubleclick(obj, path, view_column)

class SimpleTable(object):
    """
    Provide a simplified table creation interface.
    """

    def __init__(self, access, title=None):
        """
        Initialize the class with a simpledb
        """
        self.access = access
        self.title = title
        self.__columns = []
        self.__cell_markup = {} # [col][row] = "<b>data</b>"
        self.__cell_type = {} # [col] = "text"
        self.__rows = []
        self.__raw_data = []
        self.__link = []
        self.__sort_col = None
        self.__sort_reverse = False
        self.__link_col = None
        self._callback_leftclick = None
        self._callback_leftdouble = None
        self.model_index_of_column = {}

    def get_row_count(self):
        return len(self.__rows)

    def get_row(self, index):
        return self.__rows[index]

    def get_raw_data(self, index):
        return self.__raw_data[index]

    def columns(self, *cols):
        """
        Set the columns
        """
        self.__columns = [unicode(col) for col in cols]
        self.__sort_vals = [[] for i in range(len(self.__columns))]

    def set_callback(self, which, callback):
        """
        Override (or add) a function for click/double-click
        """
        if which == "leftclick":
            self._callback_leftclick = callback
        elif which == "leftdouble":
            self._callback_leftdouble = callback

    def on_table_doubleclick(self, obj, path, view_column):
        """
        Handle events on tables. obj is a treeview
        """
        from gui.editors import (EditPerson, EditEvent, EditFamily, EditSource,
                                 EditPlace, EditRepository, EditNote, EditMedia)
        selection = obj.get_selection()
        store, node = selection.get_selected()
        if not node:
            return
        index = store.get_value(node, 0) # index
        if self._callback_leftdouble:
            self._callback_leftdouble(store.get_value(node, 1))
            return True
        elif self.__link[index]:
            objclass, handle = self.__link[index]
            if objclass == 'Person':
                person = self.access.dbase.get_person_from_handle(handle)
                try:
                    EditPerson(self.simpledoc.doc.dbstate, 
                               self.simpledoc.doc.uistate, [], person)
                    return True # handled event
                except Errors.WindowActiveError:
                    pass
            elif objclass == 'Event':
                event = self.access.dbase.get_event_from_handle(handle)
                try:
                    EditEvent(self.simpledoc.doc.dbstate, 
                              self.simpledoc.doc.uistate, [], event)
                    return True # handled event
                except Errors.WindowActiveError:
                    pass
            elif objclass == 'Family':
                ref = self.access.dbase.get_family_from_handle(handle)
                try:
                    EditFamily(self.simpledoc.doc.dbstate, 
                               self.simpledoc.doc.uistate, [], ref)
                    return True # handled event
                except Errors.WindowActiveError:
                    pass
            elif objclass == 'Source':
                ref = self.access.dbase.get_source_from_handle(handle)
                try:
                    EditSource(self.simpledoc.doc.dbstate, 
                               self.simpledoc.doc.uistate, [], ref)
                    return True # handled event
                except Errors.WindowActiveError:
                    pass
            elif objclass == 'Place':
                ref = self.access.dbase.get_place_from_handle(handle)
                try:
                    EditPlace(self.simpledoc.doc.dbstate, 
                               self.simpledoc.doc.uistate, [], ref)
                    return True # handled event
                except Errors.WindowActiveError:
                    pass
            elif objclass == 'Repository':
                ref = self.access.dbase.get_repository_from_handle(handle)
                try:
                    EditRepository(self.simpledoc.doc.dbstate, 
                               self.simpledoc.doc.uistate, [], ref)
                    return True # handled event
                except Errors.WindowActiveError:
                    pass
            elif objclass == 'Note':
                ref = self.access.dbase.get_note_from_handle(handle)
                try:
                    EditNote(self.simpledoc.doc.dbstate, 
                             self.simpledoc.doc.uistate, [], ref)
                    return True # handled event
                except Errors.WindowActiveError:
                    pass
            elif objclass in ['Media', 'MediaObject']:
                ref = self.access.dbase.get_object_from_handle(handle)
                try:
                    EditMedia(self.simpledoc.doc.dbstate, 
                              self.simpledoc.doc.uistate, [], ref)
                    return True # handled event
                except Errors.WindowActiveError:
                    pass
            elif objclass == 'PersonList':
                from QuickReports import run_quick_report_by_name
                run_quick_report_by_name(self.simpledoc.doc.dbstate,
                                         self.simpledoc.doc.uistate, 
                                         'filterbyname', 
                                         'list of people',
                                         handles=handle)
            elif objclass == 'Filter':
                from QuickReports import run_quick_report_by_name
                run_quick_report_by_name(self.simpledoc.doc.dbstate,
                                         self.simpledoc.doc.uistate, 
                                         'filterbyname', 
                                         handle[0])
        return False # didn't handle event

    def on_table_click(self, obj):
        """
        Handle events on tables. obj is a treeview
        """
        selection = obj.get_selection()
        store, node = selection.get_selected()
        if not node:
            return
        index = store.get_value(node, 0) # index
        if self._callback_leftclick:
            self._callback_leftclick(store.get_value(node, 1))
            return True
        elif self.__link[index]:
            objclass, handle = self.__link[index]
            if objclass == 'Person':
                import gobject
                # If you emmit the signal here and it causes this table to be deleted, 
                # then you'll crash Python:
                #self.simpledoc.doc.uistate.set_active(handle, 'Person')
                # So, let's return from this, then change the active person:
                return gobject.timeout_add(100, self.simpledoc.doc.uistate.set_active, handle, 'Person')
                return True
        return False # didn't handle event

    def row_sort_val(self, col, val):
        """
        Add a row of data to sort by.
        """
        self.__sort_vals[col].append(val) 

    def set_link_col(self, col):
        """
        Manually sets the column that defines link.
        col is either a number (column) or a (object_type_name, handle).
        """
        self.__link_col = col

    def row(self, *data):
        """
        Add a row of data.
        """
        retval = [] 
        link   = None
        row = len(self.__rows)
        self.__raw_data.append([])
        for col in range(len(data)):
            item = data[col]
            self.__raw_data[-1].append(item)
            # FIXME: add better text representations of these objects
            if item is None:
                retval.append("")
            elif isinstance(item, basestring):
                if item == "checkbox": 
                    retval.append("")
                    self.set_cell_type(col, "checkbox")
                else:
                    retval.append(item)
            elif isinstance(item, (int, float, long)):
                retval.append(item)
                self.row_sort_val(col, item)
            elif isinstance(item, gen.lib.Person):
                name = self.access.name(item)
                retval.append(name)
                if (self.__link_col == col or link is None):
                    link = ('Person', item.handle)
            elif isinstance(item, gen.lib.Family): 
                father = self.access.father(item)
                mother = self.access.mother(item)
                if father:
                    text = self.access.name(father)
                else:
                    text = _("Unknown father")
                text += " " + _("and")
                if mother:
                    text += " " + self.access.name(mother)
                else:
                    text += " " + _("Unknown mother")
                retval.append(text)
                if (self.__link_col == col or link is None):
                    link = ('Family', item.handle)
            elif isinstance(item, gen.lib.Source): 
                retval.append(item.gramps_id)
                if (self.__link_col == col or link is None):
                    link = ('Source', item.handle)
            elif isinstance(item, gen.lib.Event):
                name = self.access.event_type(item)
                retval.append(name)
                if (self.__link_col == col or link is None):
                    link = ('Event', item.handle)
            elif isinstance(item, gen.lib.MediaObject):
                retval.append(item.gramps_id)
                if (self.__link_col == col or link is None):
                    link = ('Media', item.handle)
            elif isinstance(item, gen.lib.Place):
                retval.append(item.gramps_id)
                if (self.__link_col == col or link is None):
                    link = ('Place', item.handle)
            elif isinstance(item, gen.lib.Repository):
                retval.append(item.gramps_id)
                if (self.__link_col == col or link is None):
                    link = ('Repository', item.handle)
            elif isinstance(item, gen.lib.Note):
                retval.append(item.gramps_id)
                if (self.__link_col == col or link is None):
                    link = ('Note', item.handle)
            elif isinstance(item, gen.lib.Date):
                text = DateHandler.displayer.display(item)
                retval.append(text)
                if item.get_valid():
                    if item.format:
                        self.set_cell_markup(col, row, 
                                             item.format % cgi.escape(text))
                    self.row_sort_val(col, item.sortval)
                else:
                    # sort before others:
                    self.row_sort_val(col, -1)
                    # give formatted version:
                    invalid_date_format = config.get('preferences.invalid-date-format')
                    self.set_cell_markup(col, row,
                                         invalid_date_format % cgi.escape(text))
                if (self.__link_col == col or link is None):
                    link = ('Date', item)
            elif isinstance(item, gen.lib.Span):
                text = str(item)
                retval.append(text)
                self.row_sort_val(col, item)
            elif isinstance(item, list): # [text, "PersonList", handle, ...]
                retval.append(item[0])
                link = (item[1], item[2:])
            else:
                retval.append(str(item))
        self.__link.append(link)
        self.__rows.append(retval)

    def sort(self, column_name, reverse=False):
        self.__sort_col = column_name
        self.__sort_reverse = reverse

    def __sort(self):
        idx = self.__columns.index(self.__sort_col)
        # FIXME: move raw_data with this
        if self.__sort_reverse:
            self.__rows.sort(lambda a, b: -cmp(a[idx],b[idx]))
        else:
            self.__rows.sort(lambda a, b: cmp(a[idx],b[idx]))

    def toggle(self, obj, path, col):
        """
        obj - column widget
        path - row
        col - column
        """
        self.treeview.get_model()[path][col] = not \
            self.treeview.get_model()[path][col]

    def write(self, document):
        self.simpledoc = document # simpledoc; simpledoc.doc = docgen object
        if self.simpledoc.doc.type == "standard":
            doc = self.simpledoc.doc
            columns = len(self.__columns)
            doc.start_table('simple', 'Table')
            doc._tbl.set_column_widths([100/columns] * columns)
            doc._tbl.set_columns(columns)
            if self.title:
                doc.start_row()
                doc.start_cell('TableHead', span=columns) 
                doc.start_paragraph('TableTitle')
                doc.write_text(_(self.title))
                doc.end_paragraph()
                doc.end_cell()
                doc.end_row()
            if self.__sort_col:
                self.__sort()
            doc.start_row()
            for col in self.__columns:
                doc.start_cell('TableHeaderCell', span=1) 
                doc.write_text(col, 'TableTitle')
                doc.end_cell()
            doc.end_row()
            index = 0
            for row in self.__rows:
                doc.start_row()
                for col in row:
                    doc.start_cell('TableDataCell', span=1) 
                    obj_type, handle = None, None
                    if isinstance(self.__link_col, tuple):
                        obj_type, handle = self.__link_col
                    elif isinstance(self.__link_col, list):
                        obj_type, handle = self.__link_col[index]
                    elif self.__link[index]:
                        obj_type, handle = self.__link[index]
                    if obj_type:
                        if obj_type.lower() == "url":
                            doc.start_link(handle)
                        else:
                            doc.start_link("/%s/%s" % 
                                           (obj_type.lower(), handle))
                    doc.write_text(col, 'Normal')
                    if obj_type:
                        doc.stop_link()
                    doc.end_cell()
                doc.end_row()
                index += 1
            doc.end_table()
            doc.start_paragraph("Normal")
            doc.end_paragraph()
        elif self.simpledoc.doc.type == "gtk":
            import gtk
            buffer = self.simpledoc.doc.buffer
            text_view = self.simpledoc.doc.text_view
            model_index = 1 # start after index
            if self.__sort_col:
                sort_index = self.__columns.index(self.__sort_col)
            else:
                sort_index = 0
            treeview = gtk.TreeView()
            treeview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
            treeview.connect('row-activated', on_table_doubleclick, self)
            treeview.connect('cursor-changed', on_table_click, self)
            renderer = gtk.CellRendererText()
            types = [int] # index
            cnt = 0
            sort_data = []
            sort_data_types = []
            for col in self.__columns:
                if self.get_cell_type(cnt) == "text":
                    types.append(str)
                    if self.get_cell_markup(cnt):
                        column = gtk.TreeViewColumn(col,renderer,markup=model_index)
                    else:
                        column = gtk.TreeViewColumn(col,renderer,text=model_index)
                elif self.get_cell_type(cnt) == "checkbox":
                    types.append(bool)
                    toggle_renderer = gtk.CellRendererToggle()
                    toggle_renderer.set_property('activatable', True)
                    toggle_renderer.connect("toggled", self.toggle, model_index)
                    column = gtk.TreeViewColumn(col, toggle_renderer)
                    column.add_attribute(toggle_renderer, "active", model_index)
                column.set_resizable(True)
                if self.__sort_vals[cnt] != []:
                    sort_data.append(self.__sort_vals[cnt])
                    column.set_sort_column_id(len(self.__columns) + 
                                              len(sort_data))
                    sort_data_types.append(int)
                else:
                    column.set_sort_column_id(model_index)
                treeview.append_column(column)
                self.model_index_of_column[col] = model_index
                #if model_index == sort_index:
                # FIXME: what to set here?    
                model_index += 1
                cnt += 1
            if self.title:
                self.simpledoc.paragraph(self.title)
            # Make a GUI to put the tree view in
            types += sort_data_types
            model = gtk.ListStore(*types)
            treeview.set_model(model)
            iter = buffer.get_end_iter()
            anchor = buffer.create_child_anchor(iter)
            text_view.add_child_at_anchor(treeview, anchor)
            self.treeview= treeview
            count = 0
            for data in self.__rows:
                col = 0
                rowdata = []
                for cell in data:
                    rowdata.append(self.get_cell_markup(col, count, cell))
                    col += 1
                try:
                    model.append(row=([count] + list(rowdata) + [col[count] for col in sort_data]))
                except:
                    print "error in row %d: data: %s, sort data: %d" % (count, rowdata, len(sort_data[0]))
                count += 1
            text_view.show_all()
            self.simpledoc.paragraph("")
            self.simpledoc.paragraph("")

    def get_cell_markup(self, x, y=None, data=None):
        """
        See if a column has formatting (if x and y are supplied) or
        see if a cell has formatting. If it does, return the formatted 
        string, otherwise return data that is escaped (if that column
        has formatting), or just the plain data.
        """
        if x in self.__cell_markup:
            if y is None: 
                return True # markup for this column
            elif y in self.__cell_markup[x]:
                return self.__cell_markup[x][y]
            else:
                return cgi.escape(data)
        else:
            if y is None: 
                return False # no markup for this column
            else:
                return data

    def get_cell_type(self, col):
        """
        See if a column has a type, else return "text" as default.
        """
        if col in self.__cell_type:
            return self.__cell_type[col]
        return "text"

    def set_cell_markup(self, x, y, data):
        """
        Set the cell at position [x][y] to a formatted string.
        """
        col_dict = self.__cell_markup.get(x, {})
        col_dict[y] = data
        self.__cell_markup[x] = col_dict

    def set_cell_type(self, col, value):
        """
        Set the cell type at position [x].
        """
        self.__cell_type[col] = value
