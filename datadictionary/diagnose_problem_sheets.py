#!/usr/bin/env python3
"""
Diagnostic Script for Problem Sheets
Analyzes the sheets that failed to load and identifies specific issues
"""

import pandas as pd
import numpy as np

EXCEL_FILE = 'teradata-mcp-server/datadictionary/MTDT_vx.xlsx'

# Sheets that failed based on your error log
PROBLEM_SHEETS = [
    'BUS_GLSRY',      # Error 502: parameter 6 type mismatch
    'TBL',            # Error 502: parameter 16 type mismatch (TIMESTAMP issue)
    'TBL_JOINS',      # Error 502: parameter 13 type mismatch (TIMESTAMP issue)
    'TBL_PARTN',      # Error 6706: untranslatable character
]

def analyze_sheet_dtypes(sheet_name, df):
    """Analyze data types in a sheet"""
    print(f"\n{'='*80}")
    print(f"Sheet: {sheet_name}")
    print(f"{'='*80}\n")
    
    print("Column Data Types:")
    print("-" * 80)
    for i, (col, dtype) in enumerate(df.dtypes.items(), 1):
        print(f"{i:2d}. {col:30s} -> {str(dtype):15s}", end="")
        
        # Check for mixed types in object columns
        if dtype == 'object':
            non_null = df[col].dropna()
            if len(non_null) > 0:
                sample = non_null.head(5).tolist()
                types = set(type(x).__name__ for x in non_null)
                if len(types) > 1:
                    print(f" [MIXED TYPES: {types}]")
                else:
                    print(f" [All {list(types)[0]}]")
                print(f"     Sample values: {sample}")
            else:
                print(" [All NULL]")
        else:
            print()


def check_for_problematic_characters(sheet_name, df):
    """Check for characters that might cause encoding issues"""
    print(f"\nChecking for problematic characters in {sheet_name}...")
    print("-" * 80)
    
    problem_found = False
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]):
            for idx, val in df[col].items():
                if isinstance(val, str):
                    # Check for non-ASCII characters
                    problematic_chars = [c for c in val if ord(c) > 127 and ord(c) not in range(160, 256)]
                    if problematic_chars:
                        problem_found = True
                        print(f"Row {idx}, Column '{col}':")
                        print(f"  Value: {val[:100]}")
                        print(f"  Problematic characters: {set(problematic_chars)}")
                        print(f"  Character codes: {[ord(c) for c in set(problematic_chars)]}")
                        # Only show first few instances
                        break
    
    if not problem_found:
        print("No problematic characters found")


def analyze_timestamp_columns(sheet_name, df):
    """Analyze columns that might have timestamp type issues"""
    print(f"\nAnalyzing potential TIMESTAMP columns in {sheet_name}...")
    print("-" * 80)
    
    for col in df.columns:
        if 'TS' in col.upper() or 'DATE' in col.upper() or 'TIME' in col.upper():
            print(f"\nColumn: {col}")
            print(f"  Pandas dtype: {df[col].dtype}")
            print(f"  Non-null count: {df[col].notna().sum()}")
            print(f"  Sample values:")
            for val in df[col].dropna().head(5):
                print(f"    {val} (type: {type(val).__name__})")


def main():
    print("="*80)
    print("DIAGNOSTIC ANALYSIS OF PROBLEM SHEETS")
    print("="*80)
    
    for sheet_name in PROBLEM_SHEETS:
        print(f"\n\n{'#'*80}")
        print(f"# Analyzing: {sheet_name}")
        print(f"{'#'*80}")
        
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
            
            # Show basic info
            print(f"\nRows: {len(df):,}")
            print(f"Columns: {len(df.columns)}")
            
            # Analyze data types
            analyze_sheet_dtypes(sheet_name, df)
            
            # Check for timestamp issues
            analyze_timestamp_columns(sheet_name, df)
            
            # Check for character encoding issues (especially for TBL_PARTN)
            if sheet_name == 'TBL_PARTN':
                check_for_problematic_characters(sheet_name, df)
            
        except Exception as e:
            print(f"Error analyzing {sheet_name}: {str(e)}")
    
    # Additional analysis for specific error cases
    print("\n\n" + "="*80)
    print("SPECIFIC ERROR ANALYSIS")
    print("="*80)
    
    # BUS_GLSRY - Error at parameter 6 (COL_DATA_TYP_LEN)
    print("\n\nBUS_GLSRY - Parameter 6 issue (COL_DATA_TYP_LEN):")
    print("-" * 80)
    df = pd.read_excel(EXCEL_FILE, sheet_name='BUS_GLSRY')
    col = df.columns[5]  # 6th column (0-indexed)
    print(f"Column name: {col}")
    print(f"Data type: {df[col].dtype}")
    print(f"Sample values:")
    print(df[col].head(110))  # Show values around row 107 where error occurred
    print(f"\nValue types in first 110 rows:")
    for i, val in enumerate(df[col].head(110)):
        if not pd.isna(val):
            print(f"  Row {i}: {val} (type: {type(val).__name__})")


if __name__ == "__main__":
    main()
