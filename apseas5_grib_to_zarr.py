import hashlib
import logging
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import xarray as xr
from cdo import Cdo
from dask.distributed import Client, LocalCluster

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def drop_step(ds):
    return ds.drop_vars({})


def _write_to_zarr(input, store, region):
    logger.info(f"Writing {region} to {store}")
    ds = xr.open_dataset(infile1, chunks={})
    ds = ds.groupby("valid_time.month").mean()
    ds = ds.isel(month=slice(1, 7))
    ds = ds.rename_dims({"month": "step"}).drop_vars(
        {"time", "month", "longitude", "latitude", "isobaricInhPa"}
    )
    ds = ds.rename_vars({"q": field})
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


if __name__ == "__main__":
    members = 25
    forecast_dates = pd.date_range("2009-01-01", periods=12 * 4, freq="MS")
    nforecast_times = len(forecast_dates)
    file_names = {
        "hus": "wrf_isobaricInhPa_q.grb2",
    }
    for field in file_names:
        file_name = file_names[field]
        cdo_opr = "-monmean"
        fdate = forecast_dates[0].strftime("%Y%m")
        mem = 0
        zarr_out = f"data/ap84SeasRF/{field}.zarr"
        infile1 = f"/scratch/athippp/cylc-archive/ap84SeasRF/{fdate}02T0000Z/mem{mem+1}/outputs/{file_name}"
        ds = xr.open_dataset(infile1, chunks={})
        ds = ds.groupby("valid_time.month").mean()
        ds = ds.isel(month=slice(1, 7))
        ds = ds.rename_dims({"month": "step"}).drop_vars({"time", "month"})
        ds = ds.rename_vars({"longitude": "XLONG", "latitude": "XLAT", "q": field})
        ds = (
            ds.expand_dims({"member": members})
            .expand_dims({"forecast": forecast_dates})
            .chunk({"member": 1, "forecast": 1})
        )
        ds["XLONG"].load()
        ds["XLAT"].load()
        ds.to_zarr(zarr_out, compute=False, mode="w")
        logger.info(ds)
        with (
            LocalCluster(n_workers=25, threads_per_worker=1) as cluster,
            Client(cluster) as client,
        ):
            futures = []
            for mem in range(0, members):
                for nf, date in enumerate(forecast_dates):
                    fdate = date.strftime("%Y%m")

                    infile1 = f"/scratch/athippp/cylc-archive/ap84SeasRF/{fdate}02T0000Z/mem{mem+1}/outputs/{file_name}"
                    region = {
                        "member": slice(mem, mem + 1),
                        "forecast": slice(nf, nf + 1),
                    }
                    futures.append(
                        client.submit(
                            _write_to_zarr,
                            infile1,
                            zarr_out,
                            region,
                        )
                    )
            client.gather(futures)
        ds.close()
        _to_zip(zarr_out, f"{zarr_out}.zip")
        shutil.rmtree(zarr_out)
