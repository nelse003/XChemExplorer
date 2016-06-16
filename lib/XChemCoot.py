import gobject
import sys
import os
import pickle

from matplotlib.figure import Figure
#from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas

# XCE libraries
sys.path.append(os.getenv('XChemExplorer_DIR')+'/lib')
import XChemDB
import XChemRefine
import XChemUtils

# libraries from COOT
import pygtk, gtk, pango
import coot

# had to adapt the original coot_utils.py file
# otherwise unable to import the original file without complaints about missing modules etc.
# modified file is now in $XChemExplorer_DIR/lib
import coot_utils_XChem


class GUI(object):

    """
    main class which opens the actual GUI
    """

    def __init__(self):

        ###########################################################################################
        # read in settings file from XChemExplorer to set the relevant paths
        print 'current dir',os.getcwd()
        self.settings = pickle.load(open(".xce_settings.pkl","rb"))
        print 'setting',self.settings
#        self.refine_model_directory=self.settings['refine_model_directory']
        self.database_directory=self.settings['database_directory']
        self.data_source=self.settings['data_source']
        self.db=XChemDB.data_source(self.data_source)

        # checking for external software packages
        self.external_software=XChemUtils.external_software().check()

#        self.selection_criteria =   {   'Show All Datasets':                'RefinementPDB_latest is not null',
#                                        'Show Analysis Pending Only':       "RefinementOutcome='Analysis Pending'",
#                                        'Show Datasets Under Refinement':   "RefinementOutcome='Refinement Ongoing'",
#                                        'Show Confirmed Ligands':           "RefinementOutcome='Ligand Confirmed'",
#                                        'SHow Final Structures':            "RefinementOutcome='Structure Finished'"   }

        self.selection_criteria = [     '0 - All Datasets',
                                        '1 - Analysis Pending',
                                        '2 - PANDDA model',
                                        '3 - In Refinement',
                                        '4 - ComChem ready',
                                        '5 - Deposition ready',
                                        '6 - Deposited'         ]

        self.experiment_stage =     [   ['Review PANDDA export',    '2 - PANDDA model',     65000,  0,  0],
                                        ['In Refinement',           '3 - In Refinement',    65000,  0,  0],
                                        ['Comp Chem Ready!',        '4 - ComChem ready',    65000,  0,  0],
                                        ['Ready for Deposition!',   '5 - Deposition ready', 65000,  0,  0]   ]

        self.ligand_confidence_category = [     '0 - no ligand present',
                                                '1 - low confidence',
                                                '2 - pose/identity uncertain',
                                                '3 - high confidence'   ]

        self.ligand_site_information =  self.db.get_list_of_pandda_sites_for_coot()
    

        # this decides which samples will be looked at
        self.selection_mode = ''
        self.selected_site=self.ligand_site_information[0]

        # the Folder is kind of a legacy thing because my inital idea was to have separate folders
        # for Data Processing and Refinement
        self.project_directory = self.settings['initial_model_directory']
        self.Serial=0
        self.Refine=None
        self.index = -1
        self.Todo=[]

        self.xtalID=''
        self.compoundID=''
        self.spider_plot=''
        self.ligand_confidence=''
        self.refinement_folder=''
#        self.datasetOutcome=''

        self.pdb_style='refine.pdb'
        self.mtz_style='refine.mtz'

        # stores imol of currently loaded molecules and maps
        self.mol_dict = {   'protein':  -1,
                            'ligand':   -1,
                            '2fofc':    -1,
                            'fofc':     -1,
                            'event':    -1  }

        # two dictionaries which are flushed when a new crystal is loaded
        # and which contain information to update the data source if necessary
        self.db_dict_mainTable={}
        self.db_dict_panddaTable={}

        ###########################################################################################
        # some COOT settings
        coot.set_map_radius(15)
        coot.set_colour_map_rotation_for_map(0)
        coot.set_colour_map_rotation_on_read_pdb_flag(0)

        self.QualityIndicators = {  'RefinementRcryst':                         '-',
                                    'RefinementRfree':                          '-',
                                    'RefinementRfreeTraficLight':               'gray',
                                    'RefinementResolution':                     '-',
                                    'RefinementResolutionTL':                   'gray',
                                    'RefinementMolProbityScore':                '-',
                                    'RefinementMolProbityScoreTL':              'gray',
                                    'RefinementRamachandranOutliers':           '-',
                                    'RefinementRamachandranOutliersTL':         'gray',
                                    'RefinementRamachandranFavored':            '-',
                                    'RefinementRamachandranFavoredTL':          'gray',
                                    'RefinementRmsdBonds':                      '-',
                                    'RefinementRmsdBondsTL':                    'gray',
                                    'RefinementRmsdAngles':                     '-',
                                    'RefinementRmsdAnglesTL':                   'gray',
                                    'RefinementMatrixWeight':                   '-'   }

        self.spider_plot_data = {   'PANDDA_site_ligand_id':                    '-',
                                    'PANDDA_site_occupancy':                    '-',
                                    'PANDDA_site_B_average':                    '-',
                                    'PANDDA_site_B_ratio_residue_surroundings': '-',
                                    'PANDDA_site_RSCC':                         '-',
                                    'PANDDA_site_rmsd':                         '-',
                                    'PANDDA_site_RSR':                          '-',
                                    'PANDDA_site_RSZD':                         '-'     }


        # default refmac parameters
        self.RefmacParams={ 'HKLIN':            '',                 'HKLOUT': '',
                            'XYZIN':            '',                 'XYZOUT': '',
                            'LIBIN':            '',                 'LIBOUT': '',
                            'TLSIN':            '',                 'TLSOUT': '',
                            'TLSADD':           '',
                            'NCYCLES':          '10',
                            'MATRIX_WEIGHT':    'AUTO',
                            'BREF':             '    bref ISOT\n',
                            'TLS':              '',
                            'NCS':              '',
                            'TWIN':             ''    }



    def StartGUI(self):

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", gtk.main_quit)
        self.window.set_border_width(10)
        self.window.set_default_size(400, 1000)
        self.window.set_title("XChemExplorer")
        self.vbox = gtk.VBox()                      # this is the main container

        #################################################################################
        # --- Sample Selection ---
