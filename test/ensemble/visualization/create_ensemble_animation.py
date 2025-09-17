#!/usr/bin/env python3
"""
Create ensemble animation from WRF output files.

Usage:
    # Create PNG frames from ensemble directory
    python create_ensemble_animation.py --ensemble-path /path/to/ensemble --output-dir ./fig
    
    # Create PNG frames from specific files
    python create_ensemble_animation.py --wrfout-files file1.nc file2.nc --output-dir ./fig
    
    # Create PNG frames AND animated GIF
    python create_ensemble_animation.py --ensemble-path /path/to/ensemble --create-gif
    
    # Just create GIF from existing PNGs (no WRF files needed)
    python create_ensemble_animation.py --wrfout-files dummy --create-gif --output-dir ./fig
"""

import os
import sys
import argparse
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path
import glob

# Try to import imageio for GIF creation
try:
    import imageio
    HAS_IMAGEIO = True
except ImportError:
    print("Warning: imageio not available. Install with 'pip install imageio' to create GIFs")
    HAS_IMAGEIO = False

# Try to import local modules, fall back to simplified versions if not available
try:
    from ppe_io import loop_run_paths, on_wrfout, WRFOUT_FILENAME
    from phys import g
    HAS_PPE_IO = True
except ImportError:
    print("Warning: ppe_io module not found, using simplified file handling")
    HAS_PPE_IO = False
    g = 9.81
    WRFOUT_FILENAME = 'wrfout_d01_0001-01-01_00:00:00'

def find_wrfout_files(ensemble_path):
    """Find all WRF output files in ensemble run directories."""
    run_dirs = []
    if os.path.exists(ensemble_path):
        for item in sorted(os.listdir(ensemble_path)):
            if item.startswith('run'):
                run_dir = os.path.join(ensemble_path, item)
                wrfout_path = os.path.join(run_dir, WRFOUT_FILENAME)
                if os.path.exists(wrfout_path):
                    run_dirs.append(wrfout_path)
    return run_dirs

def load_sample_grid(wrfout_file):
    """Load grid information from a sample WRF output file."""
    print(f"Loading grid info from: {wrfout_file}")
    print(f"WRF output file: {wrfout_file}")
    ds = xr.open_dataset(wrfout_file, decode_times=False)
    
    # Get spatial coordinates
    z_stag = ds.PHB.isel(Time=0, south_north=0, west_east=0).values / g
    x_stag = np.arange(ds.west_east_stag.size) * ds.DX
    x_stag -= x_stag.mean()
    
    # Get a sample data array for initial plotting
    if len(ds.south_north) > 1:
        sample_data = ds.QCLOUD.isel(Time=3, south_north=0).values
    else:
        sample_data = ds.QCLOUD.isel(Time=3).squeeze().values
    
    ds.close()
    return x_stag, z_stag, sample_data

def load_data_at_time(wrfout_files, time_index, threshold=1e-5):
    """Load cloud + rain data from all files at a specific time."""
    data_list = []
    
    for wrfout_file in wrfout_files:
        try:
            ds = xr.open_dataset(wrfout_file, decode_times=False)
            
            # Handle both 3D and 4D data (with/without south_north dimension)
            qcloud = ds.QCLOUD.isel(Time=time_index)
            qrain = ds.QRAIN.isel(Time=time_index)
            
            # Combine cloud and rain water
            ql = (qcloud + qrain).values
            
            # Remove singleton dimensions and ensure 2D
            ql = np.squeeze(ql)
            if ql.ndim != 2:
                print(f"Warning: Unexpected data shape {ql.shape} in {wrfout_file}")
                # Take the first 2D slice if still multidimensional
                while ql.ndim > 2:
                    ql = ql[0]
            
            # Set threshold for visualization
            ql[ql < threshold] = np.nan
            data_list.append(ql)
            ds.close()
            
        except Exception as e:
            print(f"Error loading {wrfout_file} at time {time_index}: {e}")
            # Create dummy data to maintain consistent list length
            if data_list:
                dummy_data = np.full_like(data_list[0], np.nan)
                data_list.append(dummy_data)
    
    return data_list

def setup_figure(n_files, x_stag, z_stag, sample_data, vmin=0, vmax=2e-3):
    """Set up the figure with appropriate subplot grid."""
    # Determine grid layout
    if n_files <= 4:
        p_width, p_height = min(n_files, 2), (n_files + 1) // 2
    elif n_files <= 8:
        p_width, p_height = 4, 2
    elif n_files <= 12:
        p_width, p_height = 4, 3
    elif n_files <= 16:
        p_width, p_height = 4, 4
    else:
        # For larger ensembles, use square-ish grid
        p_width = int(np.ceil(np.sqrt(n_files)))
        p_height = int(np.ceil(n_files / p_width))
    
    print(f"Creating {p_width}x{p_height} grid for {n_files} files")
    
    # Create figure
    gs_kw = dict(width_ratios=[1]*p_width, height_ratios=[1]*p_height)
    fig, axes = plt.subplots(p_height, p_width, 
                            figsize=(4*p_width, 3*p_height),
                            gridspec_kw=gs_kw,
                            layout="constrained")
    
    # Flatten axes for easier indexing
    if p_height == 1 and p_width == 1:
        axes_flat = [axes]
    else:
        axes_flat = np.array(axes).flatten()
    
    # Create initial plots
    pcms = []
    for i in range(n_files):
        ax = axes_flat[i]
        pcm = ax.pcolormesh(x_stag, z_stag, sample_data, vmin=vmin, vmax=vmax, cmap='viridis')
        pcms.append(pcm)
        
        # Formatting
        ax.set_xlim(-1500, 1500)
        ax.set_ylim(0, 4000)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.05, 0.975, f'{i:03d}', ha='left', va='top', 
                transform=ax.transAxes, color='white', fontweight='bold')
    
    # Hide unused subplots
    for i in range(n_files, len(axes_flat)):
        axes_flat[i].set_visible(False)
    
    return fig, pcms

