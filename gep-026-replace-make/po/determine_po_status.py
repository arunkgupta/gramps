#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2012 Rob G. Healey <robhealey1@gmail.com>
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

#------------------------------------------------
#        Python modules
#------------------------------------------------
import os, glob, commands

from fractions import Fraction

def determine_po_status(po_file, lang):
    '''
    determines if a po file is to be compiled or not?
    '''
    retcode, answer = commands.getstatusoutput('./check_po -s %s | grep "Localized at: "' % po_file)
    if retcode != 0:
        raise SystemExi('ERROR: Processing of translations files failed.')

    pos = answer.find('%')
    if pos != -1:
        value = answer[pos-6:pos]
        displayed = answer[pos-6:pos+1]
        percent = int(Fraction(value))
        print('%s = %s ' % (lang, displayed))

        if percent >= 48:
            return True
    else:
        raise SystemExi('ERROR: Processing of translations files failed.')
    return False

def main():
    ALL_LINGUAS = []

    for po in sorted(glob.glob('*.po')):
        lang = os.path.basename(po)[:-3]

        if determine_po_status(po, lang):
            ALL_LINGUAS.append(lang)
    print('ALL_LINGUAS = %s' % ALL_LINGUAS)

if __name__ == "__main__":
	main()


