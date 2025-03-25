#!/usr/bin/env bash
set -e

echo "[build.sh] Checking for gfortran..."
# Use system compilers instead of conda ones
echo "[build.sh] Setting up build environment..."
# Check if we're using conda compilers
if [[ -n $(which gcc | grep -o conda) ]]; then
    echo "[build.sh] Detected conda compilers, switching to system compilers"
    # Save the original PATH
    ORIGINAL_PATH=$PATH
    # Remove conda from PATH temporarily for this build
    export PATH=$(echo $PATH | tr ':' '\n' | grep -v "conda" | tr '\n' ':')
    # Set compiler environment variables explicitly
    export CC=/usr/bin/gcc
    export CXX=/usr/bin/g++
    export FC=/usr/bin/gfortran
    # Flag to restore path
    RESTORE_PATH=1
fi

if ! command -v gfortran &> /dev/null
then
    echo "[build.sh] gfortran not found. Please install it (e.g., brew install gfortran on macOS)."
    exit 1
fi

echo "[build.sh] Generating TorchScript model..."
python src/python/generate_model.py

echo "[build.sh] Creating build directory..."
mkdir -p build
cd build

echo "[build.sh] Running CMake (auto-fetching LibTorch if necessary)..."
cmake ..

echo "[build.sh] Building with make..."
make

echo "[build.sh] Build complete. Driver is at ./driver."

# Restore the original PATH if we modified it
if [[ -n $RESTORE_PATH ]]; then
    export PATH=$ORIGINAL_PATH
fi