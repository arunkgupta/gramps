##
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007  Brian G. Matherly
# Copyright (C) 2010  Peter Landgren
# Copyright (C) 2010  Jakim Friant
# Copyright (C) 2011  Adam Stein <adam@csh.rit.edu>
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
# $Id: _Endnotes.py 15169 2010-04-16 20:59:10Z bmcage $

"""
Provide utilities for printing endnotes in text reports.
"""
from gen.plug.docgen import FontStyle, ParagraphStyle, FONT_SANS_SERIF
from gen.lib import NoteType
from gen.ggettext import gettext as _

def add_endnote_styles(style_sheet):
    """
    Add paragraph styles to a style sheet to be used for displaying endnotes.
    
    @param style_sheet: Style sheet
    @type style_sheet: L{docgen.StyleSheet}
    """
    font = FontStyle()
    font.set(face=FONT_SANS_SERIF, size=14, italic=1)
    para = ParagraphStyle()
    para.set_font(font)
    para.set_header_level(2)
    para.set_top_margin(0.25)
    para.set_bottom_margin(0.25)
    para.set_description(_('The style used for the generation header.'))
    style_sheet.add_paragraph_style("Endnotes-Header", para)

    para = ParagraphStyle()
    para.set(first_indent=-0.75, lmargin=.75)
    para.set_top_margin(0.25)
    para.set_bottom_margin(0.25)
    para.set_description(_('The basic style used for the endnotes source display.'))
    style_sheet.add_paragraph_style("Endnotes-Source", para)

    para = ParagraphStyle()
    para.set(first_indent=-0.9, lmargin=1.9)
#    para.set(lmargin=1.5)
    para.set_top_margin(0.25)
    para.set_bottom_margin(0.25)
    para.set_description(_('The basic style used for the endnotes reference display.'))
    style_sheet.add_paragraph_style("Endnotes-Ref", para)
    
    para = ParagraphStyle()
    para.set(lmargin=1.5)
    para.set_top_margin(0.25)
    para.set_bottom_margin(0.25)
    para.set_description(_('The basic style used for the endnotes notes display.'))
    style_sheet.add_paragraph_style("Endnotes-Notes", para)

def cite_source(bibliography, obj):
    """
    Cite any sources for the object and add them to the bibliography.
    
    @param bibliography: The bibliography to contain the citations.
    @type bibliography: L{Bibliography}
    @param obj: An object with source references.
    @type obj: L{gen.lib.srcbase}
    """
    txt = ""
    slist = obj.get_source_references()
    if slist:
        first = 1
        for ref in slist:
            if not first:
                txt += ', '
            first = 0
            (cindex, key) = bibliography.add_reference(ref)
            txt += "%d" % (cindex + 1)
            if key is not None:
                txt += key
    return txt

def write_endnotes(bibliography, database, doc, printnotes=False, links=False):
    """
    Write all the entries in the bibliography as endnotes.
    
    @param bibliography: The bibliography that contains the citations.
    @type bibliography: L{Bibliography}
    @param database: The database that the sources come from.
    @type database: DbBase
    @param doc: The document to write the endnotes into.
    @type doc: L{docgen.TextDoc}
    @param printnotes: Indicate if the notes attached to a source must be
            written too.
    @type printnotes: bool
    @param links: Indicate if URL links should be makde 'clickable'.
    @type links: bool
    """
    if bibliography.get_citation_count() == 0:
        return

    doc.start_paragraph('Endnotes-Header')
    doc.write_text(_('Endnotes'))
    doc.end_paragraph()
    
    cindex = 0
    for citation in bibliography.get_citation_list():
        cindex += 1
        source = database.get_source_from_handle(citation.get_source_handle())
        first = True
        
        doc.start_paragraph('Endnotes-Source', "%d." % cindex)
        
        src_txt = _format_source_text(source)
            
        doc.write_text(src_txt, links=links)
        doc.end_paragraph()

        ref_list = citation.get_ref_list()
        
        if ref_list:
            first = True
            reflines = ""
            for key, ref in ref_list:
                datepresent = False
                date = ref.get_date_object()
                if date is not None and not date.is_empty():
                    datepresent = True
                if datepresent:
                    if ref.get_page():
                        txt = "%s: %s - %s" % (key, ref.get_page(), str(date))
                    else:
                        txt = "%s: %s" % (key, str(date))
                else:
                    txt = "%s: %s" % (key, ref.get_page())
                if first:
                    reflines += txt
                    first = False
                else:
                    reflines += ('\n%s' % txt)
            doc.write_endnotes_ref(reflines,'Endnotes-Ref', links=links)

        if printnotes:
            note_list = source.get_note_list()
            ind = 1
            for notehandle in note_list: 
                note = database.get_note_from_handle(notehandle)
                doc.start_paragraph('Endnotes-Notes')
                doc.write_text(_('Note %(ind)d - Type: %(type)s') % {
                                'ind': ind,
                                'type': str(note.get_type())})
                doc.end_paragraph()
                doc.write_styled_note(note.get_styledtext(), 
                                        note.get_format(),'Endnotes-Notes',
                                        contains_html= note.get_type() \
                                                        == NoteType.HTML_CODE,
                                        links=links)
                ind += 1

def _format_source_text(source):
    if not source: return ""

    src_txt = ""
    
    if source.get_author():
        src_txt += source.get_author()
    
    if source.get_title():
        if src_txt:
            src_txt += ", "
        src_txt += '"%s"' % source.get_title()
        
    if source.get_publication_info():
        if src_txt:
            src_txt += ", "
        src_txt += source.get_publication_info()
        
    if source.get_abbreviation():
        if src_txt:
            src_txt += ", "
        src_txt += "(%s)" % source.get_abbreviation()
        
    return src_txt
