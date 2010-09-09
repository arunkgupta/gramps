#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2009       Gary Burton
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
Import from GEDCOM

The GEDCOM file format is defined by the GEDCOM 5.5 Specfication, found
at http://www.familysearch.org/GEDCOM/GEDCOM55.EXE

The basic structure is a line with three attributes:

<LEVEL> <TOKEN> <DATA>

Because of this structure, it does not lend itself to more traditional
parsing techniques, such as LALR. The LEVEL token implies too much to be
useful in this context. While this makes parsing more difficult, it
does provide one very beneficial feature for GEDCOM: Error recoverability.
GEDCOM is a poorly implemented standard, primarily because it is a poor
standard to begin with. 

Most commercial applications that implement GEDCOM output add custom 
extensions, and feel free to violate the existing structure. If one were
cynical, one might believe that the commercial programs were trying to
make it difficult to transfer your data to another application.

This parser takes a different approach to parsing a GEDCOM file. The first
state, GedcomLex, reads lines from the file, and does some basic lexical
analysis on each line (actually several lines, since it automatically
combines CONT and CONC tagged lines). Each logical line returned to this
parser contains:

  Level, Token, Token text, Data, and line number.

The Data field is typically text, but in some cases, it may be a integer 
value representing an enumerated type or a GRAMPS object (in the case of
dates).

The parser works on the current level. Each context and level has a an 
associated table (dictionary) of functions indexed by the corresponding
TOKEN. When a token is found, we index into the table to find the function
associated with the token. If no token is found, a function that skips the
line and all subordinate (lines with a higher number). If a function is 
found, then we call that function, which in turn processes the line, and
all tokens at the lower level. 

For example:

1 BIRT
  2 DATE 1 JAN 2000
  2 UKNOWN TAG
    3 NOTE DATA

