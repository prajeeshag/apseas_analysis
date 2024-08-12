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
    "ApSEAS": (
        "data/20090102T0000Z/monthly/ap84SeasRF/t2_monmean_ap84SeasRF_ensmean.nc",
        "T2",
        1,
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

keys = ("ApSEAS",)
ref = ds["ApSEAS"][0, :, :]
for m in range(1, 5):
    fig, axes = plt.subplots(
        nrows=1,
        ncols=len(keys),
        figsize=(15, 7),
        subplot_kw={"projection": proj},
    )

    darrays = [ds[i][m, :, :] - ref for i in keys]

    vmin, vmax = calculate_colormap_range(
        [x.values for x in darrays],
    )
    print(f"Colormap min max = {vmin} {vmax}")
    cmap, norm = get_cmap(np.linspace(vmin, vmax, 30), cc.cm["rainbow4"])

    for i, k in enumerate(keys):
        # Model data for the given month
        ax = axes
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
        ax.set_title(f"{k} - lead month {m+1}")

    # Add a single colorbar for all subplots
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    plt.colorbar(
        cs,
        cax=cbar_ax,
        label="2m temperature (C)",
    )
    plt.savefig(f"{fname}_lead_month-{m+1}.png")
    plt.close()
