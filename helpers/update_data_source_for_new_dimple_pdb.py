# last edited: 15/11/2016, 15:00

import os,sys
sys.path.append(os.path.join(os.getenv('XChemExplorer_DIR'),'lib'))
import glob

from iotbx import mtz

from XChemUtils import parse
import XChemDB

if __name__=='__main__':
    db_file=sys.argv[1]
    xtal=sys.argv[2]
    inital_model_directory=sys.argv[3]

    db=XChemDB.data_source(db_file)
    if os.path.isfile(os.path.join(inital_model_directory,xtal,'dimple.pdb')):
        db_dict={}
        db_dict['DimplePathToPDB']=os.path.join(inital_model_directory,xtal,'dimple.pdb')
        dimple_ran_successfully=False
        if os.path.isfile(os.path.join(inital_model_directory,xtal,'dimple.mtz')):
            db_dict['DimplePathToMTZ']=os.path.join(inital_model_directory,xtal,'dimple.mtz')
            dimple_ran_successfully=True
            db_dict['DataProcessingDimpleSuccessful']='True'
            db_dict['DimpleStatus'] = 'finished'
        if not dimple_ran_successfully:
            db_dict['DataProcessingDimpleSuccessful']='False'
            db_dict['DimpleStatus'] = 'failed'
        pdb=parse().PDBheader(os.path.join(inital_model_directory,xtal,'dimple.pdb'))
        db_dict['DimpleRcryst']=pdb['Rcryst']
        db_dict['DimpleRfree']=pdb['Rfree']
        db_dict['RefinementOutcome']='1 - Analysis Pending'
        db_dict['RefinementSpaceGroup']=pdb['SpaceGroup']
#        if not os.path.isfile(xtal+'.free.mtz'):
#            os.chdir(os.path.join(inital_model_directory,xtal))
#            os.system('/bin/rm '+xtal+'.free.mtz')
#            if os.path.isfile(os.path.join(inital_model_directory,xtal,'dimple','dimple_rerun_on_selected_file','dimple','prepared2.mtz')):
#                os.symlink(os.path.join('dimple','dimple_rerun_on_selected_file','dimple','prepared2.mtz'),xtal+'.free.mtz')
#                db_dict['RefinementMTZfree']=xtal+'.free.mtz'
#            elif os.path.isfile(os.path.join(inital_model_directory,xtal,'dimple','dimple_rerun_on_selected_file','dimple','prepared.mtz')):
#                os.symlink(os.path.join('dimple','dimple_rerun_on_selected_file','dimple','prepared.mtz'),xtal+'.free.mtz')
#                db_dict['RefinementMTZfree']=xtal+'.free.mtz'

        # setting free.mtz file

        os.chdir(os.path.join(inital_model_directory,xtal))
        os.system('/bin/rm -f %s.free.mtz' %xtal)
        mtzFree = None
        db_dict['RefinementMTZfree'] = ''
        if os.path.isfile(os.path.join(inital_model_directory,xtal,'dimple','dimple_rerun_on_selected_file','dimple','prepared2.mtz')):
            mtzFree = os.path.join(inital_model_directory,xtal,'dimple','dimple_rerun_on_selected_file','dimple','prepared2.mtz')
        elif os.path.isfile(os.path.join(inital_model_directory,xtal,'dimple','dimple_rerun_on_selected_file','dimple','prepared.mtz')):
            mtzFree = os.path.join(inital_model_directory,xtal,'dimple','dimple_rerun_on_selected_file','dimple','prepared.mtz')
        
        if mtzFree is not None:
            if 'F_unique' in mtz.object(mtzFree).column_labels():
                cmd = ( 'cad hklin1 %s hklout %s.free.mtz << eof\n' %(mtzFree,xtal) +
                        ' monitor BRIEF\n'
                        ' labin file 1 E1=F E2=SIGF E3=FreeR_flag\n'
                        ' labout file 1 E1=F E2=SIGF E3=FreeR_flag\n'
                        'eof\n' )

                os.system(cmd)
            else:
                os.symlink(mtzFree,xtal+'.free.mtz')

            db_dict['RefinementMTZfree']=xtal+'.free.mtz'




        # if no refinement was carried out yet, then we also want to link the dimple files to refine.pdb/refine.log
        # so that we can look at them with the COOT plugin
        # 15/11/2016: obsolete since COOT will now read dimple.pdb/dimple.mtz if no refine.pdb/refine.mtz is present
#        found_previous_refinement=False
#        os.chdir(os.path.join(inital_model_directory,xtal))
#        for dirs in glob.glob('*'):
#            if os.path.isdir(dirs) and dirs.startswith('Refine_'):
#                found_previous_refinement=True
#                break
#        if not found_previous_refinement:
#            # first delete possible old symbolic links
#            if os.path.isfile('refine.pdb'): os.system('/bin/rm refine.pdb')
#            os.symlink('dimple.pdb','refine.pdb')
#            if os.path.isfile('refine.mtz'): os.system('/bin/rm refine.mtz')
#            os.symlink('dimple.mtz','refine.mtz')

        # finally, update data source
        print '==> xce: updating data source after DIMPLE run'
        db.update_data_source(xtal,db_dict)

    else:
        # the actual dimple script creates symbolic links regardless if dimple was successful or not
        # python os.path.isfile is False if symbolic link points to non existing file
        # so we remove all of them!
        os.chdir(os.path.join(inital_model_directory,xtal))
        os.system('/bin/rm dimple.pdb')
        os.system('/bin/rm dimple.mtz')
        os.system('/bin/rm 2fofc.map')
        os.system('/bin/rm fofc.map')
