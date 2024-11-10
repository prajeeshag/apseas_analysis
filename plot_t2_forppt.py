from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import colorcet as cc
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from utils import calculate_colormap_range, get_cmap, get_lon_lat

fname = Path(__file__).stem

datasets: dict[str, tuple[Path, str]] = {
    "CPLD": (
        "data/20090102T0000Z/monthly/ap84SeasRF/mem1/t2_monmean_ap84SeasRF_mem1.nc",
        "T2",
        1,
        -1,
    ),
    "ERA5": (
        "data/era5/monthly/era5_surface_monthly_2009.nc",
        "2t",
        1,
        None,
    ),
    "ECMWF": (
        "data/20090102T0000Z/monthly/seas5/seas5_surface_monthly_mem1.nc",
        "2t",
        0,
        -1,
    ),
}

ds: dict[str, xr.DataArray] = {}
for k in datasets:
    ds[k] = xr.open_dataset(datasets[k][0])[datasets[k][1]][
        datasets[k][2] : datasets[k][3]
    ]

proj = ccrs.LambertConformal(
    central_longitude=45,
    central_latitude=27,
    standard_parallels=(18, 27),
)

keys = ("CPLD", "ECMWF", "ERA5")
fig, axes = plt.subplots(
    nrows=len(keys),
    ncols=1,
    figsize=(5, 15),
    subplot_kw={"projection": proj},
)
for m in range(1, 2):
    mm = m + 2
    darrays = [ds[i][mm, :, :] for i in keys]

    vmin, vmax = calculate_colormap_range(
        [x.values - 273.15 for x in darrays],
    )
    vmin = 15
    vmax = 40
    print(f"Colormap min max = {vmin} {vmax}")
    cmap, norm = get_cmap(np.linspace(vmin, vmax, 11), cc.cm["rainbow4"])

    for i, k in enumerate(keys):
        # Model data for the given month
        ax = axes[i]
        darray = darrays[i]
        lon, lat = get_lon_lat(darray)
        values = darray.values - 273.15
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
        ax.set_title(f"{k}", fontsize=18, loc="left")
        if k in ["CPLD", "ECMWF"]:
            ax.set_title("ensemble mean", loc="right")

cbar_ax = fig.add_axes([0.15, 0.08, 0.7, 0.02])

cbar = plt.colorbar(
    cs,
    cax=cbar_ax,
    orientation="horizontal",
)

cbar.ax.tick_params(labelsize=18)
cbar.set_label("2m temperature (C)", fontsize=18)

plt.savefig(f"{fname}.png")
plt.savefig(f"{fname}.png", bbox_inches="tight")
plt.close()
