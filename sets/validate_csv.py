#!/usr/bin/env python3
"""
Data validation script for CSV files in the sets folder.

This script validates CSV files against the schema defined in READ.md:
- Checks that all required columns are present
- Validates row count is exactly 158 (number of neighbourhoods in Ontario)
- Provides overview of nulls, empty strings, and 0 values

Usage:
    python validate_csv.py <csv_file_path>
    python validate_csv.py *.csv  # Validate all CSVs in current directory
"""

import argparse
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
import pandas as pd

# Fixed columns (no year suffix)
FIXED_COLUMNS = [
    'AREA_NAME', 'CLASSIFICATION', 'CLASSIFICATION_CODE', 'geometry_wkt',
    'geometry_type', 'Area', 'Bachelor Leased', 'bachelor_avg_lease_rate',
    '1_bedrooms_leased', '1_bed_room_avg_lease_rate', '2_bedrooms_leased',
    '2_bedrooms_avg_lease_rate', '3_bedrooms_leased',
    '3_bedrooms_avg_lease_rate', 'area_sq_meters', 'perimeter_meters',
    'park_count', 'total_stop_count', 'avg_stop_frequency', 'max_stop_frequency',
    'total_line_length_meters', 'transit_line_density',
    'distinct_route_count'
]

# Column patterns that should have a year suffix (2010-2024)
# Format: (base_pattern, required_suffix_pattern)
# The suffix pattern is used to match the year part
YEAR_PATTERN_COLUMNS = [
    ('ASSAULT', '_RATE_'),           # ASSAULT_YYYY and ASSAULT_RATE_YYYY
    ('AUTOTHEFT', '_RATE_'),         # AUTOTHEFT_YYYY and AUTOTHEFT_RATE_YYYY
    ('BIKETHEFT_RATE', ''),          # BIKETHEFT_RATE_YYYY (and BIKETHEFT_RATE_YYYY_1)
    ('BREAKENTER', ''),              # BREAKENTER_YYYY
    ('HOMICIDE', '_RATE_'),          # HOMICIDE_YYYY and HOMICIDE_RATE_YYYY
    ('ROBBERY', '_RATE_'),           # ROBBERY_YYYY and ROBBERY_RATE_YYYY
    ('SHOOTING', '_RATE_'),          # SHOOTING_YYYY and SHOOTING_RATE_YYYY
    ('THEFTFROMMV', '_RATE_'),       # THEFTFROMMV_YYYY and THEFTFROMMV_RATE_YYYY
    ('THEFTOVER', '_RATE_'),         # THEFTOVER_YYYY and THEFTOVER_RATE_YYYY
    ('POPULATION', ''),              # POPULATION_YYYY
]

# Valid years range
MIN_YEAR = 2010
MAX_YEAR = 2024
VALID_YEARS = set(range(MIN_YEAR, MAX_YEAR + 1))

# Expected number of rows (158 neighbourhoods in Ontario)
EXPECTED_ROW_COUNT = 158

# Most important column (must exist)
CRITICAL_COLUMN = 'bachelor_avg_lease_rate'


def extract_year_from_column(col_name: str) -> Optional[int]:
    """
    Extract year from a column name if it matches pattern _YYYY or _YYYY_*
    Returns the year if found and valid (2010-2024), None otherwise.
    """
    # Match pattern: _YYYY or _YYYY_ (with optional suffix)
    match = re.search(r'_(\d{4})(?:_|$)', col_name)
    if match:
        year = int(match.group(1))
        if year in VALID_YEARS:
            return year
    return None


