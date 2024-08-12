from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import colorcet as cc
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from utils import calculate_colormap_range, get_cmap, get_lon_lat

fname = Path(__file__).stem

datasets: dict[str, tuple[str, str, int, int, int]] = {
    "SeasAP": (
        "data/20090102T0000Z/monthly/ap84SeasRF/mem1/pr_monmean_ap84SeasRF_mem1.nc",
        "RAINC",
        1,
        -1,
        86400,
    ),
    "ERA5": (
        "data/era5/monthly/era5_surface_monthly_2009.nc",
        "mtpr",
        1,
        -1,
        86400,
    ),
    "Seas5": (
        "data/20090102T0000Z/monthly/seas5/seas5_surface_monthly_mem1.nc",
        "tprate",
        0,
        -1,
        86400000,
    ),
}

ds: dict[str, xr.DataArray] = {}
for k in datasets:
    ds[k] = xr.open_dataset(datasets[k][0])[datasets[k][1]][
        datasets[k][2] : datasets[k][3]
    ]
    ds[k].values *= datasets[k][4]

proj = ccrs.LambertConformal(
    central_longitude=45,
    central_latitude=27,
    standard_parallels=(18, 27),
)

keys = ("SeasAP", "Seas5", "ERA5")
fig, axes = plt.subplots(
    nrows=3,
    ncols=len(keys),
    figsize=(15, 15),
    subplot_kw={"projection": proj},
)
for m in range(3):
    mm = m + 2
    darrays = [ds[i][mm, :, :] for i in keys]

    vmin, vmax = calculate_colormap_range(
        [x.values for x in darrays],
    )
    print(f"Colormap min max = {vmin} {vmax}")
    cmap, norm = get_cmap(
        np.linspace(vmin, vmax, 30), cc.cm["CET_CBTL3_r"], extend="max"
    )

    for i, k in enumerate(keys):
        # Model data for the given month
        ax = axes[m, i]
        darray = darrays[i]
        lon, lat = get_lon_lat(darray)
        values = darray.values
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
        ax.set_title(f"{k} - lead month {mm+1}")

    # Add a single colorbar for all subplots
cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
plt.colorbar(
    cs,
    cax=cbar_ax,
    label="Rainfall (mm/day)",
)
plt.savefig(f"{fname}.png")
plt.close()
