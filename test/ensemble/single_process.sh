#!/bin/bash
set -e
ens_path=$(pwd)
wrf_path=${ens_path}/../..
arch_path=${ens_path}/arch
n_cases=1

python gen_ens/gen_ens.py ${ens_path} ${n_cases}

for run_path in $(echo ${ens_path}/run*); do

    cd ${run_path}
    echo "Entering directory: ${run_path}"

    ln -sf ${wrf_path}/run/* .
    rm namelist.*
    ln -sf ${arch_path}/* .
    ln -sf ./input_sounding.ppe ./input_sounding

    nprocs=1 envsubst < template.namelist > namelist.input
    ./ideal.exe

    nprocs=1 envsubst < template.namelist > namelist.input
    ./wrf.exe
	
done

