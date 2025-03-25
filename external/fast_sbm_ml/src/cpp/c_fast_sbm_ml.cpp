#include <iostream>
#include <cstring> // for std::memcpy
#include <memory>
#include <torch/script.h>

#include "c_fast_sbm_ml.h"


// Global pointer to the TorchScript module, loaded once
static std::shared_ptr<torch::jit::script::Module> g_module = nullptr;
static bool g_is_loaded = false;

// Path to the model (relative to the build directory if running from there)
static const std::string DEFAULT_MODEL_PATH = "../../../external/fast_sbm_ml/models/emulator.pt";

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

 void c_fast_sbm_ml_(
        const double* w, const double* u, const double* v, double* th_old,
        double* chem_new, const int* n_chem,
        const int* itimestep, const double* dt, const double* dx, const double* dy,
        const double* dz8w, const double* rho_phy, const double* p_phy, const double* pi_phy, double* th_phy,
        const double* xland, const int* domain_id, const int* ivgtyp, const double* xlat, const double* xlong,
        double* qv, double* qc, double* qr, double* qi, double* qs, double* qg, double* qv_old,
        double* qnc, double* qnr, double* qni, double* qns, double* qng, double* qna,
        const int* ids, const int* ide, const int* jds, const int* jde, const int* kds, const int* kde,
        const int* ims, const int* ime, const int* jms, const int* jme, const int* kms, const int* kme,
        const int* its, const int* ite, const int* jts, const int* jte, const int* kts, const int* kte,
        const bool* diagflag,
        double* sbmradar, const int* num_sbmradar,
        const int* sbm_diagnostics,
        double* rainnc, double* rainncv, double* snownc, double* snowncv,
        double* graupelnc, double* graupelncv, double* sr
    )
{
    load_model_if_needed();
    if (!g_module) {
        std::cerr << "[C++] Model was not loaded; cannot run inference.\n";
        return;
    }
    int nx, ny, nz;

    nx = *ime - *ims + 1;
    ny = *jme - *jms + 1;
    nz = *kme - *kms + 1;
    int nb = nx * ny * nz;
    int nfeat = *n_chem;

    // from_blob with shape (nfeat, nb) to match Fortran’s memory layout
    auto opts = torch::TensorOptions().dtype(torch::kFloat64).device(torch::kCPU);
    auto input_tensor = torch::from_blob(chem_new, {*n_chem, ny, nz, nx}, opts);

    // Forward pass
    at::Tensor output = g_module->forward({input_tensor}).toTensor();
    std::cout << "[C++] Successfully ran forward pass.\n";

    // Copy output data back
    if (output.dim() == 4 && output.size(0) == *n_chem && output.size(1) == ny && output.size(1) == nz && output.size(1) == nx) {
        double* out_ptr = output.data_ptr<double>();
        std::memcpy(chem_new, out_ptr, *n_chem * ny * nz * nx * sizeof(double));
    } else {
        std::cerr << "[C++] Unexpected output shape from the model.\n";
    }
}
