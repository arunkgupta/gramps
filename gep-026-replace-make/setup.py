#!/usr/bin/env python

import os, sys, glob

from distutils.core import setup

def os_files():
    # Windows or MacOSX
    if (os.name == 'nt' or os.name == 'darwin'):
        return [
                # application icon
                (os.path.join('share', 'pixmaps'), [os.path.join('gramps', 'images', 'ped24.ico')]),
                (os.path.join('share', 'pixmaps'), [os.path.join('gramps', 'images', 'gramps.png')]),
                (os.path.join('share', 'icons', 'scalable'),
                        glob.glob(os.path.join('gramps', 'images', 'scalable', '*.svg'))),
                (os.path.join('share', 'icons', '16x16'),
                        glob.glob(os.path.join('gramps', 'images', '16x16', '*.png'))),
                (os.path.join('share', 'icons', '22x22'),
                        glob.glob(os.path.join('gramps', 'images', '22x22' ,'*.png'))),
                (os.path.join('share', 'icons', '48x48'),
                        glob.glob(os.path.join('gramps', 'images', '48x48', '*.png'))),
                # doc
                ('share', ['AUTHORS']),
                ('share', ['COPYING']),
                ('share', ['FAQ']),
                ('share', ['INSTALL']),
                ('share', ['LICENSE']),
                ('share', ['NEWS']),
                ('share', ['README']),
                ('share', ['TODO'])
        ]
    else:
        # Linux or FreeBSD
        return [
                # XDG application description
                ('share/applications', ['data/gramps.desktop']),

                # XDG application icon
                ('share/pixmaps', ['gramps/images/gramps.png']),

                # XDG desktop mime types cache
                ('share/mime/packages', ['data/gramps.xml']),

                # mime.types
                ('share/mime-info', ['data/gramps.mime']),
                ('share/mime-info', ['data/gramps.keys']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gedcom.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-geneweb.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gramps.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gramps-package.png']),
                ('share/icons/gnome/48x48/mimetypes', ['data/gnome-mime-application-x-gramps-xml.png']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gedcom.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-geneweb.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gramps.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gramps-package.svg']),
                ('share/icons/gnome/scalable/mimetypes', ['data/gnome-mime-application-x-gramps-xml.svg']),

                # man-page, /!\ should be gramps.1 with variables
                # migration to sphinx/docutils/gettext environment ?
                (os.path.join(MAN_DIR, 'man1'), ['data/man/gramps.1.in']),
                (os.path.join(MAN_DIR, 'cs', 'man1'), ['data/man/cs/gramps.1.in']),
                (os.path.join(MAN_DIR, 'fr', 'man1'), ['data/man/fr/gramps.1.in']),
                (os.path.join(MAN_DIR, 'nl', 'man1'), ['data/man/nl/gramps.1.in']),
                (os.path.join(MAN_DIR, 'pl', 'man1'), ['data/man/pl/gramps.1.in']),
                (os.path.join(MAN_DIR, 'sv', 'man1'), ['data/man/sv/gramps.1.in']),
                # icons 
                ('share/icons/hicolor/scalable/apps', glob.glob('gramps/images/scalable/*.svg')),
                ('share/icons/hicolor/16x16/apps', glob.glob('gramps/images/16x16/*.png')),
                ('share/icons/hicolor/22x22/apps', glob.glob('gramps/images/22x22/*.png')),
                ('share/icons/hicolor/48x48/apps', glob.glob('gramps/images/48x48/*.png')),
                # doc
                ('share/doc/gramps', ['COPYING']),
                ('share/doc/gramps', ['FAQ']),
                ('share/doc/gramps', ['INSTALL']),
                ('share/doc/gramps', ['NEWS']),
                ('share/doc/gramps', ['README']),
                ('share/doc/gramps', ['TODO'])
        ]

def trans_files():
    '''
    List of available compiled translations; ready for installation
    '''
    translation_files = []
    for mo in glob.glob(os.path.join(MO_DIR, '*', 'gramps.mo')):
        lang = os.path.basename(os.path.dirname(mo))
        if os.name == 'posix':
            dest = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
        else :
            dest = os.path.join('locale', lang, 'LC_MESSAGES')
        translation_files.append((dest, [mo]))
    return translation_files

setup(
        name='gramps',
        version='3.5.0',
        description='gramps (Genealogical Research and Analysis Management Programming System)',
        long_description=['gramps (Genealogical Research and Analysis Management Programming',
                'System) is a GNOME based genealogy program supporting a Python based plugin system.'],
        author='Donald N. Allingham',
        author_email='don@gramps-project.org',
        maintainer='Gramps Development Team',
        maintainer_email='benny.malengier@gmail.com',
        url='http://gramps-project.org/',
        download_url='http://gramps-project.org/download/',
        keywords=[
            'Genealogy',
            'Pedigree',
            'Ancestry',
            'Birth',
            'Marriage',
            'Death',
            'Family',
            'Family-tree',
            'GEDCOM',
        ],
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Environment :: MacOS X',
            'Environment :: Plugins',
            'Environment :: Web Environment',
            'Environment :: Win32 (MS Windows)',
            'Environment :: X11 Applications :: GTK',
            'Framework :: Django',
             'Intended Audience :: Education',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: Other Audience',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Natural Language :: Bulgarian',
            'Natural Language :: Catalan',
            'Natural Language :: Chinese (Simplified)',
            'Natural Language :: Croatian',
            'Natural Language :: Czech',
            'Natural Language :: Danish',
            'Natural Language :: Dutch',
            'Natural Language :: English',
            'Natural Language :: Esperanto',
            'Natural Language :: Finnish',
            'Natural Language :: French',
            'Natural Language :: German',
            'Natural Language :: Hebrew',
            'Natural Language :: Hungarian',
            'Natural Language :: Italian',
            'Natural Language :: Japanese',
            'Natural Language :: Norwegian',
            'Natural Language :: Polish',
            'Natural Language :: Portuguese (Brazilian)',
            'Natural Language :: Portuguese',
            'Natural Language :: Russian',
            'Natural Language :: Slovak',
            'Natural Language :: Slovenian',
            'Natural Language :: Spanish',
            'Natural Language :: Swedish',
            'Natural Language :: Ukranian',
            'Natural Language :: Vietnamese',
            'Operating System :: MacOS',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: Other OS',
            'Operating System :: POSIX :: BSD',
            'Operating System :: POSIX :: Linux',
            'Operating System :: POSIX :: SunOS/Solaris',
            'Operating System :: Unix',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Topic :: Database',
            'Topic :: Desktop Environment :: Gnome',
            'Topic :: Education',
            'Topic :: Multimedia',
            'Topic :: Other/Nonlisted Topic',
            'Topic :: Scientific/Engineering :: Visualization',
            'Topic :: Sociology :: Genealogy',
        ],
        platforms=['Linux', 'FreeBSD', 'MacOS', 'Windows'],
        license='GPL v2 or greater',
#        package_dir={'gramps' : 'gramps'},
        packages=['gramps', 'gramps.cli', 'gramps.data', 'gramps.gen', 'gramps.glade',
                  'gramps.gui', 'gramps.images', 'gramps.plugins', 'gramps.webapp'],
        package__data={
            'gramps' : [
                '*.py',
                'DateHandler/*.py',
                'docgen/*.py',
                'Filters/*.py',
                'Filters/*/*.py',
                'Filters/Rules/*/*.py',
                'GrampsLocale/*.py',
                'GrampsLogger/*.py',
                'Merge/*.py',
                'Simple/*.py',
                'TestPlan.txt',
                'test/*.py'],
            'gramps.cli': [
                '*.py',
                'plug/*.py'],
            'gramps.data': [
                '*.txt',
                '*.xml'],
            'gramps.gen': [
                '*.py',
                'db/*.py',
                'display/*.py',
                'lib/*.py',
                'mime/*.py',
                'plug/*.py',
                'plug/*/*.py',
                'proxy/*.py',
                'test/*.py',
                'utils/*.py'],
            'gramps.glade': [
                '*.glade',
                'glade/catalog/*.py',
                'catalog/*.xml'],
            'gramps.gui': [
                '*.py',
                'editors/*.py',
                'editors/*/*.py',
                'plug/*.py',
                'plug/*/*.py',
                'selectors/*.py',
                'views/*.py',
                'views/treemodels/*.py',
                'widgets/*.py'],
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
                '*/*.glade'],
                'gramps.webapp': [
                '*.py',
                'webstuff/css/*.css',
                'webstuff/images/*.svg',
                'webstuff/images/*.png',
                'webstuff/images/*.gif',
                'grampsdb/fixtures/initial_data.json',
                '*/*.py',
                'sqlite.db',
                'grampsdb/*.py',
                'fixtures/initial_data.json',
                'templatetags/*py'],
        },
        scripts=['gramps.sh'],
        extra_files=os_files() + trans_files(),
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
