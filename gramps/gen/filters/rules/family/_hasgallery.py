#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2008  Brian G. Matherly
# Copyright (C) 2008  Jerome Rapinat
# Copyright (C) 2008  Benny Malengier
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
# gen.filters.rules/Family/_HasGallery.py
# $Id$
#

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
from .._hasgallerybase import HasGalleryBase

#-------------------------------------------------------------------------
# "Families who have media object reference"
#-------------------------------------------------------------------------
class HasGallery(HasGalleryBase):
    """Rule that checks for family who has media object reference"""

    name        = _('Families with <count> media')
    description = _("Matches families with a certain number of items in the gallery")
