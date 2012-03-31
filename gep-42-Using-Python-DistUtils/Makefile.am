# This is the top level Makefile for Gramps
# $Id$

SUBDIRS = data example gramps locale m4

EXTRA_DIST = \
	AUTHORS COPYING FAQ LICENSE NEWS README RELEASE_NOTES TODO \
	.intltool-extract .intltool-merge .intltool-update

bin_SCRIPTS = gramps.sh

dist_pkgdata_DATA = AUTHORS COPYING FAQ LICENSE README

distuninstallcheck_listfiles = find . -type -f -print | grep -E -v '/(globs|magic|XMLnamespaces)'

DISTCLEANFILES = gnome-doc-utils.make

gramps: gramps.sh

.PHONY: pycheck trans

pycheck:
	(cd gramps; make pycheck) 
trans:
	(cd gramps; make trans) 

distuninstallcheck:
	@:

CLEANFILES = gramps

ACLOCAL_AMFLAGS = -I m4
