#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007-2009 Stephane Charette
# Copyright (C) 2008 Brian Matherly
# Copyright (C) 2010       Jakim Friant
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

"Find people who are not related to the selected person"

#------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#------------------------------------------------------------------------
import gtk
import gobject

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
import const
from gen.ggettext import ngettext
from gui.plug import tool
from gen.plug.report import utils as ReportUtils
from gui.editors import EditPerson, EditFamily
import ManagedWindow
from gui.utils import ProgressMeter
import GrampsDisplay
from gen.ggettext import sgettext as _
from glade import Glade

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = '%s_-_Tools' % const.URL_MANUAL_PAGE
WIKI_HELP_SEC = _('manual|Not_Related...')

#------------------------------------------------------------------------
#
# NotRelated class
#
#------------------------------------------------------------------------
class NotRelated(tool.ActivePersonTool, ManagedWindow.ManagedWindow) :

    def __init__(self, dbstate, uistate, options_class, name, callback=None):
        tool.ActivePersonTool.__init__(self, dbstate, uistate, options_class,
                                       name)

        if self.fail:   # bug #2709 -- fail if we have no active person
            return

        person_handle = uistate.get_active('Person')
        person = dbstate.db.get_person_from_handle(person_handle)
        self.name = person.get_primary_name().get_regular_name()
        self.title = _('Not related to "%s"') % self.name
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self.__class__)
        self.dbstate = dbstate
        self.uistate = uistate
        self.db = dbstate.db
        
        topDialog = Glade()
        
        topDialog.connect_signals({
            "destroy_passed_object" : self.close,
            "on_help_clicked"       : self.on_help_clicked,
            "on_delete_event"       : self.close,
        })

        window = topDialog.toplevel
        title = topDialog.get_object("title")
        self.set_window(window, title, self.title)

        self.markercombo = topDialog.get_object("markercombo")
        self.markerapply = topDialog.get_object("markerapply")
        self.markercombo.set_sensitive(False)
        self.markerapply.set_sensitive(False)
        self.markerapply.connect('clicked', self.applyMarkerClicked)

    
        # start the progress indicator
        self.progress = ProgressMeter(self.title,_('Starting'))

        # setup the columns
        self.model = gtk.TreeStore(
            gobject.TYPE_STRING,    # 0==name
            gobject.TYPE_STRING,    # 1==person gid
            gobject.TYPE_STRING,    # 2==parents
            gobject.TYPE_STRING,    # 3==marker
            gobject.TYPE_STRING)    # 4==family gid (not shown to user)

        # note -- don't assign the model to the tree until it has been populated,
        # otherwise the screen updates are terribly slow while names are appended
        self.treeView = topDialog.get_object("treeview")
        col1 = gtk.TreeViewColumn(_('Name'),    gtk.CellRendererText(), text=0)
        col2 = gtk.TreeViewColumn(_('ID'),      gtk.CellRendererText(), text=1)
        col3 = gtk.TreeViewColumn(_('Parents'), gtk.CellRendererText(), text=2)
        col4 = gtk.TreeViewColumn(_('Marker'),  gtk.CellRendererText(), text=3)
        col1.set_resizable(True)
        col2.set_resizable(True)
        col3.set_resizable(True)
        col4.set_resizable(True)
        col1.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        col2.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        col3.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        col4.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        col1.set_sort_column_id(0)
#        col2.set_sort_column_id(1)
#        col3.set_sort_column_id(2)
        col4.set_sort_column_id(3)
        self.treeView.append_column(col1)
        self.treeView.append_column(col2)
        self.treeView.append_column(col3)
        self.treeView.append_column(col4)
        self.treeSelection = self.treeView.get_selection()
        self.treeSelection.set_mode(gtk.SELECTION_MULTIPLE)
        self.treeSelection.set_select_function(self.selectIsAllowed, full=True)
        self.treeSelection.connect('changed', self.rowSelectionChanged)
        self.treeView.connect('row-activated', self.rowActivated)

        # initialize a few variables we're going to need
        self.numberOfPeopleInDatabase    = self.db.get_number_of_people()
        self.numberOfRelatedPeople       = 0
        self.numberOfUnrelatedPeople     = 0

        # create the sets used to track related and unrelated people
        self.handlesOfPeopleToBeProcessed       = set()
        self.handlesOfPeopleAlreadyProcessed    = set()
        self.handlesOfPeopleNotRelated          = set()

        # build a set of all people related to the selected person
        self.handlesOfPeopleToBeProcessed.add(person.get_handle())
        self.findRelatedPeople()

        # now that we have our list of related people, find everyone
        # in the database who isn't on our list
        self.findUnrelatedPeople()

        # populate the treeview model with the names of unrelated people
        if self.numberOfUnrelatedPeople == 0:
            title.set_text(_('Everyone in the database is related to %s') % self.name)
        else:
            self.populateModel()
            self.model.set_sort_column_id(0, gtk.SORT_ASCENDING)
            self.treeView.set_model(self.model)
