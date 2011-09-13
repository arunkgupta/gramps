#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2005 Donald N. Allingham
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

# $Id:exceptions.py 9912 2008-01-22 09:17:46Z acraphae $

"""Exceptions generated by the GrampsDb package."""


class GrampsDbException(Exception):
    
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value
        
    def __str__(self):
        return self.value

class GrampsDbWriteFailure(Exception):
    """
    Error used to indicate that a write to a database has failed.
    """
    def __init__(self, value, value2=""):
        Exception.__init__(self)
        self.value = value
        self.value2 = value2
        
    def __str__(self):
        return self.value
    
    def messages(self):
        return self.value, self.value2
    
class FileVersionError(Exception):
    """
    Error used to report that a file could not be read because it is written 
    in an unsupported version of the file format.
    """
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return self.value