# WRF Autoencoder Experiment Automation

This directory contains scripts and configuration files to automate the process of running WRF experiments with multiple autoencoder models, managing ensembles, and generating visualizations.

## Workflow Overview

1. **Configuration**: Edit `config.yaml` to specify autoencoder dimensions, hidden layer sizes, number of runs, and other parameters.
2. **Directory Setup**: Use `setup_experiments.py` to create all necessary run directories and copy the correct autoencoder models into each.
3. **Job Submission**: Use `submit_jobs.py` to submit WRF jobs for all run directories.
4. **Visualization**: After runs complete, use `create_visualizations.py` to generate comparison GIFs and time series plots.

## Directory Structure

```
gen_ens/
├── README.md
├── config.yaml
├── main.py
├── setup_experiments.py
├── submit_jobs.py
├── create_visualizations.py
├── test_visualization.py
├── gen_ens.py
├── ppe_io.py
└── phys.py
```

Output directories (created by the workflow):
```
ensemble_results_v9/
├── full_simulation/
│   ├── run0000/
│   ├── run0001/
│   └── ...
├── dim_2_hidden_256/
│   ├── run0000/
│   ├── run0001/
│   └── ...
├── dim_4_hidden_256/
│   └── ...
└── bad_autoencoder/
    └── ...
```

## Scripts

### 1. `config.yaml`
Main configuration file. Example:
```yaml
dimensions: [2, 4, 8, 16, 33]
hidden_dim: 256
num_runs: 8
output_dir: "/anvil/scratch/x-yyang40/ensemble_results_v9"
model_dir: "../models"
visualization_dir: "../visualization"
wrf_dir: "/home/x-yyang40/kangen-wrf-33-cpy"

# Visualization settings
visualization:
  create_gifs: true
  create_time_series: true
  plot_all_runs: true  # If false, only plots run0000
  output_format: "png"
  dpi: 150
  time_range: [0, 60]  # Time range in minutes for plots
```

### 2. `main.py`
Orchestration script that can run the entire workflow or individual steps:
```bash
python main.py --all                    # Run all steps
python main.py --setup                  # Only setup experiments
python main.py --submit                 # Only submit jobs
python main.py --visualize              # Only create visualizations
```

### 3. `setup_experiments.py`
Creates all run directories for each (dimension, hidden_dim, run) combination, copies the base run files, and places the correct autoencoder models in each directory. Uses `gen_ens.py` to generate initial ensemble members.

### 4. `submit_jobs.py`
Submits a WRF job for each run directory using SLURM (calls `sbatch`).

### 5. `create_visualizations.py`
After all runs are complete, generates:
- **GIFs**: Multi-panel comparison GIFs for each dimension showing full simulation vs autoencoder
- **Time Series Plots**: Four-panel plots showing RAINNC, QCLOUD+QRAIN sum/max, and liquid water content over time

### 6. `test_visualization.py`
Test script to verify that the visualization integration works correctly.

## Visualization Integration

The visualization system is now fully integrated with the Python workflow:

### Time Series Plots (`plot_wrf_quantities.py`)
- **Refactored** to accept a config dictionary and be callable from other Python scripts
- **Configurable** via `config.yaml` visualization settings
- **Plots 4 quantities**:
  1. Total precipitation (cumulative RAINNC)
  2. Sum of liquid water mixing ratio (QCLOUD + QRAIN)
  3. Maximum liquid water mixing ratio
  4. Total liquid water content (physical calculation)

### GIF Creation (`create_multi_comparison_gif.py`)
- Creates multi-panel GIFs comparing full simulation vs autoencoder runs
- One GIF per dimension showing spatial evolution of liquid water content

### Configuration Options
- `create_gifs`: Enable/disable GIF creation
- `create_time_series`: Enable/disable time series plots
- `plot_all_runs`: If false, only plots run0000 (faster for testing)
- `output_format`: File format for plots (png, pdf, etc.)
- `dpi`: Resolution for plots
- `time_range`: Time range in minutes for x-axis

## Example Workflow

1. **Edit `config.yaml`** to set your experiment parameters.
2. **Run the full workflow:**
   ```bash
   python main.py --all
   ```
   
   Or run individual steps:
   ```bash
   python main.py --setup
   python main.py --submit
   python main.py --visualize
   ```

3. **Test the visualization integration:**
   ```bash
   python test_visualization.py
   ```

## Notes
- The scripts assume you have a working SLURM environment and the necessary WRF and Python dependencies installed.
- Visualization scripts are now integrated and configurable via `config.yaml`
- The system supports both direct Python function calls and subprocess fallbacks for robustness
- All paths are handled using `pathlib` for cross-platform compatibility 