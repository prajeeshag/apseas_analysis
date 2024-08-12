#!/bin/bash
set -e

year=2009
mon=01

cdo -f nc --eccodes -remapbil,data/20090102T0000Z/monthly/ap84SeasRF/mem1/t2_monmean_ap84SeasRF_mem1.nc seas5_surface_monthly_${year}_${mon}.grib _out.nc
for i in $(seq 1 25); do
    cdo -f nc -seltimestep,"${i}"/-1/25 _out.nc data/${year}${mon}02T0000Z/monthly/seas5/seas5_surface_monthly_mem${i}.nc
done
