# WRF Autoencoder Experiment Automation

This directory contains scripts and configuration files to automate the process of running WRF experiments with multiple autoencoder models, managing ensembles, and generating visualizations.

## Workflow Overview

1. **Configuration**: Edit `config.yaml` to specify autoencoder dimensions, hidden layer sizes, number of runs, and other parameters.
2. **Directory Setup**: Use `setup_experiments.py` to create all necessary run directories (e.g., `run0000_2_32`) and copy the correct autoencoder models into each.
3. **Job Submission**: Use `submit_jobs.py` to submit WRF jobs for all run directories.
4. **Visualization**: After runs complete, use `create_visualizations.py` to generate comparison GIFs and time series plots.

## Directory Structure

```
automation/
├── README.md
├── config.yaml
├── setup_experiments.py
├── submit_jobs.py
├── create_visualizations.py
```

Other directories (created by the workflow):
```
ensemble_results/
    run0000_2_32/
    run0001_2_32/
    ...
visualization/
    ...
```

## Scripts

### 1. `config.yaml`
Main configuration file. Example:
```yaml
dimensions: [2, 4, 8, 16, 33]
hidden_dims: [32, 64]
num_runs: 10
base_run_dir: "../base-run"
output_dir: "../ensemble_results"
model_dir: "../models"
visualization_dir: "../visualization"
```

### 2. `setup_experiments.py`
Creates all run directories for each (dimension, hidden_dim, run) combination, copies the base run files, and places the correct autoencoder models in each directory.

### 3. `submit_jobs.py`
Submits a WRF job for each run directory using SLURM (calls `sbatch`).

### 4. `create_visualizations.py`
After all runs are complete, generates comparison GIFs and time series plots by calling the appropriate visualization scripts.

## Example Workflow

1. **Edit `config.yaml`** to set your experiment parameters.
2. **Set up experiments:**
   ```bash
   python setup_experiments.py
   ```
3. **Submit jobs:**
   ```bash
   python submit_jobs.py
   ```
4. **Wait for all jobs to finish.**
5. **Create visualizations:**
   ```bash
   python create_visualizations.py
   ```

## Notes
- You can run each step independently.
- The scripts assume you have a working SLURM environment and the necessary WRF and Python dependencies installed.
- Visualization scripts should be adapted to read from the output directories created by this workflow. 