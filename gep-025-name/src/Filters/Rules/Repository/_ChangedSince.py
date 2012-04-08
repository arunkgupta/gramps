#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _

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
    """Rule that checks for repositories changed since a specific time."""

    name        = _('Repositories changed after <date time>')
    description = _("Matches repository records changed after a specified "
                    "date/time (yyyy-mm-dd hh:mm:ss) or in the range, if a second "
                    "date/time is given.")