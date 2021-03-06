# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011 Nick Hall
# Copyright (C) 2011       Tim G L Lyons
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
#

from gramps.gui.listmodel import ListModel, NOSORT
from gramps.gen.utils.db import navigation_label
from gramps.gen.plug import Gramplet
from gramps.gen.ggettext import gettext as _
from gi.repository import Gtk

class Backlinks(Gramplet):
    """
    Displays the back references for an object.
    """
    def init(self):
        self.gui.WIDGET = self.build_gui()
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(self.gui.WIDGET)
        self.gui.WIDGET.show()

    def build_gui(self):
        """
        Build the GUI interface.
        """
        top = Gtk.TreeView()
        titles = [(_('Type'), 1, 100),
                  (_('Name'), 2, 100)]
        self.model = ListModel(top, titles)
        return top
        
    def display_backlinks(self, active_handle):
        """
        Display the back references for an object.
        """
        for classname, handle in \
                        self.dbstate.db.find_backlink_handles(active_handle):
            name = navigation_label(self.dbstate.db, classname, handle)[0]
            self.model.add((_(classname), name))
        self.set_has_data(self.model.count > 0)

    def get_has_data(self, active_handle):
        """
        Return True if the gramplet has data, else return False.
        """
        if active_handle is None:
            return False
        for handle in self.dbstate.db.find_backlink_handles(active_handle):
            return True
        return False
        
class PersonBacklinks(Backlinks):
    """
    Displays the back references for a person.
    """
    def db_changed(self):
        self.dbstate.db.connect('person-update', self.update)

    def active_changed(self, handle):
        self.update()

    def update_has_data(self):
        active_handle = self.get_active('Person')
        self.set_has_data(self.get_has_data(active_handle))
    
    def main(self):
        active_handle = self.get_active('Person')
        self.model.clear()
        if active_handle:
            self.display_backlinks(active_handle)
        else:
            self.set_has_data(False)

class EventBacklinks(Backlinks):
    """
    Displays the back references for an event.
    """
    def db_changed(self):
        self.dbstate.db.connect('event-update', self.update)
        self.connect_signal('Event', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Event')
        self.set_has_data(self.get_has_data(active_handle))
    
    def main(self):
        active_handle = self.get_active('Event')
        self.model.clear()
        if active_handle:
            self.display_backlinks(active_handle)
        else:
            self.set_has_data(False)

class FamilyBacklinks(Backlinks):
    """
    Displays the back references for a family.
    """
    def db_changed(self):
        self.dbstate.db.connect('family-update', self.update)
        self.connect_signal('Family', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Family')
        self.set_has_data(self.get_has_data(active_handle))
    
    def main(self):
        active_handle = self.get_active('Family')
        self.model.clear()
        if active_handle:
            self.display_backlinks(active_handle)
        else:
            self.set_has_data(False)

class PlaceBacklinks(Backlinks):
    """
    Displays the back references for a place.
    """
    def db_changed(self):
        self.dbstate.db.connect('place-update', self.update)
        self.connect_signal('Place', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Place')
        self.set_has_data(self.get_has_data(active_handle))
    
    def main(self):
        active_handle = self.get_active('Place')
        self.model.clear()
        if active_handle:
            self.display_backlinks(active_handle)
        else:
            self.set_has_data(False)

class SourceBacklinks(Backlinks):
    """
    Displays the back references for a source,.
    """
    def db_changed(self):
        self.dbstate.db.connect('source-update', self.update)
        self.connect_signal('Source', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Source')
        self.set_has_data(self.get_has_data(active_handle))
    
    def main(self):
        active_handle = self.get_active('Source')
        self.model.clear()
        if active_handle:
            self.display_backlinks(active_handle)
        else:
            self.set_has_data(False)

class CitationBacklinks(Backlinks):
    """
    Displays the back references for a Citation,.
    """
    def db_changed(self):
        self.dbstate.db.connect('citation-update', self.update)
        self.connect_signal('Citation', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Citation')
        self.set_has_data(self.get_has_data(active_handle))
    
    def main(self):
        active_handle = self.get_active('Citation')
        self.model.clear()
        if active_handle:
            self.display_backlinks(active_handle)
        else:
            self.set_has_data(False)

class RepositoryBacklinks(Backlinks):
    """
    Displays the back references for a repository.
    """
    def db_changed(self):
        self.dbstate.db.connect('repository-update', self.update)
        self.connect_signal('Repository', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Repository')
        self.set_has_data(self.get_has_data(active_handle))
    
    def main(self):
        active_handle = self.get_active('Repository')
        self.model.clear()
        if active_handle:
            self.display_backlinks(active_handle)
        else:
            self.set_has_data(False)

class MediaBacklinks(Backlinks):
    """
    Displays the back references for a media object.
    """
    def db_changed(self):
        self.dbstate.db.connect('media-update', self.update)
        self.connect_signal('Media', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Media')
        self.set_has_data(self.get_has_data(active_handle))
    
    def main(self):
        active_handle = self.get_active('Media')
        self.model.clear()
        if active_handle:
            self.display_backlinks(active_handle)
        else:
            self.set_has_data(False)

class NoteBacklinks(Backlinks):
    """
    Displays the back references for a note.
    """
    def db_changed(self):
        self.dbstate.db.connect('note-update', self.update)
        self.connect_signal('Note', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Note')
        self.set_has_data(self.get_has_data(active_handle))
    
    def main(self):
        active_handle = self.get_active('Note')
        self.model.clear()
        if active_handle:
            self.display_backlinks(active_handle)
        else:
            self.set_has_data(False)

