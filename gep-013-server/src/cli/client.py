#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009 Doug Blank <doug.blank@gmail.com>
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

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import pickle
import socket
import sys
from xml.dom import minidom

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib import *

#-------------------------------------------------------------------------
#
# Functions
#
#-------------------------------------------------------------------------
def xml_unpickle(xml):
    """
    Takes an XML string and returns Python objects.
    """
    xmldoc = minidom.parseString(xml)
    if xmldoc.childNodes.length == 1:
        return xml_unpickle_doc(xmldoc.childNodes[0])
    else:
        return None

def xml_unpickle_doc(xmldoc):
    """
    Takes a minidom XML object and returns Python objects.
    """
    if xmldoc.nodeName == 'list':
        return [xml_unpickle_doc(item) for item in xmldoc.childNodes]
    elif xmldoc.nodeName == 'tuple':
        return tuple([xml_unpickle_doc(item) for item in xmldoc.childNodes])
    elif xmldoc.nodeName == 'dict':
        retval = {}
        for pair in xmldoc.childNodes:
            key = xml_unpickle_doc(pair.childNodes[0].childNodes[0])
            value = xml_unpickle_doc(pair.childNodes[1].childNodes[0])
            retval[key] = value
        return retval
    elif xmldoc.nodeName == 'object':
        objType = xmldoc.getAttributeNode("type").value
        data = xml_unpickle_doc(xmldoc.childNodes[0])
        if objType == 'Person':
            return Person(data)
        elif objType == 'Family':
            return Family(data)
        elif objType == 'Event':
            return Event(data)
        elif objType == 'Source':
            return Source(data)
        elif objType == 'Place':
            return Place(data)
        elif objType == 'Date':
            return Date(data)
        elif objType == 'MediaObject':
            return MediaObject(data)
        elif objType == 'Repository':
            return Repository(data)
        elif objType == 'Note':
            return Note(data)
        elif objType == 'Exception':
            return Exception(data)
        else:
            return Exception("unknown xml object type: '%s'" % objType)
    else:
        # int, str, unicode, float, long, bool, NoneType
        typeName = xmldoc.nodeName
        if xmldoc.childNodes.length > 0:
            nodeValue = xmldoc.childNodes[0].nodeValue
        else:
            nodeValue = ''
        if typeName == "NoneType":
            return None
        elif typeName in ['int', 'str', 'unicode', 'float', 'long', 'bool']:
            if typeName in ['str', 'unicode']:
                nodeValue = nodeValue.replace("&amp;", "&")
                nodeValue = nodeValue.replace("&lt;", "<")
            if typeName != "bool":
                nodeValue = '"""%s"""' % nodeValue
            try:
                return eval('''%s(%s)''' % (typeName, nodeValue))
            except Exception, e:
                print "    Evaluation error in conversion:", e
                return Exception(str(e))
        else:
            return Exception("unknown xml type: '%s'" % typeName)

#-------------------------------------------------------------------------
#
# Classes
#
#-------------------------------------------------------------------------
class RemoteObject:
    """
    A wrapper to access underlying attributes by asking over a 
    socket. A server will pickle the result, and return.
    """
    def __init__(self, host, port, prefix = "self."):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.socket.settimeout(10) # second timeout
        self.prefix = prefix
    
    def __repr__(self):
        return self.remote("repr(self)")
    
    def person(self, handle):
        data = self.remote("self.dbstate.db.get_raw_person_data(%s)" % repr(handle))
        return Person(data)

    def family(self, handle):
        data = self.remote("self.dbstate.db.get_raw_family_data(%s)" % repr(handle))
        return Family(data)

    def object(self, handle):
        data = self.remote("self.dbstate.db.get_raw_object_data(%s)" % repr(handle))
        return MediaObject(data)

    def place(self, handle):
        data = self.remote("self.dbstate.db.get_raw_place_data(%s)" % repr(handle))
        return Place(data)

    def event(self, handle):
        data = self.remote("self.dbstate.db.get_raw_event_data(%s)" % repr(handle))
        return Event(data)

    def source(self, handle):
        data = self.remote("self.dbstate.db.get_raw_source_data(%s)" % repr(handle))
        return Source(data)

    def repository(self, handle):
        data = self.remote("self.dbstate.db.get_raw_repository_data(%s)" % repr(handle))
        return Repository(data)

    def note(self, handle):
        data = self.remote("self.dbstate.db.get_raw_note_data(%s)" % repr(handle))
        return Note(data)

    def remote(self, command):
        """
        Use this interface to directly talk to server.
        """
        retval = None
        self.socket.send(command)
        data = self.socket.recv(1024)
        if data != "":
            while True:
                try:
                    retval = xml_unpickle(data)
                    break
                except:
                    data += self.socket.recv(1024)
        if type(retval) == Exception:
            raise retval
        return retval

    def _eval(self, item, *args, **kwargs):
        """
        The interface for calling prefix.item.item...(args, kwargs)
        """
        commandArgs = ""
        for a in args:
            if commandArgs != "":
                commandArgs += ", "
            commandArgs += repr(a)
        for a in kwargs.keys():
            if commandArgs != "":
                commandArgs += ", "
            commandArgs += a + "=" + repr(kwargs[a])
        self.socket.send(self.prefix + item + "(" + commandArgs + ")")
        retval = None
        data = self.socket.recv(1024)
        if data != "":
            while True:
                try:
                    retval =  xml_unpickle(data)
                    break
                except:
                    data += self.socket.recv(1024)
        if type(retval) == Exception:
            raise retval
        return retval

    def representation(self, item):
        return self.remote("repr(%s)" % (self.prefix + item))

    def __getattr__(self, item):
        return TempRemoteObject(self, item)

    def dir(self, item = ''):
        return self.remote("dir(%s)" % ((self.prefix + item)[:-1]))

class TempRemoteObject:
    """
    Temporary field/method access object.
    """
    def __init__(self, parent, item):
        self.parent = parent
        self.item = item
    def __call__(self, *args, **kwargs):
        return self.parent._eval(self.item, *args, **kwargs)
    def _eval(self, prefix, *args, **kwargs):
        return self.parent._eval(self.item + "." + prefix, *args, **kwargs)
    def __repr__(self):
        return self.parent.representation(self.item)
    def representation(self, item):
        return self.parent.representation(self.item + "." + item)
    def __getattr__(self, item):
        return TempRemoteObject(self, item)
    def dir(self, item = ''):
        return self.parent.dir(self.item + "." + item)

if __name__ == "__main__":
    host = sys.argv[1]
    port = int(sys.argv[2])
    self = RemoteObject(host, port)
    print "GRAMPS Remote interface; use 'self' to access GRAMPS"
