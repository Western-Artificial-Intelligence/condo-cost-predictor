"""
Data validation script for Toronto condo rental data pipeline.

This script validates data files against predefined Pandera schemas and performs
comprehensive data quality checks including:
- Schema validation (column names, types, constraints)
- Missing value analysis with thresholds
- Geographic join sanity checks (duplicate neighborhoods, orphaned records)
- Data consistency checks (negative values, outliers)
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import pandera as pa
from datetime import datetime
import json
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.schemas import TorontoCondoDataSchema

# Feature schema globals (set in main from CLI)
FEATURE_SCHEMA_PATH = None  # type: Path | None
WRITE_FEATURE_SCHEMA = False

# Map schema names to schema objects
SCHEMA_MAP = {
    "toronto_condo": TorontoCondoDataSchema,
}

# Data quality thresholds
MISSING_VALUE_THRESHOLDS = {
    # Critical columns - should have minimal missing values
    "AREA_NAME": 0.0,  # 0% missing allowed
    "AREA_ID": 0.0,
    "geometry_wkt": 0.05,  # 5% missing allowed
    
    # Target variables - some missing is expected
    "Bachelor Leased": 0.5,  # 50% missing allowed (not all neighborhoods have data)
    "bachelor_avg_lease_rate": 0.5,
    "1_bedrooms_leased": 0.5,
    "1_bed_room_avg_lease_rate": 0.5,
    "2_bedrooms_leased": 0.5,
    "2_bedrooms_avg_lease_rate": 0.5,
    "3_bedrooms_leased": 0.5,
    "3_bedrooms_avg_lease_rate": 0.5,
    
    # Spatial features - should exist for all neighborhoods
    "area_sq_meters": 0.05,
    "perimeter_meters": 0.05,
    
    # Crime data - some missing is acceptable
    "default_crime": 0.4,  # 40% missing allowed for common crime
    "HOMICIDE": 0.8,  # 80% missing allowed for rare crimes (homicide, shooting)
    "SHOOTING": 0.8,
    
    # Transit - some neighborhoods may not have transit
    "total_stop_count": 0.3,
}

# === Feature schema (column contract) helpers ===

def save_feature_schema_yaml(df: pd.DataFrame, path: Path) -> None:
    """Write a simple column-contract YAML from a dataframe."""
    spec = {
        "generated_at": datetime.now().isoformat(),
        "columns": [
            {
                "name": str(col),
                "dtype": str(df[col].dtype),
                "allows_null": bool(df[col].isna().any()),
            }
            for col in df.columns
        ],
    }
    with open(path, "w") as f:
        yaml.safe_dump(spec, f, sort_keys=False)


def load_feature_schema_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def check_feature_schema(df: pd.DataFrame, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Compare dataframe columns to a YAML column-contract spec."""
    expected_cols = [c["name"] if isinstance(c, dict) else c for c in spec.get("columns", [])]
    expected_set = set(expected_cols)
    actual_set = set(map(str, df.columns))

    missing = sorted(expected_set - actual_set)
    unexpected = sorted(actual_set - expected_set)

    violations = []
    if missing:
        violations.append({
            "check": "feature_schema_missing",
            "message": f"Missing {len(missing)} expected column(s)",
            "details": missing[:20],
        })
    if unexpected:
        violations.append({
            "check": "feature_schema_unexpected",
            "message": f"Found {len(unexpected)} unexpected column(s)",
            "details": unexpected[:20],
        })

    # Optional dtype sanity check for overlapping columns
    dtype_issues = []
    spec_dtypes = {c["name"]: str(c.get("dtype")) for c in spec.get("columns", []) if isinstance(c, dict)}
    for col in sorted(expected_set & actual_set):
        actual = str(df[col].dtype)
        expected = spec_dtypes.get(col)
        if expected and expected != actual:
            dtype_issues.append({"column": col, "expected": expected, "actual": actual})
    if dtype_issues:
        violations.append({
            "check": "feature_schema_dtype",
            "message": f"Detected {len(dtype_issues)} dtype differences (FYI)",
            "details": dtype_issues[:10],
        })

    return {
        "violations": violations,
        "summary": {
            "expected_count": len(expected_set),
            "actual_count": len(actual_set),
            "matching": len(expected_set & actual_set),
        }
    }


