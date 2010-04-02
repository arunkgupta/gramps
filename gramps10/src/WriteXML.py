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
"""
Contains the interface to allow a database to get written using
GRAMPS' XML file format.
"""

#-------------------------------------------------------------------------
#
# load standard python libraries
#
#-------------------------------------------------------------------------
import string
import time
import shutil
import os

from gnome.ui import GnomeErrorDialog

#-------------------------------------------------------------------------
#
# load GRAMPS libraries
#
#-------------------------------------------------------------------------
import const
import GrampsCfg
from RelLib import *
from Date import SingleDate
from intl import gettext
_ = gettext

#-------------------------------------------------------------------------
#
# Attempt to load the GZIP library. Some version of python do not seem
# to be compiled with this available.
#
#-------------------------------------------------------------------------
try:
    import gzip
    _gzip_ok = 1
except:
    _gzip_ok = 0

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def exportData(database, filename, callback):
    if os.path.isfile(filename):
        shutil.copy(filename, filename + ".bak")

    compress = GrampsCfg.uncompress ==0 and _gzip_ok == 1

    try:
        g = XmlWriter(database,callback,0,compress)
        g.write(filename)
    except:
        import DisplayTrace

        DisplayTrace.DisplayTrace()
        GnomeErrorDialog(_("Failure writing %s, original file restored") % filename)
        shutil.copy(filename + ".bak", filename)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def quick_write(database, filename,callback=None):
    g = XmlWriter(database,callback,0,1)
    g.write(filename)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class XmlWriter:
    """
    Writes a database to the XML file.
    """

    def __init__(self,db,callback,strip_photos,compress=1):
        """
        Initializes, but nots not write, and XML file.

        db - database to write
        callback - function to provide progress indication
        strip_photos - remove full paths off of media object paths
        compress - attempt to compress the database
        """
        self.compress = compress
        self.db = db
        self.callback = callback
        self.strip_photos = strip_photos
        
    def write(self,filename):
        """
        Write the database to the specfied file.
        """
        self.fileroot = os.path.dirname(filename)
        if self.compress:
            try:
                self.g = gzip.open(filename,"wb")
            except:
                self.g = open(filename,"w")
        else:
            self.g = open(filename,"w")

        self.write_xml_data()
        self.g.close()

    def write_handle(self,handle):
        """
        Write the database to the specfied file handle.
        """

        use_g = 0
        if self.compress:
            try:
                self.g = gzip.GzipFile(mode="wb",fileobj=handle)
                use_g = 1
            except:
                self.g = handle
        else:
            self.g = handle

        self.write_xml_data()
        if use_g:
            self.g.close()

    def write_xml_data(self):

        date = string.split(time.ctime(time.time()))
        owner = self.db.getResearcher()
        familyList = self.db.getFamilyMap().values()
        person_len = len(self.db.getPersonKeys())
        family_len = len(familyList)
        source_len = len(self.db.getSourceKeys())
        place_len = len(self.db.getPlaceKeys())
        objList = self.db.getObjectMap().values()
        
        total = person_len + family_len + place_len + source_len

        self.g.write('<?xml version="1.0" encoding="iso-8859-1"?>\n')
        self.g.write('<!DOCTYPE database SYSTEM "gramps.dtd" []>\n')
        self.g.write("<database>\n")
        self.g.write("  <header>\n")
        self.g.write("    <created date=\"%s %s %s\"" % (date[2],string.upper(date[1]),date[4]))
        self.g.write(" version=\"" + const.version + "\"")
        self.g.write(" people=\"%d\"" % person_len)
        self.g.write(" families=\"%d\"" % family_len)
        self.g.write(" sources=\"%d\"" % source_len)
        self.g.write(" places=\"%d\"/>\n" % place_len)
        self.g.write("    <researcher>\n")
        self.write_line("resname",owner.getName(),3)
        self.write_line("resaddr",owner.getAddress(),3)
        self.write_line("rescity",owner.getCity(),3)
        self.write_line("resstate",owner.getState(),3)
        self.write_line("rescountry",owner.getCountry(),3)
        self.write_line("respostal",owner.getPostalCode(),3)
        self.write_line("resphone",owner.getPhone(),3)
        self.write_line("resemail",owner.getEmail(),3)
        self.g.write("    </researcher>\n")
        self.g.write("  </header>\n")

        count = 0
        delta = max(int(total/50),1)

        if person_len > 0:
            self.g.write("  <people")
            person = self.db.getDefaultPerson()
            if person:
                self.g.write(' default="%s"' % person.getId())
            self.g.write(">\n")

            for key in self.db.getPersonKeys():
                person = self.db.getPerson(key)
                if not person:
                    GnomeErrorDialog("Person ID %s was NULL" % key)
                    continue
                if self.callback and count % delta == 0:
                    self.callback(float(count)/float(total))
                count = count + 1
            
                self.write_id("person",person,2)
                if person.getGender() == Person.male:
                    self.write_line("gender","M",3)
                elif person.getGender() == Person.female:
                    self.write_line("gender","F",3)
                else:
                    self.write_line("gender","U",3)
                self.dump_name("name",person.getPrimaryName(),3)
                for name in person.getAlternateNames():
                    self.dump_name("aka",name,3)
            
                self.write_line("uid",person.getPafUid(),3)
                self.write_line("nick",person.getNickName(),3)
                pos = person.getPosition()
                if pos != None:
                    self.g.write('      <pos x="%d" y="%d"/>\n'% pos)
                self.dump_my_event("Birth",person.getBirth(),3)
                self.dump_my_event("Death",person.getDeath(),3)
                for event in person.getEventList():
                    self.dump_event(event,3)
                
                self.dump_ordinance("baptism",person.getLdsBaptism(),3)
                self.dump_ordinance("endowment",person.getLdsEndowment(),3)
                self.dump_ordinance("sealed_to_parents",person.getLdsSeal(),3)

                self.write_photo_list(person.getPhotoList())

                if len(person.getAddressList()) > 0:
                    for address in person.getAddressList():
                        self.g.write('      <address%s>\n' % conf_priv(address))
                        self.write_date(address.getDateObj(),4)
                        self.write_line("street",address.getStreet(),4)
                        self.write_line("city",address.getCity(),4)
                        self.write_line("state",address.getState(),4)
                        self.write_line("country",address.getCountry(),4)
                        self.write_line("postal",address.getPostal(),4)
                        if address.getNote() != "":
                            self.write_note("note",address.getNote(),4)
                        for s in address.getSourceRefList():
                            self.dump_source_ref(s,4)
                        self.g.write('      </address>\n')

                self.write_attribute_list(person.getAttributeList())
                self.write_url_list(person.getUrlList())

                for alt in person.getParentList():
                    if alt[1] != "Birth":
                        mrel=' mrel="%s"' % alt[1]
                    else:
                        mrel=''
                    if alt[2] != "Birth":
                        frel=' frel="%s"' % alt[2]
                    else:
                        frel=''
                    self.g.write("      <childof ref=\"%s\"%s%s/>\n" % \
                            (alt[0].getId(), mrel, frel))

                for family in person.getFamilyList():
                    self.write_ref("parentin",family,3)

                self.write_note("note",person.getNote(),3)

                self.g.write("    </person>\n")
            self.g.write("  </people>\n")

        if family_len > 0:
            self.g.write("  <families>\n")
            
            for family in familyList:
                if self.callback and count % delta == 0:
                    self.callback(float(count)/float(total))
                count = count + 1
            
                self.write_family_id(family,2)
                self.write_ref("father",family.getFather(),3)
                self.write_ref("mother",family.getMother(),3)
                pos = family.getPosition()
                if pos != None:
                    self.g.write('      <pos x="%d" y="%d"/>\n'% pos)

                for event in family.getEventList():
                    self.dump_event(event,3)
                self.dump_ordinance("sealed_to_spouse",family.getLdsSeal(),3)

                self.write_photo_list(family.getPhotoList())

                if len(family.getChildList()) > 0:
                    for person in family.getChildList():
                        self.write_ref("child",person,3)
                self.write_attribute_list(family.getAttributeList())
                self.write_note("note",family.getNote(),3)
                self.g.write("    </family>\n")
            self.g.write("  </families>\n")

        if source_len > 0:
            self.g.write("  <sources>\n")
            for key in self.db.getSourceKeys():
                source = self.db.getSource(key)
                if not source:
                    d = self.db.getSourceDisplay(key)
                    GnomeErrorDialog("Database inconsistency found with sources\n"
                                     "Index found for %s (%s)\n"
                                     "but not included in tables - attempting to fix" % (d[0],d[1]))
                    continue
                if self.callback and count % delta == 0:
                    self.callback(float(count)/float(total))
                count = count + 1
                self.g.write("    <source id=\"" + source.getId() + "\">\n")
                self.write_force_line("stitle",source.getTitle(),3)
                self.write_line("sauthor",source.getAuthor(),3)
                self.write_line("spubinfo",source.getPubInfo(),3)
                self.write_line("scallno",source.getCallNumber(),3)
                if source.getNote() != "":
                    self.write_note("note",source.getNote(),3)
                self.write_photo_list(source.getPhotoList())
                self.g.write("    </source>\n")
            self.g.write("  </sources>\n")

        if place_len > 0:
            self.g.write("  <places>\n")
            for key in self.db.getPlaceKeys():
                try:
                    place = self.db.getPlace(key)
                    if self.callback and count % delta == 0:
                        self.callback(float(count)/float(total))
                    self.write_place_obj(place)
                except:
                    print "Could not find place %s" % key
                count = count + 1
                    
            self.g.write("  </places>\n")

        if len(objList) > 0:
            self.g.write("  <objects>\n")
            for object in objList:
                self.write_object(object)
            self.g.write("  </objects>\n")

        if len(self.db.getBookmarks()) > 0:
            self.g.write("  <bookmarks>\n")
            for person in self.db.getBookmarks():
                self.g.write('    <bookmark ref="%s"/>\n' % person.getId())
            self.g.write("  </bookmarks>\n")

        self.g.write("</database>\n")

    def fix(self,line):
        l = string.strip(line)
        l = string.replace(l,'&','&amp;')
        l = string.replace(l,'>','&gt;')
        l = string.replace(l,'<','&lt;')
        return string.replace(l,'"','&quot;')

    def write_note(self,val,note,indent=0):
        if not note:
            return
        if indent != 0:
            self.g.write("  " * indent)
        
        self.g.write("<%s>" % val)
        self.g.write(self.fix(string.rstrip(note)))
        self.g.write("</%s>\n" % val)
			
    def dump_event(self,event,index=1):
        if event:
            self.dump_my_event(event.getName(),event,index)

    def dump_my_event(self,name,event,index=1):
        if not event or event.is_empty():
            return

        sp = "  " * index
        self.g.write('%s<event type="%s"%s>\n' % (sp,self.fix(name),conf_priv(event)))
        self.write_date(event.getDateObj(),index+1)
        self.write_ref("place",event.getPlace(),index+1)
        self.write_line("cause",event.getCause(),index+1)
        self.write_line("description",event.getDescription(),index+1)
        if event.getNote():
            self.write_note("note",event.getNote(),index+1)
            
        for s in event.getSourceRefList():
            self.dump_source_ref(s,index+1)
        self.g.write("%s</event>\n" % sp)

    def dump_ordinance(self,name,ord,index=1):
        if not ord:
            return

        sp = "  " * index
        sp2 = "  " * (index+1)
        self.g.write('%s<lds_ord type="%s">\n' % (sp,self.fix(name)))
        dateobj = ord.getDateObj()
        if dateobj != None and not dateobj.isEmpty():
            self.write_date(dateobj,index+1)
        if ord.getTemple():
            self.g.write('%s<temple val="%s"/>\n' % (sp2,self.fix(ord.getTemple())))
        self.write_ref("place",ord.getPlace(),index+1)
        if ord.getStatus() != 0:
            self.g.write('%s<status val="%d"/>\n' % (sp2,ord.getStatus()))
        if ord.getFamily():
            self.g.write('%s<sealed_to ref="%s"/>\n' % (sp2,self.fix(ord.getFamily().getId())))
        if ord.getNote() != "":
            self.write_note("note",ord.getNote(),index+1)
        for s in ord.getSourceRefList():
            self.dump_source_ref(s,index+1)
        self.g.write('%s</lds_ord>\n' % sp)
    
    def dump_source_ref(self,source_ref,index=1):
        source = source_ref.getBase()
        if source:
            p = source_ref.getPage()
            c = source_ref.getComments()
            t = source_ref.getText()
            d = source_ref.getDate()
            q = source_ref.getConfidence()
            self.g.write("  " * index)
            if p == "" and c == "" and t == "" and d.isEmpty() and q == 2:
                self.g.write('<sourceref ref="%s"/>\n' % source.getId())
            else:
                if q == 2:
                    self.g.write('<sourceref ref="%s">\n' % source.getId())
                else:
                    self.g.write('<sourceref ref="%s" conf="%d">\n' % (source.getId(),q))
                self.write_line("spage",p,index+1)
                self.write_note("scomments",c,index+1)
                self.write_note("stext",t,index+1)
                self.write_date(d,index+1)
                self.g.write("%s</sourceref>\n" % ("  " * index))

    def write_ref(self,label,person,index=1):
        if person:
            self.g.write('%s<%s ref="%s"/>\n' % ("  "*index,label,person.getId()))

    def write_id(self,label,person,index=1):
        if person:
            self.g.write('%s<%s id="%s">\n' % ("  "*index,label,person.getId()))

    def write_family_id(self,family,index=1):
        if family:
            rel = family.getRelationship()
            sp = "  " * index
            self.g.write('%s<family id="%s"' % (sp,family.getId()))
            if rel != "":
                self.g.write(' type="%s">\n' % rel)
            else:
                self.g.write('>\n')

    def write_line(self,label,value,indent=1):
        if value:
            self.g.write('%s<%s>%s</%s>\n' % ('  '*indent,label,self.fix(value),label))

    def write_date(self,date,indent=1):
        sp = '  '*indent

        if date.isEmpty():
            return

        cal = date.get_calendar()
        if cal != 0:
            calstr = ' calendar="%s"' % self.fix(str(cal))
        else:
            calstr = ''

        if date.isRange():
            d1 = date.get_start_date().getIsoDate()
            d2 = date.get_stop_date().getIsoDate()
            self.g.write('%s<daterange start="%s" stop="%s"%s/>\n' % (sp,d1,d2,calstr))
        elif date.isValid():
            d1 = date.get_start_date()
            mode = d1.getModeVal()
            dstr = d1.getIsoDate()
            
            if mode == SingleDate.before:
                pref = ' type="before"'
            elif mode == SingleDate.after:
                pref = ' type="after"'
            elif mode == SingleDate.about:
                pref = ' type="about"'
            else:
                pref = ""
            
            self.g.write('%s<dateval val="%s"%s%s/>\n' % (sp,dstr,pref,calstr))
        else:
            self.g.write('%s<datestr val="%s"/>\n' %(sp,self.fix(date.getText())))

    def write_force_line(self,label,value,indent=1):
        if value != None:
            self.g.write('%s<%s>%s</%s>\n' % ('  '*indent,label,self.fix(value),label))

    def dump_name(self,label,name,index=1):
        sp = "  "*index
        type = name.getType()
        if type:
            self.g.write('%s<%s type="%s"%s>\n' % (sp,label,type,conf_priv(name)))
        else:
            self.g.write('%s<%s%s>\n' % (sp,label,conf_priv(name)))
        self.write_line("first",name.getFirstName(),index+1)
        self.write_line("last",name.getSurname(),index+1)
        self.write_line("suffix",name.getSuffix(),index+1)
        self.write_line("title",name.getTitle(),index+1)
        if name.getNote() != "":
            self.write_note("note",name.getNote(),index+1)
        for s in name.getSourceRefList():
            self.dump_source_ref(s,index+1)
    
        self.g.write('%s</%s>\n' % (sp,label))

    def append_value(self,orig,val):
        if orig:
            return "%s, %s" % (orig,val)
        else:
            return val

    def build_place_title(self,loc):
        "Builds a title from a location"
        city = self.fix(loc.get_city())
        parish = self.fix(loc.get_parish())
        state = self.fix(loc.get_state())
        country = self.fix(loc.get_country())
        county = self.fix(loc.get_county())

        value = ""

        if city:
            value = city
        if parish:
            value = self.append_value(value,parish)
        if county:
            value = self.append_value(value,county)
        if state:
            value = self.append_value(value,state)
        if country:
            value = self.append_value(value,country)
        return value

    def dump_location(self,loc):
        "Writes the location information to the output file"
        city = self.fix(loc.get_city())
        parish = self.fix(loc.get_parish())
        state = self.fix(loc.get_state())
        country = self.fix(loc.get_country())
        county = self.fix(loc.get_county())
        
        if not city and not state and not parish and not county and not country:
            return
    
        self.g.write('      <location')
        if city:
            self.g.write(' city="%s"' % city)
        if parish:
            self.g.write(' parish="%s"' % parish)
        if county:
            self.g.write(' county="%s"' % county)
        if state:
            self.g.write(' state="%s"' % state)
        if country:
            self.g.write(' country="%s"' % country)
        self.g.write('/>\n')

    def write_attribute_list(self, list, indent=3):
        sp = '  ' * indent
        for attr in list:
            self.g.write('%s<attribute%s type="%s" value="%s"' % \
                         (sp,conf_priv(attr),attr.getType(),self.fix(attr.getValue())))
            slist = attr.getSourceRefList()
            note = attr.getNote()
            if note == "" and len(slist) == 0:
                self.g.write('/>\n')
            else:
                self.g.write('>\n')
                for s in attr.getSourceRefList():
                    self.dump_source_ref(s,indent+1)
                self.write_note("note",attr.getNote(),4)
                self.g.write('%s</attribute>\n' % sp)

    def write_photo_list(self,list,indent=3):
        sp = '  '*indent
        for photo in list:
            mobj = photo.getReference()
            self.g.write('%s<objref ref="%s"' % (sp,mobj.getId()))
            if photo.getPrivacy():
                self.g.write(' priv="1"')
            proplist = photo.getAttributeList()
            if len(proplist) == 0 and photo.getNote() == "":
                self.g.write("/>\n")
            else:
                self.g.write(">\n")
                self.write_attribute_list(proplist,indent+1)
                self.write_note("note",photo.getNote(),indent+1)
                self.g.write('%s</objref>\n' % sp)

    def write_url_list(self,list):
        for url in list:
            self.g.write('      <url priv="%d" href="%s"' % \
                         (url.getPrivacy(),self.fix(url.get_path())))
            if url.get_description() != "":
                self.g.write(' description="%s"' % self.fix(url.get_description()))
            self.g.write('/>\n')

    def write_place_obj(self,place):
        title = self.fix(place.get_title())
        long = self.fix(place.get_longitude())
        lat = self.fix(place.get_latitude())
        id = place.getId()
        main_loc = place.get_main_location()
        llen = len(place.get_alternate_locations()) + len(place.getUrlList()) + \
               len(place.getPhotoList()) + len(place.getSourceRefList())
                                                      
        ml_empty = main_loc.is_empty()
        note = place.getNote()

        if title == "":
            title = self.fix(self.build_place_title(place.get_main_location()))
    
        self.g.write('    <placeobj id="%s" title="%s"' % (id,title))

        if long or lat or not ml_empty or llen > 0 or note:
            self.g.write('>\n')
        else:
            self.g.write('/>\n')
            return
    
        if long or lat:
            self.g.write('      <coord long="%s" lat="%s"/>\n' % (long,lat))

        self.dump_location(main_loc)
        for loc in place.get_alternate_locations():
            self.dump_location(loc)
        self.write_photo_list(place.getPhotoList())
        self.write_url_list(place.getUrlList())
        if note != "":
            self.write_note("note",note,3)
        for s in place.getSourceRefList():
            self.dump_source_ref(s,3)
        self.g.write("    </placeobj>\n")

    def write_object(self,object):
        id = object.getId()
        type = object.getMimeType()
        path = object.getPath()
        if self.strip_photos:
            path = os.path.basename(path)
        else:
            l = len(self.fileroot)
            if len(path) >= l:
                if self.fileroot == path[0:l]:
                    path = path[l+1:]
        self.g.write('    <object id="%s" src="%s" mime="%s"' % (id,path,type))
        self.g.write(' description="%s"' % self.fix(object.getDescription()))
        alist = object.getAttributeList()
        note = object.getNote()
        slist = object.getSourceRefList()
        if len(alist) == 0 and len(slist) == 0 and note == "":
            self.g.write('/>\n')
        else:
            self.g.write('>\n')
            self.write_attribute_list(alist)
            if note != "":
                self.write_note("note",note,3)
            for s in slist:
                self.dump_source_ref(s,3)
            self.g.write("    </object>\n")

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def sortById(first,second):
    fid = first.getId()
    sid = second.getId()

    if fid < sid:
        return -1
    else:
        return fid != sid

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def conf_priv(obj):
    if obj.getPrivacy() != 0:
        return ' priv="%d"' % obj.getPrivacy()
    else:
        return ''
