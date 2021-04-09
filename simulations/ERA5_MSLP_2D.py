import os
import sys
import time
import xarray as xr
import numpy  as np
from pathlib import Path

# Import library specific modules
sys.path.append("/hpctmp/e0546050/PySPOD/")
import pyspod
from pyspod.spod_low_storage import SPOD_low_storage
from pyspod.spod_low_ram     import SPOD_low_ram
from pyspod.spod_streaming   import SPOD_streaming
import pyspod.postprocessing as ps
import pyspod.weights as weights

# Current path
CWD = os.getcwd()

# Data path
DP = '/hpctmp2/e0546050/data/ERA5/'

# Inspect and load data
#file = os.path.join(CWD,'ERA5_RA_2019_MSLP.nc')
file = os.path.join(DP,'ERA5_MSL_Summer_2010_2019_hourly.nc')
ds = xr.open_dataset(file)
print(ds)


# we extract time, longitude and latitude
t = np.array(ds['time'])
x1 = np.array(ds['longitude'])
x2 = np.array(ds['latitude'])
print('shape of t (time): ', t.shape)
print('shape of x1 (longitude): ', x1.shape)
print('shape of x2 (latitude) : ', x2.shape)



def read_data(data, t_0, t_end, variables):
	if t_0 == t_end: ti = [t_0]
	else           : ti = np.arange(t_0,t_end)
	X = np.empty([len(ti), x2.shape[0], x1.shape[0], len(variables)])
	for _,var in enumerate(variables):
		X = np.array(ds[var].isel(time=ti))
	return X

# we set the variables we want to use for the analysis
# (we select all the variables present) and load the in RAM
s = time.time()
variables = ['msl']
X = read_data(data=ds, t_0=0, t_end=0, variables=variables)
# for i,var in enumerate(variables):
#     X[...,i] = np.array(ds[var])
# #   X[...,i] = np.einsum('ijk->ikj', np.array(ds[var]))
# #   X[...,i] = np.nan_to_num(X[...,i])
# print('shape of data matrix X: ', X.shape)
# print('elapsed time: ', time.time() - s, 's.')

# define required and optional parameters
params = dict()

# required parameters
params['dt'          ] = 1                	# data time-sampling (1 hour)
params['nt'          ] = t.shape[0]       	# number of time snapshots (we consider all data)
params['xdim'        ] = 2                	# number of spatial dimensions (longitude and latitude)
params['nv'          ] = len(variables)            	# number of variables
params['p_blk'		   ] = 24 * 30 * 3				    #*Newly added* period of a block
params['n_FFT'       ] = np.ceil( params['p_blk'] / params['dt'] )     # *Edited* Number of variables in a block
#params['n_FFT'       ] = np.ceil(24 * 30)          	# length of FFT blocks (24 hours by 30 days)
params['n_freq'      ] = params['n_FFT'] / 2 + 1   	# number of frequencies
params['n_overlap'   ] = np.ceil(params['n_FFT'] * 0 / 100) # dimension block overlap region
params['mean'        ] = 'blockwise' 						# type of mean to subtract to the data
params['normalize'   ] = True        						# normalization of weights by data variance
params['savedir'     ] = os.path.join(CWD, 'results', Path(file).stem) # folder where to save results


# optional parameters
params['weights'] = weights.geo_weights_trapz_2D(\
    lat=x2, lon=x1, R=1, n_vars=params['nv']) 	# weights
params['savefreqs'   ] = np.arange(0,params['n_freq']) # frequencies to be saved
params['n_modes_save'] = 3      # modes to be saved
params['normvar'     ] = False  # normalize data by data variance
params['conf_level'  ] = 0.95   # calculate confidence level
params['savefft'     ] = True   # save FFT blocks to reuse them in the future (saves time)

print('nt value',params['nt'])
# Perform SPOD analysis using low storage module
SPOD_analysis = SPOD_low_ram(X=ds, params=params, data_handler=read_data, variables=variables)
spod = SPOD_analysis.fit()


# Show results
T_approx = 10 # approximate period = 10 days (in days)                                             # changes make here, from 4 to 24

# freq,n_freq,n_DFT = ps.generate_freq(params['n_FFT'], params['dt']) 
# print(freq)

freq = spod.freq * 24 # (in days)                                                                       # changes make here, from 4 to 24
freq_found, freq_idx = spod.find_nearest_freq(freq_required=1/T_approx, freq = freq)                           # changes make here to freq.
modes_at_freq = spod.get_modes_at_freq(freq_idx=freq_idx)


spod.plot_eigs_vs_frequency(
	freq=freq,
	filename=('eigs_vs_frequency.png'))



spod.plot_eigs_vs_period(
	freq=freq,
	xticks=[1, 7, 14, 30],
	filename=('eigs_vs_period.png'))


print ('frequency plotting is ', freq_found)
#print('x1 value',x1)
#print('x2 value',x2)

# x1 from the calculations is the longtitude
# x2 from the calculations is the latitude
spod.plot_2D_modes_at_frequency(
	freq_required=freq_found,
	freq=freq,
	modes_idx=[0,1],
	x1=x2,
	x2=x1-175,
	vars_idx=[0],
	coastlines='regular',
	filename=('2D_data.png'))
    
