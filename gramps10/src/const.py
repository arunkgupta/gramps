#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
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

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os

#-------------------------------------------------------------------------
#
# internationalization
#
#-------------------------------------------------------------------------
from intl import gettext
_ = gettext

#-------------------------------------------------------------------------
#
# Paths to external programs
#
#-------------------------------------------------------------------------
editor  = "gimp"
zipcmd  = "zip -r -q"
convert = "convert"

#-------------------------------------------------------------------------
#
# Paths to files - assumes that files reside in the same directory as
# this one, and that the plugins directory is in a directory below this.
#
#-------------------------------------------------------------------------

if os.environ.has_key('GRAMPSDIR'):
    rootDir = os.environ['GRAMPSDIR']
else:
    rootDir = "."

system_filters = "%s/system_filters.xml" % rootDir
custom_filters = "~/.gramps/custom_filters.xml"
icon           = "%s/gramps.xpm" % rootDir
logo           = "%s/logo.png" % rootDir
gladeFile      = "%s/gramps.glade" % rootDir
placesFile     = "%s/places.glade" % rootDir
imageselFile   = "%s/imagesel.glade" % rootDir
marriageFile   = "%s/marriage.glade" % rootDir
editPersonFile = "%s/EditPerson.glade" % rootDir
bookFile       = "%s/bookmarks.glade" % rootDir
pluginsFile    = "%s/plugins.glade" % rootDir
editnoteFile   = "%s/editnote.glade" % rootDir
configFile     = "%s/config.glade" % rootDir
prefsFile      = "%s/preferences.glade" % rootDir
stylesFile     = "%s/styles.glade" % rootDir
dialogFile     = "%s/dialog.glade" % rootDir
revisionFile   = "%s/revision.glade" % rootDir
srcselFile     = "%s/srcsel.glade" % rootDir
findFile       = "%s/find.glade" % rootDir
mergeFile      = "%s/mergedata.glade" % rootDir
traceFile      = "%s/trace.glade" % rootDir
filterFile     = "%s/rule.glade" % rootDir

pluginsDir     = "%s/plugins" % rootDir
docgenDir      = "%s/docgen" % rootDir
filtersDir     = "%s/filters" % rootDir
dataDir        = "%s/data" % rootDir
gtkrcFile      = "%s/gtkrc" % rootDir
template_dir   = "%s/templates" % dataDir

startup        = 1

#-------------------------------------------------------------------------
#
# About box information
#
#-------------------------------------------------------------------------
progName     = "GRAMPS"
version      = "0.8.1-pl1"
copyright    = "� 2001-2003 Donald N. Allingham"
authors      = ["Donald N. Allingham", "David Hampton","Donald A. Peterson"]
comments     = _("GRAMPS (Genealogical Research and Analysis "
                 "Management Programming System) is a personal "
                 "genealogy program.")

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
picWidth     = 275.0
thumbScale   = 96.0
xmlFile      = "data.gramps"
zodbFile     = "gramps.zodb"
male         = _("male")
female       = _("female")
unknown      = _("unknown")

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------

childRelations = {
    _("Birth")     : "Birth",
    _("Adopted")   : "Adopted",
    _("Stepchild") : "Stepchild",
    _("Foster")    : "Foster",
    _("None")      : "None",
    _("Unknown")   : "Unknown",
    _("Other")     : "Other",
    }

#-------------------------------------------------------------------------
#
# Confidence
#
#-------------------------------------------------------------------------
confidence = [
    _("Very Low"),
    _("Low"),
    _("Normal"),
    _("High"),
    _("Very High")
    ]

#-------------------------------------------------------------------------
#
# Family event string mappings
#
#-------------------------------------------------------------------------
familyConstantEvents = {
    "Annulment"           : "ANUL",
    "Divorce Filing"      : "DIVF",
    "Divorce"             : "DIV",
    "Engagement"          : "ENGA",
    "Marriage Contract"   : "MARC",
    "Marriage License"    : "MARL",
    "Marriage Settlement" : "MARS",
    "Marriage"            : "MARR"
    }

