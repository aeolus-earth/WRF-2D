#!/bin/bash
# Comprehensive WRF Experiment Setup Script
# This script automates the entire workflow:
# 1. Create 100 perturbed WRF input files
# 2. Setup comprehensive experiments for all autoencoder configurations

set -e  # Exit on any error

echo "=== Comprehensive WRF Experiment Setup ==="
echo "This will create 100 perturbed inputs and setup all experiments"
echo ""

# Check if we're in the right directory
if [ ! -f "setup_comprehensive_experiments.py" ]; then
    echo "ERROR: setup_comprehensive_experiments.py not found in current directory"
    echo "Please run this script from the ensemble/gen_ens directory"
    exit 1
fi

# Configuration - modify these paths as needed
INPUT_FILE="../../../wrfinput_d01"  # Path to your original WRF input file (relative to this script)
OUTPUT_DIR="../../../perturbed_inputs"  # Directory for perturbed files (relative to this script)
NUM_PERTURBATIONS=100  # Number of perturbed files to create
NOISE_STD=0.001  # Standard deviation for Gaussian noise
BASE_SEED=42  # Base random seed

echo "Configuration:"
echo "  Input file: $INPUT_FILE"
echo "  Output directory: $OUTPUT_DIR"
echo "  Number of perturbations: $NUM_PERTURBATIONS"
echo "  Noise standard deviation: $NOISE_STD"
echo "  Base seed: $BASE_SEED"
echo ""

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Input file '$INPUT_FILE' not found!"
    echo "Please ensure you have a WRF input file named 'wrfinput_d01' in the parent directory"
    echo "Or modify the INPUT_FILE path in this script"
    exit 1
fi

# Step 1: Create perturbed input files
echo "=== Step 1: Creating $NUM_PERTURBATIONS perturbed WRF input files ==="
python3 ../../../modify_wrf_input.py "$INPUT_FILE" \
    --output-dir "$OUTPUT_DIR" \
    --num-files "$NUM_PERTURBATIONS" \
    --noise-std "$NOISE_STD" \
    --seed "$BASE_SEED"

echo ""
echo "✓ Step 1 complete: Created $NUM_PERTURBATIONS perturbed input files"
echo ""

# Step 2: Setup comprehensive experiments
echo "=== Step 2: Setting up comprehensive experiments ==="
echo "This will create:"
echo "  - 100 perturbed runs for noop and threshold models (1e-07, 1e-09, 1e-11)"
echo "  - First 10 perturbed runs for all autoencoder configurations"
echo "    (hidden dims: 43, 64, 256; latent dims: 2, 4, 8, 16, 33)"
echo ""

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "ERROR: config.yaml not found in $(pwd)"
    echo "Please ensure you have a valid config.yaml file with the required settings:"
    echo "  - wrf_dir: path to WRF installation"
    echo "  - output_dir: path for experiment output"
    echo "  - submit_script: path to job submission script"
    echo "  - model_dir: path to autoencoder model files"
    echo "  - perturbed_inputs:"
    echo "      perturbed_dir: path to perturbed inputs (relative to this script)"
    echo "      base_run: path to base run directory"
    echo "      submit_jobs: true/false"
    echo ""
    echo "You can use the sample config template: config_template.yaml"
    exit 1
fi

# Run the comprehensive experiment setup using the NEW script
python3 setup_comprehensive_experiments.py

echo ""
echo "✓ Step 2 complete: Comprehensive experiments setup complete"
echo ""

echo "=== Summary ==="
echo "✓ Created $NUM_PERTURBATIONS perturbed WRF input files in '$OUTPUT_DIR/'"
echo "✓ Setup comprehensive experiments for all autoencoder configurations"
echo ""
echo "Next steps:"
echo "1. Check the experiment summary in the output directory"
echo "2. Verify that all model files exist and are accessible"
echo "3. Monitor job submissions and WRF runs"
echo ""
echo "To check experiment status:"
echo "  ls -la comprehensive_experiments_*/"
echo "  cat comprehensive_experiments_*/comprehensive_experiment_summary.txt"
echo ""
echo "=== Setup Complete! ==="


