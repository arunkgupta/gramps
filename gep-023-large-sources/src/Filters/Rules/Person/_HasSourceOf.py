#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
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
from gen.ggettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from Filters.Rules._Rule import Rule

#-------------------------------------------------------------------------
#
# HasSourceOf
#
#-------------------------------------------------------------------------
class HasSourceOf(Rule):
    """Rule that checks people that have a particular source."""

    labels      = [ _('Source ID:') ]
    name        = _('People with the <source>')
    category    = _('Citation/source filters')
    description = _('Matches people who have a particular source')
    
    def prepare(self,db):
        if self.list[0] == '':
            self.source_handle = None
            self.nosource = True
            return

        self.nosource = False
        try:
            self.source_handle = db.get_source_from_gramps_id(
                    self.list[0]).get_handle()
        except:
            self.source_handle = None

    def apply(self, db, person):
        if not self.source_handle:
            if self.nosource:
                # check whether the citation list is empty as a proxy for
                # there being no sources
                return len(person.get_all_citation_lists()) == 0
            else:
                return False
        else:
            for citation_handle in person.get_all_citation_lists():
                citation = db.get_citation_from_handle(citation_handle)
                if citation.get_reference_handle() == self.source_handle:
                    return True
            return False