_fe_e2l = {
    "Annulment"           : _("Annulment"),
    "Divorce Filing"      : _("Divorce Filing"),
    "Divorce"             : _("Divorce"),
    "Engagement"          : _("Engagement"),
    "Marriage Contract"   : _("Marriage Contract"),
    "Marriage License"    : _("Marriage License"),
    "Marriage Settlement" : _("Marriage Settlement"),
    "Marriage"            : _("Marriage")
    }

_fe_l2e = {}
for a in _fe_e2l.keys():
    _fe_l2e[_fe_e2l[a]] = a

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def display_fevent(st):
    if _fe_e2l.has_key(st):
        return _fe_e2l[st]
    else:
        return st

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def save_fevent(st):
    if _fe_l2e.has_key(st):
        return _fe_l2e[st]
    else:
        return st

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
personalConstantEvents = {
    "Adopted"             : "ADOP",
    "Adult Christening"   : "CHRA",
    "Alternate Birth"     : "BIRT",
    "Alternate Death"     : "DEAT",
    "Baptism"             : "BAPM",
    "Bar Mitzvah"         : "BARM",
    "Bas Mitzvah"         : "BASM",
    "Blessing"            : "BLES",
    "Burial"              : "BURI",
    "Cause Of Death"      : "CAUS",
    "Ordination"          : "ORDI",
    "Census"              : "CENS",
    "Christening"         : "CHR" ,
    "Confirmation"        : "CONF",
    "Cremation"           : "CREM",
    "Degree"              : "", 
    "Divorce Filing"      : "DIVF",
    "Education"           : "EDUC",
    "Elected"             : "",
    "Emigration"          : "EMIG",
    "First Communion"     : "FCOM",
    "Graduation"          : "GRAD",
    "Medical Information" : "", 
    "Military Service"    : "", 
    "Naturalization"      : "NATU",
    "Nobility Title"      : "TITL",
    "Number of Marriages" : "NMR",
    "Immigration"         : "IMMI",
    "Occupation"          : "OCCU",
    "Probate"             : "PROB",
    "Property"            : "PROP",
    "Religion"            : "RELI",
    "Residence"           : "RESI", 
    "Retirement"          : "RETI",
    "Will"                : "WILL"
    }

_pe_e2l = {
    "Adopted"             : _("Adopted"),
    "Alternate Birth"     : _("Alternate Birth"),
    "Alternate Death"     : _("Alternate Death"),
    "Adult Christening"   : _("Adult Christening"),
    "Baptism"             : _("Baptism"),
    "Bar Mitzvah"         : _("Bar Mitzvah"),
    "Bas Mitzvah"         : _("Bas Mitzvah"),
    "Blessing"            : _("Blessing"),
    "Burial"              : _("Burial"),
    "Cause Of Death"      : _("Cause Of Death"),
    "Census"              : _("Census"),
    "Christening"         : _("Christening"),
    "Confirmation"        : _("Confirmation"),
    "Cremation"           : _("Cremation"),
    "Degree"              : _("Degree"),
    "Divorce Filing"      : _("Divorce Filing"),
    "Education"           : _("Education"),
    "Elected"             : _("Elected"),
    "Emigration"          : _("Emigration"),
    "First Communion"     : _("First Communion"),
    "Immigration"         : _("Immigration"),
    "Graduation"          : _("Graduation"),
    "Medical Information" : _("Medical Information"),
    "Military Service"    : _("Military Service"), 
    "Naturalization"      : _("Naturalization"),
    "Nobility Title"      : _("Nobility Title"),
    "Number of Marriages" : _("Number of Marriages"),
    "Occupation"          : _("Occupation"),
    "Ordination"          : _("Ordination"),
    "Probate"             : _("Probate"),
    "Property"            : _("Property"),
    "Religion"            : _("Religion"),
    "Residence"           : _("Residence"),
    "Retirement"          : _("Retirement"),
    "Will"                : _("Will")
    }

