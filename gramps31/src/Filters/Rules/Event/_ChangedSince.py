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
    """Rule that checks for an event changed after a specific time."""

    name        = _('Events changed after <date time>')
    description = _("Matches event records changed after a specified "
                    "date/time (yyyy-mm-dd hh:mm:ss) or in the range, if a second "
                    "date/time is given")
