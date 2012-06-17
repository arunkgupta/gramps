#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
# Copyright (C) 2010  Benny Malengier
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
from gen.filters.rules import MatchesFilterBase

#-------------------------------------------------------------------------
#
# MatchesFilter
#
#-------------------------------------------------------------------------
class MatchesSourceFilter(MatchesFilterBase):
    """
    Rule that checks against another filter.
    """

    labels      = [_('Source filter name:')]
    name        = _('Citations with source matching the <source filter>')
    description = _("Matches citations with sources that match the "
                    "specified source filter name")
    category    = _('General filters')

    # we want to have this filter show source filters
    namespace   = 'Source'

    def prepare(self, db):
        MatchesFilterBase.prepare(self, db)
        self.MRF_filt = self.find_filter()
            
    def apply(self, db, object):
        if self.MRF_filt is None :
            return False
        
        source_handle = object.source_handle
        if self.MRF_filt.check(db, source_handle):
            return True
        return False
