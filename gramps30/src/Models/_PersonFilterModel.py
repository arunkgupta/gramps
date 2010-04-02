
from _FastFilterModel import FastFilterModel
import gen.lib


class PersonFilterModel(FastFilterModel):
    """Provide a fast model interface to the Person table.
    """
        
    def __init__(self,db,apply_filter):
        FastFilterModel.__init__(self,db,apply_filter)


    def _get_object_class(self,db):
        return gen.lib.Person

    
    def _get_fetch_func(self,db):
        return db.get_person_from_handle
