#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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

# Written by Alex Roitman

"""
Module responsible for handling the command line arguments for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os
import getopt
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import ReadXML
import GrampsMime
import DbPrompter
import QuestionDialog
import GrampsKeys
import RecentFiles
import PluginMgr
import Report
import Tool

#-------------------------------------------------------------------------
#
# ArgHandler
#
#-------------------------------------------------------------------------
class ArgHandler:
    """
    This class is responsible for handling command line arguments (if any)
    given to gramps. The valid arguments are:

    FILE                :   filename to open. 
                            All following arguments will be ignored.
    -i, --import=FILE   :   filename to import.
    -O, --open=FILE     :   filename to open.
    -o, --output=FILE   :   filename to export.
    -f, --format=FORMAT :   format of the file preceding this option.
    
    If the filename (no flags) is specified, the interactive session is 
    launched using data from filename. If the filename is not in a natvive
    (grdb) format, dialog will be presented to set up a grdb database.
    In this mode (filename, no flags), the rest of the arguments is ignored.
    This is a mode suitable by default for GUI launchers, mime type handlers,
    and the like
    
    If no filename or -i option is given, a new interactive session (empty
    database) is launched, since no data is given anyway.
    
    If -O or -i option is given, but no -o or -a options are given, an
    interactive session is launched with the FILE (specified with -i). 
    
    If both input (-O or -i) and processing (-o or -a) options are given,
    interactive session will not be launched. 
    """

    def __init__(self,parent,args):
        self.parent = parent
        self.args = args

        self.open_gui = None
        self.open = None
        self.exports = []
        self.actions = []
        self.imports = []

        self.parse_args()
        self.handle_args()

    #-------------------------------------------------------------------------
    #
    # Argument parser: sorts out given arguments
    #
    #-------------------------------------------------------------------------
    def parse_args(self):
        """
        Fill in lists with open, exports, imports, and actions options.
        """

        try:
            options,leftargs = getopt.getopt(self.args[1:],
                        const.shortopts,const.longopts)
        except getopt.GetoptError:
            # return without filling anything if we could not parse the args
            print "Error parsing arguments: %s " % self.args[1:]
            return

        if leftargs:
            # if there were an argument without option, use it as a file to 
            # open and return
            self.open_gui = leftargs[0]
            print "Trying to open: %s ..." % leftargs[0]
            return

        for opt_ix in range(len(options)):
            o,v = options[opt_ix]
            if o in ( '-O', '--open'):
                fname = v
                ftype = GrampsMime.get_type(
                    os.path.abspath(os.path.expanduser(fname)))
                if opt_ix<len(options)-1 \
                            and options[opt_ix+1][0] in ( '-f', '--format'): 
                    format = options[opt_ix+1][1]
                    if format not in ('gedcom','gramps-xml','grdb'):
                        print "Invalid format:  %s" % format
                        print "Ignoring input file:  %s" % fname
                        continue
                elif ftype == const.app_gedcom:
                    format = 'gedcom'
                elif ftype == const.app_gramps_xml:
                    format = 'gramps-xml'
                elif ftype == const.app_gramps:
                    format = 'grdb'
                else:
                    print "Unrecognized format for input file %s" % fname
                    print "Ignoring input file:  %s" % fname
                    continue
                self.open = (fname,format)
            elif o in ( '-i', '--import'):
                fname = v
                ftype = GrampsMime.get_type(
                    os.path.abspath(os.path.expanduser(fname)))
                if opt_ix<len(options)-1 \
                            and options[opt_ix+1][0] in ( '-f', '--format'): 
                    format = options[opt_ix+1][1]
                    if format not in ('gedcom',
                                      'gramps-xml',
                                      'gramps-pkg',
                                      'grdb',
                                      'geneweb'):
                        print "Invalid format:  %s" % format
                        print "Ignoring input file:  %s" % fname
                        continue
                elif ftype == const.app_gedcom:
                    format = 'gedcom'
                elif ftype == const.app_gramps_package:
                    format = 'gramps-pkg'
                elif ftype == const.app_gramps_xml:
                    format = 'gramps-xml'
                elif ftype == const.app_gramps:
                    format = 'grdb'
                elif ftype == const.app_geneweb:
                    format = 'geneweb'
                else:
                    print "Unrecognized format for input file %s" % fname
                    print "Ignoring input file:  %s" % fname
                    continue
                self.imports.append((fname,format))
            elif o in ( '-o', '--output' ):
                outfname = v
                if opt_ix<len(options)-1 \
                            and options[opt_ix+1][0] in ( '-f', '--format'): 
                    outformat = options[opt_ix+1][1]
                    if outformat not in ('gedcom',
                                         'gramps-xml',
                                         'gramps-pkg',
                                         'grdb',
                                         'iso',
                                         'wft',
                                         'geneweb'):
                        print "Invalid format:  %s" % outformat
                        print "Ignoring output file:  %s" % outfname
                        continue
                elif outfname[-3:].upper() == "GED":
                    outformat = 'gedcom'
                elif outfname[-4:].upper() == "GPKG":
                    outformat = 'gramps-pkg'
                elif outfname[-3:].upper() == "WFT":
                    outformat = 'wft'
                elif outfname[-2:].upper() == "GW":
                    outformat = 'geneweb'
                elif outfname[-6:].upper() == "GRAMPS":
                    outformat = 'gramps-xml'
                elif outfname[-4:].upper() == "GRDB":
                    outformat = 'grdb'
                else:
                    print "Unrecognized format for output file %s" % outfname
                    print "Ignoring output file:  %s" % outfname
                    continue
                self.exports.append((outfname,outformat))
            elif o in ( '-a', '--action' ):
                action = v
                if action not in ( 'check', 'summary', 'report', 'tool' ):
                    print "Unknown action: %s. Ignoring." % action
                    continue
                options_str = ""
                if opt_ix<len(options)-1 \
                            and options[opt_ix+1][0] in ( '-p', '--options' ): 
                    options_str = options[opt_ix+1][1]
                self.actions.append((action,options_str))
            
    #-------------------------------------------------------------------------
    #
    # open data in native format
    #
    #-------------------------------------------------------------------------
    def auto_save_load(self,filename):
        self.parent.active_person = None
        filename = os.path.normpath(os.path.abspath(filename))
        filetype = GrampsMime.get_type(filename)
        if filetype == const.app_gramps:
            import GrampsBSDDB
            self.parent.db.close()
            self.parent.db = GrampsBSDDB.GrampsBSDDB()
            return self.parent.read_file(filename)
        elif filetype == const.app_gramps_xml:
            import GrampsXMLDB
            self.parent.db.close()
            self.parent.db = GrampsXMLDB.GrampsXMLDB()
            return self.parent.read_file(filename)
        elif filetype == const.app_gedcom:
            import GrampsGEDDB
            self.parent.db.close()
            self.parent.db = GrampsGEDDB.GrampsGEDDB()
            return self.parent.read_file(filename)
        else:
            return 0

    #-------------------------------------------------------------------------
    #
    # Overall argument handler: 
    # sorts out the sequence and details of operations
    #
    #-------------------------------------------------------------------------
    def handle_args(self):
        """
        Depending on the given arguments, import or open data, launch
        session, write files, and/or perform actions.
        """

        if self.open_gui:
            # Filename was given. Open a session with that file. Forget
            # the rest of given arguments.
            success = False
            filename = os.path.abspath(os.path.expanduser(self.open_gui))
            filetype = GrampsMime.get_type(filename) 
            if filetype in (const.app_gramps,const.app_gedcom,
                                        const.app_gramps_xml):
                # Say the type outloud
                if filetype == const.app_gramps:
                    print "Type: GRAMPS database"
                elif filetype == const.app_gedcom:
                    print "Type: GEDCOM file"
                elif filetype == const.app_gramps_xml:
                    print "Type: GRAMPS XML database"

                if self.auto_save_load(filename):
                    print "Opened successfully!"
                    success = True
                else:
                    print "Cannot open %s. Exiting..."
            elif filetype in (const.app_gramps_package,):
                QuestionDialog.OkDialog( _("Opening non-native format"), 
                                    _("New GRAMPS database has to be set up "
                                      "when opening non-native formats. The "
                                      "following dialog will let you select "
                                      "the new database."),
                                    self.parent.topWindow)
                prompter = DbPrompter.NewNativeDbPrompter(self.parent)
                if not prompter.chooser():
                    QuestionDialog.ErrorDialog( 
                        _("New GRAMPS database was not set up"),
                        _('GRAMPS cannot open non-native data '
                          'without setting up new GRAMPS database.'))
                    print "Cannot continue without native database. Exiting..." 
                    os._exit(1)
                elif filetype == const.app_gramps_package:
                    print "Type: GRAMPS package"
                    self.parent.read_pkg(filename)
                success = True
            else:
                print "Unknown file type: %s" % filetype
                QuestionDialog.ErrorDialog( 
                        _("Could not open file: %s") % filename,
                        _('File type "%s" is unknown to GRAMPS.\n\n'
                          'Valid types are: GRAMPS database, GRAMPS XML, '
                          'GRAMPS package, and GEDCOM.') % filetype)
                print "Exiting..." 
                os._exit(1)
            if success:
                # Add the file to the recent items
                RecentFiles.recent_files(filename,filetype)
                self.parent.build_recent_menu()
            else:
                os._exit(1)
            return
           
        if self.open:
            # Filename to open was given. Open it natively (grdb or any of
            # the InMem formats, without setting up a new database. Then
            # go on and process the rest of the command line arguments.

            self.parent.cl = bool(self.exports or self.actions)

            name,format = self.open
            success = False
            filename = os.path.abspath(os.path.expanduser(name))

            if format == 'grdb':
                print "Type: GRAMPS database"
            elif format == 'gedcom':
                print "Type: GEDCOM"
            elif format == 'gramps-xml':
                print "Type: GRAMPS XML"
            else:
                print "Unknown file type: %s" % format
                print "Exiting..." 
                os._exit(1)

            if self.auto_save_load(filename):
                print "Opened successfully!"
                success = True
            else:
                print "Error opening the file." 
                print "Exiting..." 
                os._exit(1)

        if self.imports:
            self.parent.cl = bool(self.exports or
                                  self.actions or self.parent.cl)

            # Create dir for imported database(s)
            self.impdir_path = os.path.expanduser("~/.gramps/import" )
            self.imp_db_path = os.path.expanduser(
                "~/.gramps/import/import_db.grdb" )
            if not os.path.isdir(self.impdir_path):
                try:
                    os.mkdir(self.impdir_path,0700)
                except:
                    print "Could not create import directory %s. Exiting." \
                        % self.impdir_path 
                    os._exit(1)
            elif not os.access(self.impdir_path,os.W_OK):
                print "Import directory %s is not writable. Exiting." \
                    % self.impdir_path 
                os._exit(1)
            # and clean it up before use
            files = os.listdir(self.impdir_path) ;
            for fn in files:
                if os.path.isfile(os.path.join(self.impdir_path,fn)):
                    os.remove(os.path.join(self.impdir_path,fn))

            self.parent.load_database(self.imp_db_path)

            for imp in self.imports:
                print "Importing: file %s, format %s." % imp
                self.cl_import(imp[0],imp[1])

        elif len(self.args) > 1 and not self.open:
            print "No data was given -- will launch interactive session."
            print "To use in the command-line mode,", \
                "supply at least one input file to process."
            print "Launching interactive session..."

        if self.parent.cl:
            for (action,options_str) in self.actions:
                print "Performing action: %s." % action
                if options_str:
                    print "Using options string: %s" % options_str
                self.cl_action(action,options_str)
            
            for expt in self.exports:
                print "Exporting: file %s, format %s." % expt
                self.cl_export(expt[0],expt[1])

            print "Cleaning up."
            # remove import db after use
            self.parent.db.close()
            if self.imports:
                os.remove(self.imp_db_path)
            print "Exiting."
            os._exit(0)

        if self.imports:
            self.parent.import_tool_callback()
        elif GrampsKeys.get_lastfile() and GrampsKeys.get_autoload():
            if self.auto_save_load(GrampsKeys.get_lastfile()) == 0:
                DbPrompter.DbPrompter(self.parent,0)
        else:
            DbPrompter.DbPrompter(self.parent,0)


    #-------------------------------------------------------------------------
    #
    # Import handler
    #
    #-------------------------------------------------------------------------
    def cl_import(self,filename,format):
        """
        Command-line import routine. Try to import filename using the format.
        Any errors will cause the os._exit(1) call.
        """
        if format == 'grdb':
            import ReadGrdb
            filename = os.path.normpath(os.path.abspath(filename))
            try:
                ReadGrdb.importData(self.parent.db,filename,None)
            except:
                print "Error importing %s" % filename
                os._exit(1)
        elif format == 'gedcom':
            import ReadGedcom
            filename = os.path.normpath(os.path.abspath(filename))
            try:
                g = ReadGedcom.GedcomParser(self.parent.db,filename,None)
                g.parse_gedcom_file()
                g.resolve_refns()
                del g
            except:
                print "Error importing %s" % filename
                os._exit(1)
        elif format == 'gramps-xml':
            try:
                ReadXML.importData(self.parent.db,filename,None,self.parent.cl)
            except:
                print "Error importing %s" % filename
                os._exit(1)
        elif format == 'geneweb':
            import ImportGeneWeb
            filename = os.path.normpath(os.path.abspath(filename))
            try:
                ImportGeneWeb.importData(self.parent.db,filename,None)
            except:
                print "Error importing %s" % filename
                os._exit(1)
        elif format == 'gramps-pkg':
            # Create tempdir, if it does not exist, then check for writability
            tmpdir_path = os.path.expanduser("~/.gramps/tmp" )
            if not os.path.isdir(tmpdir_path):
                try:
                    os.mkdir(tmpdir_path,0700)
                except:
                    print "Could not create temporary directory %s" \
                          % tmpdir_path 
                    os._exit(1)
            elif not os.access(tmpdir_path,os.W_OK):
                print "Temporary directory %s is not writable" % tmpdir_path 
                os._exit(1)
            else:    # tempdir exists and writable -- clean it up if not empty
                files = os.listdir(tmpdir_path) ;
                for fn in files:
                    os.remove( os.path.join(tmpdir_path,fn) )

            try:
                import TarFile
                t = TarFile.ReadTarFile(filename,tmpdir_path)
                t.extract()
                t.close()
            except:
                print "Error extracting into %s" % tmpdir_path 
                os._exit(1)

            dbname = os.path.join(tmpdir_path,const.xmlFile)

            try:
                ReadXML.importData(self.parent.db,dbname,None)
            except:
                print "Error importing %s" % filename
                os._exit(1)
            # Clean up tempdir after ourselves
            files = os.listdir(tmpdir_path) 
            for fn in files:
                os.remove(os.path.join(tmpdir_path,fn))
            os.rmdir(tmpdir_path)
        else:
            print "Invalid format:  %s" % format
            os._exit(1)
        if not self.parent.cl:
            return self.parent.post_load(self.imp_db_path)

    #-------------------------------------------------------------------------
    #
    # Export handler
    #
    #-------------------------------------------------------------------------
    def cl_export(self,filename,format):
        """
        Command-line export routine. 
        Try to write into filename using the format.
        Any errors will cause the os._exit(1) call.
        """
        if format == 'grdb':
            import WriteGrdb
            try:
                WriteGrdb.exportData(self.parent.db,filename)
            except:
                print "Error exporting %s" % filename
                os._exit(1)
        elif format == 'gedcom':
            import WriteGedcom
            try:
                gw = WriteGedcom.GedcomWriter(self.parent.db,None,1,filename)
                ret = gw.export_data(filename)
            except:
                print "Error exporting %s" % filename
                os._exit(1)
        elif format == 'gramps-xml':
            filename = os.path.normpath(os.path.abspath(filename))
            if filename:
                try:
                    import WriteXML
                    g = WriteXML.XmlWriter(self.parent.db,None,0,1)
                    ret = g.write(filename)
                except:
                    print "Error exporting %s" % filename
                    os._exit(1)
        elif format == 'gramps-pkg':
            try:
                import WritePkg
                writer = WritePkg.PackageWriter(self.parent.db,filename)
                ret = writer.export()
            except:
                print "Error creating %s" % filename
                os._exit(1)
        elif format == 'iso':
            import WriteCD
            try:
                writer = WriteCD.PackageWriter(self.parent.db,filename,1)
                ret = writer.export()
            except:
                print "Error exporting %s" % filename
                os._exit(1)
        elif format == 'wft':
            import WriteFtree
            try:
                writer = WriteFtree.FtreeWriter(self.parent.db,None,1,filename)
                ret = writer.export_data()
            except:
                print "Error exporting %s" % filename
                os._exit(1)
        elif format == 'geneweb':
            import WriteGeneWeb
            try:
                writer = WriteGeneWeb.GeneWebWriter(self.parent.db,
                                                    None,1,filename)
                ret = writer.export_data()
            except:
                print "Error exporting %s" % filename
                os._exit(1)
        else:
            print "Invalid format: %s" % format
            os._exit(1)

    #-------------------------------------------------------------------------
    #
    # Action handler
    #
    #-------------------------------------------------------------------------
    def cl_action(self,action,options_str):
        """
        Command-line action routine. Try to perform specified action.
        Any errors will cause the os._exit(1) call.
        """
        if action == 'check':
            import Check
            checker = Check.CheckIntegrity(self.parent.db,None,None)
            checker.check_for_broken_family_links()
            checker.cleanup_missing_photos(1)
            checker.check_parent_relationships()
            checker.cleanup_empty_families(0)
            errs = checker.build_report(1)
            if errs:
                checker.report(1)
        elif action == 'summary':
            import Summary
            text = Summary.build_report(self.parent.db,None)
            print text
        elif action == "report":
            try:
                options_str_dict = dict( [ tuple(chunk.split('='))
                    for chunk in options_str.split(',') ] )
            except:
                options_str_dict = {}
                print "Ignoring invalid options string."

            name = options_str_dict.pop('name',None)
            if not name:
                print "Report name not given. Please use name=reportname"
                os._exit(1)

            for item in PluginMgr.cl_list:
                if name == item[0]:
                    category = item[1]
                    report_class = item[2]
                    options_class = item[3]
                    if category in (Report.CATEGORY_BOOK,Report.CATEGORY_CODE,
                                    Report.CATEGORY_WEB):
                        options_class(self.parent.db,name,
                                      category,options_str_dict)
                    else:
                        Report.cl_report(self.parent.db,name,category,
                                         report_class,options_class,
                                         options_str_dict)
                    return

            print "Unknown report name. Available names are:"
            for item in PluginMgr.cl_list:
                print "   %s" % item[0]
        elif action == "tool":
            try:
                options_str_dict = dict( [ tuple(chunk.split('=')) for
                                           chunk in options_str.split(',') ] )
            except:
                options_str_dict = {}
                print "Ignoring invalid options string."

            name = options_str_dict.pop('name',None)
            if not name:
                print "Tool name not given. Please use name=toolname"
                os._exit(1)

            for item in PluginMgr.cli_tool_list:
                if name == item[0]:
                    category = item[1]
                    tool_class = item[2]
                    options_class = item[3]
                    Tool.cli_tool(self.parent.db,name,category,
                                  tool_class,options_class,options_str_dict)
                    return

            print "Unknown tool name. Available names are:"
            for item in PluginMgr.cli_tool_list:
                print "   %s" % item[0]
        else:
            print "Unknown action: %s." % action
            os._exit(1)
