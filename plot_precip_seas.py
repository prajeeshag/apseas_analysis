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

    Times = slice(lead - 1, lead + nmons - 1)
    ds = ds.sel(forecast=[year in list(yearrange) for year in ds.forecast.dt.year])
    ds = ds.sel(forecast=ds.forecast.dt.month == forecast_month).isel(Times=Times)
    ds = ds.isel(south_north=slice(5, -5), west_east=slice(5, -5))
    # get DateTimeIndex by adding Times months to forecast.values
    dates = pd.to_datetime([])
    print(ds["forecast"].values)
    for i in range(nmons):
        dates = dates.union(
            pd.to_datetime(ds["forecast"].values) + pd.DateOffset(months=lead + i)
        )
    ds = ds.mean("Times")

    ds = ens_stat(ensstat, ds)
    return ds, dates


def ens_stat(ensstat, ds):
    if ensstat == "mean":
        ds = ds.mean("member").mean("forecast")
    elif ensstat == "median":
        ds = ds.median("member").mean("forecast")
    else:
        ds = ds.isel(member=0).mean("forecast")
    return ds


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
    ds = ens_stat(ensstat, ds)
    ds = ds * 86400 * 30 * 1000  # convert to mm/month
    ds.load()
    if "SEAS5" not in REGRIDDERS:
        REGRIDDERS["SEAS5"] = xe.Regridder(ds, to_grid, "bilinear")
    ds = REGRIDDERS["SEAS5"](ds)
    return ds


@memory.cache(ignore=["to_grid"])
def ymonmean_precip_era5(dates, to_grid):
    yearmons = [(dt.year, dt.month) for dt in dates]
    print(yearmons)
    ds = xr.open_dataset(
        "obs_data/era5_surface_fields.nc",
        chunks={},
    )["mtpr"]
    ds = ds.sel(
        time=[
            t for t in pd.to_datetime(ds.time.values) if (t.year, t.month) in yearmons
        ]
    )
    ds = ds.mean("time")
    ds = ds * 86400 * 30  # convert to mm/month
    ds.load()
    if "ERA5" not in REGRIDDERS:
        REGRIDDERS["ERA5"] = xe.Regridder(ds, to_grid, "bilinear")
    ds = REGRIDDERS["ERA5"](ds)
    return ds


@memory.cache(ignore=["to_grid"])
def ymonmean_precip_trmm(dates, to_grid):
    yearmons = [(dt.year, dt.month) for dt in dates]
    print(yearmons)
    ds = xr.open_dataset(
        "/project/k10035/athippp/DATA/TRMM/monthly/trmm_2000-2019_monthly.nc",
        chunks={},
    )["precip"]
    ds = ds.sel(
        time=[
            t for t in pd.to_datetime(ds.time.values) if (t.year, t.month) in yearmons
        ]
    )
    ds = ds.mean("time")
    ds = ds * 30  # convert to mm/month
    ds.load()
    if "TRMM" not in REGRIDDERS:
        REGRIDDERS["TRMM"] = xe.Regridder(ds, to_grid, "bilinear")
    ds = REGRIDDERS["TRMM"](ds)
    return ds


REGRIDDERS = {}


def make_seas_plots(fname, lead, enstat, field="precip", yearrange=range(2009, 2013)):
    nmons = 3
    # seas = {12: "DJF", 3: "MAM", 6: "JJA", 9: "SON"}
    seas = {12: "DJF", 6: "JJA"}
    proj = ccrs.LambertConformal(
        central_longitude=45,
        central_latitude=27,
        standard_parallels=(18, 27),
    )
    fig, axes1 = plt.subplots(
        nrows=len(seas),
        ncols=3,
        figsize=(5 * 3, 5 * len(seas)),
        subplot_kw={"projection": proj},
    )

    for n, (mon, seaname) in enumerate(seas.items()):
        month = mon
        if month < 1:
            month += 12
        apseas, dates = ymonmean_precip_apseas(
            month,
            lead,
            ensstat=enstat,
            nmons=nmons,
            field=field,
            yearrange=yearrange,
        )
        seas5 = ymonmean_precip_seas5(
            month,
            lead,
            to_grid=apseas,
            ensstat=enstat,
            nmons=nmons,
            yearrange=yearrange,
        )
        era5 = ymonmean_precip_era5(dates, to_grid=apseas)
        # trmm = ymonmean_precip_trmm(dates, to_grid=apseas)

        data_dict = {
            "APSEAS": apseas,
            "SEAS5": seas5,
            "ERA5": era5,
            #    "TRMM": trmm,
        }
        levels = [1, 3, 6, 9, 12, 16, 20, 25, 30, 40, 50, 75, 100, 150]
        cmap, norm = get_cmap(levels, cc.cm["rainbow4"], extend="max")
        axes = axes1[n, :]
        for i, (dname, data) in enumerate(data_dict.items()):
            print(dname)
            # Model data for the given month
            ax = axes[i]
            lon, lat = get_lon_lat(data)
            values = data.values
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
            ax.set_title(dname, loc="left")
            ax.set_title(seaname, loc="right")

    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    startyear = list(yearrange)[0]
    endyear = list(yearrange)[-1]
    title_year = f"{startyear}-{endyear}"
    if startyear == endyear:
        title_year = f"{startyear}"
    fig.suptitle(
        f"Rainfall {title_year} (Lead {lead})"
    )  # Add a single colorbar for all subplots
    plt.colorbar(
        cs,
        cax=cbar_ax,
        label=f"Rainfall (mm) - {title_year} ",
    )
    plt.savefig(f"{fname}_seas_lead{lead}_ens{enstat}_{field}_{title_year}.png")
    plt.gca()
    plt.gcf()
    plt.close()


def plot_c2nc_ratio_apseas(fname, lead, enstat):
    nmons = 3
    seas = {12: "DJF", 3: "MAM", 6: "JJA", 9: "SON"}
    proj = ccrs.LambertConformal(
        central_longitude=45,
        central_latitude=27,
        standard_parallels=(18, 27),
    )
    fig, axes1 = plt.subplots(
        nrows=2,
        ncols=2,
        figsize=(15, 15),
        subplot_kw={"projection": proj},
    )
    axes = axes1.ravel()
    levels = [0, 3, 6, 9, 12, 16, 20, 25, 30, 40, 50, 75, 100, 120]

    cmap, norm = get_cmap(levels, cc.cm["rainbow4"])
    for n, (mon, seaname) in enumerate(seas.items()):
        month = mon
        if month < 1:
            month += 12
        precip, _ = ymonmean_precip_apseas(
            month, lead, ensstat=enstat, nmons=nmons, field="precip"
        )
        precipc, _ = ymonmean_precip_apseas(
            month, lead, ensstat=enstat, nmons=nmons, field="precipc"
        )

        data = (precipc / precip) * 100.0

        ax = axes[n]
        lon, lat = get_lon_lat(data)
        values = data.values
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
        ax.set_title(seaname, loc="right")

    fig.suptitle(
        f"Convective Rainfall / Total Rainfall (Forecast Lead {lead})"
    )  # Add a single colorbar for all subplots
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    plt.colorbar(
        cs,
        cax=cbar_ax,
        label="Rainfall (mm)",
    )
    plt.savefig(f"{fname}_seas_lead{lead}_ens{enstat}.png")
    plt.gca()
    plt.gcf()
    plt.close()


if __name__ == "__main__":
    lead = 1
    enstat = "mem0"
    make_seas_plots(fname, lead, enstat, yearrange=range(2009, 2013))
    # plot_c2nc_ratio_apseas("convetive2total_ratio_apseas", lead, enstat)