The function parsing the individual at level 1, would encounter the BIRT tag.
It would look up the BIRT token in the table to see if a function as defined 
for this TOKEN, and pass control to this function. This function would then
start parsing level 2. It would encounter the DATE tag, look up the 
corresponding function in the level 2 table, and pass control to its 
associated function. This function would terminate, and return control back to
the level 2 parser, which would then encounter the "UKNOWN" tag. Since this is
not a valid token, it would not be in the table, and a function that would skip
all lines until the next level 2 token is found (in this case, skipping the 
"3 NOTE DATA" line.
"""

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
import os
import sys
import re
import time
from gettext import gettext as _

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".GedcomImport")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import Errors
import gen.lib
from BasicUtils import name_displayer, UpdateCallback
import Mime
import LdsUtils
import Utils

from _GedcomTokens import *

import _GedcomInfo as GedcomInfo
import _GedcomUtils as GedcomUtils 
import _GedcomLex as GedcomLex
import _GedcomChar as GedcomChar

from gen.db.dbconst import EVENT_KEY

#-------------------------------------------------------------------------
#
# Address/Place constants
#
#-------------------------------------------------------------------------
ADDR_RE  = re.compile('(.+)([\n\r]+)(.+)\s*, (.+)\s+(\d+)\s*(.*)')
ADDR2_RE = re.compile('(.+)([\n\r]+)(.+)\s*, (.+)\s+(\d+)')
ADDR3_RE = re.compile('(.+)([\n\r]+)(.+)\s*, (.+)')

TRUNC_MSG = _("Your GEDCOM file is corrupted. "
              "It appears to have been truncated.")

#-------------------------------------------------------------------------
#
# constants
#
#-------------------------------------------------------------------------
TYPE_BIRTH  = gen.lib.ChildRefType()
TYPE_ADOPT  = gen.lib.ChildRefType(gen.lib.ChildRefType.ADOPTED)
TYPE_FOSTER = gen.lib.ChildRefType(gen.lib.ChildRefType.FOSTER)

RELATION_TYPES = (
    gen.lib.ChildRefType.BIRTH, 
    gen.lib.ChildRefType.UNKNOWN, 
    gen.lib.ChildRefType.NONE, 
    )

PEDIGREE_TYPES = {
    'birth'  : gen.lib.ChildRefType(), 
    'natural': gen.lib.ChildRefType(), 
    'step'   : TYPE_ADOPT, 
    'adopted': TYPE_ADOPT, 
    'foster' : TYPE_FOSTER, 
    }

MIME_MAP = {
    'jpeg' : 'image/jpeg',   'jpg'  : 'image/jpeg', 
    'rtf'  : 'text/rtf',     'pdf'  : 'application/pdf', 
    'mpeg' : 'video/mpeg',   'mpg'  : 'video/mpeg', 
    'gif'  : 'image/gif',    'bmp'  : 'image/x-ms-bmp', 
    'tiff' : 'image/tiff',   'aif'  : 'audio/x-aiff', 
    'text' : 'text/plain',   'w8bn' : 'application/msword', 
    'wav'  : 'audio/x-wav',  'mov'  : 'video/quicktime', 
    }

FTW_BAD_PLACE = [
    gen.lib.EventType.OCCUPATION, 
    gen.lib.EventType.RELIGION, 
    gen.lib.EventType.DEGREE
    ]

MEDIA_MAP = {
    'audio'      : gen.lib.SourceMediaType.AUDIO, 
    'book'       : gen.lib.SourceMediaType.BOOK, 
    'card'       : gen.lib.SourceMediaType.CARD, 
    'electronic' : gen.lib.SourceMediaType.ELECTRONIC, 
    'fiche'      : gen.lib.SourceMediaType.FICHE, 
    'microfiche' : gen.lib.SourceMediaType.FICHE, 
    'microfilm'  : gen.lib.SourceMediaType.FICHE, 
    'film'       : gen.lib.SourceMediaType.FILM, 
    'magazine'   : gen.lib.SourceMediaType.MAGAZINE, 
    'manuscript' : gen.lib.SourceMediaType.MANUSCRIPT, 
    'map'        : gen.lib.SourceMediaType.MAP, 
    'newspaper'  : gen.lib.SourceMediaType.NEWSPAPER, 
    'photo'      : gen.lib.SourceMediaType.PHOTO, 
    'tombstone'  : gen.lib.SourceMediaType.TOMBSTONE, 
    'grave'      : gen.lib.SourceMediaType.TOMBSTONE, 
    'video'      : gen.lib.SourceMediaType.VIDEO, 
}

#-------------------------------------------------------------------------
#
# GEDCOM events to GRAMPS events conversion
#
#-------------------------------------------------------------------------
GED_2_GRAMPS = {}
for _val, _key in GedcomInfo.personalConstantEvents.iteritems():
    #_key = GedcomInfo.personalConstantEvents[_val]
    if _key != "":
        GED_2_GRAMPS[_key] = _val

GED_2_FAMILY = {}
for _val, _key in GedcomInfo.familyConstantEvents.iteritems():
    #_key = GedcomInfo.familyConstantEvents[_val]
    if _key != "":
        GED_2_FAMILY[_key] = _val

#-------------------------------------------------------------------------
#
# regular expressions
#
#-------------------------------------------------------------------------
NOTE_RE    = re.compile(r"\s*\d+\s+\@(\S+)\@\s+NOTE(.*)$")
CONT_RE    = re.compile(r"\s*\d+\s+CONT\s?(.*)$")
CONC_RE    = re.compile(r"\s*\d+\s+CONC\s?(.*)$")
PERSON_RE  = re.compile(r"\s*\d+\s+\@(\S+)\@\s+INDI(.*)$")

#-------------------------------------------------------------------------
#
# find_from_handle
#
#-------------------------------------------------------------------------
def find_from_handle(gramps_id, table):
    """
    Find a handle corresponding to the specified GRAMPS ID. 
    
    The passed table contains the mapping. If the value is found, we return 
    it, otherwise we create a new handle, store it, and return it.
    
    """
    intid = table.get(gramps_id)
    if not intid:
        intid = Utils.create_id()
        table[gramps_id] = intid
    return intid

#-------------------------------------------------------------------------
#
# GedcomParser
#
#-------------------------------------------------------------------------
class GedcomParser(UpdateCallback):
    """
    Performs the second pass of the GEDCOM parser, which does all the heavy
    lifting.
    """

    SyntaxError = "Syntax Error"
    BadFile = "Not a GEDCOM file"

    def __init__(self, dbase, ifile, filename, callback, stage_one, default_source):
        UpdateCallback.__init__(self, callback)

        self.set_total(stage_one.get_line_count())
        self.repo2id = {}
        self.trans = None
        self.maxpeople = stage_one.get_person_count()
        self.dbase = dbase
        self.emapper = GedcomUtils.IdFinder(dbase.get_gramps_ids(EVENT_KEY), 
                                            dbase.event_prefix)
        self.famc_map = stage_one.get_famc_map()
        self.fams_map = stage_one.get_fams_map()

        self.place_parser = GedcomUtils.PlaceParser()
        self.inline_srcs = {}
        self.media_map = {}
        self.gedmap = GedcomInfo.GedcomInfoDB()
        self.gedsource = self.gedmap.get_from_source_tag('GEDCOM 5.5')
        self.use_def_src = default_source
        if self.use_def_src:
            self.def_src = gen.lib.Source()
            fname = os.path.basename(filename).split('\\')[-1]
            self.def_src.set_title(_("Import from GEDCOM (%s)") % fname)
        self.dir_path = os.path.dirname(filename)
        self.is_ftw = False
        self.groups = None
        self.want_parse_warnings = True

        self.pid_map = GedcomUtils.IdMapper(
            self.dbase.id_trans, 
            self.dbase.find_next_person_gramps_id, 
            self.dbase.get_number_of_people())
        self.fid_map = GedcomUtils.IdMapper(
            self.dbase.fid_trans, 
            self.dbase.find_next_family_gramps_id, 
            self.dbase.get_number_of_families())
        self.sid_map = GedcomUtils.IdMapper(
            self.dbase.sid_trans, 
            self.dbase.find_next_source_gramps_id, 
            self.dbase.get_number_of_sources())
        self.oid_map = GedcomUtils.IdMapper(
            self.dbase.oid_trans, 
            self.dbase.find_next_object_gramps_id, 
            self.dbase.get_number_of_media_objects())
        self.rid_map = GedcomUtils.IdMapper(
            self.dbase.rid_trans, 
            self.dbase.find_next_repository_gramps_id, 
            self.dbase.get_number_of_repositories())
        self.nid_map = GedcomUtils.IdMapper(
            self.dbase.nid_trans, 
            self.dbase.find_next_note_gramps_id, 
            self.dbase.get_number_of_notes())

        self.gid2id = {}
        self.oid2id = {}
        self.sid2id = {}
        self.lid2id = {}
        self.fid2id = {}
        self.rid2id = {}
        self.nid2id = {}

        #
        # Parse table for SUBM tag
        #
        self.subm_parse_tbl = {
            # +1 NAME <SUBMITTER_NAME>
            TOKEN_NAME  : self.__subm_name, 
            # +1 <<ADDRESS_STRUCTURE>>
            TOKEN_ADDR  : self.__subm_addr, 
            TOKEN_PHON  : self.__subm_phon,
            # +1 <<MULTIMEDIA_LINK>>
            # +1 LANG <LANGUAGE_PREFERENCE>
            # +1 RFN <SUBMITTER_REGISTERED_RFN>
            # +1 RIN <AUTOMATED_RECORD_ID>
            # +1 <<CHANGE_DATE>>
            }

        #
        # Parse table for INDI tag
        #
        self.indi_parse_tbl = {
            # +1 RESN <RESTRICTION_NOTICE> {0:1}
            TOKEN_RESN  : self.__person_resn, 
            # +1 <<PERSONAL_NAME_STRUCTURE>> {0:M}
            TOKEN_NAME  : self.__person_name, 
            # +1 SEX <SEX_VALUE> {0:1}
            TOKEN_SEX   : self.__person_sex, 
            # +1 <<INDIVIDUAL_EVENT_STRUCTURE>> {0:M}
            TOKEN_EVEN  : self.__person_even, 
            TOKEN_GEVENT: self.__person_std_event, 
            TOKEN_BIRT  : self.__person_birt, 
            TOKEN_RELI  : self.__person_reli, 
            TOKEN_ADOP  : self.__person_adop, 
            TOKEN_DEAT  : self.__person_deat, 
            # +1 <<INDIVIDUAL_ATTRIBUTE_STRUCTURE>> {0:M}
            # +1 AFN <ANCESTRAL_FILE_NUMBER> {0:1}
            TOKEN_ATTR  : self.__person_std_attr, 
            TOKEN_FACT  : self.__person_fact, 
            #+1 <<LDS_INDIVIDUAL_ORDINANCE>> {0:M}
            TOKEN_BAPL  : self.__person_bapl, 
            TOKEN_CONL  : self.__person_conl, 
            TOKEN_ENDL  : self.__person_endl, 
            TOKEN_SLGC  : self.__person_slgc, 
            #+1 <<CHILD_TO_FAMILY_LINK>> {0:M}
            TOKEN_FAMC  : self.__person_famc, 
            # +1 <<SPOUSE_TO_FAMILY_LINK>> {0:M}
            TOKEN_FAMS  : self.__person_fams, 
            # +1 SUBM @<XREF:SUBM>@ {0:M}
            TOKEN_SUBM  : self.__skip_record, 
            # +1 <<ASSOCIATION_STRUCTURE>> {0:M}
            TOKEN_ASSO  : self.__person_asso, 
            # +1 ALIA @<XREF:INDI>@ {0:M}
            TOKEN_ALIA  : self.__person_alt_name, 
            # +1 ANCI @<XREF:SUBM>@ {0:M}
            TOKEN_ANCI  : self.__skip_record, 
            # +1 DESI @<XREF:SUBM>@ {0:M}
            TOKEN_DESI  : self.__skip_record, 
            # +1 <<SOURCE_CITATION>> {0:M}
            TOKEN_SOUR  : self.__person_sour, 
            # +1 <<MULTIMEDIA_LINK>> {0:M}
            TOKEN_OBJE  : self.__person_object, 
            # +1 <<NOTE_STRUCTURE>> {0:M} 
            TOKEN_NOTE  : self.__person_note, 
            TOKEN_RNOTE : self.__person_note, 
            TOKEN__COMM : self.__person_note, 
            # +1 RFN <PERMANENT_RECORD_FILE_NUMBER> {0:1}
            TOKEN_RFN   : self.__person_attr, 
            # +1 REFN <USER_REFERENCE_NUMBER> {0:M}
            # +2 TYPE <USER_REFERENCE_TYPE> {0:1}
            TOKEN_REFN  : self.__person_attr, 
            # +1 RIN <AUTOMATED_RECORD_ID> {0:1}
            TOKEN_RIN   : self.__skip_record, 
            # +1 <<CHANGE_DATE>> {0:1}
            TOKEN_CHAN  : self.__person_chan, 

            TOKEN_ADDR  : self.__person_addr, 
            TOKEN_PHON  : self.__person_phon, 
            TOKEN__TODO : self.__skip_record, 
            TOKEN_TITL  : self.__person_titl, 
            }

        #
        # Parse table for INDI.NAME
        # 
        self.name_parse_tbl = {
            # +1 NPFX <NAME_PIECE_PREFIX> {0:1}
            TOKEN_NPFX   : self.__name_npfx, 
            # +1 GIVN <NAME_PIECE_GIVEN> {0:1}
            TOKEN_GIVN   : self.__name_givn, 
            # NICK <NAME_PIECE_NICKNAME> {0:1}
            TOKEN_NICK   : self.__name_nick, 
            # +1 SPFX <NAME_PIECE_SURNAME_PREFIX {0:1}
            TOKEN_SPFX   : self.__name_spfx, 
            # +1 SURN <NAME_PIECE_SURNAME> {0:1}
            TOKEN_SURN   : self.__name_surn, 
            # +1 NSFX <NAME_PIECE_SUFFIX> {0:1}
            TOKEN_NSFX   : self.__name_nsfx, 
            # +1 <<SOURCE_CITATION>> {0:M}
            TOKEN_SOUR   : self.__name_sour, 
            # +1 <<NOTE_STRUCTURE>> {0:M}
            TOKEN_NOTE   : self.__name_note, 
            TOKEN_RNOTE  : self.__name_note, 
            # Extensions
            TOKEN_ALIA   : self.__name_alia, 
            TOKEN__MARNM : self.__name_marnm, 
            TOKEN__AKA   : self.__name_aka, 
            TOKEN_TYPE   : self.__name_type, 
            TOKEN_BIRT   : self.__ignore, 
            }

        self.repo_parse_tbl = {
            TOKEN_NAME   : self.__repo_name, 
            TOKEN_ADDR   : self.__repo_addr, 
            TOKEN_RIN    : self.__ignore, 
            TOKEN_NOTE   : self.__repo_note, 
            TOKEN_RNOTE  : self.__repo_note, 
            }

        self.event_parse_tbl = {
            # n TYPE <EVENT_DESCRIPTOR> {0:1}
            TOKEN_TYPE   : self.__event_type, 
            # n DATE <DATE_VALUE> {0:1} p.*/*
            TOKEN_DATE   : self.__event_date, 
            # n <<PLACE_STRUCTURE>> {0:1} p.*
            TOKEN_PLAC   : self.__event_place, 
            # n <<ADDRESS_STRUCTURE>> {0:1} p.*
            TOKEN_ADDR   : self.__event_addr, 
            # n AGE <AGE_AT_EVENT> {0:1} p.*
            TOKEN_AGE    : self.__event_age, 
            # n AGNC <RESPONSIBLE_AGENCY> {0:1} p.*
            TOKEN_AGNC   : self.__event_agnc, 
            # n CAUS <CAUSE_OF_EVENT> {0:1} p.*
            TOKEN_CAUS   : self.__event_cause, 
            # n <<SOURCE_CITATION>> {0:M} p.*
            TOKEN_SOUR   : self.__event_source, 
            # n <<MULTIMEDIA_LINK>> {0:M} p.*, *
            TOKEN_OBJE   : self.__event_object, 
            # n <<NOTE_STRUCTURE>> {0:M} p.
            TOKEN_NOTE   : self.__event_inline_note, 
            TOKEN_RNOTE  : self.__event_note, 
            # Other
            TOKEN__PRIV  : self.__event_privacy, 
            TOKEN_OFFI   : self.__event_note, 
            TOKEN_PHON   : self.__ignore, 
            TOKEN__GODP  : self.__event_witness, 
            TOKEN__WITN  : self.__event_witness, 
            TOKEN__WTN   : self.__event_witness, 
            TOKEN_RELI   : self.__ignore, 
            TOKEN_TIME   : self.__ignore, 
            TOKEN_ASSO   : self.__ignore, 
            TOKEN_IGNORE : self.__ignore, 
            TOKEN_STAT   : self.__ignore, 
            TOKEN_TEMP   : self.__ignore, 
            TOKEN_HUSB   : self.__event_husb, 
            TOKEN_WIFE   : self.__event_wife, 
            TOKEN_FAMC   : self.__person_birth_famc, 
            # Not legal, but inserted by Ultimate Family Tree
            TOKEN_CHAN   : self.__ignore, 
            TOKEN_QUAY  : self.__ignore, 
            }

        self.adopt_parse_tbl = {
            TOKEN_TYPE   : self.__event_type, 
            TOKEN__PRIV  : self.__event_privacy, 
            TOKEN_DATE   : self.__event_date, 
            TOKEN_SOUR   : self.__event_source, 
            TOKEN_PLAC   : self.__event_place, 
            TOKEN_ADDR   : self.__event_addr, 
            TOKEN_CAUS   : self.__event_cause, 
            TOKEN_AGNC   : self.__event_agnc, 
            TOKEN_AGE    : self.__event_age, 
            TOKEN_NOTE   : self.__event_note, 
            TOKEN_RNOTE  : self.__event_note, 
            TOKEN_OFFI   : self.__event_note, 
            TOKEN__GODP  : self.__event_witness, 
            TOKEN__WITN  : self.__event_witness, 
            TOKEN__WTN   : self.__event_witness, 
            TOKEN_RELI   : self.__ignore, 
            TOKEN_TIME   : self.__ignore, 
            TOKEN_ASSO   : self.__ignore, 
            TOKEN_IGNORE : self.__ignore, 
            TOKEN_STAT   : self.__ignore, 
            TOKEN_TEMP   : self.__ignore, 
            TOKEN_OBJE   : self.__event_object, 
            TOKEN_FAMC   : self.__person_adopt_famc, 
            # Not legal, but inserted by Ultimate Family Tree
            TOKEN_CHAN   : self.__ignore, 
            TOKEN_QUAY   : self.__ignore, 
            }

        self.famc_parse_tbl = {
            # n FAMC @<XREF:FAM>@ {1:1}
            # +1 PEDI <PEDIGREE_LINKAGE_TYPE> {0:M} p.*
            TOKEN_PEDI   : self.__person_famc_pedi, 
            # +1 <<NOTE_STRUCTURE>> {0:M} p.*
            TOKEN_NOTE   : self.__person_famc_note, 
            TOKEN_RNOTE  : self.__person_famc_note, 
            # Extras
            TOKEN__PRIMARY: self.__person_famc_primary, 
            TOKEN_SOUR   : self.__person_famc_sour, 
            # GEDit
            TOKEN_STAT   : self.__ignore, 
            }

        self.person_fact_parse_tbl = {
            TOKEN_TYPE   : self.__person_fact_type, 
            }

        self.person_attr_parse_tbl = {
            TOKEN_TYPE   : self.__person_attr_type, 
            TOKEN_CAUS   : self.__ignore, 
            TOKEN_DATE   : self.__ignore, 
            TOKEN_TIME   : self.__ignore, 
            TOKEN_ADDR   : self.__ignore, 
            TOKEN_IGNORE : self.__ignore, 
            TOKEN_STAT   : self.__ignore, 
            TOKEN_TEMP   : self.__ignore, 
            TOKEN_OBJE   : self.__ignore, 
            TOKEN_SOUR   : self.__person_attr_source, 
            TOKEN_PLAC   : self.__person_attr_place, 
            TOKEN_NOTE   : self.__person_attr_note, 
            TOKEN_RNOTE  : self.__person_attr_note, 
            }

        self.lds_parse_tbl = {
            TOKEN_TEMP   : self.__lds_temple, 
            TOKEN_DATE   : self.__lds_date, 
            TOKEN_FAMC   : self.__lds_famc, 
            TOKEN_FORM   : self.__lds_form, 
            TOKEN_PLAC   : self.__lds_plac, 
            TOKEN_SOUR   : self.__lds_sour, 
            TOKEN_NOTE   : self.__lds_note, 
            TOKEN_RNOTE  : self.__lds_note, 
            TOKEN_STAT   : self.__lds_stat, 
            }

        self.asso_parse_tbl = {
            TOKEN_RELA   : self.__person_asso_rela, 
            TOKEN_SOUR   : self.__person_asso_sour, 
            TOKEN_NOTE   : self.__person_asso_note, 
            TOKEN_RNOTE  : self.__person_asso_note, 
            }

        self.srcref_parse_tbl = {
            TOKEN_PAGE   : self.__srcref_page, 
            TOKEN_DATE   : self.__srcref_date, 
            TOKEN_DATA   : self.__srcref_data, 
            TOKEN_OBJE   : self.__srcref_obje, 
            TOKEN_REFN   : self.__srcref_refn, 
            TOKEN_EVEN   : self.__ignore, 
            TOKEN_IGNORE : self.__ignore, 
            TOKEN__LKD   : self.__ignore, 
            TOKEN_QUAY   : self.__srcref_quay, 
            TOKEN_NOTE   : self.__srcref_note, 
            TOKEN_RNOTE  : self.__srcref_note, 
            TOKEN_TEXT   : self.__srcref_data_text, 
            }

        self.object_parse_tbl = {
            TOKEN_FORM   : self.__object_ref_form, 
            TOKEN_TITL   : self.__object_ref_titl, 
            TOKEN_FILE   : self.__object_ref_file, 
            TOKEN_NOTE   : self.__object_ref_note, 
            TOKEN_RNOTE  : self.__object_ref_note, 
            TOKEN_IGNORE : self.__ignore, 
        }

        self.parse_loc_tbl = {
            TOKEN_ADDR   : self.__location_addr, 
            TOKEN_ADR1   : self.__location_addr, 
            TOKEN_ADR2   : self.__location_addr, 
            TOKEN_DATE   : self.__location_date, 
            TOKEN_CITY   : self.__location_city, 
            TOKEN_STAE   : self.__location_stae, 
            TOKEN_POST   : self.__location_post, 
            TOKEN_CTRY   : self.__location_ctry, 
            TOKEN_NOTE   : self.__location_note, 
            TOKEN_RNOTE  : self.__location_note, 
            TOKEN__LOC   : self.__ignore, 
            TOKEN__NAME  : self.__ignore, 
            TOKEN_PHON   : self.__ignore, 
            TOKEN_IGNORE : self.__ignore, 
            }
        
        #
        # FAM 
        # 
        self.family_func = {
            # +1 <<FAMILY_EVENT_STRUCTURE>>  {0:M}
            TOKEN_GEVENT : self.__family_std_event, 
            TOKEN_EVEN   : self.__family_even, 
            # +1 HUSB @<XREF:INDI>@  {0:1}
            TOKEN_HUSB   : self.__family_husb, 
            # +1 WIFE @<XREF:INDI>@  {0:1}
            TOKEN_WIFE   : self.__family_wife, 
            # +1 CHIL @<XREF:INDI>@  {0:M}
            TOKEN_CHIL   : self.__family_chil, 
            # +1 NCHI <COUNT_OF_CHILDREN>  {0:1}
            # +1 SUBM @<XREF:SUBM>@  {0:M}
            # +1 <<LDS_SPOUSE_SEALING>>  {0:M}
            TOKEN_SLGS   : self.__family_slgs, 
            # +1 <<SOURCE_CITATION>>  {0:M}
            TOKEN_SOUR   : self.__family_source, 
            # +1 <<MULTIMEDIA_LINK>>  {0:M}
            TOKEN_OBJE   : self.__family_object, 
            # +1 <<NOTE_STRUCTURE>>  {0:M}
            TOKEN__COMM  : self.__family_comm, 
            TOKEN_NOTE   : self.__family_note, 
            TOKEN_RNOTE  : self.__family_note, 
            # +1 REFN <USER_REFERENCE_NUMBER>  {0:M}
            TOKEN_REFN   : self.__family_cust_attr, 
            # +1 RIN <AUTOMATED_RECORD_ID>  {0:1}
            # +1 <<CHANGE_DATE>>  {0:1}
            TOKEN_CHAN   : self.__family_chan, 
            TOKEN_ENDL   : self.__ignore, 

            TOKEN_ADDR   : self.__family_addr, 
            TOKEN_RIN    : self.__family_cust_attr, 
            TOKEN_SUBM   : self.__ignore, 
            TOKEN_ATTR   : self.__family_attr, 
            }

        self.family_rel_tbl = {
            TOKEN__FREL  : self.__family_frel, 
            TOKEN__MREL  : self.__family_mrel, 
            TOKEN_ADOP   : self.__family_adopt, 
            TOKEN__STAT  : self.__family_stat, 
            }

        self.source_func = {
            TOKEN_TITL   : self.__source_title, 
            TOKEN_TAXT   : self.__source_taxt_peri, 
            TOKEN_PERI   : self.__source_taxt_peri, 
            TOKEN_AUTH   : self.__source_auth, 
            TOKEN_PUBL   : self.__source_publ, 
            TOKEN_NOTE   : self.__source_note, 
            TOKEN_RNOTE  : self.__source_note, 
            TOKEN_TEXT   : self.__source_text, 
            TOKEN_ABBR   : self.__source_abbr, 
            TOKEN_REFN   : self.__source_attr, 
            TOKEN_RIN    : self.__ignore, 
            TOKEN_REPO   : self.__source_repo, 
            TOKEN_OBJE   : self.__source_object, 
            TOKEN_CHAN   : self.__source_chan, 
            TOKEN_MEDI   : self.__source_attr, 
            TOKEN__NAME  : self.__source_attr, 
            TOKEN_DATA   : self.__ignore, 
            TOKEN_TYPE   : self.__source_attr, 
            TOKEN_CALN   : self.__ignore, 
            # not legal, but Ultimate Family Tree does this
            TOKEN_DATE   : self.__ignore,  
            TOKEN_IGNORE : self.__ignore, 
        }

        self.obje_func = {
            TOKEN_FORM   : self.__obje_form, 
            TOKEN_TITL   : self.__obje_title, 
            TOKEN_FILE   : self.__obje_file, 
            TOKEN_NOTE   : self.__obje_note, 
            TOKEN_RNOTE  : self.__obje_note, 
            TOKEN_BLOB   : self.__obje_blob, 
            TOKEN_REFN   : self.__obje_refn, 
            TOKEN_TYPE   : self.__obje_type, 
            TOKEN_RIN    : self.__obje_rin, 
            TOKEN_CHAN   : self.__obje_chan, 
            }

        self.parse_addr_tbl = {
            TOKEN_DATE   : self.__address_date, 
            TOKEN_CITY   : self.__address_city, 
            TOKEN_STAE   : self.__address_state, 
            TOKEN_POST   : self.__address_post, 
            TOKEN_CTRY   : self.__address_country, 
            TOKEN_PHON   : self.__address_phone, 
            TOKEN_SOUR   : self.__address_sour, 
            TOKEN_NOTE   : self.__address_note, 
            TOKEN_RNOTE  : self.__address_note, 
            TOKEN__LOC   : self.__ignore, 
            TOKEN__NAME  : self.__ignore, 
            TOKEN_IGNORE : self.__ignore, 
            TOKEN_TYPE   : self.__ignore, 
            TOKEN_CAUS   : self.__ignore, 
            }

        self.event_cause_tbl = {
            TOKEN_SOUR   : self.__event_cause_source, 
            }

        self.event_place_map = {
            TOKEN_NOTE   : self.__event_place_note, 
            TOKEN_RNOTE  : self.__event_place_note, 
            TOKEN_FORM   : self.__event_place_form, 
            TOKEN_OBJE   : self.__event_place_object, 
            TOKEN_SOUR   : self.__event_place_sour, 
            TOKEN__LOC   : self.__ignore, 
            TOKEN_MAP    : self.__place_map, 
            # Not legal,  but generated by Ultimate Family Tree
            TOKEN_QUAY   : self.__ignore, 
            }

        self.place_map_tbl = {
            TOKEN_LATI   : self.__place_lati, 
            TOKEN_LONG   : self.__place_long, 
            }

        self.repo_ref_tbl = {
            TOKEN_CALN   : self.__repo_ref_call, 
            TOKEN_NOTE   : self.__repo_ref_note, 
            TOKEN_RNOTE  : self.__repo_ref_note, 
            TOKEN_MEDI   : self.__repo_ref_medi, 
            TOKEN_IGNORE : self.__ignore, 
            }

        self.parse_person_adopt = {
            TOKEN_ADOP   : self.__person_adopt_famc_adopt, 
            }

        self.opt_note_tbl = {
            TOKEN_RNOTE  : self.__optional_note, 
            TOKEN_NOTE   : self.__optional_note, 
            }

        self.srcref_data_tbl = {
            TOKEN_DATE   : self.__srcref_data_date, 
            TOKEN_TEXT   : self.__srcref_data_text,
            TOKEN_RNOTE  : self.__srcref_data_note, 
            TOKEN_NOTE   : self.__srcref_data_note, 
            }

        self.header_sour = {
            TOKEN_SOUR   : self.__header_sour, 
            TOKEN_NAME   : self.__ignore, 
            TOKEN_VERS   : self.__header_vers, 
            TOKEN_FILE   : self.__header_file, 
            TOKEN_COPR   : self.__header_copr, 
            TOKEN_SUBM   : self.__header_subm, 
            TOKEN_CORP   : self.__ignore, 
            TOKEN_DATA   : self.__ignore, 
            TOKEN_SUBN   : self.__ignore, 
            TOKEN_LANG   : self.__ignore, 
            TOKEN_TIME   : self.__ignore, 
            TOKEN_DEST   : self.__header_dest, 
            TOKEN_CHAR   : self.__ignore, 
            TOKEN_GEDC   : self.__ignore, 
            TOKEN__SCHEMA: self.__ignore, 
            TOKEN_PLAC   : self.__header_plac, 
            TOKEN_DATE   : self.__header_date, 
            TOKEN_NOTE   : self.__header_note, 
            }

        self.header_subm = {
            TOKEN_NAME   : self.__header_subm_name, 
            }

        self.place_form = {
            TOKEN_FORM   : self.__place_form, 
            }

        # look for existing place titles, build a map 
        self.place_names = {}
        cursor = dbase.get_place_cursor()
        data = cursor.next()
        while data:
            (handle, val) = data
            self.place_names[val[2]] = handle
            data = cursor.next()
        cursor.close()

        enc = stage_one.get_encoding()

        if enc == "ANSEL":
            rdr = GedcomChar.AnselReader(ifile)
        elif enc in ("UTF-8", "UTF8"):
            rdr = GedcomChar.UTF8Reader(ifile)
        elif enc in ("UTF-16", "UTF16", "UNICODE"):
            rdr = GedcomChar.UTF16Reader(ifile)
        else:
            rdr = GedcomChar.AnsiReader(ifile)

        self.lexer = GedcomLex.Reader(rdr)
        self.filename = filename
        self.backoff = False

        fullpath = os.path.normpath(os.path.abspath(filename))
        self.geddir = os.path.dirname(fullpath)
    
        self.error_count = 0
        amap = GedcomInfo.personalConstantAttributes
        
        self.attrs = amap.values()
        self.gedattr = {}
        for val, key in amap.iteritems():
            self.gedattr[key] = val
        self.search_paths = []

    def parse_gedcom_file(self, use_trans=False):
        """
        Parses the opened GEDCOM file.
        """
        no_magic = self.maxpeople < 1000
        self.trans = self.dbase.transaction_begin("", not use_trans, no_magic)

        self.dbase.disable_signals()
        self.__parse_header_head()
        self.want_parse_warnings = False
        self.__parse_header_source()
        self.want_parse_warnings = True
        if self.use_def_src:
            self.dbase.add_source(self.def_src, self.trans)
        self.__parse_record()
        self.__parse_trailer()
        for title, handle in self.inline_srcs.iteritems():
            src = gen.lib.Source()
            src.set_handle(handle)
            src.set_title(title)
            self.dbase.add_source(src, self.trans)
            
        self.dbase.transaction_commit(self.trans, _("GEDCOM import"))
        self.dbase.enable_signals()
        self.dbase.request_rebuild()
        
    def __find_person_handle(self, gramps_id):
        """
        Return the database handle associated with the person's GRAMPS ID
        """
        return find_from_handle(gramps_id, self.gid2id)

    def __find_family_handle(self, gramps_id):
        """
        Return the database handle associated with the family's GRAMPS ID
        """
        return find_from_handle(gramps_id, self.fid2id)
        
    def __find_object_handle(self, gramps_id):
        """
        Return the database handle associated with the media object's GRAMPS ID
        """
        return find_from_handle(gramps_id, self.oid2id)

    def __find_note_handle(self, gramps_id):
        """
        Return the database handle associated with the media object's GRAMPS ID
        """
        return find_from_handle(gramps_id, self.nid2id)

    def __find_or_create_person(self, gramps_id):
        """
        Finds or creates a person based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise, 
        we create a new person, assign the handle and GRAMPS ID.
        """
        person = gen.lib.Person()
        intid = self.gid2id.get(gramps_id)
        if self.dbase.has_person_handle(intid):
            person.unserialize(self.dbase.get_raw_person_data(intid))
        else:
            intid = find_from_handle(gramps_id, self.gid2id)
            person.set_handle(intid)
            person.set_gramps_id(gramps_id)
        return person

    def __find_or_create_family(self, gramps_id):
        """
        Finds or creates a family based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise, 
        we create a new family, assign the handle and GRAMPS ID.
        """
        family = gen.lib.Family()
        intid = self.fid2id.get(gramps_id)
        if self.dbase.has_family_handle(intid):
            family.unserialize(self.dbase.get_raw_family_data(intid))
        else:
            intid = find_from_handle(gramps_id, self.fid2id)
            family.set_handle(intid)
            family.set_gramps_id(gramps_id)
        return family

    def __find_or_create_object(self, gramps_id):
        """
        Finds or creates a media object based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise, 
        we create a new media object, assign the handle and GRAMPS ID.
        """
        obj = gen.lib.MediaObject()
        intid = self.oid2id.get(gramps_id)
        if self.dbase.has_object_handle(intid):
            obj.unserialize(self.dbase.get_raw_object_data(intid))
        else:
            intid = find_from_handle(gramps_id, self.oid2id)
            obj.set_handle(intid)
            obj.set_gramps_id(gramps_id)
        return obj

    def __find_or_create_source(self, gramps_id):
        """
        Find or create a source based on the GRAMPS ID. 
        
        If the ID is already used (is in the db), we return the item in the 
        db. Otherwise, we create a new source, assign the handle and GRAMPS ID.
        
        """
        obj = gen.lib.Source()
        intid = self.sid2id.get(gramps_id)
        if self.dbase.has_source_handle(intid):
            obj.unserialize(self.dbase.get_raw_source_data(intid))
        else:
            intid = find_from_handle(gramps_id, self.sid2id)
            obj.set_handle(intid)
            obj.set_gramps_id(gramps_id)
        return obj

    def __find_or_create_repository(self, gramps_id):
        """
        Finds or creates a repository based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise, 
        we create a new repository, assign the handle and GRAMPS ID.

        Some GEDCOM "flavors" destroy the specification, and declare the 
        repository inline instead of in a object. 
        """
        repository = gen.lib.Repository()
        if not gramps_id:
            need_commit = True
            gramps_id = self.dbase.find_next_repository_gramps_id()
        else:
            need_commit = False

        intid = self.rid2id.get(gramps_id)
        if self.dbase.has_repository_handle(intid):
            repository.unserialize(self.dbase.get_raw_repository_data(intid))
        else:
            intid = find_from_handle(gramps_id, self.rid2id)
            repository.set_handle(intid)
            repository.set_gramps_id(gramps_id)
        if need_commit:
            self.dbase.commit_repository(repository, self.trans)
        return repository

    def __find_or_create_note(self, gramps_id):
        """
        Finds or creates a repository based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise, 
        we create a new repository, assign the handle and GRAMPS ID.

        Some GEDCOM "flavors" destroy the specification, and declare the 
        repository inline instead of in a object. 
        """
        note = gen.lib.Note()
        if not gramps_id:
            need_commit = True
            gramps_id = self.dbase.find_next_note_gramps_id()
        else:
            need_commit = False

        intid = self.nid2id.get(gramps_id)
        if self.dbase.has_note_handle(intid):
            note.unserialize(self.dbase.get_raw_note_data(intid))
        else:
            intid = find_from_handle(gramps_id, self.nid2id)
            note.set_handle(intid)
            note.set_gramps_id(gramps_id)
        if need_commit:
            self.dbase.add_note(note, self.trans)
        return note

    def __find_or_create_place(self, title):
        """
        Finds or creates a place based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise, 
        we create a new place, assign the handle and GRAMPS ID.
        """
        place = gen.lib.Place()

        # check to see if we've encountered this name before
        # if we haven't we need to get a new GRAMPS ID
        
        intid = self.place_names.get(title)
        if intid is None:
            intid = self.lid2id.get(title)
            if intid is None:
                new_id = self.dbase.find_next_place_gramps_id()
            else:
                new_id = None
        else:
            new_id = None

        # check to see if the name already existed in the database
        # if it does, create a new name by appending the GRAMPS ID.
        # generate a GRAMPS ID if needed
        
        if self.dbase.has_place_handle(intid):
            place.unserialize(self.dbase.get_raw_place_data(intid))
        else:
            intid = Utils.create_id()
            place.set_handle(intid)
            place.set_title(title)
            place.set_gramps_id(new_id)
            self.dbase.add_place(place, self.trans)
            self.lid2id[title] = intid
        return place

    def __find_file(self, fullname, altpath):
        tries = []
        fullname = fullname.replace('\\', os.path.sep)
        tries.append(fullname)
        
        try:
            if os.path.isfile(fullname):
                return (1, fullname)
        except UnicodeEncodeError:
            # FIXME: problem possibly caused by umlaut/accented character 
            # in filename
            return (0, tries)
        other = os.path.join(altpath, fullname)
        tries.append(other)
        if os.path.isfile(other):
            return (1, other)
        other = os.path.join(altpath, os.path.basename(fullname))
        tries.append(other)
        if os.path.isfile(other):
            return (1, other)
        if len(fullname) > 3:
            if fullname[1] == ':':
                fullname = fullname[2:]
                for path in self.search_paths:
                    other = os.path.normpath("%s/%s" % (path, fullname))
                    tries.append(other)
                    if os.path.isfile(other):
                        return (1, other)
            return (0, tries)
        else:
            return (0, tries)

    def __level_is_finished(self, text, level):
        """
        Check to see if the level has been completed, indicated by finding
        a level indiciated by the passed level value. If the level is finished, 
        then make sure to call self._backup to reset the text pointer.
        """
        done = text.level < level
        if done:
            self._backup()
        return done

    def __get_next_line(self):
        """
        Get the next line for analysis from the lexical analyzer. Return the
        same value if the _backup flag is set.
        """
        if not self.backoff:
            self.groups = self.lexer.readline()
            self.update()
            
            # EOF ?
            if not self.groups:
                self.backoff = False
                self.__warn(TRUNC_MSG)
                self.groups = None
                raise Errors.GedcomError(TRUNC_MSG)

        self.backoff = False
        return self.groups
            
    def __not_recognized(self, line, level):
        """
        Prints a message when an undefined token is found. All subordinate items
        to the current item are ignored.

        @param level: Current level in the file
        @type level: int
        """
        msg = _("Line %d was not understood, so it was ignored.") % line.line
        self.__warn(msg)
        self.__skip_subordinate_levels(level)

    def __warn(self, msg):
        """
        Displays a msg using the logging facilities.
        """
        LOG.warning(msg)
        self.error_count += 1

    def _backup(self):
        """
        Set the _backup flag so that the current line can be accessed by the
        next level up.
        """
        self.backoff = True

    def __parse_trailer(self):
        """
        Looks for the expected TRLR token
        """
        try:
            line = self.__get_next_line()
            if line and line.token != TOKEN_TRLR:
                self.__not_recognized(line, 0)
        except TypeError:
            return
        
    def __parse_submitter(self, line):
        """
        Parses the submitter data

        n @<XREF:SUBM>@ SUBM
        +1 NAME <SUBMITTER_NAME>
        +1 <<ADDRESS_STRUCTURE>>
        +1 <<MULTIMEDIA_LINK>>
        +1 LANG <LANGUAGE_PREFERENCE>
        +1 RFN <SUBMITTER_REGISTERED_RFN>
        +1 RIN <AUTOMATED_RECORD_ID>
        +1 <<CHANGE_DATE>>
        """
        researcher = gen.lib.Researcher()
        state = GedcomUtils.CurrentState()
        state.res = researcher
        state.level = 1
        self.__parse_level(state, self.subm_parse_tbl, self.__undefined)
        self.dbase.set_researcher(state.res)

    def __parse_record(self):
        """
        Parse the top level (0 level) instances.
        """
        while True:
            line = self.__get_next_line()
            key = line.data
            if not line or line.token == TOKEN_TRLR:
                self._backup()
                break
            if line.token == TOKEN_UNKNOWN:
                self.__skip_subordinate_levels(1)
            elif key in ("FAM", "FAMILY"):
                self.__parse_fam(line)
            elif key in ("INDI", "INDIVIDUAL"):
                self.__parse_indi(line)
            elif key in ("OBJE", "OBJECT"):
                self.__parse_obje(line)
            elif key in ("REPO", "REPOSITORY"):
                self.__parse_repo(line)
            elif key in ("SUBM", "SUBMITTER"):
                self.__parse_submitter(line)
            elif key in ("SUBN"):
                self.__skip_subordinate_levels(1)
            elif line.token in (TOKEN_SUBM, TOKEN_SUBN, TOKEN_IGNORE):
                self.__skip_subordinate_levels(1)
            elif key in ("SOUR", "SOURCE"):
                self.__parse_source(line.token_text, 1)
            elif line.data.startswith("SOUR ") or \
                    line.data.startswith("SOURCE "):
                # A source formatted in a single line, for example:
                # 0 @S62@ SOUR This is the title of the source
                source = self.__find_or_create_source(self.sid_map[line.data])
                source.set_title(line.data[5:])
                self.dbase.commit_source(source, self.trans)
            elif key[0:4] == "NOTE":
                try:
                    line.data = line.data[5:]
                except:
                    # don't think this path is ever taken, but if it is..
                    # ensure a message is emitted & subordinates skipped
                    line.data = None
                self.__parse_inline_note(line, 1)
            else:
                self.__not_recognized(line, 1)

    def __parse_level(self, state, __map, default):
        """
        Loop trough the current GEDCOM level, calling the appropriate 
        functions associated with the TOKEN. 
        
        If no matching function for the token is found, the default function 
        is called instead.
        
        """
        while True:
            line = self.__get_next_line()
            if line.level < state.level:
                self.backoff = True
                return
            else:
                func = __map.get(line.token, default)
                func(line, state)

    def __undefined(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__not_recognized(line, state.level+1)

    #----------------------------------------------------------------------
    #
    # INDI parsing
    #
    #----------------------------------------------------------------------
    def __parse_indi(self, line):
        """
        Handling of the GEDCOM INDI tag and all lines subordinate to the current
        line.

        n  @XREF:INDI@ INDI {1:1}
        +1 RESN <RESTRICTION_NOTICE> {0:1}
        +1 <<PERSONAL_NAME_STRUCTURE>> {0:M}
        +1 SEX <SEX_VALUE> {0:1}
        +1 <<INDIVIDUAL_EVENT_STRUCTURE>> {0:M}
        +1 <<INDIVIDUAL_ATTRIBUTE_STRUCTURE>> {0:M}
        +1 <<LDS_INDIVIDUAL_ORDINANCE>> {0:M}
        +1 <<CHILD_TO_FAMILY_LINK>> {0:M}
        +1 <<SPOUSE_TO_FAMILY_LINK>> {0:M}
        +1 SUBM @<XREF:SUBM>@ {0:M}
        +1 <<ASSOCIATION_STRUCTURE>> {0:M}
        +1 ALIA @<XREF:INDI>@ {0:M}
        +1 ANCI @<XREF:SUBM>@ {0:M}
        +1 DESI @<XREF:SUBM>@ {0:M}
        +1 <<SOURCE_CITATION>> {0:M}
        +1 <<MULTIMEDIA_LINK>> {0:M}
        +1 <<NOTE_STRUCTURE>> {0:M} 
        +1 RFN <PERMANENT_RECORD_FILE_NUMBER> {0:1}
        +1 AFN <ANCESTRAL_FILE_NUMBER> {0:1}
        +1 REFN <USER_REFERENCE_NUMBER> {0:M}
        +2 TYPE <USER_REFERENCE_TYPE> {0:1}
        +1 RIN <AUTOMATED_RECORD_ID> {0:1}
        +1 <<CHANGE_DATE>> {0:1}
        """

        # find the person
        real_id = self.pid_map[line.token_text]
        person = self.__find_or_create_person(real_id)

        # set up the state for the parsing
        state = GedcomUtils.CurrentState(person=person, level=1)

        # do the actual parsing
        self.__parse_level(state, self.indi_parse_tbl, self.__person_event)

        # Add the default reference if no source has found
        self.__add_default_source(person)

        # commit the person to the database
        if person.change:
            self.dbase.commit_person(person, self.trans, 
                                     change_time=state.person.change)
        else:
            self.dbase.commit_person(person, self.trans)

    def __person_sour(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        source_ref = self.handle_source(line, state.level)
        state.person.add_source_reference(source_ref)

    def __person_attr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = gen.lib.Attribute()
        attr.set_type((gen.lib.AttributeType.CUSTOM, line.token_text))
        attr.set_value(line.data)
        state.person.add_attribute(attr)
        self.__skip_subordinate_levels(state.level+1)

    def __person_event(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self.__build_event_pair(state, gen.lib.EventType.CUSTOM, 
                                            self.event_parse_tbl, line.data)
        state.person.add_event_ref(event_ref)

    def __skip_record(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__skip_subordinate_levels(2)

    def __person_chan(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_change(line, state.person, state.level+1)
        
    def __person_resn(self, line, state):
        """
        Parses the RESN tag, adding it as an attribute.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = gen.lib.Attribute()
        attr.set_type((gen.lib.AttributeType.CUSTOM, 'RESN'))
        state.person.add_attribute(attr)

    def __person_alt_name(self, line, state):
        """
        Parse a altername name, usually indicated by a AKA or _AKA
        tag. This is not valid GEDCOM, but several programs will add
        this just to make life interesting. Odd, since GEDCOM supports
        multiple NAME indicators, which is the correct way of handling
        multiple names.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        name = GedcomUtils.parse_name_personal(line.data)
        name.set_type(gen.lib.NameType.AKA)
        state.person.add_alternate_name(name)

        # Create a new state, and parse the remainder of the NAME level
        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.name = name
        sub_state.level = 2

        self.__parse_level(sub_state,  self.name_parse_tbl, self.__undefined)

    def __person_object(self, line, state):
        """
        Currently, the embedded form is not supported
        
        Embedded form
        
        >   n OBJE @<XREF:OBJE>@ {1:1}

        Linked form
         
        >   n OBJE {1:1}
        >   +1 FORM <MULTIMEDIA_FORMAT> {1:1}
        >   +1 TITL <DESCRIPTIVE_TITLE> {0:1}
        >   +1 FILE <MULTIMEDIA_FILE_REFERENCE> {1:1}
        >   +1 <<NOTE_STRUCTURE>> {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            ref = gen.lib.MediaRef()
            handle = self.__find_object_handle(line.data[1:-1])
            ref.set_reference_handle(handle)
            state.person.add_media_reference(ref)
        else:
            (form, filename, title, note) = self.__obje(state.level+1)
            self.build_media_object(state.person, form, filename, title, note)

    def __person_name(self, line, state):
        """
        Parsers the NAME token in a GEDCOM file. The text is in the format
        of (according to the GEDCOM Spec):
        >   <TEXT>|/<TEXT>/|<TEXT>/<TEXT>/|/<TEXT>/<TEXT>|<TEXT>/<TEXT>/<TEXT>
        We have encountered some variations that use:
        >   <TEXT>/

        The basic Name structure is:

          n  NAME <NAME_PERSONAL> {1:1}
          +1 NPFX <NAME_PIECE_PREFIX> {0:1}
          +1 GIVN <NAME_PIECE_GIVEN> {0:1}
          +1 NICK <NAME_PIECE_NICKNAME> {0:1}
          +1 SPFX <NAME_PIECE_SURNAME_PREFIX {0:1}
          +1 SURN <NAME_PIECE_SURNAME> {0:1}
          +1 NSFX <NAME_PIECE_SUFFIX> {0:1}
          +1 <<SOURCE_CITATION>> {0:M}
          +1 <<NOTE_STRUCTURE>> {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """

        # build a gen.lib.Name structure from the text
        
        name = GedcomUtils.parse_name_personal(line.data)

        # Add the name as the primary name if this is the first one that
        # we have encountered for this person. Assume that if this is the
        # first name, that it is a birth name. Otherwise, label it as an
        # "Also Known As (AKA)". GEDCOM does not seem to have the concept
        # of different name types
        
        if state.name_cnt == 0:
            name.set_type(gen.lib.NameType.BIRTH)
            state.person.set_primary_name(name)
        else:
            name.set_type(gen.lib.NameType.AKA)
            state.person.add_alternate_name(name)
        state.name_cnt += 1

        # Create a new state, and parse the remainder of the NAME level
        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.name = name
        sub_state.level = state.level+1

        self.__parse_level(sub_state, self.name_parse_tbl, self.__undefined)

    def __person_sex(self, line, state):
        """
        Parses the SEX line of a GEDCOM file. It has the format of:

        +1 SEX <SEX_VALUE> {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.person.set_gender(line.data)

    def __person_even(self, line, state):
        """
        Parses the custom EVEN tag, which has the format of:

           n  <<EVENT_TYPE>> {1:1}
           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self.__build_event_pair(state, gen.lib.EventType.CUSTOM, 
                                           self.event_parse_tbl, line.data)
        state.person.add_event_ref(event_ref)

    def __person_std_event(self, line, state):
        """
        Parses GEDCOM event types that map to a GRAMPS standard type. Additional
        parsing required is for the event detail:

           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """

        event = line.data
        event.set_gramps_id(self.emapper.find_next())
        event_ref = gen.lib.EventRef()
        self.dbase.add_event(event, self.trans)

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level+1
        sub_state.event = event
        sub_state.event_ref = event_ref

        self.__parse_level(sub_state, self.event_parse_tbl, self.__undefined)

        self.dbase.commit_event(event, self.trans)
        event_ref.ref = event.handle
        state.person.add_event_ref(event_ref)

    def __person_reli(self, line, state):
        """
        Parses the RELI tag.

           n  RELI [Y|<NULL>] {1:1}
           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self.__build_event_pair(state, gen.lib.EventType.RELIGION, 
                                           self.event_parse_tbl, line.data)
        state.person.add_event_ref(event_ref)

    def __person_birt(self, line, state):
        """
        Parses GEDCOM BIRT tag into a GRAMPS birth event. Additional work
        must be done, since additional handling must be done by GRAMPS to set 
        this up as a birth reference event.

           n  BIRT [Y|<NULL>] {1:1}
           +1 <<EVENT_DETAIL>> {0:1} p.*
           +1 FAMC @<XREF:FAM>@ {0:1} p.*

        I'm not sure what value the FAMC actually offers here, since
        the FAMC record should handle this. Why it is a valid sub value
        is beyond me.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self.__build_event_pair(state, gen.lib.EventType.BIRTH, 
                                           self.event_parse_tbl, line.data)
        if state.person.get_birth_ref():
            state.person.add_event_ref(event_ref)
        else:
            state.person.set_birth_ref(event_ref)

    def __person_adop(self, line, state):
        """
        Parses GEDCOM ADOP tag, subordinate to the INDI tag. Additinal tags
        are needed by the tag, so we pass a different function map.

           n  ADOP [Y|<NULL>] {1:1}
           +1 <<EVENT_DETAIL>> {0:1} p.*
           +1 FAMC @<XREF:FAM>@ {0:1} p.*
           +2 ADOP <ADOPTED_BY_WHICH_PARENT> {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self.__build_event_pair(state, gen.lib.EventType.ADOPT, 
                                           self.adopt_parse_tbl, line.data)
        state.person.add_event_ref(event_ref)

    def __person_deat(self, line, state):
        """
        Parses GEDCOM DEAT tag into a GRAMPS birth event. Additional work
        must be done, since additional handling must be done by GRAMPS to set 
        this up as a death reference event.

           n  DEAT [Y|<NULL>] {1:1}
           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self.__build_event_pair(state, gen.lib.EventType.DEATH, 
                                           self.event_parse_tbl, line.data)
        if state.person.get_death_ref():
            state.person.add_event_ref(event_ref)
        else:
            state.person.set_death_ref(event_ref)

    def __person_note(self, line, state):
        """
        Parses a note associated with the person

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.person, 1)

    def __person_rnote(self, line, state):
        """
        Parses a note associated with the person

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.person, 1)

    def __person_addr(self, line, state):
        """
        Parses the Address structure

        n ADDR <ADDRESS_LINE> {0:1} 
        +1 CONT <ADDRESS_LINE> {0:M}
        +1 ADR1 <ADDRESS_LINE1> {0:1}
        +1 ADR2 <ADDRESS_LINE2> {0:1}
        +1 CITY <ADDRESS_CITY> {0:1}
        +1 STAE <ADDRESS_STATE> {0:1}
        +1 POST <ADDRESS_POSTAL_CODE> {0:1}
        +1 CTRY <ADDRESS_COUNTRY> {0:1}
        n PHON <PHONE_NUMBER> {0:3}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState()
        sub_state.level = state.level+1
        sub_state.addr = gen.lib.Address()
        sub_state.addr.set_street(line.data)
        state.person.add_address(sub_state.addr)
        self.__parse_level(sub_state, self.parse_addr_tbl, self.__ignore)

    def __person_phon(self, line, state):
        """
        n PHON <PHONE_NUMBER> {0:3}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        addr = gen.lib.Address()
        addr.set_street("Unknown")
        addr.set_phone(line.data)
        state.person.add_address(addr)

    def __person_titl(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event = gen.lib.Event()
        event_ref = gen.lib.EventRef()
        event.set_gramps_id(self.emapper.find_next())
        event.set_type(gen.lib.EventType.NOB_TITLE)
        event.set_description(line.data)

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level+1
        sub_state.event = event
        sub_state.event_ref = event_ref

        self.__parse_level(sub_state, self.event_parse_tbl, self.__undefined)

        self.dbase.add_event(event, self.trans)
        event_ref.ref = event.handle
        state.person.add_event_ref(event_ref)

    def __person_attr_plac(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if state.attr.get_value() == "":
            state.attr.set_value(line.data)

    def __name_type(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data == "_OTHN":
            state.name.set_type(gen.lib.NameType.AKA)
        else:
            state.name.set_type((gen.lib.NameType.CUSTOM, line.data))

    def __name_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.name, state.level+1)

    def __name_alia(self, line, state):
        """
        The ALIA tag is supposed to cross reference another person.
        However, we do not support this.

        Some systems use the ALIA tag as an alternate NAME tag, which
        is not legal in GEDCOM, but oddly enough, is easy to support.
        """
        if line.data[0] == '@':
            aka = GedcomUtils.parse_name_personal(line.data)
            state.person.add_alternate_name(aka)

    def __name_npfx(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.name.set_title(line.data.strip())
        self.__skip_subordinate_levels(state.level+1)

    def __name_givn(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.name.set_first_name(line.data.strip())
        self.__skip_subordinate_levels(state.level+1)

    def __name_spfx(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.name.set_surname_prefix(line.data.strip())
        self.__skip_subordinate_levels(state.level+1)

    def __name_surn(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.name.set_surname(line.data.strip())
        self.__skip_subordinate_levels(state.level+1)

    def __name_marnm(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        text = line.data.strip()
        data = text.split()
        if len(data) == 1:
            name = gen.lib.Name(state.person.primary_name)
            name.set_surname(data[0].strip())
            name.set_type(gen.lib.NameType.MARRIED)
            state.person.add_alternate_name(name)
        elif len(data) > 1:
            name = GedcomUtils.parse_name_personal(text)
            name.set_type(gen.lib.NameType.MARRIED)
            state.person.add_alternate_name(name)

    def __name_nsfx(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if state.name.get_suffix() == "":
            state.name.set_suffix(line.data)
        self.__skip_subordinate_levels(state.level+1)

    def __name_nick(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = gen.lib.Attribute()
        attr.set_type(gen.lib.AttributeType.NICKNAME)
        attr.set_value(line.data)
        state.person.add_attribute(attr)
        self.__skip_subordinate_levels(state.level+1)

    def __name_aka(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """        
        lname = line.data.split()
        name_len = len(lname)
        if name_len == 1:
            attr = gen.lib.Attribute()
            attr.set_type(gen.lib.AttributeType.NICKNAME)
            attr.set_value(line.data)
            state.person.add_attribute(attr)
        else:
            name = gen.lib.Name()
            name.set_surname(lname[-1].strip())
            name.set_first_name(' '.join(lname[0:name_len-1]))
            state.person.add_alternate_name(name)

    def __name_sour(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sref = self.handle_source(line, state.level)
        state.name.add_source_reference(sref)

    def __ignore(self, line, state):
        """
        Ignores an unsupported tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__skip_subordinate_levels(state.level+1)

    def __person_std_attr(self, line, state):
        """
        Parses an TOKEN that GRAMPS recognizes as an Attribute

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.attr = line.data
        sub_state.level = state.level+1
        state.person.add_attribute(sub_state.attr)
        self.__parse_level(sub_state, self.person_attr_parse_tbl, 
                         self.__ignore)

    def __person_fact(self, line, state):
        """
        Parses an TOKEN that GRAMPS recognizes as an Attribute

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.attr = gen.lib.Attribute()
        sub_state.attr.set_value(line.data)
        sub_state.level = state.level+1
        state.person.add_attribute(sub_state.attr)
        self.__parse_level(sub_state, self.person_fact_parse_tbl, 
                         self.__ignore)

    def __person_fact_type(self, line, state):
        state.attr.set_type(line.data)
        self.__skip_subordinate_levels(state.level)
        
    def __person_bapl(self, line, state):
        """
        Parses an BAPL TOKEN, producing a GRAMPS LdsOrd instance

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.build_lds_ord(state, gen.lib.LdsOrd.BAPTISM)

    def __person_conl(self, line, state):
        """
        Parses an CONL TOKEN, producing a GRAMPS LdsOrd instance

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.build_lds_ord(state, gen.lib.LdsOrd.CONFIRMATION)

    def __person_endl(self, line, state):
        """
        Parses an ENDL TOKEN, producing a GRAMPS LdsOrd instance

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.build_lds_ord(state, gen.lib.LdsOrd.ENDOWMENT)

    def __person_slgc(self, line, state):
        """
        Parses an SLGC TOKEN, producing a GRAMPS LdsOrd instance

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.build_lds_ord(state, gen.lib.LdsOrd.SEAL_TO_PARENTS)

    def build_lds_ord(self, state, lds_type):
        """
        Parses an LDS ordinance, using the type passed to the routine

        @param state: The current state
        @type state: CurrentState
        @param lds_type: The type of the LDS ordinance
        @type line: LdsOrd type
        """
        sub_state = GedcomUtils.CurrentState()
        sub_state.level = state.level + 1
        sub_state.lds_ord = gen.lib.LdsOrd()
        sub_state.lds_ord.set_type(lds_type)
        sub_state.place = None
        sub_state.place_fields = GedcomUtils.PlaceParser()
        sub_state.person = state.person
        state.person.lds_ord_list.append(sub_state.lds_ord)

        self.__parse_level(sub_state, self.lds_parse_tbl, self.__ignore)

        if sub_state.place:
            sub_state.place_fields.load_place(sub_state.place, 
                                              sub_state.place.get_title())

    def __lds_temple(self, line, state):
        """
        Parses the TEMP tag, looking up the code for a match.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        value = self.__extract_temple(line)
        if value:
            state.lds_ord.set_temple(value)

    def __lds_date(self, line, state): 
        """
        Parses the DATE tag for the LdsOrd

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.lds_ord.set_date_object(line.data)

    def __lds_famc(self, line, state):
        """
        Parses the FAMC tag attached to the LdsOrd

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        gid = self.fid_map[line.data]
        state.lds_ord.set_family_handle(self.__find_family_handle(gid))

    def __lds_form(self, line, state): 
        """
        Parses the FORM tag thate defines the place structure for a place. 
        This tag, if found, will override any global place structure.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.pf = GedcomUtils.PlaceParser(line)

    def __lds_plac(self, line, state):
        """
        Parses the PLAC tag attached to the LdsOrd. Create a new place if
        needed and set the title.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        try:
            state.place = self.__find_or_create_place(line.data)
            state.place.set_title(line.data)
            state.lds_ord.set_place_handle(state.place.handle)
        except NameError:
            return

    def __lds_sour(self, line, state):
        """
        Parses the SOUR tag attached to the LdsOrd. 

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        srcref = self.handle_source(line, state.level)
        state.lds_ord.add_source_reference(srcref)

    def __lds_note(self, line, state):
        """
        Parses the NOTE tag attached to the LdsOrd. 

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.lds_ord, state.level+1)

    def __lds_stat(self, line, state): 
        """
        Parses the STAT (status) tag attached to the LdsOrd. 

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        status = GedcomInfo.lds_status.get(line.data, gen.lib.LdsOrd.STATUS_NONE)
        state.lds_ord.set_status(status)

    def __person_famc(self, line, state):
        """
        Handles the parsing of the FAMC line, which indicates which family the
        person is a child of.

        n FAMC @<XREF:FAM>@ {1:1}
        +1 PEDI <PEDIGREE_LINKAGE_TYPE> {0:M} p.*
        +1 <<NOTE_STRUCTURE>> {0:M} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level + 1
        sub_state.ftype = None
        sub_state.primary = False

        gid = self.fid_map[line.data]
        handle = self.__find_family_handle(gid)

        self.__parse_level(sub_state, self.famc_parse_tbl, self.__undefined)

        # if the handle is not already in the person's parent family list, we
        # need to add it to thie list.

        flist = [fam[0] for fam in state.person.get_parent_family_handle_list()]
        if not handle in flist:
            if sub_state.ftype and int(sub_state.ftype) in RELATION_TYPES:
                state.person.add_parent_family_handle(handle)
            else:
                if state.person.get_main_parents_family_handle() == handle:
                    state.person.set_main_parent_family_handle(None)
                state.person.add_parent_family_handle(handle)

            # search childrefs
            family, new = self.dbase.find_family_from_handle(handle, self.trans)
            family.set_gramps_id(gid)
                
            for ref in family.get_child_ref_list():
                if ref.ref == state.person.handle:
                    if sub_state.ftype:
                        ref.set_mother_relation(sub_state.ftype)
                        ref.set_father_relation(sub_state.ftype)
                    break
            else:
                ref = gen.lib.ChildRef()
                ref.ref = state.person.handle
                if sub_state.ftype:
                    ref.set_mother_relation(sub_state.ftype)
                    ref.set_father_relation(sub_state.ftype)
                family.add_child_ref(ref)
            self.dbase.commit_family(family, self.trans)

    def __person_famc_pedi(self, line, state): 
        """
        Parses the PEDI tag attached to a INDI.FAMC record. No values are set
        at this point, because we have to do some post processing. Instead, we
        assign the ftype field of the state variable. We convert the text from
        the line to an index into the PEDIGREE_TYPES dictionary, which will map
        to the correct ChildTypeRef.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.ftype = PEDIGREE_TYPES.get(line.data.lower(), 
                                         gen.lib.ChildRefType.UNKNOWN)

    def __person_famc_note(self, line, state):
        """
        Parses the INDI.FAMC.NOTE tag .

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.person, state.level+1)

    def __person_famc_primary(self, line, state): 
        """
        Parses the _PRIM tag on an INDI.FAMC tag. This value is stored in 
        the state record to be used later.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.primary = True

    def __person_famc_sour(self, line, state):
        """
        Parses the SOUR tag on an INDI.FAMC tag. GRAMPS has no corresponding
        record on its family relationship, so we add the source to the Person
        record.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        source_ref = self.handle_source(line, state.level)
        state.person.add_source_reference(source_ref)

    def __person_fams(self, line, state):
        """
        Parses the INDI.FAMS record, which indicates the family in which the
        person is a spouse.

        n FAMS @<XREF:FAM>@ {1:1} p.*
        +1 <<NOTE_STRUCTURE>> {0:M} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        handle = self.__find_family_handle(self.fid_map[line.data])
        state.person.add_family_handle(handle)

        sub_state = GedcomUtils.CurrentState(level=state.level+1)
        sub_state.obj = state.person
        self.__parse_level(sub_state, self.opt_note_tbl, self.__ignore)

    def __person_asso(self, line, state):
        """
        Parse the ASSO tag, add the the referenced person to the person we
        are currently parsing. The GEDCOM spec indicates that valid ASSO tag
        is:
        
        n ASSO @<XREF:INDI>@ {0:M}
           
        And the the sub tags are:
        
        ASSOCIATION_STRUCTURE:=
         +1 RELA <RELATION_IS_DESCRIPTOR> {1:1}
         +1 <<NOTE_STRUCTURE>> {0:M}
         +1 <<SOURCE_CITATION>> {0:M}

        The Gedcom spec notes that the ASSOCIATION_STRUCTURE 
        can only link to an INDIVIDUAL_RECORD

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """

        # find the id and person that we are referencing
        handle = self.__find_person_handle(self.pid_map[line.data])

        # create a new PersonRef, and assign the handle, add the
        # PersonRef to the active person

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level + 1
        sub_state.ref = gen.lib.PersonRef()
        sub_state.ref.ref = handle
        sub_state.ignore = False

        self.__parse_level(sub_state, self.asso_parse_tbl, self.__ignore)
        if not sub_state.ignore:
            state.person.add_person_ref(sub_state.ref)

    def __person_asso_rela(self, line, state): 
        """
        Parses the INDI.ASSO.RELA tag.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.ref.rel = line.data

    def __person_asso_sour(self, line, state):
        """
        Parses the INDI.ASSO.SOUR tag.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.ref.add_source_reference(self.handle_source(line, state.level))

    def __person_asso_note(self, line, state):
        """
        Parses the INDI.ASSO.NOTE tag.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.ref, state.level)

    #-------------------------------------------------------------------
    # 
    # Family parsing
    #
    #-------------------------------------------------------------------
        
    def __parse_fam(self, line):
        """
          n @<XREF:FAM>@   FAM   {1:1}
          +1 <<FAMILY_EVENT_STRUCTURE>>  {0:M}
          +1 HUSB @<XREF:INDI>@  {0:1}
          +1 WIFE @<XREF:INDI>@  {0:1}
          +1 CHIL @<XREF:INDI>@  {0:M}
          +1 NCHI <COUNT_OF_CHILDREN>  {0:1}
          +1 SUBM @<XREF:SUBM>@  {0:M}
          +1 <<LDS_SPOUSE_SEALING>>  {0:M}
          +1 <<SOURCE_CITATION>>  {0:M}
          +1 <<MULTIMEDIA_LINK>>  {0:M}
          +1 <<NOTE_STRUCTURE>>  {0:M}
          +1 REFN <USER_REFERENCE_NUMBER>  {0:M}
          +1 RIN <AUTOMATED_RECORD_ID>  {0:1}
          +1 <<CHANGE_DATE>>  {0:1}
        """
        # create a family
        
        family = self.__find_or_create_family(self.fid_map[line.token_text])

        # parse the family

        state = GedcomUtils.CurrentState(level=1)
        state.family = family

        self.__parse_level(state, self.family_func, self.__family_even)

        # handle addresses attached to families
        if state.addr is not None:
            father_handle = family.get_father_handle()
            father = self.dbase.get_person_from_handle(father_handle)
            if father:
                father.add_address(state.addr)
                self.dbase.commit_person(father, self.trans)
            mother_handle = family.get_mother_handle()
            mother = self.dbase.get_person_from_handle(mother_handle)
            if mother:
                mother.add_address(state.addr)
                self.dbase.commit_person(mother, self.trans)

            for child_ref in family.get_child_ref_list():
                child_handle = child_ref.ref
                child = self.dbase.get_person_from_handle(child_handle)
                if child:
                    child.add_address(state.addr)
                    self.dbase.commit_person(child, self.trans)

        # add default reference if no reference exists
        self.__add_default_source(family)

        # commit family to database
        if family.change:
            self.dbase.commit_family(family, self.trans, 
                                  change_time=family.change)
        else:
            self.dbase.commit_family(family, self.trans)
    
    def __family_husb(self, line, state):
        """
        Parses the husband line of a family

        n HUSB @<XREF:INDI>@  {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
            """
        handle = self.__find_person_handle(self.pid_map[line.data])
        state.family.set_father_handle(handle)

    def __family_wife(self, line, state):
        """
            Parses the wife line of a family

              n WIFE @<XREF:INDI>@  {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
            """
        handle = self.__find_person_handle(self.pid_map[line.data])
        state.family.set_mother_handle(handle)

    def __family_std_event(self, line, state):
        """
        Parses GEDCOM event types that map to a GRAMPS standard type. Additional
        parsing required is for the event detail:

           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event = line.data
        event.set_gramps_id(self.emapper.find_next())
        event_ref = gen.lib.EventRef()
        event_ref.set_role(gen.lib.EventRoleType.FAMILY)
        self.dbase.add_event(event, self.trans)

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level+1
        sub_state.event = event
        sub_state.event_ref = event_ref

        self.__parse_level(sub_state, self.event_parse_tbl, self.__undefined)

        if event.type == gen.lib.EventType.MARRIAGE:
            descr = event.get_description()
            if descr == "Civil Union":
                state.family.type.set(gen.lib.FamilyRelType.CIVIL_UNION)
                event.set_description('')
            elif descr == "Unmarried":
                state.family.type.set(gen.lib.FamilyRelType.UNMARRIED)
                event.set_description('')
            else:
                state.family.type.set(gen.lib.FamilyRelType.MARRIED)

        self.dbase.commit_event(event, self.trans)
        event_ref.ref = event.handle
        state.family.add_event_ref(event_ref)

    def __family_even(self, line, state):
        """
        Parses GEDCOM event types that map to a GRAMPS standard type. Additional
        parsing required is for the event detail:

           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event = gen.lib.Event()
        event_ref = gen.lib.EventRef()
        event_ref.set_role(gen.lib.EventRoleType.FAMILY)
        event.set_gramps_id(self.emapper.find_next())
        event.set_type(line.data)
        self.dbase.add_event(event, self.trans)

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level+1
        sub_state.event = event
        sub_state.event_ref = event_ref

        self.__parse_level(sub_state, self.event_parse_tbl, self.__undefined)

        self.dbase.commit_event(event, self.trans)
        event_ref.ref = event.handle
        state.family.add_event_ref(event_ref)

    def __family_chil(self, line, state):
        """
        Parses the child line of a family

        n CHIL @<XREF:INDI>@  {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState()
        sub_state.family = state.family
        sub_state.level = state.level + 1
        sub_state.mrel = None
        sub_state.frel = None

        self.__parse_level(sub_state, self.family_rel_tbl, self.__ignore)

        child = self.__find_or_create_person(self.pid_map[line.data])

        reflist = [ ref for ref in state.family.get_child_ref_list() \
                    if ref.ref == child.handle ]

        if reflist:
            ref = reflist[0]
            if sub_state.frel:
                ref.set_father_relation(sub_state.frel)
            if sub_state.mrel:
                ref.set_mother_relation(sub_state.mrel)
        else:
            ref = gen.lib.ChildRef()
            ref.ref = child.handle
            if sub_state.frel:
                ref.set_father_relation(sub_state.frel)
            if sub_state.mrel:
                ref.set_mother_relation(sub_state.mrel)
            state.family.add_child_ref(ref)

    def __family_slgs(self, line, state):
        """
        n  SLGS          {1:1}
        +1 STAT <LDS_SPOUSE_SEALING_DATE_STATUS>  {0:1}
        +1 DATE <DATE_LDS_ORD>  {0:1}
        +1 TEMP <TEMPLE_CODE>  {0:1}
        +1 PLAC <PLACE_LIVING_ORDINANCE>  {0:1}
        +1 <<SOURCE_CITATION>>  {0:M}
        +1 <<NOTE_STRUCTURE>>  {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
            """
        sub_state = GedcomUtils.CurrentState()
        sub_state.level = state.level + 1
        sub_state.lds_ord = gen.lib.LdsOrd()
        sub_state.lds_ord.set_type(gen.lib.LdsOrd.SEAL_TO_SPOUSE)
        sub_state.place = None
        sub_state.family = state.family
        sub_state.place_fields = GedcomUtils.PlaceParser()
        state.family.lds_ord_list.append(sub_state.lds_ord)

        self.__parse_level(sub_state, self.lds_parse_tbl, self.__ignore)

        if sub_state.place:
            sub_state.place_fields.load_place(sub_state.place, 
                                              sub_state.place.get_title())

    def __family_source(self, line, state):
        """
        n SOUR @<XREF:SOUR>@ /* pointer to source record */ {1:1} p.*
        +1 PAGE <WHERE_WITHIN_SOURCE> {0:1} p.*
        +1 EVEN <EVENT_TYPE_CITED_FROM> {0:1} p.*
        +1 DATA {0:1}
        +1 QUAY <CERTAINTY_ASSESSMENT> {0:1} p.*
        +1 <<MULTIMEDIA_LINK>> {0:M} p.*, *
        +1 <<NOTE_STRUCTURE>> {0:M} p.*

        | /* Systems not using source records */
        n SOUR <SOURCE_DESCRIPTION> {1:1} p.*
        +1 [ CONC | CONT ] <SOURCE_DESCRIPTION> {0:M}
        +1 TEXT <TEXT_FROM_SOURCE> {0:M} p.*
        +1 <<NOTE_STRUCTURE>> {0:M} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        source_ref = self.handle_source(line, state.level)
        state.family.add_source_reference(source_ref)

    def __family_object(self, line, state):
        """
          +1 <<MULTIMEDIA_LINK>>  {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            self.__not_recognized(line, state.level)
        else:
            (form, filename, title, note) = self.__obje(state.level + 1)
            self.build_media_object(state.family, form, filename, title, note)

    def __family_comm(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        note = line.data
        state.family.add_note(note)
        self.__skip_subordinate_levels(state.level+1)

    def __family_note(self, line, state):
        """
        +1 <<NOTE_STRUCTURE>>  {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.family, state.level)

    def __family_chan(self, line, state):
        """
        +1 <<CHANGE_DATE>>  {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_change(line, state.family, state.level+1)

    def __family_addr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr = gen.lib.Address()
        state.addr.set_street(line.data)
        self.__parse_level(state, self.parse_addr_tbl, self.__ignore)

    def __family_attr(self, line, state): 
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.family.add_attribute(line.data)

    def __family_cust_attr(self, line, state): 
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = gen.lib.Attribute()
        attr.set_type(line.token_text)
        attr.set_value(line.data)
        state.family.add_attribute(attr)

    def __obje(self, level):
        """
          n  OBJE {1:1}
          +1 FORM <MULTIMEDIA_FORMAT> {1:1}
          +1 TITL <DESCRIPTIVE_TITLE> {0:1}
          +1 FILE <MULTIMEDIA_FILE_REFERENCE> {1:1}
          +1 <<NOTE_STRUCTURE>> {0:M} 

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState()
        sub_state.form = ""
        sub_state.filename = ""
        sub_state.title = ""
        sub_state.note = ""
        sub_state.level = level

        self.__parse_level(sub_state, self.object_parse_tbl, self.__ignore)
        return (sub_state.form, sub_state.filename, sub_state.title, 
                sub_state.note)

    def __object_ref_form(self, line, state): 
        """
          +1 FORM <MULTIMEDIA_FORMAT> {1:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.form = line.data

    def __object_ref_titl(self, line, state): 
        """
          +1 TITL <DESCRIPTIVE_TITLE> {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.title = line.data

    def __object_ref_file(self, line, state): 
        """
          +1 FILE <MULTIMEDIA_FILE_REFERENCE> {1:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.filename = line.data

    def __object_ref_note(self, line, state): 
        """
          +1 <<NOTE_STRUCTURE>> {0:M} 

          TODO: Fix this for full reference

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.note = line.data

    def __family_adopt(self, line, state):
        """
        n ADOP

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.frel = TYPE_ADOPT
        state.mrel = TYPE_ADOPT

    def __family_frel(self, line, state):
        """
        The _FREL key is a FTW specific extension to indicate father/child
        relationship.

        n _FREL <type>

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.frel = PEDIGREE_TYPES.get(line.data.strip().lower())

    def __family_mrel(self, line, state):
        """
        The _MREL key is a FTW specific extension to indicate father/child
        relationship.

        n _MREL <type>

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.mrel = PEDIGREE_TYPES.get(line.data.strip().lower())

    def __family_stat(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.mrel = TYPE_BIRTH
        state.frel = TYPE_BIRTH

    def __event_object(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            self.__not_recognized(line, state.level)
        else:
            (form, filename, title, note) = self.__obje(state.level + 1)
            self.build_media_object(state.event, form, filename, title, note)

    def __event_type(self, line, state):
        """
        Parses the TYPE line for an event.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if state.event.get_type().is_custom():
            if line.data in GED_2_GRAMPS:
                name = gen.lib.EventType(GED_2_GRAMPS[line.data])
            else:
                val = self.gedsource.tag2gramps(line.data)
                if val:
                    name = gen.lib.EventType((gen.lib.EventType.CUSTOM, val))
                else:
                    try:
                        name = gen.lib.EventType((gen.lib.EventType.CUSTOM, 
                                                 line.data))
                    except AttributeError:
                        name = gen.lib.EventType(gen.lib.EventType.UNKNOWN)
            state.event.set_type(name)
        else:
            try:
                if line.data not in GED_2_GRAMPS and \
                       line.data not in GED_2_FAMILY and \
                       line.data[0] != 'Y':
                    state.event.set_description(line.data)
            except IndexError:
                return

    def __event_date(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.event.set_date_object(line.data)

    def __event_place(self, line, state):
        """
        Parse the place portion of a event. A special case has to be made for
        Family Tree Maker, which violates the GEDCOM spec. It uses the PLAC 
        field to store the description or value assocated with the event.

         n  PLAC <PLACE_VALUE> {1:1}
         +1 FORM <PLACE_HIERARCHY> {0:1}
         +1 <<SOURCE_CITATION>> {0:M}
         +1 <<NOTE_STRUCTURE>> {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """

        if self.is_ftw and state.event.type in FTW_BAD_PLACE:
            state.event.set_description(line.data)
        else:
            place = self.__find_or_create_place(line.data)
            place.set_title(line.data)
            state.event.set_place_handle(place.handle)

            sub_state = GedcomUtils.CurrentState()
            sub_state.place = place
            sub_state.level = state.level+1
            sub_state.pf = self.place_parser

            self.__parse_level(sub_state, self.event_place_map, 
                             self.__undefined)

            sub_state.pf.load_place(place, place.get_title())
            self.dbase.commit_place(place, self.trans)

    def __event_place_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.place, state.level+1)

    def __event_place_form(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.pf = GedcomUtils.PlaceParser(line)

    def __event_place_object(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            self.__not_recognized(line, state.level)
        else:
            (form, filename, title, note) = self.__obje(state.level)
            self.build_media_object(state.place, form, filename, title, note)

    def __event_place_sour(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.place.add_source_reference(self.handle_source(line, state.level))

    def __place_map(self, line, state):
        """
        
        n   MAP
        n+1 LONG <PLACE_LONGITUDE>
        n+1 LATI <PLACE_LATITUDE>
        
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState()
        sub_state.level = state.level + 1
        sub_state.place = state.place
        self.__parse_level(sub_state, self.place_map_tbl, self.__undefined)
        state.place = sub_state.place

    def __place_lati(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.place.set_latitude( line.data)

    def __place_long(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.place.set_longitude( line.data)

    def __event_addr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState(level=state.level+1)
        sub_state.location = gen.lib.Location()
        sub_state.location.set_street(line.data)
        sub_state.note = []
        sub_state.event = state.event

        self.__parse_level(sub_state, self.parse_loc_tbl, self.__undefined)

        location = sub_state.location
        note_list = sub_state.note

        place_handle = state.event.get_place_handle()
        if place_handle:
            place = self.dbase.get_place_from_handle(place_handle)
            index = place.get_title() + location.get_street()

            old_title = place.get_title()
            place = self.__find_or_create_place(index)
            if place.get_title():
                place.set_title(old_title)
                place_handle = place.handle
                place.set_main_location(location)
        else:
            place = self.__find_or_create_place(line.data)
            place.set_title(line.data)
            place_handle = place.handle
            place.set_main_location(location)

        for note in note_list:
            place.add_note(note)

        state.event.set_place_handle(place_handle)
        self.dbase.commit_place(place, self.trans)

    def __event_privacy(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.event.set_privacy(True)

    def __event_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.event, state.level+1)

    def __event_inline_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data[0:13] == "Description: ":
            state.event.set_description(line.data[13:])
        else:
            if not line.data:
                # empty: discard, with warning and skip subs
                # Note: level+2
                msg = _("Line %d: empty event note was ignored.")\
                        % line.line
                self.__warn(msg)
                self.__skip_subordinate_levels(state.level+2)
            else:
                new_note = gen.lib.Note(line.data)
                new_note.set_handle(Utils.create_id())
                self.dbase.add_note(new_note, self.trans)
                self.__skip_subordinate_levels(state.level+2)
                state.event.add_note(new_note.get_handle())
                
    def __event_source(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.event.add_source_reference(self.handle_source(line, state.level))

    def __event_cause(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = gen.lib.Attribute()
        attr.set_type(gen.lib.AttributeType.CAUSE)
        attr.set_value(line.data)
        state.event.add_attribute(attr)

        sub_state = GedcomUtils.CurrentState()
        sub_state.event = state.event
        sub_state.level = state.level + 1
        sub_state.attr = attr

        self.__parse_level(sub_state, self.event_cause_tbl, self.__undefined)

    def __event_cause_source(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.attr.add_source_reference(self.handle_source(line, state.level))

    def __event_age(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = gen.lib.Attribute()
        attr.set_type(gen.lib.AttributeType.AGE)
        attr.set_value(line.data)
        state.event_ref.add_attribute(attr)

    def __event_husb(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        while True:
            line = self.__get_next_line()
            if self.__level_is_finished(line, state.level):
                break
            elif line.token == TOKEN_AGE:
                attr = gen.lib.Attribute()
                attr.set_type(gen.lib.AttributeType.FATHER_AGE)
                attr.set_value(line.data)
                state.event_ref.add_attribute(attr)

    def __event_wife(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        while True:
            line = self.__get_next_line()
            if self.__level_is_finished(line, state.level):
                break
            elif line.token == TOKEN_AGE:
                attr = gen.lib.Attribute()
                attr.set_type(gen.lib.AttributeType.MOTHER_AGE)
                attr.set_value(line.data)
                state.event_ref.add_attribute(attr)

    def __event_agnc(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = gen.lib.Attribute()
        attr.set_type(gen.lib.AttributeType.AGENCY)
        attr.set_value(line.data)
        state.event.add_attribute(attr)

    def __event_witness(self, line, state):
        """
        Parse the witness of an event

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == "@":
            # n  _WITN @<XREF:INDI>@
            # +1 TYPE <TYPE_OF_RELATION>
            assert( state.event.handle)  # event handle is required to be set
            wit = self.__find_or_create_person(self.pid_map[line.data])
            event_ref = gen.lib.EventRef()
            event_ref.set_reference_handle(state.event.handle)
            while True:
                line = self.__get_next_line()
                if self.__level_is_finished(line, state.level+1):
                    break
                elif line.token == TOKEN_TYPE:
                    if line.data in ("WITNESS_OF_MARRIAGE"):
                        role = gen.lib.EventRoleType(
                            gen.lib.EventRoleType.WITNESS)
                    else:
                        role = gen.lib.EventRoleType(
                            (gen.lib.EventRoleType.CUSTOM, line.data))
                    event_ref.set_role(role)
            wit.add_event_ref(event_ref)
            self.dbase.commit_person(wit, self.trans)
        else:
            # n _WITN <TEXTUAL_LIST_OF_NAMES>
            attr = gen.lib.Attribute()
            attr.set_type(gen.lib.AttributeType.WITNESS)
            attr.set_value(line.data)
            state.event.add_attribute(attr)
        
    def __person_adopt_famc(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        gid = self.fid_map[line.data]
        handle = self.__find_family_handle(gid)
        family = self.__find_or_create_family(gid)

        sub_state = GedcomUtils.CurrentState(level=state.level+1)
        sub_state.mrel = TYPE_BIRTH
        sub_state.frel = TYPE_BIRTH

        self.__parse_level(sub_state, self.parse_person_adopt, 
                         self.__undefined)

        if (int(sub_state.mrel) == gen.lib.ChildRefType.BIRTH  and
            int(sub_state.frel) == gen.lib.ChildRefType.BIRTH):
            sub_state.mrel = sub_state.frel = TYPE_ADOPT

        if state.person.get_main_parents_family_handle() == handle:
            state.person.set_main_parent_family_handle(None)
        state.person.add_parent_family_handle(handle)
        
        reflist = [ ref for ref in family.get_child_ref_list() \
                        if ref.ref == state.person.handle ]
        if reflist:
            ref = reflist[0]
            ref.set_father_relation(sub_state.frel)
            ref.set_mother_relation(sub_state.mrel)
        else:
            ref = gen.lib.ChildRef()
            ref.ref = state.person.handle
            ref.set_father_relation(sub_state.frel)
            ref.set_mother_relation(sub_state.mrel)
            family.add_child_ref(ref)
            self.dbase.commit_family(family, self.trans)

    def __person_adopt_famc_adopt(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data.strip() == "HUSB":
            state.frel = TYPE_ADOPT
        elif line.data.strip() == "WIFE":
            state.mrel = TYPE_ADOPT
        else:
            state.mrel = TYPE_ADOPT
            state.frel = TYPE_ADOPT

    def __person_birth_famc(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        handle = self.__find_family_handle(self.fid_map[line.data])

        if state.person.get_main_parents_family_handle() == handle:
            state.person.set_main_parent_family_handle(None)
        state.person.add_parent_family_handle(handle)
        
        frel = mrel = gen.lib.ChildRefType.BIRTH

        family, new = self.dbase.find_family_from_handle(handle, self.trans)
        reflist = [ ref for ref in family.get_child_ref_list() \
                        if ref.ref == state.person.handle ]
        if reflist:
            ref = reflist[0]
            ref.set_father_relation(frel)
            ref.set_mother_relation(mrel)
        else:
            ref = gen.lib.ChildRef()
            ref.ref = state.person.handle
            ref.set_father_relation(frel)
            ref.set_mother_relation(mrel)
            family.add_child_ref(ref)
            self.dbase.commit_family(family, self.trans)

    def __address_date(self, line, state):
        """
        Parses the DATE line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_date_object(line.data)

    def __address_city(self, line, state):
        """
        Parses the CITY line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_city(line.data)

    def __address_state(self, line, state):
        """
        Parses the STAE line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_state(line.data)

    def __address_post(self, line, state):
        """
        Parses the POST line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_postal_code(line.data)
            
    def __address_country(self, line, state):
        """
        Parses the country line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_country(line.data)
    
    def __address_phone(self, line, state):
        """
        Parses the PHON line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_phone(line.data)
            
    def __address_sour(self, line, state):
        """
        Parses the SOUR line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.add_source_reference(self.handle_source(line, state.level))
            
    def __address_note(self, line, state):
        """
        Parses the NOTE line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.addr, state.level+1)

    def __srcref_page(self, line, state):
        """
        Parses the PAGE line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.src_ref.set_page(line.data)

    def __srcref_date(self, line, state):
        """
        Parses the DATE line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.src_ref.set_date_object(line.data)

    def __srcref_data(self, line, state): 
        """
        Parses the DATA line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState(level=state.level+1)
        sub_state.src_ref = state.src_ref

        self.__parse_level(sub_state, self.srcref_data_tbl, self.__undefined)

    def __srcref_data_date(self, line, state):
        state.src_ref.set_date_object(line.data)

    def __source_text(self, line, state):
        note = gen.lib.Note()
        note.set(line.data)
        gramps_id = self.dbase.find_next_note_gramps_id()
        note.set_gramps_id(gramps_id)
        note.set_type(gen.lib.NoteType.SOURCE_TEXT)
        self.dbase.add_note(note, self.trans)

        state.source.add_note(note.get_handle())

    def __srcref_data_text(self, line, state):
        note = gen.lib.Note()
        note.set(line.data)
        gramps_id = self.dbase.find_next_note_gramps_id()
        note.set_gramps_id(gramps_id)
        note.set_type(gen.lib.NoteType.SOURCE_TEXT)
        self.dbase.add_note(note, self.trans)

        state.src_ref.add_note(note.get_handle())

    def __srcref_data_note(self, line, state):
        self.__parse_note(line, state.src_ref, state.level)

    def __srcref_obje(self, line, state): 
        """
        Parses the OBJE line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            self.__not_recognized(line, state.level)
        else:
            src = self.dbase.get_source_from_handle(state.handle)
            (form, filename, title, note) = self.__obje(state.level)
            self.build_media_object(src, form, filename, title, note)
            self.dbase.commit_source(src, self.trans)

    def __srcref_refn(self, line, state): 
        """
        Parses the REFN line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__skip_subordinate_levels(state.level+1)

    def __srcref_quay(self, line, state): 
        """
        Parses the QUAY line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        try:
            val = int(line.data)
        except ValueError:
            return
        # If value is greater than 3, cap at 3
        val = min(val, 3)
        if val > 1:
            state.src_ref.set_confidence_level(val+1)
        else:
            state.src_ref.set_confidence_level(val)

    def __srcref_note(self, line, state): 
        """
        Parses the NOTE line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.src_ref, state.level+1)

    def __parse_source(self, name, level):
        """
          n @<XREF:SOUR>@ SOUR {1:1}
          +1 DATA {0:1}
          +2 EVEN <EVENTS_RECORDED> {0:M}
          +3 DATE <DATE_PERIOD> {0:1} 
          +3 PLAC <SOURCE_JURISDICTION_PLACE> {0:1}
          +2 AGNC <RESPONSIBLE_AGENCY> {0:1}
          +2 <<NOTE_STRUCTURE>> {0:M}
          +1 AUTH <SOURCE_ORIGINATOR> {0:1}
          +1 TITL <SOURCE_DESCRIPTIVE_TITLE> {0:1}
          +1 ABBR <SOURCE_FILED_BY_ENTRY> {0:1}
          +1 PUBL <SOURCE_PUBLICATION_FACTS> {0:1}
          +1 TEXT <TEXT_FROM_SOURCE> {0:1}
          +1 <<SOURCE_REPOSITORY_CITATION>> {0:1} 
          +1 <<MULTIMEDIA_LINK>> {0:M} 
          +1 <<NOTE_STRUCTURE>> {0:M}
          +1 REFN <USER_REFERENCE_NUMBER> {0:M}
          +2 TYPE <USER_REFERENCE_TYPE> {0:1}
          +1 RIN <AUTOMATED_RECORD_ID> {0:1}
          +1 <<CHANGE_DATE>> {0:1}
        """

        state = GedcomUtils.CurrentState()
        state.source = self.__find_or_create_source(self.sid_map[name]) 
        state.source.set_title("No title - ID %s" % 
                               state.source.get_gramps_id())
        state.level = level

        self.__parse_level(state, self.source_func, self.__undefined)
        self.dbase.commit_source(state.source, self.trans)

    def __source_attr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.source.set_data_item(line.token_text, line.data)

    def __source_object(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            self.__not_recognized(line, state.level)
        else:
            (form, filename, title, note) = self.__obje(state.level+1)
            self.build_media_object(state.source, form, filename, title, note)

    def __source_chan(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_change(line, state.source, state.level+1)

    def __source_undef(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__not_recognized(line, state.level+1)

    def __source_repo(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            gid = self.rid_map[line.data]
            repo = self.__find_or_create_repository(gid)
        else:
            gid = self.repo2id.get(line.data)
            repo = self.__find_or_create_repository(gid)
            self.repo2id[line.data] = repo.get_gramps_id()
            repo.set_name(line.data)
            self.dbase.commit_repository(repo, self.trans)
        repo_ref = gen.lib.RepoRef()
        repo_ref.set_reference_handle(repo.handle)

        sub_state = GedcomUtils.CurrentState()
        sub_state.repo_ref = repo_ref
        sub_state.level = state.level + 1

        self.__parse_level(sub_state, self.repo_ref_tbl, self.__undefined)

        state.source.add_repo_reference(repo_ref)

    def __repo_ref_call(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.repo_ref.set_call_number(line.data)
        self.__skip_subordinate_levels(state.level+1)

    def __repo_ref_medi(self, line, state):
        name = line.data
        mtype = MEDIA_MAP.get(name.lower(), 
                              (gen.lib.SourceMediaType.CUSTOM, name))
        state.repo_ref.set_media_type(mtype)

    def __repo_ref_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.repo_ref, state.level+1)

    def __source_abbr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.source.set_abbreviation(line.data)

    def __source_agnc(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = gen.lib.Attribute()
        attr.set_type(gen.lib.AttributeType.AGENCY)
        attr.set_value(line.data)
        state.source.add_attribute(attr)

    def __source_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.source, state.level+1)

    def __source_auth(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.source.set_author(line.data)

    def __source_publ(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.source.set_publication_info(line.data)
        self.__skip_subordinate_levels(state.level+1)

    def __source_title(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.source.set_title(line.data.replace('\n', ' '))

    def __source_taxt_peri(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if state.source.get_title() == "":
            state.source.set_title(line.data.replace('\n', ' '))

    def __parse_obje(self, line):
        """
           n  @XREF:OBJE@ OBJE {1:1}
           +1 FORM <MULTIMEDIA_FORMAT> {1:1} p.*
           +1 TITL <DESCRIPTIVE_TITLE> {0:1} p.*
           +1 <<NOTE_STRUCTURE>> {0:M} p.*
           +1 BLOB {1:1}
           +2 CONT <ENCODED_MULTIMEDIA_LINE> {1:M} p.*
           +1 OBJE @<XREF:OBJE>@ /* chain to continued object */ {0:1} p.*
           +1 REFN <USER_REFERENCE_NUMBER> {0:M} p.*
           +2 TYPE <USER_REFERENCE_TYPE> {0:1} p.*
           +1 RIN <AUTOMATED_RECORD_ID> {0:1} p.*
           +1 <<CHANGE_DATE>> {0:1} p.*
        """
        gid = line.token_text.strip()
        media = self.__find_or_create_object(self.oid_map[gid])

        state = GedcomUtils.CurrentState()
        state.media = media
        state.level = 1

        self.__parse_level(state, self.obje_func, self.__undefined)

        # Add the default reference if no source has found
        self.__add_default_source(media)

        # commit the person to the database
        if media.change:
            self.dbase.commit_media_object(media, self.trans, 
                                        change_time=media.change)
        else:
            self.dbase.commit_media_object(media, self.trans)

    def __obje_form(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        # TODO: FIX THIS!!!
        state.media_form = line.data.strip()
        self.__skip_subordinate_levels(state.level+1)

    def __obje_file(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        (file_ok, filename) = self.__find_file(line.data, self.dir_path)
        if state.media != "URL":
            if not file_ok:
                self.__warn(_("Could not import %s") % filename[0])
        path = filename[0].replace('\\', os.path.sep)
        state.media.set_path(path)
        state.media.set_mime_type(Mime.get_type(path))
        if not state.media.get_description():
            state.media.set_description(path)

    def __obje_title(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.media.set_description(line.data)

    def __obje_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.media, state.level+1)

    def __obje_blob(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__skip_subordinate_levels(state.level+1)

    def __obje_refn(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__skip_subordinate_levels(state.level+1)

    def __obje_type(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__skip_subordinate_levels(state.level+1)

    def __obje_rin(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__skip_subordinate_levels(state.level+1)

    def __obje_chan(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__skip_subordinate_levels(state.level+1)

    def __person_attr_type(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if state.attr.get_type() == "":
            if line.data in GED_2_GRAMPS:
                name = GED_2_GRAMPS[line.data]
            else:
                val = self.gedsource.tag2gramps(line.data)
                if val:
                    name = val
                else:
                    name = line.data
            state.attr.set_type(name)

    def __person_attr_source(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.attr.add_source_reference(self.handle_source(line, state.level))

    def __person_attr_place(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        val = line.data
        if state.attr.get_value() == "":
            state.attr.set_value(val)
        self.__skip_subordinate_levels(state.level)

    def __person_attr_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.attr, state.level+1)

    #----------------------------------------------------------------------
    #
    # REPO parsing
    #
    #----------------------------------------------------------------------
    def __parse_repo(self, line):
        """
        REPOSITORY_RECORD:=
          n @<XREF:REPO>@ REPO {1:1}
         +1 NAME <NAME_OF_REPOSITORY> {0:1} p.*
         +1 <<ADDRESS_STRUCTURE>> {0:1} p.*
         +1 <<NOTE_STRUCTURE>> {0:M} p.*
         +1 REFN <USER_REFERENCE_NUMBER> {0:M} p.*
         +1 RIN <AUTOMATED_RECORD_ID> {0:1} p.*
         +1 <<CHANGE_DATE>> {0:1} p.
        """
        repo = self.__find_or_create_repository(line.token_text)

        state = GedcomUtils.CurrentState()
        state.repo = repo
        state.level = 1
        self.__parse_level(state, self.repo_parse_tbl, self.__ignore)

        self.dbase.commit_repository(repo, self.trans)

    def __repo_name(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.repo.set_name(line.data)

    def __repo_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.repo, state.level+1)

    def __repo_addr(self, line, state):
        """
        n ADDR <ADDRESS_LINE> {0:1} 
        +1 CONT <ADDRESS_LINE> {0:M}
        +1 ADR1 <ADDRESS_LINE1> {0:1}
        +1 ADR2 <ADDRESS_LINE2> {0:1}
        +1 CITY <ADDRESS_CITY> {0:1}
        +1 STAE <ADDRESS_STATE> {0:1}
        +1 POST <ADDRESS_POSTAL_CODE> {0:1}
        +1 CTRY <ADDRESS_COUNTRY> {0:1}
        n PHON <PHONE_NUMBER> {0:3}

        Some repositories do not try to break up the address, 
        instead they put everything on a single line. Try to determine
        if this happened, and try to fix it.
        """

        addr = gen.lib.Address()
        addr.set_street(line.data)

        sub_state = GedcomUtils.CurrentState()
        sub_state.level = state.level+1
        sub_state.addr = addr

        self.__parse_level(sub_state, self.parse_addr_tbl, self.__ignore)

        text = addr.get_street()
        if not addr.get_city() and not addr.get_state() and \
           not addr.get_postal_code() and not addr.get_country():
        
            match = ADDR_RE.match(text)
            if match:
                groups = match.groups()
                addr.set_street(groups[0].strip())
                addr.set_city(groups[2].strip())
                addr.set_state(groups[3].strip())
                addr.set_postal_code(groups[4].strip())
                addr.set_country(groups[5].strip())
            
            match = ADDR2_RE.match(text)
            if match:
                groups = match.groups()
                addr.set_street(groups[0].strip())
                addr.set_city(groups[2].strip())
                addr.set_state(groups[3].strip())
                addr.set_postal_code(groups[4].strip())

            match = ADDR3_RE.match(text)
            if match:
                groups = match.groups()
                addr.set_street(groups[0].strip())
                addr.set_city(groups[2].strip())
                addr.set_state(groups[3].strip())

        state.repo.add_address(addr)

    def __location_addr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = gen.lib.Location()
        val = state.location.get_street()
        if val:
            val = "%s, %s" % (val, line.data.strip())
        else:
            val = line.data.strip()
        state.location.set_street(val.replace('\n', ' '))

    def __location_date(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = gen.lib.Location()
        state.location.set_date_object(line.data)

    def __location_city(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = gen.lib.Location()
        state.location.set_city(line.data)

    def __location_stae(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = gen.lib.Location()
        state.location.set_state(line.data)

    def __location_post(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = gen.lib.Location()
        state.location.set_postal_code(line.data)

    def __location_ctry(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = gen.lib.Location()
        state.location.set_country(line.data)

    def __location_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = gen.lib.Location()
        self.__parse_note(line, state.event, state.level+1)

    def __optional_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.__parse_note(line, state.obj, state.level)

    def __parse_header_source(self):
        state = GedcomUtils.CurrentState(level=1)
        self.__parse_level(state, self.header_sour, self.__undefined)

    def __header_sour(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.gedsource = self.gedmap.get_from_source_tag(line.data)
        if line.data.strip() == "FTW":
            self.is_ftw = True
        state.genby = line.data

    def __header_vers(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if self.use_def_src:
            self.def_src.set_data_item('Generated by', "%s %s" %
                                       (state.genby, line.data))
        
    def __header_file(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if self.use_def_src:
            filename = os.path.basename(line.data).split('\\')[-1]
            self.def_src.set_title(_("Import from %s") % filename)

    def __header_copr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if self.use_def_src:
            self.def_src.set_publication_info(line.data)

    def __header_subm(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState(level=state.level+1)
        self.__parse_level(sub_state, self.header_subm, self.__ignore)

    def __header_dest(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if state.genby == "GRAMPS":
            self.gedsource = self.gedmap.get_from_source_tag(line.data)

    def __header_plac(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState(level=state.level+1)
        self.__parse_level(sub_state, self.place_form, self.__undefined)

    def __place_form(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.place_parser.parse_form(line)

    def __header_date(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if self.use_def_src:
            self.def_src.set_data_item('Creation date', line.data)

    def __header_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if self.use_def_src:
            self.__parse_note(line, self.def_src, 2)

    def __header_subm_name(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if self.use_def_src:
            self.def_src.set_author(line.data)

###############################################################################

    def __parse_note(self, line, obj, level):
        if line.token == TOKEN_RNOTE:
            # reference to a named note defined elsewhere
            gid = line.data.strip()
            obj.add_note(self.__find_note_handle(self.nid_map[gid]))
        else:
            if not line.data:
                msg = _("Line %d: empty note was ignored.") % line.line
                self.__warn(msg)
                self.__skip_subordinate_levels(level+1)
            else:
                new_note = gen.lib.Note(line.data)
                new_note.set_handle(Utils.create_id())
                self.dbase.add_note(new_note, self.trans)
                self.__skip_subordinate_levels(level+1)
                obj.add_note(new_note.get_handle())

    def __parse_inline_note(self, line, level):
        if not line.data:
            msg = _("Line %d: empty note was ignored.") % line.line
            self.__warn(msg)
            self.__skip_subordinate_levels(level)
        else:
            new_note = gen.lib.Note(line.data)
            gid = self.nid_map[line.token_text]
            handle = self.nid2id.get(gid)
            new_note.set_handle(handle)
            new_note.set_gramps_id(gid)
            self.dbase.add_note(new_note, self.trans)
            self.nid2id[new_note.gramps_id] = new_note.handle
            self.__skip_subordinate_levels(level)

    def __parse_source_reference(self, src_ref, level, handle):
        """
        Read the data associated with a SOUR reference.
        """
        state = GedcomUtils.CurrentState(level=level+1)
        state.src_ref = src_ref
        state.handle = handle
        self.__parse_level(state, self.srcref_parse_tbl, self.__ignore)
    
    def __parse_header_head(self):
        """
        Validate that this is a valid GEDCOM file.
        """
        line = self.__get_next_line()
        if line.token != TOKEN_HEAD:
            raise Errors.GedcomError("%s is not a GEDCOM file" % self.filename)
    
    def __skip_subordinate_levels(self, level):
        """
        Skip add lines of the specified level or lower.
        """
        skips = 0;
        while True:
            line = self.__get_next_line()
            if self.__level_is_finished(line, level):
                if skips and self.want_parse_warnings:
                    msg = _("skipped %d subordinate(s) at line %d")\
                            % (skips, line.line - skips)
                    self.__warn(msg)
                return
            skips += 1
    
    def handle_source(self, line, level):
        """
        Handle the specified source, building a source reference to
        the object.
        """
        source_ref = gen.lib.SourceRef()
        if line.data and line.data[0] != "@":
            title = line.data
            handle = self.inline_srcs.get(title, Utils.create_id())
            src = gen.lib.Source()
            src.handle = handle
            src.gramps_id = self.dbase.find_next_source_gramps_id()
            self.inline_srcs[title] = handle
        else:
            src = self.__find_or_create_source(self.sid_map[line.data])
        self.dbase.commit_source(src, self.trans)
        self.__parse_source_reference(source_ref, level, src.handle)
        source_ref.set_reference_handle(src.handle)
        return source_ref

    def __parse_change(self, line, obj, level):
        """
        CHANGE_DATE:=

        >  n CHAN {1:1}
        >  +1 DATE <CHANGE_DATE> {1:1}
        >  +2 TIME <TIME_VALUE> {0:1}
        >  +1 <<NOTE_STRUCTURE>> {0:M}

        The Note structure is ignored, since we have nothing
        corresponding in GRAMPS.

        Based on the values calculated, attempt to convert to a valid
        change time using time.strptime. If this fails (and it shouldn't
        unless the value is meaningless and doesn't conform to the GEDCOM
        spec), the value is ignored.
        """
        tstr = None
        dstr = None
        
        while True:
            line = self.__get_next_line()
            if self.__level_is_finished(line, level):
                break
            elif line.token == TOKEN_TIME:
                tstr = line.data
            elif line.token == TOKEN_DATE:
                dstr = line.data
            elif line.token == TOKEN_NOTE:
                self.__skip_subordinate_levels(level+1)
            else:
                self.__not_recognized(line, level+1)

        # Attempt to convert the values to a valid change time
        if tstr:
            try:
                if dstr:
                    tstruct = time.strptime("%s %s" % (dstr, tstr), 
                                            "%d %b %Y %H:%M:%S")
                else:
                    tstruct = time.strptime(tstr, "%d %b %Y")
                val = time.mktime(tstruct)
                obj.change = val
            except ValueError:
                # parse of time structure failed, so ignore
                pass
        
    def build_media_object(self, obj, form, filename, title, note):
        if form == "url":
            url = gen.lib.Url()
            url.set_path(filename)
            url.set_description(title)
            url.set_type(gen.lib.UrlType.WEB_HOME)
            obj.add_url(url)
        else:
            (valid, path) = self.__find_file(filename, self.dir_path)
            if not valid:
                self.__warn(_("Could not import %s") % filename)
                path = filename.replace('\\', os.path.sep)
            photo_handle = self.media_map.get(path)
            if photo_handle is None:
                photo = gen.lib.MediaObject()
                photo.set_path(path)
                photo.set_description(title)
                full_path = os.path.abspath(path)
                if os.path.isfile(full_path):
                    photo.set_mime_type(Mime.get_type(full_path))
                else:
                    photo.set_mime_type(MIME_MAP.get(form.lower(), 'unknown'))
                self.dbase.add_object(photo, self.trans)
                self.media_map[path] = photo.handle
            else:
                photo = self.dbase.get_object_from_handle(photo_handle)
            oref = gen.lib.MediaRef()
            oref.set_reference_handle(photo.handle)
            if note:
                oref.add_note(self.__find_note_handle(self.nid_map[note]))
            obj.add_media_reference(oref)

    def __build_event_pair(self, state, event_type, event_map, description):
        """
        n TYPE <EVENT_DESCRIPTOR> {0:1} p.*
        n DATE <DATE_VALUE> {0:1} p.*/*
        n <<PLACE_STRUCTURE>> {0:1} p.*
        n <<ADDRESS_STRUCTURE>> {0:1} p.*
        n AGE <AGE_AT_EVENT> {0:1} p.*
        n AGNC <RESPONSIBLE_AGENCY> {0:1} p.*
        n CAUS <CAUSE_OF_EVENT> {0:1} p.*
        n <<SOURCE_CITATION>> {0:M} p.*
        n <<MULTIMEDIA_LINK>> {0:M} p.*, *
        n <<NOTE_STRUCTURE>> {0:M} p.
        """
        event = gen.lib.Event()
        event_ref = gen.lib.EventRef()
        event.set_gramps_id(self.emapper.find_next())
        event.set_type(event_type)

        if description and description != 'Y':
            event.set_description(description)
        self.dbase.add_event(event, self.trans)

        sub_state = GedcomUtils.CurrentState()
        sub_state.level = state.level + 1
        sub_state.event_ref = event_ref
        sub_state.event = event
        sub_state.person = state.person

        self.__parse_level(sub_state, event_map, self.__undefined)
        self.dbase.commit_event(event, self.trans)

        event_ref.set_reference_handle(event.handle)
        return event_ref

    def __build_family_event_pair(self, state, event_type, event_map, 
                                 description):
        event = gen.lib.Event()
        event_ref = gen.lib.EventRef()
        event.set_gramps_id(self.emapper.find_next())
        event.set_type(event_type)
        if description and description != 'Y':
            event.set_description(description)

        self.dbase.add_event(event, self.trans)

        sub_state = GedcomUtils.CurrentState()
        sub_state.family = state.family
        sub_state.level = state.level+1
        sub_state.event = event
        sub_state.event_ref = event_ref

        self.__parse_level(sub_state, event_map, self.__undefined)

        self.dbase.commit_event(event, self.trans)
        event_ref.set_reference_handle(event.handle)
        return event_ref

    def __extract_temple(self, line):
        def get_code(code):
            if LdsUtils.TEMPLES.is_valid_code(code):
                return code
            elif LdsUtils.TEMPLES.is_valid_name(code):
                return LdsUtils.TEMPLES.code(code)
        
        code = get_code(line.data)
        if code: 
            return code
        
        ## Not sure why we do this. Kind of ugly.
        code = get_code(line.data.split()[0])
        if code: 
            return code

        ## Okay we have no clue which temple this is.
        ## We should tell the user and store it anyway.
        self.__warn("Invalid temple code '%s'" % (line.data, ))
        return line.data

    def __add_default_source(self, obj):
        """
        Add the default source to the object.
        """
        if self.use_def_src and len(obj.get_source_references()) == 0:
            sref = gen.lib.SourceRef()
            sref.set_reference_handle(self.def_src.handle)
            obj.add_source_reference(sref)

    def __subm_name(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.res.set_name(line.data)

    def __subm_addr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState(level=state.level + 1)
        sub_state.location = gen.lib.Location()
        sub_state.location.set_street(line.data)

        self.__parse_level(sub_state, self.parse_loc_tbl, self.__undefined)

        location = sub_state.location
        state.res.set_address(location.get_street())
        state.res.set_city(location.get_city())
        state.res.set_state(location.get_state())
        state.res.set_country(location.get_country())
        state.res.set_postal_code(location.get_postal_code())

    def __subm_phon(self, line, state):
        """
        n PHON <PHONE_NUMBER> {0:3}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.res.set_phone(line.data)

#===eof===
