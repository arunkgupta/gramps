#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
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

"""Tools/Analysis and Exploration/Compare Individual Events"""

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
import os
import sys

#------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#------------------------------------------------------------------------
import gtk
from gtk import glade

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from Filters import GenericFilter, build_filter_menu, Rules
import Sort
import Utils
from docgen import ODSTab
import const
import Errors
import DateHandler
from QuestionDialog import WarningDialog
from PluginUtils import Tool
from gen.plug import PluginManager
from ReportBase import ReportUtils
import GrampsDisplay 
import ManagedWindow
from TransUtils import sgettext as _


#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = '%s_-_Tools' % const.URL_MANUAL_PAGE
WIKI_HELP_SEC = _('manual|Compare_Individual_Events...')

#------------------------------------------------------------------------
#
# EventCmp
#
#------------------------------------------------------------------------
class TableReport(object):
    """
    This class provides an interface for the spreadsheet table
    used to save the data into the file.
    """

    def __init__(self,filename,doc):
        self.filename = filename
        self.doc = doc
        
    def initialize(self,cols):
        self.doc.open(self.filename)
        self.doc.start_page()

    def finalize(self):
        self.doc.end_page()
        self.doc.close()
        
    def write_table_data(self,data,skip_columns=[]):
        self.doc.start_row()
        index = -1
        for item in data:
            index += 1
            if index not in skip_columns:
                self.doc.write_cell(item)
        self.doc.end_row()

    def set_row(self,val):
        self.row = val + 2
        
    def write_table_head(self,data):
        self.doc.start_row()
        for item in data:
            self.doc.write_cell(item)
        self.doc.end_row()

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class EventComparison(Tool.Tool,ManagedWindow.ManagedWindow):
    def __init__(self, dbstate, uistate, options_class, name, callback=None):
        self.dbstate = dbstate
        self.uistate = uistate
        
        Tool.Tool.__init__(self,dbstate, options_class, name)
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self)

        base = os.path.dirname(__file__)
        self.glade_file = base + os.sep + "eventcmp.glade"
        self.qual = 0

        self.filterDialog = glade.XML(self.glade_file,"filters","gramps")
        self.filterDialog.signal_autoconnect({
            "on_apply_clicked"       : self.on_apply_clicked,
            "on_editor_clicked"      : self.filter_editor_clicked,
            "on_filters_delete_event": self.close,
            "on_help_clicked"        : self.on_help_clicked,
            "destroy_passed_object"  : self.close
            })
    
        window = self.filterDialog.get_widget("filters")
        self.filters = self.filterDialog.get_widget("filter_list")
        self.label = _('Event comparison filter selection')
        self.set_window(window,self.filterDialog.get_widget('title'),
                        self.label)

        all = GenericFilter()
        all.set_name(_("Entire Database"))
        all.add_rule(Rules.Person.Everyone([]))

        the_filters = [all]
        from Filters import CustomFilters
        the_filters.extend(CustomFilters.get_filters('Person'))

        self.filter_menu = build_filter_menu(the_filters)
        filter_num = self.options.handler.options_dict['filter']
        self.filter_menu.set_active(filter_num)
        self.filter_menu.show()
        self.filters.set_menu(self.filter_menu)

        self.show()

    def on_help_clicked(self, obj):
        """Display the relevant portion of GRAMPS manual"""
        GrampsDisplay.help(webpage=WIKI_HELP_PAGE, section=WIKI_HELP_SEC)

    def build_menu_names(self, obj):
        return (_("Filter selection"),_("Event Comparison tool"))

    def filter_editor_clicked(self, obj):
        import FilterEditor
        try:
            FilterEditor.FilterEditor('Person',const.CUSTOM_FILTERS,
                                      self.dbstate,self.uistate)
        except Errors.WindowActiveError:
            pass

    def on_apply_clicked(self, obj):
        cfilter = self.filter_menu.get_active().get_data("filter")

        progress_bar = Utils.ProgressMeter(_('Comparing events'),'')
        progress_bar.set_pass(_('Selecting people'),1)

        plist = cfilter.apply(self.db,
                              self.db.get_person_handles(sort_handles=False))

        progress_bar.step()
        progress_bar.close()
        self.options.handler.options_dict['filter'] = self.filters.get_history()
        # Save options
        self.options.handler.save_options()

        if len(plist) == 0:
            WarningDialog(_("No matches were found"))
        else:
            DisplayChart(self.dbstate,self.uistate,plist,self.track)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def by_value(first,second):
    return cmp(second[0],first[0])

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def fix(line):
    l = line.strip().replace('&','&amp;').replace('>','&gt;')
    return l.replace(l,'<','&lt;').replace(l,'"','&quot;')

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class DisplayChart(ManagedWindow.ManagedWindow):
    def __init__(self,dbstate,uistate,people_list,track):
        self.dbstate = dbstate
        self.uistate = uistate

        ManagedWindow.ManagedWindow.__init__(self, uistate, track, self)

        self.db = dbstate.db
        self.my_list = people_list
        self.row_data = []
        self.save_form = None
        
        base = os.path.dirname(__file__)
        self.glade_file = base + os.sep + "eventcmp.glade"

        self.topDialog = glade.XML(self.glade_file,"view","gramps")
        self.topDialog.signal_autoconnect({
            "on_write_table"        : self.on_write_table,
            "destroy_passed_object" : self.close,
            "on_help_clicked"       : self.on_help_clicked,
            })

        window = self.topDialog.get_widget("view")
        self.set_window(window, self.topDialog.get_widget('title'),
                        _('Event Comparison Results'))
                        
        self.eventlist = self.topDialog.get_widget('treeview')
        self.sort = Sort.Sort(self.db)
        self.my_list.sort(self.sort.by_last_name)

        self.event_titles = self.make_event_titles()
        
        self.table_titles = [_("Person"),_("ID")]
        for event_name in self.event_titles:
            self.table_titles.append(event_name + _(" Date"))
            self.table_titles.append('sort') # This won't be shown in a tree
            self.table_titles.append(event_name + _(" Place"))
            
        self.build_row_data()
        self.draw_display()
        self.show()

    def on_help_clicked(self, obj):
        """Display the relevant portion of GRAMPS manual"""
        GrampsDisplay.help(webpage=WIKI_HELP_PAGE, section=WIKI_HELP_SEC)

    def build_menu_names(self, obj):
        return (_("Event Comparison Results"),None)

    def draw_display(self):

        model_index = 0
        tree_index = 0
        mylist = []
        renderer = gtk.CellRendererText()
        for title in self.table_titles:
            mylist.append(str)
            if title == 'sort':
                # This will override the previously defined column
                self.eventlist.get_column(
                    tree_index-1).set_sort_column_id(model_index)
            else:
                column = gtk.TreeViewColumn(title,renderer,text=model_index)
                column.set_sort_column_id(model_index)
                self.eventlist.append_column(column)
                # This one numbers the tree columns: increment on new column
                tree_index = tree_index + 1
            # This one numbers the model columns: always increment
            model_index = model_index + 1

        model = gtk.ListStore(*mylist)
        self.eventlist.set_model(model)

        self.progress_bar.set_pass(_('Building display'),len(self.row_data))
        for data in self.row_data:
            model.append(row=list(data))
            self.progress_bar.step()
        self.progress_bar.close()

    def build_row_data(self):
        self.progress_bar = Utils.ProgressMeter(_('Comparing Events'),'')
        self.progress_bar.set_pass(_('Building data'),len(self.my_list))
        for individual_id in self.my_list:
            individual = self.db.get_person_from_handle(individual_id)
            name = individual.get_primary_name().get_name()
            gid = individual.get_gramps_id()

            the_map = {}
            for ievent_ref in individual.get_event_ref_list():
                ievent = self.db.get_event_from_handle(ievent_ref.ref)
                event_name = str(ievent.get_type())
                if event_name in the_map:
                    the_map[event_name].append(ievent_ref.ref)
                else:
                    the_map[event_name] = [ievent_ref.ref]

            first = 1
            done = 0
            while done == 0:
                added = 0
                if first:
                    tlist = [name,gid]
                else:
                    tlist = ["",""]
                for ename in self.event_titles:
                    if ename in the_map and len(the_map[ename]) > 0:
                        event_handle = the_map[ename][0]
                        del the_map[ename][0]
                        date = ""
                        place = ""
                        if event_handle:
                            event = self.db.get_event_from_handle(event_handle)
                            date = DateHandler.get_date(event)
                            sortdate = "%09d" % \
                                       event.get_date_object().get_sort_value()
                            place_handle = event.get_place_handle()
                            if place_handle:
                                place = self.db. \
                                get_place_from_handle(place_handle).get_title()
                        tlist.append(date)
                        tlist.append(sortdate)
                        tlist.append(place)
                        added = 1
                    else:
                        tlist.append("")
                        tlist.append("")
                        tlist.append("")
                
                if first:
                    first = 0
                    self.row_data.append(tlist)
                elif added == 0:
                    done = 1
                else:
                    self.row_data.append(tlist)
            self.progress_bar.step()

    def make_event_titles(self):
        """
        Create the list of unique event types, along with the person's
        name, birth, and death.
        This should be the column titles of the report.
        """
        the_map = {}
        for individual_id in self.my_list:
            individual = self.db.get_person_from_handle(individual_id)
            for event_ref in individual.get_event_ref_list():
                event = self.db.get_event_from_handle(event_ref.ref)
                name = str(event.get_type())
                if not name:
                    break
                if name in the_map:
                    the_map[name] = the_map[name] + 1
                else:
                    the_map[name] = 1

        unsort_list = [ (the_map[item],item) for item in the_map.keys() ]
        unsort_list.sort(by_value)
        sort_list = [ item[1] for item in unsort_list ]
