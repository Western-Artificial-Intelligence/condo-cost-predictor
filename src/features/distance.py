from math import radians, asin, sqrt, sin, cos
from typing import Union, Iterable
import numpy as np

def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance in km between two points (lon,lat in degrees)."""
    lon1_r, lat1_r, lon2_r, lat2_r = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2_r - lon1_r
    dlat = lat2_r - lat1_r
    a = sin(dlat / 2.0) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2.0) ** 2
    c = 2 * asin(sqrt(a))
    return 6371.0 * c

def haversine_vectorized(lon1: Union[float, Iterable], lat1: Union[float, Iterable],
                         lon2: Union[float, Iterable], lat2: Union[float, Iterable]) -> np.ndarray:
    """Vectorized haversine: supports scalars or array-like inputs. Returns numpy array (km)."""
    lon1_arr = np.asarray(lon1, dtype=float)
    lat1_arr = np.asarray(lat1, dtype=float)
    lon2_arr = np.asarray(lon2, dtype=float)
    lat2_arr = np.asarray(lat2, dtype=float)

    # broadcast to (n,m) if needed
    lon1_r = np.radians(lon1_arr)
    lat1_r = np.radians(lat1_arr)
    lon2_r = np.radians(lon2_arr)
    lat2_r = np.radians(lat2_arr)

    dlon = lon2_r - lon1_r
    dlat = lat2_r - lat1_r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    out = 6371.0 * c

    # propagate NaNs where inputs were NaN
    mask = np.isnan(lon1_arr) | np.isnan(lat1_arr) | np.isnan(lon2_arr) | np.isnan(lat2_arr)
    if out.shape == ():
        out = np.array(out)
    out = np.where(mask, np.nan, out)
    return out

def nearest_station_distance(neigh_lon, neigh_lat, stations_lon, stations_lat):
    """
    For each neighborhood point, return min distance to any station (km).
    Inputs: 1D arrays for neighborhood (n,) and stations (m,)
    Returns: numpy array (n,) with min distances.
    """
    neigh_lon = np.asarray(neigh_lon, dtype=float)
    neigh_lat = np.asarray(neigh_lat, dtype=float)
    stations_lon = np.asarray(stations_lon, dtype=float)
    stations_lat = np.asarray(stations_lat, dtype=float)

    # pairwise distances (n x m)
    dists = haversine_vectorized(
        neigh_lon[:, None], neigh_lat[:, None],
        stations_lon[None, :], stations_lat[None, :]
    )  # shape (n, m)
    return np.nanmin(dists, axis=1)