def create_animation(wrfout_files, output_dir, vmin=0, vmax=2e-3, 
                    time_range=None, file_prefix="ensemble", threshold=1e-5):
    """Create animation frames from WRF output files."""
    
    if not wrfout_files:
        print("No WRF output files found!")
        return
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load grid information from first file
    x_stag, z_stag, sample_data = load_sample_grid(wrfout_files[0])
    
    # Determine time range
    ds_sample = xr.open_dataset(wrfout_files[0], decode_times=False)
    max_time = len(ds_sample.Time)
    ds_sample.close()
    
    if time_range is None:
        time_range = range(max_time)
    else:
        time_range = range(min(time_range[0], max_time), 
                          min(time_range[1], max_time))
    
    print(f"Creating animation for times {time_range.start} to {time_range.stop-1}")
    
    # Set up figure
    fig, pcms = setup_figure(len(wrfout_files), x_stag, z_stag, sample_data, vmin, vmax)
    
    # Create frames
    for time_idx in time_range:
        print(f'Creating frame for time {time_idx}')
        
        # Load data for this time step
        data_list = load_data_at_time(wrfout_files, time_idx, threshold)
        
        # Update plots
        for pcm, data in zip(pcms, data_list):
            if data is not None:
                pcm.set_array(data.ravel())
        
        # Save frame
        output_file = os.path.join(output_dir, f'{file_prefix}.{time_idx:04d}.png')
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
    
    plt.close(fig)
    print(f"Animation frames saved to {output_dir}")

def create_gif(output_dir, file_prefix="ensemble", gif_name=None, duration=200, loop=0):
    """Create an animated GIF from PNG frames using imageio."""
    
    if not HAS_IMAGEIO:
        print("imageio not available - cannot create GIF")
        return False
    
    # Find all PNG files
    png_pattern = os.path.join(output_dir, f"{file_prefix}.*.png")
    png_files = sorted(glob.glob(png_pattern))
    
    if not png_files:
        print(f"No PNG files found matching pattern: {png_pattern}")
        return False
    
    print(f"Found {len(png_files)} PNG files")
    
    # Set default GIF name
    if gif_name is None:
        gif_name = f"{file_prefix}_animation.gif"
    
    gif_path = os.path.join(output_dir, gif_name)
    
    # Create GIF using imageio
    print(f"Creating GIF: {gif_path}")
    try:
        # Load all images
        images = []
        for png_file in png_files:
            try:
                image = imageio.imread(png_file)
                images.append(image)
            except Exception as e:
                print(f"Error loading {png_file}: {e}")
        
        if not images:
            print("No valid images loaded")
            return False
        
        # Convert duration from milliseconds to seconds for imageio
        duration_sec = duration / 1000.0
        
        # Create GIF using mimsave
        imageio.mimsave(gif_path, images, duration=duration_sec, loop=loop)
        
        print(f"GIF created successfully: {gif_path}")
        return True
    except Exception as e:
        print(f"Error creating GIF: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Create ensemble animation from WRF output')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ensemble-path', type=str,
                      help='Path to ensemble directory containing run* subdirectories')
    group.add_argument('--wrfout-files', nargs='+', type=str,
                      help='List of WRF output files')
    
    parser.add_argument('--output-dir', type=str, default='./fig',
                       help='Output directory for animation frames')
    parser.add_argument('--vmin', type=float, default=0,
                       help='Minimum value for color scale')
    parser.add_argument('--vmax', type=float, default=2e-3,
                       help='Maximum value for color scale')
    parser.add_argument('--time-start', type=int, default=None,
                       help='Start time index')
    parser.add_argument('--time-end', type=int, default=None,
                       help='End time index')
    parser.add_argument('--file-prefix', type=str, default='ensemble',
                       help='Prefix for output files')
    parser.add_argument('--create-gif', action='store_true',
                       help='Create animated GIF from PNG frames')
    parser.add_argument('--gif-name', type=str, default=None,
                       help='Name for output GIF file')
    parser.add_argument('--gif-duration', type=int, default=200,
                       help='Duration per frame in milliseconds for GIF')
    parser.add_argument('--threshold', type=float, default=1e-5,
                       help='Threshold for removing small values from data')
    
    args = parser.parse_args()
    
    # Get WRF output files
    if args.ensemble_path:
        wrfout_files = find_wrfout_files(args.ensemble_path)
        if not wrfout_files:
            print(f"No WRF output files found in {args.ensemble_path}")
            sys.exit(1)
    else:
        wrfout_files = args.wrfout_files
        # Check that files exist
        for f in wrfout_files:
            if not os.path.exists(f):
                print(f"File not found: {f}")
                sys.exit(1)
    
    print(f"Found {len(wrfout_files)} WRF output files")
    
    # Set time range
    time_range = None
    if args.time_start is not None or args.time_end is not None:
        start = args.time_start or 0
        end = args.time_end or 181  # Default from your notebook
        time_range = (start, end)
    
    # Create animation
    create_animation(wrfout_files, args.output_dir, 
                    vmin=args.vmin, vmax=args.vmax,
                    time_range=time_range, file_prefix=args.file_prefix,
                    threshold=args.threshold)
    
    # Create GIF if requested
    if args.create_gif:
        create_gif(args.output_dir, 
                  file_prefix=args.file_prefix,
                  gif_name=args.gif_name,
                  duration=args.gif_duration)

if __name__ == '__main__':
    main() 