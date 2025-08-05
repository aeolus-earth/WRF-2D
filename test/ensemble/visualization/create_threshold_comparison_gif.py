#!/usr/bin/env python3
"""
Create multi-panel comparison GIF showing different threshold effects on the same WRF output.

Usage:
    # Compare different thresholds for a single file
    python create_threshold_comparison_gif.py --file file.nc --thresholds 1e-5 1e-6 1e-7 1e-8 --output threshold_comparison.gif
    
    # Compare with custom time range
    python create_threshold_comparison_gif.py --file file.nc --time-start 0 --time-end 100 --output threshold_comparison.gif
    
    # Compare with automatic threshold generation
    python create_threshold_comparison_gif.py --file file.nc --auto-thresholds --output threshold_comparison.gif
"""

import os
import sys
import argparse
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.cm as cm
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

def load_data_at_time_with_threshold(wrfout_file, time_index, threshold=1e-5, previous_threshold=None):
    """Load cloud + rain data from a file at a specific time with threshold applied."""
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
        
        # Apply threshold
        ql[ql < threshold] = np.nan
        # print("ql", ql.shape)

        # If we have a previous threshold, create a mask for points that were NaN in previous threshold
        red_mask = None
        if previous_threshold is not None:
            # Create data with previous threshold
            ql_prev = (qcloud + qrain).values
            # print("ql_prev", ql_prev.shape)
            ql_prev = np.squeeze(ql_prev)
            while ql_prev.ndim > 2:
                ql_prev = ql_prev[0]
            
            # Apply previous threshold to get the "before" state
            ql_prev_thresholded = ql_prev.copy()
            ql_prev_thresholded[ql_prev_thresholded < previous_threshold] = np.nan
            
            # Find points that were NaN with previous threshold but are not NaN now
            prev_nan_mask = np.isnan(ql_prev_thresholded)
            # print("prev_nan_mask", np.sum(prev_nan_mask))
            current_nan_mask = np.isnan(ql)
            # print("current_nan_mask", np.sum(current_nan_mask))
            
            # Red points: were NaN before, but not NaN now (threshold got more permissive)
            red_mask = prev_nan_mask & ~current_nan_mask
            
            # Debug prints
            # print(f"Threshold: {threshold:.2e}, Previous: {previous_threshold:.2e}")
            # print(f"Data range: {np.nanmin(ql_prev):.2e} to {np.nanmax(ql_prev):.2e}")
            # print(f"Points below prev threshold: {np.sum(ql_prev < previous_threshold)}")
            # print(f"Points below current threshold: {np.sum(ql_prev < threshold)}")
            # print(f"Points in between: {np.sum((ql_prev >= threshold) & (ql_prev < previous_threshold))}")
            # print(f"Red mask sum: {np.sum(red_mask) if red_mask is not None else 0}")
            # print("---")
        
        ds.close()
        return ql, red_mask
        
    except Exception as e:
        print(f"Error loading {wrfout_file} at time {time_index}: {e}")
        return None, None

def generate_threshold_labels(thresholds):
    """Generate labels for threshold panels."""
    labels = []
    for threshold in thresholds:
        if threshold >= 1e-3:
            label = f"{threshold:.0e}"
        elif threshold >= 1e-6:
            label = f"{threshold:.1e}"
        else:
            label = f"{threshold:.2e}"
        labels.append(f"Threshold: {label}")
    return labels

def calculate_subplot_layout(num_thresholds):
    """Calculate optimal subplot layout for given number of thresholds."""
    if num_thresholds <= 0:
        return 1, 1
    elif num_thresholds == 1:
        return 1, 1
    elif num_thresholds == 2:
        return 1, 2
    elif num_thresholds <= 4:
        return 2, 2
    elif num_thresholds <= 6:
        return 2, 3
    elif num_thresholds <= 9:
        return 3, 3
    elif num_thresholds <= 12:
        return 3, 4
    else:
        # For larger numbers, try to keep it roughly square
        cols = math.ceil(math.sqrt(num_thresholds))
        rows = math.ceil(num_thresholds / cols)
        return rows, cols

