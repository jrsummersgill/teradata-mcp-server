# MCP Tools for Custom Data Dictionary (ADLSTE_HCLS_MCP_DATA_DICT)

## Overview
This document defines MCP tool instructions for querying the custom data dictionary stored in the `ADLSTE_HCLS_MCP_DATA_DICT` database. The data dictionary contains comprehensive metadata about databases, tables, columns, relationships, and business glossary terms across the Teradata system.

## Data Dictionary Schema

### Core Tables
1. **DB** - Database catalog with business names and descriptions
2. **TBL** - Table catalog with business metadata
3. **TBL_COL** - Column-level metadata including data types, constraints, and privacy indicators
4. **SBJ_AREA** - Subject areas for logical data organization
5. **TBL_JOINS** - Table relationship and join patterns
6. **BUS_GLSRY** - Business glossary mapping technical to business terms
7. **TBL_IDX** - Index information
8. **TBL_PARTN** - Partition details
9. **DB_OWNR** - Database ownership information
10. **TBL_DATA_PRFL** - Data profiling statistics
11. **TBL_REC_CNT** - Table row counts
12. **COLUMN_SECURITY** - Column-level security classifications
13. **MRR_TBL** - Mirror table relationships
14. **NATR_KEY_SRC** - Natural key sources
15. **DATA_TYP_REF** - Data type reference
16. **AST** - Asset catalog
17. **AST_ABOUT** - Asset descriptions
18. **AST_URLS** - Asset URLs and links
19. **NEWALIAS** - Table/column aliases

---

## MCP Tool Definitions

### 1. Search for Databases
**Tool Name:** `datadict_search_databases`

**Description:** Search for databases by name, business name, or description keywords.

**Use Cases:**
- "What databases do we have?"
- "Find databases related to claims"
- "Show me all active databases"

**SQL Template:**
```sql
SELECT 
    d.DB_ID,
    d.DB_NM as "Database Name",
    d.DB_BUS_NM as "Business Name",
    d.DB_DESC as "Description",
    d.INSTC_NM as "Instance",
    d.DBMS_TYP_NM as "DBMS Type",
    d.ACTV_DB_IND as "Active",
    a.AST_ID,
    sa.SBJ_AREA_NM as "Subject Area"
FROM ADLSTE_HCLS_MCP_DATA_DICT.DB d
LEFT JOIN ADLSTE_HCLS_MCP_DATA_DICT.AST a ON d.AST_ID = a.AST_ID
LEFT JOIN ADLSTE_HCLS_MCP_DATA_DICT.SBJ_AREA sa ON a.AST_ID = sa.AST_ID
WHERE d.ACTV_DB_IND = 'Y'
  AND (
    UPPER(d.DB_NM) LIKE UPPER('%{search_term}%')
    OR UPPER(d.DB_BUS_NM) LIKE UPPER('%{search_term}%')
    OR UPPER(d.DB_DESC) LIKE UPPER('%{search_term}%')
  )
ORDER BY d.DB_NM;
```

**Parameters:**
- `search_term` (optional): Keyword to search for. If not provided, returns all active databases.

---

### 2. Search for Tables
**Tool Name:** `datadict_search_tables`

**Description:** Search for tables by name, business name, description, or subject area.

**Use Cases:**
- "Find tables related to claims"
- "What tables are in the Member subject area?"
- "Show me all fact tables"

**SQL Template:**
```sql
SELECT 
    t.TBL_ID,
    d.DB_NM as "Database",
    t.TBL_NM as "Table Name",
    t.TBL_BUS_NM as "Business Name",
    t.TBL_BUS_DESC as "Description",
    sa.SBJ_AREA_NM as "Subject Area",
    t.TBL_TYP_TXT as "Table Type",
    t.TBL_SRC_TXT as "Source System",
    t.UPDT_FREQ_TXT as "Update Frequency",
    t.TMLN_IND as "Timeline Indicator",
    t.USER_UPDT_TS as "Last Updated"
FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL t
JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB d ON t.DB_ID = d.DB_ID
LEFT JOIN ADLSTE_HCLS_MCP_DATA_DICT.SBJ_AREA sa ON t.SBJ_AREA_ID = sa.SBJ_AREA_ID
WHERE (
    UPPER(t.TBL_NM) LIKE UPPER('%{search_term}%')
    OR UPPER(t.TBL_BUS_NM) LIKE UPPER('%{search_term}%')
    OR UPPER(t.TBL_BUS_DESC) LIKE UPPER('%{search_term}%')
    OR UPPER(sa.SBJ_AREA_NM) LIKE UPPER('%{search_term}%')
  )
  {database_filter}
  {table_type_filter}
  {subject_area_filter}
ORDER BY d.DB_NM, t.TBL_NM;
```