#            self.treeView.set_row_separator_func(self.iterIsSeparator)
            self.treeView.expand_all()

        # done searching through the database, so close the progress bar
        self.progress.close()

        self.show()


    def iterIsSeparator(self, model, iter) :
        # return True only if the row is to be treated as a separator
        if self.model.get_value(iter, 1) == '':  # does the row have a GID?
            return True
        return False


    def selectIsAllowed(self, selection, model, path, isSelected) :
        # return True/False depending on if the row being selected is a leaf node
        iter = self.model.get_iter(path)
        if self.model.get_value(iter, 1) == '': # does the row have a GID?
            return False
        return True


    def rowSelectionChanged(self, selection) :
        state = selection.count_selected_rows() > 0
        self.markercombo.set_sensitive(state)
        self.markerapply.set_sensitive(state)


    def rowActivated(self, treeView, path, column) :
        # first we need to check that the row corresponds to a person
        iter = self.model.get_iter(path)
        personGid = self.model.get_value(iter, 1)
        familyGid = self.model.get_value(iter, 4)

        if familyGid != '': # do we have a family?
            # get the parent family for this person
            family = self.db.get_family_from_gramps_id(familyGid)
            if family:
                try:
                    EditFamily(self.dbstate, self.uistate, [], family)
                except Errors.WindowActiveError:
                    pass

        elif personGid != '': # do we have a person?
            # get the person that corresponds to this GID
            person = self.db.get_person_from_gramps_id(personGid)
            if person:
                try:
                    EditPerson(self.dbstate, self.uistate, [], person)
                except Errors.WindowActiveError:
                    pass

    def on_help_clicked(self, obj):
        """Display the relevant portion of GRAMPS manual"""
        GrampsDisplay.help(WIKI_HELP_PAGE , WIKI_HELP_SEC)    


    def applyMarkerClicked(self, button) :
        progress    = None
        rows        = self.treeSelection.count_selected_rows()
        marker      = self.markercombo.get_active_text()

        # if more than 1 person is selected, use a progress indicator
        if rows > 1:
            progress = ProgressMeter(self.title,_('Starting'))
            #TRANS: no singular form needed, as rows is always > 1
            progress.set_pass(ngettext("Setting marker for %d person", 'Setting marker for %d people', \
                              rows) % rows, rows)

        # start the db transaction
        transaction = self.db.transaction_begin()

        # iterate through all of the selected rows
        (model, paths) = self.treeSelection.get_selected_rows()
        for path in paths:
            if progress:
                progress.step()

            # for the current row, get the GID and the person from the database
            iter        = self.model.get_iter(path)
            personGid   = self.model.get_value(iter, 1)
            person      = self.db.get_person_from_gramps_id(personGid)

            # change the marker
            person.set_marker(marker)
            self.model.set_value(iter, 3, marker)

            # save this change
            self.db.commit_person(person, transaction)

        # commit the entire transaction
        self.db.transaction_commit(transaction, "mark not related")

        if progress:
            progress.close()


    def findRelatedPeople(self) :

        #TRANS: No singular form is needed.
        self.progress.set_pass(ngettext("Finding relationships between %d person", "Finding relationships between %d people",\
                               self.numberOfPeopleInDatabase) \
                               % self.numberOfPeopleInDatabase, \
                               self.numberOfPeopleInDatabase)

        # as long as we have people we haven't processed yet, keep looping
        while len(self.handlesOfPeopleToBeProcessed) > 0:
            handle = self.handlesOfPeopleToBeProcessed.pop()

