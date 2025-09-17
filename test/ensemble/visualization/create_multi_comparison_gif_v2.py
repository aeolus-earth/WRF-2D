#!/usr/bin/env python3
"""
Create multi-panel comparison GIF from multiple WRF output files with different start times.

Usage:
    # Compare multiple WRF files with different start times
    python create_multi_comparison_gif_v2.py --files file1.nc file2.nc file3.nc --start-times 0 5 10 --labels "2-dim" "4-dim" "8-dim" --output comparison.gif
    
    # Compare with automatic start time detection from restart runs
    python create_multi_comparison_gif_v2.py --files *.nc --auto-start-times --labels auto --output all_dims.gif
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
import re

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

def extract_start_time_from_filename(filename):
    """Extract start time from directory name like 'run0001_base_0005' or 'run0001_base_0100'."""
    filepath = Path(filename)
    # Look for pattern like _0005, _0010, _0100, etc. in the directory name
    dirname = filepath.parent.name
    match = re.search(r'_(\d{4})$', dirname)
    if match:
        time_code = int(match.group(1))
        # Convert HHMM format to minutes
        hours = time_code // 100
        minutes = time_code % 100
        total_minutes = hours * 60 + minutes
        return total_minutes
    return 0


def format_time_label(minutes):
    """Format minutes into a readable time label (e.g., 100 -> '1h 00m')."""
    hours = minutes // 100
    mins = minutes % 100
    if hours > 0:
        return f"{hours}h {mins:02d}m"
    else:
        return f"{mins}m"


def generate_auto_labels(files, start_times=None):
    """Generate automatic labels from filenames and start times."""
    labels = []
    for i, file in enumerate(files):
        # Check if this is the first file (original run)
        if i == 0:
            labels.append("Full simulation")
        else:
            # Use start time as label for restart runs
            if start_times is not None and i < len(start_times):
                time_label = format_time_label(start_times[i])
                labels.append(f"Restart at {time_label}")
            else:
                labels.append(f"File {len(labels)+1}")
    return labels

def get_time_ranges_with_start_times(files, start_times=None, time_ends=None, auto_start_times=False):
    """Determine time ranges for all files with different start times."""
    
    num_files = len(files)
    
    # Get max times for all files
    max_times = []
    for file in files:
        ds = xr.open_dataset(file, decode_times=False)
        max_times.append(len(ds.Time))
        ds.close()
    
    # Handle start times
    if auto_start_times:
        # Extract start times from filenames
        start_times = [extract_start_time_from_filename(f) for f in files]
        print(f"Auto-detected start times: {start_times}")
    elif start_times is None:
        start_times = [0] * num_files
    
    # Set default end times
    if time_ends is None:
        time_ends = max_times.copy()
    
    # Ensure we have the right number of start/end times
    if len(start_times) != num_files:
        if len(start_times) == 1:
            start_times = start_times * num_files
        else:
            raise ValueError(f"Number of start_times ({len(start_times)}) must match number of files ({num_files})")
    
    if len(time_ends) != num_files:
        if len(time_ends) == 1:
            time_ends = time_ends * num_files
        else:
            raise ValueError(f"Number of time_ends ({len(time_ends)}) must match number of files ({num_files})")
    
    # All files should have the same length (181 timesteps = 0 to 90 minutes inclusive)
    expected_timesteps = 181
    expected_minutes = (expected_timesteps - 1) / 2.0  # 90 minutes (timesteps 0-180)
    
    # Verify all files have the expected length
    for i, max_time in enumerate(max_times):
        if max_time != expected_timesteps:
            print(f"Warning: File {i} has {max_time} timesteps, expected {expected_timesteps}")
    
    # Set all end times to the full available time
    time_ends = [expected_minutes] * num_files
    
    # Clamp start times to available data
    for i in range(num_files):
        start_times[i] = max(0, min(start_times[i], expected_minutes - 0.5))
    
    # Adjust start times for restart runs (they don't include the restart time point)
    # For restart runs (i > 0), shift start time by half a timestep (0.5 minutes) to account
    # for the fact that their first data point corresponds to start_time + 0.5 minutes
    for i in range(1, num_files):  # Skip the first file (full simulation)
        start_times[i] += 0.5
    
    # Calculate the overall time range (from earliest start to latest end)
    overall_start = min(start_times)
    overall_end = max(time_ends)
    overall_length = overall_end - overall_start
    
    print("Time ranges for files:")
    for i, (file, start, end) in enumerate(zip(files, start_times, time_ends)):
        print(f"  {Path(file).name}: {start} to {end} (starts at {start_times[i]} minutes)")
    
    print(f"Overall time range: {overall_start} to {overall_end} ({overall_length} minutes)")
    
    return start_times, time_ends, overall_start, overall_end

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

def create_multi_comparison_gif_v2(files, output_path, start_times=None, time_ends=None,
                                   labels=None, vmin=0, vmax=2e-3, duration=200, auto_start_times=False):
    """Create a multi-panel comparison GIF from multiple WRF files with different start times."""
    
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
        labels = generate_auto_labels(files, start_times)
    elif len(labels) != num_files:
        print(f"Number of labels ({len(labels)}) must match number of files ({num_files})")
        return False
    
    # Get grid information (assuming all files have similar grids)
    x_stag, z_stag = load_sample_grid(files[0])
    
    # Get time ranges with start times
    start_times, time_ends, overall_start, overall_end = get_time_ranges_with_start_times(
        files, start_times, time_ends, auto_start_times
    )
    
    # Convert time ranges from minutes to timesteps (each timestep is 30 seconds = 0.5 minutes)
    start_times_timesteps = [int(st * 2) for st in start_times]
    time_ends_timesteps = [int(te * 2) for te in time_ends]
    overall_start_timesteps = int(overall_start * 2)
    overall_end_timesteps = int(overall_end * 2) + 1
    
    # Calculate subplot layout
    rows, cols = calculate_subplot_layout(num_files)
    
    # Set up figure with dynamic layout
    fig_width = 4 * cols
    fig_height = 3 * rows + 2.0  # Extra space for suptitle and colorbar
    fig, axes = plt.subplots(rows, cols, figsize=(fig_width, fig_height))
    
    # Handle single subplot case
    if num_files == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
    
    # Load initial data and create plots
    pcms = []
    for i in range(num_files):
        # Check if this simulation has started at the overall start time
        if overall_start >= start_times[i]:
            # Simulation has started, load data
            local_time = overall_start - start_times[i]
            data = load_data_at_time(files[i], local_time)
            if data is None:
                print(f"Error loading initial data from {files[i]}")
                return False
        else:
            # Simulation hasn't started yet, use NaN data
            # Create NaN data with the same shape as the grid
            data = np.full((len(z_stag)-1, len(x_stag)-1), np.nan)  # Match the grid shape
        
        ax = axes[i]
        pcm = ax.pcolormesh(x_stag, z_stag, data, vmin=vmin, vmax=vmax, cmap='viridis')
        pcms.append(pcm)
        
        # Format axis
        ax.set_xlim(-1500, 1500)
        ax.set_ylim(0, 4000)
        # Add start time to title
        start_time_label = format_time_label(start_times[i] - 0.5)
        # ax.set_title(f"{labels[i]}\n(Started at {start_time_label})")
        if i == 0:
            ax.set_title(f"Full simulation")
        else:
            ax.set_title(f"Restart from {start_time_label}")
        
        # Only show y-labels on leftmost column
        if i % cols != 0:
            ax.set_yticklabels([])
        
        # Only show x-labels on bottom row
        if i < num_files - cols:
            ax.set_xticklabels([])
    
    # Hide unused subplots
    for i in range(num_files, len(axes)):
        axes[i].set_visible(False)
    
    fig.supylabel('Height (m)', y=0.53)
    # Leave space at top for suptitle and at bottom for colorbar
    plt.tight_layout(rect=(0, 0.1, 1, 0.95))
    fig.supxlabel('Horizontal coordinate (m)', y=0.085, x=0.53)
    
    # Add colorbar at the bottom (much lower now)
    cbar_ax = fig.add_axes((0.18, 0.02, 0.7, 0.04))  # Positioned in the reserved bottom space
    cbar = plt.colorbar(pcms[0], cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Liquid water content (kg/kg)')
    
    # Create temporary directory for frames
    temp_dir = Path(output_path).parent / "temp_frames"
    temp_dir.mkdir(exist_ok=True)
    
    # Generate frames
    num_frames = overall_end_timesteps - overall_start_timesteps
    print(f"Creating {num_frames} comparison frames...")
    
    frame_paths = []
    for frame_idx in range(num_frames):
        current_time_timesteps = overall_start_timesteps + frame_idx
        current_time_minutes = current_time_timesteps / 2.0  # Convert back to minutes
        print(f"Frame {frame_idx+1}/{num_frames} (time: {current_time_minutes:.1f} minutes)")
        
        # Load data for all files at this frame
        frame_data = []
        
        for i in range(num_files):
            # Check if this simulation has started at the current time
            if current_time_minutes >= start_times[i]:
                # Simulation has started, load data
                local_time = current_time_minutes - start_times[i]
                local_time_timesteps = int(local_time * 2)  # Convert to timesteps
                if local_time_timesteps < time_ends_timesteps[i] - start_times_timesteps[i]:  # Check if within local time range
                    data = load_data_at_time(files[i], local_time_timesteps)
                    if data is not None:
                        frame_data.append(data)
                    else:
                        # Use NaN data if file failed to load
                        print(f"Warning: Failed to load data from {files[i]} at time {current_time_minutes:.1f} minutes, using NaN")
                        data = np.full((len(z_stag)-1, len(x_stag)-1), np.nan)
                        frame_data.append(data)
                else:
                    # Beyond local time range, use NaN data
                    data = np.full((len(z_stag)-1, len(x_stag)-1), np.nan)
                    frame_data.append(data)
            else:
                # Simulation hasn't started yet, use NaN data
                data = np.full((len(z_stag)-1, len(x_stag)-1), np.nan)
                frame_data.append(data)
        
        # Always create the frame, even if some data is missing
        if len(frame_data) == num_files:
            # Update all plots
            for i, (pcm, data) in enumerate(zip(pcms, frame_data)):
                pcm.set_array(data.ravel())
            
            # Update suptitle with current time
            current_time_label = format_time_label(current_time_minutes)
            # fig.suptitle(f"Time: {current_time_label}", fontsize=16, y=0.96)
            fig.suptitle(f"Time: {current_time_label}", fontsize=16, y=0.96)
            
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
            # for frame_path in frame_paths:
            #     os.remove(frame_path)
            # temp_dir.rmdir()
            
            return True
        except Exception as e:
            print(f"Error creating GIF: {e}")
            return False
    else:
        print("No frames generated")
        return False

def main():
    parser = argparse.ArgumentParser(description='Create multi-panel comparison GIF from multiple WRF files with different start times')
    
    parser.add_argument('--files', nargs='+', required=True,
                       help='Paths to WRF output files (supports wildcards)')
    parser.add_argument('--start-times', nargs='*', type=int, default=None,
                       help='Start times in minutes for each file (single value applies to all)')
    parser.add_argument('--time-ends', nargs='*', type=int, default=None,
                       help='End time indices for each file (single value applies to all)')
    parser.add_argument('--labels', nargs='*', default=None,
                       help='Labels for each panel (use "auto" for automatic labels)')
    parser.add_argument('--output', type=str, default='multi_comparison_v2.gif',
                       help='Output GIF filename')
    parser.add_argument('--vmin', type=float, default=0,
                       help='Minimum value for color scale')
    parser.add_argument('--vmax', type=float, default=2e-3,
                       help='Maximum value for color scale')
    parser.add_argument('--duration', type=int, default=200,
                       help='Duration per frame in milliseconds')
    parser.add_argument('--auto-start-times', action='store_true',
                       help='Automatically detect start times from filenames (e.g., _0000, _0010)')
    
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
    success = create_multi_comparison_gif_v2(
        files, args.output,
        start_times=args.start_times, time_ends=args.time_ends,
        labels=args.labels,
        vmin=args.vmin, vmax=args.vmax, duration=args.duration,
        auto_start_times=args.auto_start_times
    )
    
    if success:
        print(f"\nMulti-panel comparison GIF created successfully: {args.output}")
    else:
        print("Failed to create comparison GIF")
        sys.exit(1)

if __name__ == '__main__':
    main() 