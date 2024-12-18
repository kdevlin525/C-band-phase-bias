# This script downlooks, filters, and unwraps SLCs to create sequential interferograms

import os, glob
import shutil
import math
from osgeo import gdal
#import pandas as pd
import numpy as np

datadir = 'path/to/your/dir'
# switch into folder where unwrapped interferograms will be stored
os.chdir(f'{datadir}/unw_ifgs')
driver=gdal.GetDriverByName('ISCE')

# size of entire SLC
az0 = 0
daz= 3500
rg0 = 0
drg = 30000

# number of looks
rlks = 19
alks = 7

dates = [os.path.basename(x) for x in glob.glob(f'{datadir}/SLC_vv/2*')]
dates = sorted(dates)
dates = dates[128:]
nd = len(dates)

slc1 = np.ndarray([daz,drg],'complex')
slc2 = np.ndarray([daz,drg],'complex')

for k in np.arange(nd-1): 
    ds1 = gdal.Open(f'{datadir}/SLC_vv/{dates[k]}/{dates[k]}.slc.full', gdal.GA_ReadOnly)
    ds2 = gdal.Open(f'{datadir}/SLC_vv/{dates[k+1]}/{dates[k+1]}.slc.full', gdal.GA_ReadOnly)
    slc1[:,:] = ds1.GetRasterBand(1).ReadAsArray(rg0,az0,drg,daz)
    slc2[:,:] = ds2.GetRasterBand(1).ReadAsArray(rg0,az0,drg,daz)
    ifg   = slc1*np.conj(slc2)

    # # Do these steps if downlooking with looks.py

    # # write to temp full res file
    # print('write to temp')
    # colds = driver.Create('temp.int',drg,daz,1,gdal.GDT_CFloat32)
    # colds.GetRasterBand(1).WriteArray(ifg)
    # colds=None

    # # create vrt file for temp
    # print('create vrt')
    # cmd = 'fixImageXml.py -i temp.int -f'
    # os.system(cmd)

    # # downlook
    # print('downlook')
    # cmd = f'looks.py -i temp.int -o tempdl.int -r {rlks} -a {alks}'
    # os.system(cmd)

    # downlook using boxcar func
    def boxcar_nan(image, size) -> np.ndarray:
        """Calculate the downsampled image with window "size", ignoring nans.

        Parameters
        ----------
        image : ndarray
            input image, 1 band, can be real or complex.
        size : int or tuple of int
            Window size. If a single int, the window is square.
            If a tuple of (row_size, col_size), the window can be rectangular.

        Returns
        -------
        ndarray
            image downlooked by size, simple average over the "size" window, ignoring nans.  
        """
        if isinstance(size, int):
            size = (size, size)
        if len(size) != 2:
            raise ValueError("size must be a single int or a tuple of 2 ints")
    
        row_size, col_size = size
    
        im_row_size, im_col_size = np.shape(image)
        rows=np.arange(0,im_row_size,row_size)
        cols=np.arange(0,im_col_size,col_size)[:-1]
        dt = image.dtype
    
        small = np.zeros([len(rows),len(cols)],dtype=dt)

        for i in range(len(rows)):
            for j in range(len(cols)):
                thumb=image[rows[i]:rows[i]+row_size,cols[j]:cols[j]+col_size]
                small[i,j] = np.nanmean(thumb)

        return small
    
    ifg_dl = boxcar_nan(ifg,(alks,rlks))
    ifg_dl = np.nan_to_num(ifg_dl)

    print('write to tempdl')
    colds = driver.Create('tempdl.int',math.floor(drg/rlks),math.floor(daz/alks),1,gdal.GDT_CFloat32)
    colds.GetRasterBand(1).WriteArray(ifg_dl)
    colds=None

    # create vrt file for temp_dl
    print('create vrt')
    cmd = 'fixImageXml.py -i tempdl.int -f'
    os.system(cmd)    

    # filter and coherence
    print('filter and coherence')
    cmd = 'FilterAndCoherence.py -i tempdl.int -f filt_tempdl.int -s .1'
    os.system(cmd)

    # unwrap
    print('unwrap')
    # make dir if doesn't exist
    if not os.path.isdir(f'{datadir}/realtimeseries/unw_ifgs/notmasked/{str(dates[k])}_{str(dates[k+1])}'):
        os.mkdir(f'{datadir}/realtimeseries/unw_ifgs/notmasked/{str(dates[k])}_{str(dates[k+1])}')
    os.system(cmd)
    # unwrap with snaphu
    cmd = f'/home/krd86/Software/snaphu-v2.0.6/bin/snaphu -d filt_tempdl.int 1578 -o {datadir}/realtimeseries/unw_ifgs/notmasked/{str(dates[k])}_{str(dates[k+1])}/{str(dates[k])}_{str(dates[k+1])}.unw'
    os.system(cmd)

    print(f'{str(k)} ifg done')