_pe_l2e = {}
for a in _pe_e2l.keys():
    val = _pe_e2l[a]
    if val:
        _pe_l2e[val] = a

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def display_pevent(st):
    if _pe_e2l.has_key(st):
        return _pe_e2l[st]
    else:
        return st

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def save_pevent(st):
    if _pe_l2e.has_key(st):
        return _pe_l2e[st]
    else:
        return st

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
personalConstantAttributes = {
    "Caste"                 : "CAST",
    "Description"           : "DSCR",
    "Identification Number" : "IDNO",
    "National Origin"       : "NATI",
    "Social Security Number": "SSN"
    }

_pa_e2l = {
    "Caste"                 : _("Caste"),
    "Description"           : _("Description"),
    "Identification Number" : _("Identification Number"),
    "National Origin"       : _("National Origin"),
    "Social Security Number": _("Social Security Number")
    }

_pa_l2e = {}
for a in _pa_e2l.keys():
    _pa_l2e[_pa_e2l[a]] = a

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def display_pattr(st):
    if _pa_e2l.has_key(st):
        return _pa_e2l[st]
    else:
        return st

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def save_pattr(st):
    if _pa_l2e.has_key(st):
        return _pa_l2e[st]
    else:
        return st

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
familyConstantAttributes = {
    "Number of Children" : "NCHI",
    }

_fa_e2l = {
    "Number of Children" : _("Number of Children"),
    }

_fa_l2e = {}
for a in _fa_e2l.keys():
    _fa_l2e[_fa_e2l[a]] = a

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def display_fattr(st):
    if _fa_e2l.has_key(st):
        return _fa_e2l[st]
    else:
        return st

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def save_fattr(st):
    if _fa_l2e.has_key(st):
        return _fa_l2e[st]
    else:
        return st

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------

_frel2def = {
    _("Married")  : _("A legal or common-law relationship between a husband and wife"),
    _("Unmarried"): _("No legal or common-law relationship between man and woman"),
    _("Partners") : _("An established relationship between members of the same sex"),
    _("Unknown")  : _("Unknown relationship between a man and woman"),
    _("Other")    : _("An unspecified relationship between a man and woman")
}

_fr_e2l = {
    "Married"   : _("Married"),
    "Unmarried" : _("Unmarried"),
    "Partners"  : _("Partners"),
    "Unknown"   : _("Unknown"),
    "Other"     : _("Other")
}

_fr_l2e = {}
for a in _fa_e2l.keys():
    _fa_l2e[_fa_e2l[a]] = a

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def relationship_def(txt):
    if _frel2def.has_key(txt):
        return _frel2def[txt]
    else:
        return _("No definition available")

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def display_frel(st):
    if _fr_e2l.has_key(st):
        return _fr_e2l[st]
    else:
        return st

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def save_frel(st):
    if _fr_l2e.has_key(st):
        return _fr_l2e[st]
    else:
        return st

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def init_personal_event_list():
    p = []
    for event in personalConstantEvents.keys():
        p.append(_pe_e2l[event])
    p.sort()
    return p

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def init_marriage_event_list():
    p = []
    for event in familyConstantEvents.keys():
        p.append(_fe_e2l[event])
    p.sort()
    return p

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def init_personal_attribute_list():
    p = []
    for event in personalConstantAttributes.keys():
        p.append(_pa_e2l[event])
    p.sort()
    return p

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def init_family_attribute_list():
    p = []
    for event in familyConstantAttributes.keys():
        p.append(_fa_e2l[event])
    p.sort()
    return p

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def init_family_relation_list():
    p = []
    for event in _fr_e2l.keys():
        p.append(_fr_e2l[event])
    p.sort()
    return p

