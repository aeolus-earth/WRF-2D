#!/usr/bin/env python3
"""
Setup experiment directories for threshold comparison runs, using gen_ens.py to generate run directories.
Now uses copytree to copy everything except *.pt, rsl.*, wrfrst*, wrfout*, ff1* files, preserving symlinks.
Refactored to use a setup_run_dir function to avoid code repetition.
"""
import yaml
from pathlib import Path
import shutil
import subprocess


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

    # Get threshold configuration
    thresholds_config = config.get('thresholds_runs', {})
    if not thresholds_config:
        raise ValueError("thresholds_runs configuration not found in config.yaml")
    
    thresholds = thresholds_config.get('thresholds', [])
    base_run = Path(thresholds_config.get('base_run'))
    end_time_minutes = thresholds_config.get('end_time_minutes', 90)
    submit_jobs = thresholds_config.get('submit_jobs', True)
    output_suffix = thresholds_config.get('output_suffix', 'with_thresholds')
    
    if not base_run.exists():
        raise FileNotFoundError(f"Base run directory {base_run} not found!")
    
    print(f"Setting up threshold experiments with {len(thresholds)} thresholds")
    print(f"Thresholds: {thresholds}")
    print(f"Base run: {base_run}")
    print(f"End time: {end_time_minutes} minutes")
    
    # Create output directory for threshold runs
    output_dir = Path(config['output_dir'])
    threshold_dir = output_dir / f"threshold_experiments_{output_suffix}"
    threshold_dir.mkdir(parents=True, exist_ok=True)

    submit_script = Path(config['submit_script'])
    
    # Create runs for each threshold
    for threshold in thresholds:
        # Format threshold for directory naming (e.g., 1e-5 -> 1e_5)
        threshold_float = float(threshold)  # Convert string to float if needed
        threshold_str = f"{threshold_float:.0e}"#.replace('-', '_').replace('+', '')
        threshold_run_dir = threshold_dir / f"threshold_{threshold_str}"

        print(f"\nSetting up threshold {threshold} in {threshold_run_dir}")

        # Copy appropriate encoder/decoder files
        encoder_src = Path(config['model_dir']) / f"encoder_model_threshold_{threshold_str}.pt"
        decoder_src = Path(config['model_dir']) / f"decoder_model_threshold_{threshold_str}.pt"
        
        # Use setup_run_dir function to copy base run and model files
        setup_run_dir(base_run, threshold_run_dir, encoder_src, decoder_src, ignore_patterns)

        # Submit job if requested
        if submit_jobs:
            print(f"Submitting job for threshold {threshold} in {threshold_run_dir}")
            subprocess.run(['sbatch', submit_script, str(threshold_run_dir), str(wrf_dir)], cwd=threshold_run_dir)
    
    print(f"\nThreshold experiments setup complete!")
    print(f"Created {len(thresholds)} threshold runs in {threshold_dir}")
    print(f"Each run will end at {end_time_minutes} minutes")

if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    main(config) 
