#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
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

# $Id: _HasNoteRegexp.py 9912 2008-01-22 09:17:46Z acraphae $

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
import re
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from Filters.Rules import Rule

#-------------------------------------------------------------------------
# "Repos having notes that contain a substring"
#-------------------------------------------------------------------------
class MatchesRegexpOf(Rule):

    labels      = [ _('Regular expression:')]
    name        = _('Notes containing <regular expression>')
    description = _("Matches notes who contain text "
                    "matching a regular expression")
    category    = _('General filters')

    def __init__(self, list):
        Rule.__init__(self, list)
        
        try:
            self.match = re.compile(list[0], re.I|re.U|re.L)
        except:
            self.match = re.compile('')
            
    def apply(self, db, note):
        """ Apply the filter """
        text = unicode(note.get())
        if self.match.match(text) is not None:
            return True
        return False
