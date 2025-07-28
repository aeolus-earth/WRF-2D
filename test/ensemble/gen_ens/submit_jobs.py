#!/usr/bin/env python3
"""
Submit a WRF job for each run directory using SLURM, including hidden_dim in naming.
"""
import yaml
from pathlib import Path
import subprocess

def main(config):
    wrf_dir = config.get('wrf_dir', None)
    if wrf_dir is None:
        raise ValueError("wrf_dir must be provided in config.yaml")
    wrf_dir = Path(wrf_dir).absolute()
    submit_script = wrf_dir / 'test' / 'ensemble' / 'submit_wrf.sh'

    full_simulation_dir = Path(config['output_dir']) / "full_simulation"
    if full_simulation_dir.exists():
        for run_idx in range(config['num_runs']):
            run_dir = (full_simulation_dir / f"run{run_idx:04d}").absolute()
            if run_dir.exists():
                print(f"Submitting job for {run_dir}")
                subprocess.run(['sbatch', str(submit_script), str(run_dir), str(wrf_dir)], cwd=run_dir)
            else:
                raise FileNotFoundError(f"Run directory {run_dir} does not exist. Please check if the full simulation directory exists.")

    hidden_dim = config['hidden_dim']
    for dim in config['dimensions']:
        for run_idx in range(config['num_runs']):
            run_dir = (Path(config['output_dir']) / f"dim_{dim}_hidden_{hidden_dim}" / f"run{run_idx:04d}").absolute()
            if run_dir.exists():
                print(f"Submitting job for {run_dir}")
                subprocess.run(['sbatch', str(submit_script), str(run_dir), str(wrf_dir)], cwd=run_dir)
            else:
                raise FileNotFoundError(f"Run directory {run_dir} does not exist. Please check if the full simulation directory exists.")

    for run_idx in range(config['num_runs']):
        run_dir = (Path(config['output_dir']) / f"bad_autoencoder" / f"run{run_idx:04d}").absolute()
        if run_dir.exists():
            print(f"Submitting job for {run_dir}")
            subprocess.run(['sbatch', str(submit_script), str(run_dir), str(wrf_dir)], cwd=run_dir)
        else:
            raise FileNotFoundError(f"Run directory {run_dir} does not exist. Please check if the full simulation directory exists.")

if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    main(config) 


    sbatch /home/x-yyang40/kangen-wrf-33-cpy/test/ensemble/gen_ens/submit_wrf.sh /anvil/scratch/x-yyang40/ensemble_results_v9/dim_2_hidden_256/run0001 /home/x-yyang40/kangen-wrf-33-cpy