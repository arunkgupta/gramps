# -*- coding: utf-8 -*-
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
# Rule
#
#-------------------------------------------------------------------------
class Rule(object):
    """Base rule class."""

    labels      = []
    name        = ''
    category    = _('Miscellaneous filters')
    description = _('No description')

    def __init__(self, arg):
        self.set_list(arg)

    def is_empty(self):
        return False
    
    def prepare(self, db):
        pass

    def reset(self):
        pass
 
    def set_list(self, arg):
        assert isinstance(arg, list) or arg is None, "Argument is not a list"
        assert len(arg) == len(self.labels), \
               "ERROR: Number of arguments does not match number of labels.\n"\
               "       list:   %s\n"\
               "       labels: %s" % (arg,self.labels)
        self.list = arg

    def values(self):
        return self.list
    
    def check(self):
        return len(self.list) == len(self.labels)

    def apply(self, db, person):
        return True

    def display_values(self):
        v = ( '%s="%s"' % (_(self.labels[ix]), self.list[ix])
              for ix in xrange(len(self.list)) if self.list[ix] )

        return ';'.join(v)

    def match_substring(self, param_index, str_var):
        # make str_var unicode so that search for ü works
        # see issue 3188
        str_var = unicode(str_var)
        if self.list[param_index] and \
               (str_var.upper().find(self.list[param_index].upper()) == -1):
            return False
        else:
            return True
