"""
MacroFactor data loading module.
"""
import pandas as pd
from pathlib import Path


def load_macrofactor_data(filepath: str) -> pd.DataFrame:
    """
    Load and merge MacroFactor XLSX export into a single DataFrame.
    
    Args:
        filepath: Path to MacroFactor data_weight.xlsx file
        
    Returns:
        Merged DataFrame with Date as index
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required sheets are missing or data is invalid
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if filepath.suffix.lower() != '.xlsx':
        raise ValueError("File must be .xlsx format")
    
    # Required sheets
    required_sheets = [
        'Calories & Macros',
        'Weight Trend',
        'Expenditure',
        'Scale Weight'
    ]
    
    try:
        excel_file = pd.ExcelFile(filepath)
    except Exception as e:
        raise ValueError(f"Failed to read Excel file: {str(e)}")
    
    # Validate required sheets exist
    missing_sheets = [sheet for sheet in required_sheets if sheet not in excel_file.sheet_names]
    if missing_sheets:
        raise ValueError(
            f"Missing required sheet(s): {', '.join(missing_sheets)}. "
            f"Expected sheets: {', '.join(required_sheets)}"
        )
    
    # Load each sheet
    try:
        df_macros = pd.read_excel(filepath, sheet_name='Calories & Macros')
        df_weight_trend = pd.read_excel(filepath, sheet_name='Weight Trend')
        df_expenditure = pd.read_excel(filepath, sheet_name='Expenditure')
        df_scale_weight = pd.read_excel(filepath, sheet_name='Scale Weight')
    except Exception as e:
        raise ValueError(f"Error reading sheet data: {str(e)}")
    
    # Validate Date column exists in all sheets
    for name, df in [
        ('Calories & Macros', df_macros),
        ('Weight Trend', df_weight_trend),
        ('Expenditure', df_expenditure),
        ('Scale Weight', df_scale_weight)
    ]:
        if 'Date' not in df.columns:
            raise ValueError(f"Missing 'Date' column in '{name}' sheet")
    
    # Merge into single DataFrame
    df_raw = df_weight_trend.copy()
    df_raw = df_raw.merge(df_macros, on='Date', how='left')
    df_raw = df_raw.merge(df_expenditure, on='Date', how='left')
    df_raw = df_raw.merge(
        df_scale_weight[['Date', 'Weight (kg)']], 
        on='Date', 
        how='left', 
        suffixes=('', '_scale')
    )
    
    # Set DateTime index
    df_raw['Date'] = pd.to_datetime(df_raw['Date'])
    df_raw.set_index('Date', inplace=True)
    df_raw = df_raw.sort_index()
    
    return df_raw
