#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2005  Donald N. Allingham
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
# Standard python modules
#
#-------------------------------------------------------------------------

#-------------------------------------------------------------------------
#
# GNOME
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.ggettext import sgettext as _
import const
import GrampsDisplay
import ManagedWindow
from glade import Glade

#-------------------------------------------------------------------------
#
# GRAMPS constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = '%s_-_Entering_and_Editing_Data:_Detailed_-_part_3' % const.URL_MANUAL_PAGE
WIKI_HELP_SEC = _('manual|Merge_Sources')
_GLADE_FILE = 'mergedata.glade'

#-------------------------------------------------------------------------
#
# Merge Sources
#
#-------------------------------------------------------------------------
class MergeSources(ManagedWindow.ManagedWindow):
    """
    Merges to sources into a single source. Displays a dialog box that
    allows the sources to be combined into one.
    """
    def __init__(self, dbstate, uistate, new_handle, old_handle):
        
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self.__class__)

        self.db = dbstate.db
        
        self.new_handle = new_handle
        self.old_handle = old_handle
        self.s1 = self.db.get_source_from_handle(self.new_handle)
        self.s2 = self.db.get_source_from_handle(self.old_handle)

        self.glade = Glade(_GLADE_FILE, toplevel='mergesource')

        self.set_window(self.glade.toplevel,
                        self.glade.get_object('source_title'),
                        _("Merge Sources"))

        self.title1 = self.glade.get_object("title1")
        self.title2 = self.glade.get_object("title2")
        self.title1.set_text(self.s1.get_title())
        self.title2.set_text(self.s2.get_title())

        self.author1 = self.glade.get_object("author1")
        self.author2 = self.glade.get_object("author2")
        self.author1.set_text(self.s1.get_author())
        self.author2.set_text(self.s2.get_author())

        self.abbrev1 = self.glade.get_object("abbrev1")
        self.abbrev2 = self.glade.get_object("abbrev2")
        self.abbrev1.set_text(self.s1.get_abbreviation())
        self.abbrev2.set_text(self.s2.get_abbreviation())

        self.pub1 = self.glade.get_object("pub1")
        self.pub2 = self.glade.get_object("pub2")
        self.pub1.set_text(self.s1.get_publication_info())
        self.pub2.set_text(self.s2.get_publication_info())

        self.gramps1 = self.glade.get_object("gramps1")
        self.gramps2 = self.glade.get_object("gramps2")
        self.gramps1.set_text(self.s1.get_gramps_id())
        self.gramps2.set_text(self.s2.get_gramps_id())
        
        self.glade.get_object('source_ok').connect('clicked',self.merge)
        self.glade.get_object('source_cancel').connect('clicked',self.close_window)
        self.glade.get_object('source_help').connect('clicked',self.help)
        self.show()

    def close_window(self, obj):
        self.close()

    def help(self, obj):
        """Display the relevant portion of GRAMPS manual"""
        GrampsDisplay.help(webpage = WIKI_HELP_PAGE, section = WIKI_HELP_SEC)

    def merge(self, obj):
        """
        Performs the merge of the sources when the merge button is clicked.
        """

        use_title1 = self.glade.get_object("title_btn1").get_active()
        use_author1 = self.glade.get_object("author_btn1").get_active()
        use_abbrev1 = self.glade.get_object("abbrev_btn1").get_active()
        use_pub1 = self.glade.get_object("pub_btn1").get_active()
        use_gramps1 = self.glade.get_object("gramps_btn1").get_active()
        
        if not use_title1:
            self.s1.set_title(self.s2.get_title())

        if not use_author1:
            self.s1.set_author(self.s2.get_author())

        if not use_abbrev1:
            self.s1.set_abbreviation(self.s2.get_abbreviation())

        if not use_pub1:
            self.s1.set_publication_info(self.s2.get_publication_info())

        if not use_gramps1:
            self.s1.set_gramps_id(self.s2.get_gramps_id())

        # Copy photos from src2 to src1
        map(self.s1.add_media_reference, self.s2.get_media_list())

        # Add notes from S2 to S1
        self.s1.set_note_list(self.s1.get_note_list() + self.s2.get_note_list())

        src2_map = self.s2.get_data_map()
        src1_map = self.s1.get_data_map()
        for key in src2_map:
            if key not in src1_map:
                src1_map[key] = src2_map[key]

        # replace references in other objetcs
        trans = self.db.transaction_begin()

        self.db.remove_source(self.old_handle,trans)
        self.db.commit_source(self.s1,trans)

        # replace handles

        # people
        for person in self.db.iter_people():
            if person.has_source_reference(self.old_handle):
                person.replace_source_references(self.old_handle,
                                                        self.new_handle)
                self.db.commit_person(person,trans)

        # family
        for family in self.db.iter_families():
            if family.has_source_reference(self.old_handle):
                family.replace_source_references(self.old_handle,
                                                        self.new_handle)
                self.db.commit_family(family,trans)

        # events
        for event in self.db.iter_events():
            if event.has_source_reference(self.old_handle):
                event.replace_source_references(self.old_handle,
                                                        self.new_handle)
                self.db.commit_event(event,trans)

        # sources
        for source in self.db.iter_sources():
            if source.has_source_reference(self.old_handle):
                source.replace_source_references(self.old_handle,
                                                        self.new_handle)
                self.db.commit_source(source,trans)

        # places
        for place in self.db.iter_places():
            if place.has_source_reference(self.old_handle):
                place.replace_source_references(self.old_handle,
                                                        self.new_handle)
                self.db.commit_place(place,trans)

        # media
        for obj in self.db.iter_media_objects():
            if obj.has_source_reference(self.old_handle):
                obj.replace_source_references(self.old_handle,
                                                        self.new_handle)
                self.db.commit_media_object(obj,trans)
        
        self.db.transaction_commit(trans,_("Merge Sources"))
        self.close()