**Parameters:**
- `search_term` (optional): Keyword to search for
- `database_name` (optional): Filter by specific database
- `table_type` (optional): Filter by table type (Fact, Dimension, Keymap, MRR, etc.)
- `subject_area` (optional): Filter by subject area name

**Dynamic Filters:**
- `{database_filter}`: `AND d.DB_NM = '{database_name}'` (if database_name provided)
- `{table_type_filter}`: `AND t.TBL_TYP_TXT = '{table_type}'` (if table_type provided)
- `{subject_area_filter}`: `AND sa.SBJ_AREA_NM = '{subject_area}'` (if subject_area provided)

---

### 3. Get Table Details
**Tool Name:** `datadict_get_table_details`

**Description:** Get comprehensive details about a specific table including all metadata.

**Use Cases:**
- "Tell me about the MEMBER table"
- "What's the purpose of table X?"
- "Show me details for ADJD_MCE_SRVC"

**SQL Template:**
```sql
SELECT 
    t.TBL_ID,
    d.DB_NM as "Database",
    t.TBL_NM as "Table Name",
    t.TBL_BUS_NM as "Business Name",
    t.TBL_BUS_DESC as "Business Description",
    sa.SBJ_AREA_NM as "Subject Area",
    sa.SBJ_AREA_DESC as "Subject Area Description",
    t.TBL_TYP_TXT as "Table Type",
    t.TBL_SRC_TXT as "Source System",
    t.UPDT_FREQ_TXT as "Update Frequency",
    t.TMLN_IND as "Timeline Indicator",
    o.DB_OWNR_NM as "Owner",
    t.USER_UPDT_ID as "Last Updated By",
    t.USER_UPDT_TS as "Last Updated Timestamp",
    d.INSTC_NM as "Instance",
    d.DBMS_TYP_NM as "DBMS Type"
FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL t
JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB d ON t.DB_ID = d.DB_ID
LEFT JOIN ADLSTE_HCLS_MCP_DATA_DICT.SBJ_AREA sa ON t.SBJ_AREA_ID = sa.SBJ_AREA_ID
LEFT JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB_OWNR o ON t.DB_OWNR_ID = o.DB_OWNR_ID
WHERE d.DB_NM = '{database_name}'
  AND t.TBL_NM = '{table_name}';
```

**Parameters:**
- `database_name` (required): Database name
- `table_name` (required): Table name

---

### 4. Get Table Columns
**Tool Name:** `datadict_get_table_columns`

**Description:** Get all columns for a specific table with detailed metadata.

**Use Cases:**
- "What columns are in table X?"
- "Show me the structure of the MEMBER table"
- "What are the key columns in table Y?"

**SQL Template:**
```sql
SELECT 
    c.COL_ID,
    c.COL_NM as "Column Name",
    c.COL_BUS_NM as "Business Name",
    c.COL_DESC as "Description",
    c.DATA_TYP_CD as "Data Type",
    c.COL_LEN_NUM as "Length",
    c.COL_SCL_NUM as "Scale",
    c.PRI_KEY_IND as "Primary Key",
    c.FGN_KEY_IND as "Foreign Key",
    c.NATR_KEY_IND as "Natural Key",
    c.NULL_IND as "Nullable",
    c.COL_DFLT_VAL_TXT as "Default Value",
    c.PHI_IND as "PHI Indicator",
    c.PII_IND as "PII Indicator",
    c.DE_ID_COL_IND as "De-ID Column",
    c.DATA_PVT_LVL_NM as "Data Privacy Level",
    c.COL_VLD_VAL_TXT as "Valid Values"
FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL_COL c
JOIN ADLSTE_HCLS_MCP_DATA_DICT.TBL t ON c.TBL_ID = t.TBL_ID
JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB d ON t.DB_ID = d.DB_ID
WHERE d.DB_NM = '{database_name}'
  AND t.TBL_NM = '{table_name}'
ORDER BY c.COL_ID;
```

