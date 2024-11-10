fcstdate=20090102T0000Z
exp=ap84SeasRF
idir=/scratch/athippp/cylc-archive/${exp}/$fcstdate/
outdir=data/$fcstdate/monthly
for mem in $(seq 1 25); do
    out_dir="$outdir/${exp}/mem${mem}"
    mkdir -p $out_dir
    ifile1=$idir/mem${mem}/outputs/wrf2d_RAINNC.nc
    cdo -r -monmean -divc,3600 -sub -seltimestep,2/-1 "$ifile1" -seltimestep,1/-2 "$ifile1" "$out_dir/prnc_monmean_${exp}_mem${mem}.nc"

    ifile1=$idir/mem${mem}/outputs/wrf2d_RAINC.nc
    cdo -r -monmean -divc,3600 -sub -seltimestep,2/-1 "$ifile1" -seltimestep,1/-2 "$ifile1" "$out_dir/prc_monmean_${exp}_mem${mem}.nc"

    cdo -r -add "$out_dir/prc_monmean_${exp}_mem${mem}.nc" "$out_dir/prnc_monmean_${exp}_mem${mem}.nc" "$out_dir/pr_monmean_${exp}_mem${mem}.nc"
done
out_dir="$outdir/${exp}"
cdo -r -ensmean $out_dir/mem*/pr_*.nc $out_dir/pr_monmean_${exp}_ensmean.nc
cdo -r -ensmean $out_dir/mem*/prnc_*.nc $out_dir/prnc_monmean_${exp}_ensmean.nc
cdo -r -ensmean $out_dir/mem*/prc_*.nc $out_dir/prc_monmean_${exp}_ensmean.nc

cdo -r -ensmedian $out_dir/mem*/pr_*.nc $out_dir/pr_monmean_${exp}_ensmedian.nc
cdo -r -ensmedian $out_dir/mem*/prnc_*.nc $out_dir/prnc_monmean_${exp}_ensmedian.nc
cdo -r -ensmedian $out_dir/mem*/prc_*.nc $out_dir/prc_monmean_${exp}_ensmedian.nc
