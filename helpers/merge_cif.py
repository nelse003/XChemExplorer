import os,glob
pD = '/dls/labxchem/data/2017/lb18145-17/processing/analysis/initial_model'
cif = '/dls/labxchem/data/2017/lb18145-17/processing/reference/XX02KALRNA-Rac1-Dk-2-reference.cif'
for y in glob.glob(os.path.join(pD,'*')):
    try:    
        xtal_num = int(y.split('-x')[1])
    except IndexError:
        continue
    except ValueError:
        continue
    if int(xtal_num) > 1613:
        x=y[y.rfind('/')+1:]
        os.chdir(y)
        for c in glob.glob('*.cif'):
            if not os.path.isfile('LIG.cif'):
                os.system('/bin/cp %s LIG.cif' %c)
            	cmd = (
                        '#!/bin/bash\n'
                        '\n'
                        '$CCP4/bin/libcheck << eof \n'
                        '_Y\n'
                        '_FILE_L LIG.cif\n'
                        '_FILE_L2 '+cif+'\n'
                        '_FILE_O '+c+'\n'
                        '_END\n'
                        'eof\n'
                        )
             	print cmd
             	os.system(cmd)
        for l in glob.glob('*.lib'):
            if l.startswith('Z'):
                v = l[:l.rfind('.lib')]
                print '/bin/cp %s %s' %(l,v)
                os.system('/bin/mv %s %s' %(l,v))
                print v
