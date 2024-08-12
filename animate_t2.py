from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import colorcet as cc
import diskcache as dc
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from cdo import Cdo

from utils import calculate_colormap_range, get_cmap, get_lon_lat

fname = Path(__file__).stem

cdo = Cdo(tempdir="cache")

exp = "ap84SeasRF_WRF_ERA5sfc"
date = "20090102T0000Z"

dataset = f"/scratch/athippp/cylc-archive/{exp}/{date}/mem1/outputs/wrf2d_T2.nc"

cache = dc.Cache("cache")


@cache.memoize()
def get_data(dataset) -> xr.DataArray:
    dset = cdo.daymean(input=dataset)
    dvar = xr.open_dataset(dset)["T2"].load()
    return dvar


dvar = get_data(dataset)

proj = ccrs.LambertConformal(
    central_longitude=45,
    central_latitude=27,
    standard_parallels=(18, 27),
)

fig, axes = plt.subplots(
    nrows=1,
    ncols=1,
    figsize=(15, 15),
    subplot_kw={"projection": proj},
)
dvar.values -= 273.15
vmin, vmax = calculate_colormap_range(dvar.values)
cmap, norm = get_cmap(np.linspace(vmin, vmax, 30), cc.cm["rainbow4"])
lon, lat = get_lon_lat(dvar)
cs = axes.pcolormesh(
    lon,
    lat,
    dvar.values[0, :, :],
    transform=ccrs.PlateCarree(),
    cmap=cmap,
    norm=norm,
)
axes.coastlines()
axes.add_feature(cfeature.BORDERS)
cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
plt.colorbar(cs, cax=cbar_ax, label="2m temperature (C)")
print(dvar.shape)


def update(frame):
    print(frame)
    axes.clear()
    cax = axes.pcolormesh(
        lon,
        lat,
        dvar.values[frame, :, :],
        cmap=cmap,
        norm=norm,
        transform=ccrs.PlateCarree(),
    )
    return (cax,)


ani = animation.FuncAnimation(fig, update, frames=range(dvar.shape[0]), blit=False)

ani.save(f"{fname}_{exp}_{date}.mp4", writer="ffmpeg", fps=10)