def check_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for missing values and compare against thresholds.
    
    Returns:
        Dictionary with missing value analysis and violations
    """
    results = {
        "total_rows": len(df),
        "violations": [],
        "warnings": [],
        "summary": {}
    }
    
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_pct = missing_count / len(df)
        
        # Determine threshold
        if col in MISSING_VALUE_THRESHOLDS:
            threshold = MISSING_VALUE_THRESHOLDS[col]
        elif "HOMICIDE" in col or "SHOOTING" in col:
            threshold = MISSING_VALUE_THRESHOLDS["HOMICIDE"]  # Rare crimes
        elif any(crime in col for crime in ["ASSAULT", "AUTOTHEFT", "BIKETHEFT", "BREAKENTER", 
                                             "ROBBERY", "THEFTFROMMV", "THEFTOVER"]):
            threshold = MISSING_VALUE_THRESHOLDS["default_crime"]
        else:
            threshold = 1.0  # No threshold - just report
        
        results["summary"][col] = {
            "missing_count": int(missing_count),
            "missing_pct": float(missing_pct),
            "threshold": float(threshold)
        }
        
        # Check if violation
        if missing_pct > threshold:
            results["violations"].append({
                "column": col,
                "missing_pct": float(missing_pct),
                "threshold": float(threshold),
                "message": f"Column '{col}' has {missing_pct:.1%} missing values (threshold: {threshold:.1%})"
            })
        elif missing_pct > threshold * 0.8:  # Warning at 80% of threshold
            results["warnings"].append({
                "column": col,
                "missing_pct": float(missing_pct),
                "threshold": float(threshold),
                "message": f"Column '{col}' approaching threshold: {missing_pct:.1%} missing (threshold: {threshold:.1%})"
            })
    
    return results


def check_geographic_joins(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for geographic join issues:
    - Duplicate neighborhood entries
    - Mismatched area names from different joins
    - Orphaned or incomplete geographic data
    """
    results = {
        "duplicate_checks": {},
        "consistency_checks": {},
        "geometry_checks": {},
        "violations": []
    }
    
    # Check for duplicate neighborhoods
    if "AREA_NAME" in df.columns:
        duplicates = df[df.duplicated(subset=["AREA_NAME"], keep=False)]
        results["duplicate_checks"]["duplicate_area_names"] = {
            "count": len(duplicates),
            "neighborhoods": duplicates["AREA_NAME"].tolist() if len(duplicates) > 0 else []
        }
        if len(duplicates) > 0:
            results["violations"].append({
                "check": "duplicate_neighborhoods",
                "message": f"Found {len(duplicates)} duplicate neighborhood entries",
                "details": duplicates["AREA_NAME"].unique().tolist()
            })
    
    # Check AREA_ID duplicates
    if "AREA_ID" in df.columns:
        id_duplicates = df[df.duplicated(subset=["AREA_ID"], keep=False)]
        results["duplicate_checks"]["duplicate_area_ids"] = {
            "count": len(id_duplicates),
            "ids": id_duplicates["AREA_ID"].tolist() if len(id_duplicates) > 0 else []
        }
        if len(id_duplicates) > 0:
            results["violations"].append({
                "check": "duplicate_area_ids",
                "message": f"Found {len(id_duplicates)} duplicate AREA_ID values",
                "details": id_duplicates["AREA_ID"].unique().tolist()
            })
    
    # Check consistency between AREA_NAME and AREA_NAME_1 (crime join artifact)
    if "AREA_NAME" in df.columns and "AREA_NAME_1" in df.columns:
        mismatches = df[
            (df["AREA_NAME"].notna()) & 
            (df["AREA_NAME_1"].notna()) & 
            (df["AREA_NAME"] != df["AREA_NAME_1"])
        ]
        results["consistency_checks"]["area_name_mismatch"] = {
            "count": len(mismatches),
            "examples": mismatches[["AREA_NAME", "AREA_NAME_1"]].head(5).to_dict("records") if len(mismatches) > 0 else []
        }
        if len(mismatches) > 0:
            results["violations"].append({
                "check": "area_name_consistency",
                "message": f"Found {len(mismatches)} mismatches between AREA_NAME and AREA_NAME_1",
                "details": "Check geographic join integrity"
            })
    
    # Check geometry presence
    if "geometry_wkt" in df.columns:
        no_geometry = df[df["geometry_wkt"].isna()]
        results["geometry_checks"]["missing_geometry"] = {
            "count": len(no_geometry),
            "neighborhoods": no_geometry["AREA_NAME"].tolist() if "AREA_NAME" in no_geometry.columns and len(no_geometry) > 0 else []
        }
        if len(no_geometry) > 0:
            results["violations"].append({
                "check": "missing_geometry",
                "message": f"{len(no_geometry)} neighborhoods missing geometry data",
                "details": no_geometry["AREA_NAME"].tolist()[:10] if "AREA_NAME" in no_geometry.columns else []
            })
    
    # Check for orphaned records (has crime/transit data but missing core neighborhood info)
    if all(col in df.columns for col in ["AREA_NAME", "ASSAULT_2024"]):
        orphaned = df[df["AREA_NAME"].isna() & df["ASSAULT_2024"].notna()]
        results["consistency_checks"]["orphaned_crime_records"] = {
            "count": len(orphaned)
        }
        if len(orphaned) > 0:
            results["violations"].append({
                "check": "orphaned_records",
                "message": f"Found {len(orphaned)} records with crime data but no neighborhood identifier",
                "details": "Possible join issue in data pipeline"
            })
    
    return results