### DEBUG DEBUG DEBUG
#            if len(self.handlesOfPeopleAlreadyProcessed) > 50:
#                break
###

            # see if we've already processed this person
            if handle in self.handlesOfPeopleAlreadyProcessed:
                continue

            person = self.db.get_person_from_handle(handle)

            # if we get here, then we're dealing with someone new
            self.progress.step()

            # remember that we've now seen this person
            self.handlesOfPeopleAlreadyProcessed.add(handle)

            # we have 3 things to do:  find (1) spouses, (2) parents, and (3) children

            # step 1 -- spouses
            for familyHandle in person.get_family_handle_list():
                family = self.db.get_family_from_handle(familyHandle)
                spouseHandle = ReportUtils.find_spouse(person, family)
                if spouseHandle and \
                  spouseHandle not in self.handlesOfPeopleAlreadyProcessed:
                    self.handlesOfPeopleToBeProcessed.add(spouseHandle)

            # step 2 -- parents
            for familyHandle in person.get_parent_family_handle_list():
                family = self.db.get_family_from_handle(familyHandle)
                fatherHandle = family.get_father_handle()
                motherHandle = family.get_mother_handle()
                if fatherHandle and \
                  fatherHandle not in self.handlesOfPeopleAlreadyProcessed:
                    self.handlesOfPeopleToBeProcessed.add(fatherHandle)
                if motherHandle and \
                  motherHandle not in self.handlesOfPeopleAlreadyProcessed:
                    self.handlesOfPeopleToBeProcessed.add(motherHandle)

            # step 3 -- children
            for familyHandle in person.get_family_handle_list():
                family = self.db.get_family_from_handle(familyHandle)
                for childRef in family.get_child_ref_list():
                    childHandle = childRef.ref
                    if childHandle and \
                      childHandle not in self.handlesOfPeopleAlreadyProcessed:
                        self.handlesOfPeopleToBeProcessed.add(childHandle)


    def findUnrelatedPeople(self) :

        # update our numbers
        self.numberOfRelatedPeople = len(self.handlesOfPeopleAlreadyProcessed)
        self.numberOfUnrelatedPeople = self.numberOfPeopleInDatabase - \
            self.numberOfRelatedPeople

        if self.numberOfUnrelatedPeople > 0:
            # we have at least 1 "unrelated" person to find

            self.progress.set_pass( \
                    ngettext("Looking for %d person", "Looking for %d people",\
                    self.numberOfUnrelatedPeople) % self.numberOfUnrelatedPeople,\
                    self.numberOfPeopleInDatabase) 

            # loop through everyone in the database
            for handle in self.db.iter_person_handles():

                self.progress.step()

                # if this person is related, then skip to the next one
                if handle in self.handlesOfPeopleAlreadyProcessed:
                    continue

### DEBUG DEBUG DEBUG
#                if len(self.handlesOfPeopleNotRelated) > 10:
#                    break
###

                # if we get here, we have someone who is "not related"
                self.handlesOfPeopleNotRelated.add(handle)


    def populateModel(self) :

        self.progress.set_pass( \
                ngettext("Looking up the name of %d person", "Looking up the names of %d people", \
                self.numberOfUnrelatedPeople) % self.numberOfUnrelatedPeople,\
                self.numberOfUnrelatedPeople)

        # loop through the entire list of unrelated people
        for handle in self.handlesOfPeopleNotRelated:
            self.progress.step()
            person      = self.db.get_person_from_handle(handle)
            primaryname = person.get_primary_name()
            surname     = primaryname.get_surname()
            name        = primaryname.get_name()
            gid         = person.get_gramps_id()
            marker      = person.get_marker()

            # find the names of the parents
            familygid   = ''
            parentNames = ''
            parentFamilyHandle = person.get_main_parents_family_handle()
            if parentFamilyHandle:
                parentFamily = self.db.get_family_from_handle(parentFamilyHandle)
                familygid    = parentFamily.get_gramps_id()
                fatherName   = None
                motherName   = None
                fatherHandle = parentFamily.get_father_handle()
                if fatherHandle:
                    father      = self.db.get_person_from_handle(fatherHandle)
                    fatherName  = father.get_primary_name().get_first_name()
                motherHandle = parentFamily.get_mother_handle()
                if motherHandle:
                    mother      = self.db.get_person_from_handle(motherHandle)
                    motherName  = mother.get_primary_name().get_first_name()

                # now that we have the names, come up with a label we can use
                if fatherName:
                    parentNames += fatherName
                if fatherName and motherName:
                    parentNames += ' & '
                if motherName:
                    parentNames += motherName

            # get the surname node (or create it if it doesn't exist)

            # start with the root
            iter = self.model.get_iter_root()
            # look for a node with a matching surname
            while iter:
                if self.model.get_value(iter, 0) == surname:
                    break;
                iter = self.model.iter_next(iter)

            # if we don't have a valid iter, then create a new top-level node
            if not iter:
                iter = self.model.append(None, [surname, '', '', '', ''])

            # finally, we now get to add this person to the model
            self.model.append(iter, [name, gid, parentNames, marker, familygid])


    def build_menu_names(self, obj):
        return (self.title, None)
    
#------------------------------------------------------------------------
#
# NotRelatedOptions
#
#------------------------------------------------------------------------
class NotRelatedOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """
    def __init__(self, name, person_id=None):
        """ Initialize the options class """
        tool.ToolOptions.__init__(self, name, person_id)
