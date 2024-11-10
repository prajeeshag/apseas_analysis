import shutil
import subprocess

import pandas as pd
import xarray as xr
from dask.distributed import Client, LocalCluster


def drop_step(ds):
    return ds.drop_vars({"step", "valid_time", "surface", "time", "number"})


def _write_to_zarr(gfile, store, region, nforecast, nmembers):
    ds = drop_step(xr.open_dataset(gfile, chunks={})).drop_vars(
        {"latitude", "longitude"}
    )
    ds = ds.expand_dims({"member": 1}).expand_dims({"forecast": 1})
    print(region)
    ds.to_zarr(store, region=region)
    ds.close()


def _to_zip(input, output):
    # 7zz a -tzip archive.zarr.zip archive.zarr/.
    tmp = output + ".tmp.zip"
    subprocess.run(["7zz", "a", "-tzip", tmp, f"{input}/."])
    shutil.move(tmp, output)


if __name__ == "__main__":
    members = 25
    forecast_dates = pd.date_range("2000-01-01", periods=12 * 24, freq="MS")
    nforecast_times = len(forecast_dates)
    for field in ["t2min", "t2max", "precip", "dewpt2"]:
        fdate = forecast_dates[0].strftime("%Y%m")
        mem = 0
        zarr_out = f"output/{field}.zarr"
        ds = drop_step(
            xr.open_dataset(
                f"output/{field}/{field}_seas5_monthly_{fdate}_mem{mem}.grib", chunks={}
            )
        )
        ds = (
            ds.expand_dims({"member": members})
            .expand_dims({"forecast": forecast_dates})
            .chunk({"member": 1, "forecast": 1})
        )
        print(ds)
        ds.to_zarr(zarr_out, compute=False, mode="w")
        drop_vars = set(ds.data_vars) - set(["XLAT", "XLONG"])
        with (
            LocalCluster(n_workers=150, threads_per_worker=1) as cluster,
            Client(cluster) as client,
        ):
            futures = []
            for mem in range(0, members):
                for nf, date in enumerate(forecast_dates):
                    fdate = date.strftime("%Y%m")
                    gfile = (
                        f"output/{field}/{field}_seas5_monthly_{fdate}_mem{mem}.grib"
                    )
                    region = {
                        "member": slice(mem, mem + 1),
                        "forecast": slice(nf, nf + 1),
                    }
                    futures.append(
                        client.submit(
                            _write_to_zarr,
                            gfile,
                            zarr_out,
                            region,
                            len(forecast_dates),
                            members,
                        )
                    )
            client.gather(futures)
        ds.close()
        _to_zip(zarr_out, f"{zarr_out}.zip")
        shutil.rmtree(zarr_out)
