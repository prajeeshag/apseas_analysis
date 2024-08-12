fcstdate=20090102T0000Z
exp=ap84SeasRF
idir=/scratch/athippp/cylc-archive/${exp}/$fcstdate/
outdir=data/$fcstdate/monthly
for mem in $(seq 1 25); do
    out_dir="$outdir/${exp}/mem${mem}"
    mkdir -p $out_dir
    cdo -r -monmean $idir/mem${mem}/outputs/wrf2d_T2.nc $out_dir/t2_monmean_${exp}_mem${mem}.nc
done
out_dir="$outdir/${exp}"
cdo -r -ensmean $out_dir/mem*/t2_*.nc $out_dir/t2_monmean_${exp}_ensmean.nc
