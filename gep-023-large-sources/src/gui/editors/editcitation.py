#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011       Tim G L Lyons, Nick Hall
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
# Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
import logging
LOG = logging.getLogger(".citation")

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
from gen.db import DbTxn
from editprimary import EditPrimary

from displaytabs import (NoteTab, GalleryTab, DataEmbedList,
                         SourceBackRefList, RepoEmbedList)
from gui.widgets import (MonitoredEntry, PrivacyButton, MonitoredMenu,
                        MonitoredDate)
from QuestionDialog import ErrorDialog
from editreference import RefTab
from glade import Glade

#-------------------------------------------------------------------------
#
# EditCitationclass
#
#-------------------------------------------------------------------------

class EditCitation(EditPrimary):

    def __init__(self, dbstate, uistate, track, obj, source, callback=None,
                 callertitle = None):
        """
        Create an EditCitation window. Associate a citation with the window.
        
        This class is called both to edit the Citation Primary object
        and to edit references from other objects to citation.
        It is called from gui.editors.__init__ for editing the primary object
        and is called from CitationEmbedList for editing references
        
        @param callertitle: Text passed by calling object to add to title 
        @type callertitle: str
        """
        self.source = source
        self.callertitle = callertitle
        EditPrimary.__init__(self, dbstate, uistate, track, obj, 
                             dbstate.db.get_citation_from_handle, 
                             dbstate.db.get_citation_from_gramps_id, callback)

    def empty_object(self):
        """
        Return an empty Citation object for comparison for changes.
        
        It is used by the base class L{EditPrimary}.
        """
        return gen.lib.Citation()

    def get_menu_title(self):
        title = self.obj.get_page()
        if title:
            if self.callertitle:
                title = _('Citation') + \
                        (': %(id)s - %(context)s' % {
                         'id'      : title,
                         'context' : self.callertitle
                         })
            else:
                title = _('Citation') + ": " + title
        else:
            if self.callertitle:
                title = _('New Citation') + \
                        (': %(id)s - %(context)s' % {
                         'id'      : title,
                         'context' : self.callertitle
                         })
            else:     
                title = _('New Citation')
        return title

    # The functions define_warn_box, enable_warn_box and define_expander
    # are normally inherited from editreference,
    # but have to be defined here because this class inherits from 
    # EditPrimary instead
    def define_warn_box(self,box):
        self.warn_box = box

    def enable_warnbox(self):
        self.warn_box.show()

    def define_warn_box2(self,box):
        self.warn_box2 = box

    def enable_warnbox2(self):
        self.warn_box2.show()

    def define_expander(self,expander):
        expander.set_expanded(True)

    def _local_init(self):
        """Local initialization function.
        
        Perform basic initialization, including setting up widgets
        and the glade interface. It is called by the base class L{EditPrimary},
        and overridden here.
        
        """
        self.width_key = 'interface.citation-width'
        self.height_key = 'interface.citation-height'
        assert(self.obj)
        
        self.glade = Glade()
        self.set_window(self.glade.toplevel, None, 
                        self.get_menu_title())
        
        self.define_warn_box(self.glade.get_object("warn_box"))
        self.define_warn_box2(self.glade.get_object("warn_box2"))
        self.define_expander(self.glade.get_object("src_expander"))

        tblref =  self.glade.get_object('table67')
        notebook = self.glade.get_object('notebook_ref')
        #recreate start page as GrampsTab
        notebook.remove_page(0)
        self.reftab = RefTab(self.dbstate, self.uistate, self.track, 
                              _('General'), tblref)
        tblref =  self.glade.get_object('table68')
        notebook = self.glade.get_object('notebook_src')
        #recreate start page as GrampsTab
        notebook.remove_page(0)
        self.primtab = RefTab(self.dbstate, self.uistate, self.track, 
                              _('General'), tblref)


    def _connect_signals(self):
        """Connects any signals that need to be connected.
        
        Called by the init routine of the base class L{EditPrimary}.
        
        """
        self.define_ok_button(self.glade.get_object('ok'),self.save)
        self.define_cancel_button(self.glade.get_object('cancel'))
        self.define_help_button(self.glade.get_object('help'))

    def _connect_db_signals(self):
        """
        Connect any signals that need to be connected. 
        Called by the init routine of the base class (_EditPrimary).
        """
        # FIXME: Should this be modified so that the 'close' routines
        # are executed not only for the 'Citation', bit also for the 'Source'
        self._add_db_signal('citation-rebuild', self._do_close)
        self._add_db_signal('citation-delete', self.check_for_close)

    def _setup_fields(self):
        """Get control widgets and attach them to Citation's attributes."""
        
        # Populate the Citation section
        
        self.date = MonitoredDate(
            self.glade.get_object("date_entry"),
            self.glade.get_object("date_stat"), 
            self.obj.get_date_object(),
            self.uistate,
            self.track,
            self.db.readonly)

        self.gid = MonitoredEntry(
            self.glade.get_object('gid2'), self.obj.set_gramps_id,
            self.obj.get_gramps_id,self.db.readonly)

        self.volume = MonitoredEntry(
            self.glade.get_object("volume"), self.obj.set_page,
            self.obj.get_page, self.db.readonly)
        
        self.type_mon = MonitoredMenu(
            self.glade.get_object('confidence'),
            self.obj.set_confidence_level,
            self.obj.get_confidence_level, [
            (_('Very Low'), gen.lib.Citation.CONF_VERY_LOW),
            (_('Low'), gen.lib.Citation.CONF_LOW),
            (_('Normal'), gen.lib.Citation.CONF_NORMAL),
            (_('High'), gen.lib.Citation.CONF_HIGH),
            (_('Very High'), gen.lib.Citation.CONF_VERY_HIGH)],
            self.db.readonly)

        self.ref_privacy = PrivacyButton(
            self.glade.get_object('privacy'), self.obj, self.db.readonly)
        
        # Populate the Source section
        
        self.title = MonitoredEntry(
            self.glade.get_object('title'), 
            self.source.set_title,
            self.source.get_title,
            self.db.readonly)
        
        self.author = MonitoredEntry(
            self.glade.get_object('author'), self.source.set_author,
            self.source.get_author,self.db.readonly)
        
        self.gid = MonitoredEntry(
            self.glade.get_object('gid'), self.source.set_gramps_id,
            self.source.get_gramps_id,self.db.readonly)

        self.source_privacy = PrivacyButton(
            self.glade.get_object("private"),
            self.obj, self.db.readonly)

        self.abbrev = MonitoredEntry(
            self.glade.get_object('abbrev'), self.source.set_abbreviation,
            self.source.get_abbreviation,self.db.readonly)

        self.pubinfo = MonitoredEntry(
            self.glade.get_object('pub_info'), self.source.set_publication_info,
            self.source.get_publication_info,self.db.readonly)

    def _create_tabbed_pages(self):
        """
        Create the notebook tabs and inserts them into the main
        window.
        """
        # create notebook tabs for Citation
        
        notebook_ref = self.glade.get_object('notebook_ref')
        self._add_tab(notebook_ref, self.reftab)

        self.comment_tab = NoteTab(self.dbstate, self.uistate, self.track,
                    self.obj.get_note_list(), self.get_menu_title(),
                    notetype=gen.lib.NoteType.SOURCEREF)
        self._add_tab(notebook_ref, self.comment_tab)
        self.track_ref_for_deletion("comment_tab")

        self.gallery_tab = GalleryTab(self.dbstate, self.uistate, self.track,
                       self.obj.get_media_list())
        self._add_tab(notebook_ref, self.gallery_tab)
        self.track_ref_for_deletion("gallery_tab")
            
        self.data_tab = DataEmbedList(self.dbstate, self.uistate, self.track,
                          self.obj)
        self._add_tab(notebook_ref, self.data_tab)
        self.track_ref_for_deletion("data_tab")
            
        self.citationref_list = SourceBackRefList(self.dbstate, self.uistate, 
                              self.track,
                              self.db.find_backlink_handles(self.obj.handle),
                              self.enable_warnbox2)
        self._add_tab(notebook_ref, self.citationref_list)
        self.track_ref_for_deletion("citationref_list")

        # Create notebook tabs for Source
        
        notebook_src = self.glade.get_object('notebook_src')
        
        self._add_tab(notebook_src, self.primtab)
        
        self.note_tab = NoteTab(self.dbstate, self.uistate, self.track,
                                self.source.get_note_list(), 
                                self.get_menu_title(),
                                notetype=gen.lib.NoteType.SOURCE)
        self._add_tab(notebook_src, self.note_tab)
        self.track_ref_for_deletion("note_tab")
            
        self.gallery_tab = GalleryTab(self.dbstate, self.uistate, self.track,
                       self.source.get_media_list())
        self._add_tab(notebook_src, self.gallery_tab)
        self.track_ref_for_deletion("gallery_tab")
            
        self.data_tab = DataEmbedList(self.dbstate, self.uistate, self.track,
                          self.source)
        self._add_tab(notebook_src, self.data_tab)
        self.track_ref_for_deletion("data_tab")
            
        self.repo_tab = RepoEmbedList(self.dbstate, self.uistate, self.track,
                          self.source.get_reporef_list())
        self._add_tab(notebook_src, self.repo_tab)
        self.track_ref_for_deletion("repo_tab")
            
        # FIXME:
        # SourceBackrefList inherits from BackrefList inherits from EmbeddedList
        # inherits from ButtonTab
        # _create_buttons is defined in ButtonTab, and overridden in BackRefList.
        # But needs to be overriden here so that there is no edit button for
        # References to Source, because they will all be citations,
        # and the Citations will be displayed in the top part of the
        # edit dialogue.
        self.srcref_list = SourceBackRefList(self.dbstate,self.uistate, 
                              self.track,
                              self.db.find_backlink_handles(self.source.handle),
                              self.enable_warnbox)
        self._add_tab(notebook_src, self.srcref_list)
        self.track_ref_for_deletion("srcref_list")

        self._setup_notebook_tabs(notebook_src)
        self._setup_notebook_tabs(notebook_ref)

    def build_menu_names(self, source):
        """
        Provide the information needed by the base class to define the
        window management menu entries.
        """
        return (_('Edit Citation'), self.get_menu_title())        

    def save(self, *obj):
        """Save the data."""
        self.ok_button.set_sensitive(False)
        if self.object_is_empty():
            ErrorDialog(_("Cannot save citation"),
                        _("No data exists for this citation. Please "
                          "enter data or cancel the edit."))
            self.ok_button.set_sensitive(True)
            return
        
        (uses_dupe_id, id) = self._uses_duplicate_id()
        if uses_dupe_id:
            prim_object = self.get_from_gramps_id(id)
            name = prim_object.get_page()
            msg1 = _("Cannot save citation. ID already exists.")
            msg2 = _("You have attempted to use the existing Gramps ID with "
                         "value %(id)s. This value is already used by '" 
                         "%(prim_object)s'. Please enter a different ID or leave "
                         "blank to get the next available ID value.") % {
                         'id' : id, 'prim_object' : name }
            ErrorDialog(msg1, msg2)
            self.ok_button.set_sensitive(True)
            return

        with DbTxn('', self.db) as trans:
            # First commit the Source Primary object
            if not self.source.get_handle():
                self.db.add_source(self.source, trans)
                msg = _("Add Source (%s)") % self.source.get_title()
            else:
                if not self.source.get_gramps_id():
                    self.source.set_gramps_id(self.db.find_next_source_gramps_id())
                self.db.commit_source(self.source, trans)
                msg = _("Edit Source (%s)") % self.source.get_title()

            self.obj.ref = self.source.handle
            
            # Now commit the Citation Primary object
            if not self.obj.get_handle():
                self.db.add_citation(self.obj, trans)
                msg += _(" " + "Add Citation (%s)") % self.obj.get_page()
            else:
                if not self.obj.get_gramps_id():
                    self.obj.set_gramps_id(self.db.find_next_citation_gramps_id())
                self.db.commit_citation(self.obj, trans)
                msg += _("\n" + "Edit Citation (%s)") % self.obj.get_page()
            trans.set_description(msg)
            LOG.debug(msg)
                        
        if self.callback:
            self.callback(self.obj.get_handle())
        self.close()

