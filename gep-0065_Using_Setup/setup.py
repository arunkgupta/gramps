# Gramps - a GTK+/GNOME based genealogy program
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
# testing a setup.py for Gramps

import os
import shutil

from distutils.core import setup

def main():
    ROOT_DIR = os.getcwd()

    const_file_in = os.path.join(ROOT_DIR, 'gramps', 'const.py.in')
    const_file    = os.path.join(ROOT_DIR, 'gramps', 'const.py')
    if (os.path.exists(const_file_in) and not os.path.exists(const_file)):
        shutil.copy(const_file_in, const_file)

    from gramps.const import VERSION

    setup (
        name             = 'gramps',
        version          = VERSION,
        author           = 'Gramps Development Team',
        author_email     = 'benny.malengier@gmail.com',
        url              = 'http://gramps-project.org/',
        download_url     = 'http://sourceforge.net/projects/gramps/files/Stable/3.3.1/',
        license          = "GPLv2 or greater",
        long_description = ('gramps (Genealogical Research and Analysis Management Programming '
                            'System) is a GNOME based genealogy program supporting a Python based plugin system.'),
        platforms        = ['Linux', 'Mac OS-X', 'Windows'],
    )

if __name__ == '__main__':
    main()
