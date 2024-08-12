import typing as t

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr


def get_lon_lat(ar: xr.DataArray):
    lon_lat = [None, None]

    for i, c in ar.coords.items():
        if all(x is not None for x in lon_lat):
            break
        try:
            units = c.attrs["units"]
            if units in ("degree_east", "degrees_east"):
                lon_lat[0] = c
                continue
            elif units in ("degree_north", "degrees_north"):
                lon_lat[1] = c
                continue
        except KeyError:
            pass
    return lon_lat


def load_single_data_variable(dataset: xr.Dataset) -> xr.DataArray:
    data_vars = []
    for var in dataset.data_vars:
        if not var.endswith("_bnds") and dataset[var].shape != ():
            data_vars.append(var)
    if len(data_vars) == 1:
        return dataset[data_vars[0]]
    elif len(data_vars) == 0:
        raise ValueError("No data variables found in the dataset.")
    else:
        raise ValueError(f"Multiple data variables found in the dataset: {data_vars}")


def detect_time_dimension(dataarray: xr.DataArray):
    for dim in dataarray.dims:
        if np.issubdtype(dataarray[dim].dtype, np.datetime64):
            return dim
    raise ValueError("No time dimension found in the dataarray.")


def get_cmap(levels, cmap=plt.get_cmap("viridis"), ncolors=256, extend="both"):
    norm = mcolors.BoundaryNorm(boundaries=levels, ncolors=ncolors, extend=extend)
    if extend == "neither" or extend is None:
        cmap.set_under("white", alpha=0)
        cmap.set_over("white", alpha=0)
    if extend == "min":
        cmap.set_over("white", alpha=0)
    if extend == "max":
        cmap.set_under("white", alpha=0)

    return cmap, norm


def calculate_colormap_range(
    arrays: t.List[t.Union[xr.DataArray, np.ndarray]],
    low_percentile: float = 2,
    high_percentile: float = 98,
) -> t.Tuple[float, float]:
    """
    Calculate colormap range based on the combined percentiles of multiple xarray DataArrays or numpy ndarrays.

    Parameters:
    - arrays: list of xarray.DataArray or numpy.ndarray
    - low_percentile: lower percentile for the colormap range (default is 2)
    - high_percentile: higher percentile for the colormap range (default is 98)

    Returns:
    - vmin: minimum value for the colormap range
    - vmax: maximum value for the colormap range
    """
    # Flatten and concatenate all arrays
    combined_flat = np.concatenate(
        [
            arr.values.flatten() if isinstance(arr, xr.DataArray) else arr.flatten()
            for arr in arrays
        ]
    )

    # Calculate the desired percentiles
    vmin = np.percentile(combined_flat, low_percentile)
    vmax = np.percentile(combined_flat, high_percentile)

    return vmin, vmax
