cdo -output -sub -fldmean -seltimestep,1 /scratch/athippp/cylc-archive/ap84SeasRF/20090102T0000Z/mem1/outputs/wrf2d_T2.nc \
 -fldmean -seltimestep,-1 /scratch/athippp/cylc-archive/ap84SeasRF/20090102T0000Z/mem1/outputs/wrf2d_T2.nc
cdo -output -fldmean -seltimestep,1 /scratch/athippp/cylc-archive/ap84SeasRF/20090102T0000Z/mem1/outputs/wrf2d_T2.nc 
cdo -output -fldmean -seltimestep,-1 /scratch/athippp/cylc-archive/ap84SeasRF/20090102T0000Z/mem1/outputs/wrf2d_T2.nc

cdo -output -sub -fldmean -selvar,T2 /scratch/athippp/cylc-run/ap84SeasRF/run1/work/20090102T0000Z/share/mem1/wrf2d_d01_2009-01-02_00:00:00 \
 -fldmean -selvar,T2 /scratch/athippp/cylc-run/ap84SeasRF/run1/work/20090102T0000Z/share/mem1/wrf2d_d01_2009-07-06_00:00:00 
cdo -output -fldmean -selvar,T2 /scratch/athippp/cylc-run/ap84SeasRF/run1/work/20090102T0000Z/share/mem1/wrf2d_d01_2009-01-02_00:00:00 
cdo -output -fldmean -selvar,T2 /scratch/athippp/cylc-run/ap84SeasRF/run1/work/20090102T0000Z/share/mem1/wrf2d_d01_2009-07-06_00:00:00

#cdo -output -sub -fldmean -seltimestep,1 data/20090102T0000Z/monthly/ap84SeasRF/mem1/t2_monmean_ap84SeasRF_mem1.nc -fldmean -seltimestep,-1 data/20090102T0000Z/monthly/ap84SeasRF/mem1/t2_monmean_ap84SeasRF_mem1.nc
#cdo -output -sub -fldmean -seltimestep,1 data/20090102T0000Z/monthly/ap84SeasRF/t2_monmean_ap84SeasRF_ensmean.nc -fldmean -seltimestep,-1 data/20090102T0000Z/monthly/ap84SeasRF/t2_monmean_ap84SeasRF_ensmean.nc 