def create_threshold_comparison_gif(wrfout_file, output_path, thresholds, 
                                   time_start=0, time_end=None, 
                                   vmin=0, vmax=2e-3, duration=200, show_red_markers=True):
    """Create a multi-panel comparison GIF showing different threshold effects."""
    
    # Check file exists
    if not os.path.exists(wrfout_file):
        print(f"File not found: {wrfout_file}")
        return False
    
    num_thresholds = len(thresholds)
    if num_thresholds == 0:
        print("No thresholds provided")
        return False
    
    # Generate labels
    labels = generate_threshold_labels(thresholds)
    
    # Get grid information
    x_stag, z_stag = load_sample_grid(wrfout_file)
    
    # Get time range
    ds = xr.open_dataset(wrfout_file, decode_times=False)
    max_time = len(ds.Time)
    ds.close()
    
    if time_end is None:
        time_end = max_time
    else:
        time_end = min(time_end, max_time)
    
    time_start = max(0, min(time_start, max_time - 1))
    time_end = max(time_start + 1, time_end)
    
    print(f"Time range: {time_start} to {time_end-1} ({time_end - time_start} frames)")
    
    # Calculate subplot layout
    rows, cols = calculate_subplot_layout(num_thresholds)
    
    # Set up figure with dynamic layout
    fig_width = 4 * cols
    fig_height = 3 * rows + 1.5  # More extra space for colorbar
    fig, axes = plt.subplots(rows, cols, figsize=(fig_width, fig_height))
    
    # Handle single subplot case
    if num_thresholds == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
    
    # Load initial data and create plots
    pcms = []
    red_pcms = []
    for i, threshold in enumerate(thresholds):
        # Get previous threshold for red marking
        prev_threshold = thresholds[i-1] if i > 0 else None
        
        data, red_mask = load_data_at_time_with_threshold(wrfout_file, time_start, threshold, prev_threshold)
        # print("red_mask", np.sum(red_mask))
        if data is None:
            print(f"Error loading initial data with threshold {threshold}")
            return False
        
        ax = axes[i]
        
        # Create combined data with red markers
        if show_red_markers:
            # Create combined data where red points get a special value
            combined_data = data.copy()
            # Use a value outside the normal range for red points
            red_value = vmax + (vmax - vmin) * 0.1  # 10% above vmax
            combined_data[red_mask] = red_value
            
            print(f"Red points: {np.sum(red_mask)} points")
            
            # Create custom colormap using lambda function
            # import matplotlib.pyplot as plt
            
            # Lambda function for custom colormap
            print(combined_data[50, 50:60])
            viridis = cm.get_cmap('viridis', 256)
            newcolors = viridis(np.linspace(0, 1, 256))
            red = np.array([1, 0/256, 0/256, 1])
            newcolors[-10:, :] = red
            newcmp = ListedColormap(newcolors)
            print("using newcmp")

            # custom_cmap = lambda x: [1.0, 0.0, 0.0, 0.8] if x >= 1.0 else plt.cm.viridis(x)
            
            # Plot with custom colormap
            pcm = ax.pcolormesh(x_stag, z_stag, combined_data, 
                               vmin=vmin, vmax=vmax, cmap=newcmp, zorder=1)
            pcms.append(pcm)
            red_pcms.append(None)  # No separate red overlay needed
        else:
            # Normal plotting without red markers
            print("using viridis")
            pcm = ax.pcolormesh(x_stag, z_stag, data, vmin=vmin, vmax=vmax, cmap='viridis', zorder=1)
            pcms.append(pcm)
            red_pcms.append(None)
        
        # Format axis
        ax.set_xlim(-1500, 1500)
        ax.set_ylim(0, 4000)
        ax.set_title(labels[i])
        
        # Only show y-labels on leftmost column
        if i % cols != 0:
            ax.set_yticklabels([])
        
        # Only show x-labels on bottom row
        if i < num_thresholds - cols:
            ax.set_xticklabels([])
    
    # Hide unused subplots
    for i in range(num_thresholds, len(axes)):
        axes[i].set_visible(False)
    
    # Add overall labels
    fig.supylabel('Height (m)', y=0.56)
    plt.tight_layout(rect=(0, 0.1, 1, 1))
    fig.supxlabel('Horizontal coordinate (m)', y=0.085, x=0.53)
    
    # Add colorbar at the bottom
    cbar_ax = fig.add_axes((0.18, 0.02, 0.7, 0.04))
    cbar = plt.colorbar(pcms[0], cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Liquid water content (kg/kg)')
    
    # Create temporary directory for frames
    temp_dir = Path(output_path).parent / "temp_threshold_frames"
    temp_dir.mkdir(exist_ok=True)
    
    # Generate frames
    num_frames = time_end - time_start
    print(f"Creating {num_frames} threshold comparison frames...")
    
    frame_paths = []
    for frame_idx in range(num_frames):
        time_idx = time_start + frame_idx
        print(f"Frame {frame_idx+1}/{num_frames} (time {time_idx})")
        
        # Load data for all thresholds at this frame
        all_data_valid = True
        frame_data = []
        frame_red_masks = []
        
        for i, threshold in enumerate(thresholds):
            # Get previous threshold for red marking
            prev_threshold = thresholds[i-1] if i > 0 else None
            
            data, red_mask = load_data_at_time_with_threshold(wrfout_file, time_idx, threshold, prev_threshold)
            if data is not None:
                frame_data.append(data)
                frame_red_masks.append(red_mask)
            else:
                all_data_valid = False
                break
        
        if all_data_valid:
            # Update all plots
            for i, (pcm, data) in enumerate(zip(pcms, frame_data)):
                if show_red_markers and frame_red_masks[i] is not None and np.any(frame_red_masks[i]):
                    # Create combined data with red markers
                    combined_data = data.copy()
                    red_value = vmax + (vmax - vmin) * 0.1
                    combined_data[frame_red_masks[i]] = red_value
                    pcm.set_array(combined_data.ravel())
                else:
                    # Normal data update
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
    parser = argparse.ArgumentParser(description='Create multi-panel comparison GIF showing different threshold effects')
    
    parser.add_argument('--file', type=str, required=True,
                       help='Path to WRF output file')
    parser.add_argument('--thresholds', nargs='+', type=float, default=None,
                       help='List of thresholds to compare')
    parser.add_argument('--auto-thresholds', action='store_true',
                       help='Use automatic threshold generation (10^-5 to 10^-12)')
    parser.add_argument('--time-start', type=int, default=0,
                       help='Start time index')
    parser.add_argument('--time-end', type=int, default=None,
                       help='End time index')
    parser.add_argument('--output', type=str, default='threshold_comparison.gif',
                       help='Output GIF filename')
    parser.add_argument('--vmin', type=float, default=0,
                       help='Minimum value for color scale')
    parser.add_argument('--vmax', type=float, default=3e-3,
                       help='Maximum value for color scale')
    parser.add_argument('--duration', type=int, default=200,
                       help='Duration per frame in milliseconds')
    parser.add_argument('--show-red-markers', action='store_true', default=True,
                       help='Show red markers for newly revealed data points')
    
    args = parser.parse_args()
    
    # Check file exists
    if not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)
    
    # Determine thresholds
    if args.auto_thresholds:
        thresholds = [10**(-1 * i) for i in range(5, 13)]
        print(f"Using auto-generated thresholds: {thresholds}")
    elif args.thresholds:
        thresholds = args.thresholds
        print(f"Using provided thresholds: {thresholds}")
    else:
        print("Error: Must provide either --thresholds or --auto-thresholds")
        sys.exit(1)
    
    # Create threshold comparison GIF
    success = create_threshold_comparison_gif(
        args.file, args.output,
        thresholds=thresholds,
        time_start=args.time_start, time_end=args.time_end,
        vmin=args.vmin, vmax=args.vmax, duration=args.duration,
        show_red_markers=args.show_red_markers
    )
    
    if success:
        print(f"\nThreshold comparison GIF created successfully: {args.output}")
    else:
        print("Failed to create threshold comparison GIF")
        sys.exit(1)

if __name__ == '__main__':
    main() 