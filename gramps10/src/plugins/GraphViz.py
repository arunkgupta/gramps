#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
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

"Generate files/Relationship graph"

import os
import string

import intl
import Utils

import gtk

_ = intl.gettext

import libglade
from Report import *
from TextDoc import *

_scaled = 0
_single = 1
_multiple = 2

_pagecount_map = {
    _("Single (scaled)") : _scaled,
    _("Single") : _single,
    _("Multiple") : _multiple,
    }
    
#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class GraphVizDialog(ReportDialog):
    def __init__(self,database,person):
        ReportDialog.__init__(self,database,person)

    #------------------------------------------------------------------------
    #
    # Customization hooks
    #
    #------------------------------------------------------------------------
    def get_title(self):
        """The window title for this dialog"""
        return "%s - %s - GRAMPS" % (_("Relationship Graph"),
                                     _("Graphical Reports"))

    def get_target_browser_title(self):
        """The title of the window created when the 'browse' button is
        clicked in the 'Save As' frame."""
        return _("Graphviz File")

    def get_print_pagecount_map(self):
        """Set up the list of possible page counts."""
        return (_pagecount_map, _("Single (scaled)"))

    def get_report_generations(self):
        """Default to 10 generations, no page breaks."""
        return (10, 0)

    def get_report_filters(self):
        """Set up the list of possible content filters."""

        name = self.person.getPrimaryName().getName()
        
        all = GenericFilter.GenericFilter()
        all.set_name(_("Entire Database"))
        all.add_rule(GenericFilter.Everyone([]))

        des = GenericFilter.GenericFilter()
        des.set_name(_("Descendants of %s") % name)
        des.add_rule(GenericFilter.IsDescendantOf([self.person.getId()]))
        
        ans = GenericFilter.GenericFilter()
        ans.set_name(_("Ancestors of %s") % name)
        ans.add_rule(GenericFilter.IsAncestorOf([self.person.getId()]))

        com = GenericFilter.GenericFilter()
        com.set_name(_("People with common ancestor with %s") % name)
        com.add_rule(GenericFilter.HasCommonAncestorWith([self.person.getId()]))

        return [all,des,ans,com]

    def add_user_options(self):
        self.arrowstyle_optionmenu = gtk.GtkOptionMenu()
        menu = gtk.GtkMenu()
        
        menuitem = gtk.GtkMenuItem(_("Descendants <- Ancestors"))
        menuitem.set_data('t', ('none', 'normal'))
        menuitem.show()
        menu.append(menuitem)
        
        menuitem = gtk.GtkMenuItem(_("Descendants -> Ancestors"))
        menuitem.set_data('t', ('normal', 'none'))
        menuitem.show()
        menu.append(menuitem)

        menuitem = gtk.GtkMenuItem(_("Descendants <-> Ancestors"))
        menuitem.set_data('t', ('normal', 'normal'))
        menuitem.show()
        menu.append(menuitem)

        menuitem = gtk.GtkMenuItem(_("Descendants - Ancestors"))
        menuitem.set_data('t', ('none', 'none'))
        menuitem.show()
        menu.append(menuitem)

        menu.set_active(0)

        self.arrowstyle_optionmenu.set_menu(menu)

        self.add_frame_option(_("GraphViz Options"),
                              _("Arrowhead Options"),
                              self.arrowstyle_optionmenu,
                              _("Choose the direction that the arrows point."))
        
        msg = _("Include Birth and Death Dates")
        self.includedates_cb = gtk.GtkCheckButton(msg)
        self.includedates_cb.set_active(1)
        self.add_frame_option(_("GraphViz Options"), '',
                              self.includedates_cb,
                              _("Include the years that the individual "
                                "was born and/or died in the graph node "
                                "labels."))

        self.includeurl_cb = gtk.GtkCheckButton(_("Include URLs"))
        self.includeurl_cb.set_active(1)
        self.add_frame_option(_("GraphViz Options"), '',
                              self.includeurl_cb,
                              _("Include a URL in each graph node so "
                                "that PDF and imagemap files can be "
                                "generated that contain active links "
                                "to the files generated by the 'Generate "
                                "Web Site' report."))

        self.colorize_cb = gtk.GtkCheckButton(_("Colorize Graph"))
        self.colorize_cb.set_active(1)
        self.add_frame_option(_("GraphViz Options"),
                              '',
                              self.colorize_cb,
                              _("Males will be outlined in blue, females "
                                "will be outlined in pink.  If the sex of "
                                "an individual is unknown it will be "
                                "outlined in black."))

        self.adoptionsdashed_cb = gtk.GtkCheckButton(_("Indicate non-birth relationships with dashed lines"))
        self.adoptionsdashed_cb.set_active(1)
        self.add_frame_option(_("GraphViz Options"),
                              '',
                              self.adoptionsdashed_cb,
                              _("Non-birth relationships will show up "
                                "as dashed lines in the graph."))

        self.show_families_cb = gtk.GtkCheckButton(_("Show family nodes"))
        self.show_families_cb.set_active(0)
        self.add_frame_option(_("GraphViz Options"),
                              '',
                              self.show_families_cb,
                              _("Families will show up as circles, linked "
                                "to parents and children."))

        tb_margin_adj = gtk.GtkAdjustment(value=0.5, lower=0.25,
                                      upper=100.0, step_incr=0.25)
        lr_margin_adj = gtk.GtkAdjustment(value=0.5, lower=0.25,
                                      upper=100.0, step_incr=0.25)

        self.tb_margin_sb = gtk.GtkSpinButton(adj=tb_margin_adj, digits=2)
        self.lr_margin_sb = gtk.GtkSpinButton(adj=lr_margin_adj, digits=2)

        self.add_frame_option(_("GraphViz Options"),
                              _("Top & Bottom Margins"),
                              self.tb_margin_sb)
        self.add_frame_option(_("GraphViz Options"),
                              _("Left & Right Margins"),
                              self.lr_margin_sb)

        hpages_adj = gtk.GtkAdjustment(value=1, lower=1, upper=25, step_incr=1)
        vpages_adj = gtk.GtkAdjustment(value=1, lower=1, upper=25, step_incr=1)

        self.hpages_sb = gtk.GtkSpinButton(adj=hpages_adj, digits=0)
        self.vpages_sb = gtk.GtkSpinButton(adj=vpages_adj, digits=0)

        self.add_frame_option(_("GraphViz Options"),
                              _("Number of Horizontal Pages"),
                              self.hpages_sb,
                              _("GraphViz can create very large graphs by "
                                "spreading the graph across a rectangular "
                                "array of pages. This controls the number "
                                "pages in the array horizontally."))
        self.add_frame_option(_("GraphViz Options"),
                              _("Number of Vertical Pages"),
                              self.vpages_sb,
                              _("GraphViz can create very large graphs "
                                "by spreading the graph across a "
                                "rectangular array of pages. This "
                                "controls the number pages in the array "
                                "vertically."))

    #------------------------------------------------------------------------
    #
    # Functions related to selecting/changing the current file format
    #
    #------------------------------------------------------------------------
    def make_doc_menu(self):
        """Build a one item menu of document types that are
        appropriate for this report."""
        map = {"Graphviz (dot)" : None}
        myMenu = Utils.build_string_optmenu(map, None)
        self.format_menu.set_menu(myMenu)

    def make_document(self):
        """Do Nothing.  This document will be created in the
        make_report routine."""
        pass

    #------------------------------------------------------------------------
    #
    # Functions related to setting up the dialog window
    #
    #------------------------------------------------------------------------
    def setup_style_frame(self):
        """The style frame is not used in this dialog."""
        pass

    #------------------------------------------------------------------------
    #
    # Functions related to retrieving data from the dialog window
    #
    #------------------------------------------------------------------------
    def parse_style_frame(self):
        """The style frame is not used in this dialog."""
        pass

    def parse_other_frames(self):
        menu = self.arrowstyle_optionmenu.get_menu()
        self.arrowheadstyle, self.arrowtailstyle = menu.get_active().get_data('t')
        self.includedates = self.includedates_cb.get_active()
        self.includeurl = self.includeurl_cb.get_active()
        self.tb_margin = self.tb_margin_sb.get_value_as_float()
        self.lr_margin = self.lr_margin_sb.get_value_as_float()
        self.colorize = self.colorize_cb.get_active()
        self.adoptionsdashed = self.adoptionsdashed_cb.get_active()
        self.hpages = self.hpages_sb.get_value_as_int()
        self.vpages = self.vpages_sb.get_value_as_int()
        self.show_families = self.show_families_cb.get_active()

    #------------------------------------------------------------------------
    #
    # Functions related to creating the actual report document.
    #
    #------------------------------------------------------------------------
    def make_report(self):
        """Create the object that will produce the GraphViz file."""
        width = self.paper.get_width_inches()
        height = self.paper.get_height_inches()

        file = open(self.target_path,"w")

        ind_list = self.filter.apply(self.db, self.db.getPersonMap().values())

        write_dot(file, ind_list, self.orien, width, height,
                  self.tb_margin, self.lr_margin, self.hpages,
                  self.vpages, self.includedates, self.includeurl,
                  self.colorize, self.adoptionsdashed, self.arrowheadstyle,
                  self.arrowtailstyle, self.show_families)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def report(database,person):
    GraphVizDialog(database,person)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def write_dot(file, ind_list, orien, width, height, tb_margin,
              lr_margin, hpages, vpages, includedates, includeurl,
              colorize, adoptionsdashed, arrowheadstyle, arrowtailstyle,
              show_families):
    file.write("digraph g {\n")
    file.write("bgcolor=white;\n")
    file.write("rankdir=LR;\n")
    file.write("center=1;\n")
    file.write("margin=0.5;\n")
    file.write("ratio=fill;\n")
    file.write("size=\"%3.1f,%3.1f\";\n" % ((width*hpages)-(lr_margin*2)-((hpages-1)*1.0),
                                            (height*vpages)-(tb_margin*2)-((vpages-1)*1.0)))
    file.write("page=\"%3.1f,%3.1f\";\n" % (width,height))

    if orien == PAPER_LANDSCAPE:
        file.write("rotate=90;\n")

    if len(ind_list) > 1:
        dump_index(ind_list,file,includedates,includeurl,colorize,
                   arrowheadstyle,arrowtailstyle,show_families)
        dump_person(ind_list,file,adoptionsdashed,arrowheadstyle,
                    arrowtailstyle,show_families)

    file.write("}\n")
    file.close()

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def dump_person(person_list,file,adoptionsdashed,arrowheadstyle,
                arrowtailstyle,show_families):
    for person in person_list:
        pid = string.replace(person.getId(),'-','_')
        for family, mrel, frel in person.getParentList():
            father   = family.getFather()
            mother   = family.getMother()
            fadopted = frel != _("Birth")
            madopted = mrel != _("Birth")
            if show_families:
                # Link to the family node.
                famid = string.replace(family.getId(),'-','_')
                file.write('p%s -> f%s ['  % (pid, famid))
                file.write('arrowhead=%s, arrowtail=%s, ' %
                           (arrowheadstyle, arrowtailstyle))
                if adoptionsdashed and (fadopted or madopted):
                    file.write('style=dashed')
                else:
                    file.write('style=solid')
                file.write('];\n')
            else:
                # Link to the parents' nodes directly.
                if father and father in person_list:
                    fid = string.replace(father.getId(),'-','_')
                    file.write('p%s -> p%s ['  % (pid, fid))
                    file.write('arrowhead=%s, arrowtail=%s, ' %
                               (arrowheadstyle, arrowtailstyle))
                    if adoptionsdashed and fadopted:
                        file.write('style=dashed')
                    else:
                        file.write('style=solid')
                    file.write('];\n')
                if mother and mother in person_list:
                    mid = string.replace(mother.getId(),'-','_')
                    file.write('p%s -> p%s ['  % (pid, mid))
                    file.write('arrowhead=%s, arrowtail=%s, ' %
                               (arrowheadstyle, arrowtailstyle))
                    if adoptionsdashed and madopted:
                        file.write('style=dashed')
                    else:
                        file.write('style=solid')
                    file.write('];\n')

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def dump_index(person_list,file,includedates,includeurl,colorize,
               arrowheadstyle,arrowtailstyle,show_families):
    # The list of families for which we have output the node, so we
    # don't do it twice.
    families_done = []
    for person in person_list:
        # Output the person's node.
        label = person.getPrimaryName().getName()
        id = string.replace(person.getId(),'-','_')
        if includedates:
            if person.getBirth().getDateObj().getYearValid():
                birth = '%i' % person.getBirth().getDateObj().getYear()
            else:
                birth = ''
            if person.getDeath().getDateObj().getYearValid():
                death = '%i' % person.getDeath().getDateObj().getYear()
            else:
                death = ''
            label = label + '\\n(%s - %s)' % (birth, death)
        file.write('p%s [shape=box, ' % id)
        if includeurl:
            file.write('URL="%s.html", ' % id)
        if colorize:
            gender = person.getGender()
            if gender == person.male:
                file.write('color=dodgerblue4, ')
            elif gender == person.female:
                file.write('color=deeppink, ')
            else:
                file.write('color=black, ')
        file.write('fontname="Arial", label="%s"];\n' % label)
        # Output families's nodes.
        if show_families:
            family_list = person.getFamilyList()
            for fam in family_list:
                fid = string.replace(fam.getId(),'-','_')
                if fam not in families_done:
                    file.write('f%s [shape=circle, label="", ' % fid)
                    file.write('weight=8, height=.3];\n')
                # Link this person to all his/her families.
                file.write('f%s -> p%s [' % (fid, id))
                file.write('arrowhead=%s, arrowtail=%s, ' %
                           (arrowheadstyle, arrowtailstyle))
                file.write('style=solid];\n')



#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def get_description():
    return _("Generates relationship graphs, currently only in GraphViz "
             "format. GraphViz (dot) can transform the graph into "
             "postscript, jpeg, png, vrml, svg, and many other formats. "
             "For more information or to get a copy of GraphViz, "
             "goto http://www.graphviz.org")

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
from Plugins import register_report

register_report(
    report,
    _("Relationship Graph"),
    status=(_("Beta")),
    category=_("Graphical Reports"),
    description=get_description()
    )
