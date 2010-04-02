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
# Standard python modules
#
#-------------------------------------------------------------------------
from cStringIO import StringIO
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".DisplayState")

#-------------------------------------------------------------------------
#
# GNOME python modules
#
#-------------------------------------------------------------------------
import gobject
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import GrampsDb
import Config
import NameDisplay
import const
import ManagedWindow

DISABLED = -1

#-------------------------------------------------------------------------
#
# History manager
#
#-------------------------------------------------------------------------
class History(GrampsDb.GrampsDBCallback):

    __signals__ = {
        'changed'      : (list,),
        'menu-changed' : (list,),
        }

    def __init__(self):
        GrampsDb.GrampsDBCallback.__init__(self)
        self.history = []
        self.mhistory = []
        self.index = -1
        self.lock = False

    def clear(self):
        self.history = []
        self.mhistory = []
        self.index = -1
        self.lock = False

    def remove(self,person_handle,old_id=None):
        """Removes a person from the history list"""
        if old_id:
            del_id = old_id
        else:
            del_id = person_handle

        hc = self.history.count(del_id)
        for c in range(hc):
            self.history.remove(del_id)
            self.index -= 1
        
        mhc = self.mhistory.count(del_id)
        for c in range(mhc):
            self.mhistory.remove(del_id)
        self.emit('changed',(self.history,))
        self.emit('menu-changed',(self.mhistory,))

    def push(self,person_handle):
        self.prune()
        if len(self.history) == 0 or person_handle != self.history[-1]:
            self.history.append(person_handle)
            if person_handle in self.mhistory:
                self.mhistory.remove(person_handle)
            self.mhistory.append(person_handle)
            self.index += 1
        self.emit('menu-changed',(self.mhistory,))
        self.emit('changed',(self.history,))

    def forward(self,step=1):
        self.index += step
        person_handle = self.history[self.index]
        if person_handle not in self.mhistory:
            self.mhistory.append(person_handle)
            self.emit('menu-changed',(self.mhistory,))
        return str(self.history[self.index])

    def back(self,step=1):
        self.index -= step
        try:
            person_handle = self.history[self.index]
            if person_handle not in self.mhistory:
                self.mhistory.append(person_handle)
                self.emit('menu-changed',(self.mhistory,))
            return str(self.history[self.index])
        except IndexError:
            return u""

    def at_end(self):
        return self.index+1 == len(self.history)

    def at_front(self):
        return self.index <= 0

    def prune(self):
        if not self.at_end():
            self.history = self.history[0:self.index+1]


#-------------------------------------------------------------------------
#
# Recent Docs Menu
#
#-------------------------------------------------------------------------

_rct_top = '<ui><menubar name="MenuBar"><menu action="FileMenu"><menu action="OpenRecent">'
_rct_btm = '</menu></menu></menubar></ui>'

import RecentFiles
import os

class RecentDocsMenu:
    def __init__(self,uistate, state, fileopen):
        self.action_group = gtk.ActionGroup('RecentFiles')
        self.active = DISABLED
        self.uistate = uistate
        self.uimanager = uistate.uimanager
        self.fileopen = fileopen
        self.state = state

    def load(self,item):
        name = item.get_path()
        dbtype = item.get_mime()       
        self.fileopen(name,dbtype)

    def build(self):
        f = StringIO()
        f.write(_rct_top)
        gramps_rf = RecentFiles.GrampsRecentFiles()

        count = 0
        
        if self.active != DISABLED:
            self.uimanager.remove_ui(self.active)
            self.uimanager.remove_action_group(self.action_group)
            self.action_group = gtk.ActionGroup('RecentFiles')
            self.active = DISABLED
            
        actions = []
        rfiles = gramps_rf.gramps_recent_files
        rfiles.sort(by_time)

        new_menu = gtk.Menu()

        for item in rfiles:
            try:
                filename = os.path.basename(item.get_path()).replace('_','__')
                action_id = "RecentMenu%d" % count
                f.write('<menuitem action="%s"/>' % action_id)
                actions.append((action_id,None,filename,None,None,
                                make_callback(item,self.load)))
                mitem = gtk.MenuItem(filename)
                mitem.connect('activate', make_callback(item, self.load))
                mitem.show()
                new_menu.append(mitem)
            except RuntimeError:
                pass    # ignore no longer existing files
            
            count +=1
        f.write(_rct_btm)
        self.action_group.add_actions(actions)
        self.uimanager.insert_action_group(self.action_group,1)
        self.active = self.uimanager.add_ui_from_string(f.getvalue())
        self.uimanager.ensure_update()
        f.close()

        new_menu.show()
        self.uistate.set_open_recent_menu(new_menu)

def make_callback(n,f):
    return lambda x: f(n)

def by_time(a,b):
    return cmp(b.get_time(),a.get_time())