personalEvents = init_personal_event_list()
personalAttributes = init_personal_attribute_list()
marriageEvents = init_marriage_event_list()
familyAttributes = init_family_attribute_list()
familyRelations = init_family_relation_list()
places = []
surnames = []

#
#Updated LDS Temple Codes from:
#http://www.geocities.com/rgpassey/temple/abclist.htm
#Confirmed against Temple Codes list recieved from Raliegh Temple
#Last update: 1/12/02
#

lds_temple_codes = {
    "Aba, Nigeria"               : "ABA",   #1 Added
    "Accra, Ghana"               : "ACCRA", #2 Added
    "Adelaide, Australia"        : "ADELA", #3 Added
    "Albuquerque, New Mexico"    : "ALBUQ", #4 Added
    "Anchorage, Alaska"          : "ANCHO", #6 Added
    "Apia, Samoa"                : "APIA",  #7
    "Asuncion, Paraguay"         : "ASUNC", #8 Added
    "Atlanta, Georgia"           : "ATLAN", #9
    "Baton Rouge, Louisiana"     : "BROUG", #10 Added
    "Bern, Switzerland"          : "SWISS", #11
    "Billings, Montana"          : "BILLI", #12 Added
    "Birmingham, Alabama"        : "BIRMI", #13 Added
    "Bismarck, North Dakota"     : "BISMA", #14 Added
    "Bogota, Columbia"           : "BOGOT", #15
    "Boise, Idaho"               : "BOISE", #16
    "Boston, Massachusetts"      : "BOSTO", #17 Added
    "Bountiful, Utah"            : "BOUNT", #18
    "Brisban, Australia"         : "BRISB", #19 Added
    "Buenos Aires, Argentina"    : "BAIRE", #20
    "Campinas, Brazil"           : "CAMPI", #21 Added
    "Caracas, Venezuela"         : "CARAC", #22 Added
    "Cardston, Alberta"          : "ALBER", #23
    "Chicago, Illinois"          : "CHICA", #24
    "Ciudad Juarez, Chihuahua"   : "CIUJU", #25 Added
    "Cochabamba, Boliva"         : "COCHA", #26
    "Colonia Juarez, Chihuahua"  : "COLJU", #27 Added
    "Columbia, South Carolina"   : "COLSC", #28 Added
    "Columbia River, Washington" : "CRIVE", #121 Added
    "Columbus, Ohio"             : "COLUM", #29 Added
    "Copenhagen, Denmark"        : "COPEN", #30 Added
    "Dallas, Texas"              : "DALLA", #31
    "Denver, Colorado"           : "DENVE", #32
    "Detroit, Michigan"          : "DETRO", #33 Added
    "Edmonton, Alberta"          : "EDMON", #34 Added
    "Frankfurt, Germany"         : "FRANK", #35
    "Fresno, California"         : "FRESN", #36 Added
    "Freiberg, Germany"          : "FREIB", #37
    "Fukuoka, Japan"             : "FUKUO", #38 Added
    "Guadalajara, Jalisco"       : "GUADA", #39 Added
    "Guatamala City, Guatamala"  : "GUATE", #40
    "Guayaquil, Ecuador"         : "GUAYA", #41
    "Halifax, Noca Scotia"       : "HALIF", #42 Added
    "Hamilton, New Zealand"      : "NZEAL", #43
    "Harrison, New York"         : "NYORK", #44 Added
    "Hartford, Connecticut"      : "HARTF", #Can not find in list used. ?
    "Helsinki, Finland"          : "HELSI", #45 Added
    "Hermosillo, Sonora"         : "HERMO", #46 Added
    "Hong Kong, China"           : "HKONG", #47
    "Houston, Texas"             : "HOUST", #48 Added
    "Idaho Falls, Idaho"         : "IFALL", #49
    "Johannesburg, South Africa" : "JOHAN", #50
    "Jordan River (South Jordan), Utah" : "JRIVE", #111
    "Kialua Kona, Hawaii"        : "KONA",  #51 Added
    "Kiev, Ukraine"              : "KIEV",  #52 Added
    "Laie, Hawaii"               : "HAWAI", #54
    "Las Vegas, Nevada"          : "LVEGA", #55
    "Lima, Peru"                 : "LIMA" , #56
    "Logan, Utah"                : "LOGAN", #57
    "London, England"            : "LONDO", #58
    "Los Angeles, California"    : "LANGE", #59
    "Louisville, Kentucky"       : "LOUIS", #60 Added
    "Lubbock, Texas"             : "LUBBO", #61 Added
    "Madrid, Spain"              : "MADRI", #62
    "Manila, Philippines"        : "MANIL", #63
    "Manti, Utah"                : "MANTI", #64
    "Medford, Oregon"            : "MEDFO", #65 Added
    "Melbourne, Australia"       : "MELBO", #66 Added
    "Melphis, Tennessee"         : "MEMPH", #67 Added
    "Merida, Yucatan"            : "MERID", #68 Added
    "Mesa, Arizona"              : "ARIZO", #69
    "Mexico City, Mexico"        : "MEXIC", #70
    "Monterrey, Nuevo Leon"      : "MONTE", #71 Added
    "Montevideo, Uruguay"        : "MNTVD", #72
    "Monticello, Utah"           : "MONTI", #73 Added
    "Montreal, Quebec"           : "MONTR", #74 Added
    "Mt. Timpanogos (American Fork), Utah" : "MTIMP", #5
    "Nashville, Tennessee"       : "NASHV", #75
    "Nauvoo, Illinois"           : "NAUVO", #76
    "Nauvoo, Illinois (New)"     : "NAUV2", #Rebuilt Added
    "Newport Beach, California"  : "NBEAC", #77 Added
    "Nuku'alofa, Tonga"          : "NUKUA", #78
    "Oakland, California"        : "OAKLA", #79
    "Oaxaca, Oaxaca"             : "OAKAC", #80 Added
    "Ogden, Utah"                : "OGDEN", #81
    "Oklahoma City, Oklahoma"    : "OKLAH", #82 Added
    "Orlando, Florida"           : "ORLAN", #84
    "Palmayra, New York"         : "PALMY", #85 Added
    "Papeete, Tahiti"            : "PAPEE", #86
    "Perth, Australia"           : "PERTH", #87 Added
    "Portland, Oregon"           : "PORTL", #88
    "Porto Alegre, Brazil"       : "PALEG", #89 Added
    "Preston, England"           : "PREST", #90
    "Provo, Utah"                : "PROVO", #91
    "Raleigh, North Carolina"    : "RALEI", #92 Added
    "Recife, Brazil"             : "RECIF", #93
    "Redlands, California"       : "REDLA", #94 Added
    "Regina, Saskatchewan"       : "REGIN", #95 Added
    "Reno, Nevada"               : "RENO",  #96 Added
    "Sacramento, California"     : "SACRA", #97 Added
    "St. George, Utah"           : "SGEOR", #98
    "St. Louis, Missouri"        : "SLOUI", #99
    "St. Paul, Minnesota"        : "SPMIN", #100 Added
    "Salt Lake City, Utah"       : "SLAKE", #101
    "San Diego, California"      : "SDIEG", #102
    "San Antonio, Texas"         : "ANTON", #103 Added
    "San Jose, Costa Rica"       : "SJOSE", #104 Added
    "Santiago, Chile"            : "SANTI", #105
    "Santo Domingo, Dominican Republic" : "SDOMI", #106
    "Sao Paulo, Brazil"          : "SPAUL", #107
    "Seattle, Washington"        : "SEATT", #108
    "Seoul, South Korea"         : "SEOUL", #109
    "Snowflake, Arizona"         : "SNOWF", #110 Added
    "Spokane, Washington"        : "SPOKA", #112
    "Stockholm, Sweden"          : "STOCK", #113
    "Suva, Fiji"                 : "SUVA",  #114 Added
    "Sydney, Australia"          : "SYDNE", #115
    "Taipei, Taiwan"             : "TAIPE", #116
    "Tampico, Tamaulipas"        : "TAMPI", #117 Added
    "The Hague, Netherlands"     : "HAGUE", #118 Added
    "Tokyo, Japan"               : "TOKYO", #119
    "Toronto, Ontario"           : "TORNO", #120
    "Tuxtla Gutierrez, Chiapas"  : "TGUTI", #122 Added
    "Vera Cruz, Vera Cruz"       : "VERAC", #123 Added
    "Vernal, Utah"               : "VERNA", #124
    "Villahermosa, Tabasco"      : "VILLA", #125 Added
    "Washington, D.C."           : "WASHI", #126
    "Winter Quarters (Omaha), Nebraska" : "WINTE", #83 Added
#Other Places
    "Endowment House"            : "EHOUS", #Not a temple per se
    "President's Office"         : "POFFI", #Not a temple per se


}

