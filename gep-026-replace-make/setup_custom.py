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

def build_itnl(build_cmd):
    '''
    Post-build hook to run internationisation scripts.
    '''
    import os, glob, subprocess
    print('BUILD')

    def _create_desktop_file():
        '''handles the merging and creation of the gramps desktop file'''

        gramps_desktop    = os.path.join(ROOT_DIR, 'data', 'gramps.desktop')
        gramps_desktop_in = os.path.join('data', 'gramps.desktop.in')
        if not os.path.exists(gramps_desktop):
            sys.stdout.write('Compiling gramps.desktop file...\n')
            os.system('intltool-merge -d po/ %s %s' % (gramps_desktop_in, gramps_desktop))

    def _create_xml_file():
        ''' handles the merging and creation of the gramps.xml file'''

        gramps_xml = os.path.join(ROOT_DIR, 'data', 'gramps.xml')
        gramps_xml_in = os.path.join('data', 'gramps.xml.in')
        if not os.path.exists(gramps_xml):
            sys.stdout.write('Compiling gramps.xml file...\n')
            os.system('intltool-merge -x po/ %s %s\n' % (gramps_xml_in, gramps_xml))

    def _create_keys_file():
        '''handles the merging and creation of the gramps keys file'''

        gramps_keys = os.path.join(ROOT_DIR, 'data', 'gramps.keys')
        gramps_keys_in = os.path.join('data', 'gramps.keys.in')
        if (os.path.exists(gramps_keys_in) and not os.path.exists(gramps_keys)):
            sys.stdout.write('Compiling gramps.keys file...\n')
            os.system('intltool-merge -k po/ %s %s' % (gramps_keys_in, gramps_keys))

    def _create_tips_file():
        '''handles the merging and creation of the gramps tips file'''

        gramps_tips = os.path.join('gramps', 'data', 'tips.xml')
        gramps_tips_in = os.path.join('gramps', 'data', 'tips.xml.in')
        if not os.path.exists(gramps_tips):
            sys.stdout.write('Compiling tips.xml file...\n')
            os.system('intltool-merge -k /po %s %s' % (gramps_tips_in, gramps_tips))

    PO_DIR = os.path.join('po')
    MO_DIR = os.path('build', 'mo')

    for po in glob.glob (os.path.join (PO_DIR, '*.po')):
        lang = os.path.basename(po[:-3])
        mo = os.path.join(MO_DIR, lang, 'gramps.mo')

        directory = os.path.dirname(mo)
        if not os.path.exists(directory):
            sys.stdout.write('creating %s\n' % directory)
            os.makedirs(directory)

        if newer(po, mo):
            sys.stdout.write('compiling %s -> %s\n' % (po, mo))
            try:
                bash_string = 'msgfmt -o %s %s' % (mo, po)
                result = subprocess.call(bash_string, shell=True)
                if result is not 0:
                    sys.exit('msgfmt failed, returning %s\n' % result)
            except Exceptionm, e:
                sys.stdout.write('Building gettext files failed.  Try setup.py --without-gettext [build|install]\n')
                sys.stdout.write('Error: %s\n' % str(e))
                sys.exit(1)

    try:
        # create gramps desktop file
        _create_desktop_file()
    except (IOError, OSError):
        sys.exit('Faileed to create gramps.desktop file...\n')
 
    try:
        # create gramps xml file
        _create_xml_file()
    except (IOError, OSError):
        sys.exit('Faileed to create gramps.xml file...\n')

    try:
        # create gramps keys file
        _create_keys_file()
    except (IOError, OSError):
        sys.exit('Faileed to create gramps.keys file...\n')

    try:
        # create gramps tips file
        _creat_tips_file()
    except (IOError, OSError):
        sys.exit('Faileed to create tips.xml file...\n')

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
