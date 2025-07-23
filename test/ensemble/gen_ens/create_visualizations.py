#!/usr/bin/env python3
"""
Generate visualizations for all experiments by calling the appropriate visualization scripts, including hidden_dim in naming.
"""
import yaml
import subprocess
from pathlib import Path

def main():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    hidden_dim = config['hidden_dim']
    for dim in config['dimensions']:
        # Example: create a multi-comparison GIF for all runs of this dimension/hidden_dim
        pattern = str(Path(config['output_dir']) / f"run*_{dim}_{hidden_dim}" / "wrfout*")
        output_gif = str(Path(config['visualization_dir']) / f"comparison_{dim}_{hidden_dim}.gif")
        print(f"Creating GIF for dimension {dim}, hidden_dim {hidden_dim}")
        subprocess.run([
            'python', '../visualization/create_multi_comparison_gif.py',
            '--files', pattern,
            '--output', output_gif,
            '--labels', 'auto'
        ])
        # Example: create time series plots (if you have a script for this)
        # output_png = str(Path(config['visualization_dir']) / f"quantities_{dim}_{hidden_dim}.png")
        # subprocess.run([
        #     'python', '../visualization/plot_wrf_quantities.py',
        #     '--files', pattern,
        #     '--output', output_png
        # ])

if __name__ == '__main__':
    main() 
