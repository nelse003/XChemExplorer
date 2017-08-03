# last edited: 03/08/2017, 15:00

import os,sys
sys.path.append(os.path.join(os.getenv('XChemExplorer_DIR'),'lib'))



# - select datasets with highest resolution
# - select only those without an event map
# - take the one with the lowest Rfree


def find_highest_resolution_datasets(panddaDir):
    found=False
    datasetList=[]
    for logFile in glob.glob(os.path.join(panddaDir,'logs','*.log')):
        for n,line in enumerate(open(logFile)):
            if line.startswith('Statistical Electron Density Characterisation') and len(line.split()) == 6:
                resolution=line.split()[5]
                found=True
                foundLine=n
            if found and n>=foundLine+3:
                if line.startswith('Statistical Electron Density Characterisation'):
                    break
                else:
                    datasetList.append(line.split(',')[0].replace(' ','').replace('\t',''))
    print datasetList


if __name__=='__main__':
    panddaDir=sys.argv[1]

