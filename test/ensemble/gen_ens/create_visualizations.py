#!/usr/bin/env python3
"""
Generate visualizations for all experiments by calling the appropriate visualization scripts, including hidden_dim in naming.
Creates one multi-panel GIF per run showing all dimensions together.
"""
import yaml
import subprocess
from pathlib import Path
import sys

# Add the visualization directory to the path so we can import the plotting function
sys.path.append(str(Path(__file__).parent.parent / 'visualization'))

def main(config):
    hidden_dim = config['hidden_dim']
    output_dir = Path(config['output_dir'])
    visualization_dir = Path(config['visualization_dir'])
    
    # Get visualization settings from config
    viz_config = config.get('visualization', {})
    create_gifs = viz_config.get('create_gifs', True)
    create_time_series = viz_config.get('create_time_series', True)
    
    # Labels for the multi-panel comparison
    labels = ["Full simulation"] + [f"Latent dimension {dim}" for dim in config['dimensions']]
    
    if create_gifs:
        print("Creating multi-panel comparison GIFs...")
        
        # Create output directory for GIFs
        gif_output_dir = output_dir / "figs"
        gif_output_dir.mkdir(exist_ok=True)
        
        for run_idx in range(config['num_runs']):
            # Build file paths for this run
            files = []
            
            # Full simulation file
            full_sim_file = output_dir / "full_simulation" / f"run{run_idx:04d}" / "wrfout_d01_0001-01-01_00:00:00"
            if full_sim_file.exists():
                files.append(str(full_sim_file))
            else:
                print(f"Warning: Full simulation file not found: {full_sim_file}")
                continue
            
            # Add files for each dimension
            for dim in config['dimensions']:
                dim_file = output_dir / f"dim_{dim}_hidden_{hidden_dim}" / f"run{run_idx:04d}" / "wrfout_d01_0001-01-01_00:00:00"
                if dim_file.exists():
                    files.append(str(dim_file))
                else:
                    print(f"Warning: Dimension {dim} file not found: {dim_file}")
                    continue
            
            if len(files) < 2:
                print(f"Warning: Not enough files found for run {run_idx}, skipping GIF creation")
                continue
            
            # Create output filename
            gif_filename = gif_output_dir / f"liquid_evolution_hidden_{hidden_dim}_run{run_idx:04d}.gif"
            
            # Call the multi-comparison GIF creation function
            
            from create_multi_comparison_gif import create_multi_comparison_gif
            
            success = create_multi_comparison_gif(
                files=files,
                output_path=str(gif_filename),
                labels=labels[:len(files)],  # Only use labels for files that exist
                vmin=viz_config.get('vmin', 0),
                vmax=viz_config.get('vmax', 2e-3),
                duration=viz_config.get('duration', 200)
            )

            if success:
                print(f"Created GIF: {gif_filename}")
            else:
                print(f"Failed to create GIF: {gif_filename}")

    
    if create_time_series:
        print("Creating time series plots...")
        
        # Create output directory for plots
        plot_output_dir = output_dir / "figs2"
        plot_output_dir.mkdir(exist_ok=True)
        
        for run_idx in range(config['num_runs']):
            # Build file paths for this run
            files = []
            
            # Full simulation file
            full_sim_file = output_dir / "full_simulation" / f"run{run_idx:04d}" / "wrfout_d01_0001-01-01_00:00:00"
            if full_sim_file.exists():
                files.append(str(full_sim_file))
            else:
                print(f"Warning: Full simulation file not found: {full_sim_file}")
                continue
            
            # Add files for each dimension
            for dim in config['dimensions']:
                dim_file = output_dir / f"dim_{dim}_hidden_{hidden_dim}" / f"run{run_idx:04d}" / "wrfout_d01_0001-01-01_00:00:00"
                if dim_file.exists():
                    files.append(str(dim_file))
                else:
                    print(f"Warning: Dimension {dim} file not found: {dim_file}")
                    continue
            
            # Add bad autoencoder file
            bad_file = output_dir / "bad_autoencoder" / f"run{run_idx:04d}" / "wrfout_d01_0001-01-01_00:00:00"
            if bad_file.exists():
                files.append(str(bad_file))
            else:
                print(f"Warning: Bad autoencoder file not found: {bad_file}")
                continue
            
            if len(files) < 2:
                print(f"Warning: Not enough files found for run {run_idx}, skipping time series plot creation")
                continue
            
            # Create output filename
            plot_filename = plot_output_dir / f"wrf_quantities_comparison_hidden_{hidden_dim}_run{run_idx:04d}.png"
            
            # Call the time series plotting function
            from plot_wrf_quantities import plot_wrf_quantities
            
            success = plot_wrf_quantities(
                files=files,
                output_path=str(plot_filename),
                labels=labels + ["Bad autoencoder"],  # Add bad autoencoder label
                time_range=viz_config.get('time_range', [0, 60])
            )
            
            if success:
                print(f"Created time series plot: {plot_filename}")
            else:
                print(f"Failed to create time series plot: {plot_filename}")


if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    main(config) 
