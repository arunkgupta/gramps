# This is the top level Makefile for Gramps
# $Id$

SUBDIRS = data example gramps linux locale m4

EXTRA_DIST = \
	config.rpath autogen.sh \
        COPYING FAQ INSTALL NEWS README RELEASE_NOTES \
	create_setup_cfg.py setup.cfg setup.py MANIFEST.in \
	intltool-extract.in intltool-merge.in intltool-update.in

bin_SCRIPTS = gramps

dist_pkgdata_DATA = COPYING FAQ INSTALL NEWS README RELEASE_NOTES

distuninstallcheck_listfiles = find . -type -f -print | grep -E -v '/(globs|magic|XMLnamespaces)'

DISTCLEANFILES = intltool-extract intltool-merge intltool-update \
	gnome-doc-utils.make

gramps: gramps.sh

.PHONY: pycheck trans

pycheck:
	(cd src; make pycheck) 
trans:
	(cd src; make trans) 

distuninstallcheck:
	@:

CLEANFILES = gramps

ACLOCAL_AMFLAGS = -I m4