from GrampsLogger import RotateHandler

class WarnHandler(RotateHandler):
    def __init__(self,capacity,button):
        RotateHandler.__init__(self,capacity)
        self.setLevel(logging.WARN)
        self.button = button
        button.on_clicked(self.display)
        self.timer = None

    def emit(self,record):
        if self.timer:
            gobject.source_remove(self.timer)
        gobject.timeout_add(180*1000,self._clear)
        RotateHandler.emit(self,record)
        self.button.show()

    def _clear(self):
        self.button.hide()
        self.set_capacity(self._capacity)
        self.timer = None
        return False

    def display(self,obj):
        obj.hide()
        g = gtk.glade.XML(const.gladeFile,'scrollmsg')
        top = g.get_widget('scrollmsg')
        msg = g.get_widget('msg')
        buf = msg.get_buffer()
        for i in self.get_formatted_log():
            buf.insert_at_cursor(i + '\n')
        self.set_capacity(self._capacity)
        top.run()
        top.destroy()

class DisplayState(GrampsDb.GrampsDBCallback):

    __signals__ = {
        'filters-changed' : (str,),
        'filter-name-changed' : (str,unicode,unicode),
        'nameformat-changed' : None,
        'plugins-reloaded' : (list,list),
        }

    def __init__(self, window, status, progress, warnbtn, uimanager):

        self.busy = False
        self.uimanager = uimanager
        self.window = window
        GrampsDb.GrampsDBCallback.__init__(self)
        self.status = status
        self.status_id = status.get_context_id('GRAMPS')
        self.progress = progress
        self.phistory = History()
        self.gwm = ManagedWindow.GrampsWindowManager(uimanager)
        self.widget = None
        self.warnbtn = warnbtn

        formatter = logging.Formatter('%(levelname)s %(name)s: %(message)s')
        self.rh = WarnHandler(capacity=400,button=warnbtn)
        self.rh.setFormatter(formatter)
        self.rh.setLevel(logging.WARNING)
        self.log = logging.getLogger()
        self.log.addHandler(self.rh)
        # This call has been moved one level up,
        # but this connection is still made!
        # self.dbstate.connect('database-changed', self.db_changed)

    def set_sensitive(self, state):
        self.window.set_sensitive(state)
        
    def db_changed(self, db):
        from PluginUtils import _PluginMgr
        self.relationship = _PluginMgr.relationship_class(db)

    def display_relationship(self,dbstate):
        default_person = dbstate.db.get_default_person()
        active = dbstate.get_active_person()
        if default_person == None or active == None:
            return u''

        pname = NameDisplay.displayer.display(default_person)
        (name,plist) = self.relationship.get_relationship(
            default_person,active)

        if name:
            if plist == None:
                return name
            return _("%(relationship)s of %(person)s") % {
                'relationship' : name, 'person' : pname }
        else:
            return u""

    def clear_history(self):
        self.phistory.clear()

    def set_busy_cursor(self,value):
        if value == self.busy:
            return
        else:
            self.busy = value
        if value:
            self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        else:
            self.window.window.set_cursor(None)
        while gtk.events_pending():
            gtk.main_iteration()

    def set_open_widget(self,widget):
        self.widget = widget

    def set_open_recent_menu(self,menu):
        self.widget.set_menu(menu)

    def push_message(self, dbstate, text):
        self.status_text(text)
        gobject.timeout_add(5000,self.modify_statusbar,dbstate)

    def modify_statusbar(self,dbstate,active=None):
        self.status.pop(self.status_id)
        if dbstate.active == None:
            self.status.push(self.status_id,"")
        else:
            person = dbstate.get_active_person()
            if person:
                pname = NameDisplay.displayer.display(person)
                name = "[%s] %s" % (person.get_gramps_id(),pname)
                if Config.get(Config.STATUSBAR) > 1:
                    if person.handle != dbstate.db.get_default_handle():
                        msg = self.display_relationship(dbstate)
                        if msg:
                            name = "%s (%s)" % (name,msg.strip())
            else:
                name = _("No active person")
            self.status.push(self.status_id,name)

        while gtk.events_pending():
            gtk.main_iteration()

    def pulse_progressbar(self,value):
        self.progress.set_fraction(min(value/100.0,1.0))
        self.progress.set_text("%d%%" % value)
        while gtk.events_pending():
            gtk.main_iteration()

    def status_text(self,text):
        self.status.pop(self.status_id)
        self.status.push(self.status_id,text)
        while gtk.events_pending():
            gtk.main_iteration()


if __name__ == "__main__":

    import GrampsWidgets
    
    rh = WarnHandler(capacity=400,button=GrampsWidgets.WarnButton())
    log = logging.getLogger()
    log.setLevel(logging.WARN)
    log.addHandler(rh)