**Parameters:**
- `database_name` (required): Database name
- `table_name` (required): Table name

---

### 5. Search Columns
**Tool Name:** `datadict_search_columns`

**Description:** Search for columns across all tables by name, business name, or description.

**Use Cases:**
- "Find all columns related to member ID"
- "What tables have a claim number column?"
- "Show me all PHI columns"

**SQL Template:**
```sql
SELECT 
    d.DB_NM as "Database",
    t.TBL_NM as "Table",
    t.TBL_BUS_NM as "Table Business Name",
    c.COL_NM as "Column Name",
    c.COL_BUS_NM as "Column Business Name",
    c.COL_DESC as "Description",
    c.DATA_TYP_CD as "Data Type",
    c.COL_LEN_NUM as "Length",
    c.PRI_KEY_IND as "Primary Key",
    c.FGN_KEY_IND as "Foreign Key",
    c.PHI_IND as "PHI",
    c.PII_IND as "PII",
    sa.SBJ_AREA_NM as "Subject Area"
FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL_COL c
JOIN ADLSTE_HCLS_MCP_DATA_DICT.TBL t ON c.TBL_ID = t.TBL_ID
JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB d ON t.DB_ID = d.DB_ID
LEFT JOIN ADLSTE_HCLS_MCP_DATA_DICT.SBJ_AREA sa ON t.SBJ_AREA_ID = sa.SBJ_AREA_ID
WHERE (
    UPPER(c.COL_NM) LIKE UPPER('%{search_term}%')
    OR UPPER(c.COL_BUS_NM) LIKE UPPER('%{search_term}%')
    OR UPPER(c.COL_DESC) LIKE UPPER('%{search_term}%')
  )
  {database_filter}
  {phi_filter}
  {pii_filter}
  {key_filter}
ORDER BY d.DB_NM, t.TBL_NM, c.COL_NM
LIMIT {limit};
```

**Parameters:**
- `search_term` (required): Keyword to search for
- `database_name` (optional): Filter by database
- `phi_only` (optional): Boolean - if true, only return PHI columns
- `pii_only` (optional): Boolean - if true, only return PII columns
- `key_columns_only` (optional): Boolean - if true, only return key columns (PK, FK, NK)
- `limit` (optional): Maximum number of results (default: 100)

**Dynamic Filters:**
- `{database_filter}`: `AND d.DB_NM = '{database_name}'` (if database_name provided)
- `{phi_filter}`: `AND c.PHI_IND = 'Y'` (if phi_only is true)
- `{pii_filter}`: `AND c.PII_IND = 'Y'` (if pii_only is true)
- `{key_filter}`: `AND (c.PRI_KEY_IND = 'Y' OR c.FGN_KEY_IND = 'Y' OR c.NATR_KEY_IND = 'Y')` (if key_columns_only is true)

---

### 6. Get Table Relationships (Joins)
**Tool Name:** `datadict_get_table_joins`

**Description:** Get all documented join relationships for a specific table.

**Use Cases:**
- "How does table X join to other tables?"
- "What tables can I join with MEMBER?"
- "Show me the relationships for table Y"

