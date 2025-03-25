#include <cstdlib>
#include <iostream>
#include "c_fast_sbm_ml.h"
 
int main(int argc, char *argv[])
{
    int n_chem = 3;   // Number of chemical components
    int nbatch = 2;   // Number of batches
    
    // Input data: Assume each batch has n_chem elements
    double in_data[] = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0};
    
    // Output data array, initialized to zero
    double out_data[6] = {0.0};
    
    // Call the function
    c_fast_sbm_ml_(&n_chem, &nbatch, in_data, out_data);
    
    // Print results
    std::cout << "Output Data: ";
    for (int i = 0; i < 6; ++i) {
        std::cout << out_data[i] << " ";
    }
    std::cout << std::endl;

}