#        self.vbox.add(gtk.Label('Select Samples'))

        frame = gtk.Frame(label='Select Samples')
        self.hbox_select_samples=gtk.HBox()
#        vbox=gtk.VBox()

        self.cb_select_samples = gtk.combo_box_new_text()
        self.cb_select_samples.connect("changed", self.set_selection_mode)
        for citeria in self.selection_criteria:
            self.cb_select_samples.append_text(citeria)
        self.hbox_select_samples.add(self.cb_select_samples)

        self.cb_select_sites = gtk.combo_box_new_text()
        self.cb_select_sites.connect("changed", self.set_site)
        for site in self.ligand_site_information:
            self.cb_select_sites.append_text(str(site[0])+' - '+str(site[1]))
        self.hbox_select_samples.add(self.cb_select_sites)
 #       self.hbox_select_samples.add(vbox)
        self.select_samples_button = gtk.Button(label="GO")
        self.select_samples_button.connect("clicked",self.get_samples_to_look_at)
        self.hbox_select_samples.add(self.select_samples_button)
#        self.vbox.pack_start(self.hbox_select_samples)
        frame.add(self.hbox_select_samples)
        self.vbox.pack_start(frame)

        #################################################################################
        # --- status window ---
        frame=gtk.Frame()
        self.status_label=gtk.Label()
        frame.add(self.status_label)
        self.vbox.pack_start(frame)


        # SPACER
        self.vbox.add(gtk.Label(' '))

        #################################################################################
        # --- Refinement Statistics ---
        # next comes a section which displays some global quality indicators
        # a combination of labels and textview widgets, arranged in a table

        RRfreeLabel_frame=gtk.Frame()
        self.RRfreeLabel = gtk.Label('R/Rfree')
        RRfreeLabel_frame.add(self.RRfreeLabel)
        self.RRfreeValue = gtk.Label(self.QualityIndicators['RefinementRcryst']+'/'+self.QualityIndicators['RefinementRfree'])
        RRfreeBox_frame=gtk.Frame()
        self.RRfreeBox = gtk.EventBox()
        self.RRfreeBox.add(self.RRfreeValue)
        RRfreeBox_frame.add(self.RRfreeBox)

        ResolutionLabel_frame=gtk.Frame()
        self.ResolutionLabel = gtk.Label('Resolution')
        ResolutionLabel_frame.add(self.ResolutionLabel)
        self.ResolutionValue = gtk.Label(self.QualityIndicators['RefinementResolution'])
        ResolutionBox_frame=gtk.Frame()
        self.ResolutionBox = gtk.EventBox()
        self.ResolutionBox.add(self.ResolutionValue)
        ResolutionBox_frame.add(self.ResolutionBox)

        MolprobityScoreLabel_frame=gtk.Frame()
        self.MolprobityScoreLabel = gtk.Label('MolprobityScore')
        MolprobityScoreLabel_frame.add(self.MolprobityScoreLabel)
        self.MolprobityScoreValue = gtk.Label(self.QualityIndicators['RefinementMolProbityScore'])
        MolprobityScoreBox_frame=gtk.Frame()
        self.MolprobityScoreBox = gtk.EventBox()
        self.MolprobityScoreBox.add(self.MolprobityScoreValue)
        MolprobityScoreBox_frame.add(self.MolprobityScoreBox)

        RamachandranOutliersLabel_frame=gtk.Frame()
        self.RamachandranOutliersLabel = gtk.Label('Ramachandran Outliers')
        RamachandranOutliersLabel_frame.add(self.RamachandranOutliersLabel)
        self.RamachandranOutliersValue = gtk.Label(self.QualityIndicators['RefinementRamachandranOutliers'])
        RamachandranOutliersBox_frame=gtk.Frame()
        self.RamachandranOutliersBox = gtk.EventBox()
        self.RamachandranOutliersBox.add(self.RamachandranOutliersValue)
        RamachandranOutliersBox_frame.add(self.RamachandranOutliersBox)

        RamachandranFavoredLabel_frame=gtk.Frame()
        self.RamachandranFavoredLabel = gtk.Label('Ramachandran Favored')
        RamachandranFavoredLabel_frame.add(self.RamachandranFavoredLabel)
        self.RamachandranFavoredValue = gtk.Label(self.QualityIndicators['RefinementRamachandranFavored'])
        RamachandranFavoredBox_frame=gtk.Frame()
        self.RamachandranFavoredBox = gtk.EventBox()
        self.RamachandranFavoredBox.add(self.RamachandranFavoredValue)
        RamachandranFavoredBox_frame.add(self.RamachandranFavoredBox)

        rmsdBondsLabel_frame=gtk.Frame()
        self.rmsdBondsLabel = gtk.Label('rmsd(Bonds)')
        rmsdBondsLabel_frame.add(self.rmsdBondsLabel)
        self.rmsdBondsValue = gtk.Label(self.QualityIndicators['RefinementRmsdBonds'])
        rmsdBondsBox_frame=gtk.Frame()
        self.rmsdBondsBox = gtk.EventBox()
        self.rmsdBondsBox.add(self.rmsdBondsValue)
        rmsdBondsBox_frame.add(self.rmsdBondsBox)

        rmsdAnglesLabel_frame=gtk.Frame()
        self.rmsdAnglesLabel = gtk.Label('rmsd(Angles)')
        rmsdAnglesLabel_frame.add(self.rmsdAnglesLabel)
        self.rmsdAnglesValue = gtk.Label(self.QualityIndicators['RefinementRmsdAngles'])
        rmsdAnglesBox_frame=gtk.Frame()
        self.rmsdAnglesBox = gtk.EventBox()
        self.rmsdAnglesBox.add(self.rmsdAnglesValue)
        rmsdAnglesBox_frame.add(self.rmsdAnglesBox)

        MatrixWeightLabel_frame=gtk.Frame()
        self.MatrixWeightLabel = gtk.Label('Matrix Weight')
        MatrixWeightLabel_frame.add(self.MatrixWeightLabel)
        self.MatrixWeightValue = gtk.Label(self.QualityIndicators['RefinementMatrixWeight'])
        MatrixWeightBox_frame=gtk.Frame()
        self.MatrixWeightBox = gtk.EventBox()
        self.MatrixWeightBox.add(self.MatrixWeightValue)
        MatrixWeightBox_frame.add(self.MatrixWeightBox)

        ligandIDLabel_frame=gtk.Frame()
        self.ligandIDLabel = gtk.Label('Ligand ID')
        ligandIDLabel_frame.add(self.ligandIDLabel)
        self.ligandIDValue = gtk.Label(self.spider_plot_data['PANDDA_site_ligand_id'])
        ligandIDBox_frame=gtk.Frame()
        self.ligandIDBox = gtk.EventBox()
        self.ligandIDBox.add(self.ligandIDValue)
        ligandIDBox_frame.add(self.ligandIDBox)

        ligand_occupancyLabel_frame=gtk.Frame()
        self.ligand_occupancyLabel = gtk.Label('occupancy')
        ligand_occupancyLabel_frame.add(self.ligand_occupancyLabel)
        self.ligand_occupancyValue = gtk.Label(self.spider_plot_data['PANDDA_site_occupancy'])
        ligand_occupancyBox_frame=gtk.Frame()
        self.ligand_occupancyBox = gtk.EventBox()
        self.ligand_occupancyBox.add(self.ligand_occupancyValue)
        ligand_occupancyBox_frame.add(self.ligand_occupancyBox)

        ligand_BaverageLabel_frame=gtk.Frame()
        self.ligand_BaverageLabel = gtk.Label('B average')
        ligand_BaverageLabel_frame.add(self.ligand_BaverageLabel)
        self.ligand_BaverageValue = gtk.Label(self.spider_plot_data['PANDDA_site_B_average'])
        ligand_BaverageBox_frame=gtk.Frame()
        self.ligand_BaverageBox = gtk.EventBox()
        self.ligand_BaverageBox.add(self.ligand_BaverageValue)
        ligand_BaverageBox_frame.add(self.ligand_BaverageBox)

        ligand_BratioSurroundingsLabel_frame=gtk.Frame()
        self.ligand_BratioSurroundingsLabel = gtk.Label('B ratio')
        ligand_BratioSurroundingsLabel_frame.add(self.ligand_BratioSurroundingsLabel)
        self.ligand_BratioSurroundingsValue = gtk.Label(self.spider_plot_data['PANDDA_site_B_ratio_residue_surroundings'])
        ligand_BratioSurroundingsBox_frame=gtk.Frame()
        self.ligand_BratioSurroundingsBox = gtk.EventBox()
        self.ligand_BratioSurroundingsBox.add(self.ligand_BratioSurroundingsValue)
        ligand_BratioSurroundingsBox_frame.add(self.ligand_BratioSurroundingsBox)

        ligand_RSCCLabel_frame=gtk.Frame()
        self.ligand_RSCCLabel = gtk.Label('RSCC')
        ligand_RSCCLabel_frame.add(self.ligand_RSCCLabel)
        self.ligand_RSCCValue = gtk.Label(self.spider_plot_data['PANDDA_site_RSCC'])
        ligand_RSCCBox_frame=gtk.Frame()
        self.ligand_RSCCBox = gtk.EventBox()
        self.ligand_RSCCBox.add(self.ligand_RSCCValue)
        ligand_RSCCBox_frame.add(self.ligand_RSCCBox)

        ligand_rmsdLabel_frame=gtk.Frame()
        self.ligand_rmsdLabel = gtk.Label('rmsd')
        ligand_rmsdLabel_frame.add(self.ligand_rmsdLabel)
        self.ligand_rmsdValue = gtk.Label(self.spider_plot_data['PANDDA_site_rmsd'])
        ligand_rmsdBox_frame=gtk.Frame()
        self.ligand_rmsdBox = gtk.EventBox()
        self.ligand_rmsdBox.add(self.ligand_rmsdValue)
        ligand_rmsdBox_frame.add(self.ligand_rmsdBox)

        ligand_RSRLabel_frame=gtk.Frame()
        self.ligand_RSRLabel = gtk.Label('RSR')
        ligand_RSRLabel_frame.add(self.ligand_RSRLabel)
        self.ligand_RSRValue = gtk.Label(self.spider_plot_data['PANDDA_site_RSR'])
        ligand_RSRBox_frame=gtk.Frame()
        self.ligand_RSRBox = gtk.EventBox()
        self.ligand_RSRBox.add(self.ligand_RSRValue)
        ligand_RSRBox_frame.add(self.ligand_RSRBox)

        ligand_RSZDLabel_frame=gtk.Frame()
        self.ligand_RSZDLabel = gtk.Label('RSZD')
        ligand_RSZDLabel_frame.add(self.ligand_RSZDLabel)
        self.ligand_RSZDValue = gtk.Label(self.spider_plot_data['PANDDA_site_RSZD'])
        ligand_RSZDBox_frame=gtk.Frame()
        self.ligand_RSZDBox = gtk.EventBox()
        self.ligand_RSZDBox.add(self.ligand_RSZDValue)
        ligand_RSZDBox_frame.add(self.ligand_RSZDBox)

        outer_frame = gtk.Frame()
        hbox = gtk.HBox()

        frame = gtk.Frame()
        self.table_left  = gtk.Table(8, 2, False)
        self.table_left.attach(RRfreeLabel_frame,                 0, 1, 0, 1)
        self.table_left.attach(ResolutionLabel_frame,             0, 1, 1, 2)
        self.table_left.attach(MolprobityScoreLabel_frame,        0, 1, 2, 3)
        self.table_left.attach(RamachandranOutliersLabel_frame,   0, 1, 3, 4)
        self.table_left.attach(RamachandranFavoredLabel_frame,    0, 1, 4, 5)
        self.table_left.attach(rmsdBondsLabel_frame,              0, 1, 5, 6)
        self.table_left.attach(rmsdAnglesLabel_frame,             0, 1, 6, 7)
        self.table_left.attach(MatrixWeightLabel_frame,           0, 1, 7, 8)
        self.table_left.attach(RRfreeBox_frame,                   1, 2, 0, 1)
        self.table_left.attach(ResolutionBox_frame,               1, 2, 1, 2)
        self.table_left.attach(MolprobityScoreBox_frame,          1, 2, 2, 3)
        self.table_left.attach(RamachandranOutliersBox_frame,     1, 2, 3, 4)
        self.table_left.attach(RamachandranFavoredBox_frame,      1, 2, 4, 5)
        self.table_left.attach(rmsdBondsBox_frame,                1, 2, 5, 6)
        self.table_left.attach(rmsdAnglesBox_frame,               1, 2, 6, 7)
        self.table_left.attach(MatrixWeightBox_frame,             1, 2, 7, 8)
        frame.add(self.table_left)
        hbox.add(frame)

        frame=gtk.Frame()
        self.table_right = gtk.Table(8, 2, False)
        self.table_right.attach(ligandIDLabel_frame,                   0, 1, 0, 1)
        self.table_right.attach(ligand_occupancyLabel_frame,           0, 1, 1, 2)
        self.table_right.attach(ligand_BaverageLabel_frame,            0, 1, 2, 3)
        self.table_right.attach(ligand_BratioSurroundingsLabel_frame,  0, 1, 3, 4)
        self.table_right.attach(ligand_RSCCLabel_frame,                0, 1, 4, 5)
        self.table_right.attach(ligand_rmsdLabel_frame,                0, 1, 5, 6)
        self.table_right.attach(ligand_RSRLabel_frame,                 0, 1, 6, 7)
        self.table_right.attach(ligand_RSZDLabel_frame,                0, 1, 7, 8)
        self.table_right.attach(ligandIDBox_frame,                     1, 2, 0, 1)
        self.table_right.attach(ligand_occupancyBox_frame,             1, 2, 1, 2)
        self.table_right.attach(ligand_BaverageBox_frame,              1, 2, 2, 3)
        self.table_right.attach(ligand_BratioSurroundingsBox_frame,    1, 2, 3, 4)
        self.table_right.attach(ligand_RSCCBox_frame,                  1, 2, 4, 5)
        self.table_right.attach(ligand_rmsdBox_frame,                  1, 2, 5, 6)
        self.table_right.attach(ligand_RSRBox_frame,                   1, 2, 6, 7)
        self.table_right.attach(ligand_RSZDBox_frame,                  1, 2, 7, 8)
        frame.add(self.table_right)
        hbox.add(frame)

        outer_frame.add(hbox)
        self.vbox.add(outer_frame)

        button = gtk.Button(label="Show MolProbity to-do list")
        button.connect("clicked",self.show_molprobity_to_do)
        self.vbox.add(button)
        self.vbox.pack_start(frame)


        # SPACER
        self.vbox.add(gtk.Label(' '))

        #################################################################################
        # --- hbox for compound picture & spider_plot (formerly: refinement history) ---
        frame=gtk.Frame()
        self.hbox_for_info_graphics=gtk.HBox()

        # --- compound picture ---
        compound_frame=gtk.Frame()
        pic = gtk.gdk.pixbuf_new_from_file(os.path.join(os.getenv('XChemExplorer_DIR'),'image','NO_COMPOUND_IMAGE_AVAILABLE.png'))
        self.pic = pic.scale_simple(190, 190, gtk.gdk.INTERP_BILINEAR)
        self.image = gtk.Image()
        self.image.set_from_pixbuf(self.pic)
        compound_frame.add(self.image)
        self.hbox_for_info_graphics.add(compound_frame)

        # --- Refinement History ---
