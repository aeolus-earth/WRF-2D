Based off of https://github.com/aeolus-earth/fortran-torch-adapter/


# Emulation Example: (Driver/Fortran) → C++ → TorchScript 
This **README** provides **excrutiatingly detailed** end-to-end instructions for setting up a pipeline where:

1. A **C++** driver file(c_test_driver.cpp) calls a **C++** function in c_fast_sbm_ml.cpp. This will be done by fortran code and the cpp driver is there for testing purposes
2. A **C++** function loads and runs a **TorchScript** model
3. The model is produced by a **Python** script (using PyTorch).  

The example model in this repository simply returns its square input (so that we can easily verify the pipeline). In practice, you could replace it with any TorchScript model. The goal is to teach you how to interface with pytorch models from inside of Fortran.

The aim is to give a complete example of integrating cpp to use a pytorch model within the WRF code

1. **Generate a TorchScript model** by running a Python script.  
2. **Compile the C++** using g++, linking against LibTorch.  
3. **The C++ Driver** will call the ml function. Note that this can be done in the fortran code as well as long as the right files are included
3. **The C++ ML function** loads the TorchScript model and performs inference.  

This example is useful for understanding how to pass data from Fortran → C++ → TorchScript, even if you are new to these languages.

## Tested Versions
This code has been tested with:
- **Python**: 3.8+ (3.10 recommended)
- **PyTorch**: 2.0.0+
- **LibTorch**: 2.0.0+ (matching your PyTorch version)
- **g++**: 9.0+ (or equivalent C++17 compatible compiler)
- **CMake**: 3.10+

## Explanation of Data Flow
1. Driver (`src/cpp/c_test_driver.cpp`):
   - Allocates and creates data for a test run of the model
   - Calls the c_fast_sbm_ml_ function
   - Prints the output to stdout
2. ML Model (`src/cpp/c_fast_sbm_ml.cpp`):
   - Receives the corresponding inputs but only uses a subset of them currently
   - Wraps chem_new in a Torch tensor of shape `[n_chem, ny, nz, nx]` (opposite order of fortran input shape).
   - Runs it through the TorchScript model (`models/emulator.pt`).
   - Writes the output back into a second buffer.  

## Setup Instructions
Below is a comprehensive list of all necessary tools and how to install them. We assume you are working on either **Linux (Ubuntu, Debian, etc.)** or **macOS**. If you are on **macOS**, just make sure to use `brew` instead of `apt`

### Install Compilers
```bash
sudo apt-get install g++
g++ --version
```

```bash
sudo apt-get install cmake
cmake --version
```

### Install LibTorch
For the CPU/GPU-enabled LibTorch versions, please select the correct version [here](https://pytorch.org/). Make sure to scroll down to the bottom and select your OS/platform while choosing libtorch as the package
We will assume that LibTorch resides in `/path/to/libtorch/`. We then need to export like so
```bash
export LIBTORCH=/path/to/libtorch
```

### Build & Run
Create & activate a Python venv with [uv](https://docs.astral.sh/uv/getting-started/installation/)
```bash
uv venv .venv
source .venv/bin/activate
```

Install python deps from pyproject.toml
```bash
uv pip install -e .
```

Build everything. This generates the model, compiles all binaries, ...
```bash
make
```

Run the executable to test if everything worked.

```bash
cd build
./driver
```

## Customizing the Model
The default model in this repository is a simple square model that returns its input squared. To use your own PyTorch model:

1. **Create and export your custom model**: Replace the `NoopModel` class in `src/python/generate_model.py` with your own model architecture.

2. **Match tensor shapes**: Make sure your model accepts inputs of shape  `[n_chem, ny, nz, nx]` and returns outputs matching the expected shape in `c_fast_sbm_ml_` in `src/cpp/c_fast_sbm_ml.cpp`.

3. **Update dimensions if needed**: If your model requires different input/output shapes, modify the array reshaping logic in `src/cpp/c_test_driver` accordingly.

4. **Rebuild**: Run `make` again to generate the new model and rebuild the executable.

Note that the C++ code expects the model file to be at `../../../external/fast_sbm_ml/models/emulator.pt` relative to the build directory. If you need to change this path, modify the `DEFAULT_MODEL_PATH` variable in `src/cpp/inference.cpp`.

## Troubleshooting
**"TorchConfig.cmake not found"** or **"Could NOT find Torch"**:  
  - Verify that `LIBTORCH` points to the correct folder. 

**Linker errors** about missing Torch libraries:  
  - Make sure you downloaded the correct libtorch variant (CPU or CUDA) and that your compiler is compatible.

**Python import errors**:  
  - Check that PyTorch is installed in your chosen environment. Try `pip show torch`.

**Compiler not found**:  
  - Check that `g++` (or clang, MSVC, etc.) is installed.  

**Path errors when loading the model**:
  - The C++ code assumes the model is at `../models/emulator.pt` relative to where you run the executable. Make sure you run `./driver` from the `build` directory, or update the path in `src/cpp/c_fast_sbm_ml.cpp`.

## Further Reading
- [PyTorch C++ API (LibTorch) Documentation](https://pytorch.org/cppdocs/)  
- [CMake Official Documentation](https://cmake.org/documentation/)  