**SQL Template:**
```sql
SELECT 
    j.TBL_JOIN_LN_ID as "Join ID",
    j.LFT_SIDE_DB_NM as "Left Database",
    j.LFT_SIDE_TBL_NM as "Left Table",
    j.LFT_SIDE_COL_NM as "Left Column",
    j.JOIN_EXPRS_TXT as "Join Expression",
    j.RHT_SIDE_DB_NM as "Right Database",
    j.RHT_SIDE_TBL_NM as "Right Table",
    j.RHT_SIDE_1_COL_NM as "Right Column",
    j.JOIN_SEQ_NBR as "Join Sequence"
FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL_JOINS j
WHERE (
    (j.LFT_SIDE_DB_NM = '{database_name}' AND j.LFT_SIDE_TBL_NM = '{table_name}')
    OR
    (j.RHT_SIDE_DB_NM = '{database_name}' AND j.RHT_SIDE_TBL_NM = '{table_name}')
  )
ORDER BY j.JOIN_SEQ_NBR;
```

**Parameters:**
- `database_name` (required): Database name
- `table_name` (required): Table name

---

### 7. Search Business Glossary
**Tool Name:** `datadict_search_business_glossary`

**Description:** Search the business glossary for business-friendly terms and their technical mappings.

**Use Cases:**
- "What's the business term for technical column X?"
- "Find business definitions for member-related fields"
- "Show me the glossary entry for claim amount"

**SQL Template:**
```sql
SELECT 
    bg.TBL_BUS_NM as "Table Business Name",
    bg.TBL_NM as "Table Technical Name",
    bg.COL_BUS_NM as "Column Business Name",
    bg.COL_NM as "Column Technical Name",
    bg.COL_DATA_TYP as "Data Type",
    bg.COL_DATA_TYP_LEN as "Data Length"
FROM ADLSTE_HCLS_MCP_DATA_DICT.BUS_GLSRY bg
WHERE (
    UPPER(bg.TBL_BUS_NM) LIKE UPPER('%{search_term}%')
    OR UPPER(bg.TBL_NM) LIKE UPPER('%{search_term}%')
    OR UPPER(bg.COL_BUS_NM) LIKE UPPER('%{search_term}%')
    OR UPPER(bg.COL_NM) LIKE UPPER('%{search_term}%')
  )
ORDER BY bg.TBL_BUS_NM, bg.COL_BUS_NM
LIMIT {limit};
```

**Parameters:**
- `search_term` (required): Keyword to search for
- `limit` (optional): Maximum number of results (default: 50)

---

### 8. Get Subject Areas
**Tool Name:** `datadict_get_subject_areas`

**Description:** List all subject areas with descriptions and optionally filter by asset.

**Use Cases:**
- "What subject areas do we have?"
- "Show me all subject areas"
- "What's in the Claims subject area?"

**SQL Template:**
```sql
SELECT 
    sa.SBJ_AREA_ID,
    sa.SBJ_AREA_NM as "Subject Area Name",
    sa.SBJ_AREA_DESC as "Description",
    sa.AST_ID as "Asset ID",
    COUNT(DISTINCT t.TBL_ID) as "Table Count"
FROM ADLSTE_HCLS_MCP_DATA_DICT.SBJ_AREA sa
LEFT JOIN ADLSTE_HCLS_MCP_DATA_DICT.TBL t ON sa.SBJ_AREA_ID = t.SBJ_AREA_ID
WHERE 1=1
  {asset_filter}
GROUP BY sa.SBJ_AREA_ID, sa.SBJ_AREA_NM, sa.SBJ_AREA_DESC, sa.AST_ID
ORDER BY sa.SBJ_AREA_NM;
```

**Parameters:**
- `asset_id` (optional): Filter by specific asset ID

**Dynamic Filters:**
- `{asset_filter}`: `AND sa.AST_ID = {asset_id}` (if asset_id provided)

---

### 9. Find Related Tables
**Tool Name:** `datadict_find_related_tables`

**Description:** Find tables that are commonly used together or share similar subject areas/purposes.

**Use Cases:**
- "What tables are related to the MEMBER table?"
- "Find tables that work with claims data"
- "Show me tables in the same subject area as table X"

