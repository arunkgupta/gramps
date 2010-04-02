# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2003-2005  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
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

# Written by Alex Roitman, largely based on Relationship.py by Don Allingham
# and on valuable input from Lars Kr. Lundin

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------

import gen.lib
import Relationship
import types
from gen.plug import PluginManager

#-------------------------------------------------------------------------
#
# Danish-specific definitions of relationships
#
#-------------------------------------------------------------------------

_level_name = [ "", "første", "anden", "tredje", "fjerde", "femte", "sjette",
                "syvende", "ottende", "niende", "tiende", "ellevte", "tolvte",
                "trettende", "fjortende", "femtende", "sekstende",
                "syttende", "attende", "nittende", "tyvende", "enogtyvende", "toogtyvende",
                "treogtyvende","fireogtyvende","femogtyvende","seksogtyvende",
                "syvogtyvende","otteogtyvende","niogtyvende","tredivte", ]

_parents_level = [ "forældre", "bedsteforældre", "oldeforældre",
                   "tipoldeforældre", "tiptipoldeforældre" , "tiptiptipoldeforældre", ]

_father_level = [ "", "faderen", "bedstefaderen", "oldefaderen", "tipoldefaderen", ]

_mother_level = [ "", "moderen", "bedstemoderen", "oldemoderen", "tipoldemoderen", ]

_son_level = [ "", "sønnen", "barnebarnet", "oldebarnet", ]

_daughter_level = [ "", "datteren", "barnebarnet", "oldebarnet", ]

_sister_level = [ "", "søsteren", "tanten", "grandtanten", "oldetanten", ]

_brother_level = [ "", "broderen", "onklen", "grandonklen", "oldeonkel", ]

_nephew_level = [ "", "nevøen", "næstsøskendebarnet", "broderens barnebarn", ]

_niece_level = [ "", "niecen", "næstsøskendebarnet", "søsterens barnebarn", ]



#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class RelationshipCalculator(Relationship.RelationshipCalculator):

    def __init__(self):
        Relationship.RelationshipCalculator.__init__(self)

    def get_parents(self,level):
        if level>len(_parents_level)-1:
            #return "fjern forfader"
            #Instead of "remote ancestors" using "tip (level) oldeforældre" here.
            return "tip (%d) oldeforældre" % level
        else:
            return _parents_level[level]

    def pair_up(self,rel_list):
        result = []
        item = ""
        for word in rel_list[:]:
            if not word:
                continue
            if item:
                if word == 'søster':
                    item = item[0:-1]
                    word = 'ster'
                elif word == 'sønne':
                    word = 'søn'
                result.append(item + word)
                item = ""
            else:
                item = word
        if item:
            result.append(item)
        gen_result = [ item + 's' for item in result[0:-1] ]
        return ' '.join(gen_result+result[-1:])

    def get_direct_ancestor(self,person,rel_string):
        result = []
        for ix in range(len(rel_string)):
            if rel_string[ix] == 'f':
                result.append('far')
            else:
                result.append('mor')
        return self.pair_up(result)

    def get_direct_descendant(self,person,rel_string):
        result = []
        for ix in range(len(rel_string)-2,-1,-1):
            if rel_string[ix] == 'f':
                result.append('sønne')
            else:
                result.append('datter')
        if person.get_gender() == gen.lib.Person.MALE:
            result.append('søn')
        else:
            result.append('datter')
        return self.pair_up(result)

    def get_two_way_rel(self,person,first_rel_string,second_rel_string):
        result = []
        for ix in range(len(second_rel_string)-1):
            if second_rel_string[ix] == 'f':
                result.append('far')
            else:
                result.append('mor')
        if len(first_rel_string)>1:
            if first_rel_string[-2] == 'f':
                result.append('bror')
            else:
                result.append('søster')
            for ix in range(len(first_rel_string)-3,-1,-1):
                if first_rel_string[ix] == 'f':
                    result.append('sønne')
                else:
                    result.append('datter')
            if person.get_gender() == gen.lib.Person.MALE:
                result.append('søn')
            else:
                result.append('datter')
        else:
            if person.get_gender() == gen.lib.Person.MALE:
                result.append('bror')
            else:
                result.append('søster')
        return self.pair_up(result)

    def get_relationship(self,db, orig_person, other_person):
        """
        Return a string representing the relationshp between the two people,
        along with a list of common ancestors (typically father,mother) 
    
        Special cases: relation strings "", "undefined" and "spouse".
        """

        if orig_person is None:
            return ("undefined",[])
    
        if orig_person.get_handle() == other_person.get_handle():
            return ('', [])

        is_spouse = self.is_spouse(db, orig_person, other_person)
        if is_spouse:
            return (is_spouse,[])

        #get_relationship_distance changed, first data is relation to 
        #orig person, apperently secondRel in this function
        (secondRel,firstRel,common) = \
                     self.get_relationship_distance(db, orig_person, other_person)

        if isinstance(common, basestring):
            return (common,[])
        elif common:
            person_handle = common[0]
        else:
            return ("",[])

        if not firstRel:
            if not secondRel:
                return ('',common)
            else:
                return (self.get_direct_ancestor(other_person,secondRel),common)
        elif not secondRel:
            return (self.get_direct_descendant(other_person,firstRel),common)
        else:
            return (self.get_two_way_rel(other_person,firstRel,secondRel),common)

#-------------------------------------------------------------------------
#
# Register this class with the Plugins system 
#
#-------------------------------------------------------------------------
pmgr = PluginManager.get_instance()
pmgr.register_relcalc(RelationshipCalculator,
    [ "da", "DA", "da_DK", "danish", "Danish", "da_DK.UTF8",
      "da_DK@euro", "da_DK.UTF8@euro", "dansk", "Dansk",
      "da_DK.UTF-8", "da_DK.utf-8", "da_DK.utf8",
      "da_DK.ISO-8859-1","da_DK.iso-8859-1","da_DK.iso88591" ])