def find_matching_columns(actual_columns: Set[str], base_pattern: str, 
                          suffix_pattern: str = '') -> Dict[str, List[str]]:
    """
    Find columns matching a base pattern with year suffix.
    
    Args:
        actual_columns: Set of actual column names in the dataframe
        base_pattern: Base pattern to match (e.g., 'ASSAULT', 'BIKETHEFT_RATE')
        suffix_pattern: Suffix pattern before year (e.g., '_RATE_' or '')
    
    Returns:
        Dictionary mapping expected column pattern to list of matching actual columns
    """
    matches = {}
    
    # Build regex pattern
    if suffix_pattern:
        # Pattern like: ASSAULT_RATE_2024
        pattern_re = re.compile(f'^{re.escape(base_pattern)}{re.escape(suffix_pattern)}\\d{{4}}(?:_|$)')
    else:
        # Pattern like: ASSAULT_2024 or BREAKENTER_2024
        pattern_re = re.compile(f'^{re.escape(base_pattern)}_\\d{{4}}(?:_|$)')
    
    for col in actual_columns:
        if pattern_re.match(col):
            year = extract_year_from_column(col)
            if year is not None:
                # Create key based on pattern
                if suffix_pattern:
                    # For patterns like ASSAULT_RATE_ -> key should be ASSAULT_RATE_YYYY
                    key = f"{base_pattern}{suffix_pattern}YYYY"
                else:
                    # For patterns like ASSAULT -> key should be ASSAULT_YYYY
                    key = f"{base_pattern}_YYYY"
                
                if key not in matches:
                    matches[key] = []
                matches[key].append(col)
    
    # Also check for variants like BIKETHEFT_RATE_YYYY_1
    if base_pattern == 'BIKETHEFT_RATE':
        variant_re = re.compile(f'^{re.escape(base_pattern)}_\\d{{4}}_\\d+$')
        for col in actual_columns:
            if variant_re.match(col):
                year = extract_year_from_column(col)
                if year is not None:
                    key = f"{base_pattern}_YYYY_1"
                    if key not in matches:
                        matches[key] = []
                    matches[key].append(col)
    
    return matches