#        self.canvas = FigureCanvas(self.update_plot([0],[0],[0]))
#        self.canvas.set_size_request(190, 190)
#        self.hbox_for_info_graphics.add(self.canvas)

        # --- Spider Plot ---
        spider_plot_frame=gtk.Frame()
        spider_plot_pic = gtk.gdk.pixbuf_new_from_file(os.path.join(os.getenv('XChemExplorer_DIR'),'image','NO_SPIDER_PLOT_AVAILABLE.png'))
        self.spider_plot_pic = pic.scale_simple(190, 190, gtk.gdk.INTERP_BILINEAR)
        self.spider_plot_image = gtk.Image()
        self.spider_plot_image.set_from_pixbuf(self.spider_plot_pic)
        spider_plot_frame.add(self.spider_plot_image)
        self.hbox_for_info_graphics.add(spider_plot_frame)

        frame.add(self.hbox_for_info_graphics)
        self.vbox.add(frame)

        # SPACER
        self.vbox.add(gtk.Label(' '))

        #################################################################################
        # --- crystal navigator combobox ---
        frame = gtk.Frame(label='Sample Navigator')
        self.vbox_sample_navigator=gtk.VBox()
        self.cb = gtk.combo_box_new_text()
        self.cb.connect("changed", self.ChooseXtal)
        self.vbox_sample_navigator.add(self.cb)
        # --- crystal navigator backward/forward button ---
        self.PREVbutton = gtk.Button(label="<<<")
        self.NEXTbutton = gtk.Button(label=">>>")
        self.PREVbutton.connect("clicked", self.ChangeXtal,-1)
        self.NEXTbutton.connect("clicked", self.ChangeXtal,+1)
        hbox = gtk.HBox()
        hbox.pack_start(self.PREVbutton)
        hbox.pack_start(self.NEXTbutton)
        self.vbox_sample_navigator.add(hbox)
        frame.add(self.vbox_sample_navigator)
        self.vbox.add(frame)

        # SPACER
        self.vbox.add(gtk.Label(' '))

        #################################################################################
        # --- current refinement stage ---
        outer_frame=gtk.Frame()
        hbox=gtk.HBox()

        frame = gtk.Frame(label='Analysis Status')
        vbox=gtk.VBox()
        self.experiment_stage_button_list=[]
        for n,button in enumerate(self.experiment_stage):
            if n == 0:
                new_button = gtk.RadioButton(None, button[0])
            else:
                new_button = gtk.RadioButton(new_button, button[0])
            new_button.connect("toggled",self.experiment_stage_button_clicked,button[1])
            vbox.add(new_button)
            self.experiment_stage_button_list.append(new_button)
        frame.add(vbox)
        hbox.pack_start(frame)

        # --- ligand confidence ---
        frame = gtk.Frame(label='Ligand Confidence')
        vbox=gtk.VBox()
        self.ligand_confidence_button_list=[]
        for n,criteria in enumerate(self.ligand_confidence_category):
            if n == 0:
                new_button = gtk.RadioButton(None, criteria)
            else:
                new_button = gtk.RadioButton(new_button, criteria)
            new_button.connect("toggled",self.ligand_confidence_button_clicked,citeria)
            vbox.add(new_button)
            self.ligand_confidence_button_list.append(new_button)
        frame.add(vbox)
        hbox.pack_start(frame)

        outer_frame.add(hbox)
        self.vbox.pack_start(outer_frame)

        # SPACER
        self.vbox.add(gtk.Label(' '))

        # --- ligand modeling ---
        frame = gtk.Frame(label='Ligand Modeling')
        self.hbox_for_modeling=gtk.HBox()
        self.merge_ligand_button=gtk.Button(label="Merge Ligand")
        self.place_ligand_here_button=gtk.Button(label="Place Ligand here")
        self.hbox_for_modeling.add(self.place_ligand_here_button)
        self.place_ligand_here_button.connect("clicked",self.place_ligand_here)
        self.hbox_for_modeling.add(self.merge_ligand_button)
        self.merge_ligand_button.connect("clicked",self.merge_ligand_into_protein)
        frame.add(self.hbox_for_modeling)
        self.vbox.pack_start(frame)