**SQL Template:**
```sql
WITH target_table AS (
    SELECT 
        t.TBL_ID,
        t.SBJ_AREA_ID,
        t.DB_ID,
        t.TBL_TYP_TXT
    FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL t
    JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB d ON t.DB_ID = d.DB_ID
    WHERE d.DB_NM = '{database_name}'
      AND t.TBL_NM = '{table_name}'
)
SELECT 
    d.DB_NM as "Database",
    t.TBL_NM as "Table Name",
    t.TBL_BUS_NM as "Business Name",
    t.TBL_BUS_DESC as "Description",
    sa.SBJ_AREA_NM as "Subject Area",
    t.TBL_TYP_TXT as "Table Type",
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL_JOINS j
            WHERE (j.LFT_SIDE_TBL_NM = t.TBL_NM OR j.RHT_SIDE_TBL_NM = t.TBL_NM)
              AND (j.LFT_SIDE_TBL_NM = '{table_name}' OR j.RHT_SIDE_TBL_NM = '{table_name}')
        ) THEN 'Direct Join'
        WHEN t.SBJ_AREA_ID = (SELECT SBJ_AREA_ID FROM target_table) THEN 'Same Subject Area'
        WHEN t.TBL_TYP_TXT = (SELECT TBL_TYP_TXT FROM target_table) THEN 'Same Table Type'
        ELSE 'Related'
    END as "Relationship Type"
FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL t
JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB d ON t.DB_ID = d.DB_ID
LEFT JOIN ADLSTE_HCLS_MCP_DATA_DICT.SBJ_AREA sa ON t.SBJ_AREA_ID = sa.SBJ_AREA_ID
CROSS JOIN target_table tt
WHERE t.TBL_ID != tt.TBL_ID
  AND (
    t.SBJ_AREA_ID = tt.SBJ_AREA_ID
    OR EXISTS (
        SELECT 1 FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL_JOINS j
        WHERE (j.LFT_SIDE_TBL_NM = t.TBL_NM OR j.RHT_SIDE_TBL_NM = t.TBL_NM)
          AND (j.LFT_SIDE_TBL_NM = '{table_name}' OR j.RHT_SIDE_TBL_NM = '{table_name}')
    )
  )
ORDER BY 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL_JOINS j
            WHERE (j.LFT_SIDE_TBL_NM = t.TBL_NM OR j.RHT_SIDE_TBL_NM = t.TBL_NM)
              AND (j.LFT_SIDE_TBL_NM = '{table_name}' OR j.RHT_SIDE_TBL_NM = '{table_name}')
        ) THEN 1
        WHEN t.SBJ_AREA_ID = tt.SBJ_AREA_ID THEN 2
        ELSE 3
    END,
    t.TBL_NM
LIMIT {limit};
```

**Parameters:**
- `database_name` (required): Database name
- `table_name` (required): Table name
- `limit` (optional): Maximum number of results (default: 50)

---

### 10. Get Privacy-Sensitive Columns
**Tool Name:** `datadict_get_sensitive_columns`

**Description:** Find all columns marked as PHI, PII, or requiring de-identification.

**Use Cases:**
- "What PHI columns are in the system?"
- "Show me all PII fields"
- "Find sensitive data in database X"
- "What columns need to be de-identified?"

**SQL Template:**
```sql
SELECT 
    d.DB_NM as "Database",
    t.TBL_NM as "Table",
    t.TBL_BUS_NM as "Table Business Name",
    c.COL_NM as "Column Name",
    c.COL_BUS_NM as "Column Business Name",
    c.COL_DESC as "Description",
    c.PHI_IND as "PHI",
    c.PII_IND as "PII",
    c.DE_ID_COL_IND as "De-ID Required",
    c.DATA_PVT_LVL_NM as "Privacy Level",
    sa.SBJ_AREA_NM as "Subject Area"
FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL_COL c
JOIN ADLSTE_HCLS_MCP_DATA_DICT.TBL t ON c.TBL_ID = t.TBL_ID
JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB d ON t.DB_ID = d.DB_ID
LEFT JOIN ADLSTE_HCLS_MCP_DATA_DICT.SBJ_AREA sa ON t.SBJ_AREA_ID = sa.SBJ_AREA_ID
WHERE (c.PHI_IND = 'Y' OR c.PII_IND = 'Y' OR c.DE_ID_COL_IND = 'Y')
  {database_filter}
  {sensitivity_filter}
ORDER BY d.DB_NM, t.TBL_NM, c.COL_NM
LIMIT {limit};
```

