#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2012
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

def customize_config(metadata):
    '''
    Global hook.
    '''
    print('GLOBAL')

def build_intl(build_cmd):
    '''
    Post-build hook to run internationisation scripts.
    '''
    print('BUILD')
    
def install_template(install_cmd):
    '''
    Pre-install hook to populate template files.
    '''
    print('INSTALL', install_cmd.install_dir)

def manifest_builder(distribution, manifest):
    '''
    Manifest builder.
    '''
    print("manifest_builder", manifest.files)
