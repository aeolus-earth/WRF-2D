#!/bin/bash
#SBATCH --job-name=wrf_run
#SBATCH --output=logs/wrf_%j_%a.out
#SBATCH --error=logs/wrf_%j_%a.err
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=8G
#SBATCH --partition=shared
#SBATCH --account=cis250143

# Load required modules
# module load intel/2021.4.0
# module load impi/2021.4.0
# module load netcdf/4.8.1
# Add your specific modules here



set -e

module load netcdf-c
module load conda
module use $HOME/privatemodules
module load conda-env/python_wrf_v2-py3.11
module load hdf5

cd $SLURM_SUBMIT_DIR
export NETCDF=/home/x-yyang40/netcdf
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$NETCDF/lib:/home/x-yyang40/.conda/envs/pysbm_wrf/lib/python3.11/site-packages/torch/lib

# Get the run directory and wrf directory from command line arguments
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <run_directory> <wrf_directory>"
    exit 1
fi

# Convert to absolute paths
run_dir=$(readlink -f "$1")
wrf_dir=$(readlink -f "$2")
run_name=$(basename "$run_dir")

echo "Processing run directory: $run_dir"
echo "WRF directory: $wrf_dir"
echo "Run name: $run_name"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_JOB_NODELIST"

# Set up paths
ens_path=$(readlink -f "${wrf_dir}/test/ensemble")
arch_path=$(readlink -f "${ens_path}/arch")
mpi_procs=1

# Navigate to the run directory
cd "$run_dir"
echo "Entering directory: $run_dir"



# Run wrf.exe
echo "Running wrf.exe..."
nprocs=${mpi_procs} envsubst < template.namelist > namelist.input
mpirun -n ${mpi_procs} ./wrf.exe > mpi.out 2> mpi.err

echo "Successfully completed run: $run_name"
echo "Simulation finished at $(date)" 