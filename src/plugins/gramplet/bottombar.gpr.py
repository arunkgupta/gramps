#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011 Nick Hall
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

#------------------------------------------------------------------------
#
# Register Gramplet
#
#------------------------------------------------------------------------
register(GRAMPLET, 
         id="Person Details Gramplet", 
         name=_("Person Details Gramplet"), 
         description = _("Gramplet showing details of a person"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="PersonDetails.py",
         height=200,
         gramplet = 'PersonDetails',
         gramplet_title=_("Details"),
         )

register(GRAMPLET, 
         id="Person Residence Gramplet", 
         name=_("Person Residence Gramplet"), 
         description = _("Gramplet showing residence events for a person"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="PersonResidence.py",
         height=200,
         gramplet = 'PersonResidence',
         gramplet_title=_("Residence"),
         )

register(GRAMPLET, 
         id="Person Gallery Gramplet", 
         name=_("Person Gallery Gramplet"), 
         description = _("Gramplet showing media objects for a person"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Gallery.py",
         height=200,
         gramplet = 'PersonGallery',
         gramplet_title=_("Gallery"),
         )

register(GRAMPLET, 
         id="Event Gallery Gramplet", 
         name=_("Event Gallery Gramplet"), 
         description = _("Gramplet showing media objects for an event"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Gallery.py",
         height=200,
         gramplet = 'EventGallery',
         gramplet_title=_("Gallery"),
         )

register(GRAMPLET, 
         id="Place Gallery Gramplet", 
         name=_("Place Gallery Gramplet"), 
         description = _("Gramplet showing media objects for a place"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Gallery.py",
         height=200,
         gramplet = 'PlaceGallery',
         gramplet_title=_("Gallery"),
         )

register(GRAMPLET, 
         id="Source Gallery Gramplet", 
         name=_("Source Gallery Gramplet"), 
         description = _("Gramplet showing media objects for a source"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Gallery.py",
         height=200,
         gramplet = 'SourceGallery',
         gramplet_title=_("Gallery"),
         )

register(GRAMPLET, 
         id="Person Attributes Gramplet", 
         name=_("Person Attributes Gramplet"), 
         description = _("Gramplet showing the attributes of a person"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Attributes.py",
         height=200,
         gramplet = 'PersonAttributes',
         gramplet_title=_("Attributes"),
         )

register(GRAMPLET, 
         id="Event Attributes Gramplet", 
         name=_("Event Attributes Gramplet"), 
         description = _("Gramplet showing the attributes of an event"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Attributes.py",
         height=200,
         gramplet = 'EventAttributes',
         gramplet_title=_("Attributes"),
         )

register(GRAMPLET, 
         id="Family Attributes Gramplet", 
         name=_("Family Attributes Gramplet"), 
         description = _("Gramplet showing the attributes of a family"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Attributes.py",
         height=200,
         gramplet = 'FamilyAttributes',
         gramplet_title=_("Attributes"),
         )

register(GRAMPLET, 
         id="Media Attributes Gramplet", 
         name=_("Media Attributes Gramplet"), 
         description = _("Gramplet showing the attributes of a media object"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Attributes.py",
         height=200,
         gramplet = 'MediaAttributes',
         gramplet_title=_("Attributes"),
         )

register(GRAMPLET, 
         id="Person Notes Gramplet", 
         name=_("Person Notes Gramplet"), 
         description = _("Gramplet showing the notes for a person"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Notes.py",
         height=200,
         gramplet = 'PersonNotes',
         gramplet_title=_("Notes"),
         )

register(GRAMPLET, 
         id="Event Notes Gramplet", 
         name=_("Event Notes Gramplet"), 
         description = _("Gramplet showing the notes for an event"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Notes.py",
         height=200,
         gramplet = 'EventNotes',
         gramplet_title=_("Notes"),
         )

register(GRAMPLET, 
         id="Family Notes Gramplet", 
         name=_("Family Notes Gramplet"), 
         description = _("Gramplet showing the notes for a family"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Notes.py",
         height=200,
         gramplet = 'FamilyNotes',
         gramplet_title=_("Notes"),
         )

register(GRAMPLET, 
         id="Place Notes Gramplet", 
         name=_("Place Notes Gramplet"), 
         description = _("Gramplet showing the notes for a place"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Notes.py",
         height=200,
         gramplet = 'PlaceNotes',
         gramplet_title=_("Notes"),
         )

register(GRAMPLET, 
         id="Source Notes Gramplet", 
         name=_("Source Notes Gramplet"), 
         description = _("Gramplet showing the notes for a source"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Notes.py",
         height=200,
         gramplet = 'SourceNotes',
         gramplet_title=_("Notes"),
         )

register(GRAMPLET, 
         id="Repository Notes Gramplet", 
         name=_("Repository Notes Gramplet"), 
         description = _("Gramplet showing the notes for a repository"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Notes.py",
         height=200,
         gramplet = 'RepositoryNotes',
         gramplet_title=_("Notes"),
         )

register(GRAMPLET, 
         id="Media Notes Gramplet", 
         name=_("Media Notes Gramplet"), 
         description = _("Gramplet showing the notes for a media object"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Notes.py",
         height=200,
         gramplet = 'MediaNotes',
         gramplet_title=_("Notes"),
         )

register(GRAMPLET, 
         id="Person Sources Gramplet", 
         name=_("Person Sources Gramplet"), 
         description = _("Gramplet showing the sources for a person"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Sources.py",
         height=200,
         gramplet = 'PersonSources',
         gramplet_title=_("Sources"),
         )

register(GRAMPLET, 
         id="Event Sources Gramplet", 
         name=_("Event Sources Gramplet"), 
         description = _("Gramplet showing the sources for an event"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Sources.py",
         height=200,
         gramplet = 'EventSources',
         gramplet_title=_("Sources"),
         )

register(GRAMPLET, 
         id="Family Sources Gramplet", 
         name=_("Family Sources Gramplet"), 
         description = _("Gramplet showing the sources for a family"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Sources.py",
         height=200,
         gramplet = 'FamilySources',
         gramplet_title=_("Sources"),
         )

register(GRAMPLET, 
         id="Place Sources Gramplet", 
         name=_("Place Sources Gramplet"), 
         description = _("Gramplet showing the sources for a place"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Sources.py",
         height=200,
         gramplet = 'PlaceSources',
         gramplet_title=_("Sources"),
         )

register(GRAMPLET, 
         id="Media Sources Gramplet", 
         name=_("Media Sources Gramplet"), 
         description = _("Gramplet showing the sources for a media object"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Sources.py",
         height=200,
         gramplet = 'MediaSources',
         gramplet_title=_("Sources"),
         )

register(GRAMPLET, 
         id="Person Filter Gramplet", 
         name=_("Person Filter Gramplet"), 
         description = _("Gramplet providing a person filter"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Filter.py",
         height=200,
         gramplet = 'PersonFilter',
         gramplet_title=_("Filter"),
         )

register(GRAMPLET, 
         id="Family Filter Gramplet", 
         name=_("Family Filter Gramplet"), 
         description = _("Gramplet providing a family filter"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Filter.py",
         height=200,
         gramplet = 'FamilyFilter',
         gramplet_title=_("Filter"),
         )

register(GRAMPLET, 
         id="Event Filter Gramplet", 
         name=_("Event Filter Gramplet"), 
         description = _("Gramplet providing an event filter"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Filter.py",
         height=200,
         gramplet = 'EventFilter',
         gramplet_title=_("Filter"),
         )

register(GRAMPLET, 
         id="Source Filter Gramplet", 
         name=_("Source Filter Gramplet"), 
         description = _("Gramplet providing a source filter"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Filter.py",
         height=200,
         gramplet = 'SourceFilter',
         gramplet_title=_("Filter"),
         )

register(GRAMPLET, 
         id="Place Filter Gramplet", 
         name=_("Place Filter Gramplet"), 
         description = _("Gramplet providing a place filter"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Filter.py",
         height=200,
         gramplet = 'PlaceFilter',
         gramplet_title=_("Filter"),
         )

register(GRAMPLET, 
         id="Media Filter Gramplet", 
         name=_("Media Filter Gramplet"), 
         description = _("Gramplet providing a media filter"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Filter.py",
         height=200,
         gramplet = 'MediaFilter',
         gramplet_title=_("Filter"),
         )

register(GRAMPLET, 
         id="Repository Filter Gramplet", 
         name=_("Repository Filter Gramplet"), 
         description = _("Gramplet providing a repository filter"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Filter.py",
         height=200,
         gramplet = 'RepositoryFilter',
         gramplet_title=_("Filter"),
         )

register(GRAMPLET, 
         id="Note Filter Gramplet", 
         name=_("Note Filter Gramplet"), 
         description = _("Gramplet providing a note filter"),
         version="1.0.0",
         gramps_target_version="3.3",
         status = STABLE,
         fname="Filter.py",
         height=200,
         gramplet = 'NoteFilter',
         gramplet_title=_("Filter"),
         )
