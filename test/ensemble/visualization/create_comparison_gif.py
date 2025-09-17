#!/usr/bin/env python3
"""
Create side-by-side comparison GIF from two WRF output files.

Usage:
    # Compare two WRF files with different time ranges
    python create_comparison_gif.py --left-file file1.nc --right-file file2.nc --right-start 51 --right-end 90 --output comparison.gif
    
    # Compare with custom labels
    python create_comparison_gif.py --left-file file1.nc --right-file file2.nc --left-label "33-dim" --right-label "Ground Truth" --output comparison.gif
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
    print("ERROR: imageio not available. Install with 'pip install imageio' to create GIFs")
    HAS_IMAGEIO = False
    sys.exit(1)

# Try to import local modules, fall back to simplified versions if not available
try:
    from ppe_io import loop_run_paths, on_wrfout, WRFOUT_FILENAME
    from phys import g
    HAS_PPE_IO = True
except ImportError:
    print("Warning: ppe_io module not found, using simplified file handling")
    HAS_PPE_IO = False
    g = 9.81

def load_sample_grid(wrfout_file):
    """Load grid information from a WRF output file."""
    print(f"Loading grid info from: {wrfout_file}")
    ds = xr.open_dataset(wrfout_file, decode_times=False)
    
    # Get spatial coordinates
    z_stag = ds.PHB.isel(Time=0, south_north=0, west_east=0).values / g
    x_stag = np.arange(ds.west_east_stag.size) * ds.DX
    x_stag -= x_stag.mean()
    
    ds.close()
    return x_stag, z_stag

def load_data_at_time(wrfout_file, time_index):
    """Load cloud + rain data from a file at a specific time."""
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
        # ql[ql < 1e-5] = np.nan
        ds.close()
        
        return ql
        
    except Exception as e:
        print(f"Error loading {wrfout_file} at time {time_index}: {e}")
        return None

def get_time_ranges(left_file, right_file, left_start=None, left_end=None, 
                   right_start=None, right_end=None):
    """Determine time ranges for both files."""
    
    # Get max times for both files
    ds_left = xr.open_dataset(left_file, decode_times=False)
    ds_right = xr.open_dataset(right_file, decode_times=False)
    
    left_max_time = len(ds_left.Time)
    right_max_time = len(ds_right.Time)
    
    ds_left.close()
    ds_right.close()
    
    # Set default ranges
    if left_start is None:
        left_start = 0
    if left_end is None:
        left_end = left_max_time
    if right_start is None:
        right_start = 0
    if right_end is None:
        right_end = right_max_time
    
    # Clamp to available data
    left_start = max(0, min(left_start, left_max_time - 1))
    left_end = max(left_start + 1, min(left_end, left_max_time))
    right_start = max(0, min(right_start, right_max_time - 1))
    right_end = max(right_start + 1, min(right_end, right_max_time))
    
    # Make sure both ranges have the same length
    left_length = left_end - left_start
    right_length = right_end - right_start
    min_length = min(left_length, right_length)
    
    left_end = left_start + min_length
    right_end = right_start + min_length
    
    print(f"Left file time range: {left_start} to {left_end-1} ({min_length} frames)")
    print(f"Right file time range: {right_start} to {right_end-1} ({min_length} frames)")
    
    return left_start, left_end, right_start, right_end

def create_comparison_gif(left_file, right_file, output_path, 
                         left_start=None, left_end=None, right_start=None, right_end=None,
                         left_label="Left", right_label="Right", 
                         vmin=0, vmax=2e-3, duration=200):
    """Create a side-by-side comparison GIF from two WRF files."""
    
    # Check files exist
    if not os.path.exists(left_file):
        print(f"Left file not found: {left_file}")
        return False
    if not os.path.exists(right_file):
        print(f"Right file not found: {right_file}")
        return False
    
    # Get grid information (assuming both files have similar grids)
    x_stag, z_stag = load_sample_grid(left_file)
    
    # Get time ranges
    left_start, left_end, right_start, right_end = get_time_ranges(
        left_file, right_file, left_start, left_end, right_start, right_end)
    
    # Set up figure for side-by-side comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Load initial data for setup
    left_data = load_data_at_time(left_file, left_start)
    right_data = load_data_at_time(right_file, right_start)
    
    if left_data is None or right_data is None:
        print("Error loading initial data")
        return False
    
    # Create initial plots
    pcm1 = ax1.pcolormesh(x_stag, z_stag, left_data, vmin=vmin, vmax=vmax, cmap='viridis')
    pcm2 = ax2.pcolormesh(x_stag, z_stag, right_data, vmin=vmin, vmax=vmax, cmap='viridis')
    
    # Format axes
    for ax in [ax1, ax2]:
        ax.set_xlim(-1500, 1500)
        ax.set_ylim(0, 4000)
    
    # Remove y-tick labels on right axis only
    ax2.set_yticklabels([])
    
    # Add titles
    ax1.set_title(left_label)
    ax2.set_title(right_label)
    
    # Add figure-level ylabel first
    fig.supylabel('Height (m)')
    
    plt.tight_layout(rect=(0, 0.08, 1, 0.92))
    
    # Add xlabel with manual positioning
    fig.supxlabel('Horizontal Coordinate (m)', y=0.06, x=0.54)
    
    # Create dedicated axis for colorbar with precise positioning
    cbar_ax = fig.add_axes((0.19, 0.02, 0.7, 0.03))  # [left, bottom, width, height]
    cbar = plt.colorbar(pcm1, cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Liquid water content (kg/kg)')
    
    # Create temporary directory for frames
    temp_dir = Path(output_path).parent / "temp_frames"
    temp_dir.mkdir(exist_ok=True)
    
    # Generate frames
    num_frames = left_end - left_start
    print(f"Creating {num_frames} comparison frames...")
    
    frame_paths = []
    for i in range(num_frames):
        left_time = left_start + i
        right_time = right_start + i
        
        print(f"Frame {i+1}/{num_frames}: left_time={left_time}, right_time={right_time}")
        
        # Load data for this frame
        left_data = load_data_at_time(left_file, left_time)
        right_data = load_data_at_time(right_file, right_time)
        
        if left_data is not None and right_data is not None:
            # Update plots
            pcm1.set_array(left_data.ravel())
            pcm2.set_array(right_data.ravel())
            
            # Add frame number (positioned closer to subplot titles)
            # fig.suptitle(f'Frame {i+1}/{num_frames} (Left: t={left_time}, Right: t={right_time})', 
                        # fontsize=14, y=0.94)
            
            # Save frame
            frame_path = temp_dir / f"frame_{i:04d}.png"
            fig.savefig(frame_path, dpi=150, bbox_inches='tight')
            frame_paths.append(str(frame_path))
    
    plt.close(fig)
    
    # Create GIF
    if frame_paths:
        print(f"Creating GIF with {len(frame_paths)} frames...")
        try:
            images = []
            for frame_path in frame_paths:
                image = imageio.imread(frame_path)
                images.append(image)
            
            duration_sec = duration / 1000.0
            imageio.mimsave(output_path, images, duration=duration_sec, loop=0)
            print(f"GIF created successfully: {output_path}")
            
            # Clean up temporary files
            for frame_path in frame_paths:
                os.remove(frame_path)
            temp_dir.rmdir()
            
            return True
        except Exception as e:
            print(f"Error creating GIF: {e}")
            return False
    else:
        print("No frames generated")
        return False

def main():
    parser = argparse.ArgumentParser(description='Create side-by-side comparison GIF from two WRF files')
    
    parser.add_argument('--left-file', type=str, required=True,
                       help='Path to left WRF output file')
    parser.add_argument('--right-file', type=str, required=True,
                       help='Path to right WRF output file')
    parser.add_argument('--left-start', type=int, default=None,
                       help='Start time index for left file')
    parser.add_argument('--left-end', type=int, default=None,
                       help='End time index for left file')
    parser.add_argument('--right-start', type=int, default=None,
                       help='Start time index for right file')
    parser.add_argument('--right-end', type=int, default=None,
                       help='End time index for right file')
    parser.add_argument('--left-label', type=str, default='Left',
                       help='Label for left panel')
    parser.add_argument('--right-label', type=str, default='Right',
                       help='Label for right panel')
    parser.add_argument('--output', type=str, default='comparison.gif',
                       help='Output GIF filename')
    parser.add_argument('--vmin', type=float, default=0,
                       help='Minimum value for color scale')
    parser.add_argument('--vmax', type=float, default=2e-3,
                       help='Maximum value for color scale')
    parser.add_argument('--duration', type=int, default=200,
                       help='Duration per frame in milliseconds')
    
    args = parser.parse_args()
    
    # Create comparison GIF
    success = create_comparison_gif(
        args.left_file, args.right_file, args.output,
        left_start=args.left_start, left_end=args.left_end,
        right_start=args.right_start, right_end=args.right_end,
        left_label=args.left_label, right_label=args.right_label,
        vmin=args.vmin, vmax=args.vmax, duration=args.duration
    )
    
    if success:
        print(f"\nComparison GIF created successfully: {args.output}")
    else:
        print("Failed to create comparison GIF")
        sys.exit(1)

if __name__ == '__main__':
    main() 