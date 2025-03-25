#include <cstdlib>
#include <iostream>
#include <vector>
#include "c_fast_sbm_ml.h"

int main(int argc, char *argv[])
{
    // Set up grid dimensions
    int ims = 1, ime = 2;
    int jms = 1, jme = 2;
    int kms = 1, kme = 2;
    
    // Domain dimensions
    int ids = 1, ide = 2;
    int jds = 1, jde = 2;
    int kds = 1, kde = 2;
    
    // Tile dimensions
    int its = 1, ite = 2;
    int jts = 1, jte = 2;
    int kts = 1, kte = 2;
    
    // Grid sizes
    int nx = ime - ims + 1;
    int ny = jme - jms + 1;
    int nz = kme - kms + 1;
    int grid_points = nx * ny * nz;
    
    // Other parameters
    int n_chem = 3;
    int itimestep = 1;
    double dt = 1.0, dx = 1.0, dy = 1.0;
    int domain_id = 1;
    int sbm_diagnostics = 0;
    int num_sbmradar = 1;
    bool diagflag = false;
    
    // Allocate arrays
    std::vector<double> w(grid_points, 0.1);
    std::vector<double> u(grid_points, 0.2);
    std::vector<double> v(grid_points, 0.3);
    std::vector<double> th_old(grid_points, 300.0);
    std::vector<double> dz8w(grid_points, 1.0);
    std::vector<double> rho_phy(grid_points, 1.0);
    std::vector<double> p_phy(grid_points, 1000.0);
    std::vector<double> pi_phy(grid_points, 1.0);
    std::vector<double> th_phy(grid_points, 300.0);
    
    std::vector<double> qv(grid_points, 0.01);
    std::vector<double> qc(grid_points, 0.001);
    std::vector<double> qr(grid_points, 0.0005);
    std::vector<double> qi(grid_points, 0.0002);
    std::vector<double> qs(grid_points, 0.0001);
    std::vector<double> qg(grid_points, 0.0001);
    std::vector<double> qv_old(grid_points, 0.01);
    std::vector<double> qnc(grid_points, 1.0e6);
    std::vector<double> qnr(grid_points, 1.0e4);
    std::vector<double> qni(grid_points, 1.0e4);
    std::vector<double> qns(grid_points, 1.0e3);
    std::vector<double> qng(grid_points, 1.0e3);
    std::vector<double> qna(grid_points, 1.0e5);
    
    std::vector<double> xland(nx * ny, 1.0);
    std::vector<int> ivgtyp(nx * ny, 1);
    std::vector<double> xlat(nx * ny, 45.0);
    std::vector<double> xlong(nx * ny, -90.0);
    
    std::vector<double> chem_new(grid_points * n_chem, 0.0);
    // Initialize chem_new with the original input data
    for (int i = 0; i < n_chem; i++) {
        for (int j = 0; j < grid_points; j++) {
            chem_new[i*grid_points + j] = i + 1.0;  // Values from 1.0 to 3.0
        }
    }
    
    std::vector<double> sbmradar(grid_points * num_sbmradar, 0.0);
    
    // Initialize optional arrays for precipitation
    std::vector<double> rainnc(nx * ny, 0.0);
    std::vector<double> rainncv(nx * ny, 0.0);
    std::vector<double> snownc(nx * ny, 0.0);
    std::vector<double> snowncv(nx * ny, 0.0);
    std::vector<double> graupelnc(nx * ny, 0.0);
    std::vector<double> graupelncv(nx * ny, 0.0);
    std::vector<double> sr(nx * ny, 0.0);
    
    // Print initial chem_new values
    std::cout << "Initial chem_new values:\n";
    for (int i = 0; i < n_chem; i++) {
        std::cout << "  Species " << (i+1) << ": ";
        for (int j = 0; j < std::min(5, grid_points); j++) {
            std::cout << chem_new[i*grid_points + j] << " ";
        }
        std::cout << std::endl;
    }
    
    // Call the c_fast_sbm_ml_ function
    c_fast_sbm_ml_(
        w.data(), u.data(), v.data(), th_old.data(),
        chem_new.data(), &n_chem,
        &itimestep, &dt, &dx, &dy,
        dz8w.data(), rho_phy.data(), p_phy.data(), pi_phy.data(), th_phy.data(),
        xland.data(), &domain_id, ivgtyp.data(), xlat.data(), xlong.data(),
        qv.data(), qc.data(), qr.data(), qi.data(), qs.data(), qg.data(), qv_old.data(),
        qnc.data(), qnr.data(), qni.data(), qns.data(), qng.data(), qna.data(),
        &ids, &ide, &jds, &jde, &kds, &kde,
        &ims, &ime, &jms, &jme, &kms, &kme,
        &its, &ite, &jts, &jte, &kts, &kte,
        &diagflag,
        sbmradar.data(), &num_sbmradar,
        &sbm_diagnostics,
        rainnc.data(), rainncv.data(), snownc.data(), snowncv.data(),
        graupelnc.data(), graupelncv.data(), sr.data()
    );
    
    // Print results after model inference
    std::cout << "\nModified chem_new values after inference:\n";
    for (int i = 0; i < n_chem; i++) {
        std::cout << "  Species " << (i+1) << ": ";
        for (int j = 0; j < std::min(5, grid_points); j++) {
            std::cout << chem_new[i*grid_points + j] << " ";
        }
        std::cout << std::endl;
    }
    
    // Check for changes in other arrays
    std::cout << "\nSome key values before/after inference:\n";
    std::cout << "  th_old[0] (original: 300.0): " << th_old[0] << std::endl;
    std::cout << "  th_phy[0] (original: 300.0): " << th_phy[0] << std::endl;
    std::cout << "  qv[0] (original: 0.01): " << qv[0] << std::endl;
    
    return 0;
}