lds_temple_to_abrev = {
    "ABA"  : "Aba, Nigeria",
    "ACCRA": "Accra, Ghana",
    "ADELA": "Adelaide, Australia",
    "ALBUQ": "Albuquerque, New Mexico",
    "ANCHO": "Anchorage, Alaska",
    "APIA" : "Apia, Samoa",            
    "AP"   : "Apia, Samoa",            
    "ASUNC": "Asuncion, Paraguay",
    "ATLAN": "Atlanta, Georgia",          
    "AT"   : "Atlanta, Georgia",          
    "BROUG": "Baton Rouge, Louisiana",
    "SWISS": "Bern, Switzerland",               
    "SW"   : "Bern, Switzerland",               
    "BILLI": "Billings, Montana",
    "BIRMI": "Birmingham, Alabama",
    "BISMA": "Bismarck, North Dakota",
    "BOGOT": "Bogota, Columbia",         
    "BG"   : "Bogota, Columbia",         
    "BOISE": "Boise Idaho",            
    "BO"   : "Boise Idaho",            
    "BOSTO": "Boston, Massachusetts",
    "BOUNT": "Bountiful, Utah",        
    "BRISB": "Brisban, Australia",
    "BAIRE": "Buenos Aires, Argentina",        
    "BA"   : "Buenos Aires, Argentina",        
    "CAMPI": "Campinas, Brazil",
    "CARAC": "Caracas, Venezuela",
    "ALBER": "Cardston, Alberta",
    "CHICA": "Chicago, Illinois",          
    "CH"   : "Chicago, Illinois",          
    "CIUJU": "Ciudad Juarez, Chihuahua",
    "COCHA": "Cochabamba, Boliva",  
    "COLJU": "Colonia Juarez, Chihuahua",
    "COLSC": "Columbia, South Carolina",
    "CRIVE": "Columbia River, Washington",
    "COLUM": "Columbus, Ohio",
    "COPEN": "Copenhagen, Denmark",
    "DALLA": "Dallas, Texas",          
    "DA"   : "Dallas, Texas",          
    "DENVE": "Denver, Colorado",          
    "DV"   : "Denver, Colorado",          
    "DETRO": "Detroit, Michigan",
    "EDMON": "Edmonton, Alberta",
    "FRANK": "Frankfurt, Germany",           
    "FR"   : "Frankfurt, Germany",           
    "FRESN": "Fresno, California",
    "FREIB": "Freiberg, Germany",            
    "FD"   : "Freiberg, Germany",            
    "FUKUO": "Fukuoka, Japan",
    "GUADA": "Guadalajara, Jalisco",
    "GUATE": "Guatamala City, Guatamala",           
    "GA"   : "Guatamala City, Guatamala",           
    "GUAYA": "Guayaquil, Ecuador",  
    "GY"   : "Guayaquil, Ecuador",  
    "HALIF": "Halifax, Noca Scotia",
    "NZEAL": "Hamilton, New Zealand",         
    "NZ"   : "Hamilton, New Zealand",         
    "NYORK": "Harrison, New York",
    "HARTF": "Hartford, Connecticut",      
    "HELSI": "Helsinki, Finland",
    "HERMO": "Hermosillo, Sonora",
    "HKONG": "Hong Kong, China",           
    "HOUST": "Houston, Texas",
    "IFALL": "Idaho Falls, Idaho", 
    "JOHAN": "Johannesburg, South Africa",  
    "JO"   : "Johannesburg, South Africa",  
    "JRIVE": "Jordan River (South Jordan), Utah",    
    "JR"   : "Jordan River (South Jorhan), Utah",    
    "KONA" : "Kialua Kona, Hawaii",
    "KIEV" : "Kiev, Ukraine",
    "HAWAI": "Laie, Hawaii",              
    "HA"   : "Laie, Hawaii",              
    "LVEGA": "Las Vegas, Nevada",       
    "LV"   : "Las Vegas, Nevada",       
    "LIMA" : "Lima, Peru",          
    "LI"   : "Lima, Peru",          
    "LOGAN": "Logan, Utah",           
    "LG"   : "Logan, Utah",           
    "LONDO": "London, England",              
    "LD"   : "London, England",              
    "LANGE": "Los Angeles, California",     
    "LA"   : "Los Angeles, California",     
    "LOUIS": "Louisville, Kentucky",
    "LUBBO": "Lubbock, Texas",
    "MADRI": "Madrid, Spain",       
    "MANIL": "Manila, Philippines", 
    "MA"   : "Manila, Philippines", 
    "MANTI": "Manti, Utah",           
    "MT"   : "Manti, Utah",           
    "MEDFO": "Medford, Oregon",
    "MELBO": "Melbourne, Australia",
    "MEMPH": "Melphis, Tennessee",
    "MERID": "Merida, Yucatan",
    "ARIZO": "Mesa, Arizona",
    "AZ"   : "Mesa, Arizona",
    "MEXIC": "Mexico City, Mexico",         
    "MX"   : "Mexico City, Mexico",         
    "MONTE": "Monterrey, Nuevo Leon, Mexico",
    "MNTVD": "Montevideo, Uruguay",
    "MONTI": "Monticello, Utah",
    "MONTR": "Montreal, Quebec",
    "MTIMP": "Mt. Timpanogos (American Fork), Utah",  
    "NASHV": "Nashville, Tennessee",     
    "NAUVO": "Nauvoo, Illinois",
    "NAUV2": "Nauvoo, Illinois (New)",
    "NBEAC": "Newport Beach, California",
    "NUKUA": "Nuku'alofa, Tonga",   
    "TG"   : "Nuku'alofa, Tonga",   
    "OAKLA": "Oakland, California",         
    "OK"   : "Oakland, California",         
    "OAKAC": "Oaxaca, Oaxaca",
    "OGDEN": "Ogden, Utah",           
    "OG"   : "Ogden, Utah",           
    "OKLAH": "Oklahoma City, Oklahoma",
    "ORLAN": "Orlando, Florida",         
    "PALMY": "Palmayra, New York",
    "PAPEE": "Papeete, Tahiti",     
    "TA"   : "Papeete, Tahiti",     
    "PERTH": "Perth, Australia",
    "PORTL": "Portland, Oregon",        
    "PT"   : "Portland, Oregon",        
    "PALEG": "Porto Alegre, Brazil",
    "PREST": "Preston, England",        
    "PROVO": "Provo, Utah",           
    "PV"   : "Provo, Utah",           
    "RALEI": "Raleigh, North Carolina",
    "RECIF": "Recife, Brazil",      
    "REDLA": "Redlands, California",
    "REGIN": "Regina, Saskatchewan",
    "RENO" : "Reno, Nevada",
    "SACRA": "Sacramento, California",
    "SGEOR": "St. George, Utah",      
    "SG"   : "St. George, Utah",      
    "SLOUI": "St. Louis, Missouri", 
    "SPMIN": "St. Paul, Minnesota",
    "SLAKE": "Salt Lake City, Utah",       
    "SL"   : "Salt Lake City, Utah",       
    "SDIEG": "San Diego, California",       
    "SA"   : "San Diego, California",       
    "ANTON": "San Antonio, Texas",
    "SJOSE": "San Jose, Costa Rica",
    "SANTI": "Santiago, Chile",     
    "SN"   : "Santiago, Chile",     
    "SDOMI": "Santo Domingo, Dominican Republic", 
    "SPAUL": "Sao Paulo, Brazil",     
    "SP"   : "Sao Paulo, Brazil",     
    "SEATT": "Seattle, Washington",         
    "SE"   : "Seattle, Washington",         
    "SEOUL": "Seoul, South Korea",        
    "SO"   : "Seoul, South Korea",        
    "SNOWF": "Snowflake, Arizona",
    "SPOKA": "Spokane, Washington",
    "STOCK": "Stockholm, Sweden",     
    "ST"   : "Stockholm, Sweden",     
    "SUVA" : "Suva, Fiji",
    "SYDNE": "Sydney, Australia",        
    "SD"   : "Sydney, Australia",        
    "TAIPE": "Taipei, Taiwan",      
    "TP"   : "Taipei, Taiwan",      
    "TAMPI": "Tampico, Tamaulipas",
    "HAGUE": "The Hague, Netherlands",
    "TOKYO": "Tokyo, Japan",        
    "TK"   : "Tokyo, Japan",        
    "TORNO": "Toronto, Ontario",       
    "TR"   : "Toronto, Ontario",       
    "TGUTI": "Tuxtla Gutierrez, Chiapas",
    "VERAC": "Vera Cruz, Vera Cruz",
    "VERNA": "Vernal, Utah",         
    "VILLA": "Villahermosa, Tabasco",
    "WASHI": "Washington, D.C.",      
    "WA"   : "Washington, D.C.",      
    "WINTE": "Winter Quarters (Omaha), Nebraska",
#Other Places
    "EHOUS": "Endowment House",     
    "EH"   : "Endowment House",     
    "POFFI": "President's Office",  
}

