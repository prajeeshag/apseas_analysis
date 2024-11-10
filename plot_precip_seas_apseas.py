from calendar import month_abbr
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import colorcet as cc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
import xesmf as xe
from joblib import Memory

from utils import calculate_colormap_range, get_cmap, get_lon_lat

fname = Path(__file__).stem
memory = Memory("cache")


@memory.cache
def ymonmean_precip_apseas(
    month: int,
    lead: int,
    ensstat: str = "median",
    nmons: int = 1,
    field: str = "precip",
    yearrange=range(2009, 2013),
):
    assert lead > 0 and lead < 6
    assert month > 0 and month < 13
    assert nmons > 0 and nmons < 6
    assert lead + nmons - 1 < 6

    ds = xr.open_zarr(f"data/ap84SeasRF/{field}.zarr.zip")[field]
    forecast_month = month - lead
    if forecast_month < 1:
        forecast_month += 12
    # ds(forecast, member, Times, lat, lon)
    # select month from forecast and median over members
    print(list(yearrange))
    ds = ds.sel(forecast=[year in list(yearrange) for year in ds.forecast.dt.year])
    Times = slice(lead - 1, lead + nmons - 1)
    ds = ds.sel(forecast=ds.forecast.dt.month == forecast_month).isel(Times=Times)
    # get DateTimeIndex by adding Times months to forecast.values
    dates = pd.to_datetime([])
    print(f"forecast date: {ds["forecast"].values}")
    for i in range(nmons):
        dates = dates.union(
            pd.to_datetime(ds["forecast"].values) + pd.DateOffset(months=lead + i)
        )
    ds = ds.mean("Times")
    if ensstat == "mean":
        ds = ds.median("member").mean("forecast")
    else:
        ds = ds.median("member").mean("forecast")
    return ds, dates


@memory.cache(ignore=["to_grid"])
def ymonmean_precip_seas5(
    month: int,
    lead: int,
    to_grid: xr.Dataset,
    ensstat: str = "median",
    nmons: int = 1,
    yearrange=range(2009, 2013),
):
    assert lead > 0 and lead < 6
    assert month > 0 and month < 13
    ds = xr.open_zarr("/project/k10035/athippp/DATA/SEAS5/monthly/precip.zarr.zip")[
        "tprate"
    ]
    forecast_month = month - lead
    if forecast_month < 1:
        forecast_month += 12

    Times = slice(lead - 1, lead + nmons - 1)
    ds = ds.sel(forecast=[year in list(yearrange) for year in ds.forecast.dt.year])
    ds = (
        ds.sel(forecast=ds.forecast.dt.month == forecast_month)
        .isel(step=Times)
        .mean("step")
    )
    if ensstat == "mean":
        ds = ds.median("member").mean("forecast")
    else:
        ds = ds.median("member").mean("forecast")
    ds = ds * 86400 * 30 * 1000  # convert to mm/month
    ds.load()
    if "SEAS5" not in REGRIDDERS:
        REGRIDDERS["SEAS5"] = xe.Regridder(ds, to_grid, "bilinear")
    ds = REGRIDDERS["SEAS5"](ds)
    return ds


REGRIDDERS = {}


def main():
    proj = ccrs.LambertConformal(
        central_longitude=45,
        central_latitude=27,
        standard_parallels=(18, 27),
    )
    fig, axes1 = plt.subplots(
        nrows=1,
        ncols=1,
        figsize=(15, 15),
        subplot_kw={"projection": proj},
    )

    era5, _ = ymonmean_precip_apseas(6, 1, nmons=3, yearrange=range(2009, 2010))
    print(era5)
    vmin, vmax = 0, 100
    cmap, norm = get_cmap(
        np.linspace(vmin, vmax, 25), cc.cm["CET_CBTL3_r"], extend="max"
    )
    ax = axes1
    lon, lat = get_lon_lat(era5)
    values = era5.values
    cs = ax.pcolormesh(
        lon,
        lat,
        values,
        transform=ccrs.PlateCarree(),
        cmap=cmap,
        norm=norm,
    )

    ax.coastlines()
    ax.add_feature(cfeature.BORDERS)
    ax.set_title("Rainfall - 2009 JJA - APSEAS")
    cbar_ax = fig.add_axes([0.15, 0.08, 0.7, 0.02])
    plt.colorbar(
        cs,
        cax=cbar_ax,
        orientation="horizontal",
        label="Rainfall (mm)",
    )
    plt.savefig("rainfall_jja_apseas_2009.png", bbox_inches="tight")
    plt.gca()
    plt.gcf()
    plt.close()


if __name__ == "__main__":
    lead = 1
    enstat = "median"
    main()
