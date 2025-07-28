#!/usr/bin/env python3
"""
Create multi-panel comparison GIF from multiple WRF output files.

Usage:
    # Compare multiple WRF files
    python create_multi_comparison_gif.py --files file1.nc file2.nc file3.nc --labels "2-dim" "4-dim" "8-dim" --output comparison.gif
    
    # Compare with custom time ranges for each file
    python create_multi_comparison_gif.py --files file1.nc file2.nc --time-starts 0 50 --time-ends 40 90 --output comparison.gif
    
    # Compare with automatic layout
    python create_multi_comparison_gif.py --files *.nc --labels auto --output all_dims.gif
"""

import os
import sys
import argparse
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path
import glob
import math

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
        
        ds.close()
        return ql
        
    except Exception as e:
        print(f"Error loading {wrfout_file} at time {time_index}: {e}")
        return None

def get_time_ranges(files, time_starts=None, time_ends=None):
    """Determine time ranges for all files."""
    
    # Get max times for all files
    max_times = []
    for file in files:
        ds = xr.open_dataset(file, decode_times=False)
        max_times.append(len(ds.Time))
        ds.close()
    
    num_files = len(files)
    
    # Set default ranges
    if time_starts is None:
        time_starts = [0] * num_files
    if time_ends is None:
        time_ends = max_times.copy()
    
    # Ensure we have the right number of start/end times
    if len(time_starts) != num_files:
        if len(time_starts) == 1:
            time_starts = time_starts * num_files
        else:
            raise ValueError(f"Number of time_starts ({len(time_starts)}) must match number of files ({num_files})")
    
    if len(time_ends) != num_files:
        if len(time_ends) == 1:
            time_ends = time_ends * num_files
        else:
            raise ValueError(f"Number of time_ends ({len(time_ends)}) must match number of files ({num_files})")
    
    # Clamp to available data
    for i in range(num_files):
        time_starts[i] = max(0, min(time_starts[i], max_times[i] - 1))
        time_ends[i] = max(time_starts[i] + 1, min(time_ends[i], max_times[i]))
    
    # Make sure all ranges have the same length
    lengths = [end - start for start, end in zip(time_starts, time_ends)]
    min_length = min(lengths)
    
    for i in range(num_files):
        time_ends[i] = time_starts[i] + min_length
    
    print("Time ranges for files:")
    for i, (file, start, end) in enumerate(zip(files, time_starts, time_ends)):
        print(f"  {Path(file).name}: {start} to {end-1} ({min_length} frames)")
    
    return time_starts, time_ends

def calculate_subplot_layout(num_files):
    """Calculate optimal subplot layout for given number of files."""
    if num_files <= 0:
        return 1, 1
    elif num_files == 1:
        return 1, 1
    elif num_files == 2:
        return 1, 2
    elif num_files <= 4:
        return 2, 2
    elif num_files <= 6:
        return 2, 3
    elif num_files <= 9:
        return 3, 3
    elif num_files <= 12:
        return 3, 4
    else:
        # For larger numbers, try to keep it roughly square
        cols = math.ceil(math.sqrt(num_files))
        rows = math.ceil(num_files / cols)
        return rows, cols

def generate_auto_labels(files):
    """Generate automatic labels from filenames."""
    labels = []
    for file in files:
        filename = Path(file).stem
        # Try to extract dimension from filename
        if 'wrfout' in filename:
            # Look for parent directory that might contain dimension info
            parent = Path(file).parent.name
            if parent.isdigit():
                labels.append(f"{parent}-dim")
            else:
                labels.append(f"File {len(labels)+1}")
        else:
            labels.append(filename)
    return labels

