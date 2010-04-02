#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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

# $Id:_EditFilter.py 9912 2008-01-22 09:17:46Z acraphae $

"""
Custom Filter Editor tool.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
log = logging.getLogger(".FilterEdit")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import const
import ListModel
import ManagedWindow
import GrampsDisplay
import Errors

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class EditFilter(ManagedWindow.ManagedWindow):
    
    def __init__(self, namespace, dbstate, uistate, track, gfilter,
                 filterdb, update):

        ManagedWindow.ManagedWindow.__init__(self, uistate, track, self)

        self.namespace = namespace
        self.update = update
        self.dbstate = dbstate
        self.db = dbstate.db
        self.filter = gfilter
        self.filterdb = filterdb
        
        self.define_glade('define_filter', const.RULE_GLADE)
        
        self.set_window(
            self.get_widget('define_filter'),
            self.get_widget('title'),
            _('Define filter'))
        
        self.rlist = ListModel.ListModel(
            self.get_widget('rule_list'),
            [(_('Name'),-1,150),(_('Values'),-1,150)],
            self.select_row,
            self.on_edit_clicked)
                                         
        self.fname = self.get_widget('filter_name')
        self.logical = self.get_widget('rule_apply')
        self.logical_not = self.get_widget('logical_not')
        self.comment = self.get_widget('comment')
        self.ok_btn = self.get_widget('ok')
        self.edit_btn = self.get_widget('edit')
        self.del_btn = self.get_widget('delete')
        self.add_btn = self.get_widget('add')

        self.ok_btn.connect('clicked', self.on_ok_clicked)
        self.edit_btn.connect('clicked', self.on_edit_clicked)
        self.del_btn.connect('clicked', self.on_delete_clicked)
        self.add_btn.connect('clicked', self.on_add_clicked)
        
        self.get_widget('help').connect('clicked',
                                        self.on_help_clicked)
        self.get_widget('cancel').connect('clicked',
                                          self.close_window)
        self.fname.connect('changed', self.filter_name_changed)

        if self.filter.get_logical_op() == 'or':
            self.logical.set_active(1)
        elif self.filter.get_logical_op() == 'one':
            self.logical.set_active(2)
        else:
            self.logical.set_active(0)
        self.logical_not.set_active(self.filter.get_invert())
        if self.filter.get_name():
            self.fname.set_text(self.filter.get_name())
        self.comment.set_text(self.filter.get_comment())
        self.draw_rules()

        self.show()

    def on_help_clicked(self, obj):
        """Display the relevant portion of GRAMPS manual"""
        GrampsDisplay.help('tools-util-cfe')

    def close_window(self, obj):
        self.close()

    def filter_name_changed(self, obj):
        name = unicode(self.fname.get_text())
        # Make sure that the name is not empty
        # and not in the list of existing filters (excluding this one)
        names = [filt.get_name()
                 for filt in self.filterdb.get_filters(self.namespace)
                 if filt != self.filter]
        self.ok_btn.set_sensitive((len(name) != 0) and (name not in names))
    
    def select_row(self, obj):
        store, node = self.rlist.get_selected()
        if node:
            self.edit_btn.set_sensitive(True)
            self.del_btn.set_sensitive(True)
        else:
            self.edit_btn.set_sensitive(False)
            self.del_btn.set_sensitive(False)

    def draw_rules(self):
        self.rlist.clear()
        for r in self.filter.get_rules():
            self.rlist.add([r.name,r.display_values()],r)
            
    def on_ok_clicked(self, obj):
        n = unicode(self.fname.get_text()).strip()
        if n == '':
            return
        if n != self.filter.get_name():
            self.uistate.emit('filter-name-changed',
                              (self.namespace,unicode(self.filter.get_name()), n))
        self.filter.set_name(n)
        self.filter.set_comment(unicode(self.comment.get_text()).strip())
        for f in self.filterdb.get_filters(self.namespace)[:]:
            if n == f.get_name():
                self.filterdb.get_filters(self.namespace).remove(f)
                break
        val = self.logical.get_active() 
        if val == 1:
            op = 'or'
        elif val == 2:
            op = 'one'
        else:
            op = 'and'
        self.filter.set_logical_op(op)
        self.filter.set_invert(self.logical_not.get_active())
        self.filterdb.add(self.namespace,self.filter)
        self.update()
        self.close()
        
    def on_add_clicked(self, obj):
        from _EditRule import EditRule
        
        try:
            EditRule(self.namespace, self.dbstate, self.uistate, self.track,
                     self.filterdb, None, _('Add Rule'), self.update_rule,
                     self.filter.get_name())
        except Errors.WindowActiveError:
            pass

    def on_edit_clicked(self, obj):
        store, node = self.rlist.get_selected()
        if node:
            from _EditRule import EditRule
            
            d = self.rlist.get_object(node)

            try:
                EditRule(self.namespace, self.dbstate, self.uistate, self.track,
                         self.filterdb, d, _('Edit Rule'), self.update_rule,
                         self.filter.get_name())
            except Errors.WindowActiveError:
                pass

    def update_rule(self, old_rule, new_rule):
        if old_rule:
            self.filter.delete_rule(old_rule)
        self.filter.add_rule(new_rule)
        self.draw_rules()

    def on_delete_clicked(self, obj):
        store, node = self.rlist.get_selected()
        if node:
            gfilter = self.rlist.get_object(node)
            self.filter.delete_rule(gfilter)
            self.draw_rules()