class DeleteCitationQuery(object):
    def __init__(self, dbstate, uistate, citation, the_lists):
        self.citation = citation
        self.db = dbstate.db
        self.uistate = uistate
        self.the_lists = the_lists

    def query_response(self):
        with DbTxn(_("Delete Citation (%s)") % self.citation.get_page(),
                   self.db) as trans:
            self.db.disable_signals()
        
            (person_list, family_list, event_list, place_list, source_list, 
             media_list, repo_list) = self.the_lists

            ctn_handle_list = [self.citation.get_handle()]

            for handle in person_list:
                person = self.db.get_person_from_handle(handle)
                person.remove_citation_references(ctn_handle_list)
                self.db.commit_person(person, trans)

            for handle in family_list:
                family = self.db.get_family_from_handle(handle)
                family.remove_citation_references(ctn_handle_list)
                self.db.commit_family(family, trans)

            for handle in event_list:
                event = self.db.get_event_from_handle(handle)
                event.remove_citation_references(ctn_handle_list)
                self.db.commit_event(event, trans)

            for handle in place_list:
                place = self.db.get_place_from_handle(handle)
                place.remove_citation_references(ctn_handle_list)
                self.db.commit_place(place, trans)

            for handle in source_list:
                source = self.db.get_source_from_handle(handle)
                source.remove_citation_references(ctn_handle_list)
                self.db.commit_source(source, trans)

            for handle in media_list:
                media = self.db.get_object_from_handle(handle)
                media.remove_citation_references(ctn_handle_list)
                self.db.commit_media_object(media, trans)

            for handle in repo_list:
                repo = self.db.get_repository_from_handle(handle)
                repo.remove_citation_references(ctn_handle_list)
                self.db.commit_repository(repo, trans)

            self.db.enable_signals()
            self.db.remove_citation(self.citation.get_handle(), trans)
