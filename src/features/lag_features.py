import pandas as pd

def calculate_lagged_starts(df, lag_periods=[3, 6, 12]):
    """
    Calculate lagged condo construction starts.
    
    Parameters:
    -----------
    data : pd.DataFrame
        Must have columns: ['date', 'neighborhood', 'condo_starts']
    lag_periods : list
        List of lag periods in months (default: [3, 6, 12])
    
    Returns:
    --------
    pd.DataFrame with new columns:
        - lag_3_starts
        - lag_6_starts
        - lag_12_starts
    """
    # Data is sorted by neighborhood and date 
    df = df.sort_values(by=["neighborhood", "date"]).copy()

    # Create new df columns for lag intervals 
    for lag in lag_periods: 
        col_name = f"lag_{lag}_starts" 
        df[col_name] = df.groupby('neighborhood')['condo_starts'].shift(lag)
    
    return df

    
    