#        # --- ligand confidence ---
#        self.cb_ligand_confidence = gtk.combo_box_new_text()
#        self.cb_ligand_confidence.connect("changed", self.set_ligand_confidence)
#        for citeria in self.ligand_confidence:
#            self.cb_ligand_confidence.append_text(citeria)
#        self.vbox.add(self.cb_ligand_confidence)


        # --- refinement & options ---
        self.hbox_for_refinement=gtk.HBox()
        self.REFINEbutton = gtk.Button(label="Refine")
        self.RefinementParamsButton = gtk.Button(label="refinement parameters")
        self.REFINEbutton.connect("clicked",self.REFINE)
        self.hbox_for_refinement.add(self.REFINEbutton)
        self.RefinementParamsButton.connect("clicked",self.RefinementParams)
        self.hbox_for_refinement.add(self.RefinementParamsButton)
        self.vbox.add(self.hbox_for_refinement)

#        self.VALIDATEbutton = gtk.Button(label="validate structure")
#        self.DEPOSITbutton = gtk.Button(label="prepare for deposition")


        # --- CANCEL button ---
        self.CANCELbutton = gtk.Button(label="CANCEL")
        self.CANCELbutton.connect("clicked", self.CANCEL)
        self.vbox.add(self.CANCELbutton)

        self.window.add(self.vbox)
        self.window.show_all()

    def CANCEL(self,widget):
        self.window.destroy()


    def ChangeXtal(self,widget,data=None):
        self.index = self.index + data
        if self.index < 0:
            self.index = 0
        if self.index >= len(self.Todo):
            self.index = len(self.Todo)
        self.cb.set_active(self.index)

    def ChooseXtal(self, widget):
        self.xtalID = str(widget.get_active_text())
        for n,item in enumerate(self.Todo):
            if str(item[0]) == self.xtalID:
                self.index = n

        self.db_dict_mainTable={}
        self.db_dict_panddaTable={}
        if str(self.Todo[self.index][0]) != None:
            self.compoundID=str(self.Todo[self.index][1])
            self.refinement_folder=str(self.Todo[self.index][4])
            self.refinement_outcome=str(self.Todo[self.index][5])
            self.ligand_confidence=str(self.Todo[self.index][6])
            # updating dataset outcome radiobuttons
            current_stage=0
            for i,entry in enumerate(self.experiment_stage):
                if entry[1]==self.refinement_outcome:
                    current_stage=i
                    break
            for i,button in enumerate(self.experiment_stage_button_list):
                if i==current_stage:
                    button.set_active(True)
                    break
            # updating ligand confidence radiobuttons
            current_stage=0
            for i,entry in enumerate(self.ligand_confidence_category):
                if entry==self.ligand_confidence:
                    current_stage=i
                    break
            for i,button in enumerate(self.ligand_confidence_button_list):
                if i==current_stage:
                    button.set_active(True)
                    break
            if self.selected_site[0] > 0:
                pandda_info=self.db.get_pandda_info_for_coot(self.xtalID,self.selected_site[0])
                self.event_map=str(self.Todo[self.index][0])
                coot.set_rotation_centre(float(self.Todo[self.index][1]),float(self.Todo[self.index][2]),float(self.Todo[self.index][3]))
                self.spider_plot=pandda_info[4]
            else:
                self.event_map=''
                self.spider_plot=''
        self.RefreshData()