**Parameters:**
- `database_name` (optional): Filter by database
- `sensitivity_type` (optional): 'PHI', 'PII', 'DEID', or 'ALL' (default: 'ALL')
- `limit` (optional): Maximum number of results (default: 200)

**Dynamic Filters:**
- `{database_filter}`: `AND d.DB_NM = '{database_name}'` (if database_name provided)
- `{sensitivity_filter}`: Based on sensitivity_type:
  - 'PHI': `AND c.PHI_IND = 'Y'`
  - 'PII': `AND c.PII_IND = 'Y'`
  - 'DEID': `AND c.DE_ID_COL_IND = 'Y'`
  - 'ALL': no additional filter

---

### 11. Get Key Columns for Join Design
**Tool Name:** `datadict_get_key_columns`

**Description:** Find all primary keys, foreign keys, and natural keys for a table to help design joins.

**Use Cases:**
- "What are the key columns in table X?"
- "Show me the primary keys for this table"
- "How do I join table A to table B?"

**SQL Template:**
```sql
SELECT 
    c.COL_NM as "Column Name",
    c.COL_BUS_NM as "Business Name",
    c.COL_DESC as "Description",
    c.DATA_TYP_CD as "Data Type",
    c.COL_LEN_NUM as "Length",
    c.PRI_KEY_IND as "Primary Key",
    c.FGN_KEY_IND as "Foreign Key",
    c.NATR_KEY_IND as "Natural Key",
    c.NULL_IND as "Nullable"
FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL_COL c
JOIN ADLSTE_HCLS_MCP_DATA_DICT.TBL t ON c.TBL_ID = t.TBL_ID
JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB d ON t.DB_ID = d.DB_ID
WHERE d.DB_NM = '{database_name}'
  AND t.TBL_NM = '{table_name}'
  AND (c.PRI_KEY_IND = 'Y' OR c.FGN_KEY_IND = 'Y' OR c.NATR_KEY_IND = 'Y')
ORDER BY 
    CASE 
        WHEN c.PRI_KEY_IND = 'Y' THEN 1
        WHEN c.FGN_KEY_IND = 'Y' THEN 2
        WHEN c.NATR_KEY_IND = 'Y' THEN 3
        ELSE 4
    END,
    c.COL_NM;
```

**Parameters:**
- `database_name` (required): Database name
- `table_name` (required): Table name

---

### 12. Build Join Query Helper
**Tool Name:** `datadict_suggest_join_query`

**Description:** Suggest a SQL join query between two tables based on documented relationships.

**Use Cases:**
- "How do I join table A to table B?"
- "Show me a sample query joining these tables"
- "What's the join syntax for X and Y?"

**SQL Template:**
```sql
SELECT 
    j.LFT_SIDE_DB_NM || '.' || j.LFT_SIDE_TBL_NM as "Left Table",
    j.LFT_SIDE_COL_NM as "Left Column",
    j.JOIN_EXPRS_TXT as "Operator",
    j.RHT_SIDE_DB_NM || '.' || j.RHT_SIDE_TBL_NM as "Right Table",
    j.RHT_SIDE_1_COL_NM as "Right Column",
    j.JOIN_SEQ_NBR as "Sequence",
    'SELECT * FROM ' || j.LFT_SIDE_DB_NM || '.' || j.LFT_SIDE_TBL_NM || ' a' ||
    ' JOIN ' || j.RHT_SIDE_DB_NM || '.' || j.RHT_SIDE_TBL_NM || ' b' ||
    ' ON a.' || j.LFT_SIDE_COL_NM || ' ' || j.JOIN_EXPRS_TXT || ' b.' || j.RHT_SIDE_1_COL_NM as "Sample Query"
FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL_JOINS j
WHERE (
    (j.LFT_SIDE_DB_NM = '{left_database}' AND j.LFT_SIDE_TBL_NM = '{left_table}' 
     AND j.RHT_SIDE_DB_NM = '{right_database}' AND j.RHT_SIDE_TBL_NM = '{right_table}')
    OR
    (j.LFT_SIDE_DB_NM = '{right_database}' AND j.LFT_SIDE_TBL_NM = '{right_table}'
     AND j.RHT_SIDE_DB_NM = '{left_database}' AND j.RHT_SIDE_TBL_NM = '{left_table}')
  )
ORDER BY j.JOIN_SEQ_NBR;
```

