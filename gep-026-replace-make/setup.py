#!/usr/bin/env python

from distutils.core import setup 

setup(
        platforms=['Linux', 'FreeBSD', 'MacOS', 'Windows'],
        license='GPL v2 or greater',
        package_dir={'gramps' : 'gramps'},
        packages=['gramps', 'gramps.cli', 'gramps.data', 'gramps.gen', 'gramps.glade', 'gramps.gui', 'gramps.images', 'gramps.plugins', 'gramps.webapp'],
        package__data={
            'gramps.data': [
                '*.txt',
                '*.xml'],
            'gramps.glade': [
                '*.glade',
                'glade/catalog/*.py',
                'catalog/*.xml'],
            'gramps.images': [
                '*/*.png',
                 '*/*.svg',
                '*.png',
                '*.jpg',
                '*.ico',
                 '*.gif'],
            'gramps.plugins': [
                '*.py',
                '*/*.py',
                'lib/*.xml',
                'lib/maps/*.py',
                'webstuff/css/*.css',
                'webstuff/images/*.svg',
                'webstuff/images/*.png',
                'webstuff/images/*.gif',            
                '*.glade',
                '*/*.glade']
        },
        scripts=['gramps.sh'],
#        extra_files=os_files() + trans_files(),
        requires_dist=['pygtk2', 'pycairo', 'pygobject2'],
        resources=[
            'data/ gramps.desktop = {data}/share/applications',
            'gramps/images/ gramps.png = {data}/share/pixmaps',
            'data/ gramps.xml = {data}/share/mime/packages',
            'data/ gramps.mime = {data}/share/mime-info',
            'data/ gramps.keys = {data}/share/mime-info',
            'data/ gnome-mime-application-x-gedcom.png = {data}/share/icons/gnome/48x48/mimetypes',
            'data/ gnome-mime-application-x-geneweb.png = {data}/share/icons/gnome/48x48/mimetypes',
            'data/ gnome-mime-application-x-gramps.png = {data}/share/icons/gnome/48x48/mimetypes',
            'data/ gnome-mime-application-x-gramps-package.png = {data}/share/icons/gnome/48x48/mimetypes',
            'data/ gnome-mime-application-x-gramps-xml.png = {data}/share/icons/gnome/48x48/mimetypes',
            'data/ gnome-mime-application-x-gedcom.svg = {data}/share/icons/gnome/scalable/mimetypes',
            'data/ gnome-mime-application-x-geneweb.svg = {data}/share/icons/gnome/scalable/mimetypes',
            'data/ gnome-mime-application-x-gramps.svg = {data}/share/icons/gnome/scalable/mimetypes',
            'data/ gnome-mime-application-x-gramps-package.svg = {data}/share/icons/gnome/scalable/mimetypes',
            'data/ gnome-mime-application-x-gramps-xml.svg = {data}/share/icons/gnome/scalable/mimetypes',
            'data/man/ gramps.1.in = {data}/share/man/man1',
            'data/man/cs/ gramps.1.in = {data}/share/man/cs/man1',
            'data/man/fr/ gramps.1.in = {data}/share/man/fr/man1',
            'data/man/nl/ gramps.1.in = {data}/share/man/nl/man1',
            'data/man/pl/ gramps.1.in = {data}/share/man/pl/man1',
            'data/man/sv/ gramps.1.in = {data}/share/man/sv/man1',
            'COPYING = {data}/share/doc/gramps',
            'FAQ = {data}/share/doc/gramps',
            'INSTALL = {data}/share/doc/gramps',
            'NEWS = {data}/share/doc/gramps',
            'README = {data}/share/doc/gramps',
            'TODO = {data}/share/doc/gramps',
        ],
)
