# this script makes synthetic interferograms only containing the phase bias calculated in the field_loop.ipynb notebook

import os, glob
import shutil
import math
from osgeo import gdal
import pandas as pd
import numpy as np
import time

start = time.time()
print('start')

# path to directory with SLCs
datadir = 'path/to/your/datadir'
# path to directory with dataframes, if different from datadir
statdir = 'path/to/your/statdir'
os.chdir(f'{datadir}/synth_ifgs')
driver=gdal.GetDriverByName('ISCE')

# size of entire SLC
az0 = 0
daz= 3500
rg0 = 0
drg = 30000

dates = [os.path.basename(x) for x in glob.glob(f'{datadir}/VV/merged/SLC/2*')]
dates = sorted(dates)
nd = len(dates)

# read in field IDs
ds = gdal.Open(f'{datadir}/fieldccarray.r4', gdal.GA_ReadOnly)
allfieldccarray = ds.ReadAsArray()

nf = int(np.max(allfieldccarray)) # number of fields

# load in dataframes
roadpixel_df = pd.read_pickle(f'{statdir}dataframes/roadpixel_df.pkl')
fieldpixel_df = pd.read_pickle(f'{statdir}dataframes/fieldpixel_df.pkl')
roadn_df = pd.read_pickle(f'{statdir}dataframes/roadn_df.pkl')
fieldn_df = pd.read_pickle(f'{statdir}dataframes/fieldn_df.pkl')
roadphs_df = pd.read_pickle(f'{statdir}dataframes/roadphs_df.pkl')
fieldphs_df = pd.read_pickle(f'{statdir}dataframes/fieldphs_df.pkl')
diffphs_df = pd.read_pickle(f'{statdir}dataframes/diffphs_df.pkl')
roadskew_df = pd.read_pickle(f'{statdir}dataframes/roadskew_df.pkl')
fieldskew_df = pd.read_pickle(f'{statdir}dataframes/fieldskew_df.pkl')
roadvar_df = pd.read_pickle(f'{statdir}dataframes/roadvar_df.pkl')
fieldvar_df = pd.read_pickle(f'{statdir}dataframes/fieldvar_df.pkl')
diffstd_df = pd.read_pickle(f'{statdir}dataframes/diffstd_df.pkl')

# create synthetic interferograms
for k in range(nd-1):
    print('intitialize '+str(k))

    # initialize gaussian array
    rand = np.exp(1j*np.random.normal(size=(daz,drg)))

    # this assumes you have separate coherence files on the same grid as your SLCs
    coh = np.ndarray([daz,drg])
    ds = gdal.Open(f'{datadir}/coherence/fullres/{dates[k]}_{dates[k+1]}/fr_coh.r4', gdal.GA_ReadOnly)
    coh[:,:] = ds.GetRasterBand(1).ReadAsArray(rg0,az0,drg,daz)

    std = np.sqrt((-2*np.log(coh))) # convert coherence to std dev

    allfieldbias = np.zeros([daz,drg])

    for f in np.arange(1,nf+1):
        fieldarray = np.zeros([daz,drg])
        fieldarray[allfieldccarray==f] = 1
        
        #  # no bias if too decorrelated
        if math.isnan(diffphs_df[f'field_{f}'][k]):
            fieldbias = 0
        # elif (roadn_df[f'field_{f}'][k]/roadpixel_df[f'field_{f}'][0]) < .1:
        #     fieldbias = 0
        # elif (fieldn_df[f'field_{f}'][k]/fieldpixel_df[f'field_{f}'][0]) < .1:
        #     fieldbias = 0    
        # # assign bias
        else:
            fieldbias = np.exp(1j*diffphs_df[f'field_{f}'][k])*fieldarray

        allfieldbias = allfieldbias+fieldbias
    
    synth = rand*std+allfieldbias

    # write to temp full res file
    print('write to temp')
    colds = driver.Create('temp.int',drg,daz,1,gdal.GDT_CFloat32)
    colds.GetRasterBand(1).WriteArray(synth)
    colds=None

    # create vrt file for temp
    print('create vrt')
    cmd = 'fixImageXml.py -i temp.int -f'
    os.system(cmd)

    # downlook
    print('downlook')
    cmd = 'looks.py -i temp.int -o tempdl.int -r 19 -a 7'
    os.system(cmd)

    # filter and coherence
    print('filter and coherence')
    cmd = 'FilterAndCoherence.py -i tempdl.int -f filt_tempdl.int -s .1'
    os.system(cmd)

    # unwrap
    print('unwrap')
    # make dir if doesn't exist
    if not os.path.isdir(f'{datadir}/synth_ifgs/{dates[k]}_{dates[k+1]}'):
        os.mkdir(f'{datadir}/synth_{dates[k]}_{dates[k+1]}')
    cmd = f'unwrap.py -i filt_tempdl.int -u {datadir}/synth_ifgs/{dates[k]}_{dates[k+1]}/{dates[k]}_{dates[k+1]}.unw'
    os.system(cmd)

    cmd = f'fixImageXml.py -i {datadir}/synth_ifgs/{dates[k]}_{dates[k+1]}/{dates[k]}_{dates[k+1]}.unw -f'
    os.system(cmd)

    # move conncomp
    shutil.move('filt_tempdl.conncomp',f'{datadir}/synth_ifgs/{dates[k]}_{dates[k+1]}/{dates[k]}_{dates[k+1]}.unw.conncomp')
    shutil.move('filt_tempdl.conncomp.xml',f'{datadir}/synth_ifgs/{dates[k]}_{dates[k+1]}/{dates[k]}_{dates[k+1]}.unw.conncomp.xml')
    shutil.move('filt_tempdl.conncomp.vrt',f'{datadir}/synth_ifgs/{dates[k]}_{dates[k+1]}/{dates[k]}_{dates[k+1]}.unw.conncomp.vrt')

    print(str(k)+' done')

end = time.time()
print((end - start)/60)