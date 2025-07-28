#!/usr/bin/env python3
"""
Setup experiment directories for all (dimension, run) combinations, including hidden_dim in naming, using gen_ens.py to generate run directories.
Now uses copytree to copy everything except *.pt, rsl.*, wrfrst*, wrfout*, ff1* files, preserving symlinks.
Refactored to use a setup_run_dir function to avoid code repetition.
"""
import yaml
from pathlib import Path
import shutil
import subprocess
from gen_ens import generate_ensemble

def setup_run_dir(src, dst, encoder_src, decoder_src, ignore_patterns):
    if not dst.exists():
        shutil.copytree(src, dst, symlinks=True, ignore=ignore_patterns)
    if encoder_src.exists():
        shutil.copy(encoder_src, dst)
    else:
        raise FileNotFoundError(f"Encoder model {encoder_src} not found!")
    if decoder_src.exists():
        shutil.copy(decoder_src, dst)
    else:
        raise FileNotFoundError(f"Decoder model {decoder_src} not found!")

def main(config):
    wrf_dir = config.get('wrf_dir', None)
    if wrf_dir is None:
        raise ValueError("wrf_dir must be provided in config.yaml")
    wrf_dir = str(Path(wrf_dir).resolve())

    # Define ignore patterns for copytree
    ignore_patterns = shutil.ignore_patterns('*.pt', 'rsl.*', 'wrfrst*', 'wrfout*', 'ff1*')

    full_simulation_dir = Path(config['output_dir']) / "full_simulation"
    if not full_simulation_dir.exists() or not any(full_simulation_dir.iterdir()):
        print(f"Generating ensemble for full simulation using gen_ens.py")
        generate_ensemble(full_simulation_dir, config['num_runs'])
        # Run setup_single.sh for each run directory to generate wrfinput_d01
        setup_script = Path(wrf_dir) / 'test' / 'ensemble' / 'setup_single.sh'
        for run_idx in range(config['num_runs']):
            run_dir = full_simulation_dir / f"run{run_idx:04d}"
            # Copy noop encoder/decoder models
            encoder_src = Path(config['model_dir']) / f"noop_encoder.pt"
            decoder_src = Path(config['model_dir']) / f"noop_decoder.pt"
            if encoder_src.exists():
                shutil.copy(encoder_src, run_dir)
            else:
                raise FileNotFoundError(f"Encoder model {encoder_src} not found!")
            if decoder_src.exists():
                shutil.copy(decoder_src, run_dir)
            else:
                raise FileNotFoundError(f"Decoder model {decoder_src} not found!")
            print(f"Running setup_single.sh for {run_dir}")
            subprocess.run(['bash', str(setup_script), str(run_dir), wrf_dir], check=True)
    else:
        raise FileExistsError(f"Full simulation directory {full_simulation_dir} already exists! Avoiding running gen_ens.py. "
        "Please delete it or set a different output directory.")

    hidden_dim = config['hidden_dim']
    for dim in config['dimensions']:
        dim_dir = Path(config['output_dir']) / f"dim_{dim}_hidden_{hidden_dim}"
        for run_idx in range(config['num_runs']):
            simulation_dir = full_simulation_dir / f"run{run_idx:04d}"
            run_dir = dim_dir / f"run{run_idx:04d}"
            encoder_src = Path(config['model_dir']) / f"encoder_model_{dim}_hidden_{hidden_dim}.pt"
            decoder_src = Path(config['model_dir']) / f"decoder_model_{dim}_hidden_{hidden_dim}.pt"
            setup_run_dir(simulation_dir, run_dir, encoder_src, decoder_src, ignore_patterns)

    bad_dir = Path(config['output_dir']) / "bad_autoencoder"
    for run_idx in range(config['num_runs']):
        simulation_dir = full_simulation_dir / f"run{run_idx:04d}"
        run_dir = bad_dir / f"run{run_idx:04d}"
        encoder_src = Path(config['model_dir']) / f"bad_encoder.pt"
        decoder_src = Path(config['model_dir']) / f"bad_decoder.pt"
        setup_run_dir(simulation_dir, run_dir, encoder_src, decoder_src, ignore_patterns)

if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    main(config) 
