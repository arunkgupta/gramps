# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007-2009  Douglas S. Blank <doug.blank@gmail.com>
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

# $Id$

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
import time

from gramps.gen.lib import Person, Family
from gramps.gen.db import PERSON_KEY, FAMILY_KEY, TXNDEL
from gramps.gen.plug import Gramplet
from gramps.gen.ggettext import sgettext as _
from gramps.gen.display.name import displayer as name_displayer
from gramps.gen.utils.db import family_name

#------------------------------------------------------------------------
#
# LogGramplet class
#
#------------------------------------------------------------------------
class LogGramplet(Gramplet):
    def init(self):
        self.set_tooltip(_("Click name to change active\nDouble-click name to edit"))
        self.set_text(_("Log for this Session") + "\n")
        self.gui.force_update = True # will always update, even if minimized
        self.last_log = None
        
    def timestamp(self):
        self.append_text(time.strftime("%Y-%m-%d %H:%M:%S "))

    def db_changed(self):
        self.timestamp()
        self.append_text(_("Opened data base -----------\n"))
        # List of translated strings used here (translated in self.log ).
        _('Added'), _('Deleted'), _('Edited'), _('Selected') # Dead code for l10n
        self.dbstate.db.connect('person-add', 
                                lambda handles: self.log('Person', 'Added', handles))
        self.dbstate.db.connect('person-delete', 
                                lambda handles: self.log('Person', 'Deleted', handles))
        self.dbstate.db.connect('person-update', 
                                lambda handles: self.log('Person', 'Edited', handles))
        self.dbstate.db.connect('family-add', 
                                lambda handles: self.log('Family', 'Added', handles))
        self.dbstate.db.connect('family-delete', 
                                lambda handles: self.log('Family', 'Deleted', handles))
        self.dbstate.db.connect('family-update', 
                                lambda handles: self.log('Family', 'Edited', handles))
    
    def active_changed(self, handle):
        self.log('Person', 'Selected', [handle])

    def log(self, ltype, action, handles):
        for handle in set(handles):
            if self.last_log == (ltype, action, handle):
                continue
            self.last_log = (ltype, action, handle)
            self.timestamp()
            self.append_text("%s: " % _(action) )
            if action == 'Deleted':
                transaction = self.dbstate.db.transaction
                if ltype == 'Person':
                    name = 'a person'
                    if transaction is not None:
                        for i in transaction.get_recnos(reverse=True):
                            (obj_type, trans_type, hndl, old_data, dummy) = \
                                    transaction.get_record(i)
                            if (obj_type == PERSON_KEY and trans_type == TXNDEL
                                    and hndl == handle):
                                person = Person()
                                person.unserialize(old_data)
                                name = name_displayer.display(person)
                                break
                elif ltype == 'Family':
                    name = 'a family'
                    if transaction is not None:
                        for i in transaction.get_recnos(reverse=True):
                            (obj_type, trans_type, hndl, old_data, dummy) = \
                                    transaction.get_record(i)
                            if (obj_type == FAMILY_KEY and trans_type == TXNDEL
                                    and hndl == handle):
                                family = Family()
                                family.unserialize(old_data)
                                name = family_name(family, self.dbstate.db,name)
                                break
                self.append_text(name)
            else:
                if ltype == 'Person':
                    person = self.dbstate.db.get_person_from_handle(handle)
                    name = name_displayer.display(person)
                elif ltype == 'Family':
                    family = self.dbstate.db.get_family_from_handle(handle)
                    name = family_name(family, self.dbstate.db, 'a family')
                self.link(name, ltype, handle)
            self.append_text("\n")
