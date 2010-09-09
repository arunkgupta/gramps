from django.db import models

### START GRAMPS TYPES  
def get_datamap(grampsclass):
    return [(x[0],x[2]) for x in grampsclass._DATAMAP]

def get_class(grampsclass, val):
    return [g[1] for g in grampsclass if g[0] == val][0]


class mGrampsType(models.Model):
    """
    The abstract base class for all types. 
    Types are enumerated integers. One integer corresponds with custom, then 
    custom_type holds the type name
    """
    _CUSTOM = 0
    _DEFAULT = 0

    _DATAMAP = []
    
    custom_name = models.CharField(max_length=40, blank=True)
    
    class Meta:
        abstract = True

    def __unicode__(self):
        if self.custom_name:
            return get_class(self._DATAMAP, self.val) + ":" + self.custom_name 
        else:
            return get_class(self._DATAMAP, self.val)

class MarkerType(mGrampsType):
    from gen.lib.markertype import MarkerType
    _DATAMAP = get_datamap(MarkerType)
    val = models.IntegerField('marker', choices=_DATAMAP, blank=False)

class NameType(mGrampsType):
    from gen.lib.nametype import NameType
    _DATAMAP = get_datamap(NameType)
    val = models.IntegerField('name type', choices=_DATAMAP, blank=False)

class AttributeType(mGrampsType):
    from gen.lib.attrtype import AttributeType
    _DATAMAP = get_datamap(AttributeType)
    val = models.IntegerField('attribute type', choices=_DATAMAP, blank=False)

class UrlType(mGrampsType):
    from gen.lib.urltype import UrlType
    _DATAMAP = get_datamap(UrlType)
    val = models.IntegerField('url type', choices=_DATAMAP, blank=False)

class ChildRefType(mGrampsType):
    from gen.lib.childreftype import ChildRefType
    _DATAMAP = get_datamap(ChildRefType)
    val = models.IntegerField('child reference type', choices=_DATAMAP, blank=False)

class RepositoryType(mGrampsType):
    from gen.lib.repotype import RepositoryType
    _DATAMAP = get_datamap(RepositoryType)
    val = models.IntegerField('repository type', choices=_DATAMAP, blank=False)

class EventType(mGrampsType):
    from gen.lib.eventtype import EventType
    _DATAMAP = get_datamap(EventType)
    val = models.IntegerField('event type', choices=_DATAMAP, blank=False)

class FamilyRelType(mGrampsType):
    from gen.lib.familyreltype import FamilyRelType
    _DATAMAP = get_datamap(FamilyRelType)
    val = models.IntegerField('family relation type', choices=_DATAMAP, blank=False)

class SourceMediaType(mGrampsType):
    from gen.lib.srcmediatype import SourceMediaType
    _DATAMAP = get_datamap(SourceMediaType)
    val = models.IntegerField('source medium type', choices=_DATAMAP, blank=False)

class EventRoleType(mGrampsType):
    from gen.lib.eventroletype import EventRoleType
    _DATAMAP = get_datamap(EventRoleType)
    val = models.IntegerField('event role type', choices=_DATAMAP, blank=False)

class NoteType(mGrampsType):
    from gen.lib.notetype import NoteType
    _DATAMAP = get_datamap(NoteType)
    val = models.IntegerField('note type', choices=_DATAMAP, blank=False)

### END GRAMPS TYPES 

class Handle(models.Model):
    """
    Table to use as referring table for secondary and primary objects
    It ensures uniqueness of handles, and allows to retrieve the correct
    object.
    
    When a save on a primary object happens, first a save of a handle must
    be done
    """
    OBJECTS = (('P', 'Person'),
               ('F', 'Family'),
               ('S', 'Source'),
               ('E', 'Event'),
               ('R', 'Repository'),
               ('P', 'Place'),
               ('M', 'Media'),
               ('N', 'Note'),
              )
    handle = models.CharField(max_length=40, primary_key=True, unique=True)
    object = models.CharField('object type', max_length=1, choices=OBJECTS, 
                blank=False)

    def __unicode__(self):
        return self.object + ":" + self.handle
    
class PrimaryObject(models.Model):
    """
    Common attribute of all primary objects with key on the handle
    """
    handle = models.ForeignKey(Handle, blank=False, unique=True)
    gramps_id =  models.CharField(max_length=10, unique=True)
    change = models.DateTimeField()
    private = models.BooleanField()
    marker = models.ForeignKey(MarkerType)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.gramps_id 

class Person(PrimaryObject):
    """
    The model for the person object
    """
    gendermap = [(2, 'Unknown'), (1, 'Male'), (0, 'Female')]
    gender = models.IntegerField(blank=False, choices=gendermap)

class SecondaryObject(models.Model):
    """
    We use interlinked objects, secondary object is the table for primary 
    objects to refer to when linking to non primary objects
    """

    OBJECTS = (('Att', 'Attribute'),
               ('Adr', 'Address'),
               ('LDS', 'LDS ordinance'),
               ('Url', 'URL'),
               ('Nam', 'Name'),
               ('Pas', 'Person Assocation'),
               ('SoR', 'Source Reference'),
               ('EvR', 'Event Reference'),
               ('ReR', 'Repository Reference'),
               ('MeR', 'Media Reference'),
               ('ChR', 'Child Reference'),
               ('Loc', 'Location'),
              )
    private = models.BooleanField()
    primary_object = models.ForeignKey(Handle, blank=False)

    class Meta:
        abstract = True

    def __unicode__(self):
        return "SecondaryObject->" + (["Public", "Private"][self.private])