def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str], List[str], Dict[str, str]]:
    """
    Validate that the dataframe has all required columns.
    Handles flexible year suffixes (2010-2024) for crime and population columns.
    
    Returns:
        (is_valid, missing_columns, extra_columns, year_mappings)
        year_mappings: Dict mapping expected pattern to actual column found
    """
    actual_columns = set(df.columns)
    missing_columns = []
    year_mappings = {}  # Maps expected pattern to actual column name
    
    # Check fixed columns (no year suffix)
    for col in FIXED_COLUMNS:
        if col not in actual_columns:
            missing_columns.append(col)
        else:
            year_mappings[col] = col
    
    # Check year-pattern columns
    for base_pattern, suffix_pattern in YEAR_PATTERN_COLUMNS:
        matches = find_matching_columns(actual_columns, base_pattern, suffix_pattern)
        
        if base_pattern == 'ASSAULT':
            # Need both ASSAULT_YYYY and ASSAULT_RATE_YYYY
            assault_matches = find_matching_columns(actual_columns, 'ASSAULT', '')
            rate_matches = find_matching_columns(actual_columns, 'ASSAULT', '_RATE_')
            
            if not assault_matches:
                missing_columns.append('ASSAULT_YYYY')
            else:
                # Use the first match found
                year_mappings['ASSAULT_YYYY'] = assault_matches[list(assault_matches.keys())[0]][0]
            
            if not rate_matches:
                missing_columns.append('ASSAULT_RATE_YYYY')
            else:
                year_mappings['ASSAULT_RATE_YYYY'] = rate_matches[list(rate_matches.keys())[0]][0]
        
        elif base_pattern == 'AUTOTHEFT':
            # Need both AUTOTHEFT_YYYY and AUTOTHEFT_RATE_YYYY
            autotheft_matches = find_matching_columns(actual_columns, 'AUTOTHEFT', '')
            rate_matches = find_matching_columns(actual_columns, 'AUTOTHEFT', '_RATE_')
            
            if not autotheft_matches:
                missing_columns.append('AUTOTHEFT_YYYY')
            else:
                year_mappings['AUTOTHEFT_YYYY'] = autotheft_matches[list(autotheft_matches.keys())[0]][0]
            
            if not rate_matches:
                missing_columns.append('AUTOTHEFT_RATE_YYYY')
            else:
                year_mappings['AUTOTHEFT_RATE_YYYY'] = rate_matches[list(rate_matches.keys())[0]][0]
        
        elif base_pattern == 'BIKETHEFT_RATE':
            # Need BIKETHEFT_RATE_YYYY and optionally BIKETHEFT_RATE_YYYY_1
            matches = find_matching_columns(actual_columns, 'BIKETHEFT_RATE', '')
            if not matches:
                missing_columns.append('BIKETHEFT_RATE_YYYY')
            else:
                # Find the one without suffix first
                for key, cols in matches.items():
                    for col in cols:
                        if not re.search(r'_\d+$', col):  # No trailing _N
                            year_mappings['BIKETHEFT_RATE_YYYY'] = col
                            break
                    else:
                        # If no match without suffix, use first one
                        year_mappings['BIKETHEFT_RATE_YYYY'] = cols[0]
                
                # Check for _1 variant
                variant_found = any(re.search(r'_\d+$', col) for cols in matches.values() for col in cols)
                if variant_found:
                    for key, cols in matches.items():
                        for col in cols:
                            if re.search(r'_\d+$', col):
                                year_mappings['BIKETHEFT_RATE_YYYY_1'] = col
                                break
        
        elif base_pattern == 'BREAKENTER':
            matches = find_matching_columns(actual_columns, 'BREAKENTER', '')
            if not matches:
                missing_columns.append('BREAKENTER_YYYY')
            else:
                year_mappings['BREAKENTER_YYYY'] = matches[list(matches.keys())[0]][0]
        
        elif base_pattern in ['HOMICIDE', 'ROBBERY', 'SHOOTING', 'THEFTFROMMV', 'THEFTOVER']:
            # Need both COUNT_YYYY and COUNT_RATE_YYYY
            count_matches = find_matching_columns(actual_columns, base_pattern, '')
            rate_matches = find_matching_columns(actual_columns, base_pattern, '_RATE_')
            
            if not count_matches:
                missing_columns.append(f'{base_pattern}_YYYY')
            else:
                year_mappings[f'{base_pattern}_YYYY'] = count_matches[list(count_matches.keys())[0]][0]
            
            if not rate_matches:
                missing_columns.append(f'{base_pattern}_RATE_YYYY')
            else:
                year_mappings[f'{base_pattern}_RATE_YYYY'] = rate_matches[list(rate_matches.keys())[0]][0]
        
        elif base_pattern == 'POPULATION':
            matches = find_matching_columns(actual_columns, 'POPULATION', '')
            if not matches:
                missing_columns.append('POPULATION_YYYY')
            else:
                year_mappings['POPULATION_YYYY'] = matches[list(matches.keys())[0]][0]
    
    # Find extra columns (not in fixed list and not matching any year pattern)
    extra_columns = []
    used_columns = set(year_mappings.values()) | set(FIXED_COLUMNS)
    
    for col in actual_columns:
        if col not in used_columns:
            # Check if it's a year-pattern column we already matched
            is_year_column = False
            for base_pattern, suffix_pattern in YEAR_PATTERN_COLUMNS:
                matches = find_matching_columns({col}, base_pattern, suffix_pattern)
                if matches:
                    is_year_column = True
                    break
            
            if not is_year_column:
                extra_columns.append(col)
    
    is_valid = len(missing_columns) == 0
    
    return is_valid, sorted(missing_columns), sorted(extra_columns), year_mappings


def validate_row_count(df: pd.DataFrame) -> Tuple[bool, int]:
    """
    Validate that the dataframe has exactly 158 rows.
    
    Returns:
        (is_valid, actual_count)
    """
    actual_count = len(df)
    is_valid = actual_count == EXPECTED_ROW_COUNT
    return is_valid, actual_count