**Parameters:**
- `left_database` (required): Left table's database name
- `left_table` (required): Left table name
- `right_database` (required): Right table's database name
- `right_table` (required): Right table name

---

## Implementation Guidelines

### When to Trigger These Tools

1. **User mentions specific table/column names** → Use `datadict_get_table_details`, `datadict_get_table_columns`

2. **User asks about relationships/joins** → Use `datadict_get_table_joins`, `datadict_suggest_join_query`, `datadict_find_related_tables`

3. **User searches with keywords** → Use `datadict_search_tables`, `datadict_search_columns`, `datadict_search_business_glossary`

4. **User asks about data categories** → Use `datadict_get_subject_areas`

5. **User asks about data privacy/security** → Use `datadict_get_sensitive_columns`

6. **User needs to design a query** → Use `datadict_get_key_columns`, `datadict_suggest_join_query`

### Tool Call Sequencing

For complex queries, chain tools together:

**Example 1: "Show me how to join member and claims tables"**
1. Call `datadict_search_tables` with "member" → get table names
2. Call `datadict_search_tables` with "claims" → get table names
3. Call `datadict_suggest_join_query` with both table names
4. If no documented join, call `datadict_get_key_columns` for both tables

**Example 2: "What PHI data do we have about members?"**
1. Call `datadict_search_tables` with "member" → get member-related tables
2. For each table, call `datadict_get_sensitive_columns` with PHI filter

**Example 3: "Find all tables in the Claims subject area"**
1. Call `datadict_get_subject_areas` → get subject area list
2. Identify Claims subject area ID
3. Call `datadict_search_tables` with subject_area filter

### Response Formatting

When returning data dictionary results to users:

1. **Summarize first** - Give a brief overview before detailed results
2. **Group logically** - Group tables by subject area, columns by table
3. **Highlight key information** - Emphasize primary keys, sensitive data flags
4. **Provide context** - Include business descriptions and purposes
5. **Suggest next steps** - Recommend related queries or tables to explore

### Error Handling

- If a table is not found, suggest similar table names using fuzzy matching
- If no joins are documented, suggest analyzing key columns
- If search returns no results, broaden the search terms or suggest alternative keywords

---

## Example User Interactions

### Example 1: Finding Claims Data
**User:** "I need to analyze claims data. What tables should I use?"

**Assistant Actions:**
1. Call `datadict_search_tables` with search_term="claims"
2. Summarize results grouping by subject area
3. Call `datadict_get_subject_areas` to provide context
4. Offer to show detailed column information for specific tables

**Response:** "I found 24 claims-related tables across 3 subject areas: Adjudicated Claims (15 tables), Pre-adjudicated Claims (6 tables), and Financial Expense (3 tables). The main fact tables are ADJD_MCE_SRVC (Adjudicated Medical Claim Event Service) and PRE_ADJD_MCE (Pre-Adjudicated Medical Claim Event). Would you like to see the column details for any of these tables?"

### Example 2: Understanding Table Structure
**User:** "What's in the MEMBER table?"

**Assistant Actions:**
1. Call `datadict_get_table_details` with database="EDWBASESECUREVIEW1", table="MEMBER"
2. Call `datadict_get_table_columns` with same parameters
3. Call `datadict_get_key_columns` with same parameters
4. Present organized summary

**Response:** "The MEMBER table in EDWBASESECUREVIEW1 contains member demographic and enrollment information. It has 47 columns including:
- **Primary Keys**: EDW_MBR_ID (surrogate key)
- **Natural Keys**: MBR_NBR (member number)
- **Key Dates**: BIRTH_DT, ENRLMT_EFF_DT, ENRLMT_TERM_DT
- **Demographics**: GNDR_CD, ZIP_CD, LANG_CD
- **PHI Fields**: 12 columns marked as PHI including name, address, and SSN

