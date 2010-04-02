#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from Filters.Rules._ChangedSinceBase import ChangedSinceBase

#-------------------------------------------------------------------------
#
# ChangedSince
#
#-------------------------------------------------------------------------
class ChangedSince(ChangedSinceBase):
    """Rules that checks for places changed since a specific time."""

    name    = _('Places changed after <date time>')
    description = _("Matches place records changed after a specified "
                    "date-time (yyyy-mm-dd hh:mm:ss) or in the range, if a second "
                    "date-time is given")
