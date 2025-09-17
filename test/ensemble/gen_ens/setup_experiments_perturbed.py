#!/usr/bin/env python3
"""
Setup experiment directories for perturbed WRF input files.
This script copies perturbed wrfinput files, renames them properly, and creates symlinks
to test different perturbed initial conditions with WRF.

Supports:
1. 100 perturbed runs for noop autoencoder and threshold models (1e-7, 1e-9, 1e-11)
2. First 10 perturbed runs for all autoencoder configurations (hidden dims: 43,64,256; latent dims: 2,4,8,16,33)
"""
import yaml
from pathlib import Path
import shutil
import subprocess
import os
from gen_ens import generate_ensemble


def setup_run_dir_with_perturbed_input(src, dst, encoder_src, decoder_src, perturbed_input_file, ignore_patterns):
    """
    Setup run directory with perturbed input file.
    
    Args:
        src: Source directory to copy from
        dst: Destination directory
        encoder_src: Path to encoder model file
        decoder_src: Path to decoder model file  
        perturbed_input_file: Path to perturbed wrfinput file
        ignore_patterns: Patterns to ignore when copying
    """
    if not dst.exists():
        shutil.copytree(src, dst, symlinks=True, ignore=ignore_patterns)
    
    # Copy encoder/decoder models
    if encoder_src.exists():
        shutil.copy(encoder_src, dst)
    else:
        raise FileNotFoundError(f"Encoder model {encoder_src} not found!")
    if decoder_src.exists():
        shutil.copy(decoder_src, dst)
    else:
        raise FileNotFoundError(f"Decoder model {decoder_src} not found!")
    
    # Copy and setup perturbed input file
    if perturbed_input_file.exists():
        # Copy the perturbed file to the run directory with standard name
        dst_input_file = dst / "wrfinput_d01"
        shutil.copy(perturbed_input_file, dst_input_file)
        print(f"  Copied perturbed input: {perturbed_input_file.name} -> wrfinput_d01")
        
        # Also copy the original for comparison (if it exists in src)
        original_input = src / "wrfinput_d01"
        if original_input.exists():
            original_backup = dst / "wrfinput_d01_original"
            shutil.copy(original_input, original_backup)
            print(f"  Backed up original: wrfinput_d01 -> wrfinput_d01_original")
    else:
        raise FileNotFoundError(f"Perturbed input file {perturbed_input_file} not found!")


