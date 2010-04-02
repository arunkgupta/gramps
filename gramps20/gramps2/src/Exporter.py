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

# $Id$

# Written by Alex Roitman

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import os
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# Gnome modules
#
#-------------------------------------------------------------------------
import gtk
from gnome.ui import Druid, DruidPageEdge, DruidPageStandard

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import Utils
import PluginMgr
import QuestionDialog
import GrampsKeys
import GrampsDisplay

#-------------------------------------------------------------------------
#
# Exporter
#
#-------------------------------------------------------------------------
class Exporter:
    """
    This class creates Gnome Druid to guide the user through the various
    Save as/Export options. The overall goal is to keep things simple by
    presenting few choice options on each druid page.
    
    The export formats and options are obtained from the plugins, with the
    exception of a native save. Native save as just copies file to another 
    name. 
    """

    def __init__(self,parent,parent_window):
        """
        Set up the window, the druid, and build all the druid's pages. 
        Some page elements are left empty, since their contents depends
        on the user choices and on the success of the attempted save. 
        """
        self.parent = parent
        self.parent_window = parent_window
        if self.parent.active_person:
            self.person = self.parent.active_person
        else:
            self.person = self.parent.find_initial_person()

        self.build_exports()
        self.confirm_label = gtk.Label()
        self.extra_pages = []

        self.w = gtk.Window()

        self.fg_color = gtk.gdk.color_parse('#7d684a')
        self.bg_color = gtk.gdk.color_parse('#e1dbc5')
        self.logo = gtk.gdk.pixbuf_new_from_file("%s/gramps.png" % const.rootDir)
        self.splash = gtk.gdk.pixbuf_new_from_file("%s/splash.jpg" % const.rootDir)

        self.d = Druid()
        self.w.add(self.d)
        self.w.set_title(_('GRAMPS: Export'))
        self.d.add(self.build_info_page())
        self.d.add(self.build_format_page())
        self.file_sel_page = self.build_file_sel_page()
        self.d.add(self.file_sel_page)
        self.d.add(self.build_confirm_page())
        self.last_page = self.build_last_page()
        self.d.add(self.last_page)

        self.d.set_show_help(True)
        self.d.connect('cancel',self.close)
        self.d.connect('help',self.help)
        self.w.connect("destroy_event",self.close)
        self.w.set_transient_for(self.parent_window)
        
        self.w.show_all()

    def close(self,obj,obj2=None):
        """
        Close and delete handler.
        """
        self.w.destroy()

    def help(self,obj):
        """
        Help handler.
        """
        GrampsDisplay.help('export-data')

    def build_info_page(self):
        """
        Build initial druid page with the overall information about the process.
        This is a static page, nothing fun here :-)
        """
        p = DruidPageEdge(0)
        p.set_title(_('Saving your data'))
        p.set_title_color(self.fg_color)
        p.set_bg_color(self.bg_color)
        p.set_logo(self.logo)
        p.set_watermark(self.splash)
        p.set_text(_('Under normal circumstances, GRAMPS does not require you '
                    'to directly save your changes. All changes you make are '
                    'immediately saved to the database.\n\n'
                    'This process will help you save a copy of your data '
                    'in any of the several formats supported by GRAMPS. '
                    'This can be used to make a copy of your data, backup '
                    'your data, or convert it to a format that will allow '
                    'you to transfer it to a different program.\n\n'
                    'If you change your mind during this process, you '
                    'can safely press the Cancel button at any time and your '
                    'present database will still be intact.'))
        return p

    def build_last_page(self):
        """
        Build the last druid page. The actual text will be added after the
        save is performed and the success status us known. 
        """
        p = DruidPageEdge(1)
        p.set_title_color(self.fg_color)
        p.set_bg_color(self.bg_color)
        p.set_logo(self.logo)
        p.set_watermark(self.splash)
        p.connect('finish',self.close)
        return p

    def build_confirm_page(self):
        """
        Build a save confirmation page. Setting up the actual label 
        text is deferred until the page is being prepared. This
        is necessary, because no choice is made by the user when this
        page is set up. 
        """
        p = DruidPageStandard()
        p.set_title(_('Final save confirmation'))
        p.set_title_foreground(self.fg_color)
        p.set_background(self.bg_color)
        p.set_logo(self.logo)
        
        p.append_item("",self.confirm_label,"")

        p.connect('prepare',self.build_confirm_label)
        p.connect('next',self.save)
        return p

    def build_confirm_label(self,obj,obj2):
        """
        Build the text of the confirmation label. This should query
        the selected options (format, filename) and present the summary
        of the proposed action.
        """
        filename = self.chooser.get_filename()
        name = os.path.split(filename)[1]
        folder = os.path.split(filename)[0]
        ix = self.get_selected_format_index()
        format = self.exports[ix][1].replace('_','')

        self.confirm_label.set_text(
                _('The data will be saved as follows:\n\n'
                'Format:\t%s\nName:\t%s\nFolder:\t%s\n\n'
                'Press Forward to proceed, Cancel to abort, or Back to '
                'revisit your options.') % (format, name, folder))
        self.confirm_label.set_line_wrap(True)

    def save(self,obj,obj2):
        """
        Perform the actual Save As/Export operation. 
        Depending on the success status, set the text for the final page.
        """
        filename = self.chooser.get_filename()
        GrampsKeys.save_last_export_dir(os.path.split(filename)[0])
        ix = self.get_selected_format_index()
        if self.exports[ix][3]:
            success = self.exports[ix][0](self.parent.db,filename,self.person,
                    self.option_box_instance)
        else:
            success = self.exports[ix][0](self.parent.db,filename,self.person)
        if success:
            self.last_page.set_title(_('Your data has been saved'))
            self.last_page.set_text(_('The copy of your data has been '
                    'successfully saved. You may press Apply button '
                    'now to continue.\n\n'
                    'Note: the database currently opened in your GRAMPS '
                    'window is NOT the file you have just saved. '
                    'Future editing of the currently opened database will '
                    'not alter the copy you have just made. '))
        else:
            self.last_page.set_title(_('Saving failed'))
            self.last_page.set_text(_('There was an error '
                    'while saving your data. Please go back and try again.\n\n'
                    'Note: your currently opened database is safe. It was only '
                    'a copy of your data that failed to save.'))

    def build_format_page(self):
        """
        Build a page with the table of format radio buttons and 
        their descriptions.
        """
        self.format_buttons = []

        p = DruidPageStandard()
        p.set_title(_('Choosing the format to save'))
        p.set_title_foreground(self.fg_color)
        p.set_background(self.bg_color)
        p.set_logo(self.logo)

        box = gtk.VBox()
        box.set_spacing(12)
        p.append_item("",box,"")
        
        table = gtk.Table(2*len(self.exports),2)
        table.set_row_spacings(6)
        table.set_col_spacings(6)
        
        tip = gtk.Tooltips()
        
        group = None
        for ix in range(len(self.exports)):
            title = self.exports[ix][1]
            description= self.exports[ix][2]

            button = gtk.RadioButton(group,title)
            if not group:
                group = button
            self.format_buttons.append(button)
            table.attach(button,0,2,2*ix,2*ix+1)
            tip.set_tip(button,description)
        
        box.add(table)
        box.show_all()
        p.connect('next',self.build_options)
        return p

    def build_options(self,obj,obj2):
        """
        Build an extra page with the options specific for the chosen format.
        If there's already a page (or pages) for this format in 
        self.empty_pages then do nothing, otherwise add a page.

        If the chosen format does not have options then remove all
        extra pages that are already there (from previous user passes 
        through the druid).
        """
        ix = self.get_selected_format_index()
        if self.exports[ix][3]:
            title = self.exports[ix][3][0]
            for (ep_ix,ep) in self.extra_pages:
                if ep_ix == ix:
                    return
                else:
                   ep.destroy()
                   self.extra_pages.remove((ep_ix,ep))

            option_box_class = self.exports[ix][3][1]
            self.option_box_instance = option_box_class(self.person)

            p = DruidPageStandard()
            p.set_title(title)
            p.set_title_foreground(self.fg_color)
            p.set_background(self.bg_color)
            p.set_logo(self.logo)
            p.append_item("",self.option_box_instance.get_option_box(),"")
            self.extra_pages.append((ix,p))
            self.d.insert_page(self.file_sel_page,p)
            p.show_all()
        else:
            for (ep_ix,ep) in self.extra_pages:
                ep.destroy()
            self.extra_pages = []

    def build_file_sel_page(self):
        """
        Build a druid page embedding the FileChooserWidget.
        """
        p = DruidPageStandard()
        p.set_title(_('Selecting the file name'))
        p.set_title_foreground(self.fg_color)
        p.set_background(self.bg_color)
        p.set_logo(self.logo)

        self.chooser = gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_SAVE)
        self.chooser.set_local_only(False)
        p.append_item("",self.chooser,"")
        # Dirty hack to enable proper EXPAND and FILL properties of the chooser
        parent = self.chooser.get_parent()
        parent.set_child_packing(self.chooser,1,1,0,gtk.PACK_START)
        gradnparent = parent.get_parent()
        gradnparent.set_child_packing(parent,1,1,0,gtk.PACK_START)
        p.connect('prepare',self.suggest_filename)
        return p

    def suggest_filename(self,obj,obj2):
        """
        Prepare suggested filename and set it in the file chooser. 
        """
        ix = self.get_selected_format_index()
        ext = self.exports[ix][4]
        
        # Suggested folder: try last export, then last import, then home.
        default_dir = GrampsKeys.get_last_export_dir()
        if len(default_dir)<=1:
            default_dir = GrampsKeys.get_last_import_dir()
        if len(default_dir)<=1:
            default_dir = '~/'

        if ext == 'gramps':
            new_filename = os.path.expanduser(default_dir + 'data.gramps')
        elif ext == 'burn':
            new_filename = os.path.basename(self.parent.db.get_save_path())
        else:
            new_filename = Utils.get_new_filename(ext,default_dir)
        self.chooser.set_current_folder(default_dir)
        self.chooser.set_current_name(os.path.split(new_filename)[1])

    def get_selected_format_index(self):
        """
        Query the format radiobuttons and return the index number 
        of the selected one. 
        """
        for ix in range(len(self.format_buttons)):
            button = self.format_buttons[ix]
            if button.get_active():
                return ix
        else:
            return 0
    
    def native_export(self,database,filename,person):
        """
        Native database export.
        
        In the future, filter and other options may be added.
        """
        try:
            import WriteGrdb
            WriteGrdb.exportData(database,filename,person)
            return 1
        except IOError, msg:
            QuestionDialog.ErrorDialog( _("Could not write file: %s") % filename,
                    _('System message was: %s') % msg )
            return 0

    def build_exports(self):
        """
        This method builds its own list of available exports. 
        The list is built from the PluginMgr.export_list list 
        and from the locally defined exports (i.e. native export defined here).
        """
        native_title = _('GRAMPS _GRDB database')
        native_description =_('The GRAMPS GRDB database is a format '
                'that GRAMPS uses to store information. '
                'Selecting this option will allow you to '
                'make a copy of the current database.') 
        native_config = None
        native_ext = 'grdb'
        native_export = self.native_export

        self.exports = [ (native_export,native_title,native_description,
                    native_config,native_ext) ]
        self.exports = self.exports + [ item for item in PluginMgr.export_list ]
