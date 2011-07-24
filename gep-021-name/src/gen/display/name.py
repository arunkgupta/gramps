#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2007  Donald N. Allingham
# Copyright (C) 2010       Brian G. Matherly
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

# $Id:_NameDisplay.py 9912 2008-01-22 09:17:46Z acraphae $

"""
Class handling language-specific displaying of names.

Specific symbols for parts of a name are defined:
    't' : title
    'f' : given (first names)
    'l' : full surname (lastname)
    'c' : callname
    'x' : callname if existing, otherwise first first name (common name)
    'i' : initials of the first names
    'y' : patronymic surname (father)
    'o' : surnames without patronymic 
    'm' : primary surname (main)
    'p' : list of all prefixes
    'q' : surnames without prefixes and connectors
    's' : suffix
    'n' : nick name
    'g' : family nick name
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import sgettext as _
import re

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib import Name, NameOriginType

try:
    import config
    WITH_GRAMPS_CONFIG=True
except ImportError:
    WITH_GRAMPS_CONFIG=False
    

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
_FIRSTNAME    = 4
_SURNAME_LIST = 5
_SUFFIX       = 6
_TITLE        = 7
_TYPE         = 8
_GROUP        = 9
_SORT         = 10
_DISPLAY      = 11
_CALL         = 12
_NICK         = 13
_FAMNICK      = 14
_SURNAME_IN_LIST   = 0
_PREFIX_IN_LIST    = 1
_PRIMARY_IN_LIST   = 2
_TYPE_IN_LIST      = 3
_CONNECTOR_IN_LIST = 4
_ORIGINPATRO = NameOriginType.PATRONYMIC

_ACT = True
_INA = False

_F_NAME = 0  # name of the format
_F_FMT = 1   # the format string
_F_ACT = 2   # if the format is active
_F_FN = 3    # name format function
_F_RAWFN = 4 # name format raw function

#-------------------------------------------------------------------------
#
# Local functions
#
#-------------------------------------------------------------------------
# Because of occurring in an exec(), this couldn't be in a lambda:
# we sort names first on longest first, then last letter first, this to 
# avoid translations of shorter terms which appear in longer ones, eg
# namelast may not be mistaken with name, so namelast must first be 
# converted to %k before name is converted. 
def _make_cmp(a, b): return -cmp((len(a[1]),a[1]), (len(b[1]), b[1]))

#-------------------------------------------------------------------------
#
# NameDisplayError class
#
#-------------------------------------------------------------------------
class NameDisplayError(Exception):
    """
    Error used to report that the name display format string is invalid.
    """
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return self.value

#-------------------------------------------------------------------------
#
# Functions to extract data from raw lists (unserialized objects)
#
#-------------------------------------------------------------------------
    
def _raw_full_surname(raw_surn_data_list):
    """method for the 'l' symbol: full surnames"""
    result = ""
    for raw_surn_data in raw_surn_data_list:
        result += "%s %s %s " % (raw_surn_data[_PREFIX_IN_LIST],
                                 raw_surn_data[_SURNAME_IN_LIST],
                                 raw_surn_data[_CONNECTOR_IN_LIST])
    return ' '.join(result.split()).strip()

def _raw_primary_surname(raw_surn_data_list):
    """method for the 'm' symbol: primary surname"""
    for raw_surn_data in raw_surn_data_list:
        if raw_surn_data[_PRIMARY_IN_LIST]:
            result = "%s %s" % (raw_surn_data[_PREFIX_IN_LIST],
                                raw_surn_data[_SURNAME_IN_LIST])
            return ' '.join(result.split())
    return ''

def _raw_patro_surname(raw_surn_data_list):
    """method for the 'y' symbol: patronymic surname"""
    for raw_surn_data in raw_surn_data_list:
        if raw_surn_data[_TYPE_IN_LIST][0] == _ORIGINPATRO:
            result = "%s %s" % (raw_surn_data[_PREFIX_IN_LIST],
                                raw_surn_data[_SURNAME_IN_LIST])
            return ' '.join(result.split())
    return '' 

def _raw_nonpatro_surname(raw_surn_data_list):
    """method for the 'o' symbol: full surnames without patronymic"""
    result = ""
    for raw_surn_data in raw_surn_data_list:
        if raw_surn_data[_TYPE_IN_LIST][0] != _ORIGINPATRO:
            result += "%s %s %s " % (raw_surn_data[_PREFIX_IN_LIST],
                                    raw_surn_data[_SURNAME_IN_LIST],
                                    raw_surn_data[_CONNECTOR_IN_LIST])
    return ' '.join(result.split()).strip()

def _raw_prefix_surname(raw_surn_data_list):
    """method for the 'p' symbol: all prefixes"""
    result = ""
    for raw_surn_data in raw_surn_data_list:
        result += "%s " % (raw_surn_data[_PREFIX_IN_LIST])
    return ' '.join(result.split()).strip()

def _raw_single_surname(raw_surn_data_list):
    """method for the 'q' symbol: surnames without prefix and connectors"""
    result = ""
    for raw_surn_data in raw_surn_data_list:
        result += "%s " % (raw_surn_data[_SURNAME_IN_LIST])
    return ' '.join(result.split()).strip()

#-------------------------------------------------------------------------
#
# NameDisplay class
#
#-------------------------------------------------------------------------
class NameDisplay(object):
    """
    Base class for displaying of Name instances.
    """

    format_funcs = {}
    raw_format_funcs = {}

    STANDARD_FORMATS = [
        (Name.DEF,_("Default format (defined by Gramps preferences)"),'',_ACT),
        (Name.LNFN,_("Surname, Given"),'%l, %f %s',_ACT),
        (Name.FN,_("Given"),'%f',_ACT),
        (Name.FNLN,_("Given Surname"),'%f %l %s',_ACT),
        # DEPRECATED FORMATS
        (Name.PTFN,_("Patronymic, Given"),'%y, %s %f',_INA),
    ]
    
    def __init__(self):
        global WITH_GRAMP_CONFIG
        self.name_formats = {}
        self.set_name_format(self.STANDARD_FORMATS)
        
        if WITH_GRAMPS_CONFIG:
            self.default_format = config.get('preferences.name-format')
            if self.default_format == 0 \
                    or self.default_format not in Name.NAMEFORMATS :
                self.default_format = Name.LNFN
                config.set('preferences.name-format', self.default_format)
        else:
            self.default_format = Name.LNFN
            
        self.set_default_format(self.default_format)

    def _format_fn(self, fmt_str):
        return lambda x: self.format_str(x, fmt_str)
    
    def _format_raw_fn(self, fmt_str):
        return lambda x: self.format_str_raw(x, fmt_str)

    def _raw_lnfn(self, raw_data):
        result =  "%s, %s %s" % (_raw_full_surname(raw_data[_SURNAME_LIST]),
                                 raw_data[_FIRSTNAME],
                                 raw_data[_SUFFIX])
        return ' '.join(result.split())

    def _raw_fnln(self, raw_data):
        result = "%s %s %s" % (raw_data[_FIRSTNAME],
                               _raw_full_surname(raw_data[_SURNAME_LIST]),
                               raw_data[_SUFFIX])
        return ' '.join(result.split())

    def _raw_fn(self, raw_data):
        result = raw_data[_FIRSTNAME]        
        return ' '.join(result.split())

    def set_name_format(self, formats):
        raw_func_dict = {
            Name.LNFN : self._raw_lnfn,
            Name.FNLN : self._raw_fnln,
            Name.FN   : self._raw_fn,
            }

        for (num, name, fmt_str, act) in formats:
            func = self._format_fn(fmt_str)
            func_raw = raw_func_dict.get(num)
            if func_raw is None:
                func_raw = self._format_raw_fn(fmt_str)
            self.name_formats[num] = (name, fmt_str, act, func, func_raw)

    def add_name_format(self, name, fmt_str):
        num = -1
        while num in self.name_formats:
            num -= 1
        self.set_name_format([(num, name, fmt_str,_ACT)])
        return num
    
    def edit_name_format(self, num, name, fmt_str):
        self.set_name_format([(num, name, fmt_str,_ACT)])
        if self.default_format == num:
            self.set_default_format(num)
        
    def del_name_format(self, num):
        try:
            del self.name_formats[num]
        except:
            pass
        
    def set_default_format(self, num):
        if num not in self.name_formats:
            num = Name.LNFN
            
        self.default_format = num
        
        self.name_formats[Name.DEF] = (self.name_formats[Name.DEF][_F_NAME],
                                       self.name_formats[Name.DEF][_F_FMT],
                                       self.name_formats[Name.DEF][_F_ACT],
                                       self.name_formats[num][_F_FN],
                                       self.name_formats[num][_F_RAWFN])
    
    def get_default_format(self):
        return self.default_format

    def set_format_inactive(self, num):
        try:
            self.name_formats[num] = (self.name_formats[num][_F_NAME],
                                      self.name_formats[num][_F_FMT],
                                      _INA,
                                      self.name_formats[num][_F_FN],
                                      self.name_formats[num][_F_RAWFN])
        except:
            pass
        
    def get_name_format(self, also_default=False,
                        only_custom=False,
                        only_active=True):
        """
        Get a list of tuples (num, name,fmt_str,act)
        """
        the_list = []

        keys = sorted(self.name_formats, self._sort_name_format) 
        
        for num in keys:
            if ((also_default or num) and
                (not only_custom or (num < 0)) and
                (not only_active or self.name_formats[num][_F_ACT])):
                the_list.append((num,) + self.name_formats[num][_F_NAME:_F_FN])

        return the_list

    def _sort_name_format(self, x, y):
        if x < 0:
            if y < 0: 
                return x+y
            else: 
                return -x+y
        else:
            if y < 0: 
                return -x+y
            else: 
                return x-y
        
    def _is_format_valid(self, num):
        try:
            if not self.name_formats[num][_F_ACT]:
                num = 0
        except:
            num = 0    
        return num

    #-------------------------------------------------------------------------


    def _gen_raw_func(self, format_str):
        """The job of building the name from a format string is rather
        expensive and it is called lots and lots of times. So it is worth
        going to some length to optimise it as much as possible. 

        This method constructs a new function that is specifically written 
        to format a name given a particular format string. This is worthwhile
        because the format string itself rarely changes, so by caching the new
        function and calling it directly when asked to format a name to the
        same format string again we can be as quick as possible.

        The new function is of the form:

        def fn(raw_data):
            return "%s %s %s" % (raw_data[_TITLE],
                   raw_data[_FIRSTNAME],
                   raw_data[_SUFFIX])

        Specific symbols for parts of a name are defined (keywords given):
        't' : title      = title
        'f' : given      = given (first names)
        'l' : surname    = full surname (lastname)
        'c' : call       = callname
        'x' : common     = callname if existing, otherwise first first name (common name)
        'i' : initials   = initials of the first names
        'y' : patronymic = patronymic surname (father)
        'o' : notpatronymic = surnames without patronymic 
        'm' : primary    = primary surname (main)
        'p' : prefix     = list of all prefixes
        'q' : rawsurnames = surnames without prefixes and connectors
        's' : suffix     = suffix
        'n' : nickname   = nick name
        'g' : familynick = family nick name

        """

        # we need the names of each of the variables or methods that are
        # called to fill in each format flag.
        # Dictionary is "code": ("expression", "keyword", "i18n-keyword")
        d = {"t": ("raw_data[_TITLE]",     "title",      
                                _("Person|title")),
             "f": ("raw_data[_FIRSTNAME]", "given",      
                                _("given")),
             "l": ("_raw_full_surname(raw_data[_SURNAME_LIST])",   "surname",
                                _("surname")),
             "s": ("raw_data[_SUFFIX]",    "suffix",     
                                _("suffix")),
             "c": ("raw_data[_CALL]",      "call",       
                                _("Name|call")),
             "x": ("(raw_data[_CALL] or raw_data[_FIRSTNAME].split(' ')[0])",
                                "common",
                                _("Name|common")),
             "i": ("''.join([word[0] +'.' for word in ('. ' +" +
                   " raw_data[_FIRSTNAME]).split()][1:])",
                                "initials",
                                _("initials")),
             "y": ("_raw_patro_surname(raw_data[_SURNAME_LIST])", "patronymic",     
                                _("patronymic")),
             "o": ("_raw_nonpatro_surname(raw_data[_SURNAME_LIST])", "notpatronymic",     
                                _("notpatronymic")),
             "m": ("_raw_primary_surname(raw_data[_SURNAME_LIST])", 
                                "primary",     
                                _("Name|primary")),
             "p": ("_raw_prefix_surname(raw_data[_SURNAME_LIST])", 
                                "prefix",     
                                _("prefix")),
             "q": ("_raw_single_surname(raw_data[_SURNAME_LIST])", 
                                "rawsurnames",     
                                _("rawsurnames")),
             "n": ("raw_data[_NICK]",      "nickname",       
                                _("nickname")),
             "g": ("raw_data[_FAMNICK]",      "familynick",       
                                _("familynick")),
             }
        args = "raw_data"
        return self._make_fn(format_str, d, args)

    def _gen_cooked_func(self, format_str):
        """The job of building the name from a format string is rather
        expensive and it is called lots and lots of times. So it is worth
        going to some length to optimise it as much as possible. 

        This method constructs a new function that is specifically written 
        to format a name given a particular format string. This is worthwhile
        because the format string itself rarely changes, so by caching the new
        function and calling it directly when asked to format a name to the
        same format string again we can be as quick as possible.

        The new function is of the form:

        def fn(first, raw_surname_list, suffix, title, call,):
            return "%s %s" % (first,suffix)
        
        Specific symbols for parts of a name are defined (keywords given):
        't' : title      = title
        'f' : given      = given (first names)
        'l' : surname    = full surname (lastname)
        'c' : call       = callname
        'x' : common     = callname if existing, otherwise first first name (common name)
        'i' : initials   = initials of the first names
        'y' : patronymic = patronymic surname (father)
        'o' : notpatronymic = surnames without patronymic 
        'm' : primary    = primary surname (main)
        'p' : prefix     = list of all prefixes
        'q' : rawsurnames = surnames without prefixes and connectors
        's' : suffix     = suffix
        'n' : nickname   = nick name
        'g' : familynick = family nick name

        """

        # we need the names of each of the variables or methods that are
        # called to fill in each format flag.
        # Dictionary is "code": ("expression", "keyword", "i18n-keyword")
        d = {"t": ("title",      "title",      
                        _("Person|title")),
             "f": ("first",      "given",      
                        _("given")),
             "l": ("_raw_full_surname(raw_surname_list)",   "surname",
                        _("surname")),
             "s": ("suffix",     "suffix",     
                        _("suffix")),
             "c": ("call",       "call",       
                        _("Name|call")),
             "x": ("(call or first.split(' ')[0])", "common", 
                        _("Name|common")),
             "i": ("''.join([word[0] +'.' for word in ('. ' + first).split()][1:])",
                        "initials", 
                        _("initials")),
             "y": ("_raw_patro_surname(raw_surname_list)", "patronymic",     
                        _("patronymic")),
             "o": ("_raw_nonpatro_surname(raw_surname_list)", "notpatronymic",     
                        _("notpatronymic")),
             "m": ("_raw_primary_surname(raw_surname_list)", "primary",     
                        _("Name|primary")),
             "p": ("_raw_prefix_surname(raw_surname_list)", "prefix",     
                        _("prefix")),
             "q": ("_raw_single_surname(raw_surname_list)", "rawsurnames",     
                        _("rawsurnames")),
             "n": ("nick",       "nickname",       
                        _("nickname")),
             "g": ("famnick",    "familynick",       
                        _("familynick")),
             }
        args = "first,raw_surname_list,suffix,title,call,nick,famnick"
        return self._make_fn(format_str, d, args)

    def _make_fn(self, format_str, d, args):
        """
        Create the name display function and handles dependent
        punctuation.
        """
        # d is a dict: dict[code] = (expr, word, translated word)

        # First, go through and do internationalization-based
        # key-word replacement. Just replace ikeywords with
        # %codes (ie, replace "irstnamefay" with "%f", and
        # "IRSTNAMEFAY" for %F)

        if (len(format_str) > 2 and 
            format_str[0] == format_str[-1] == '"'):
            pass
        else:
            d_keys = [(code, _tuple[2]) for code, _tuple in d.iteritems()]
            d_keys.sort(_make_cmp) # reverse on length and by ikeyword
            for (code, ikeyword) in d_keys:
                exp, keyword, ikeyword = d[code]
                #ikeyword = unicode(ikeyword, "utf8")
                format_str = format_str.replace(ikeyword, "%"+ code)
                format_str = format_str.replace(ikeyword.title(), "%"+ code)
                format_str = format_str.replace(ikeyword.upper(), "%"+ code.upper())
        # Next, go through and do key-word replacement.
        # Just replace keywords with
        # %codes (ie, replace "firstname" with "%f", and
        # "FIRSTNAME" for %F)
        if (len(format_str) > 2 and 
            format_str[0] == format_str[-1] == '"'):
            pass
        else:
            d_keys = [(code, _tuple[1]) for code, _tuple in d.iteritems()]
            d_keys.sort(_make_cmp) # reverse sort on length and by keyword
            # if in double quotes, just use % codes
            for (code, keyword) in d_keys:
                exp, keyword, ikeyword = d[code]
                keyword = unicode(keyword, "utf8")
                format_str = format_str.replace(keyword, "%"+ code)
                format_str = format_str.replace(keyword.title(), "%"+ code)
                format_str = format_str.replace(keyword.upper(), "%"+ code.upper())
        # Get lower and upper versions of codes:
        codes = d.keys() + [c.upper() for c in d]
        # Next, list out the matching patterns:
        # If it starts with "!" however, treat the punctuation verbatim:
        if len(format_str) > 0 and format_str[0] == "!":
            patterns = ["%(" + ("|".join(codes)) + ")",          # %s
                        ]
            format_str = format_str[1:]
        else:
            patterns = [
                ",\W*\"%(" + ("|".join(codes)) + ")\"",  # ,\W*"%s"
                ",\W*\(%(" + ("|".join(codes)) + ")\)",  # ,\W*(%s)
                ",\W*%(" + ("|".join(codes)) + ")",      # ,\W*%s
                "\"%(" + ("|".join(codes)) + ")\"",      # "%s"
                "_%(" + ("|".join(codes)) + ")_",        # _%s_
                "\(%(" + ("|".join(codes)) + ")\)",      # (%s)
                "%(" + ("|".join(codes)) + ")",          # %s
                ]
        new_fmt = format_str

        # replace the specific format string flags with a 
        # flag that works in standard python format strings.
        new_fmt = re.sub("|".join(patterns), "%s", new_fmt)

        # find each format flag in the original format string
        # for each one we find the variable name that is needed to 
        # replace it and add this to a list. This list will be used to
        # generate the replacement tuple.

        # This compiled pattern should match all of the format codes.
        pat = re.compile("|".join(patterns))
        param = ()
        mat = pat.search(format_str)
        while mat:
            match_pattern = mat.group(0) # the matching pattern
            # prefix, code, suffix:
            p, code, s = re.split("%(.)", match_pattern)
            field = d[code.lower()][0]
            if code.isupper():
                field += ".upper()"
            if p == '' and s == '':
                param = param + (field,)
            else:
                param = param + ("ifNotEmpty(%s,'%s','%s')" % (field, p, s), )
            mat = pat.search(format_str, mat.end())
        s = """
