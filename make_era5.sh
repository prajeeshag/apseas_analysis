#!/bin/bash
set -e

year=2009

cdo -f nc --eccodes -remapbil,data/20090102T0000Z/monthly/ap84SeasRF/mem1/t2_monmean_ap84SeasRF_mem1.nc \
    era5_surface_fields_${year}.grib \
    data/era5/monthly/era5_surface_monthly_${year}.nc
