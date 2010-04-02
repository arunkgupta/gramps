#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2005  Donald N. Allingham
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

"""
Provides the SubstKeywords class that will replace keywords in a passed
string with informatin about the person. For sample:

foo = SubstKeywords(person)
print foo.replace('$n was born on $b.')

Will return a value such as:

Mary Smith was born on 3/28/1923.
"""

__author__ = "Donald N. Allingham"
__version__ = "$Revision$"

#------------------------------------------------------------------------
#
# Gramps modules
#
#------------------------------------------------------------------------

import NameDisplay

#------------------------------------------------------------------------
#
# SubstKeywords
#
#------------------------------------------------------------------------
class SubstKeywords:
    """
    Produces an object that will substitute information about a person
    into a passed string.

    $n -> Name - FirstName LastName
    $N -> Name - LastName, FirstName
    $i -> GRAMPS ID
    $b -> Date of birth
    $B -> Place of birth
    $d -> Date of death
    $D -> Place of death
    $s -> Preferred spouse's name - FirstName LastName
    $S -> Preferred spouse's name - LastName, FirstName
    $m -> Date of preferred marriage
    $M -> Place of preferred marriage
    """
    
    def __init__(self,database,person_handle):
        """Creates a new object and associates a person with it."""

        person = database.get_person_from_handle(person_handle)
        self.n = NameDisplay.displayer.display(person)
        self.N = NameDisplay.displayer.sorted(person)
        self.b = ""
        self.B = ""
        self.d = ""
        self.D = ""
        self.s = ""
        self.S = ""
        self.m = ""
        self.M = ""
        
        birth_handle = person.get_birth_handle()
        if birth_handle:
            birth = database.get_event_from_handle(birth_handle)
            self.b = birth.get_date()
            bplace_handle = birth.get_place_handle()
            if bplace_handle:
                self.B = database.get_place_from_handle(bplace_handle).get_title()
        death_handle = person.get_death_handle()
        if death_handle:
            death = database.get_event_from_handle(death_handle)
            self.d = death.get_date()
            dplace_handle = death.get_place_handle()
            if dplace_handle:
                self.D = database.get_place_from_handle(dplace_handle).get_title()
        self.i = str(person_handle)

        if person.get_family_handle_list():
            f_id = person.get_family_handle_list()[0]
            f = database.get_family_from_handle(f_id)
            father_handle = f.get_father_handle()
            mother_handle = f.get_mother_handle()
            if father_handle == person_handle:
                if mother_handle:
                    mother = database.get_person_from_handle(mother_handle)
                    self.s = NameDisplay.displayer.display(mother)
                    self.S = NameDisplay.displayer.sorted(mother)
            else:
                if father_handle:
                    father = database.get_person_from_handle(father_handle)
                    self.s = NameDisplay.displayer.display(father)
                    self.S = NameDisplay.displayer.sorted(father)
            for e_id in f.get_event_list():
                if not e_id:
                    continue
                e = database.get_event_from_handle(e_id)
                if e.get_name() == 'Marriage':
                    self.m = e.get_date()
                    mplace_handle = e.get_place_handle()
                    if mplace_handle:
                        self.M = database.get_place_from_handle(mplace_handle).get_title()

    def replace(self,line):
        """Returns a new line of text with the substitutions performed."""
        
        line = line.replace("$n",self.n)
        line = line.replace("$N",self.N)
        line = line.replace("$b",self.b)
        line = line.replace("$B",self.B)
        line = line.replace("$d",self.d)
        line = line.replace("$D",self.D)
        line = line.replace("$i",self.i)
        line = line.replace("$S",self.S)
        line = line.replace("$s",self.s)
        line = line.replace("$m",self.m)
        line = line.replace("$M",self.M)
        return line.replace("$$",'$')

    def replace_and_clean(self, lines):
        array = [ ("%n",self.n), ("%N",self.N), ("%b",self.b),
                  ("%B",self.B), ("%d",self.d), ("%D",self.D),
                  ("%i",self.i), ("%S",self.S), ("%s",self.s),
                  ("%m",self.m), ("%M",self.M)]

        new = []
        for line in lines:
            remove = False
            for (key,value) in array:
                if line.find(key) != -1:
                    if value:
                        line = line.replace(key,value)
                    else:
                        remove = True
            if not remove:
                new.append(self.replace(line))
        if len(new) == 0:
            return [ u"" ]
        else:
            return new
            
        
        
