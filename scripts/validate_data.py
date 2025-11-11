"""
Data validation script for condo-cost-predictor pipeline.

Usage:
    python scripts/validate_data.py --input data/raw/neighbourhoods.csv --schema neighbourhoods
    python scripts/validate_data.py --input data/raw/*.csv --schema auto
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import pandera as pa
from pandera.errors import SchemaError

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.schemas import (
    NeighbourhoodsSchema,
    SocioeconomicsSchema,
    HousingIndicatorsSchema,
    PermitsSchema,
    TransitSchema,
    CrimeSchema,
    ParksSchema,
    MacroSchema,
)

# Map schema names to schema objects
SCHEMA_MAP = {
    "neighbourhoods": NeighbourhoodsSchema,
    "socioeconomics": SocioeconomicsSchema,
    "housing_indicators": HousingIndicatorsSchema,
    "permits": PermitsSchema,
    "transit": TransitSchema,
    "crime": CrimeSchema,
    "parks": ParksSchema,
    "macro": MacroSchema,
}


def detect_schema(file_path: Path) -> Optional[str]:
    """Detect schema type from filename."""
    filename = file_path.stem.lower()
    for schema_name in SCHEMA_MAP.keys():
        if schema_name in filename:
            return schema_name
    return None


def validate_file(file_path: Path, schema_name: str) -> Dict:
    """
    Validate a single file against a schema.
    
    Returns dict with validation results.
    """
    result = {
        "file": str(file_path),
        "schema": schema_name,
        "passed": False,
        "errors": [],
        "warnings": [],
        "row_count": 0,
    }
    
    try:
        # Load data
        df = pd.read_csv(file_path)
        result["row_count"] = len(df)
        
        # Get schema
        schema = SCHEMA_MAP.get(schema_name)
        if schema is None:
            result["errors"].append(f"Unknown schema: {schema_name}")
            return result
        
        # Validate
        schema.validate(df, lazy=True)
        result["passed"] = True
        
        # Check for warnings (nulls, duplicates)
        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                null_pct = (null_count / len(df)) * 100
                result["warnings"].append(
                    f"Column '{col}': {null_count} nulls ({null_pct:.2f}%)"
                )
        
        # Check for duplicate rows
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            result["warnings"].append(f"{dup_count} duplicate rows found")
        
    except SchemaError as e:
        result["errors"].append(str(e))
    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")
    
    return result


def print_report(results: List[Dict]):
    """Print validation report to console."""
    print("\n" + "="*70)
    print(" "*20 + "DATA VALIDATION REPORT")
    print("="*70 + "\n")
    
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    
    for result in results:
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"{status} | {result['file']}")
        print(f"         Schema: {result['schema']} | Rows: {result['row_count']}")
        
        if result["errors"]:
            print("         Errors:")
            for error in result["errors"]:
                # Truncate long error messages
                error_lines = error.split("\n")
                for line in error_lines[:5]:  # Show first 5 lines
                    print(f"           • {line[:100]}")
                if len(error_lines) > 5:
                    print(f"           ... ({len(error_lines) - 5} more lines)")
        
        if result["warnings"]:
            print("         Warnings:")
            for warning in result["warnings"][:5]:  # Show first 5 warnings
                print(f"           ⚠️  {warning}")
            if len(result["warnings"]) > 5:
                print(f"           ... ({len(result['warnings']) - 5} more warnings)")
        
        print()
    
    print("="*70)
    print(f"Total files: {total} | Passed: {passed} | Failed: {failed}")
    print("="*70 + "\n")
    
    if failed > 0:
        print("❌ Validation FAILED. Please fix errors above.")
        return False
    else:
        print("✅ All validations PASSED!")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Validate data files against expected schemas"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input file(s) to validate (supports wildcards)"
    )
    parser.add_argument(
        "--schema",
        required=True,
        help=f"Schema name: {', '.join(SCHEMA_MAP.keys())} or 'auto' to detect"
    )
    
    args = parser.parse_args()
    
    # Find files
    input_path = Path(args.input)
    if "*" in str(input_path):
        files = list(input_path.parent.glob(input_path.name))
    else:
        files = [input_path]
    
    if not files:
        print(f"❌ No files found matching: {args.input}")
        sys.exit(1)
    
    # Validate each file
    results = []
    for file_path in files:
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue
        
        schema_name = args.schema
        if schema_name == "auto":
            schema_name = detect_schema(file_path)
            if schema_name is None:
                print(f"⚠️  Could not auto-detect schema for {file_path}, skipping...")
                continue
        
        result = validate_file(file_path, schema_name)
        results.append(result)
    
    # Print report
    success = print_report(results)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
