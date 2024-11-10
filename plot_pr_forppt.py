from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import colorcet as cc
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from utils import calculate_colormap_range, get_cmap, get_lon_lat

fname = Path(__file__).stem

ens_titles = {"ensmean": "Ensemble mean", "ensmedian": "Ensemble median"}

ens = "ensmean"

datasets: dict[str, tuple[str, str, int, int, int]] = {
    "CPLD": (
        f"data/20090102T0000Z/monthly/ap84SeasRF/pr_monmean_ap84SeasRF_{ens}.nc",
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
    "ECMWF": (
        f"data/20090102T0000Z/monthly/seas5/seas5_surface_monthly_{ens}.nc",
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

keys = ("CPLD", "ECMWF", "ERA5")
fig, axes = plt.subplots(
    ncols=1,
    nrows=len(keys),
    figsize=(5, 15),
    subplot_kw={"projection": proj},
)
for m in range(1, 2):
    mm = m + 2
    darrays = [ds[i][mm, :, :] for i in keys]

    vmin, vmax = calculate_colormap_range(
        [x.values for x in darrays],
    )
    vmin = 0
    vmax = 3
    print(f"Colormap min max = {vmin} {vmax}")
    cmap, norm = get_cmap(
        np.linspace(vmin, vmax, 11), cc.cm["CET_CBTL3_r"], extend="max"
    )

    for i, k in enumerate(keys):
        # Model data for the given month
        ax = axes[i]
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
        ax.set_title(f"{k}", fontsize=18, loc="left")
        if k in ["CPLD", "ECMWF"]:
            ax.set_title(ens_titles[ens], loc="right")
    # fig.suptitle("June forecast from the January 2009 run")

cbar_ax = fig.add_axes([0.15, 0.08, 0.7, 0.02])
cbar = plt.colorbar(
    cs,
    cax=cbar_ax,
    orientation="horizontal",
    label="Rainfall (mm/day)",
)
cbar.set_label("Rainfall (mm/day)", fontsize=18)
cbar.ax.tick_params(labelsize=18)
plt.savefig(f"{fname}_{ens}.png", bbox_inches="tight")
plt.close()
