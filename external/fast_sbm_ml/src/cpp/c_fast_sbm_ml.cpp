

#include "c_fast_sbm_ml.h"


// Global pointer to the TorchScript module, loaded once
static std::shared_ptr<torch::jit::script::Module> g_module = nullptr;
static bool g_is_loaded = false;

// Path to the model (relative to the build directory if running from there)
static const std::string DEFAULT_MODEL_PATH = "../models/emulator.pt";

// Load the model once
static void load_model_if_needed() {
    if (!g_is_loaded) {
        try {
            g_module = std::make_shared<torch::jit::script::Module>(
                torch::jit::load(DEFAULT_MODEL_PATH)
            );
            std::cout << "[C++] Loaded TorchScript model: " << DEFAULT_MODEL_PATH << "\n";
            g_is_loaded = true;
        } catch (const c10::Error &e) {
            std::cerr << "[C++] Error loading model at " << DEFAULT_MODEL_PATH 
                      << ": " << e.what() << std::endl;
            throw;
        }
    }
}

void c_fast_sbm_ml_(int* n_chem, int* nbatch,
                    double* in_data, double* out_data)
{
    load_model_if_needed();
    if (!g_module) {
        std::cerr << "[C++] Model was not loaded; cannot run inference.\n";
        return;
    }

    int nb = *nbatch;
    int nfeat = *n_chem;

    // from_blob with shape (nfeat, nb) to match Fortran’s memory layout
    auto opts = torch::TensorOptions().dtype(torch::kFloat64).device(torch::kCPU);
    auto input_tensor = torch::from_blob(in_data, {nfeat, nb}, opts);

    // Transpose to get shape (nb, nfeat)
    input_tensor = input_tensor.t(); // shape becomes (nb, nfeat)

    // Forward pass
    at::Tensor output = g_module->forward({input_tensor}).toTensor();
    std::cout << "[C++] Successfully ran forward pass.\n";

    // Transpose to get shape (nfeat, nb)
    output = output.t(); // shape becomes (nfeat, nb)

    // Copy output data back
    if (output.dim() == 2 && output.size(0) == nfeat && output.size(1) == nb) {
        double* out_ptr = output.data_ptr<double>();
        std::memcpy(out_data, out_ptr, nb * nfeat * sizeof(double));
    } else {
        std::cerr << "[C++] Unexpected output shape from the model.\n";
    }
}


