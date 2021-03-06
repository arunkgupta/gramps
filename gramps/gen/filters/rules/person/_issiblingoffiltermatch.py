#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2007  Donald N. Allingham
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
# Standard Python modules
#
#-------------------------------------------------------------------------
from ....ggettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from .. import Rule
from _matchesfilter import MatchesFilter

#-------------------------------------------------------------------------
#
# IsSiblingOfFilterMatch
#
#-------------------------------------------------------------------------
class IsSiblingOfFilterMatch(Rule):
    """Rule that checks for siblings of someone matched by a filter"""

    labels      = [ _('Filter name:') ]
    name        = _('Siblings of <filter> match')
    category    = _('Family filters')
    description = _("Matches siblings of anybody matched by a filter")

    def prepare(self,db):
        self.db = db
        self.map = set()
        filt = MatchesFilter(self.list)
        filt.requestprepare(db)
        for person in db.iter_people():
            if filt.apply (db, person):
                self.init_list (person)
        filt.requestreset()

    def reset(self):
        self.map.clear()

    def apply(self,db,person):
        return person.handle in self.map

    def init_list(self,person):
        if not person:
            return
        fam_id = person.get_main_parents_family_handle()
        fam = self.db.get_family_from_handle(fam_id)
        if fam:
            self.map.update(child_ref.ref
                for child_ref in fam.get_child_ref_list()
                    if child_ref and child_ref.ref != person.handle)
