#include <iostream>
#include <cstring> // for std::memcpy

extern "C" {

// Minimal no-op function that the Fortran code calls
void c_fast_sbm_ml_(int* n_chem, int* nbatch,
                    double* in_data, double* out_data)
{
    std::cout << "[C++] c_fast_sbm_ml_ no-op called" << std::endl;
    int nk = *n_chem;
    int nb = *nbatch;
    size_t total = static_cast<size_t>(nk) * static_cast<size_t>(nb);

    // Copy input -> output if pointers are valid
    if (in_data && out_data) {
        std::memcpy(out_data, in_data, total * sizeof(double));
    }
}

} // extern "C"
