import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
import argparse
import yaml


def calculate_alt(qv, p, theta):
    r_d = 287.
    cp = 7. * r_d / 2.
    rvovrd = 461.6 / 287
    cv = cp - 287
    cvpm = -cv / cp
    qvf = 1. + rvovrd * qv
    alt = (r_d / 100000.) * theta * qvf * ((p / 100000.) ** cvpm)
    return alt


def plot_wrf_quantities(files, output_path, labels=None, time_range=None):
    """
    Plot WRF quantities for multiple files in a single comparison plot.
    
    Args:
        files: List of file paths to WRF output files
        output_path: Output file path for the plot
        labels: List of labels for each file (optional, will auto-generate if None)
        time_range: [start_time, end_time] in minutes (optional, defaults to [0, 60])
    """
    if not files:
        print("No files provided")
        return False
    
    # Check files exist
    missing_files = [f for f in files if not Path(f).exists()]
    if missing_files:
        print(f"Files not found: {missing_files}")
        return False
    
    # Generate labels if not provided
    if labels is None:
        labels = []
        for i, file in enumerate(files):
            if "full_simulation" in str(file):
                labels.append("Full simulation")
            elif "bad_autoencoder" in str(file):
                labels.append("Bad autoencoder")
            else:
                # Try to extract dimension from path
                path_parts = Path(file).parts
                for part in path_parts:
                    if part.startswith("dim_") and "_hidden_" in part:
                        dim = part.split("_")[1]
                        labels.append(f"Latent dimension {dim}")
                        break
                else:
                    labels.append(f"File {i+1}")
    
    if len(labels) != len(files):
        print(f"Number of labels ({len(labels)}) must match number of files ({len(files)})")
        return False
    
    # Set default time range
    if time_range is None:
        time_range = [0, 60]
    
    rainnc_avgs = []
    ql_sums = []
    ql_maxs = []
    liquid_water_sums = []

    for idx, path in enumerate(files):
        print(f"Processing {path}")
        ds = xr.open_dataset(path, decode_times=False)
        
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
        liquid_water_sums.append(liquid_water_sum)
        
        # RAINNC average
        rainnc_avg = np.mean(rainnc, axis=-1)
        if rainnc_avg.ndim == 3:
            rainnc_avg = np.mean(rainnc_avg, axis=1)
        rainnc_avgs.append(rainnc_avg)

        # QCLOUD+QRAIN sum and max
        ql_sum = np.sum(ql, axis=(1, 3))
        if ql_sum.ndim == 2:
            ql_sum = np.mean(ql_sum, axis=1)
        ql_sums.append(ql_sum)

        ql_max = np.max(ql, axis=(1, 3))
        if ql_max.ndim == 2:
            ql_max = np.max(ql_max, axis=1)
        ql_maxs.append(ql_max)

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
            times = np.arange(0, arr.shape[0]/2, 0.5)
            axs[i].plot(times, arr, label=label, linewidth=linewidth)
        axs[i].set_title(title)
        axs[i].set_ylabel(ylabel)
        axs[i].legend()
        axs[i].set_xlim(time_range[0], time_range[1])

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


def plot_wrf_quantities_from_config(config=None, run_idx=None, output_dir=None):
    """
    Legacy function that builds file list from config and calls plot_wrf_quantities.
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
        output_filename = output_dir / f"{date_str}_wrf_quantities_comparison_hidden_{hidden_dim}_run{run_idx:04d}.{output_format}"
        
        # Call the main plotting function
        success = plot_wrf_quantities(
            files=[str(f) for f in cur_files],
            output_path=str(output_filename),
            labels=labels,
            time_range=time_range
        )
        
        if success:
            print(f"Created time series plot for run {run_idx}")
        else:
            print(f"Failed to create time series plot for run {run_idx}")


def main():
    parser = argparse.ArgumentParser(description='Plot WRF quantities from multiple files')
    parser.add_argument('--files', nargs='+', required=True, help='Paths to WRF output files')
    parser.add_argument('--output', type=str, required=True, help='Output file path for the plot')
    parser.add_argument('--labels', nargs='*', help='Labels for each file (optional)')
    parser.add_argument('--time-range', nargs=2, type=float, default=[0, 60], help='Time range in minutes [start, end]')
    
    args = parser.parse_args()
    
    # Call the main plotting function
    success = plot_wrf_quantities(
        files=args.files,
        output_path=args.output,
        labels=args.labels,
        time_range=args.time_range
    )
    
    if not success:
        import sys
        sys.exit(1)


if __name__ == '__main__':
    main() 