#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=100
#SBATCH --account=k10035
#SBATCH -o split_seas5.out

PARALLEL=/scratch/athippp/iops/micromamba/bin/parallel
WGRIB=/scratch/athippp/iops/micromamba/bin/wgrib
rm -f command.list

for var in t2mean t2max t2min dewpt2 precip; do
    mkdir output/$var
    for yyyy in {2000..2023}; do
        for mm in {01..12}; do
            for mem in $(seq 0 0); do
                yy=${yyyy: -2}
                echo "$WGRIB ${var}_seas5_monthly_2000-2023.grib | grep Ensem_mem=${mem}: | grep d=${yy}${mm}0100: | \
                    $WGRIB ${var}_seas5_monthly_2000-2023.grib -i -grib -o output/${var}/${var}_seas5_monthly_${yyyy}${mm}_mem${mem}.grib 2>/dev/null" >>command.list
            done
        done
    done
done
$PARALLEL -j 100 <command.list