def check_data_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for data consistency issues:
    - Negative values in columns that should be positive
    - Extreme outliers
    - Logical inconsistencies
    """
    results = {
        "negative_value_checks": {},
        "outlier_checks": {},
        "logic_checks": {},
        "violations": []
    }
    
    # Check for negative values in count/rate columns
    positive_only_patterns = [
        "_leased", "lease_rate", "RATE_", "_count", "area_sq_meters", 
        "perimeter_meters", "POPULATION", "frequency", "density"
    ]
    
    for col in df.columns:
        if any(pattern in col for pattern in positive_only_patterns):
            if pd.api.types.is_numeric_dtype(df[col]):
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    results["negative_value_checks"][col] = {
                        "count": int(negative_count),
                        "min_value": float(df[col].min())
                    }
                    results["violations"].append({
                        "check": "negative_values",
                        "column": col,
                        "message": f"Found {negative_count} negative values in '{col}' (min: {df[col].min()})"
                    })
    
    # Check for extreme outliers in lease rates
    lease_rate_cols = [c for c in df.columns if "lease_rate" in c]
    for col in lease_rate_cols:
        if df[col].notna().sum() > 0:
            q99 = df[col].quantile(0.99)
            outliers = df[df[col] > q99 * 3]  # 3x the 99th percentile
            if len(outliers) > 0:
                results["outlier_checks"][col] = {
                    "count": len(outliers),
                    "threshold": float(q99 * 3),
                    "max_value": float(df[col].max()),
                    "examples": outliers[[col]].head(5).to_dict("records") if len(outliers) > 0 else []
                }
    
    # Logical check: area should be positive
    if "area_sq_meters" in df.columns:
        zero_area = df[df["area_sq_meters"] <= 0]
        if len(zero_area) > 0:
            results["logic_checks"]["zero_or_negative_area"] = {
                "count": len(zero_area),
                "neighborhoods": zero_area["AREA_NAME"].tolist() if "AREA_NAME" in zero_area.columns else []
            }
            results["violations"].append({
                "check": "invalid_area",
                "message": f"Found {len(zero_area)} neighborhoods with zero or negative area",
                "details": zero_area["AREA_NAME"].tolist()[:10] if "AREA_NAME" in zero_area.columns else []
            })
    
    return results


def print_validation_report(schema_validation: Dict, missing_values: Dict, 
                           geographic: Dict, consistency: Dict, file_path: Path):
    """Print a comprehensive validation report."""
    print("\n" + "="*80)
    print(f"DATA VALIDATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"File: {file_path}")
    print("="*80)
    
    # Schema validation summary
    print("\nSCHEMA VALIDATION")
    print("-" * 80)
    if schema_validation.get("passed"):
        print("✓ Schema validation PASSED")
        print(f"  • {schema_validation.get('row_count', 0)} rows validated successfully")
    else:
        print("✗ Schema validation FAILED")
        print(f"  • Error: {schema_validation.get('error', 'Unknown error')}")
    
    # Missing values summary
    print("\nMISSING VALUE ANALYSIS")
    print("-" * 80)
    violations = missing_values.get("violations", [])
    warnings = missing_values.get("warnings", [])
    
    if violations:
        print(f"✗ {len(violations)} VIOLATIONS found:")
        for v in violations[:10]:  # Show first 10
            print(f"  • {v['message']}")
        if len(violations) > 10:
            print(f"  ... and {len(violations) - 10} more")
    else:
        print("✓ No missing value violations")
    
    if warnings:
        print(f"\n⚠ {len(warnings)} WARNINGS:")
        for w in warnings[:5]:
            print(f"  • {w['message']}")
    
    # Geographic checks summary
    print("\nGEOGRAPHIC JOIN INTEGRITY")
    print("-" * 80)
    geo_violations = geographic.get("violations", [])
    
    if geo_violations:
        print(f"✗ {len(geo_violations)} ISSUES found:")
        for v in geo_violations:
            print(f"  • {v['check']}: {v['message']}")
    else:
        print("✓ No geographic join issues detected")
    
    # Data consistency summary
    print("\n DATA CONSISTENCY CHECKS")
    print("-" * 80)
    cons_violations = consistency.get("violations", [])
    
    if cons_violations:
        print(f"✗ {len(cons_violations)} ISSUES found:")
        for v in cons_violations[:10]:
            print(f"  • {v.get('check', 'unknown')}: {v.get('message', 'No message')}")
    else:
        print("✓ No data consistency issues detected")
    
    # Overall summary
    print("\n" + "="*80)
    total_issues = (
        (0 if schema_validation.get("passed") else 1) +
        len(violations) +
        len(geo_violations) +
        len(cons_violations)
    )
    
    if total_issues == 0:
        print("✓ VALIDATION PASSED - All checks successful!")
        print("="*80 + "\n")
        return True
    else:
        print(f"✗ VALIDATION FAILED - {total_issues} issue(s) found")
        print("="*80 + "\n")
        return False


def detect_schema(file_path: Path) -> str:
    """
    Auto-detect schema based on file name.
    
    Args:
        file_path: Path to the data file
        
    Returns:
        Schema name string
    """
    filename = file_path.stem.lower()
    
    if "tor_neighborhood" in filename or "condo" in filename:
        return "toronto_condo"
    
    raise ValueError(f"Cannot auto-detect schema for file: {file_path.name}")


def validate_file(file_path: Path, schema_name: Optional[str] = None, lazy: bool = True) -> bool:
    """
    Validate a data file against a schema.
    
    Args:
        file_path: Path to the data file
        schema_name: Name of the schema to use (auto-detected if None)
        lazy: If True, collect all validation errors; if False, fail on first error
        
    Returns:
        True if validation passes, False otherwise
    """
    # Auto-detect schema if not specified
    if schema_name is None:
        try:
            schema_name = detect_schema(file_path)
            print(f"Auto-detected schema: {schema_name}")
        except ValueError as e:
            print(f"Error: {e}")
            print("Please specify a schema with --schema")
            return False
    
    # Get schema
    schema = SCHEMA_MAP.get(schema_name)
    if schema is None:
        print(f"Error: Unknown schema '{schema_name}'")
        print(f"Available schemas: {', '.join(SCHEMA_MAP.keys())}")
        return False
    
    # Load data
    print(f"Loading data from {file_path}...")
    try:
        if file_path.suffix.lower() == ".parquet":
            df = pd.read_parquet(file_path)
        elif file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
        else:
            print(f"Error: Unsupported file format '{file_path.suffix}'")
            print("Supported formats: .parquet, .csv")
            return False
    except Exception as e:
        print(f"Error loading file: {e}")
        return False
    
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # === SCHEMA VALIDATION ===
    print(f"\n Running schema validation...")
    schema_results = {"passed": False, "error": None, "row_count": len(df)}
    
    try:
        if lazy:
            # Lazy validation - collect all errors
            validated_df = schema.validate(df, lazy=True)
            schema_results["passed"] = True
        else:
            # Strict validation - fail on first error
            validated_df = schema.validate(df, lazy=False)
            schema_results["passed"] = True
    except Exception as e:
        schema_results["passed"] = False
        schema_results["error"] = str(e)
    
    # === DATA QUALITY CHECKS ===
    print(f"Running data quality checks...")
    
    missing_results = check_missing_values(df)
    print(f"  • Missing value analysis complete")
    
    geographic_results = check_geographic_joins(df)
    print(f"  • Geographic join integrity checks complete")
    
    consistency_results = check_data_consistency(df)
    print(f"  • Data consistency checks complete")

    # === FEATURE SCHEMA (COLUMN CONTRACT) CHECK ===
    if FEATURE_SCHEMA_PATH:
        try:
            spec = load_feature_schema_yaml(Path(FEATURE_SCHEMA_PATH))
            feature_results = check_feature_schema(df, spec)
            # Merge violations into consistency violations so they appear in report
            for v in feature_results.get("violations", []):
                consistency_results.setdefault("violations", []).append(v)
            print(f"  • Feature schema check complete (expected {feature_results['summary']['expected_count']} cols)")
        except Exception as e:
            consistency_results.setdefault("violations", []).append({
                "check": "feature_schema_error",
                "message": f"Error checking feature schema: {e}",
            })
            print(f"  • Feature schema check error: {e}")
    
    # === PRINT REPORT ===
    validation_passed = print_validation_report(
        schema_results, missing_results, geographic_results, 
        consistency_results, file_path
    )
    
    # === SAVE DETAILED REPORT ===
    save_report = False  # TODO: Add as CLI argument
    if save_report:
        report_path = file_path.parent / f"{file_path.stem}_validation_report.json"
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "file": str(file_path),
            "schema": schema_name,
            "schema_validation": schema_results,
            "missing_values": missing_results,
            "geographic_checks": geographic_results,
            "data_consistency": consistency_results,
            "overall_passed": validation_passed
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"Detailed report saved to: {report_path}")
    
    return validation_passed


def main():
    parser = argparse.ArgumentParser(
        description="Validate data files against predefined schemas"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to the input data file (.parquet or .csv)",
    )
    parser.add_argument(
        "--schema",
        "-s",
        choices=list(SCHEMA_MAP.keys()),
        help="Schema to validate against (auto-detected if not specified)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use strict validation (fail on first error)",
    )
    parser.add_argument(
        "--feature-schema",
        type=Path,
        help="Path to YAML file describing expected columns (column contract)",
    )
    parser.add_argument(
        "--write-feature-schema",
        action="store_true",
        help="Generate a feature_schema YAML from the input file and exit",
    )
    
    args = parser.parse_args()

    # Set globals for use inside validate_file
    global FEATURE_SCHEMA_PATH, WRITE_FEATURE_SCHEMA
    FEATURE_SCHEMA_PATH = args.feature_schema
    WRITE_FEATURE_SCHEMA = args.write_feature_schema
    
    # Check file exists
    if not args.input.exists():
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    # If requested, write the feature schema and exit
    if WRITE_FEATURE_SCHEMA:
        try:
            # Load the input file quickly
            if args.input.suffix.lower() == ".parquet":
                df = pd.read_parquet(args.input)
            else:
                df = pd.read_csv(args.input)
            out_path = FEATURE_SCHEMA_PATH or (args.input.parent / "feature_schema.yaml")
            save_feature_schema_yaml(df, out_path)
            print(f"Wrote feature schema: {out_path}")
            sys.exit(0)
        except Exception as e:
            print(f"Error writing feature schema: {e}")
            sys.exit(1)
    
    # Validate
    success = validate_file(args.input, args.schema, lazy=not args.strict)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