# this works, but will try something else
#    def ChooseXtal(self, widget):
#        self.xtalID = str(widget.get_active_text())
#        for n,item in enumerate(self.Todo):
#            if str(item[0]) == self.xtalID:
#                self.index = n
#        self.xtalID=str(self.Todo[self.index][0])
#        self.db_dict_mainTable={}
#        self.db_dict_panddaTable={}
#        looking_at_pandda_models=False
#        if str(self.Todo[self.index][0]) != None:
#            self.compoundID=str(self.Todo[self.index][1])
#            self.refinement_folder=str(self.Todo[self.index][4])
#            self.refinement_outcome=str(self.Todo[self.index][5])
#            current_stage=0
#            for i,entry in enumerate(self.experiment_stage):
#                if entry[1]==self.refinement_outcome:
#                    current_stage=i
#                    break
#            for i,button in enumerate(self.experiment_stage_button_list):
#                if i==current_stage:
#                    button.set_active(True)
#                    break
#            if len(self.Todo[self.index]) > 6:
#                self.ligand_confidence_of_sample=str(self.Todo[self.index][7])
#                self.event_map=str(self.Todo[self.index][6])
#                coot.set_rotation_centre(float(self.Todo[self.index][8]),float(self.Todo[self.index][9]),float(self.Todo[self.index][10]))
#                looking_at_pandda_models=True
#        if not looking_at_pandda_models:
#            self.compoundID=''
#            self.ligand_confidence_of_sample=''
#            self.refinement_folder=''
#            self.event_map=''
#        self.RefreshData()



    def update_data_source(self,widget,data=None):              # update and move to next xtal
