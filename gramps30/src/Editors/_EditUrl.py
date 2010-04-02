#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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
# python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from gtk import glade

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import Config
from _EditSecondary import EditSecondary
from GrampsWidgets import MonitoredEntry, PrivacyButton, MonitoredDataType

#-------------------------------------------------------------------------
#
# EditUrl class
#
#-------------------------------------------------------------------------
class EditUrl(EditSecondary):

    WIDTH_KEY = Config.URL_WIDTH
    HEIGHT_KEY = Config.URL_HEIGHT

    def __init__(self, dbstate, uistate, track, name, url, callback):

        EditSecondary.__init__(self, dbstate, uistate, track,
                               url, callback)

    def _local_init(self):
        self.top = glade.XML(const.GLADE_FILE, "url_edit", "gramps")
        self.jump = self.top.get_widget('jump')

        self.set_window(self.top.get_widget("url_edit"),
                        self.top.get_widget("title"),
                        _('Internet Address Editor'))
            
    def _connect_signals(self):
        self.jump.connect('clicked', self.jump_to)
        self.define_cancel_button(self.top.get_widget('button125'))
        self.define_ok_button(self.top.get_widget('button124'), self.save)
        self.define_help_button(self.top.get_widget('button130'), 'gramps-edit_complete')
        
    def jump_to(self, obj):
        if self.obj.get_path():
            import GrampsDisplay
            GrampsDisplay.url(self.obj.get_path())

    def _setup_fields(self):
        self.des  = MonitoredEntry(self.top.get_widget("url_des"),
                                   self.obj.set_description, 
                                   self.obj.get_description, self.db.readonly)

        self.addr  = MonitoredEntry(self.top.get_widget("url_addr"), 
                                    self.obj.set_path, self.obj.get_path, 
                                    self.db.readonly)
        
        self.priv = PrivacyButton(self.top.get_widget("priv"),
                                  self.obj, self.db.readonly)

        self.type_sel = MonitoredDataType(self.top.get_widget("type"), 
                                          self.obj.set_type, 
                                          self.obj.get_type, self.db.readonly)
            
    def build_menu_names(self, obj):
        etitle =_('Internet Address Editor')
        return (etitle, etitle)

    def save(self,*obj):
        self.callback(self.obj)
        self.close()
