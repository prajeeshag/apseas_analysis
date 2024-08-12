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
    "SeasAP": (
        "data/20090102T0000Z/monthly/ap84SeasRF/t2_monmean_ap84SeasRF_ensmean.nc",
        "T2",
        1,
        -1,
    ),
    "ERA5": (
        "data/20090102T0000Z/monthly/era5/era5_surface_field_Ap.nc",
        "2t",
        1,
        None,
    ),
    "Seas5": (
        "data/20090102T0000Z/monthly/seas5/seas5_surface_monthly_Ap_ensmean.nc",
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
        [x.values - 273.15 for x in darrays],
    )
    print(f"Colormap min max = {vmin} {vmax}")
    cmap, norm = get_cmap(np.linspace(vmin, vmax, 30), cc.cm["rainbow4"])

    for i, k in enumerate(keys):
        # Model data for the given month
        ax = axes[m, i]
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
        ax.set_title(f"{k} - lead month {mm+1}")

    # Add a single colorbar for all subplots
cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
plt.colorbar(
    cs,
    cax=cbar_ax,
    label="2m temperature (C)",
)
plt.savefig(f"{fname}.png")
plt.close()
