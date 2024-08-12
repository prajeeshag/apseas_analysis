import colorcet as cc
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from utils import calculate_colormap_range, get_cmap

ds = xr.open_dataset(
    "/scratch/athippp/cylc-run/ap84SeasRF/run1/work/20090102T0000Z/share/mem1/wrfbdy_d01"
)

data_var_names = [str(v) for v in ds.data_vars if str(v).endswith("_BXS")]
bdy_width = 5
for vname in data_var_names:
    print(f"{vname}")
    if len(ds[vname].shape) != 4:
        continue
    dvar = ds[vname][0, :, :, :]
    if np.all(dvar == dvar[0, 0, 0]):
        print(f"{vname} - All values are: {dvar[0,0,0].values}")
        continue
    fig, axes = plt.subplots(
        nrows=5,
        ncols=1,
        figsize=(15, 15),
    )
    vmin, vmax = calculate_colormap_range(dvar.values)
    cmap, norm = get_cmap(np.linspace(vmin, vmax, 30), cc.cm["rainbow4"])
    for bd in range(bdy_width):
        print(f"{vname} - {bd}")
        var = dvar[bd, :, :].values
        x = np.arange(var.shape[1] + 1)
        y = np.arange(var.shape[0] + 1)
        cs = axes[bd].pcolormesh(x, y, var, cmap=cmap, norm=norm)

    plt.suptitle(f"{dvar.attrs["description"]} - {dvar.attrs["units"]}")
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    plt.colorbar(
        cs,
        cax=cbar_ax,
    )

    plt.savefig(f"{vname}_SEAS5_bdy.png")
    plt.close()

for vname in data_var_names:
    print(f"{vname}")
    if len(ds[vname].shape) == 4:
        continue

    dvar = ds[vname][0, :, :]
    if np.all(dvar == dvar[0, 0]):
        print(f"{vname} - All values are: {dvar[0,0].values}")
        continue
    fig, axes = plt.subplots(
        nrows=1,
        ncols=1,
        figsize=(15, 15),
    )
    vmin, vmax = calculate_colormap_range(dvar.values)
    cmap, norm = get_cmap(np.linspace(vmin, vmax, 30), cc.cm["rainbow4"])
    print(f"{vname} - {bd}")
    var = dvar[:, :].values
    x = np.arange(var.shape[1] + 1)
    y = np.arange(var.shape[0] + 1)
    cs = axes.pcolormesh(x, y, var, cmap=cmap, norm=norm)

    plt.suptitle(f"{dvar.attrs["description"]} - {dvar.attrs["units"]}")
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    plt.colorbar(
        cs,
        cax=cbar_ax,
    )

    plt.savefig(f"{vname}_SEAS5_bdy.png")
    plt.close()
