#!/usr/bin/env python3
"""
Plot ensemble distributions of WRF quantities across different autoencoder categories.

This script analyzes the comprehensive experiments and creates visualizations showing:
1. Distribution of key WRF quantities across ensemble members
2. Evolution of quantities over time for each model category
3. Comparison between different autoencoder types
4. Ensemble statistics and spread analysis
"""

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pandas as pd
from typing import Dict, List, Tuple
import yaml
import glob
import re


def load_experiment_config(config_file: str = '../gen_ens/config.yaml') -> dict:
    """Load experiment configuration."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def get_experiment_categories(experiment_dir: Path) -> Dict[str, List[Path]]:
    """
    Categorize experiments by type.
    
    Returns:
        Dictionary with categories and their experiment directories
    """
    categories = {}
    
    # Find full ensemble experiments (100 perturbed runs)
    for category in ['noop', 'threshold_1e-07', 'threshold_1e-09', 'threshold_1e-11']:
        full_ensemble_dir = experiment_dir / f"full_ensemble_{category}"
        if full_ensemble_dir.exists():
            categories[category] = list(full_ensemble_dir.glob("perturb_*"))
    
    # Find dimension-based experiments (first 10 perturbed runs) - each as separate category
    dim_dirs = list(experiment_dir.glob("partial_ensemble_dim_*"))
    if dim_dirs:
        for dim_dir in dim_dirs:
            # Extract category name from directory (e.g., "partial_ensemble_dim_2_hidden_32" -> "dim_2_hidden_32")
            category_name = dim_dir.name.replace("partial_ensemble_", "")
            categories[category_name] = list(dim_dir.glob("perturb_*"))
    
    return categories


def extract_wrf_output_files(experiment_dir: Path) -> Dict[str, List[Path]]:
    """
    Find WRF output files for each experiment category.
    
    Returns:
        Dictionary mapping categories to lists of WRF output files
    """
    categories = get_experiment_categories(experiment_dir)
    wrf_files = {}
    
    for category, exp_dirs in categories.items():
        wrf_files[category] = []
        for exp_dir in exp_dirs:
            # Look for WRF output files
            wrfouts = list(exp_dir.glob("wrfout_d01_*"))
            if wrfouts:
                wrf_files[category].extend(wrfouts)
    
    return wrf_files


def load_wrf_quantity(wrf_file: Path, quantity: str, time_idx: int = -1) -> np.ndarray:
    """
    Load a specific WRF quantity from a file.
    
    Args:
        wrf_file: Path to WRF output file
        quantity: Name of quantity to extract
        time_idx: Time index (-1 for last timestep)
    
    Returns:
        Array of quantity values
    """
    try:
        with xr.open_dataset(wrf_file) as ds:
            if quantity in ds:
                data = ds[quantity].isel(Time=time_idx).values
                # Remove singleton dimensions and get 2D slice
                data = np.squeeze(data)
                if data.ndim > 2:
                    # Take a vertical level (e.g., level 10 for 3D data)
                    data = data[10, :, :] if data.ndim == 3 else data[10, :, :, :]
                return data
            else:
                print(f"Warning: Quantity '{quantity}' not found in {wrf_file}")
                return None
    except Exception as e:
        print(f"Error loading {wrf_file}: {e}")
        return None


def calculate_ensemble_statistics(quantity_data: List[np.ndarray]) -> Dict[str, np.ndarray]:
    """
    Calculate ensemble statistics for a quantity.
    
    Args:
        quantity_data: List of quantity arrays from ensemble members
    
    Returns:
        Dictionary with mean, std, percentiles
    """
    # Filter out None values
    valid_data = [data for data in quantity_data if data is not None]
    
    if not valid_data:
        return {}
    
    # Stack arrays and calculate statistics
    stacked = np.stack(valid_data)
    
    stats = {
        'mean': np.mean(stacked, axis=0),
        'std': np.std(stacked, axis=0),
        'min': np.min(stacked, axis=0),
        'max': np.max(stacked, axis=0),
        'p25': np.percentile(stacked, 25, axis=0),
        'p75': np.percentile(stacked, 75, axis=0),
        'p05': np.percentile(stacked, 5, axis=0),
        'p95': np.percentile(stacked, 95, axis=0)
    }
    
    return stats


def plot_quantity_distributions(experiment_dir: Path, quantities: List[str], 
                              time_indices: List[int] = [-1]):
    """
    Plot distributions of WRF quantities across ensemble categories.
    
    Args:
        experiment_dir: Path to experiment directory
        quantities: List of WRF quantities to plot
        time_indices: List of time indices to analyze
    """
    wrf_files = extract_wrf_output_files(experiment_dir)
    
    # Set up plotting style
    plt.style.use('seaborn-v0_8')
    # Use a larger color palette for many categories
    colors = plt.cm.tab20(np.linspace(0, 1, 20))
    
    for quantity in quantities:
        print(f"Plotting distributions for {quantity}")
        
        # Create figure with subplots for each time index
        fig, axes = plt.subplots(1, len(time_indices), figsize=(6*len(time_indices), 8))
        if len(time_indices) == 1:
            axes = [axes]
        
        for time_idx, ax in zip(time_indices, axes):
            time_label = f"Time {time_idx}" if time_idx >= 0 else "Final Time"
            
            # Collect data for each category
            category_data = {}
            for category, files in wrf_files.items():
                if files:
                    data_list = []
                    for wrf_file in files[:20]:  # Limit to first 20 for performance
                        data = load_wrf_quantity(wrf_file, quantity, time_idx)
                        if data is not None:
                            # Flatten and sample for plotting
                            flat_data = data.flatten()
                            if len(flat_data) > 1000:
                                flat_data = np.random.choice(flat_data, 1000, replace=False)
                            data_list.append(flat_data)
                    
                    if data_list:
                        category_data[category] = np.concatenate(data_list)
            
            # Create violin plots
            if category_data:
                labels = list(category_data.keys())
                data_arrays = list(category_data.values())
                
                # Create violin plot
                parts = ax.violinplot(data_arrays, showmeans=True, showextrema=True)
                
                # Customize violin plot with colors
                for i, pc in enumerate(parts['bodies']):
                    pc.set_alpha(0.7)
                    pc.set_facecolor(colors[i % len(colors)])
                
                ax.set_xticks(range(1, len(labels) + 1))
                ax.set_xticklabels(labels, rotation=45, ha='right')
                ax.set_ylabel(quantity)
                ax.set_title(f'{quantity} Distribution - {time_label}')
                ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'ensemble_distribution_{quantity}.png', dpi=300, bbox_inches='tight')
        plt.show()


def plot_quantity_evolution(experiment_dir: Path, quantities: List[str], 
                          max_time_steps: int = 10):
    """
    Plot evolution of quantities over time for each ensemble category.
    
    Args:
        experiment_dir: Path to experiment directory
        quantities: List of WRF quantities to plot
        max_time_steps: Maximum number of time steps to analyze
    """
    wrf_files = extract_wrf_output_files(experiment_dir)
    
    for quantity in quantities:
        print(f"Plotting evolution for {quantity}")
        
        fig, axes = plt.subplots(1, 1, figsize=(12, 8))
        
        # Colors for different categories - use a larger color palette for many categories
        colors = plt.cm.tab20(np.linspace(0, 1, len(wrf_files)))
        
        for i, (category, files) in enumerate(wrf_files.items()):
            if not files:
                continue
            
            # Sample a few files for performance
            sample_files = files[:min(10, len(files))]
            
            # Collect time evolution data
            time_data = []
            for wrf_file in sample_files:
                try:
                    with xr.open_dataset(wrf_file) as ds:
                        if quantity in ds:
                            # Get time evolution
                            data = ds[quantity].values
                            if data.ndim > 3:
                                # Take a spatial point (e.g., center of domain)
                                data = data[:, 10, 50, 50]  # time, level, y, x
                            elif data.ndim == 3:
                                data = data[:, 50, 50]  # time, y, x
                            else:
                                data = data[:, 50, 50]  # time, y, x
                            
                            time_data.append(data)
                except Exception as e:
                    print(f"Error processing {wrf_file}: {e}")
                    continue
            
            if time_data:
                # Stack and calculate ensemble statistics
                stacked = np.stack(time_data)
                mean_evolution = np.mean(stacked, axis=0)
                std_evolution = np.std(stacked, axis=0)
                
                # Limit time steps
                if len(mean_evolution) > max_time_steps:
                    step = len(mean_evolution) // max_time_steps
                    mean_evolution = mean_evolution[::step]
                    std_evolution = std_evolution[::step]
                    time_points = np.arange(0, len(mean_evolution)) * step
                else:
                    time_points = np.arange(len(mean_evolution))
                
                # Plot mean ± std
                color = colors[i % len(colors)]
                axes.plot(time_points, mean_evolution, color=color, label=category, linewidth=2)
                axes.fill_between(time_points, 
                                mean_evolution - std_evolution,
                                mean_evolution + std_evolution,
                                color=color, alpha=0.3)
        
        axes.set_xlabel('Time Step')
        axes.set_ylabel(quantity)
        axes.set_title(f'{quantity} Evolution Over Time')
        axes.legend()
        axes.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'ensemble_evolution_{quantity}.png', dpi=300, bbox_inches='tight')
        plt.show()


def plot_ensemble_comparison(experiment_dir: Path, quantities: List[str]):
    """
    Create comparison plots between different ensemble categories.
    
    Args:
        experiment_dir: Path to experiment directory
        quantities: List of WRF quantities to compare
    """
    wrf_files = extract_wrf_output_files(experiment_dir)
    
    for quantity in quantities:
        print(f"Creating comparison plots for {quantity}")
        
        # Create box plot comparison
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Box plot
        category_data = []
        category_labels = []
        
        for category, files in wrf_files.items():
            if files:
                data_list = []
                for wrf_file in files[:15]:  # Sample files
                    data = load_wrf_quantity(wrf_file, quantity)
                    if data is not None:
                        flat_data = data.flatten()
                        if len(flat_data) > 500:
                            flat_data = np.random.choice(flat_data, 500, replace=False)
                        data_list.append(flat_data)
                
                if data_list:
                    category_data.append(np.concatenate(data_list))
                    category_labels.append(category)
        
        if category_data:
            # Box plot
            bp = ax1.boxplot(category_data, labels=category_labels, patch_artist=True)
            for patch in bp['boxes']:
                patch.set_alpha(0.7)
            
            ax1.set_ylabel(quantity)
            ax1.set_title(f'{quantity} - Box Plot Comparison')
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, alpha=0.3)
            
            # Histogram comparison
            for i, (data, label) in enumerate(zip(category_data, category_labels)):
                ax2.hist(data, bins=30, alpha=0.6, label=label, density=True)
            
            ax2.set_xlabel(quantity)
            ax2.set_ylabel('Density')
            ax2.set_title(f'{quantity} - Histogram Comparison')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'ensemble_comparison_{quantity}.png', dpi=300, bbox_inches='tight')
        plt.show()


def main():
    """Main function to run ensemble analysis and plotting."""
    # Load configuration
    try:
        config = load_experiment_config()
        experiment_dir = Path(config['output_dir']) / "comprehensive_experiments_comprehensive"
    except Exception as e:
        print(f"Error loading config: {e}")
        print("Using default experiment directory...")
        experiment_dir = Path("/anvil/scratch/x-yyang40/perturbation_experiments/comprehensive_experiments_comprehensive")
    
    if not experiment_dir.exists():
        print(f"Experiment directory not found: {experiment_dir}")
        return
    
    print(f"Analyzing experiments in: {experiment_dir}")
    
    # Define quantities to analyze (modify as needed)
    quantities = ['QVAPOR', 'T2', 'U10', 'V10', 'PSFC']
    
    # Plot distributions
    print("\n=== Plotting Quantity Distributions ===")
    plot_quantity_distributions(experiment_dir, quantities)
    
    # Plot evolution over time
    print("\n=== Plotting Quantity Evolution ===")
    plot_quantity_evolution(experiment_dir, quantities)
    
    # Plot ensemble comparisons
    print("\n=== Plotting Ensemble Comparisons ===")
    plot_ensemble_comparison(experiment_dir, quantities)
    
    print("\n=== Analysis Complete ===")
    print("Generated plots:")
    for quantity in quantities:
        print(f"  - ensemble_distribution_{quantity}.png")
        print(f"  - ensemble_evolution_{quantity}.png")
        print(f"  - ensemble_comparison_{quantity}.png")


if __name__ == '__main__':
    main()
