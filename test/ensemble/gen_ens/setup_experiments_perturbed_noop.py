#!/usr/bin/env python3
"""
Setup experiment directories for perturbed WRF input files using noop encoder/decoder.
Simplified version that only handles noop models.
"""
import yaml
from pathlib import Path
import shutil
import subprocess
import os


def setup_perturbed_noop_experiments(config):
    """Setup experiments using perturbed WRF input files with noop encoder/decoder."""
    wrf_dir = config.get('wrf_dir', None)
    if wrf_dir is None:
        raise ValueError("wrf_dir must be provided in config.yaml")
    wrf_dir = str(Path(wrf_dir).resolve())

    # Define ignore patterns for copytree
    ignore_patterns = shutil.ignore_patterns('*.pt', 'rsl.*', 'wrfrst*', 'wrfout*', 'ff1*')

    # Get perturbed input configuration
    perturbed_config = config.get('perturbed_inputs', {})
    if not perturbed_config:
        raise ValueError("perturbed_inputs configuration not found in config.yaml")
    
    perturbed_dir = Path(perturbed_config.get('perturbed_dir'))
    base_run = Path(perturbed_config.get('base_run'))
    submit_jobs = perturbed_config.get('submit_jobs', True)
    output_suffix = perturbed_config.get('output_suffix', 'perturbed')
    
    if not perturbed_dir.exists():
        raise FileNotFoundError(f"Perturbed input directory {perturbed_dir} not found!")
    if not base_run.exists():
        raise FileNotFoundError(f"Base run directory {base_run} not found!")
    
    # Find all perturbed input files
    perturbed_files = list(perturbed_dir.glob("wrfinput_d01_perturbed_*.nc"))
    if not perturbed_files:
        raise FileNotFoundError(f"No perturbed input files found in {perturbed_dir}")
    
    perturbed_files.sort()
    
    print(f"Setting up {len(perturbed_files)} perturbed experiments with noop encoder")
    print(f"Base run: {base_run}")
    print(f"Perturbed inputs: {perturbed_dir}")
    
    # Setup noop model files
    encoder_src = Path(config['model_dir']) / "noop_encoder.pt"
    decoder_src = Path(config['model_dir']) / "noop_decoder.pt"
    
    # Create output directory
    output_dir = Path(config['output_dir'])
    experiment_dir = output_dir / f"perturbed_noop_{output_suffix}"
    experiment_dir.mkdir(parents=True, exist_ok=True)

    submit_script = Path(config['submit_script'])
    
    # Create runs for each perturbed input file
    for i, perturbed_file in enumerate(perturbed_files):
        perturb_num = perturbed_file.stem.split('_')[-1]
        run_dir = experiment_dir / f"perturb_{perturb_num}"
        
        print(f"\nSetting up run {i+1}/{len(perturbed_files)}: {run_dir}")
        
        # Copy base run directory
        if not run_dir.exists():
            shutil.copytree(base_run, run_dir, symlinks=True, ignore=ignore_patterns)
        
        # Copy noop models
        shutil.copy(encoder_src, run_dir)
        shutil.copy(decoder_src, run_dir)
        
        # Copy perturbed input file as wrfinput_d01
        dst_input = run_dir / "wrfinput_d01"
        shutil.copy(perturbed_file, dst_input)
        print(f"  Copied: {perturbed_file.name} -> wrfinput_d01")
        
        # Backup original for comparison
        original_input = base_run / "wrfinput_d01"
        if original_input.exists():
            original_backup = run_dir / "wrfinput_d01_original"
            shutil.copy(original_input, original_backup)
            print(f"  Backed up original wrfinput_d01")
        
        # Submit job if requested
        if submit_jobs:
            print(f"  Submitting job for perturb_{perturb_num}")
            subprocess.run(['sbatch', submit_script, str(run_dir), str(wrf_dir)], cwd=run_dir)
    
    print(f"\nSetup complete! Created {len(perturbed_files)} runs in {experiment_dir}")
    print(f"To verify: cd {experiment_dir} && ls -la perturb_000/wrfinput*")


def main():
    """Main function."""
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    setup_perturbed_noop_experiments(config)


if __name__ == '__main__':
    main() 