from calendar import month_abbr
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import colorcet as cc
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import xesmf as xe
from joblib import Memory
from matplotlib import gridspec

from utils import get_cmap, get_lon_lat

fname = Path(__file__).stem
memory = Memory("cache")


@memory.cache
def ymonmean_precip_wrfapseas(
    exp_name: str,
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

    ds_nc = xr.open_dataset(
        f"/scratch/athippp/cylc-archive/{exp_name}_H200911/20091102T0000Z/mem1/outputs/wrf2d_RAINNC.nc",
        chunks={},
    )["RAINNC"]
    ds_c = xr.open_dataset(
        f"/scratch/athippp/cylc-archive/{exp_name}_H200911/20091102T0000Z/mem1/outputs/wrf2d_RAINC.nc",
        chunks={},
    )["RAINC"]
    ds = ds_nc + ds_c
    year_month = ds.Times.dt.year.astype(str) + ds.Times.dt.month.astype(str).str.zfill(
        2
    )
    ds = ds.assign_coords(year_month=year_month)
    ds = ds.groupby("year_month").map(lambda x: x.isel(Times=-1))
    print(ds)
    ds1 = ds[1:, :, :]
    ds1.values = ds.values[1:, :, :] - ds.values[:-1, :, :]
    ds = ds1[:-1, :, :]
    ds = ds.isel(south_north=slice(5, -5), west_east=slice(5, -5))
    ds = ds.mean("year_month")
    return ds


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
    # seas = {12: "DJF", 6: "JJA"}
    seas = {12: "DJF"}
    proj = ccrs.LambertConformal(
        central_longitude=45,
        central_latitude=27,
        standard_parallels=(18, 27),
    )
    fig = plt.figure(figsize=(5 * 2, 5 * 3))
    axes = []
    gs = gridspec.GridSpec(3, 2, height_ratios=[1, 1, 1])
    for i in range(3):
        for j in range(2):
            axes.append(fig.add_subplot(gs[i, j], projection=proj))
    # axes.append(fig.add_subplot(gs[2, :], projection=proj))

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
        wrfapseas = ymonmean_precip_wrfapseas(
            "WRF8kmSEAS",
            month,
            lead,
            ensstat=enstat,
            nmons=nmons,
            field=field,
            yearrange=yearrange,
        )
        cpldapseas_no_nudge = ymonmean_precip_wrfapseas(
            "nSNCPLD8kmSEAS",
            month,
            lead,
            ensstat=enstat,
            nmons=nmons,
            field=field,
            yearrange=yearrange,
        )
        wrfapseas_no_nudge = ymonmean_precip_wrfapseas(
            "nSNWRF8kmSEAS",
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
            "CPLDSEAS": apseas,
            "WRFSEAS": wrfapseas,
            "CPLDSEASnoNudge": cpldapseas_no_nudge,
            "WRFSEASnoNudge": wrfapseas_no_nudge,
            "SEAS5": seas5,
            "ERA5": era5,
            #    "TRMM": trmm,
        }
        levels = [1, 3, 6, 9, 12, 16, 20, 25, 30, 40, 50, 75, 100, 150]
        cmap, norm = get_cmap(levels, cc.cm["rainbow4"], extend="max")
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
            ax.set_title(dname, loc="left", fontsize=16)
            ax.set_title(seaname, loc="right", fontsize=16)

    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    startyear = list(yearrange)[0]
    endyear = list(yearrange)[-1]
    title_year = f"{startyear}-{endyear}"
    if startyear == endyear:
        title_year = f"{startyear}"
    fig.suptitle(
        f"Rainfall {title_year} (Lead {lead})",
        fontsize=16,
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


if __name__ == "__main__":
    lead = 1
    enstat = "mem0"
    make_seas_plots(fname, lead, enstat, yearrange=range(2009, 2010))
    # plot_c2nc_ratio_apseas("convetive2total_ratio_apseas", lead, enstat)
