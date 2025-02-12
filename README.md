
### 2D WRF-LES-SBM Demo ###


## Model description

This model is modified to run a perturbed parameter ensemble of 2D idealized LES simulations for single marine shallow cumulus clouds.

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

```shell
# choose the corresponding compiler
./configure

# compile WRF-LES
./compile em_les

# extract files needed for SBM
cd run/
tar -xvzf sbm_files.tar.gz
cd ..
```

### Run LES ensemble

```shell
cd test/ensemble
sh ./script.sh
```