The table is updated daily from the PRIME source system. Would you like to see the documented joins for this table?"

### Example 3: Joining Tables
**User:** "How do I join MEMBER to CLAIM tables?"

**Assistant Actions:**
1. Call `datadict_get_table_joins` with table="MEMBER"
2. Filter results for claim-related tables
3. If direct joins found, call `datadict_suggest_join_query`
4. If no direct joins, use `datadict_find_related_tables` to find intermediate tables

**Response:** "To join MEMBER to CLAIM tables, you typically use this pattern:

```sql
SELECT *
FROM EDWBASESECUREVIEW1.MEMBER m
JOIN EDWBASESECUREVIEW1.MBR_COV mc 
  ON m.EDW_MBR_ID = mc.EDW_MBR_ID
JOIN EDWBASESECUREVIEW1.ADJD_MCE_SRVC claim
  ON mc.EDW_MBR_COV_ID = claim.EDW_MBR_COV_ID
```

The MEMBER table doesn't join directly to claim tables. You need the intermediate MBR_COV (Member Coverage) table which contains both EDW_MBR_ID and EDW_MBR_COV_ID keys."

---

## Configuration for MCP Server

When implementing these tools in an MCP server, use this configuration structure:

```json
{
  "tools": [
    {
      "name": "datadict_search_databases",
      "description": "Search for databases by name or description",
      "inputSchema": {
        "type": "object",
        "properties": {
          "search_term": {
            "type": "string",
            "description": "Keyword to search for (optional)"
          }
        }
      }
    },
    {
      "name": "datadict_search_tables",
      "description": "Search for tables by name, business name, or description",
      "inputSchema": {
        "type": "object",
        "properties": {
          "search_term": {
            "type": "string",
            "description": "Keyword to search for"
          },
          "database_name": {
            "type": "string",
            "description": "Filter by database (optional)"
          },
          "table_type": {
            "type": "string",
            "description": "Filter by table type (optional)"
          },
          "subject_area": {
            "type": "string",
            "description": "Filter by subject area (optional)"
          }
        },
        "required": ["search_term"]
      }
    }
    // ... continue for all 12 tools
  ]
}
```

---

## Performance Optimization Tips

1. **Use appropriate indexes** - Ensure DB, TBL, TBL_COL have indexes on search columns
2. **Limit result sets** - Always include reasonable LIMIT clauses
3. **Cache frequently accessed data** - Cache subject areas, database lists
4. **Use LIKE efficiently** - Place wildcards appropriately (avoid leading wildcards when possible)
5. **Join optimization** - Use INNER JOINs where appropriate instead of LEFT JOINs

---

## Security Considerations

1. **Respect privacy indicators** - Alert users when querying PHI/PII columns
2. **Data privacy levels** - Enforce appropriate access controls based on DATA_PVT_LVL_NM
3. **Audit trail** - Log all data dictionary queries for compliance
4. **Row-level security** - Implement if needed based on user roles

---

## Maintenance and Updates

1. **Regular synchronization** - Keep data dictionary in sync with actual database schema
2. **Validation checks** - Periodically validate that documented joins actually work
3. **Completeness monitoring** - Track which tables/columns lack documentation
4. **User feedback loop** - Allow users to suggest improvements to descriptions

---

## Future Enhancements

1. **Lineage tracking** - Track data lineage from source to target
2. **Impact analysis** - Show downstream impacts of schema changes
3. **Usage analytics** - Track which tables/columns are most queried
4. **AI-powered suggestions** - Use ML to suggest better join paths
5. **Visual ERD generation** - Generate entity-relationship diagrams on demand
6. **Natural language to SQL** - Convert user questions directly to SQL using the data dictionary

---

## Summary

This data dictionary MCP implementation provides 12 comprehensive tools that enable users to:
- Discover and explore databases, tables, and columns
- Understand data relationships and design efficient joins
- Find business-friendly terminology and descriptions
- Identify sensitive data requiring special handling
- Navigate complex data structures with confidence

The tools are designed to work together, allowing for sophisticated multi-step queries that answer complex data discovery questions.
