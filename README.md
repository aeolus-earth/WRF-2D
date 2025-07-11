
### 2D WRF-LES-SBM Demo ###


## Model description

This model is modified to run a perturbed parameter ensemble of 2D idealized LES simulations for single marine shallow cumulus clouds modified to use a machine learning module for the sbm-fast.

The current model is based on the [WRF v4.3 release](https://github.com/wrf-model/WRF/tree/v4.3).

### References
- [Experiment setups for this repo](https://doi.org/10.22541/essoar.173134625.56730820/v1)
- [Single cumulus cloud simulation](https://doi.org/10.5194/acp-21-16203-2021)
- [Cloud Botany](https://doi.org/10.1029/2023MS003796)

----------

### WRF-ARW Modeling System  ###

We request that all new users of WRF please register. This allows us to better determine how to support and develop the model. Please register using this form:[https://www2.mmm.ucar.edu/wrf/users/download/wrf-regist.php](https://www2.mmm.ucar.edu/wrf/users/download/wrf-regist.php).

For an overview of the WRF modeling system, along with information regarding downloads, user support, documentation, publications, and additional resources, please see the WRF Model Users' Web Site: [https://www2.mmm.ucar.edu/wrf/users/](https://www2.mmm.ucar.edu/wrf/users/).
 
Information regarding WRF Model citations (including a DOI) can be found here: [https://www2.mmm.ucar.edu/wrf/users/citing_wrf.html](https://www2.mmm.ucar.edu/wrf/users/citing_wrf.html).

The WRF Model is open-source code in the public domain, and its use is unrestricted. The name "WRF", however, is a registered trademark of the University Corporation for Atmospheric Research. The WRF public domain notice and related information may be found here: [https://www2.mmm.ucar.edu/wrf/users/public.html](https://www2.mmm.ucar.edu/wrf/users/public.html).




## Run the model

### Setting up WRF
See this [link](https://forum.mmm.ucar.edu/threads/full-wrf-and-wps-installation-example-gnu.12385/) for help downloading any necessary packages

You will first need to install [pysbm](https://github.com/aeolus-earth/pysbm/tree/ry/kangen-fast-sbm) on the  and get the associated libsbm_ae_all.a file resulting from building pysbm. This file will be located in the pysbm/python directory.


```shell
# choose the corresponding compiler
./configure

# edit the LIB_EXTERNAL variable in configure.wrf to include the compiled static library and necesssary libraries
# example of use in example_configure 
vim configure.wrf

# extract files needed for SBM
cd run/
tar -xvzf sbm_files.tar.gz
cd ..

# compiles and runs the ensemble test
# Modify test/ensemble/script.sh to do more/less tests
./compile
```

### Running the compiled executable

```shell
# required for running ideal.exe and wrf.exe if libtorch 
# is not LD_LIBRARY_PATH already (e.g. Download using wget instead of package manager)
export LD_LIBRARY_PATH=/path/to/libtorch/lib:$LD_LIBRARY_PATH

# run script.sh in enesemble
cd test/ensemble
./script.sh
```