# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2008 - 2009  Douglas S. Blank <doug.blank@gmail.com>
# Copyright (C) 2009         B. Malengier <benny.malengier@gmail.com>
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
# $Id: ExportSql.py 12940 2009-08-10 01:25:34Z dsblank $
#

"""
Export to the Django Models on the configured database backend


"""

#------------------------------------------------------------------------
#
# Standard Python Modules
#
#------------------------------------------------------------------------
import sys
import os
from gettext import gettext as _
from gettext import ngettext
import time

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
log = logging.getLogger(".ExportDjango")

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gen.plug import PluginManager, ExportPlugin
import ExportOptions
from Utils import create_id
import const
import gen.lib

from django.conf import settings
import gen.web.settings as default_settings
try:
    settings.configure(default_settings, DEBUG=True)
except:
    pass

from gen.web.libdjango import DjangoInterface

def export_all(database, filename, option_box=None, callback=None):
    if not callable(callback): 
        callback = lambda (percent): None # dummy

    start = time.time()
    total = (database.get_number_of_notes() + 
             database.get_number_of_people() +
             database.get_number_of_events() + 
             database.get_number_of_families() +
             database.get_number_of_repositories() +
             database.get_number_of_places() +
             database.get_number_of_media_objects() +
             database.get_number_of_sources()) * 2 # steps
    count = 0.0
    dji = DjangoInterface()
    dji.clear_tables("primary", "secondary")

    for step in (0, 1):
        print "Exporting Step %d..." % (step + 1)
        # ---------------------------------
        # Person
        # ---------------------------------
        for person_handle in database.person_map.keys():
            data = database.person_map[person_handle]
            if step == 0:
                dji.add_person(data)
            elif step == 1:
                dji.add_person_detail(data)
            count += 1
            callback(100 * count/total)

        # ---------------------------------
        # Notes
        # ---------------------------------
        for note_handle in database.note_map.keys():
            data = database.note_map[note_handle]
            if step == 0:
                dji.add_note(data)
            count += 1
            callback(100 * count/total)

        # ---------------------------------
        # Family
        # ---------------------------------
        for family_handle in database.family_map.keys():
            data = database.family_map[family_handle]
            if step == 0:
                dji.add_family(data)
            elif step == 1:
                dji.add_family_detail(data)
            count += 1
            callback(100 * count/total)

        # ---------------------------------
        # Source
        # ---------------------------------
        for source_handle in database.source_map.keys():
            data = database.source_map[source_handle]
            if step == 0:
                dji.add_source(data)
            elif step == 1:
                dji.add_source_detail(data)
            count += 1
            callback(100 * count/total)

        # ---------------------------------
        # Event
        # ---------------------------------
        for event_handle in database.event_map.keys():
            data = database.event_map[event_handle]
            if step == 0:
                dji.add_event(data)
            elif step == 1:
                dji.add_event_detail(data)
            count += 1
            callback(100 * count/total)

        # ---------------------------------
        # Repository
        # ---------------------------------
        for repository_handle in database.repository_map.keys():
            data = database.repository_map[repository_handle]
            if step == 0:
                dji.add_repository(data)
            elif step == 1:
                dji.add_repository_detail(data)
            count += 1
            callback(100 * count/total)
    
        # ---------------------------------
        # Place 
        # ---------------------------------
        for place_handle in database.place_map.keys():
            data = database.place_map[place_handle]
            if step == 0:
                dji.add_place(data)
            elif step == 1:
                dji.add_place_detail(data)
            count += 1
            callback(100 * count/total)
    
        # ---------------------------------
        # Media
        # ---------------------------------
        for media_handle in database.media_map.keys():
            data = database.media_map[media_handle]
            if step == 0:
                dji.add_media(data)
            elif step == 1:
                dji.add_media_detail(data)
            count += 1
            callback(100 * count/total)

    total_time = time.time() - start
    msg = ngettext('Export Complete: %d second','Export Complete: %d seconds', total_time ) % total_time
    print msg
    return True

# Future ideas
# Also include meta:
#   Bookmarks
#   Header - researcher info
#   Name formats
#   Namemaps?
#   GRAMPS Version #, date, exporter

#-------------------------------------------------------------------------
#
# Register the plugin
#
#-------------------------------------------------------------------------

class NoFilenameOptions(ExportOptions.WriterOptionBox):
    no_fileselect = True

_name = _('Django Export')
_description = _('Django is a web framework working on a configured database')
_config = (_('Django options'), NoFilenameOptions)

pmgr = PluginManager.get_instance()
plugin = ExportPlugin(name            = _name, 
                      description     = _description,
                      export_function = export_all,
                      extension       = "django",
                      config          = _config )
pmgr.register_plugin(plugin)
