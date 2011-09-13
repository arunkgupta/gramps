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

#------------------------------------------------------------------------
#
# Comma _Separated Values Spreadsheet (CSV)
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'ex_csv'
plg.name  = _("Comma Separated Values Spreadsheet (CSV)")
plg.name_accell  = _("Comma _Separated Values Spreadsheet (CSV)")
plg.description =  _("CSV is a common spreadsheet format.")
plg.version = '1.0'
plg.gramps_target_version = '3.3'
plg.status = STABLE
plg.fname = 'ExportCsv.py'
plg.ptype = EXPORT
plg.export_function = 'exportData'
plg.export_options = 'CSVWriterOptionBox'
plg.export_options_title = ('CSV spreadsheet options')
plg.extension = "csv"

#------------------------------------------------------------------------
#
# Web Family Tree export
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'ex_webfamtree'
plg.name  = _('Web Family Tree')
plg.name_accell  = _('_Web Family Tree')
plg.description =  _("Web Family Tree format")
plg.version = '1.0'
plg.gramps_target_version = '3.3'
plg.status = STABLE
plg.fname = 'ExportFtree.py'
plg.ptype = EXPORT
plg.export_function = 'writeData'
plg.export_options = 'WriterOptionBox'
plg.export_options_title = ('Web Family Tree export options')
plg.extension = "wft"

#------------------------------------------------------------------------
#
# GEDCOM
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'ex_ged'
plg.name  = _('GEDCOM')
plg.name_accell  = _('GE_DCOM')
plg.description =  _('GEDCOM is used to transfer data between genealogy programs. '
                'Most genealogy software will accept a GEDCOM file as input.')
plg.version = '1.0'
plg.gramps_target_version = '3.3'
plg.status = STABLE
plg.fname = 'ExportGedcom.py'
plg.ptype = EXPORT
plg.export_function = 'export_data'
plg.export_options = 'WriterOptionBox'
plg.export_options_title = ('GEDCOM export options')
plg.extension = "ged"

#------------------------------------------------------------------------
#
# Geneweb
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'ex_geneweb'
plg.name  = _('GeneWeb')
plg.name_accell  = _('_GeneWeb')
plg.description =  _('GeneWeb is a web based genealogy program.')
plg.version = '1.0'
plg.gramps_target_version = '3.3'
plg.status = STABLE
plg.fname = 'ExportGeneWeb.py'
plg.ptype = EXPORT
plg.export_function = 'exportData'
plg.export_options = 'WriterOptionBox'
plg.export_options_title = ('GeneWeb export options')
plg.extension = "gw"

#------------------------------------------------------------------------
#
# GRAMPS package (portable XML)
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'ex_gpkg'
plg.name  = _('Gramps XML Package (family tree and media)')
plg.name_accell  = _('Gra_mps XML Package (family tree and media)')
plg.description =  _('Gramps package is an archived XML family tree together '
                 'with the media object files.')
plg.version = '1.0'
plg.gramps_target_version = '3.3'
plg.status = STABLE
plg.fname = 'ExportPkg.py'
plg.ptype = EXPORT
plg.export_function = 'writeData'
plg.export_options = 'WriterOptionBox'
plg.export_options_title = ('Gramps package export options')
plg.extension = "gpkg"

#------------------------------------------------------------------------
#
# GRAMPS XML database
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'ex_gramps'
plg.name  = _('Gramps XML (family tree)')
plg.name_accell  = _('Gramps _XML (family tree)')
plg.description =  _('Gramps XML export is a complete archived XML backup of a' 
                 ' Gramps family tree without the media object files.'
                 ' Suitable for backup purposes.')
plg.version = '1.0'
plg.gramps_target_version = '3.3'
plg.status = STABLE
plg.fname = 'ExportXml.py'
plg.ptype = EXPORT
plg.export_function = 'export_data'
plg.export_options = 'WriterOptionBox'
plg.export_options_title = ('Gramps XML export options')
plg.extension = "gramps"

#------------------------------------------------------------------------
#
# vCalendar
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'ex_vcal'
plg.name  = _('vCalendar')
plg.name_accell  = _('vC_alendar')
plg.description =  _('vCalendar is used in many calendaring and PIM applications.')
plg.version = '1.0'
plg.gramps_target_version = '3.3'
plg.status = STABLE
plg.fname = 'ExportVCalendar.py'
plg.ptype = EXPORT
plg.export_function = 'exportData'
plg.export_options = 'WriterOptionBox'
plg.export_options_title = ('vCalendar export options')
plg.extension = "vcs"

#------------------------------------------------------------------------
#
# vCard
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'ex_vcard'
plg.name  = _('vCard')
plg.name_accell  = _('_vCard')
plg.description =  _('vCard is used in many addressbook and pim applications.')
plg.version = '1.0'
plg.gramps_target_version = '3.3'
plg.status = STABLE
plg.fname = 'ExportVCard.py'
plg.ptype = EXPORT
plg.export_function = 'exportData'
plg.export_options = 'WriterOptionBox'
plg.export_options_title = ('vCard export options')
plg.extension = "vcf"