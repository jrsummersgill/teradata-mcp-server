#!/usr/bin/env python3
"""
Teradata Excel Loader Script
Loads worksheets from Excel file to Teradata database
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
import getpass

# Teradata ML imports
# for managing connections
from teradataml import create_context, get_context, remove_context
# for setting configure options
from teradataml import configure
# DataFrames
from teradataml.dataframe.dataframe import DataFrame, in_schema
# for dropping tables or views
from teradataml.dbutils.dbutils import db_drop_table, db_drop_view 
# for fastload, copy_to_sql, fastexport
from teradataml.dataframe.fastload import fastload
from teradataml.dataframe.copy_to import copy_to_sql

# Configuration
EXCEL_FILE = 'teradata-mcp-server/datadictionary/MTDT_vx.xlsx'
DATABASE_NAME = 'ADLSTE_HCLS_MCP_DATA_DICT'
FASTLOAD_THRESHOLD = 100000  # Use fastload for sheets with more than 100K rows
DRY_RUN = False  # Set to False to actually execute the loads

# Teradata Connection Configuration
# TODO: Update these values before executing
TD_HOST = 'tddevtest.td.teradata.com'
TD_USERNAME = 'js186127'
TD_LOGMECH = 'LDAP'
TD_SSLMODE = 'ALLOW'


def clean_column_name(col_name):
    """
    Clean column name to be Teradata-compatible
    """
    # Replace spaces and special characters with underscores
    clean_name = str(col_name).strip()
    clean_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in clean_name)
    
    # Remove leading/trailing underscores
    clean_name = clean_name.strip('_')
    
    # Ensure it doesn't start with a number
    if clean_name and clean_name[0].isdigit():
        clean_name = 'COL_' + clean_name
    
    # Teradata column name max length is 30 characters
    if len(clean_name) > 30:
        clean_name = clean_name[:30]
    
    return clean_name.upper()


def clean_table_name(table_name):
    """
    Clean table name to be Teradata-compatible
    """
    clean_name = str(table_name).strip()
    clean_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in clean_name)
    clean_name = clean_name.strip('_')
    
    # Teradata table name max length is 30 characters
    if len(clean_name) > 30:
        clean_name = clean_name[:30]
    
    return clean_name.upper()

def prepare_dataframe_for_load(df, sheet_name=""):
    """
    Prepare DataFrame for loading into Teradata
    - Clean column names
    - Handle NaN values
    - Convert data types appropriately
    - Fix character encoding issues
    - Handle known data type issues
    """
    # Clean column names
    df.columns = [clean_column_name(col) for col in df.columns]
    
    # Replace NaN with None for SQL compatibility
    df = df.replace({np.nan: None})
    
    # Handle specific known issues by sheet
    if sheet_name == 'BUS_GLSRY':
        # COL_DATA_TYP_LEN has mixed types (int and string like "16,2")
        # Convert all to string to match VARCHAR(6) in table definition
        if 'COL_DATA_TYP_LEN' in df.columns:
            df['COL_DATA_TYP_LEN'] = df['COL_DATA_TYP_LEN'].astype(str).replace('nan', None)
    
    if sheet_name == 'TBL':
        # LST_UPDT_TS has mixed datetime and string types
        if 'LST_UPDT_TS' in df.columns:
            # Convert all to string first, then try to parse as datetime
            df['LST_UPDT_TS'] = pd.to_datetime(df['LST_UPDT_TS'], errors='coerce')
    
    if sheet_name == 'TBL_JOINS':
        # RHT_SIDE_1_VAL_TXT has mixed datetime, string, and int
        # LFT_SIDE_VAL_TXT has mixed datetime and string
        if 'RHT_SIDE_1_VAL_TXT' in df.columns:
            df['RHT_SIDE_1_VAL_TXT'] = df['RHT_SIDE_1_VAL_TXT'].apply(
                lambda x: str(x) if x is not None and not pd.isna(x) else None
            )
        if 'LFT_SIDE_VAL_TXT' in df.columns:
            df['LFT_SIDE_VAL_TXT'] = df['LFT_SIDE_VAL_TXT'].apply(
                lambda x: str(x) if x is not None and not pd.isna(x) else None
            )
    
    # Handle data type conversions and encoding issues
    for col in df.columns:
        # Convert datetime columns - keep as datetime objects for teradataml
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            # Keep as datetime, teradataml will handle the conversion
            pass
        
        # Handle string columns - fix encoding issues
        elif pd.api.types.is_object_dtype(df[col]):
            # Check if this is a mixed-type column that should be string
            non_null = df[col].dropna()
            if len(non_null) > 0:
                # If we have mixed types (datetime + string), convert all to string
                types = set(type(x).__name__ for x in non_null.head(100))
                if 'datetime' in types and len(types) > 1:
                    df[col] = df[col].apply(
                        lambda x: str(x) if x is not None and not pd.isna(x) else None
                    )
            
            # Clean up string data to remove untranslatable characters
            df[col] = df[col].apply(lambda x: clean_string_value(x) if x is not None else None)
        
        # Ensure numeric columns stay numeric (don't let pandas convert to string)
        elif pd.api.types.is_numeric_dtype(df[col]):
            # Replace inf/-inf with None
            df[col] = df[col].replace([np.inf, -np.inf], None)
    
    return df


def diagnose_dataframe_issues(sheet_name, df):
    """
    Diagnose potential data loading issues in a DataFrame
    Returns list of warnings
    """
    warnings = []
    table_name = clean_table_name(sheet_name)
    
    # Check for mixed types in columns
    for col in df.columns:
        col_clean = clean_column_name(col)
        
        # Skip if column is all null
        if df[col].isna().all():
            continue
            
        # Check for mixed types in object columns
        if pd.api.types.is_object_dtype(df[col]):
            non_null = df[col].dropna()
            if len(non_null) > 0:
                types = non_null.apply(type).unique()
                if len(types) > 1:
                    warnings.append(f"  ⚠ {col_clean}: Mixed types detected {[t.__name__ for t in types]}")
                
                # Check for problematic characters
                has_unicode = False
                for val in non_null.head(100):  # Check first 100 non-null values
                    if isinstance(val, str):
                        if any(ord(c) > 127 and ord(c) not in range(160, 256) for c in val):
                            has_unicode = True
                            break
                
                if has_unicode:
                    warnings.append(f"  ⚠ {col_clean}: Contains extended unicode characters that may need cleaning")
        
        # Check for infinity in numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            if np.isinf(df[col]).any():
                warnings.append(f"  ⚠ {col_clean}: Contains infinity values (will be converted to NULL)")
    
    return warnings


def clean_string_value(value):
    """
    Clean string values to remove problematic characters that Teradata can't handle
    """
    if value is None or pd.isna(value):
        return None
    
    # Convert to string
    str_value = str(value)
    
    # Remove or replace non-printable and problematic characters
    # Keep only ASCII and common extended characters
    cleaned = ''
    for char in str_value:
        # Keep ASCII printable characters and common extended chars
        if ord(char) < 128 or ord(char) in range(160, 256):
            cleaned += char
        else:
            # Replace problematic unicode with space
            cleaned += ' '
    
    # Clean up multiple spaces
    cleaned = ' '.join(cleaned.split())
    
    return cleaned if cleaned else None


def load_sheet_to_teradata(sheet_name, df, use_fastload=False):
    """
    Load a DataFrame to Teradata using appropriate method
    """
    table_name = clean_table_name(sheet_name)
    row_count = len(df)
    
    print(f"\n{'='*80}")
    print(f"Loading: {sheet_name} -> {DATABASE_NAME}.{table_name}")
    print(f"Rows: {row_count:,}")
    print(f"Method: {'FASTLOAD' if use_fastload else 'COPY_TO_SQL'}")
    print(f"{'='*80}")
    
    if DRY_RUN:
        print("DRY RUN MODE - Not executing actual load")
        return True
    
    # Prepare data - pass sheet_name for specific handling
    df_clean = prepare_dataframe_for_load(df.copy(), sheet_name=sheet_name)
    
    try:
        if use_fastload:
            # Use fastload for large datasets
            print(f"Starting FASTLOAD for {table_name}...")
            try:
                fastload(df=df_clean, 
                        table_name=table_name,
                        if_exists='append')
                print(f"✓ FASTLOAD completed: {row_count:,} rows")
            except Exception as fl_error:
                # If fastload fails, fall back to copy_to_sql
                print(f"⚠ FASTLOAD failed, falling back to COPY_TO_SQL...")
                print(f"  Error: {str(fl_error)[:100]}")
                copy_to_sql(df=df_clean,
                           table_name=table_name,
                           if_exists='append',
                           index=False)
                print(f"✓ COPY_TO_SQL fallback completed: {row_count:,} rows")
            
        else:
            # Use copy_to_sql for smaller datasets
            print(f"Starting COPY_TO_SQL for {table_name}...")
            copy_to_sql(df=df_clean,
                       table_name=table_name,
                       if_exists='append',
                       index=False)
            print(f"✓ COPY_TO_SQL completed: {row_count:,} rows")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Error loading {table_name}:")
        
        # Parse and display specific error details
        if "Error 2644" in error_msg:
            print(f"  Database space error - need more space in {DATABASE_NAME}")
        elif "Error 502" in error_msg:
            print(f"  Data type mismatch - check column types in Excel vs table definition")
            # Extract which parameter/column had the issue
            if "parameter" in error_msg:
                import re
                match = re.search(r'parameter (\d+)', error_msg)
                if match:
                    param_num = int(match.group(1))
                    if param_num <= len(df_clean.columns):
                        print(f"  Problem column: {df_clean.columns[param_num-1]}")
        elif "Error 6706" in error_msg:
            print(f"  Character encoding error - untranslatable characters in data")
        else:
            print(f"  {error_msg[:200]}")
        
        return False


def main():
    """
    Main execution function
    """
    print(f"\nTeradata Excel Loader")
    print(f"{'='*80}")
    print(f"Excel File: {EXCEL_FILE}")
    print(f"Target Database: {DATABASE_NAME}")
    print(f"Fastload Threshold: {FASTLOAD_THRESHOLD:,} rows")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE EXECUTION'}")
    print(f"{'='*80}\n")
    
    # Create Teradata connection context
    if not DRY_RUN:
        try:
            print("Connecting to Teradata...")
            #password = getpass.getpass(f"Enter password for {TD_USERNAME}: ")
            password='BombadeSumider0$'
            
            td_context = create_context(host=TD_HOST,
                                       username=TD_USERNAME,
                                       password=password,
                                       logmech=TD_LOGMECH,
                                       sslmode=TD_SSLMODE,
                                       database=DATABASE_NAME)
            
            print(f"✓ Connected to Teradata: {TD_HOST}")
            print(f"✓ Default database: {DATABASE_NAME}\n")
            
        except Exception as e:
            print(f"✗ Error connecting to Teradata: {str(e)}")
            sys.exit(1)
    
    # Load Excel file
    try:
        xl = pd.ExcelFile(EXCEL_FILE)
        print(f"Found {len(xl.sheet_names)} worksheets\n")
    except Exception as e:
        print(f"Error loading Excel file: {str(e)}")
        sys.exit(1)
    
    # Analyze sheets and prepare for loading
    print("\n" + "="*80)
    print("SHEET ANALYSIS & DIAGNOSTICS")
    print("="*80 + "\n")
    
    sheet_info = {}
    
    for sheet_name in xl.sheet_names:
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
            row_count = len(df)
            col_count = len(df.columns)
            use_fastload = row_count > FASTLOAD_THRESHOLD
            
            sheet_info[sheet_name] = {
                'rows': row_count,
                'columns': col_count,
                'use_fastload': use_fastload,
                'dataframe': df
            }
            
            print(f"Sheet: {sheet_name}")
            print(f"  Table: {clean_table_name(sheet_name)}")
            print(f"  Rows: {row_count:,}")
            print(f"  Columns: {col_count}")
            print(f"  Load Method: {'FASTLOAD' if use_fastload else 'COPY_TO_SQL'}")
            
            # Run diagnostics
            warnings = diagnose_dataframe_issues(sheet_name, df)
            if warnings:
                print(f"  Data Quality Warnings:")
                for warning in warnings:
                    print(warning)
            
            print()
            
        except Exception as e:
            print(f"Error processing sheet '{sheet_name}': {str(e)}\n")
    
    print("-" * 80 + "\n")
    
    # Ask for confirmation before proceeding with data load
    if not DRY_RUN:
        response = input("\nProceed with data load? (yes/no): ")
        if response.lower() != 'yes':
            print("Load cancelled by user.")
            remove_context()
            sys.exit(0)
    
    # Load data
    print("\n" + "="*80)
    print("DATA LOAD EXECUTION")
    print("="*80 + "\n")
    
    results = {}
    for sheet_name, info in sheet_info.items():
        use_fastload = info['use_fastload']
        df = info['dataframe']
        
        success = load_sheet_to_teradata(sheet_name, df, use_fastload)
        results[sheet_name] = success
    
    # Cleanup connection
    if not DRY_RUN:
        try:
            remove_context()
            print("\n✓ Teradata connection closed")
        except:
            pass
    
    # Summary
    print("\n" + "="*80)
    print("LOAD SUMMARY")
    print("="*80 + "\n")
    
    total_sheets = len(results)
    successful = sum(1 for v in results.values() if v)
    failed = total_sheets - successful
    total_rows = sum(info['rows'] for info in sheet_info.values())
    
    print(f"Total Sheets: {total_sheets}")
    print(f"Total Rows: {total_rows:,}")
    print(f"Successful Loads: {successful}")
    print(f"Failed Loads: {failed}")
    
    if failed > 0:
        print("\nFailed sheets:")
        for sheet_name, success in results.items():
            if not success:
                print(f"  - {sheet_name}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