#        outcome_dict={'RefinementOutcome': data}
#        self.db.update_data_source(self.xtalID,outcome_dict)
        self.index+=1
        if self.index >= len(self.Todo):
            self.index = len(self.Todo)
        self.cb.set_active(self.index)


    def experiment_stage_button_clicked(self,widget, data=None):
        if self.selected_site[0] == 0:
            self.db_dict_mainTable['RefinementOutcome']=data
            print '==> XCE: setting Refinement Outcome for '+self.xtalID+' to '+str(data)+' in mainTable of datasource'
            self.db.update_data_source(self.xtalID,self.db_dict_mainTable)
        else:
            self.db_dict_panddaTable['RefinementOutcome']=data
            print '==> XCE: setting Refinement Outcome for '+self.xtalID+' (site='+str(self.selected_site)+') to '+str(data)+' in panddaTable of datasource'
            self.db.update_panddaTable(self.xtalID,self.selected_site[0],self.db_dict_panddaTable)

    def ligand_confidence_button_clicked(self,widget, data=None):
        if self.selected_site[0] == 0:
            self.db_dict_mainTable['RefinementLigandConfidence']=data
            print '==> XCE: setting Ligand Confidence for '+self.xtalID+' to '+str(data)+' in mainTable of datasource'
            self.db.update_data_source(self.xtalID,self.db_dict_mainTable)
        else:
            self.db_dict_panddaTable['PANDDA_site_confidence']=data
            print '==> XCE: setting Ligand Confidence for '+self.xtalID+' (site='+str(self.selected_site)+') to '+str(data)+' in panddaTable of datasource'
            self.db.update_panddaTable(self.xtalID,self.selected_site[0],self.db_dict_panddaTable)


    def RefreshData(self):
        # initialize Refinement library
        self.Refine=XChemRefine.Refine(self.project_directory,self.xtalID,self.compoundID,self.data_source)
        self.Serial=self.Refine.GetSerial()

#        self.QualityIndicators=XChemUtils.ParseFiles(self.project_directory,self.xtalID).UpdateQualityIndicators()
        # all this information is now updated in the datasource after each refinement cycle
        self.QualityIndicators=self.db.get_db_dict_for_sample(self.xtalID)
        if self.selected_site[0] > 0:
            self.spider_plot_data=self.db.get_db_pandda_dict_for_sample_and_site(self.xtalID,self.selected_site[0])
            self.ligandIDValue.set_label(self.spider_plot_data['PANDDA_site_ligand_id'])
            self.ligand_occupancyValue.set_label(self.spider_plot_data['PANDDA_site_occupancy'])
            self.ligand_BaverageValue.set_label(self.spider_plot_data['PANDDA_site_B_average'])
            self.ligand_BratioSurroundingsValue.set_label(self.spider_plot_data['PANDDA_site_B_ratio_residue_surroundings'])
            self.ligand_RSCCValue.set_label(self.spider_plot_data['PANDDA_site_RSCC'])
            self.ligand_rmsdValue.set_label(self.spider_plot_data['PANDDA_site_rmsd'])
            self.ligand_RSRValue.set_label(self.spider_plot_data['PANDDA_site_RSR'])
            self.ligand_RSZDValue.set_label(self.spider_plot_data['PANDDA_site_RSZD'])


        #########################################################################################
        # history
        # if the structure was previously refined, try to read the parameters
#        self.hbox_for_info_graphics.remove(self.canvas)
        if self.Serial > 1:
            self.RefmacParams=self.Refine.ParamsFromPreviousCycle(self.Serial-1)
            refinement_cycle,Rfree,Rcryst=self.Refine.GetRefinementHistory()
