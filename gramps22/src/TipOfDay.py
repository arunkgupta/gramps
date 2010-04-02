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

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
from xml.parsers.expat import ParserCreate
from random import Random
from gettext import gettext as _
import os

#-------------------------------------------------------------------------
#
# GTK/GNOME modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import const
import Config
import ManagedWindow

#-------------------------------------------------------------------------
#
# Tip Display class
#
#-------------------------------------------------------------------------
class TipOfDay(ManagedWindow.ManagedWindow):
    def __init__(self,uistate):

        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self)
        
        xml = gtk.glade.XML(const.gladeFile, "tod_window", "gramps")
        window = xml.get_widget("tod_window")
        self.set_window(window,
                        xml.get_widget("title"),
                        _("Tip of the Day"),
                        _("Tip of the Day"))
        
        self.tip = xml.get_widget("tip")
        self.use = xml.get_widget('usetips')
        self.use.set_active(Config.get(Config.USE_TIPS))
        image = xml.get_widget('image')
        image.set_from_file(os.path.join(const.image_dir,'splash.jpg'))

        next = xml.get_widget('next')
        next.connect("clicked",self.next_tip_cb)
        close = xml.get_widget('close')
        close.connect("clicked",self.close_cb)
        
        tp = TipParser()
        self.tip_list = tp.get()

        self.new_index = range(len(self.tip_list))
        Random().shuffle(self.new_index)

        self.index = 0
        self.next_tip_cb()
        
        window.show_all()

    def next_tip_cb(self,dummy=None):
        tip_text = self.escape(self.tip_list[self.new_index[self.index]])
        self.tip.set_text(_(tip_text))
        self.tip.set_use_markup(True)
        if self.index >= len(self.tip_list)-1:
            self.index = 0
        else:
            self.index += 1

    def escape(self,text):
        text = text.replace('&','&amp;');       # Must be first
        text = text.replace(' > ',' &gt; ')     # Replace standalone > char
        text = text.replace('"','&quot;')       # quotes
        return text

    def close_cb(self,dummy=None):
        Config.set(Config.USE_TIPS,self.use.get_active())
        self.close()
        
    def build_menu_names(self,obj):
        return (_("Tip of the Day"), None)

#-------------------------------------------------------------------------
#
# Tip parser class
#
#-------------------------------------------------------------------------
class TipParser:
    """
    Interface to the document template file
    """
    def __init__(self):
        """
        Creates a template parser. The parser loads map of tempate names
        to the file containing the tempate.

        data - dictionary that holds the name to path mappings
        fpath - filename of the XML file
        """

        self.mylist = []
        xml_file = open(const.tipdata)
        self.tlist = []
        p = ParserCreate()
        p.StartElementHandler = self.startElement
        p.EndElementHandler = self.endElement
        p.CharacterDataHandler = self.characters
        p.ParseFile(xml_file)
        xml_file.close()

    def get(self):
        return self.mylist
    
    def setDocumentLocator(self,locator):
        """Sets the XML document locator"""
        self.locator = locator

    def startElement(self,tag,attrs):
        """
        Loads the dictionary when an XML tag of 'template' is found. The format
        XML tag is <template title=\"name\" file=\"path\">
        """
        if tag == "tip":
            self.tlist = []
            # Skip all tips with xml:lang attribute, as they are
            # already in the translation catalog
            self.skip = attrs.has_key('xml:lang')
        elif tag != "tips":
            # let all the other tags through, except for the "tips" tag
            self.tlist.append("<%s>" % tag)

    def endElement(self,tag):
        if tag == "tip" and not self.skip:
            text = ''.join(self.tlist)
            self.mylist.append(' '.join(text.split()))
        elif tag != "tips":
            # let all the other tags through, except for the "tips" tag
            self.tlist.append("</%s>" % tag)

    def characters(self, data):
        self.tlist.append(data)
