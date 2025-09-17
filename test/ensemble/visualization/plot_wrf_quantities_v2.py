import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
import argparse
import yaml
import re


def calculate_alt(qv, p, theta):
    r_d = 287.
    cp = 7. * r_d / 2.
    rvovrd = 461.6 / 287
    cv = cp - 287
    cvpm = -cv / cp
    qvf = 1. + rvovrd * qv
    alt = (r_d / 100000.) * theta * qvf * ((p / 100000.) ** cvpm)
    return alt


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


def plot_wrf_quantities_v2(files, output_path, labels=None, time_range=None, start_times=None, auto_start_times=False):
    """
    Plot WRF quantities for multiple files in a single comparison plot with different start times.
    
    Args:
        files: List of file paths to WRF output files
        output_path: Output file path for the plot
        labels: List of labels for each file (optional, will auto-generate if None)
        time_range: [start_time, end_time] in minutes (optional, defaults to [0, 60])
        start_times: List of start times in minutes for each file (optional)
        auto_start_times: Whether to automatically detect start times from filenames
    """
    if not files:
        print("No files provided")
        return False
    
    # Check files exist
    missing_files = [f for f in files if not Path(f).exists()]
    if missing_files:
        print(f"Files not found: {missing_files}")
        return False
    
    # Handle start times first
    if auto_start_times:
        # Extract start times from filenames
        start_times = []
        for f in files:
            start_time = extract_start_time_from_filename(f)
            start_times.append(start_time)
            print(f"File: {Path(f).parent.name} -> Start time: {start_time} minutes")
        print(f"Auto-detected start times: {start_times}")
    elif start_times is None:
        start_times = [0] * len(files)
    
    if len(start_times) != len(files):
        if len(start_times) == 1:
            start_times = start_times * len(files)
        else:
            print(f"Number of start_times ({len(start_times)}) must match number of files ({len(files)})")
            return False
    
    # Generate labels based on start times if not provided
    if labels is None:
        labels = []
        for i, file in enumerate(files):
            # Check if this is the first file (original run)
            if i == 0:
                labels.append("Full simulation")
            else:
                # Use start time as label for restart runs
                start_time = start_times[i]
                time_label = format_time_label(start_time)
                labels.append(f"Restart at {time_label}")
    
    if len(labels) != len(files):
        print(f"Number of labels ({len(labels)}) must match number of files ({len(files)})")
        return False
    
    # Set default time range
    if time_range is None:
        time_range = [0, 60]
    
    # Calculate overall time range
    overall_start = min(start_times)
    overall_end = time_range[1]
    overall_length = overall_end - overall_start
    
    print(f"Overall time range: {overall_start} to {overall_end} minutes")
    print(f"Start times for each file: {start_times}")
    print(f"Labels: {labels}")
    
    rainnc_avgs = []
    ql_sums = []
    ql_maxs = []
    liquid_water_sums = []

    for idx, path in enumerate(files):
        print(f"Processing {path} (starts at {start_times[idx]} minutes)")
        ds = xr.open_dataset(path, decode_times=False)
        
        # Get the actual data length
        actual_length = len(ds.Time)
        
        # RAINNC: (Time, south_north, west_east)
        rainnc = ds["RAINNC"].values  # shape: (T, y, x)
        qcloud = ds["QCLOUD"].values
        qrain = ds["QRAIN"].values
        ql = qcloud + qrain  # (T, z, y, x)
        print(f"Data shape: {ql.shape}")

        # For liquid water sum calculation
        p = ds["P"].values  # (T, z, y, x)
        pb = ds["PB"].values  # (T, z, y, x)
        ph = ds["PH"].values  # (T, z+1, y, x)
        phb = ds["PHB"].values  # (T, z+1, y, x)
        theta = ds["T"].values + 300.  # (T, z, y, x)
        qv = ds["QVAPOR"].values  # (T, z, y, x)
        pressure = p + pb  # (T, z, y, x)
        
        # alt: (T, z, y, x)
        alt = calculate_alt(qv, pressure, theta)
        
        # dz: (T, z, y, x)
        g = 9.81
        z_stag = (ph + phb) / g  # (T, z+1, y, x)
        dz = np.diff(z_stag, axis=1)  # (T, z, y, x)
        
        # Compute sum of liquid water content
        # (1/alt) * (QCLOUD+QRAIN) * (40*40*dz)
        cell_area = 40 * 40  # m^2
        liquid_water = (1.0 / alt) * ql * (cell_area * dz)  # (T, z, y, x)
        # Sum over z, y, x
        liquid_water_sum = np.sum(liquid_water, axis=(1, 2, 3))  # (T,)
        
        # RAINNC average
        rainnc_avg = np.mean(rainnc, axis=-1)
        if rainnc_avg.ndim == 3:
            rainnc_avg = np.mean(rainnc_avg, axis=1)
        
        # QCLOUD+QRAIN sum and max
        ql_sum = np.sum(ql, axis=(1, 3))
        if ql_sum.ndim == 2:
            ql_sum = np.mean(ql_sum, axis=1)

        ql_max = np.max(ql, axis=(1, 3))
        if ql_max.ndim == 2:
            ql_max = np.max(ql_max, axis=1)
        
        # Create arrays for the overall time range
        overall_timesteps = int(overall_length * 2)  # 30-second intervals
        
        # Initialize arrays with NaN (not zeros)
        rainnc_full = np.full(overall_timesteps, np.nan)
        ql_sum_full = np.full(overall_timesteps, np.nan)
        ql_max_full = np.full(overall_timesteps, np.nan)
        liquid_water_full = np.full(overall_timesteps, np.nan)
        
        # Fill in data where simulation is active
        # For restart runs (idx > 0), shift data one timestep to the right since they don't include the restart time point
        if idx == 0:
            # Full simulation starts at time 0
            start_idx = int(start_times[idx] * 2)  # Convert minutes to timesteps
        else:
            # Restart runs: data starts one timestep after the declared start time
            start_idx = int(start_times[idx] * 2) + 1  # Shift right by one timestep
        
        end_idx = min(start_idx + actual_length, overall_timesteps)
        
        print(f"  File {idx}: start_idx={start_idx}, actual_length={actual_length}, end_idx={end_idx}")
        
        if start_idx < overall_timesteps:
            # Copy actual data
            actual_end = min(actual_length, end_idx - start_idx)
            print(f"  File {idx}: actual_end={actual_end}, data range: {start_idx} to {start_idx + actual_end}")
            
            # Ensure arrays are 1D before assignment
            rainnc_avg_1d = rainnc_avg[:actual_end].flatten()
            ql_sum_1d = ql_sum[:actual_end].flatten()
            ql_max_1d = ql_max[:actual_end].flatten()
            liquid_water_1d = liquid_water_sum[:actual_end].flatten()
            
            rainnc_full[start_idx:start_idx + actual_end] = rainnc_avg_1d
            ql_sum_full[start_idx:start_idx + actual_end] = ql_sum_1d
            ql_max_full[start_idx:start_idx + actual_end] = ql_max_1d
            liquid_water_full[start_idx:start_idx + actual_end] = liquid_water_1d
        
        rainnc_avgs.append(rainnc_full)
        ql_sums.append(ql_sum_full)
        ql_maxs.append(ql_max_full)
        liquid_water_sums.append(liquid_water_full)

        ds.close()

    # Plotting
    fig, axs = plt.subplots(4, 1, figsize=(10, 16), sharex=True)

    # Use user-specified names for titles and y-labels
    plot_info = [
        (rainnc_avgs, "Total precipitation (Cumulative)", "water (mm)"),
        (ql_sums, "Sum of liquid water mixing ratio", "water (kg/kg)"),
        (ql_maxs, "Maximum liquid water mixing ratio", "water (kg/kg)"),
        (liquid_water_sums, "Total liquid water content", "water (kg)")
    ]

    for i, (data, title, ylabel) in enumerate(plot_info):
        for idx, (arr, label) in enumerate(zip(data, labels)):
            # Use linewidth=2 for GT (first file), linewidth=1 for others
            linewidth = 2 if idx == 0 else 1
            # Create time array that matches the data array length
            times = np.arange(overall_start, overall_end, 0.5)
            if len(times) != len(arr):
                print(f"Warning: Time array length ({len(times)}) doesn't match data array length ({len(arr)})")
                # Adjust time array to match data length
                times = np.linspace(overall_start, overall_end, len(arr))
            
            # Plot only non-NaN data or add visual indication of start time
            non_nan_mask = ~np.isnan(arr)
            if np.any(non_nan_mask):
                # Plot the actual data
                axs[i].plot(times[non_nan_mask], arr[non_nan_mask], label=label, linewidth=linewidth)
                
                # Add vertical line at start time if not zero
                # if start_times[idx] > 0:
                #     axs[i].axvline(x=start_times[idx], color='gray', alpha=0.5, linestyle='--')
            else:
                # No data, just add label for legend
                axs[i].plot([], [], label=label, linewidth=linewidth)
        
        axs[i].set_title(title)
        axs[i].set_ylabel(ylabel)
        if i == 0:
            axs[i].legend()
        axs[i].set_xlim(time_range[0], time_range[1])
        axs[i].grid(True, alpha=0.3, linestyle='--')

    fig.align_ylabels()
    axs[-1].set_xlabel("Time (min)")
    plt.tight_layout()

    # Save the plot
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()  # Close the figure to free memory
    print(f"Saved plot: {output_path}")
    
    return True