def analyze_data_quality(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Analyze nulls, empty strings, and zero values for each column.
    
    Returns:
        Dictionary with column names as keys and statistics as values
    """
    results = {}
    
    for col in df.columns:
        col_data = df[col]
        
        # Count nulls
        null_count = col_data.isna().sum()
        null_pct = (null_count / len(df)) * 100
        
        # Count empty strings (for string columns)
        empty_count = 0
        if col_data.dtype == 'object':
            empty_count = (col_data == '').sum()
        empty_pct = (empty_count / len(df)) * 100
        
        # Count zeros (for numeric columns)
        zero_count = 0
        if pd.api.types.is_numeric_dtype(col_data):
            zero_count = (col_data == 0).sum()
        zero_pct = (zero_count / len(df)) * 100
        
        # Total "missing" (nulls + empty strings)
        total_missing = null_count + empty_count
        total_missing_pct = (total_missing / len(df)) * 100
        
        results[col] = {
            'null_count': int(null_count),
            'null_pct': round(null_pct, 2),
            'empty_count': int(empty_count),
            'empty_pct': round(empty_pct, 2),
            'zero_count': int(zero_count),
            'zero_pct': round(zero_pct, 2),
            'total_missing': int(total_missing),
            'total_missing_pct': round(total_missing_pct, 2),
            'dtype': str(col_data.dtype)
        }
    
    return results


def print_validation_report(file_path: Path, df: pd.DataFrame, 
                           schema_valid: bool, missing_cols: List[str], 
                           extra_cols: List[str], row_count_valid: bool,
                           actual_row_count: int, data_quality: Dict,
                           year_mappings: Dict[str, str]):
    """Print a comprehensive validation report."""
    
    print("\n" + "="*80)
    print(f"CSV VALIDATION REPORT")
    print("="*80)
    print(f"File: {file_path}")
    print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print("="*80)
    
    # Schema validation
    print("\n📋 SCHEMA VALIDATION")
    print("-" * 80)
    if schema_valid:
        print("✓ All required columns are present")
        
        # Show year mappings for year-pattern columns
        year_patterns = [k for k in year_mappings.keys() if '_YYYY' in k]
        if year_patterns:
            print(f"\n  Year mappings found (accepts years {MIN_YEAR}-{MAX_YEAR}):")
            # Group by base pattern
            pattern_groups = {}
            for pattern, actual_col in year_mappings.items():
                if '_YYYY' in pattern:
                    base = pattern.replace('_YYYY', '').replace('_RATE_YYYY', '').replace('_YYYY_1', '')
                    if base not in pattern_groups:
                        pattern_groups[base] = []
                    pattern_groups[base].append((pattern, actual_col))
            
            for base, mappings in sorted(pattern_groups.items()):
                for pattern, actual_col in mappings:
                    year = extract_year_from_column(actual_col)
                    print(f"    • {pattern} → {actual_col} (year: {year})")
    else:
        print("✗ SCHEMA VALIDATION FAILED")
        if missing_cols:
            print(f"  Missing {len(missing_cols)} required column(s):")
            for col in missing_cols:
                print(f"    • {col}")
        if extra_cols:
            print(f"  Found {len(extra_cols)} extra column(s) (not in schema):")
            for col in extra_cols[:10]:  # Show first 10
                print(f"    • {col}")
            if len(extra_cols) > 10:
                print(f"    ... and {len(extra_cols) - 10} more")
    
    # Critical column check
    print(f"\n🔑 CRITICAL COLUMN CHECK")
    print("-" * 80)
    if CRITICAL_COLUMN in df.columns:
        nulls = df[CRITICAL_COLUMN].isna().sum()
        print(f"✓ '{CRITICAL_COLUMN}' is present")
        if nulls > 0:
            print(f"  ⚠ Warning: {nulls} null values found ({nulls/len(df)*100:.1f}%)")
        else:
            print(f"  ✓ No null values")
    else:
        print(f"✗ CRITICAL: '{CRITICAL_COLUMN}' is MISSING!")
    
    # Row count validation
    print(f"\n📊 ROW COUNT VALIDATION")
    print("-" * 80)
    if row_count_valid:
        print(f"✓ Row count is correct: {actual_row_count} rows (expected: {EXPECTED_ROW_COUNT})")
    else:
        print(f"✗ ROW COUNT VALIDATION FAILED")
        print(f"  Expected: {EXPECTED_ROW_COUNT} rows")
        print(f"  Actual: {actual_row_count} rows")
        print(f"  Difference: {actual_row_count - EXPECTED_ROW_COUNT:+d} rows")
    
    # Data quality overview
    print(f"\n📈 DATA QUALITY OVERVIEW")
    print("-" * 80)
    
    # Summary statistics
    total_nulls = sum(stats['null_count'] for stats in data_quality.values())
    total_empties = sum(stats['empty_count'] for stats in data_quality.values())
    total_zeros = sum(stats['zero_count'] for stats in data_quality.values())
    
    print(f"Summary:")
    print(f"  • Total null values across all columns: {total_nulls:,}")
    print(f"  • Total empty string values: {total_empties:,}")
    print(f"  • Total zero values (numeric): {total_zeros:,}")
    
    # Columns with issues
    print(f"\nColumns with null values:")
    cols_with_nulls = [(col, stats) for col, stats in data_quality.items() 
                       if stats['null_count'] > 0]
    if cols_with_nulls:
        # Sort by null count descending
        cols_with_nulls.sort(key=lambda x: x[1]['null_count'], reverse=True)
        for col, stats in cols_with_nulls[:15]:  # Show top 15
            print(f"  • {col}: {stats['null_count']} nulls ({stats['null_pct']:.1f}%)")
        if len(cols_with_nulls) > 15:
            print(f"  ... and {len(cols_with_nulls) - 15} more columns with nulls")
    else:
        print("  ✓ No null values found")
    
    print(f"\nColumns with empty strings:")
    cols_with_empties = [(col, stats) for col, stats in data_quality.items() 
                         if stats['empty_count'] > 0]
    if cols_with_empties:
        cols_with_empties.sort(key=lambda x: x[1]['empty_count'], reverse=True)
        for col, stats in cols_with_empties[:10]:
            print(f"  • {col}: {stats['empty_count']} empty strings ({stats['empty_pct']:.1f}%)")
        if len(cols_with_empties) > 10:
            print(f"  ... and {len(cols_with_empties) - 10} more columns with empty strings")
    else:
        print("  ✓ No empty string values found")
    
    print(f"\nColumns with zero values (numeric):")
    cols_with_zeros = [(col, stats) for col, stats in data_quality.items() 
                       if stats['zero_count'] > 0 and pd.api.types.is_numeric_dtype(df[col])]
    if cols_with_zeros:
        cols_with_zeros.sort(key=lambda x: x[1]['zero_count'], reverse=True)
        for col, stats in cols_with_zeros[:10]:
            print(f"  • {col}: {stats['zero_count']} zeros ({stats['zero_pct']:.1f}%)")
        if len(cols_with_zeros) > 10:
            print(f"  ... and {len(cols_with_zeros) - 10} more columns with zeros")
    else:
        print("  ✓ No zero values found (or no numeric columns)")
    
    # Detailed table for all columns
    print(f"\n📋 DETAILED COLUMN ANALYSIS")
    print("-" * 80)
    print(f"{'Column':<40} {'Nulls':<8} {'Empty':<8} {'Zeros':<8} {'Dtype':<12}")
    print("-" * 80)
    
    # Show fixed columns
    for col in FIXED_COLUMNS:
        if col in data_quality:
            stats = data_quality[col]
            print(f"{col:<40} {stats['null_count']:<8} {stats['empty_count']:<8} "
                  f"{stats['zero_count']:<8} {stats['dtype']:<12}")
        else:
            print(f"{col:<40} {'MISSING':<8} {'N/A':<8} {'N/A':<8} {'N/A':<12}")
    
    # Show year-pattern columns with their actual names
    year_pattern_order = [
        'ASSAULT_YYYY', 'ASSAULT_RATE_YYYY',
        'AUTOTHEFT_YYYY', 'AUTOTHEFT_RATE_YYYY',
        'BIKETHEFT_RATE_YYYY', 'BIKETHEFT_RATE_YYYY_1',
        'BREAKENTER_YYYY',
        'HOMICIDE_YYYY', 'HOMICIDE_RATE_YYYY',
        'ROBBERY_YYYY', 'ROBBERY_RATE_YYYY',
        'SHOOTING_YYYY', 'SHOOTING_RATE_YYYY',
        'THEFTFROMMV_YYYY', 'THEFTFROMMV_RATE_YYYY',
        'THEFTOVER_YYYY', 'THEFTOVER_RATE_YYYY',
        'POPULATION_YYYY'
    ]
    
    for pattern in year_pattern_order:
        if pattern in year_mappings:
            actual_col = year_mappings[pattern]
            # Truncate if too long
            display_name = f"{pattern} ({actual_col})"
            if len(display_name) > 40:
                display_name = display_name[:37] + "..."
            
            if actual_col in data_quality:
                stats = data_quality[actual_col]
                print(f"{display_name:<40} {stats['null_count']:<8} {stats['empty_count']:<8} "
                      f"{stats['zero_count']:<8} {stats['dtype']:<12}")
            else:
                print(f"{display_name:<40} {'N/A':<8} {'N/A':<8} {'N/A':<8} {'N/A':<12}")
        else:
            print(f"{pattern:<40} {'MISSING':<8} {'N/A':<8} {'N/A':<8} {'N/A':<12}")
    
    # Overall validation status
    print("\n" + "="*80)
    all_valid = schema_valid and row_count_valid and (CRITICAL_COLUMN in df.columns)
    
    if all_valid:
        print("✓ VALIDATION PASSED - All checks successful!")
    else:
        print("✗ VALIDATION FAILED - Issues found:")
        if not schema_valid:
            print("  • Schema validation failed")
        if not row_count_valid:
            print("  • Row count validation failed")
        if CRITICAL_COLUMN not in df.columns:
            print("  • Critical column missing")
    
    print("="*80 + "\n")
    
    return all_valid


def validate_csv_file(file_path: Path) -> bool:
    """
    Validate a single CSV file.
    
    Returns:
        True if validation passes, False otherwise
    """
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    if not file_path.suffix.lower() == '.csv':
        print(f"Warning: File does not have .csv extension: {file_path}")
    
    try:
        # Load CSV
        print(f"Loading {file_path}...")
        df = pd.read_csv(file_path)
        print(f"Loaded successfully: {len(df)} rows, {len(df.columns)} columns")
        
        # Validate schema
        schema_valid, missing_cols, extra_cols, year_mappings = validate_schema(df)
        
        # Validate row count
        row_count_valid, actual_row_count = validate_row_count(df)
        
        # Analyze data quality
        data_quality = analyze_data_quality(df)
        
        # Print report
        all_valid = print_validation_report(
            file_path, df, schema_valid, missing_cols, extra_cols,
            row_count_valid, actual_row_count, data_quality, year_mappings
        )
        
        return all_valid
        
    except Exception as e:
        print(f"Error validating {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Validate CSV files against the schema defined in READ.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_csv.py 2024_dataframe.csv
  python validate_csv.py *.csv
  python validate_csv.py sets/*.csv
        """
    )
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='CSV file(s) to validate'
    )
    
    args = parser.parse_args()
    
    # Validate each file
    results = []
    for file_path in args.files:
        print(f"\n{'='*80}")
        print(f"Validating: {file_path.name}")
        print(f"{'='*80}")
        result = validate_csv_file(file_path)
        results.append((file_path, result))
    
    # Summary
    if len(results) > 1:
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        passed = sum(1 for _, result in results if result)
        failed = len(results) - passed
        for file_path, result in results:
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{status}: {file_path.name}")
        print(f"\nTotal: {passed} passed, {failed} failed")
        print("="*80 + "\n")
    
    # Exit with error code if any validation failed
    all_passed = all(result for _, result in results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

