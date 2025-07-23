#!/usr/bin/env python3
"""
Setup experiment directories for all (dimension, run) combinations, including hidden_dim in naming, using gen_ens.py to generate run directories.
"""
import yaml
from pathlib import Path
import shutil
from gen_ens import generate_ensemble

def main():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    wrf_dir = config.get('wrf_dir', None)
    if wrf_dir is None:
        raise ValueError("wrf_dir must be provided in config.yaml")
    wrf_dir = str(Path(wrf_dir).resolve())

    full_simulation_dir = Path(config['output_dir']) / "full_simulation"
    if not full_simulation_dir.exists() or not any(full_simulation_dir.iterdir()):
        print(f"Generating ensemble for full simulation using gen_ens.py")
        generate_ensemble(full_simulation_dir, config['num_runs']) 
        for run_idx in range(config['num_runs']):
            run_dir = full_simulation_dir / f"run{run_idx:04d}"

            encoder_src = Path(config['model_dir']) / f"noop_encoder_model.pt"
            decoder_src = Path(config['model_dir']) / f"noop_decoder_model.pt"
            if encoder_src.exists():
                shutil.copy(encoder_src, run_dir)
            else:
                raise FileNotFoundError(f"Encoder model {encoder_src} not found!")

            if decoder_src.exists():
                shutil.copy(decoder_src, run_dir)
            else:
                raise FileNotFoundError(f"Decoder model {decoder_src} not found!")
    else:
        raise FileExistsError(f"Full simulation directory {full_simulation_dir} already exists! Avoiding running gen_ens.py. "
        "Please delete it or set a different output directory.")
    
    copy_files = ["input_sounding.ppe", "ppe_parameters.json", "ppe_parameters.nml"]
    hidden_dim = config['hidden_dim']
    
    for dim in config['dimensions']:
        dim_dir = Path(config['output_dir']) / f"dim_{dim}_hidden_{hidden_dim}"
        # dim_dir.mkdir(parents=True, exist_ok=True)
        # shutil.copytree(full_simulation_dir, dim_dir)
        for run_idx in range(config['num_runs']):
            simulation_dir = full_simulation_dir / f"run{run_idx:04d}"
            run_dir = dim_dir / f"run{run_idx:04d}"
            if not run_dir.exists():
                run_dir.mkdir(parents=True, exist_ok=True)
                for file in copy_files:
                    shutil.copy(simulation_dir / file, run_dir / file)
            # Copy the correct encoder/decoder
            encoder_src = Path(config['model_dir']) / f"encoder_model_{dim}_hidden_{hidden_dim}.pt"
            decoder_src = Path(config['model_dir']) / f"decoder_model_{dim}_hidden_{hidden_dim}.pt"
            if encoder_src.exists():
                shutil.copy(encoder_src, run_dir)
            else:
                raise FileNotFoundError(f"Encoder model {encoder_src} not found!")

            if decoder_src.exists():
                shutil.copy(decoder_src, run_dir)
            else:
                raise FileNotFoundError(f"Decoder model {decoder_src} not found!")

    bad_dir = Path(config['output_dir'])/"bad_autoencoder"
    for run_idx in range(config['num_runs']):
        simulation_dir = full_simulation_dir / f"run{run_idx:04d}"
        run_dir = bad_dir / f"run{run_idx:04d}"
        if not run_dir.exists():
            run_dir.mkdir(parents=True, exist_ok=True)
            for file in copy_files:
                shutil.copy(simulation_dir / file, run_dir / file)
        # Copy the correct encoder/decoder
        encoder_src = Path(config['model_dir']) / f"bad_encoder_model.pt"
        decoder_src = Path(config['model_dir']) / f"bad_decoder_model.pt"
        if encoder_src.exists():
            shutil.copy(encoder_src, run_dir)
        else:
            raise FileNotFoundError(f"Encoder model {encoder_src} not found!")

        if decoder_src.exists():
            shutil.copy(decoder_src, run_dir)
        else:
            raise FileNotFoundError(f"Decoder model {decoder_src} not found!")

    

if __name__ == '__main__':
    main() 
