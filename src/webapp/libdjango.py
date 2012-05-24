# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009         Douglas S. Blank <doug.blank@gmail.com>
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
#

""" Interface to Django models """

#------------------------------------------------------------------------
#
# Python Modules
#
#------------------------------------------------------------------------
import time
import sys
import cPickle
import base64

#------------------------------------------------------------------------
#
# Gramps Modules
#
#------------------------------------------------------------------------
import webapp.grampsdb.models as models
from django.contrib.contenttypes.models import ContentType
import webapp
import gen

# To get a django person from a django database:
#    djperson = dji.Person.get(handle='djhgsdh324hjg234hj24')
# 
# To turn the djperson into a Gramps Person:
#    tuple = dji.get_person(djperson)
#    gperson = lib.gen.Person(tuple)
# OR
#    gperson = dbdjango.DbDjango().get_person_from_handle(handle)

#-------------------------------------------------------------------------
#
# Import functions
#
#-------------------------------------------------------------------------
def lookup_role_index(role0, event_ref_list):
    """
    Find the handle in a unserialized event_ref_list and return code.
    """
    if role0 is None:
        return -1
    else:
        count = 0
        for event_ref in event_ref_list:
            (private, note_list, attribute_list, ref, erole) = event_ref
            try:
                event = models.Event.objects.get(handle=ref)
            except:
                return -1
            if event.event_type[0] == role0:
                return count
            count += 1
        return -1

def totime(dtime):
    if dtime:
        return int(time.mktime(dtime.timetuple()))
    else:
        return 0

#-------------------------------------------------------------------------
#
# Export functions
#
#-------------------------------------------------------------------------
def todate(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))

def lookup(index, event_ref_list):
    """
    Get the unserialized event_ref in an list of them and return it.
    """
    if index < 0:
        return None
    else:
        count = 0
        for event_ref in event_ref_list:
            (private, note_list, attribute_list, ref, role) = event_ref
            if index == count:
                return ref
            count += 1
        return None

def get_datamap(grampsclass):
    return [x[0] for x in grampsclass._DATAMAP if x[0] != grampsclass.CUSTOM]

