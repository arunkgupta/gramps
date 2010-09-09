#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2005  Donald N. Allingham
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
Handles the Tip of the Day dialog
"""

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
from xml.parsers.expat import ParserCreate,ExpatError
from random import Random
from gettext import gettext as _
import os

#-------------------------------------------------------------------------
#
# GTK/GNOME modules
#
#-------------------------------------------------------------------------

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import const
import Config
import ManagedWindow
from QuestionDialog import ErrorDialog
from glade import Glade

#-------------------------------------------------------------------------
#
# Tip Display class
#
#-------------------------------------------------------------------------
class TipOfDay(ManagedWindow.ManagedWindow):
    def __init__(self, uistate):

        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self)
        
        xml = Glade()
        window = xml.toplevel
        self.set_window(window, 
                        xml.get_object("title"), 
                        _("Tip of the Day"), 
                        _("Tip of the Day"))
        
        self.tip = xml.get_object("tip")
        self.use = xml.get_object('usetips')
        self.use.set_active(Config.get(Config.USE_TIPS))
        image = xml.get_object('image')
        image.set_from_file(os.path.join(const.IMAGE_DIR, 'splash.jpg'))

        next = xml.get_object('next')
        next.connect("clicked", self.next_tip_cb)
        close = xml.get_object('close')
        close.connect("clicked", self.close_cb)
        
        try:
            tparser = TipParser()
        except (IOError,ExpatError), e:
            self.close()
            ErrorDialog(
                _("Failed to display tip of the day"),
                _("Unable to read the tips from external file.\n\n%s")%e)
            return
        self.tip_list = tparser.get()

        self.new_index = range(len(self.tip_list))
        Random().shuffle(self.new_index)

        self.index = 0
        self.next_tip_cb()
        
        window.show_all()

    def escape(self,text):
        text = text.replace('&','&amp;');       # Must be first
        text = text.replace(' > ',' &gt; ');    # Replace standalone > char
        text = text.replace('"','&quot;')       # quotes
        return text

    def next_tip_cb(self, dummy=None):
        tip_text = self.escape(self.tip_list[self.new_index[self.index]])
        self.tip.set_text(_(tip_text))
        self.tip.set_use_markup(True)
        self.index = (self.index + 1) % len(self.tip_list)

    def close_cb(self, dummy=None):
        Config.set(Config.USE_TIPS, self.use.get_active())
        self.close()
        
    def build_menu_names(self, obj):
        return (_("Tip of the Day"), None)

#-------------------------------------------------------------------------
#
# Tip parser class
#
#-------------------------------------------------------------------------
class TipParser(object):
    """
    Interface to the document template file
    """
    def __init__(self):
        """
        Create a template parser. The parser loads map of tempate names
        to the file containing the tempate.

        data - dictionary that holds the name to path mappings
        fpath - filename of the XML file
        """

        self.mylist = []
        self.skip = False
        xml_file = open(const.TIP_DATA)
        self.tlist = []
        parser = ParserCreate()
        parser.StartElementHandler = self.startElement
        parser.EndElementHandler = self.endElement
        parser.CharacterDataHandler = self.characters
        parser.ParseFile(xml_file)
        xml_file.close()

    def get(self):
        """
        Return the list of tips
        """
        return self.mylist
    
    def setDocumentLocator(self, locator):
        """Set the XML document locator"""
        self.locator = locator

    def startElement(self, tag, attrs):
        """
        Loads the dictionary when an XML tag of 'template' is found. The format
        XML tag is <template title=\"name\" file=\"path\">
        """
        if tag == "tip":
            self.tlist = []
            # Skip all tips with xml:lang attribute, as they are
            # already in the translation catalog
            self.skip = 'xml:lang' in attrs
        elif tag != "tips":
            # let all the other tags through, except for the "tips" tag
            self.tlist.append("<%s>" % tag)

    def endElement(self, tag):
        if tag == "tip" and not self.skip:
            text = ''.join(self.tlist)
            self.mylist.append(' '.join(text.split()))
        elif tag != "tips":
            # let all the other tags through, except for the "tips" tag
            self.tlist.append("</%s>" % tag)

    def characters(self, data):
        self.tlist.append(data)