def setup_comprehensive_perturbed_experiments(config):
    """
    Setup comprehensive experiments using perturbed WRF input files.
    
    Creates:
    1. 100 perturbed runs for noop and threshold models
    2. First 10 perturbed runs for all autoencoder configurations
    
    Args:
        config: Configuration dictionary from YAML file
    """
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
    output_suffix = perturbed_config.get('output_suffix', 'comprehensive')
    
    if not perturbed_dir.exists():
        raise FileNotFoundError(f"Perturbed input directory {perturbed_dir} not found!")
    if not base_run.exists():
        raise FileNotFoundError(f"Base run directory {base_run} not found!")
    
    # Find all perturbed input files
    perturbed_files = list(perturbed_dir.glob("wrfinput_d01_perturbed_*.nc"))
    if not perturbed_files:
        raise FileNotFoundError(f"No perturbed input files found in {perturbed_dir}")
    
    perturbed_files.sort()  # Sort for consistent ordering
    
    print(f"Setting up comprehensive experiments with {len(perturbed_files)} perturbed input files")
    print(f"Base run: {base_run}")
    print(f"Perturbed input directory: {perturbed_dir}")
    
    # Create output directory for comprehensive experiments
    output_dir = Path(config['output_dir'])
    experiment_dir = output_dir / f"comprehensive_experiments_{output_suffix}"
    experiment_dir.mkdir(parents=True, exist_ok=True)

    submit_script = Path(config['submit_script'])
    
    # Define model configurations
    # 1. Models that get ALL 100 perturbed runs
    full_ensemble_models = [
        ('noop', 'noop_encoder.pt', 'noop_decoder.pt'),
        ('threshold_1e-7', 'encoder_model_threshold_1e-7.pt', 'decoder_model_threshold_1e-7.pt'),
        ('threshold_1e-9', 'encoder_model_threshold_1e-9.pt', 'decoder_model_threshold_1e-9.pt'),
        ('threshold_1e-11', 'encoder_model_threshold_1e-11.pt', 'decoder_model_threshold_1e-11.pt'),
    ]
    
    # 2. Models that get only first 10 perturbed runs
    partial_ensemble_models = []
    hidden_dims = [43, 64, 256]
    latent_dims = [2, 4, 8, 16, 33]
    
    for hidden_dim in hidden_dims:
        for latent_dim in latent_dims:
            model_name = f"dim_{latent_dim}_hidden_{hidden_dim}"
            encoder_file = f"encoder_model_{latent_dim}_hidden_{hidden_dim}.pt"
            decoder_file = f"decoder_model_{latent_dim}_hidden_{hidden_dim}.pt"
            partial_ensemble_models.append((model_name, encoder_file, decoder_file))
    
    # Setup full ensemble experiments (100 perturbed runs)
    print(f"\n=== Setting up FULL ENSEMBLE experiments (100 perturbed runs) ===")
    for model_name, encoder_file, decoder_file in full_ensemble_models:
        print(f"\nSetting up {model_name} with all {len(perturbed_files)} perturbed inputs")
        
        # Create model-specific directory
        model_dir = experiment_dir / f"full_ensemble_{model_name}"
        model_dir.mkdir(exist_ok=True)
        
        # Setup model files
        encoder_src = Path(config['model_dir']) / encoder_file
        decoder_src = Path(config['model_dir']) / decoder_file
        
        if not encoder_src.exists() or not decoder_src.exists():
            print(f"  WARNING: Model files not found for {model_name}, skipping...")
            continue
        
        # Create runs for each perturbed input file
        for i, perturbed_file in enumerate(perturbed_files):
            perturb_num = perturbed_file.stem.split('_')[-1]
            perturb_run_dir = model_dir / f"perturb_{perturb_num}"
            
            print(f"  Setting up run {i+1}/{len(perturbed_files)}: {perturb_run_dir.name}")
            
            # Setup run directory with perturbed input
            setup_run_dir_with_perturbed_input(
                base_run, perturb_run_dir, encoder_src, decoder_src, 
                perturbed_file, ignore_patterns
            )
            
            # Create comparison symlink
            original_link = perturb_run_dir / "wrfinput_d01_original_link"
            if original_link.exists():
                original_link.unlink()
            
            original_backup = perturb_run_dir / "wrfinput_d01_original"
            if original_backup.exists():
                os.symlink("wrfinput_d01_original", str(original_link))
            
            # Submit job if requested
            if submit_jobs:
                subprocess.run(['sbatch', submit_script, str(perturb_run_dir), str(wrf_dir)], cwd=perturb_run_dir)
    
    # Setup partial ensemble experiments (first 10 perturbed runs)
    print(f"\n=== Setting up PARTIAL ENSEMBLE experiments (first 10 perturbed runs) ===")
    partial_perturbed_files = perturbed_files[:10]  # Only first 10
    
    for model_name, encoder_file, decoder_file in partial_ensemble_models:
        print(f"\nSetting up {model_name} with first {len(partial_perturbed_files)} perturbed inputs")
        
        # Create model-specific directory
        model_dir = experiment_dir / f"partial_ensemble_{model_name}"
        model_dir.mkdir(exist_ok=True)
        
        # Setup model files
        encoder_src = Path(config['model_dir']) / encoder_file
        decoder_src = Path(config['model_dir']) / decoder_file
        
        if not encoder_src.exists() or not decoder_src.exists():
            print(f"  WARNING: Model files not found for {model_name}, skipping...")
            continue
        
        # Create runs for first 10 perturbed input files
        for i, perturbed_file in enumerate(partial_perturbed_files):
            perturb_num = perturbed_file.stem.split('_')[-1]
            perturb_run_dir = model_dir / f"perturb_{perturb_num}"
            
            print(f"  Setting up run {i+1}/{len(partial_perturbed_files)}: {perturb_run_dir.name}")
            
            # Setup run directory with perturbed input
            setup_run_dir_with_perturbed_input(
                base_run, perturb_run_dir, encoder_src, decoder_src, 
                perturbed_file, ignore_patterns
            )
            
            # Create comparison symlink
            original_link = perturb_run_dir / "wrfinput_d01_original_link"
            if original_link.exists():
                original_link.unlink()
            
            original_backup = perturb_run_dir / "wrfinput_d01_original"
            if original_backup.exists():
                os.symlink("wrfinput_d01_original", str(original_link))
            
            # Submit job if requested
            if submit_jobs:
                subprocess.run(['sbatch', submit_script, str(perturb_run_dir), str(wrf_dir)], cwd=perturb_run_dir)
    
    # Create comprehensive summary
    print(f"\n=== Creating experiment summary ===")
    summary_file = experiment_dir / "comprehensive_experiment_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Comprehensive WRF Experiments Summary\n")
        f.write(f"====================================\n\n")
        f.write(f"Base run directory: {base_run}\n")
        f.write(f"Perturbed inputs from: {perturbed_dir}\n")
        f.write(f"Total perturbed inputs available: {len(perturbed_files)}\n\n")
        
        f.write(f"FULL ENSEMBLE (100 perturbed runs):\n")
        f.write(f"  - noop autoencoder\n")
        f.write(f"  - threshold_1e-7 autoencoder\n")
        f.write(f"  - threshold_1e-9 autoencoder\n")
        f.write(f"  - threshold_1e-11 autoencoder\n\n")
        
        f.write(f"PARTIAL ENSEMBLE (first 10 perturbed runs):\n")
        f.write(f"  Hidden dimensions: {hidden_dims}\n")
        f.write(f"  Latent dimensions: {latent_dims}\n")
        f.write(f"  Total autoencoder configurations: {len(partial_ensemble_models)}\n\n")
        
        f.write(f"Experiment structure:\n")
        f.write(f"  {experiment_dir}/\n")
        f.write(f"    full_ensemble_*/          # 100 perturbed runs each\n")
        f.write(f"    partial_ensemble_*/       # 10 perturbed runs each\n\n")
        
        f.write(f"Total experiments created:\n")
        f.write(f"  Full ensemble: {len(full_ensemble_models)} × {len(perturbed_files)} = {len(full_ensemble_models) * len(perturbed_files)}\n")
        f.write(f"  Partial ensemble: {len(partial_ensemble_models)} × 10 = {len(partial_ensemble_models) * 10}\n")
        f.write(f"  Grand total: {len(full_ensemble_models) * len(perturbed_files) + len(partial_ensemble_models) * 10}\n")
    
    print(f"Summary written to: {summary_file}")
    
    # Print verification commands
    print(f"\n=== Verification commands ===")
    print(f"cd {experiment_dir}")
    print(f"ls -la")
    print(f"# Check full ensemble:")
    print(f"ls -la full_ensemble_noop/ | head -10")
    print(f"# Check partial ensemble:")
    print(f"ls -la partial_ensemble_dim_2_hidden_43/ | head -10")
    print(f"# Count total experiments:")
    print(f"find . -name 'perturb_*' -type d | wc -l")


def setup_perturbed_experiments(config):
    """
    Legacy function - kept for backward compatibility.
    Use setup_comprehensive_perturbed_experiments for new comprehensive setup.
    """
    print("WARNING: Using legacy setup_perturbed_experiments function.")
    print("Consider using setup_comprehensive_perturbed_experiments instead.")
    
    # Call the comprehensive function with default settings
    setup_comprehensive_perturbed_experiments(config)


def main():
    """Main function to run comprehensive perturbed experiments setup."""
    print("Setting up comprehensive perturbed WRF experiments...")
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    setup_comprehensive_perturbed_experiments(config)


if __name__ == '__main__':
    main() 