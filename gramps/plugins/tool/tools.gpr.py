#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009 Benny Malengier
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
GRAMPS registration file
"""

#------------------------------------------------------------------------
#
# Fix Capitalization of Family Names
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'chname',
name  = _("Fix Capitalization of Family Names"),
description =  _("Searches the entire database and attempts to "
                    "fix capitalization of the names."),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'changenames.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DBPROC,
toolclass = 'ChangeNames',
optionclass = 'ChangeNamesOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Rename Event Types
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'chtype',
name  = _("Rename Event Types"),
description =  _("Allows all the events of a certain name "
                    "to be renamed to a new name."),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'changetypes.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DBPROC,
toolclass = 'ChangeTypes',
optionclass = 'ChangeTypesOptions',
tool_modes = [TOOL_MODE_GUI, TOOL_MODE_CLI]
  )

#------------------------------------------------------------------------
#
# Check and Repair Database
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'check',
name  = _("Check and Repair Database"),
description =  _("Checks the database for integrity problems, fixing the "
                   "problems that it can"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'check.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DBFIX,
toolclass = 'Check',
optionclass = 'CheckOptions',
tool_modes = [TOOL_MODE_GUI, TOOL_MODE_CLI]
  )

#------------------------------------------------------------------------
#
# Interactive Descendant Browser
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'dbrowse',
name  = _("Interactive Descendant Browser"),
description =  _("Provides a browsable hierarchy based on the active person"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'desbrowser.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_ANAL,
toolclass = 'DesBrowse',
optionclass = 'DesBrowseOptions',
tool_modes = [TOOL_MODE_GUI]
  )


#------------------------------------------------------------------------
#
# Python Evaluation Window
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'eval',
name  = "Python Evaluation Window",
description =  "Provides a window that can evaluate python code",
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'eval.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DEBUG,
toolclass = 'Eval',
optionclass = 'EvalOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Compare Individual Events
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'eventcmp',
name  = _("Compare Individual Events"),
description =  _("Aids in the analysis of data by allowing the "
                    "development of custom filters that can be applied "
                    "to the database to find similar events"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'eventcmp.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_ANAL,
toolclass = 'EventComparison',
optionclass = 'EventComparisonOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Extract Event Descriptions from Event Data
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'evname',
name  = _("Extract Event Description"),
description =  _("Extracts event descriptions from the event data"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'eventnames.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DBPROC,
toolclass = 'EventNames',
optionclass = 'EventNamesOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Extract Place Data from a Place Title
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'excity',
name  = _("Extract Place Data from a Place Title"),
description =  _("Attempts to extract city and state/province "
                    "from a place title"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'extractcity.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DBPROC,
toolclass = 'ExtractCity',
optionclass = 'ExtractCityOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Find Possible Duplicate People
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'dupfind',
name  = _("Find Possible Duplicate People"),
description =  _("Searches the entire database, looking for "
                    "individual entries that may represent the same person."),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'finddupes.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DBPROC,
toolclass = 'Merge',
optionclass = 'MergeOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Show Uncollected Objects
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'leak',
name  = "Show Uncollected Objects",
description =  "Provide a window listing all uncollected objects",
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'leak.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DEBUG,
toolclass = 'Leak',
optionclass = 'LeakOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Media Manager
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'mediaman',
name  = _("Media Manager"),
description =  _("Manages batch operations on media files"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'mediamanager.py',
authors = ["Alex Roitman"],
authors_email = ["shura@gramps-project.org"],
category = TOOL_UTILS,
toolclass = 'MediaMan',
optionclass = 'MediaManOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Not Related
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'not_related',
name  = _("Not Related"),
description =  _("Find people who are not in any way related to the "
                    "selected person"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'notrelated.py',
authors = ["Stephane Charette"],
authors_email = ["stephanecharette@gmail.com"],
category = TOOL_UTILS,
toolclass = 'NotRelated',
optionclass = 'NotRelatedOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Edit Database Owner Information
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'editowner',
name  = _("Edit Database Owner Information"),
description =  _("Allow editing database owner information."),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'ownereditor.py',
authors = ["Zsolt Foldvari"],
authors_email = ["zfoldvar@users.sourceforge.net"],
category = TOOL_DBPROC,
toolclass = 'OwnerEditor',
optionclass = 'OwnerEditorOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Extract Information from Names
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'patchnames',
name  = _("Extract Information from Names"),
description =  _("Extract titles, prefixes and compound surnames from given name or family name."),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'patchnames.py',
authors = ["Donald N. Allingham", "Benny Malengier"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DBPROC,
toolclass = 'PatchNames',
optionclass = 'PatchNamesOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Rebuild Secondary Indices
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'rebuild',
name  = _("Rebuild Secondary Indexes"),
description =  _("Rebuilds secondary indexes"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'rebuild.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DBFIX,
toolclass = 'Rebuild',
optionclass = 'RebuildOptions',
tool_modes = [TOOL_MODE_GUI, TOOL_MODE_CLI]
  )

#------------------------------------------------------------------------
#
# Rebuild Reference Maps
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'rebuild_refmap',
name  = _("Rebuild Reference Maps"),
description =  _("Rebuilds reference maps"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'rebuildrefmap.py',
authors = ["Alex Roitman"],
authors_email = ["shura@gramps-project.org"],
category = TOOL_DBFIX,
toolclass = 'RebuildRefMap',
optionclass = 'RebuildRefMapOptions',
tool_modes = [TOOL_MODE_GUI, TOOL_MODE_CLI]
  )

#------------------------------------------------------------------------
#
# Rebuild Gender Statistics
#
#------------------------------------------------------------------------

register(TOOL,
id    = 'rebuild_genstats',
name  = _("Rebuild Gender Statistics"),
description =  _("Rebuilds gender statistics for name gender guessing..."),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'rebuildgenderstat.py',
authors = ["Benny Malengier"],
authors_email = ["benny.malengier@gramps-project.org"],
category = TOOL_DBFIX,
toolclass = 'RebuildGenderStat',
optionclass = 'RebuildGenderStatOptions',
tool_modes = [TOOL_MODE_GUI, TOOL_MODE_CLI]
  )

#------------------------------------------------------------------------
#
# Relationship Calculator
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'relcalc',
name  = _("Relationship Calculator"),
description =  _("Calculates the relationship between two people"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'relcalc.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_UTILS,
toolclass = 'RelCalc',
optionclass = 'RelCalcOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Remove Unused Objects
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'remove_unused',
name  = _("Remove Unused Objects"),
description =  _("Removes unused objects from the database"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'removeunused.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DBFIX,
toolclass = 'RemoveUnused',
optionclass = 'CheckOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Reorder GRAMPS IDs
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'reorder_ids',
name  = _("Reorder Gramps IDs"),
description =  _("Reorders the Gramps IDs "
                    "according to Gramps' default rules."),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'reorderids.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_DBPROC,
toolclass = 'ReorderIds',
optionclass = 'ReorderIdsOptions',
tool_modes = [TOOL_MODE_GUI, TOOL_MODE_CLI]
  )

#------------------------------------------------------------------------
#
# Sorts events
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'sortevents',
name  = _("Sorts events"),
description =  _("Sorts events"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'sortevents.py',
authors = ["Gary Burton"],
authors_email = ["gary.burton@zen.co.uk"],
category = TOOL_DBPROC,
toolclass = 'SortEvents',
optionclass = 'SortEventOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Generate SoundEx Codes
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'soundgen',
name  = _("Generate SoundEx Codes"),
description =  _("Generates SoundEx codes for names"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'soundgen.py',
authors = ["Donald N. Allingham"],
authors_email = ["don@gramps-project.org"],
category = TOOL_UTILS,
toolclass = 'SoundGen',
optionclass = 'SoundGenOptions',
tool_modes = [TOOL_MODE_GUI]
  )

#------------------------------------------------------------------------
#
# Verify the Data
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'verify',
name  = _("Verify the Data"),
description =  _("Verifies the data against user-defined tests"),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'verify.py',
authors = ["Alex Roitman"],
authors_email = ["shura@gramps-project.org"],
category = TOOL_UTILS,
toolclass = 'Verify',
optionclass = 'VerifyOptions',
tool_modes = [TOOL_MODE_GUI, TOOL_MODE_CLI]
  )

#------------------------------------------------------------------------
#
# Merge citations
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'mergecitations',
name  = _("Merge Citations"),
description =  _("Searches the entire database, looking for "
                    "citations that have the same Volume/Page, Date and Confidence."),
version = '1.0',
gramps_target_version = '4.0',
status = STABLE,
fname = 'mergecitations.py',
authors = ["Tim G L Lyons"],
authors_email = ["gramps-project.org"],
category = TOOL_DBPROC,
toolclass = 'MergeCitations',
optionclass = 'MergeCitationsOptions',
tool_modes = [TOOL_MODE_GUI]
  )