#            self.canvas = FigureCanvas(self.update_plot(refinement_cycle,Rfree,Rcryst))
#        else:
#            self.canvas = FigureCanvas(self.update_plot([0],[0],[0]))  # a gtk.DrawingArea
#        self.canvas.set_size_request(190, 190)
#        self.hbox_for_info_graphics.add(self.canvas)
#        self.canvas.show()

        #########################################################################################
        # Spider plot
        # Note: refinement history was shown instead previously
        if os.path.isfile(self.spider_plot):
            spider_plot_pic = gtk.gdk.pixbuf_new_from_file(self.spider_plot)
        else:
            spider_plot_pic = gtk.gdk.pixbuf_new_from_file(os.path.join(os.getenv('XChemExplorer_DIR'),'image','NO_SPIDER_PLOT_AVAILABLE.png'))
        self.spider_plot_pic = spider_plot_pic.scale_simple(190, 190, gtk.gdk.INTERP_BILINEAR)
        self.spider_plot_image.set_from_pixbuf(self.spider_plot_pic)

        #########################################################################################
        # update pdb & maps

        #########################################################################################
        # delete old PDB and MAP files
        # - get a list of all molecules which are currently opened in COOT
        # - remove all molecules/ maps before loading a new set
        if len(coot_utils_XChem.molecule_number_list()) > 0:
            for item in coot_utils_XChem.molecule_number_list():
                coot.close_molecule(item)

        #########################################################################################
        # read new PDB files
        # read protein molecule after ligand so that this one is the active molecule
        coot.set_nomenclature_errors_on_read("ignore")
        if os.path.isfile(os.path.join(self.project_directory,self.xtalID,self.compoundID+'.pdb')):
            imol=coot.handle_read_draw_molecule_with_recentre(os.path.join(self.project_directory,self.xtalID,self.compoundID+'.pdb'),0)
            self.mol_dict['ligand']=imol
            coot.read_cif_dictionary(os.path.join(self.project_directory,self.xtalID,self.compoundID+'.cif'))
        if not os.path.isfile(os.path.join(self.project_directory,self.xtalID,self.pdb_style)):
            os.chdir(os.path.join(self.project_directory,self.xtalID))
            if os.path.isfile(os.path.join(self.project_directory,self.xtalID,self.xtalID+'-pandda-model.pdb')):
                os.symlink(self.xtalID+'-pandda-model.pdb',self.pdb_style)
            elif os.path.isfile(os.path.join(self.project_directory,self.xtalID,'dimple.pdb')):
                os.symlink('dimple.pdb',self.pdb_style)
            else:
                self.go_to_next_xtal()
        imol=coot.handle_read_draw_molecule_with_recentre(os.path.join(self.project_directory,self.xtalID,self.pdb_style),0)
        self.mol_dict['protein']=imol
        for item in coot_utils_XChem.molecule_number_list():
            if coot.molecule_name(item).endswith(self.pdb_style):
                coot.set_show_symmetry_master(1)    # master switch to show symmetry molecules
                coot.set_show_symmetry_molecule(item,1) # show symm for model

        #########################################################################################
        # check for PANDDAs EVENT maps
#        for map in glob.glob(os.path.join(self.project_directory,self.xtalID,'*')):
#            if 'event' in str(map) and '.ccp4' in str(map):
#                occupancy=map[map.find('occupancy')+10:map.rfind('_')]
#                coot.handle_read_ccp4_map((map),0)
#                for imol in coot_utils_XChem.molecule_number_list():
#                    if map in coot.molecule_name(imol):
#                        coot.set_contour_level_absolute(imol,float(occupancy))
#                        coot.set_last_map_colour(0.4,0,0.4)
        if os.path.isfile(self.event_map):
            coot.handle_read_ccp4_map((self.event_map),0)
            for imol in coot_utils_XChem.molecule_number_list():
                if self.event_map in coot.molecule_name(imol):
                    coot.set_contour_level_absolute(imol,0.5)
                    coot.set_last_map_colour(0.4,0,0.4)


        #########################################################################################
        # read fofo maps
        # - read ccp4 map: 0 - 2fofc map, 1 - fofc.map
        # read 2fofc map last so that one can change its contour level
        if os.path.isfile(os.path.join(self.project_directory,self.xtalID,'2fofc.map')):
            coot.set_default_initial_contour_level_for_difference_map(3)
            coot.handle_read_ccp4_map(os.path.join(self.project_directory,self.xtalID,'fofc.map'),1)
            coot.set_default_initial_contour_level_for_map(1)
            coot.handle_read_ccp4_map(os.path.join(self.project_directory,self.xtalID,'2fofc.map'),0)
            coot.set_last_map_colour(0,0,1)
        else:
            # try to open mtz file with same name as pdb file
            coot.set_default_initial_contour_level_for_map(1)
            if not os.path.isfile(os.path.join(self.project_directory,self.xtalID,self.mtz_style)):
                os.chdir(os.path.join(self.project_directory,self.xtalID))
                if os.path.isfile(os.path.join(self.project_directory,self.xtalID,self.xtalID+'-pandda-input.mtz')):
                    os.symlink(self.xtalID+'-pandda-input.mtz',self.mtz_style)
                elif os.path.isfile(os.path.join(self.project_directory,self.xtalID,'dimple.mtz')):
                    os.symlink('dimple.mtz',self.mtz_style)
            coot.auto_read_make_and_draw_maps(os.path.join(self.project_directory,self.xtalID,self.mtz_style))

        #########################################################################################
        # update Ligand Confidence combobox
        if str(self.ligand_confidence_of_sample)=='None':
            self.ligand_confidence_of_sample='Analysis Pending'
            db_dict={'RefinementLigandConfidence': self.ligand_confidence_of_sample}