#-------------------------------------------------------------------------
#
# Django Interface
#
#-------------------------------------------------------------------------
class DjangoInterface(object):
    """
    DjangoInterface for interoperating between Gramps and Django.
    
    This interface comes in a number of parts: 
        get_ITEMS()
        add_ITEMS()

    get_ITEM(ITEM)

    Given an ITEM from a Django table, construct a Gramps Raw Data tuple.

    add_ITEM(data)

    Given a Gramps Raw Data tuple, add the data to the Django tables.
    

    """
    def __init__(self):
        self.debug = 0

    def __getattr__(self, name):
        """
        Django Objects database interface.

        >>> self.Person.all()
        >>> self.Person.get(id=1)
        >>> self.Person.get(handle='gh71234dhf3746347734')
        """
        if hasattr(models, name):
            return getattr(models, name).objects
        else:
            raise AttributeError("no such model: '%s'" % name)

    def get_model(self, name):
        if hasattr(models, name):
            return getattr(models, name)
        else:
            raise AttributeError("no such model: '%s'" % name)

    # -----------------------------------------------
    # Get methods to retrieve list data from the tables
    # -----------------------------------------------

    def clear_tables(self, *args):
        return models.clear_tables(*args)

    def get_attribute_list(self, obj):
        obj_type = ContentType.objects.get_for_model(obj)
        attribute_list = models.Attribute.objects.filter(object_id=obj.id, 
                                                     object_type=obj_type)
        return map(self.pack_attribute, attribute_list)

    def get_primary_name(self, person):
        names = person.name_set.filter(preferred=True).order_by("order")
        if len(names) > 0:
            return gen.lib.Name.create(self.pack_name(names[0]))
        else:
            return gen.lib.Name()
      
    def get_alternate_names(self, person):
        names = person.name_set.filter(preferred=False).order_by("order")
        return [gen.lib.Name.create(self.pack_name(n)) for n in names]

    def get_names(self, person, preferred):
        names = person.name_set.filter(preferred=preferred).order_by("order")
        if preferred:
            if len(names) > 0:
                return self.pack_name(names[0])
            else:
                return gen.lib.Name().serialize()
        else:
            return map(self.pack_name, names)
     
    def get_source_datamap(self, source): 
        return dict([map.key, map.value] for map in source.sourcedatamap_set.all())

    def get_citation_datamap(self, citation): 
        return dict([map.key, map.value] for map in citation.citationdatamap_set.all())

    def get_media_list(self, obj):
        obj_type = ContentType.objects.get_for_model(obj)
        mediarefs = models.MediaRef.objects.filter(object_id=obj.id, 
                                               object_type=obj_type)
        return map(self.pack_media_ref, mediarefs)

    def get_note_list(self, obj):
        obj_type = ContentType.objects.get_for_model(obj)
        noterefs = models.NoteRef.objects.filter(object_id=obj.id, 
                                             object_type=obj_type)
        return [noteref.ref_object.handle for noteref in noterefs]

    def get_repository_ref_list(self, obj):
        obj_type = ContentType.objects.get_for_model(obj)
        reporefs = models.RepositoryRef.objects.filter(object_id=obj.id, 
                                                   object_type=obj_type)
        return map(self.pack_repository_ref, reporefs)

    def get_url_list(self, obj):
        return map(self.pack_url, obj.url_set.all().order_by("order"))

    def get_address_list(self, obj, with_parish): # person or repository
        addresses = obj.address_set.all().order_by("order")
        return [self.pack_address(address, with_parish)
                    for address in addresses]

    def get_child_ref_list(self, family):
        obj_type = ContentType.objects.get_for_model(family)
        childrefs = models.ChildRef.objects.filter(object_id=family.id,
                                        object_type=obj_type).order_by("order")
        return map(self.pack_child_ref, childrefs)

    def get_citation_list(self, obj):
        obj_type = ContentType.objects.get_for_model(obj)
        citationrefs = models.CitationRef.objects.filter(object_id=obj.id,
                                                         object_type=obj_type).order_by("order")
        return [citationref.citation.handle for citationref in citationrefs]

    def get_event_refs(self, obj, order="order"):
        obj_type = ContentType.objects.get_for_model(obj)
        eventrefs = models.EventRef.objects.filter(object_id=obj.id,
                                        object_type=obj_type).order_by(order)
        return eventrefs

    def get_event_ref_list(self, obj):
        obj_type = ContentType.objects.get_for_model(obj)
        eventrefs = models.EventRef.objects.filter(object_id=obj.id,
                                        object_type=obj_type).order_by("order")
        return map(self.pack_event_ref, eventrefs)

    def get_family_list(self, person): # person has families
        return [fam.handle for fam in person.families.all()]

    def get_parent_family_list(self, person):
        return [fam.handle for fam in person.parent_families.all()]

    def get_person_ref_list(self, person):
        obj_type = ContentType.objects.get_for_model(person)
        return map(self.pack_person_ref, 
                models.PersonRef.objects.filter(object_id=person.id, 
                                            object_type=obj_type))

    def get_lds_list(self, obj): # person or family
        return map(self.pack_lds, obj.lds_set.all().order_by("order"))

    def get_place_handle(self, obj): # obj is event
        if obj.place:
            return obj.place.handle
        return ''

    ## Packers:

    def get_event(self, event):
        handle = event.handle
        gid = event.gramps_id
        the_type = tuple(event.event_type)
        description = event.description
        change = totime(event.last_changed)
        private = event.private
        note_list = self.get_note_list(event)           
        citation_list = self.get_citation_list(event)   
        media_list = self.get_media_list(event)         
        attribute_list = self.get_attribute_list(event)
        date = self.get_date(event)
        place = self.get_place_handle(event)
        return (str(handle), gid, the_type, date, description, place, 
                citation_list, note_list, media_list, attribute_list,
                change, private)

    def get_note(self, note):
        styled_text = [note.text, []]
        markups = models.Markup.objects.filter(note=note).order_by("order")
        for markup in markups:
            value = markup.string
            start_stop_list  = markup.start_stop_list
            ss_list = eval(start_stop_list)
            styled_text[1] += [(tuple(markup.markup_type), 
                                value, ss_list)]
        changed = totime(note.last_changed)
        return (str(note.handle), 
                note.gramps_id, 
                styled_text, 
                note.preformatted, 
                tuple(note.note_type), 
                changed, 
                tuple(note.make_tag_list()), 
                note.private)

    def get_family(self, family):
        child_ref_list = self.get_child_ref_list(family)
        event_ref_list = self.get_event_ref_list(family)
        media_list = self.get_media_list(family)
        attribute_list = self.get_attribute_list(family)
        lds_seal_list = self.get_lds_list(family)
        citation_list = self.get_citation_list(family)
        note_list = self.get_note_list(family)
        if family.father:
            father_handle = family.father.handle
        else:
            father_handle = ''
        if family.mother:
            mother_handle = family.mother.handle
        else:
            mother_handle = ''
        return (str(family.handle), family.gramps_id, 
                father_handle, mother_handle,
                child_ref_list, tuple(family.family_rel_type), 
                event_ref_list, media_list,
                attribute_list, lds_seal_list, 
                citation_list, note_list,
                totime(family.last_changed), 
                tuple(family.make_tag_list()), 
                family.private)

    def get_repository(self, repository):
        note_list = self.get_note_list(repository)
        address_list = self.get_address_list(repository, with_parish=False)
        url_list = self.get_url_list(repository)
        return (str(repository.handle), 
                repository.gramps_id, 
                tuple(repository.repository_type),
                repository.name, 
                note_list,
                address_list, 
                url_list, 
                totime(repository.last_changed), 
                repository.private)

    def get_citation(self, citation):
        note_list = self.get_note_list(citation)
        media_list = self.get_media_list(citation)
        datamap = self.get_citation_datamap(citation)
        date = self.get_date(citation)
        return (str(citation.handle),  
                citation.gramps_id, 
                date,
                citation.page, 
                citation.confidence, 
                citation.source.handle,
                note_list, 
                media_list, 
                datamap, 
                totime(citation.last_changed), 
                citation.private) 

    def get_source(self, source):
        note_list = self.get_note_list(source)
        media_list = self.get_media_list(source)
        datamap = self.get_source_datamap(source)
        reporef_list = self.get_repository_ref_list(source)
        return (str(source.handle), 
                source.gramps_id, 
                source.title,
                source.author, 
                source.pubinfo,
                note_list,
                media_list,
                source.abbrev,
                totime(source.last_changed), 
                datamap,
                reporef_list,
                source.private)

    def get_media(self, media):
        attribute_list = self.get_attribute_list(media)
        citation_list = self.get_citation_list(media)
        note_list = self.get_note_list(media)
        date = self.get_date(media)
        return (str(media.handle), 
                media.gramps_id, 
                media.path, 
                media.mime, 
                media.desc,
                attribute_list,
                citation_list,
                note_list,
                totime(media.last_changed),
                date,
                tuple(media.make_tag_list()),
                media.private)

    def get_person(self, person):
        primary_name = self.get_names(person, True) # one
        alternate_names = self.get_names(person, False) # list
        event_ref_list = self.get_event_ref_list(person)
        family_list = self.get_family_list(person)
        parent_family_list = self.get_parent_family_list(person)
        media_list = self.get_media_list(person)
        address_list = self.get_address_list(person, with_parish=False)
        attribute_list = self.get_attribute_list(person)
        url_list = self.get_url_list(person)
        lds_ord_list = self.get_lds_list(person)
        pcitation_list = self.get_citation_list(person)
        pnote_list = self.get_note_list(person)
        person_ref_list = self.get_person_ref_list(person)
        # This looks up the events for the first EventType given:
        death_ref_index = person.death_ref_index
        birth_ref_index = person.birth_ref_index

        return (str(person.handle),
                person.gramps_id,  
                tuple(person.gender_type)[0],
                primary_name,       
                alternate_names,    
                death_ref_index,    
                birth_ref_index,    
                event_ref_list,     
                family_list,        
                parent_family_list, 
                media_list,         
                address_list,       
                attribute_list,     
                url_list,               
                lds_ord_list,       
                pcitation_list,       
                pnote_list,         
                totime(person.last_changed),             
                tuple(person.make_tag_list()), 
                person.private,            
                person_ref_list)

    def get_date(self, obj):
        if ((obj.calendar == obj.modifier == obj.quality == obj.sortval == obj.newyear == 0) and
            obj.text == "" and (not obj.slash1) and (not obj.slash2) and 
            (obj.day1 == obj.month1 == obj.year1 == 0) and 
            (obj.day2 == obj.month2 == obj.year2 == 0)):
            return None
        elif ((not obj.slash1) and (not obj.slash2) and 
            (obj.day2 == obj.month2 == obj.year2 == 0)):
            dateval = (obj.day1, obj.month1, obj.year1, obj.slash1)
        else:
            dateval = (obj.day1, obj.month1, obj.year1, obj.slash1, 
                       obj.day2, obj.month2, obj.year2, obj.slash2)
        return (obj.calendar, obj.modifier, obj.quality, dateval, 
                obj.text, obj.sortval, obj.newyear)

    def get_place(self, place):
        locations = place.location_set.all().order_by("order")
        main_loc = None
        alt_location_list = []
        for location in locations:
            if main_loc is None:
                main_loc = self.pack_location(location, True)
            else:
                alt_location_list.append(self.pack_location(location, True))
        url_list = self.get_url_list(place)
        media_list = self.get_media_list(place)
        citation_list = self.get_citation_list(place)
        note_list = self.get_note_list(place)
        return (str(place.handle), 
                place.gramps_id,
                place.title, 
                place.long, 
                place.lat,
                main_loc, 
                alt_location_list,
                url_list,
                media_list,
                citation_list,
                note_list,
                totime(place.last_changed), 
                place.private)

    # ---------------------------------
    # Packers
    # ---------------------------------

    ## The packers build GRAMPS raw unserialized data.

    ## Reference packers

    def pack_child_ref(self, child_ref):
        citation_list = self.get_citation_list(child_ref)
        note_list = self.get_note_list(child_ref) 
        return (child_ref.private, citation_list, note_list, child_ref.ref_object.handle, 
                tuple(child_ref.father_rel_type), tuple(child_ref.mother_rel_type))

    def pack_person_ref(self, personref):
        citation_list = self.get_citation_list(personref)
        note_list = self.get_note_list(personref)
        return (personref.private, 
                citation_list,
                note_list,
                personref.ref_object.handle,
                personref.description)

    def pack_media_ref(self, media_ref):
        citation_list = self.get_citation_list(media_ref)
        note_list = self.get_note_list(media_ref)
        attribute_list = self.get_attribute_list(media_ref)
        if ((media_ref.x1 == media_ref.y1 == media_ref.x2 == media_ref.y2 == -1) or
            (media_ref.x1 == media_ref.y1 == media_ref.x2 == media_ref.y2 == 0)):
            role = None
        else:
            role = (media_ref.x1, media_ref.y1, media_ref.x2, media_ref.y2)
        return (media_ref.private, citation_list, note_list, attribute_list, 
                media_ref.ref_object.handle, role)

    def pack_repository_ref(self, repo_ref):
        note_list = self.get_note_list(repo_ref)
        return (note_list, 
                repo_ref.ref_object.handle,
                repo_ref.call_number, 
                tuple(repo_ref.source_media_type),
                repo_ref.private)

    def pack_media_ref(self, media_ref):
        note_list = self.get_note_list(media_ref)
        attribute_list = self.get_attribute_list(media_ref)
        citation_list = self.get_citation_list(media_ref)
        return (media_ref.private, citation_list, note_list, attribute_list, 
                media_ref.ref_object.handle, (media_ref.x1,
                                              media_ref.y1,
                                              media_ref.x2,
                                              media_ref.y2))
    
    def pack_event_ref(self, event_ref):
        note_list = self.get_note_list(event_ref)
        attribute_list = self.get_attribute_list(event_ref)
        return (event_ref.private, note_list, attribute_list, 
                event_ref.ref_object.handle, tuple(event_ref.role_type))

    def pack_citation(self, citation):
        handle = citation.handle
        gid = citation.gramps_id
        date = self.get_date(citation)
        page = citation.page
        confidence = citation.confidence
        source_handle = citation.source.handle
        note_list = self.get_note_list(citation)
        media_list = self.get_media_list(citation)
        datamap = self.get_citation_datamap(citation)
        changed = totime(citation.last_changed)
        private = citation.private
        return (handle, gid, date, page, confidence, source_handle,
                note_list, media_list, datamap, changed, private) 

    def pack_address(self, address, with_parish):
        citation_list = self.get_citation_list(address)
        date = self.get_date(address)
        note_list = self.get_note_list(address)
        locations = address.location_set.all().order_by("order")
        if len(locations) > 0:
            location = self.pack_location(locations[0], with_parish)
        else:
            if with_parish:
                location = (("", "", "", "", "", "", ""), "")
            else:
                location = ("", "", "", "", "", "", "")
        return (address.private, citation_list, note_list, date, location)

    def pack_lds(self, lds):
        citation_list = self.get_citation_list(lds)
        note_list = self.get_note_list(lds)
        date = self.get_date(lds)
        if lds.famc:
            famc = lds.famc.handle
        else:
            famc = None
        place = self.get_place_handle(lds)
        return (citation_list, note_list, date, lds.lds_type[0], place,
                famc, lds.temple, lds.status[0], lds.private)

    def pack_source(self, source):
        note_list = self.get_note_list(source)
        media_list = self.get_media_list(source)
        reporef_list = self.get_repository_ref_list(source)
        datamap = self.get_source_datamap(source)
        return (source.handle, source.gramps_id, source.title,
                source.author, source.pubinfo,
                note_list,
                media_list,
                source.abbrev,
                totime(last_changed), datamap,
                reporef_list,
                source.private)

    def pack_name(self, name):
        citation_list = self.get_citation_list(name)
        note_list = self.get_note_list(name)
        date = self.get_date(name)
        return (name.private, citation_list, note_list, date,
                name.first_name, name.make_surname_list(), name.suffix,
                name.title, tuple(name.name_type), 
                name.group_as, name.sort_as.val, 
                name.display_as.val, name.call, name.nick, 
                name.famnick)

    def pack_location(self, loc, with_parish):
        if with_parish:
            return ((loc.street, loc.locality, loc.city, loc.county, loc.state, loc.country, 
                     loc.postal, loc.phone), loc.parish)
        else:
            return (loc.street, loc.locality, loc.city, loc.county, loc.state, loc.country, 
                    loc.postal, loc.phone)

    def pack_url(self, url):
        return  (url.private, url.path, url.desc, tuple(url.url_type))

    def pack_attribute(self, attribute):
        citation_list = self.get_citation_list(attribute)
        note_list = self.get_note_list(attribute)
        return (attribute.private, 
                citation_list, 
                note_list, 
                tuple(attribute.attribute_type), 
                attribute.value)


    ## Export lists:
    
    def add_child_ref_list(self, obj, ref_list):
        ## Currently, only Family references children
        for child_data in ref_list:
            self.add_child_ref(obj, child_data)
    
    def add_citation_list(self, obj, citation_list):
        for citation_handle in citation_list:
            self.add_citation_ref(obj, citation_handle)
    
    def add_event_ref_list(self, obj, event_ref_list):
        for event_ref in event_ref_list:
            self.add_event_ref(obj, event_ref)
    
    def add_surname_list(self, name, surname_list):
        order = 1
        for data in surname_list:
            (surname_text, prefix, primary, origin_type,
             connector) = data
            surname = models.Surname()
            surname.surname = surname_text
            surname.prefix = prefix
            surname.primary = primary
            surname.name_origin_type = models.get_type(models.NameOriginType, 
                                                       origin_type)
            surname.connector = connector
            surname.name = name
            surname.order = order
            surname.save() 
            order += 1

    def add_note_list(self, obj, note_list):
        for handle in note_list:
            # Just the handle
            try:
                note = models.Note.objects.get(handle=handle)
                self.add_note_ref(obj, note)
            except:
                print >> sys.stderr, ("ERROR: Note does not exist: '%s'" % 
                                      handle)
    
    def add_alternate_name_list(self, person, alternate_names):
        for name in alternate_names:
            if name:
                self.add_name(person, name, False)
    
    def add_parent_family_list(self, person, parent_family_list):
        for parent_family_data in parent_family_list:
            self.add_parent_family(person, parent_family_data)
    
    def add_media_ref_list(self, person, media_list):
        for media_data in media_list:
            self.add_media_ref(person, media_data)
    
    def add_attribute_list(self, obj, attribute_list):
        for attribute_data in attribute_list:
            self.add_attribute(obj, attribute_data)
    
    def add_url_list(self, field, obj, url_list):
        if not url_list: return None
        count = 1
        for url_data in url_list:
            self.add_url(field, obj, url_data, count) 
            count += 1
            
    def add_person_ref_list(self, obj, person_ref_list):
        for person_ref_data in person_ref_list:
            self.add_person_ref(obj, person_ref_data)
    
    def add_address_list(self, field, obj, address_list):
        count = 1
        for address_data in address_list:
            self.add_address(field, obj, address_data, count)
            count += 1
    
    def add_lds_list(self, field, obj, lds_ord_list):
        count = 1
        for ldsord in lds_ord_list:
            lds = self.add_lds(field, obj, ldsord, count)
            #obj.lds_list.add(lds)
            #obj.save()
            count += 1
    
    def add_repository_ref_list(self, obj, reporef_list):
        for data in reporef_list:
            self.add_repository_ref(obj, data)
    
    def add_family_ref_list(self, person, family_list):
        for family_handle in family_list:
            self.add_family_ref(person, family_handle) 
    
    ## Export reference objects:
    
    def add_person_ref(self, obj, person_ref_data):
        (private, 
         citation_list,
         note_list,
         handle,
         desc) = person_ref_data
        try:
            person = models.Person.objects.get(handle=handle)
        except:
            print >> sys.stderr, ("ERROR: Person does not exist: '%s'" % 
                                  handle)
            return
            
        count = person.references.count()
        person_ref = models.PersonRef(referenced_by=obj,
                                  ref_object=person,
                                  private=private,
                                  order=count + 1,
                                  description=desc)
        person_ref.save()
        self.add_note_list(person_ref, note_list)
        self.add_citation_list(person_ref, citation_list)
    
    def add_note_ref(self, obj, note):
        count = note.references.count()
        note_ref = models.NoteRef(referenced_by=obj, 
                              ref_object=note,
                              private=False,
                              order=count + 1)
        note_ref.save()
    
    def add_media_ref(self, obj, media_ref_data):
        (private, citation_list, note_list, attribute_list, 
         ref, role) = media_ref_data
        try:
            media = models.Media.objects.get(handle=ref)
        except:
            print >> sys.stderr, ("ERROR: Media does not exist: '%s'" % 
                                  ref)
            return
        count = media.references.count()
        if not role:
            role = (0,0,0,0)
        media_ref = models.MediaRef(referenced_by=obj, 
                                ref_object=media,
                                x1=role[0],
                                y1=role[1],
                                x2=role[2],
                                y2=role[3],
                                private=private,
                                order=count + 1)
        media_ref.save()
        self.add_note_list(media_ref, note_list)
        self.add_attribute_list(media_ref, attribute_list)
        self.add_citation_list(media_ref, citation_list)
    
    def add_citation_ref(self, obj, handle):
        try:
            citation = models.Citation.objects.get(handle=handle)
        except:
            print >> sys.stderr, ("ERROR: Citation does not exist: '%s'" % 
                                  handle)
            return

        count = models.CitationRef.objects.filter(object_id=obj.id,object_type=obj).count()
        citation_ref = models.CitationRef(private=False,
                                          referenced_by=obj,
                                          citation=citation,
                                          order=count + 1)
        citation_ref.save()

    def add_citation(self, citation_data):
        (handle, gid, date, page, confidence, source_handle, note_list,
         media_list, datamap, changed, private) = citation_data
        citation = models.Citation(
            handle=handle,
            gramps_id=gid,
            private=private, 
            last_changed=todate(changed),
            confidence=confidence, 
            page=page)
        citation.save()

    def add_citation_detail(self, citation_data):
        (handle, gid, date, page, confidence, source_handle, note_list,
         media_list, datamap, change, private) = citation_data
        try:
            citation = models.Citation.objects.get(handle=handle)
        except:
            print >> sys.stderr, ("ERROR: Citation does not exist: '%s'" % 
                                  handle)
            return
        try:
            source = models.Source.objects.get(handle=source_handle)
        except:
            print >> sys.stderr, ("ERROR: Source does not exist: '%s'" % 
                                  source_handle)
            return
        citation.source = source
        self.add_date(citation, date)
        citation.save()
        self.add_note_list(citation, note_list) 
        self.add_media_ref_list(citation, media_list) 
        self.add_citation_datamap_dict(citation, datamap)

    def add_child_ref(self, obj, data):
        (private, citation_list, note_list, ref, frel, mrel) = data
        try:
            child = models.Person.objects.get(handle=ref)
        except:
            print >> sys.stderr, ("ERROR: Person does not exist: '%s'" % 
                                  ref)
            return
        count = models.ChildRef.objects.filter(object_id=obj.id,object_type=obj).count()
        child_ref = models.ChildRef(private=private,
                                referenced_by=obj,
                                ref_object=child,
                                order=count + 1,
                                father_rel_type=models.get_type(models.ChildRefType, frel),
                                mother_rel_type=models.get_type(models.ChildRefType, mrel))
        child_ref.save()
        self.add_citation_list(child_ref, citation_list)
        self.add_note_list(child_ref, note_list)
    
    def add_event_ref(self, obj, event_data):
        (private, note_list, attribute_list, ref, role) = event_data
        try:
            event = models.Event.objects.get(handle=ref)
        except:
            print >> sys.stderr, ("ERROR: Event does not exist: '%s'" % 
                                  ref)
            return
        count = models.EventRef.objects.filter(object_id=obj.id,object_type=obj).count()
        event_ref = models.EventRef(private=private,
                                referenced_by=obj,
                                ref_object=event,
                                order=count + 1,
                                role_type = models.get_type(models.EventRoleType, role))
        event_ref.save()
        self.add_note_list(event_ref, note_list)
        self.add_attribute_list(event_ref, attribute_list)
    
    def add_repository_ref(self, obj, reporef_data):
        (note_list, 
         ref,
         call_number, 
         source_media_type,
         private) = reporef_data
        try:
            repository = models.Repository.objects.get(handle=ref)
        except:
            print >> sys.stderr, ("ERROR: Repository does not exist: '%s'" % 
                                  ref)
            return
        count = models.RepositoryRef.objects.filter(object_id=obj.id,object_type=obj).count()
        repos_ref = models.RepositoryRef(private=private,
                                     referenced_by=obj,
                                     call_number=call_number,
                                     source_media_type=models.get_type(models.SourceMediaType,
                                                                source_media_type),
                                     ref_object=repository,
                                     order=count + 1)
        repos_ref.save()
        self.add_note_list(repos_ref, note_list)
    
    def add_family_ref(self, obj, handle):
        try:
            family = models.Family.objects.get(handle=handle)
        except:
            print >> sys.stderr, ("ERROR: Family does not exist: '%s'" % 
                                  handle)
            return
        obj.families.add(family)
        obj.save()
    
    ## Export individual objects:
    
    def add_source_datamap_dict(self, source, datamap_dict):
        for key in datamap_dict:
            value = datamap_dict[key]
            datamap = models.SourceDatamap(key=key, value=value)
            datamap.source = source
            datamap.save()
    
    def add_citation_datamap_dict(self, citation, datamap_dict):
        for key in datamap_dict:
            value = datamap_dict[key]
            datamap = models.CitationDatamap(key=key, value=value)
            datamap.citation = citation
            datamap.save()
    
    def add_lds(self, field, obj, data, order):
        (lcitation_list, lnote_list, date, type, place_handle,
         famc_handle, temple, status, private) = data
        if place_handle:
            try:
                place = models.Place.objects.get(handle=place_handle)
            except:
                print >> sys.stderr, ("ERROR: Place does not exist: '%s'" % 
                                      place_handle)
                place = None
        else:
            place = None
        if famc_handle:
            try:
                famc = models.Family.objects.get(handle=famc_handle)
            except:
                print >> sys.stderr, ("ERROR: Family does not exist: '%s'" % 
                                      famc_handle)
                famc = None
        else:
            famc = None
        lds = models.Lds(lds_type = models.get_type(models.LdsType, type),
                     temple=temple, 
                     place=place,
                     famc=famc,
                     order=order,
                     status = models.get_type(models.LdsStatus, status),
                     private=private)
        self.add_date(lds, date)
        lds.save()
        self.add_note_list(lds, lnote_list)
        self.add_citation_list(lds, lcitation_list)
        if field == "person":
            lds.person = obj
        elif field == "family":
            lds.family = obj
        else:
            raise AttributeError("invalid field '%s' to attach lds" %
                                 field)
        lds.save()
        return lds
    
    def add_address(self, field, obj, address_data, order):
        (private, acitation_list, anote_list, date, location) = address_data
        address = models.Address(private=private, order=order)
        self.add_date(address, date)
        address.save()
        self.add_location("address", address, location, 1)
        self.add_note_list(address, anote_list) 
        self.add_citation_list(address, acitation_list)
        if field == "person":
            address.person = obj
        elif field == "repository":
            address.repository = obj
        else:
            raise AttributeError("invalid field '%s' to attach address" %
                                 field)
        address.save()
        #obj.save()
        #obj.addresses.add(address)
        #obj.save()
    
    def add_attribute(self, obj, attribute_data):
        (private, citation_list, note_list, the_type, value) = attribute_data
        attribute_type = models.get_type(models.AttributeType, the_type)
        attribute = models.Attribute(private=private,
                                 attribute_of=obj,
                                 attribute_type=attribute_type,
                                 value=value)
        attribute.save()
        self.add_citation_list(attribute, citation_list)
        self.add_note_list(attribute, note_list)
        #obj.attributes.add(attribute)
        #obj.save()
    
    def add_url(self, field, obj, url_data, order):
        (private, path, desc, type) = url_data
        url = models.Url(private=private,
                     path=path,
                     desc=desc,
                     order=order,
                     url_type=models.get_type(models.UrlType, type))
        if field == "person":
            url.person = obj
        elif field == "repository":
            url.repository = obj
        elif field == "place":
            url.place = obj
        else:
            raise AttributeError("invalid field '%s' to attach to url" %
                                 field)
        url.save()
        #obj.url_list.add(url)
        #obj.save()
    
    def add_place_ref(self, event, place_handle):
        if place_handle:
            try:
                place = models.Place.objects.get(handle=place_handle)
            except:
                print >> sys.stderr, ("ERROR: Place does not exist: '%s'" % 
                                      place_handle)
                return
            event.place = place
            event.save()
    
    def add_parent_family(self, person, parent_family_handle):
        try:
            family = models.Family.objects.get(handle=parent_family_handle)
        except:
            print >> sys.stderr, ("ERROR: Family does not exist: '%s'" % 
                                  parent_family_handle)
            return
        person.parent_families.add(family)
        person.save()
    
    def add_date(self, obj, date):
        if date is None: 
            (calendar, modifier, quality, text, sortval, newyear) = \
                (0, 0, 0, "", 0, 0)
            day1, month1, year1, slash1 = 0, 0, 0, 0
            day2, month2, year2, slash2 = 0, 0, 0, 0
        else:
            (calendar, modifier, quality, dateval, text, sortval, newyear) = date
            if len(dateval) == 4:
                day1, month1, year1, slash1 = dateval
                day2, month2, year2, slash2 = 0, 0, 0, 0
            elif len(dateval) == 8:
                day1, month1, year1, slash1, day2, month2, year2, slash2 = dateval
            else:
                raise AttributeError("ERROR: dateval format '%s'" % dateval)
        obj.calendar = calendar
        obj.modifier = modifier
        obj.quality = quality
        obj.text = text
        obj.sortval = sortval
        obj.newyear = newyear
        obj.day1 = day1
        obj.month1 = month1
        obj.year1 = year1
        obj.slash1 = slash1
        obj.day2 = day2
        obj.month2 = month2
        obj.year2 = year2
        obj.slash2 = slash2
    
    def add_name(self, person, data, preferred):
        if data:
            (private, citation_list, note_list, date,
             first_name, surname_list, suffix, title,
             name_type, group_as, sort_as, 
             display_as, call, nick, famnick) = data
    
            count = person.name_set.count()
            name = models.Name()
            name.order = count + 1
            name.preferred = preferred
            name.private = private
            name.first_name = first_name
            name.suffix = suffix
            name.title = title
            name.name_type = models.get_type(models.NameType, name_type)
            name.group_as = group_as
            name.sort_as = models.get_type(models.NameFormatType, sort_as)
            name.display_as = models.get_type(models.NameFormatType, display_as)
            name.call = call
            name.nick = nick
            name.famnick = famnick
            # we know person exists
            # needs to have an ID for key
            name.person = person
            self.add_date(name, date) 
            name.save()
            self.add_surname_list(name, surname_list)
            self.add_note_list(name, note_list)
            self.add_citation_list(name, citation_list)
            #person.save()
           
    ## Export primary objects:
    
    def add_person(self, data):
        # Unpack from the BSDDB:
        (handle,        #  0
         gid,          #  1
         gender,             #  2
         primary_name,       #  3
         alternate_names,    #  4
         death_ref_index,    #  5
         birth_ref_index,    #  6
         event_ref_list,     #  7
         family_list,        #  8
         parent_family_list, #  9
         media_list,         # 10
         address_list,       # 11
         attribute_list,     # 12
         url_list,               # 13
         lds_ord_list,       # 14
         pcitation_list,       # 15
         pnote_list,         # 16
         change,             # 17
         tag_list,             # 18
         private,           # 19
         person_ref_list,    # 20
         ) = data
    
        person = models.Person(handle=handle,
                            gramps_id=gid,
                            last_changed=todate(change),
                            private=private,
                            gender_type=models.get_type(models.GenderType, gender))
        #person.cache = base64.encodestring(cPickle.dumps(data))
        person.save()

    def add_person_detail(self, data):
        # Unpack from the BSDDB:
        (handle,        #  0
         gid,          #  1
         gender,             #  2
         primary_name,       #  3
         alternate_names,    #  4
         death_ref_index,    #  5
         birth_ref_index,    #  6
         event_ref_list,     #  7
         family_list,        #  8
         parent_family_list, #  9
         media_list,         # 10
         address_list,       # 11
         attribute_list,     # 12
         url_list,               # 13
         lds_ord_list,       # 14
         pcitation_list,       # 15
         pnote_list,         # 16
         change,             # 17
         tag_list,             # 18
         private,           # 19
         person_ref_list,    # 20
         ) = data
    
        try:
            person = models.Person.objects.get(handle=handle)
        except:
            print >> sys.stderr, ("ERROR: Person does not exist: '%s'" % 
                                  handle)
            return
        if primary_name:
            self.add_name(person, primary_name, True)
        self.add_alternate_name_list(person, alternate_names)
        self.add_event_ref_list(person, event_ref_list)
        self.add_family_ref_list(person, family_list) 
        self.add_parent_family_list(person, parent_family_list)
        self.add_media_ref_list(person, media_list)
        self.add_note_list(person, pnote_list)
        self.add_attribute_list(person, attribute_list)
        self.add_url_list("person", person, url_list) 
        self.add_person_ref_list(person, person_ref_list)
        self.add_citation_list(person, pcitation_list)
        self.add_address_list("person", person, address_list)
        self.add_lds_list("person", person, lds_ord_list)
        # set person.birth and birth.death to correct events:

        obj_type = ContentType.objects.get_for_model(person)
        events = models.EventRef.objects.filter(
            object_id=person.id, 
            object_type=obj_type, 
            ref_object__event_type__val=models.EventType.BIRTH)

        all_events = self.get_event_ref_list(person)
        if events:
            person.birth = events[0].ref_object
            person.birth_ref_index = lookup_role_index(models.EventType.BIRTH, all_events)

        events = models.EventRef.objects.filter(
            object_id=person.id, 
            object_type=obj_type, 
            ref_object__event_type__val=models.EventType.DEATH)
        if events:
            person.death = events[0].ref_object
            person.death_ref_index = lookup_role_index(models.EventType.DEATH, all_events)
        person.save()
        return person

    def add_note_detail(self, data):
        """
        Dummy method for consistency with other two-pass adds.
        """
        pass
    
    def add_note(self, data):
        # Unpack from the BSDDB:
        (handle, gid, styled_text, format, note_type,
         change, tag_list, private) = data
        text, markup_list = styled_text
        n = models.Note(handle=handle,
                        gramps_id=gid,
                        last_changed=todate(change),
                        private=private,
                        preformatted=format,
                        text=text,
                        note_type=models.get_type(models.NoteType, note_type))
        #n.cache = base64.encodestring(cPickle.dumps(data))
        n.save()
        count = 1
        for markup in markup_list:
            markup_code, value, start_stop_list = markup
            m = models.Markup(note=n, order=count, 
                   markup_type=models.get_type(models.MarkupType,
                                               markup_code, 
                                               get_or_create=True),
                              string=value,
                              start_stop_list=str(start_stop_list))
            m.save()
    
    def add_family(self, data):
        # Unpack from the BSDDB:
        (handle, gid, father_handle, mother_handle,
         child_ref_list, the_type, event_ref_list, media_list,
         attribute_list, lds_seal_list, citation_list, note_list,
         change, tag_list, private) = data
    
        family = models.Family(handle=handle, gramps_id=gid, 
                               family_rel_type = models.get_type(models.FamilyRelType, the_type),
                               last_changed=todate(change), 
                               private=private)
        #family.cache = base64.encodestring(cPickle.dumps(data))
        family.save()

    def add_family_detail(self, data):
        # Unpack from the BSDDB:
        (handle, gid, father_handle, mother_handle,
         child_ref_list, the_type, event_ref_list, media_list,
         attribute_list, lds_seal_list, citation_list, note_list,
         change, tag_list, private) = data
    
        try:
            family = models.Family.objects.get(handle=handle)
        except:
            print >> sys.stderr, ("ERROR: Family does not exist: '%s'" % 
                                  handle)
            return
        # father_handle and/or mother_handle can be None
        if father_handle:
            try:
                family.father = models.Person.objects.get(handle=father_handle)
            except:
                print >> sys.stderr, ("ERROR: Father does not exist: '%s'" % 
                                      father_handle)
                family.father = None
        if mother_handle:
            try:
                family.mother = models.Person.objects.get(handle=mother_handle)
            except:
                print >> sys.stderr, ("ERROR: Mother does not exist: '%s'" % 
                                      mother_handle)
                family.mother = None
        family.save()
        self.add_child_ref_list(family, child_ref_list)
        self.add_note_list(family, note_list)
        self.add_attribute_list(family, attribute_list)
        self.add_citation_list(family, citation_list)
        self.add_media_ref_list(family, media_list)
        self.add_event_ref_list(family, event_ref_list)
        self.add_lds_list("family", family, lds_seal_list)
        
    def add_source(self, data):
        (handle, gid, title,
         author, pubinfo,
         note_list,
         media_list,
         abbrev,
         change, datamap,
         reporef_list,
         private) = data
        source = models.Source(handle=handle, gramps_id=gid, title=title,
                               author=author, pubinfo=pubinfo, abbrev=abbrev,
                               last_changed=todate(change), private=private)
        #source.cache = base64.encodestring(cPickle.dumps(data))
        source.save()

    def add_source_detail(self, data):
        (handle, gid, title,
         author, pubinfo,
         note_list,
         media_list,
         abbrev,
         change, datamap,
         reporef_list,
         private) = data
        try:
            source = models.Source.objects.get(handle=handle)
        except:
            print >> sys.stderr, ("ERROR: Source does not exist: '%s'" % 
                                  handle)
            return
        self.add_note_list(source, note_list) 
        self.add_media_ref_list(source, media_list)
        self.add_source_datamap_dict(source, datamap)
        self.add_repository_ref_list(source, reporef_list)
    
    def add_repository(self, data):
        (handle, gid, the_type, name, note_list,
         address_list, url_list, change, private) = data
    
        repository = models.Repository(handle=handle,
                                       gramps_id=gid,
                                       last_changed=todate(change), 
                                       private=private,
                                       repository_type=models.get_type(models.RepositoryType, the_type),
                                       name=name)
        #repository.cache = base64.encodestring(cPickle.dumps(data))
        repository.save()

    def add_repository_detail(self, data):
        (handle, gid, the_type, name, note_list,
         address_list, url_list, change, private) = data
        try:
            repository = models.Repository.objects.get(handle=handle)
        except:
            print >> sys.stderr, ("ERROR: Repository does not exist: '%s'" % 
                                  handle)
            return
        self.add_note_list(repository, note_list)
        self.add_url_list("repository", repository, url_list)
        self.add_address_list("repository", repository, address_list)
    
    def add_location(self, field, obj, location_data, order):
        # location now has 8 items
        # street, locality, city, county, state,
        # country, postal, phone, parish

        if location_data == None: return
        if len(location_data) == 8:
            (street, locality, city, county, state, country, postal, phone) = location_data
            parish = None
        elif len(location_data) == 2:
            ((street, locality, city, county, state, country, postal, phone), parish) = location_data
        else:
            print >> sys.stderr, ("ERROR: unknown location: '%s'" % 
                                  location_data)
            (street, locality, city, county, state, country, postal, phone, parish) = \
                ("", "", "", "", "", "", "", "", "")
        location = models.Location(street = street,
                                   locality = locality,
                               city = city,
                               county = county,
                               state = state,
                               country = country,
                               postal = postal,
                               phone = phone,
                               parish = parish,
                               order = order)
        if field == "address":
            location.address = obj
        elif field == "place":
            location.place = obj
        else:
            raise AttributeError("invalid field '%s' to attach to location" %
                                 field)
        location.save()
        #obj.locations.add(location)
        #obj.save()
    
    def add_place(self, data):
        (handle, gid, title, long, lat,
         main_loc, alt_location_list,
         url_list,
         media_list,
         citation_list,
         note_list,
         change, private) = data
        place = models.Place(handle=handle, gramps_id=gid, title=title,
                             long=long, lat=lat, last_changed=todate(change),
                             private=private)
        #place.cache = base64.encodestring(cPickle.dumps(data))
        place.save()

    def add_place_detail(self, data):
        (handle, gid, title, long, lat,
         main_loc, alt_location_list,
         url_list,
         media_list,
         citation_list,
         note_list,
         change, private) = data
        try:
            place = models.Place.objects.get(handle=handle)
        except:
            print >> sys.stderr, ("ERROR: Place does not exist: '%s'" % 
                                  handle)
            return
        self.add_url_list("place", place, url_list)
        self.add_media_ref_list(place, media_list)
        self.add_citation_list(place, citation_list)
        self.add_note_list(place, note_list) 
        self.add_location("place", place, main_loc, 1)
        count = 2
        for loc_data in alt_location_list:
            self.add_location("place", place, loc_data, count)
            count + 1
    
    def add_media(self, data):
        (handle, gid, path, mime, desc,
         attribute_list,
         citation_list,
         note_list,
         change,
         date,
         tag_list,
         private) = data
        media = models.Media(handle=handle, gramps_id=gid,
                             path=path, mime=mime, 
                             desc=desc, last_changed=todate(change),
                             private=private)
        #media.cache = base64.encodestring(cPickle.dumps(data))
        self.add_date(media, date)
        media.save()
    
    def add_media_detail(self, data):
        (handle, gid, path, mime, desc,
         attribute_list,
         citation_list,
         note_list,
         change,
         date,
         tag_list,
         private) = data
        try:
            media = models.Media.objects.get(handle=handle)
        except:
            print >> sys.stderr, ("ERROR: Media does not exist: '%s'" % 
                                  handle)
            return
        self.add_note_list(media, note_list) 
        self.add_citation_list(media, citation_list)
        self.add_attribute_list(media, attribute_list)
    
    def add_event(self, data):
        (handle, gid, the_type, date, description, place_handle, 
         citation_list, note_list, media_list, attribute_list,
         change, private) = data
        event = models.Event(handle=handle,
                             gramps_id=gid, 
                             event_type=models.get_type(models.EventType, the_type),
                             private=private,
                             description=description,
                             last_changed=todate(change))
        #event.cache = base64.encodestring(cPickle.dumps(data))
        self.add_date(event, date)
        event.save()

    def add_event_detail(self, data):
        (handle, gid, the_type, date, description, place_handle, 
         citation_list, note_list, media_list, attribute_list,
         change, private) = data
        try:
            event = models.Event.objects.get(handle=handle)
        except:
            print >> sys.stderr, ("ERROR: Event does not exist: '%s'" % 
                                  handle)
            return
        self.add_place_ref(event, place_handle)
        self.add_note_list(event, note_list)
        self.add_attribute_list(event, attribute_list)
        self.add_media_ref_list(event, media_list)
        self.add_citation_list(event, citation_list)

    def get_raw(self, item):
        """
        Build and return the raw, serialized data of an object.
        """
        if isinstance(item, models.Person):
            raw = self.get_person(item)
        elif isinstance(item, models.Family):
            raw = self.get_family(item)
        elif isinstance(item, models.Place):
            raw = self.get_place(item)
        elif isinstance(item, models.Media):
            raw = self.get_media(item)
        elif isinstance(item, models.Source):
            raw = self.get_source(item)
        elif isinstance(item, models.Citation):
            raw = self.get_citation(item)
        elif isinstance(item, models.Repository):
            raw = self.get_repository(item)
        elif isinstance(item, models.Note):
            raw = self.get_note(item)
        elif isinstance(item, models.Event):
            raw = self.get_event(item)
        else:
            raise Exception("Don't know how to get raw '%s'" % type(item))
        return raw

    def reset_cache(self, item):
        """
        Resets the cache version of an object, but doesn't save it to the database.
        """
        raw = self.get_raw(item)
        item.cache = base64.encodestring(cPickle.dumps(raw))
    
    def rebuild_cache(self, item):
        """
        Resets the cache version of an object, and saves it to the database.
        """
        raw = self.get_raw(item)
        item.cache = base64.encodestring(cPickle.dumps(raw))
        item.save()
    
    def rebuild_caches(self, callback=None):
        """
        Call this to rebuild the caches for all primary models.
        """
        if not callable(callback): 
            callback = lambda (percent): None # dummy

        callback(0)
        count = 0.0
        total = (self.Note.all().count() + 
                 self.Person.all().count() +
                 self.Event.all().count() + 
                 self.Family.all().count() +
                 self.Repository.all().count() +
                 self.Place.all().count() +
                 self.Media.all().count() +
                 self.Source.all().count())

        for item in self.Person.all():
            raw = self.get_person(item)
            item.cache = base64.encodestring(cPickle.dumps(raw))
            item.save()
            callback(100 * count/total)
            count += 1

        for item in self.Family.all():
            raw = self.get_family(item)
            item.cache = base64.encodestring(cPickle.dumps(raw))
            item.save()
            callback(100 * count/total)
            count += 1

        for item in self.Source.all():
            raw = self.get_source(item)
            item.cache = base64.encodestring(cPickle.dumps(raw))
            item.save()
            callback(100 * count/total)
            count += 1

        for item in self.Event.all():
            raw = self.get_event(item)
            item.cache = base64.encodestring(cPickle.dumps(raw))
            item.save()
            callback(100 * count/total)
            count += 1

        for item in self.Repository.all():
            raw = self.get_repository(item)
            item.cache = base64.encodestring(cPickle.dumps(raw))
            item.save()
            callback(100 * count/total)
            count += 1

        for item in self.Place.all():
            raw = self.get_place(item)
            item.cache = base64.encodestring(cPickle.dumps(raw))
            item.save()
            callback(100 * count/total)
            count += 1

        for item in self.Media.all():
            raw = self.get_media(item)
            item.cache = base64.encodestring(cPickle.dumps(raw))
            item.save()
            callback(100 * count/total)
            count += 1

        for item in self.Note.all():
            raw = self.get_note(item)
            item.cache = base64.encodestring(cPickle.dumps(raw))
            item.save()
            callback(100 * count/total)
            count += 1

        callback(100)