lds_status = {
    "BIC"         : 1,    "CANCELED"    : 1,    "CHILD"       : 1,
    "CLEARED"     : 2,    "COMPLETED"   : 3,    "DNS"         : 4,
    "INFANT"      : 4,    "PRE-1970"    : 5,    "QUALIFIED"   : 6,
    "DNS/CAN"     : 7,    "STILLBORN"   : 7,    "SUBMITTED"   : 8,
    "UNCLEARED"   : 9,
    }

lds_baptism = [
    "<No Status>",  "Child",     "Cleared",    "Completed",
    "Infant",       "Pre-1970",  "Qualified",  "Stillborn",
    "Submitted",    "Uncleared",
    ]

lds_csealing = [
    "<No Status>",  "BIC",       "Cleared",    "Completed",
    "DNS",          "Pre-1970",  "Qualified",  "Stillborn",
    "Submitted",    "Uncleared",
    ]

lds_ssealing = [
    "<No Status>",  "Canceled",  "Cleared",    "Completed",
    "DNS",          "Pre-1970",  "Qualified",  "DNS/CAN",
    "Submitted",    "Uncleared",
    ]

    
NameTypesMap = {
    _("Also Known As") : "Also Known As",
    _("Birth Name")    : "Birth Name",
    _("Married Name")  : "Married Name",
    _("Other Name")    : "Other Name",
    }

logical_functions = ['or', 'and', 'xor', 'one']