def fn(%s):
    def ifNotEmpty(str,p,s):
        if str == '':
            return ''
        else:
            return p + str + s
    return "%s" %% (%s)""" % (args, new_fmt, ",".join(param))
        exec(s)

        return fn

    def format_str(self, name, format_str):
        return self._format_str_base(name.first_name, name.surname_list,
                                     name.suffix, name.title,
                                     name.call, name.nick, name.famnick,
                                     format_str)

    def format_str_raw(self, raw_data, format_str):
        """
        Format a name from the raw name list. To make this as fast as possible
        this uses _gen_raw_func to generate a new method for each new format_string.
        
        Is does not call _format_str_base because it would introduce an extra 
        method call and we need all the speed we can squeeze out of this.
        """
        func = self.__class__.raw_format_funcs.get(format_str)
        if func is None:
            func = self._gen_raw_func(format_str)
            self.__class__.raw_format_funcs[format_str] = func

        s = func(raw_data)
        return ' '.join(s.split())


    def _format_str_base(self, first, surname_list, suffix, title, call,
                         nick, famnick, format_str):
        """
        Generates name from a format string.

        The following substitutions are made:
        '%t' : title
        '%f' : given (first names)
        '%l' : full surname (lastname)
        '%c' : callname
        '%x' : callname if existing, otherwise first first name (common name)
        '%i' : initials of the first names
        '%y' : patronymic surname (father)
        '%o' : surnames without patronymic 
        '%m' : primary surname (main)
        '%p' : list of all prefixes
        '%q' : surnames without prefixes and connectors
        '%s' : suffix
        '%n' : nick name
        '%g' : family nick name
       The capital letters are substituted for capitalized name components.
        The %% is substituted with the single % character.
        All the other characters in the fmt_str are unaffected.
        """
        func = self.__class__.format_funcs.get(format_str)
        if func is None:
            func = self._gen_cooked_func(format_str)
            self.__class__.format_funcs[format_str] = func
        try:
            s = func(first, [surn.serialize() for surn in surname_list],
                     suffix, title, call, nick, famnick)
        except (ValueError, TypeError,):
            raise NameDisplayError, "Incomplete format string"

        return ' '.join(s.split())
    
    #-------------------------------------------------------------------------

    def sort_string(self, name):
        return u"%-25s%-30s%s" % (name.get_primary_surname, name.first_name, 
                                  name.suffix)

    def sorted(self, person):
        """
        Return a text string representing the L{gen.lib.Person} instance's
        L{Name} in a manner that should be used for displaying a sorted
        name.

        @param person: L{gen.lib.Person} instance that contains the
        L{Name} that is to be displayed. The primary name is used for
        the display.
        @type person: L{gen.lib.Person}
        @returns: Returns the L{gen.lib.Person} instance's name
        @rtype: str
        """
        name = person.get_primary_name()
        return self.sorted_name(name)

    def sorted_name(self, name):
        """
        Return a text string representing the L{Name} instance
        in a manner that should be used for displaying a sorted
        name.

        @param name: L{Name} instance that is to be displayed.
        @type name: L{Name}
        @returns: Returns the L{Name} string representation
        @rtype: str
        """
        num = self._is_format_valid(name.sort_as)
        return self.name_formats[num][_F_FN](name)

    def raw_sorted_name(self, raw_data):
        """
        Return a text string representing the L{Name} instance
        in a manner that should be used for displaying a sorted
        name.

        @param name: L{Name} instance that is to be displayed.
        @type name: L{Name}
        @returns: Returns the L{Name} string representation
        @rtype: str
        """
        num = self._is_format_valid(raw_data[_SORT])
        return self.name_formats[num][_F_RAWFN](raw_data)

    def display(self, person):
        """
        Return a text string representing the L{gen.lib.Person} instance's
        L{Name} in a manner that should be used for normal displaying.

        @param person: L{gen.lib.Person} instance that contains the
        L{Name} that is to be displayed. The primary name is used for
        the display.
        @type person: L{gen.lib.Person}
        @returns: Returns the L{gen.lib.Person} instance's name
        @rtype: str
        """
        name = person.get_primary_name()
        return self.display_name(name)

    def display_formal(self, person):
        """
        Return a text string representing the L{gen.lib.Person} instance's
        L{Name} in a manner that should be used for formal displaying.

        @param person: L{gen.lib.Person} instance that contains the
        L{Name} that is to be displayed. The primary name is used for
        the display.
        @type person: L{gen.lib.Person}
        @returns: Returns the L{gen.lib.Person} instance's name
        @rtype: str
        """
        # FIXME: At this time, this is just duplicating display() method
        name = person.get_primary_name()
        return self.display_name(name)

    def display_name(self, name):
        """
        Return a text string representing the L{Name} instance
        in a manner that should be used for normal displaying.

        @param name: L{Name} instance that is to be displayed.
        @type name: L{Name}
        @returns: Returns the L{Name} string representation
        @rtype: str
        """
        if name is None:
            return ""

        num = self._is_format_valid(name.display_as)
        return self.name_formats[num][_F_FN](name)

    def display_given(self, person):
        return self.format_str(person.get_primary_name(),'%f')

    def name_grouping(self, db, person):
        return self.name_grouping_name(db, person.primary_name)

    def name_grouping_name(self, db, pn):
        if pn.group_as:
            return pn.group_as
        sv = pn.sort_as
        if sv == Name.DEF:
            return db.get_name_group_mapping(pn.get_primary_surname())
        elif sv == Name.LNFN:
            return db.get_name_group_mapping(pn.get_surname())
        elif sv == Name.FN:
            return db.get_name_group_mapping(pn.first_name)
        else:
            return db.get_name_group_mapping(pn.get_primary_surname())

    def name_grouping_data(self, db, pn):
        if pn[_GROUP]:
            return pn[_GROUP]
        sv = pn[_SORT]
        if sv == Name.DEF:
            return db.get_name_group_mapping(_raw_primary_surname(
                                                    pn[_SURNAME_LIST]))
        elif sv == Name.LNFN:
            return db.get_name_group_mapping(_raw_full_surname(
                                                    pn[_SURNAME_LIST]))
        elif sv == Name.FN:
            return db.get_name_group_mapping(pn[_FIRSTNAME])
        else:
            return db.get_name_group_mapping(_raw_primary_surname(
                                                    pn[_SURNAME_LIST]))

displayer = NameDisplay()