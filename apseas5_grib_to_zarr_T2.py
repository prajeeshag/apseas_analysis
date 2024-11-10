import hashlib
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import xarray as xr
from cdo import Cdo
from dask.distributed import Client, LocalCluster


def drop_step(ds):
    return ds.drop_vars({"Times", "Times_bnds"})


def _write_to_zarr(input, store, region):
    print(region, store, input)
    ifile = _cdo_execute(input)
    ds = drop_step(xr.open_dataset(ifile, chunks={})).drop_vars({"XLONG", "XLAT"})
    ds = ds.expand_dims({"member": 1}).expand_dims({"forecast": 1})
    ds.to_zarr(store, region=region)
    ds.close()


def _to_zip(input, output):
    # 7zz a -tzip archive.zarr.zip archive.zarr/.
    tmp = output + ".tmp.zip"
    subprocess.run(["7zz", "a", "-tzip", tmp, f"{input}/."])
    shutil.move(tmp, output)


def _create_hash(input_string: str) -> str:
    hash = hashlib.sha256()
    hash.update(input_string.encode("utf-8"))
    return f"{hash.hexdigest()}.nc"


def _cdo_execute(input):
    _cdo = Cdo(
        tempdir="./tmp",
        silent=False,
    )
    cdo_cache_dir = Path("./cdo_cache")
    cdo_cache_dir.mkdir(parents=True, exist_ok=True)
    output = cdo_cache_dir / _create_hash(input)
    if Path(output).exists():
        return output
    tmp = _cdo.copy(input=input)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    shutil.move(tmp, output)
    return output


if __name__ == "__main__":
    members = 25
    forecast_dates = pd.date_range("2009-01-01", periods=12 * 4, freq="MS")
    nforecast_times = len(forecast_dates)
    cdo_oprs = {
        "t2min": "-monmean -daymin",
        "t2max": "-monmean -daymax",
        "t2mean": "-monmean",
    }
    for field in ["t2min", "t2max", "t2mean"]:
        cdo_opr = cdo_oprs[field]
        fdate = forecast_dates[0].strftime("%Y%m")
        mem = 0
        zarr_out = f"data/ap84SeasRF/{field}.zarr"
        infile = f"/scratch/athippp/cylc-archive/ap84SeasRF/{fdate}02T0000Z/mem{mem+1}/outputs/wrf2d_T2.nc"
        cdo_input = f"-setname,{field} -seltimestep,2/7 {cdo_opr} {infile}"
        ifile = _cdo_execute(cdo_input)
        # ifile = infile
        ds = drop_step(xr.open_dataset(ifile, chunks={}))
        ds = (
            ds.expand_dims({"member": members})
            .expand_dims({"forecast": forecast_dates})
            .chunk({"member": 1, "forecast": 1})
        )
        print(ds)
        ds.to_zarr(zarr_out, compute=False, mode="w")

        with (
            LocalCluster(n_workers=100, threads_per_worker=1) as cluster,
            Client(cluster) as client,
        ):
            futures = []
            for mem in range(0, members):
                for nf, date in enumerate(forecast_dates):
                    fdate = date.strftime("%Y%m")
                    infile = f"/scratch/athippp/cylc-archive/ap84SeasRF/{fdate}02T0000Z/mem{mem+1}/outputs/wrf2d_T2.nc"
                    cdo_input = f"-setname,{field} -seltimestep,2/7 {cdo_opr} {infile}"
                    region = {
                        "member": slice(mem, mem + 1),
                        "forecast": slice(nf, nf + 1),
                    }
                    futures.append(
                        client.submit(
                            _write_to_zarr,
                            cdo_input,
                            zarr_out,
                            region,
                        )
                    )
            client.gather(futures)
        ds.close()
        _to_zip(zarr_out, f"{zarr_out}.zip")
        shutil.rmtree(zarr_out)