#            self.db.update_data_source(self.xtalID,db_dict)
        for n,criteria in enumerate(self.ligand_confidence):
            if criteria.replace('Ligand Confidence: ','')==self.ligand_confidence_of_sample:
                self.cb_ligand_confidence.set_active(n)

        #########################################################################################
        # update Quality Indicator table
        self.RRfreeValue.set_label(self.QualityIndicators['RefinementRcryst']+' / '+self.QualityIndicators['RefinementRfree'])
        self.RRfreeBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.QualityIndicators['RefinementRfreeTraficLight']))
        self.ResolutionValue.set_label(self.QualityIndicators['RefinementResolution'])
        self.ResolutionBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.QualityIndicators['RefinementResolutionTL']))
        self.MolprobityScoreValue.set_label(self.QualityIndicators['RefinementMolProbityScore'])
        self.MolprobityScoreBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.QualityIndicators['RefinementMolProbityScoreTL']))
        self.RamachandranOutliersValue.set_label(self.QualityIndicators['RefinementRamachandranOutliers'])
        self.RamachandranOutliersBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.QualityIndicators['RefinementRamachandranOutliersTL']))
        self.RamachandranFavoredValue.set_label(self.QualityIndicators['RefinementRamachandranFavored'])
        self.RamachandranFavoredBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.QualityIndicators['RefinementRamachandranFavoredTL']))
        self.rmsdBondsValue.set_label(self.QualityIndicators['RefinementRmsdBonds'])
        self.rmsdBondsBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.QualityIndicators['RefinementRmsdBondsTL']))
        self.rmsdAnglesValue.set_label(self.QualityIndicators['RefinementRmsdAngles'])
        self.rmsdAnglesBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.QualityIndicators['RefinementRmsdAnglesTL']))
        self.MatrixWeightValue.set_label(self.QualityIndicators['RefinementMatrixWeight'])

        try:
            pic = gtk.gdk.pixbuf_new_from_file(os.path.join(self.project_directory,self.xtalID,self.compoundID+'.png'))
        except gobject.GError:
            pic = gtk.gdk.pixbuf_new_from_file(os.path.join(os.getenv('XChemExplorer_DIR'),'image','NO_COMPOUND_IMAGE_AVAILABLE.png'))
        self.pic = pic.scale_simple(190, 190, gtk.gdk.INTERP_BILINEAR)
        self.image.set_from_pixbuf(self.pic)

    def go_to_next_xtal(self):
        self.index+=1
        if self.index >= len(self.Todo):
            self.index = len(self.Todo)
        self.cb.set_active(self.index)


    def REFINE(self,widget):

        #######################################################
        # create folder for new refinement cycle
        os.mkdir(os.path.join(self.project_directory,self.xtalID,'Refine_'+str(self.Serial)))

        #######################################################
        # write PDB file
        # now take protein pdb file and write it to newly create Refine_<serial> folder
        # note: the user has to make sure that the ligand file was merged into main file
        for item in coot_utils_XChem.molecule_number_list():
            if coot.molecule_name(item).endswith(self.pdb_style):
                coot.write_pdb_file(item,os.path.join(self.project_directory,self.xtalID,'Refine_'+str(self.Serial),'in.pdb'))

        #######################################################
        # run REFMAC
        self.Refine.RunRefmac(self.Serial,self.RefmacParams,self.external_software)

        self.index+=1
        if self.index >= len(self.Todo):
            self.index = len(self.Todo)
        self.cb.set_active(self.index)


    def RefinementParams(self,widget):
        print '\n==> XCE: changing refinement parameters'
        self.RefmacParams=self.Refine.RefinementParams(self.RefmacParams)

    def set_selection_mode(self,widget):
        self.selection_mode=widget.get_active_text()
#        for criteria in self.selection_criteria:
#            if criteria==widget.get_active_text():
#                self.selection_mode=self.selection_criteria[criteria]
#                break

    def set_site(self,widget):
        for site in self.ligand_site_information:
            if str(site[0])==str(widget.get_active_text()).split()[0]:
                self.selected_site=site
                break

    def set_ligand_confidence(self,widget):
        self.ligand_confidence_of_sample=widget.get_active_text().replace('Ligand Confidence: ','')
        print '===> XCE: updating data source with new ligand confidence ',self.ligand_confidence_of_sample
        db_dict={'RefinementLigandConfidence': self.ligand_confidence_of_sample}
#        self.db.update_data_source(self.xtalID,db_dict)
        self.Todo[self.index][2]=self.ligand_confidence_of_sample


    def get_samples_to_look_at(self,widget):
        self.status_label.set_text('checking datasource for samples... ')
#        x=float(self.selected_site[2])
#        y=float(self.selected_site[3])
#        z=float(self.selected_site[4])
#        coot.set_rotation_centre(x,y,z)
        # first remove old samples if present
        if len(self.Todo) != 0:
            for n,item in enumerate(self.Todo):
                self.cb.remove_text(0)
        self.Todo=[]
        self.Todo=self.db.get_todo_list_for_coot(self.selection_mode,self.selected_site[0])
        self.status_label.set_text('found %s samples' %len(self.Todo))
        for item in self.Todo:
            self.cb.append_text('%s' %item[0])



    def update_plot(self,refinement_cycle,Rfree,Rcryst):
        fig = Figure(figsize=(2, 2), dpi=50)
        Plot = fig.add_subplot(111)
        Plot.set_ylim([0,max(Rcryst+Rfree)])
        Plot.set_xlabel('Refinement Cycle',fontsize=12)
        Plot.plot(refinement_cycle,Rfree,label='Rfree',linewidth=2)
        Plot.plot(refinement_cycle,Rcryst,label='Rcryst',linewidth=2)
        Plot.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
                ncol=2, mode="expand", borderaxespad=0.,fontsize=12)
        return fig

    def place_ligand_here(self,widget):
        print '===> XCE: moving ligand to pointer'
#        coot.move_molecule_here(<molecule_number>)
        print 'LIGAND: ',self.mol_dict['ligand']
        coot_utils_XChem.move_molecule_here(self.mol_dict['ligand'])

    def merge_ligand_into_protein(self,widget):
        print '===> XCE: merge ligand into protein structure'
        # merge_molecules(list(imols), imol) e.g. merge_molecules([1],0)
        coot.merge_molecules_py([self.mol_dict['ligand']],self.mol_dict['protein'])
        print '===> XCE: deleting ligand molecule'
        coot.close_molecule(self.mol_dict['ligand'])

    def show_molprobity_to_do(self,widget):
        if os.path.isfile(os.path.join(self.project_directory,self.xtalID,'Refine_'+str(self.Serial-1),'molprobity_coot.py')):
            print '==> XCE: running MolProbity Summary for',self.xtalID
            coot.run_script(os.path.join(self.project_directory,self.xtalID,'Refine_'+str(self.Serial-1),'molprobity_coot.py'))
        else:
            print '==> XCE: cannot find '+os.path.join(self.project_directory,self.xtalID,'Refine_'+str(self.Serial-1),'molprobity_coot.py')

#    def fit_ligand(self,widget):
#        print 'fit'

if __name__=='__main__':
    GUI().StartGUI()