#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2005-2006  Donald N. Allingham
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

"""
Provide an interface to the gtkspell interface. This requires
python-gnome-extras package. If the gtkspell package is not
present, we default to no spell checking.

"""

#-------------------------------------------------------------------------
#
# Python classes
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
import locale
import constfunc
#-------------------------------------------------------------------------
#
# Set up logging
#
#-------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".Spell")

#-------------------------------------------------------------------------
#
# GTK libraries
#
#-------------------------------------------------------------------------
import gtk

# In Windows (XP and 7) enchant must be imported before gtkspell
# otherwise import of gtkspell fails.
if constfunc.win():
    try:
        import enchant
    except ImportError:
        LOG.warn(_("pyenchant must be installed"))
try:
    import gtkspell
    HAVE_GTKSPELL = True
except ImportError:
    HAVE_GTKSPELL = False

if not HAVE_GTKSPELL:
    LOG.warn(_("Spelling checker is not installed"))

#-------------------------------------------------------------------------
#
# GRAMPS classes
#
#-------------------------------------------------------------------------
import config

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------

class Spell(object):
    """Attach a gtkspell instance to the passed TextView instance.
    """
    _spellcheck_options = {False: _('Off'), True: _('On') }
    
    def __init__(self, textview):
        self.textview = textview
        
        if HAVE_GTKSPELL and config.get('behavior.spellcheck'):
            self.spellcheck = True
        else:
            self.spellcheck = False

        self._previous_spellcheck = False
        self.__real_set_active_spellcheck(self.spellcheck)

    # Private
    
    def __real_set_active_spellcheck(self, next_spellcheck):
        """Set active spellcheck by its code."""
        if self._previous_spellcheck == next_spellcheck:
            return
        elif self._previous_spellcheck == False and next_spellcheck == True:
            try:
                gtkspell_spell = gtkspell.Spell(self.textview)
                self._previous_spellcheck = next_spellcheck
            except:
                import traceback
                print traceback.print_exc()
                # attaching the spellchecker will fail if
                # the language does not exist
                # and presumably if there is no dictionary
                pass
        elif self._previous_spellcheck == True and next_spellcheck == False:
                gtkspell_spell = gtkspell.get_from_text_view(self.textview)
                gtkspell_spell.detach()
                self._previous_spellcheck = next_spellcheck
        else:
            assert False, "spellcheck flags are not boolean -- shouldn't get here"
            
    # Public API
    
    def get_spellcheck_options(self):
        """Get the list of installed spellcheck names."""
        return self._spellcheck_options.values()
    
    def set_spellcheck_state(self, spellcheck):
        """Set active spellcheck by it's name."""
        for code, name in self._spellcheck_options.items():
            if name == spellcheck:
                self.__real_set_active_spellcheck(code)
                return
        
    def get_spellcheck_state(self):
        """Get the name of the active spellcheck."""
        return self._spellcheck_options[self._previous_spellcheck]