## Presently there's no Birth and Death. Instead there's Birth Date and
## Birth Place, as well as Death Date and Death Place.
##         # Move birth and death to the begining of the list
##         if _("Death") in the_map:
##             sort_list.remove(_("Death"))
##             sort_list = [_("Death")] + sort_list
            
##         if _("Birth") in the_map:
##             sort_list.remove(_("Birth"))
##             sort_list = [_("Birth")] + sort_list

        return sort_list

    def on_write_table(self, obj):
        f = gtk.FileChooserDialog(_("Select filename"),
                                  action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                  buttons=(gtk.STOCK_CANCEL,
                                           gtk.RESPONSE_CANCEL,
                                           gtk.STOCK_SAVE,
                                           gtk.RESPONSE_OK))

        f.set_current_folder(os.getcwd())
        status = f.run()
        f.hide()

        if status == gtk.RESPONSE_OK:
            name = Utils.get_unicode_path(f.get_filename())
            doc = ODSTab(len(self.row_data))
            doc.creator(self.db.get_researcher().get_name())

            spreadsheet = TableReport(name, doc)

            new_titles = []
            skip_columns = []
            index = 0
            for title in self.table_titles:
                if title == 'sort':
                    skip_columns.append(index)
                else:
                    new_titles.append(title)
                index += 1
            spreadsheet.initialize(len(new_titles))

            spreadsheet.write_table_head(new_titles)

            index = 0
            for top in self.row_data:
                spreadsheet.set_row(index%2)
                index += 1
                spreadsheet.write_table_data(top,skip_columns)

            spreadsheet.finalize()
        f.destroy()

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class EventComparisonOptions(Tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name,person_id=None):
        Tool.ToolOptions.__init__(self, name,person_id)

        # Options specific for this report
        self.options_dict = {
            'filter'   : 0,
        }
        filters = ReportUtils.get_person_filters(None)
        self.options_help = {
            'filter'   : ("=num","Filter number.",
                          [ filt.get_name() for filt in filters ],
                          True ),
        }

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
pmgr = PluginManager.get_instance()
pmgr.register_tool(
    name = 'eventcmp',
    category = Tool.TOOL_ANAL,
    tool_class = EventComparison,
    options_class = EventComparisonOptions,
    modes = PluginManager.TOOL_MODE_GUI,
    translated_name = _("Compare Individual Events"),
    status = _("Stable"),
    author_name = "Donald N. Allingham",
    author_email = "don@gramps-project.org",
    description = _("Aids in the analysis of data by allowing the "
                    "development of custom filters that can be applied "
                    "to the database to find similar events")
    )
