import numpy as np
import pandas as pd
from typing import List

def calculate_rolling_means(
    df: pd.DataFrame,
    price_col: str = "price",
    date_col: str = "date",
    group_col: str = "neighborhood",
    windows: List[int] = [3, 6, 12],
    use_log: bool = True,
    min_periods: int = 1,
    include_current: bool = False,
) -> pd.DataFrame:
    """
    Compute rolling mean price indices grouped by neighborhood.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with columns [group_col, date_col, price_col].
    price_col : str
        Column name for price or price_per_sqft.
    date_col : str
        Column name containing dates.
    group_col : str
        Column to group by (e.g., neighborhood).
    windows : list[int]
        Rolling windows in months (e.g., [3,6,12]).
    use_log : bool
        If True, compute rolling means on log(price) and back-transform.
    min_periods : int
        Minimum observations in window required to have a value.
    include_current : bool
        If False (default), rolling window uses only historical data (shifted by 1).
        If True, window includes the current row.

    Returns
    -------
    pd.DataFrame
        Copy of input df with added columns:
         - rolling_mean_{w}m         (back-transformed to original scale)
         - rolling_mean_log_{w}m     (present only if use_log=True)
    """
    required = {group_col, date_col, price_col}
    if not required.issubset(df.columns):
        missing = required.difference(df.columns)
        raise ValueError(f"DataFrame is missing required columns: {missing}")

    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    out = out.sort_values([group_col, date_col]).reset_index(drop=True)

    def safe_log(series: pd.Series) -> pd.Series:
        s = pd.to_numeric(series, errors="coerce")
        return pd.Series(np.log(s.where(s > 0)), index=series.index)

    for w in windows:
        if use_log:
            if include_current:
                rolled = out.groupby(group_col)[price_col].transform(
                    lambda s: safe_log(s).rolling(window=w, min_periods=min_periods).mean()
                )
            else:
                rolled = out.groupby(group_col)[price_col].transform(
                    lambda s: safe_log(s).shift(1).rolling(window=w, min_periods=min_periods).mean()
                )

            col_log = f"rolling_mean_log_{w}m"
            col_back = f"rolling_mean_{w}m"
            out[col_log] = rolled
            out[col_back] = np.exp(out[col_log])
        else:
            if include_current:
                rolled = out.groupby(group_col)[price_col].transform(
                    lambda s: pd.to_numeric(s, errors="coerce").rolling(window=w, min_periods=min_periods).mean()
                )
            else:
                rolled = out.groupby(group_col)[price_col].transform(
                    lambda s: pd.to_numeric(s, errors="coerce").shift(1).rolling(window=w, min_periods=min_periods).mean()
                )
            col_back = f"rolling_mean_{w}m"
            out[col_back] = rolled

    return out