def plot_wrf_quantities_from_config_v2(config=None, run_idx=None, output_dir=None, auto_start_times=False):
    """
    Legacy function that builds file list from config and calls plot_wrf_quantities_v2.
    This maintains backward compatibility with the existing workflow.
    """
    if config is None:
        # Load config from file if not provided
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    
    if output_dir is None:
        output_dir = Path(config.get('visualization_dir', '.'))
    else:
        output_dir = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get visualization settings from config
    viz_config = config.get('visualization', {})
    create_time_series = viz_config.get('create_time_series', True)
    plot_all_runs = viz_config.get('plot_all_runs', True)
    output_format = viz_config.get('output_format', 'png')
    dpi = viz_config.get('dpi', 150)
    time_range = viz_config.get('time_range', [0, 60])
    
    if not create_time_series:
        print("Time series plotting disabled in config")
        return
    
    hidden_dim = config['hidden_dim']
    dims = config['dimensions']
    num_runs = config['num_runs']
    base_output_dir = Path(config['output_dir'])
    
    # Labels for different simulations
    labels = ["Full simulation"] + [f"Latent dimension {dim}" for dim in dims] + ["Bad autoencoder"]
    
    # Determine which runs to process
    if run_idx is not None:
        run_indices = [run_idx]
    elif not plot_all_runs:
        run_indices = [0]  # Only plot run0000
    else:
        run_indices = range(num_runs)
    
    for run_idx in run_indices:
        print(f"Processing run {run_idx:04d}")
        
        # Build file list for this run
        cur_files = []
        
        # Full simulation
        cur_files.append(base_output_dir / "full_simulation" / f"run{run_idx:04d}" / "wrfout_d01_0001-01-01_00:00:00")
        
        # Autoencoder runs
        for dim in dims:
            cur_files.append(base_output_dir / f"dim_{dim}_hidden_{hidden_dim}" / f"run{run_idx:04d}" / "wrfout_d01_0001-01-01_00:00:00")
        
        # Bad autoencoder
        cur_files.append(base_output_dir / "bad_autoencoder" / f"run{run_idx:04d}" / "wrfout_d01_0001-01-01_00:00:00")
        
        # Check if all files exist
        missing_files = [f for f in cur_files if not f.exists()]
        if missing_files:
            print(f"Warning: Missing files for run {run_idx:04d}: {missing_files}")
            continue
        
        # Get current date as a string, e.g., '2024-06-13'
        date_str = datetime.now().strftime("%Y_%m_%d")
        
        # Create output filename
        output_filename = output_dir / f"{date_str}_wrf_quantities_comparison_v2_hidden_{hidden_dim}_run{run_idx:04d}.{output_format}"
        
        # Call the main plotting function
        success = plot_wrf_quantities_v2(
            files=[str(f) for f in cur_files],
            output_path=str(output_filename),
            labels=labels,
            time_range=time_range,
            auto_start_times=auto_start_times
        )
        
        if success:
            print(f"Created time series plot for run {run_idx}")
        else:
            print(f"Failed to create time series plot for run {run_idx}")


def main():
    parser = argparse.ArgumentParser(description='Plot WRF quantities from multiple files with different start times')
    parser.add_argument('--files', nargs='+', required=True, help='Paths to WRF output files')
    parser.add_argument('--output', type=str, required=True, help='Output file path for the plot')
    parser.add_argument('--labels', nargs='*', help='Labels for each file (optional)')
    parser.add_argument('--time-range', nargs=2, type=float, default=[0, 60], help='Time range in minutes [start, end]')
    parser.add_argument('--start-times', nargs='*', type=int, help='Start times in minutes for each file (optional)')
    parser.add_argument('--auto-start-times', action='store_true', help='Automatically detect start times from filenames')
    
    args = parser.parse_args()
    
    # Call the main plotting function
    success = plot_wrf_quantities_v2(
        files=args.files,
        output_path=args.output,
        labels=args.labels,
        time_range=args.time_range,
        start_times=args.start_times,
        auto_start_times=args.auto_start_times
    )
    
    if not success:
        import sys
        sys.exit(1)


if __name__ == '__main__':
    main() 