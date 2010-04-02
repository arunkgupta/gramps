#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2006  Donald N. Allingham
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

# $Id:gramps_main.py 9912 2008-01-22 09:17:46Z acraphae $

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _
import os
import platform

import logging
log = logging.getLogger(".")

#-------------------------------------------------------------------------
#
# GTK+/GNOME modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS  modules
#
#-------------------------------------------------------------------------
import ViewManager
import ArgHandler
import Config
import const
import Errors
import TipOfDay
import DataViews
import DbState
from Mime import mime_type_is_defined
from QuestionDialog import ErrorDialog

#-------------------------------------------------------------------------
#
# helper functions
#
#-------------------------------------------------------------------------


def register_stock_icons ():
    """
    Add the gramps names for its icons (eg gramps-person) to the GTK icon
    factory. This allows all gramps modules to call up the icons by their name
    """
        
    #iconpath to the base image. The front of the list has highest priority 
    if platform.system() == "Windows":
        iconpaths = [
                    (os.path.join(const.IMAGE_DIR, '48x48'), '.png'), 
                    (const.IMAGE_DIR, '.png'), 
                    ]
    else :
        iconpaths = [
                    (os.path.join(const.IMAGE_DIR, 'scalable'), '.svg'), 
                    (const.IMAGE_DIR, '.svg'), (const.IMAGE_DIR, '.png'), 
                    ]
    
    #sizes: menu=16, small_toolbar=18, large_toolbar=24, 
    #       button=20, dnd=32, dialog=48
    #add to the back of this list to overrule images set at beginning of list
    extraiconsize = [
                    (os.path.join(const.IMAGE_DIR, '22x22'), 
                            gtk.ICON_SIZE_LARGE_TOOLBAR), 
                    (os.path.join(const.IMAGE_DIR, '16x16'), 
                            gtk.ICON_SIZE_MENU), 
                    (os.path.join(const.IMAGE_DIR, '22x22'), 
                            gtk.ICON_SIZE_BUTTON), 
                    ]

    items = [
        ('gramps-db', _('Family Trees'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-address', _('Address'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-attribute', _('Attribute'), gtk.gdk.CONTROL_MASK, 0, ''), 
        #('gramps-bookmark', _('Bookmarks'), gtk.gdk.CONTROL_MASK, 0, ''), 
        #('gramps-bookmark-delete', _('Delete bookmark'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-bookmark-edit', _('Organize Bookmarks'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-bookmark-new', _('Add Bookmark'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-date', _('Date'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-date-edit', _('Edit Date'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-event', _('Events'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-family', _('Family'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-font', _('Font'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-font-color', _('Font Color'), gtk.gdk.CONTROL_MASK, 0, ''),        
        ('gramps-font-bgcolor', _('Font Background Color'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-gramplet', _('Gramplets'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-lock', _('Public'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-media', _('Media'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-notes', _('Notes'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-parents', _('Parents'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-parents-add', _('Add Parents'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-parents-open', _('Select Parents'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-pedigree', _('Pedigree'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-person', _('Person'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-place', _('Places'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-relation', _('Relationships'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-reports', _('Reports'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-repository', _('Repositories'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-source', _('Sources'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-spouse', _('Add Spouse'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-tools', _('Tools'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-unlock', _('Private'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-viewmedia', _('View'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-zoom-in', _('Zoom In'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-zoom-out', _('Zoom Out'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-zoom-fit-width', _('Fit Width'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ('gramps-zoom-best-fit', _('Fit Page'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ]
    # the following icons are not yet in new directory structure
    # they should be ported in the near future
    items_legacy = [
         ('gramps-export', _('Export'), gtk.gdk.CONTROL_MASK, 0, ''), 
         ('gramps-import', _('Import'), gtk.gdk.CONTROL_MASK, 0, ''),
         ('gramps-undo-history', _('Undo History'), gtk.gdk.CONTROL_MASK, 0, ''), 
         ('gramps-url', _('URL'), gtk.gdk.CONTROL_MASK, 0, ''), 
        ]
    
    # Register our stock items
    gtk.stock_add (items+items_legacy)
    
    # Add our custom icon factory to the list of defaults
    factory = gtk.IconFactory ()
    factory.add_default ()
    
    for data in items+items_legacy:
        pixbuf = 0
        for (dirname, ext) in iconpaths:
            icon_file = os.path.expanduser(os.path.join(dirname, data[0]+ext))
            if os.path.isfile(icon_file):
                try:
                    pixbuf = gtk.gdk.pixbuf_new_from_file (icon_file)
                    break
                except:
                    pass
                  
        if not pixbuf :
            icon_file = os.path.join(const.IMAGE_DIR, 'gramps.png')
            pixbuf = gtk.gdk.pixbuf_new_from_file (icon_file)
            
        pixbuf = pixbuf.add_alpha(True, chr(0xff), chr(0xff), chr(0xff))
        icon_set = gtk.IconSet (pixbuf)
        #add different sized icons, always png type!
        for size in extraiconsize :
            pixbuf = 0
            icon_file = os.path.expanduser(
                    os.path.join(size[0], data[0]+'.png'))
            if os.path.isfile(icon_file):
                try:
                    pixbuf = gtk.gdk.pixbuf_new_from_file (icon_file)
                except:
                    pass
                    
            if pixbuf :
                source = gtk.IconSource()
                source.set_size_wildcarded(False)
                source.set_size(size[1])
                source.set_pixbuf(pixbuf)
                icon_set.add_source(source)
            
        factory.add (data[0], icon_set)

def build_user_paths():
    """ check/make user-dirs on each Gramps session"""
    for path in const.USER_DIRLIST:
        if not os.path.isdir(path):
            os.mkdir(path)

#-------------------------------------------------------------------------
#
# Main Gramps class
#
#-------------------------------------------------------------------------
class Gramps:
    """
    Main class corresponding to a running gramps process.

    There can be only one instance of this class per gramps application
    process. It may spawn several windows and control several databases.
    """
    
    def __init__(self, args):
        stopload = False
        try:
            build_user_paths()  
        except OSError, msg:
            ErrorDialog(_("Configuration error"), str(msg))
        except Errors.GConfSchemaError, val:
            ErrorDialog(_("Configuration error"), str(val) +
                        _("\n\nPossibly the installation of GRAMPS "
                          "was incomplete. Make sure the GConf schema "
                          "of GRAMPS is properly installed."))
            gtk.main_quit()
            stopload = True
        except:
            log.error("Error reading configuration.", exc_info=True)
            
        if not mime_type_is_defined(const.APP_GRAMPS):
            ErrorDialog(_("Configuration error"), 
                        _("A definition for the MIME-type %s could not "
                          "be found \n\nPossibly the installation of GRAMPS "
                          "was incomplete. Make sure the MIME-types "
                          "of GRAMPS are properly installed.")
                        % const.APP_GRAMPS)
            gtk.main_quit()
            stopload = True

        register_stock_icons()
        
        state = DbState.DbState()
        self.vm = ViewManager.ViewManager(state)
        for view in DataViews.get_views():
            self.vm.register_view(view)

        if stopload:
            # We stop further loading so family tree manager is not shown
            # before the exit of GRAMPS
            return
        
        self.vm.init_interface()

        # Depending on the nature of this session, 
        # we may need to change the order of operation
        ah = ArgHandler.ArgHandler(state, self.vm, args)
        if ah.need_gui():
            retval = ah.handle_args()
            if retval:
                filename, filetype = retval
                self.vm.post_init_interface(show_manager=False)
                self.vm.open_activate(filename)
            else:
                self.vm.post_init_interface()
        else:
            ah.handle_args()
            self.vm.post_init_interface()

        if Config.get(Config.USE_TIPS):
            TipOfDay.TipOfDay(self.vm.uistate)