def create_multi_comparison_gif(files, output_path, time_starts=None, time_ends=None,
                                labels=None, vmin=0, vmax=2e-3, duration=200):
    """Create a multi-panel comparison GIF from multiple WRF files."""
    
    # Check files exist
    missing_files = [f for f in files if not os.path.exists(f)]
    if missing_files:
        print(f"Files not found: {missing_files}")
        return False
    
    num_files = len(files)
    if num_files == 0:
        print("No files provided")
        return False
    
    # Generate automatic labels if needed
    if labels is None or (isinstance(labels, list) and len(labels) == 1 and labels[0] == 'auto'):
        labels = generate_auto_labels(files)
    elif len(labels) != num_files:
        print(f"Number of labels ({len(labels)}) must match number of files ({num_files})")
        return False
    
    # Get grid information (assuming all files have similar grids)
    x_stag, z_stag = load_sample_grid(files[0])
    
    # Get time ranges
    time_starts, time_ends = get_time_ranges(files, time_starts, time_ends)
    
    # Calculate subplot layout
    rows, cols = calculate_subplot_layout(num_files)
    
    # Set up figure with dynamic layout
    fig_width = 4 * cols
    fig_height = 3 * rows + 1.5  # More extra space for colorbar
    fig, axes = plt.subplots(rows, cols, figsize=(fig_width, fig_height))
    
    # Handle single subplot case
    if num_files == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
    
    # Load initial data and create plots
    pcms = []
    for i in range(num_files):
        data = load_data_at_time(files[i], time_starts[i])
        if data is None:
            print(f"Error loading initial data from {files[i]}")
            return False
        
        ax = axes[i]
        pcm = ax.pcolormesh(x_stag, z_stag, data, vmin=vmin, vmax=vmax, cmap='viridis')
        pcms.append(pcm)
        
        # Format axis
        ax.set_xlim(-1500, 1500)
        ax.set_ylim(0, 4000)
        ax.set_title(labels[i])
        
        # Only show y-labels on leftmost column
        if i % cols != 0:
            ax.set_yticklabels([])
        
        # Only show x-labels on bottom row
        if i < num_files - cols:
            ax.set_xticklabels([])
    
    # Hide unused subplots
    for i in range(num_files, len(axes)):
        axes[i].set_visible(False)
    
    
    fig.supylabel('Height (m)', y=0.56)
    # Leave more space at bottom for colorbar
    plt.tight_layout(rect=(0, 0.1, 1, 1))
    fig.supxlabel('Horizontal coordinate (m)', y=0.085, x=0.53)
    
    # Add colorbar at the bottom (much lower now)
    cbar_ax = fig.add_axes((0.18, 0.02, 0.7, 0.04))  # Positioned in the reserved bottom space
    cbar = plt.colorbar(pcms[0], cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Liquid water content (kg/kg)')
    
    # Create temporary directory for frames
    temp_dir = Path(output_path).parent / "temp_frames"
    temp_dir.mkdir(exist_ok=True)
    
    # Generate frames
    num_frames = time_ends[0] - time_starts[0]  # All should be the same length
    print(f"Creating {num_frames} comparison frames...")
    
    frame_paths = []
    for frame_idx in range(num_frames):
        print(f"Frame {frame_idx+1}/{num_frames}")
        
        # Load data for all files at this frame
        all_data_valid = True
        frame_data = []
        
        for i in range(num_files):
            time_idx = time_starts[i] + frame_idx
            data = load_data_at_time(files[i], time_idx)
            if data is not None:
                frame_data.append(data)
            else:
                all_data_valid = False
                break
        
        if all_data_valid:
            # Update all plots
            for i, (pcm, data) in enumerate(zip(pcms, frame_data)):
                pcm.set_array(data.ravel())
            
            # Save frame
            frame_path = temp_dir / f"frame_{frame_idx:04d}.png"
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
    parser = argparse.ArgumentParser(description='Create multi-panel comparison GIF from multiple WRF files')
    
    parser.add_argument('--files', nargs='+', required=True,
                       help='Paths to WRF output files (supports wildcards)')
    parser.add_argument('--time-starts', nargs='*', type=int, default=None,
                       help='Start time indices for each file (single value applies to all)')
    parser.add_argument('--time-ends', nargs='*', type=int, default=None,
                       help='End time indices for each file (single value applies to all)')
    parser.add_argument('--labels', nargs='*', default=None,
                       help='Labels for each panel (use "auto" for automatic labels)')
    parser.add_argument('--output', type=str, default='multi_comparison.gif',
                       help='Output GIF filename')
    parser.add_argument('--vmin', type=float, default=0,
                       help='Minimum value for color scale')
    parser.add_argument('--vmax', type=float, default=2e-3,
                       help='Maximum value for color scale')
    parser.add_argument('--duration', type=int, default=200,
                       help='Duration per frame in milliseconds')
    
    args = parser.parse_args()
    
    # Expand wildcards in file paths
    expanded_files = []
    for pattern in args.files:
        matches = glob.glob(pattern)
        if matches:
            expanded_files.extend(sorted(matches))
        else:
            expanded_files.append(pattern)  # Keep original if no matches
    
    # Remove duplicates while preserving order
    files = []
    seen = set()
    for f in expanded_files:
        if f not in seen:
            files.append(f)
            seen.add(f)
    
    print(f"Processing {len(files)} files:")
    for i, f in enumerate(files):
        print(f"  {i+1}: {f}")
    
    # Create comparison GIF
    success = create_multi_comparison_gif(
        files, args.output,
        time_starts=args.time_starts, time_ends=args.time_ends,
        labels=args.labels,
        vmin=args.vmin, vmax=args.vmax, duration=args.duration
    )
    
    if success:
        print(f"\nMulti-panel comparison GIF created successfully: {args.output}")
    else:
        print("Failed to create comparison GIF")
        sys.exit(1)

if __name__ == '__main__':
    main() 