import os
import numpy as np
from scipy.stats import qmc
import matplotlib.pyplot as plt
from ppe_io import *
from phys import *

z = np.linspace(0, 7000, 701)

def get_profile(param):
    theta = param['theta_l0'] - dtheta_l0 + np.where(z<=h_ml, 0, param['gamma']*(z-h_ml)/1e3)
    Qv = param['q_tml'] * np.where(z<=h_ml, 1, np.exp(-(z-h_ml)/param['h_qt']))
    return theta, Qv

def write_wrf_profile(fname, theta, Qv, P00=1e5):
    with open(fname, 'w') as f:
        f.write(f'{int(P00/1e2):5d} {theta[0]:9.4f} {Qv[0]:7.3f}\n')
        for i in range(1, len(z)):
            f.write(f'{int(z[i]):5d} {theta[i]:9.4f} {Qv[i]:9.5f}  0  0\n')

def write_namelist(fname, param):
    with open(fname, 'w') as f:
        f.write(f'''
&profile
    theta_l0 = {param['theta_l0']:.4f}
    gamma    = {param['gamma']:.5f}
    q_tml    = {param['q_tml']:.5f}
    h_qt     = {param['h_qt']:.2f}
/

&perturb
    init_rad = {param['init_rad']:.1f}
/

&ccn
    N_m2     = {param['N_m2']:.1f}
/
        ''')

sampler = qmc.Sobol(d=7)
linscale = lambda n, xmin, xmax: (xmax - xmin) *  n + xmin
logscale = lambda n, xmin, xmax: (xmax / xmin) ** n * xmin
def generate_parameters(n_samples=10):
    sample = sampler.random(n=n_samples).T
    param = {}
    param['theta_l0'] = linscale(sample[0], 295.0, 300.0)
    param['gamma'   ] = linscale(sample[1],   3.5,   5.5)
    param['RH_ml'   ] = linscale(sample[2], 0.925, 1.050)
    param['h_qt'    ] = linscale(sample[3],  1000,  3000)
    param['N_m2'    ] = logscale(sample[4],    10,  1000)
    param['init_rad'] = linscale(sample[5],   100,  1000)
    param['delt'    ] = linscale(sample[6],   0.1,     1)
    theta0 = param['theta_l0'] - dtheta_l0
    pi_ml = 1 - (g*h_ml) / (cpd*theta0)
    T_ml = theta0 * pi_ml
    P_ml = P00 * pi_ml ** (cpd/Rd)
    param['q_tml'] = func_Qv( P_ml, param['RH_ml']*func_esl(T_ml) ) * 1e3
    rank = np.argsort(param['RH_ml'])[::-1]
    for k in param: param[k] = param[k][rank]
    return param

mkdir = lambda path: os.makedirs(path, exist_ok=True)
def setup_ensemble(ens_path, param):
    n_samples = param['theta_l0'].size
    for i in range(n_samples):
        run_path = os.path.join(ens_path, f'run{i:04d}')
        r_param = { n: v[i] for (n, v) in param.items() }
        mkdir(run_path)
        theta, Qv = get_profile(r_param)
        write_json( os.path.join(run_path, JSON_FILENAME), r_param )
        write_namelist( os.path.join(run_path, NAMELIST_FILENAME), r_param )
        write_wrf_profile( os.path.join(run_path, SOUNDING_FILENAME), theta, Qv )

def generate_ensemble(ens_path='.', n_samples=10):
    mkdir(ens_path)
    param = generate_parameters(n_samples)
    write_pickle( os.path.join(ens_path, PARAM_LIST_FILENAME), param )
    setup_ensemble(ens_path, param)
    return param

import sys
if __name__ == '__main__':
    ens_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    n_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    generate_ensemble(ens_path, n_samples)