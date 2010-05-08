#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009 Benny Malengier
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

"""Html and Html format management for the different reports 
"""

#------------------------------------------------------------------------
#
# Python modules
#
#------------------------------------------------------------------------
from xml.sax.saxutils import escape
import os.path

#-------------------------------------------------------------------------
#
# GTK modules
#
#-------------------------------------------------------------------------

#------------------------------------------------------------------------
#
# Gramps modules
#
#------------------------------------------------------------------------
from gen.plug.docbackend import DocBackend
from libhtml import Html
from Utils import xml_lang

#------------------------------------------------------------------------
#
# Document Backend class for html pages
#
#------------------------------------------------------------------------

class HtmlBackend(DocBackend):
    """
    Implementation for html pages
    Contrary to other backends, we do not write to file but to a Html object
    instead, writing out the file on close.
    """
    
    STYLETAG_TO_PROPERTY = {
        DocBackend.FONTCOLOR : 'color:%s;',
        DocBackend.HIGHLIGHT : 'background-color:%s;',
        DocBackend.FONTFACE  : "font-family:'%s';",
        DocBackend.FONTSIZE  : 'font-size:%spx;',
    }

    # overwrite base class attributes, they become static var of CairoDoc
    SUPPORTED_MARKUP = [
            DocBackend.BOLD,
            DocBackend.ITALIC,
            DocBackend.UNDERLINE,
            DocBackend.FONTFACE,
            DocBackend.FONTSIZE,
            DocBackend.FONTCOLOR,
            DocBackend.HIGHLIGHT,
            DocBackend.SUPERSCRIPT, 
            DocBackend.LINK,
            ]

    STYLETAG_MARKUP = {
        DocBackend.BOLD        : ("<strong>", "</strong>"),
        DocBackend.ITALIC      : ("<em>", "</em>"),
        DocBackend.UNDERLINE   : ('<span style="text-decoration:underline;">', 
                                    "</span>"),
        DocBackend.SUPERSCRIPT : ("<sup>", "</sup>"),
    }
    
    ESCAPE_FUNC = lambda self: escape

    def __init__(self, filename=None):
        """
        @param filename: path name of the file the backend works on
        """
        DocBackend.__init__(self, filename)
        self.html_page = None
        self.html_header = None
        self.html_body = None
        self._subdir = None
        self.title = None
        self.build_link = None
        
    def _create_xmltag(self, tagtype, value):
        """
        overwrites the method in DocBackend
        creates the pango xml tags needed for non bool style types
        """
        if tagtype not in self.SUPPORTED_MARKUP:
            return None
        elif tagtype == DocBackend.LINK:
            return self.format_link(value)
        elif tagtype == DocBackend.FONTSIZE:
            #size is in points
            value = str(value)
        elif tagtype == DocBackend.FONTFACE:
            #fonts can have strange symbols in them, ' needs to be escaped
            value = value.replace("'", "\\'")
        return ('<span style="%s">' % (self.STYLETAG_TO_PROPERTY[tagtype] %
                                       (value)), 
                '</span>')

    def _checkfilename(self):
        """
        Check to make sure filename satisfies the standards for this filetype
        """
        fparts = os.path.basename(self._filename).split('.')
        if not len(fparts) >= 2 and not (fparts[-1] == 'html' or 
                fparts[-1] == 'htm' or fparts[-1] == 'php'):
            self._filename = self._filename + ".htm"
        fparts = os.path.basename(self._filename).split('.')
        self._subdir = '.'.join(fparts[:-1])

    def set_title(self, title):
        """
        Set the title to use for the html page
        """
        self.title = title

    def open(self):
        """
        overwrite method, htmlbackend creates a html object that is written on
        close
        """
        DocBackend.open(self)
        if not os.path.isdir(self.datadirfull()): 
            os.mkdir(self.datadirfull())
        self.html_page, self.html_header, self.html_body = Html.page(
                        lang=xml_lang(), title=self.title)

    def __write(self, string):
        """ a write to the file
        """
        DocBackend.write(self, string + '\n')

    def write(self, obj):
        """ write to the html page. One can pass a html object, or a string
        """
        self.html_body += obj
        
    def close(self):
        """
        write out the html to the page
        """
        self.html_page.write(self.__write, indent='  ')
        DocBackend.close(self)
    
    def datadir(self):
        """
        the directory where to save extra files
        """
        return self._subdir
    
    def datadirfull(self):
        """
        full path of the datadir directory
        """
        return os.path.join(os.path.dirname(self.getf()), self.datadir())

    def format_link(self, value):
        """
        Override of base method.
        """
        if value.startswith("gramps://"):
            if self.build_link:
                obj_class, prop, handle = value[9:].split("/", 3)
                if prop in ["handle", "gramps_id"]:
                    value = self.build_link(prop, handle, obj_class, up=True)
                    if not value:
                        return self.STYLETAG_MARKUP[DocBackend.UNDERLINE]
                else:
                    return self.STYLETAG_MARKUP[DocBackend.UNDERLINE]
            else:
                return self.STYLETAG_MARKUP[DocBackend.UNDERLINE]
        return ('<a href="%s">' % self.ESCAPE_FUNC()(value), 
                '</a>')
        
