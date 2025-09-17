import os
import sys
import uuid
import shutil
import json
import pickle
import numpy as np
import xarray as xr

WRFOUT_FILENAME     = 'wrfout_d01_0001-01-01_00:00:00'
AUXHIST_FILENAME    = 'auxhist3_d01_0001-01-01_00:00:00'
JSON_FILENAME       = 'ppe_parameters.json'
NAMELIST_FILENAME   = 'ppe_parameters.nml'
SOUNDING_FILENAME   = 'input_sounding.ppe'
PARAM_LIST_FILENAME = 'parameter_list.pkl'
RSL_OUT_FILENAME    = 'rsl.out.0000'
SERIES_FILENAME     = 'series.nc'
SERIES_SEL_FILENAME = 'series_sel.nc'

WRF_SUCCESS_STR     = 'SUCCESS COMPLETE WRF'

def buffered_open(*o_args, **o_kwargs):
    def decorator(func):
        def wrapper(fname, *w_args, **w_kwargs):
            tmp_fname = f'./.tmp.{uuid.uuid4().hex}'
            result = None
            try:
                if os.path.exists(fname):
                    shutil.copy2(fname, tmp_fname)
                with open(tmp_fname, *o_args, **o_kwargs) as file:
                    result = func(file, *w_args, **w_kwargs)
                shutil.move(tmp_fname, fname)
            except:
                print(f'IOError at {fname}, {tmp_fname}')
                raise IOError()
            finally:
                if os.path.exists(tmp_fname):
                    os.remove(tmp_fname)
                return result
        return wrapper
    return decorator

@buffered_open('w')
def write_json(file, d): json.dump(d, file, indent=4)

@buffered_open('r')
def read_json(file): return json.load(file)

@buffered_open('wb')
def write_pickle(file, x): pickle.dump(x, file)

@buffered_open('rb')
def read_pickle(file): return pickle.load(file)

def globalize(func):
    def result(*args, **kwargs):
        return func(*args, **kwargs)
    result.__name__ = result.__qualname__ = uuid.uuid4().hex
    setattr(sys.modules[result.__module__], result.__name__, result)
    return result

from multiprocessing import Pool
def pool_map(f, arr, n_procs=32):
    res = None
    func_global = globalize(f)
    with Pool(processes=n_procs) as pool:
        res = pool.map(func_global, arr)
    return res

def loop_run_paths(func):
    def wrapper(ens_path, *args, **kwargs):
        run_paths = [ os.path.join(ens_path, s)
                      for s in sorted(os.listdir(ens_path)) if s.startswith('run') ]
        res = pool_map((lambda run_path: func(run_path, *args, **kwargs)), run_paths)
        return res
    return wrapper

def on_nc_file(filename):
    def decorator(func):
        def wrapper(file_path, *args, **kwargs):
            ds = xr.open_dataset(os.path.join(file_path, filename), decode_times=False)
            result = func(ds, *args, **kwargs)
            ds.close()
            return result
        return wrapper
    return decorator

def on_json(func):
    def wrapper(run_path, *args, **kwargs):
        param = read_json(os.path.join(run_path, JSON_FILENAME))
        return func(param)
    return wrapper

on_wrfout  = on_nc_file(WRFOUT_FILENAME )
on_auxhist = on_nc_file(AUXHIST_FILENAME)

def save_netcdf(ds, filename):
    encode = {'zlib': True, 'complevel': 9}
    ds.to_netcdf(
        path     = filename,
        format   = 'NETCDF4',
        encoding = {var: encode for var in ds.variables},
    )