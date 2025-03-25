#include <iostream>
#include <cstring> // for std::memcpy
#include <memory>
#include <torch/script.h>
#include <vector>

extern "C" {

// Minimal no-op function that the Fortran code calls
void c_fast_sbm_ml_(int* n_chem, int* nbatch,
                    double* in_data, double* out_data);
} // extern "C"
