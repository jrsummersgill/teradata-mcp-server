# Data Dictionary MCP - User Guide and Examples

## Overview
This guide shows how to interact with your custom data dictionary through Claude using the MCP (Model Context Protocol) tools. The data dictionary provides comprehensive metadata about your Teradata databases, tables, columns, and their relationships.

---

## Quick Start

### Basic Queries

#### 1. Finding Databases
```
You: "What databases do we have?"

Claude: [Calls datadict_search_databases]
Shows: List of all active databases with descriptions

You: "Find databases related to clinical data"

Claude: [Calls datadict_search_databases with search_term="clinical"]
Shows: Databases matching "clinical" in name or description
```

#### 2. Discovering Tables
```
You: "Show me tables for member information"

Claude: [Calls datadict_search_tables with search_term="member"]
Shows: All member-related tables with business names and descriptions

You: "What fact tables do we have?"

Claude: [Calls datadict_search_tables with table_type="Fact"]
Shows: All fact tables across all databases
```

#### 3. Understanding Table Structure
```
You: "What's in the MEMBER table?"

Claude: [Calls datadict_get_table_details + datadict_get_table_columns]
Shows: Complete table metadata and all columns with descriptions

You: "Show me the key columns for MEMBER"

Claude: [Calls datadict_get_key_columns]
Shows: Primary keys, foreign keys, and natural keys
```

---

## Common Use Cases

### Use Case 1: Starting a New Analysis Project

**Scenario:** You need to analyze member enrollment trends but don't know which tables to use.

**Conversation Flow:**
```
You: "I need to analyze member enrollment data. What tables should I use?"

Claude: 
[Calls datadict_search_tables with "enrollment"]
[Calls datadict_get_subject_areas]

"I found several enrollment-related tables:

**Main Tables:**
1. **MBR_COV** (Member Coverage) - Current and historical enrollment
   - Subject Area: Customer
   - Update Frequency: Daily
   - Key columns: EDW_MBR_ID, ENRLMT_EFF_DT, ENRLMT_TERM_DT

2. **MBR_COV_HIST** (Member Coverage History) - Time-based enrollment changes
   - Subject Area: Customer
   - Timeline table: Yes
   
3. **ENRLMT_TYP** (Enrollment Type) - Reference data for enrollment types

Would you like to see the column details for any of these tables?"

You: "Yes, show me the columns in MBR_COV"

Claude:
[Calls datadict_get_table_columns for MBR_COV]

"MBR_COV has 45 columns. Key columns include:

**Identifiers:**
- EDW_MBR_COV_ID (Primary Key) - Surrogate key for member coverage
- EDW_MBR_ID (Foreign Key) - Links to MEMBER table
- MBR_COV_NBR (Natural Key) - Business member coverage number

**Date Fields:**
- ENRLMT_EFF_DT - Enrollment effective date
- ENRLMT_TERM_DT - Enrollment termination date
- CVRG_EFF_DT - Coverage effective date
- CVRG_TERM_DT - Coverage termination date

**Coverage Details:**
- PROD_ID - Product identifier
- PLAN_ID - Plan identifier
- GRP_ID - Group identifier
- CVRG_STS_CD - Coverage status code

**Privacy Notes:**
- 8 columns marked as PHI (including addresses, dates)
- Privacy Level: EDWBASESECUREVIEW1/2/3

Would you like to see how to join this to other tables?"
```

### Use Case 2: Building a Complex Query

**Scenario:** You need to join multiple tables but aren't sure how they relate.

**Conversation Flow:**
```
You: "How do I join MEMBER, MBR_COV, and CLAIM tables together?"

Claude:
[Calls datadict_get_table_joins for MEMBER]
[Calls datadict_get_table_joins for MBR_COV]
[Calls datadict_suggest_join_query]

"Here's how to join these tables:

**Join Path:**
MEMBER → MBR_COV → ADJD_MCE_SRVC (claims)

**Sample SQL:**
```sql
SELECT 
    m.MBR_NBR,
    m.FIRST_NM,
    m.LAST_NM,
    mc.ENRLMT_EFF_DT,
    mc.ENRLMT_TERM_DT,
    c.CLM_NBR,
    c.SRVC_DT,
    c.PAID_AMT
FROM EDWBASESECUREVIEW1.MEMBER m
JOIN EDWBASESECUREVIEW1.MBR_COV mc 
    ON m.EDW_MBR_ID = mc.EDW_MBR_ID
JOIN EDWBASESECUREVIEW1.ADJD_MCE_SRVC c
    ON mc.EDW_MBR_COV_ID = c.EDW_MBR_COV_ID
WHERE mc.ENRLMT_EFF_DT <= c.SRVC_DT
  AND (mc.ENRLMT_TERM_DT IS NULL OR mc.ENRLMT_TERM_DT >= c.SRVC_DT)
```

**Key Points:**
- MEMBER joins to MBR_COV via EDW_MBR_ID
- MBR_COV joins to claims via EDW_MBR_COV_ID
- Add date filters to ensure coverage was active during service date

Would you like me to explain any of these columns?"
```

### Use Case 3: Finding Specific Data Elements

**Scenario:** You need to find all columns related to diagnosis codes.

**Conversation Flow:**
```
You: "Where can I find diagnosis codes?"

Claude:
[Calls datadict_search_columns with "diagnosis"]

"I found diagnosis-related columns in 12 tables:

**Primary Diagnosis Tables:**
1. **DIAG_CD** - Diagnosis Code reference table
   - DIAG_CD (Diagnosis Code) - ICD-10 diagnosis codes
   - DIAG_DESC (Description) - Full diagnosis description

2. **ADJD_MCE_SRVC_DIAG** - Claim service diagnosis linkage
   - DIAG_CD (Diagnosis Code)
   - DIAG_SEQ_NBR (Sequence) - Primary, secondary, etc.
   - DIAG_TYP_CD (Type Code) - Admitting, principal, etc.

3. **ADJD_MCE_SRVC** - Main claim table
   - PRIM_DIAG_CD (Primary Diagnosis Code)
   - ADMTG_DIAG_CD (Admitting Diagnosis Code)

**Related Reference Tables:**
- DIAG_TYP (Diagnosis Type)
- DIAG_CATGY (Diagnosis Category)
- ICD_VRSN_TYP (ICD Version Type)

Would you like to see how these tables join together?"
```

### Use Case 4: Understanding Data Privacy

**Scenario:** You need to understand what sensitive data exists before creating a report.

**Conversation Flow:**
```
You: "What PHI data do we have in member tables?"

Claude:
[Calls datadict_search_tables with "member"]
[Calls datadict_get_sensitive_columns with phi_only=true]

"Here's the PHI data in member-related tables:

**MEMBER Table (15 PHI columns):**
- Personal Identifiers: SSN, MBR_NBR
- Name Fields: FIRST_NM, LAST_NM, MIDL_NM
- Contact: EMAIL_ADDR, PHONE_NBR, CELL_PHONE_NBR
- Address: ADDR_LN_1, ADDR_LN_2, CTY_NM, STE_CD, ZIP_CD
- Demographics: BIRTH_DT, DEATH_DT

**MBR_COV Table (8 PHI columns):**
- Dates: ENRLMT_EFF_DT, ENRLMT_TERM_DT, BIRTH_DT
- Identifiers: MBR_COV_NBR, SSN_NBR

**Privacy Levels:**
- EDWBASESECUREVIEW1: Identified data (PHI visible)
- EDWBASESECUREVIEW2: Limited dataset (dates > 89 years masked)
- EDWBASESECUREVIEW3: De-identified (all PHI masked/removed)

**Recommendation:**
For analytics, consider using EDWBASESECUREVIEW2 or VIEW3 unless you specifically need identified PHI for operational purposes."
```

### Use Case 5: Exploring a Subject Area

**Scenario:** You want to understand all tables in the Claims subject area.

**Conversation Flow:**
```
You: "What tables are in the Claims subject area?"

Claude:
[Calls datadict_get_subject_areas]
[Calls datadict_search_tables with subject_area="Claims"]

"The Claims subject area contains 18 tables:

**Core Claim Tables:**
1. **ADJD_MCE** (Adjudicated Medical Claim Event)
   - Claim header information
   - 47 columns including claim number, dates, amounts

2. **ADJD_MCE_SRVC** (Adjudicated Medical Claim Event Service)
   - Claim service line details
   - 89 columns including service codes, amounts, dates

3. **PRE_ADJD_MCE** (Pre-Adjudicated Medical Claim Event)
   - Claims before adjudication
   - Raw submitted claim data

**Supporting Tables:**
- ADJD_MCE_SRVC_DIAG (Claim diagnoses)
- ADJD_MCE_SRVC_PROC (Claim procedures)
- ADJD_MCE_SRVC_PROC_MOD (Procedure modifiers)
- ADJD_MCE_PROV (Claim providers)

**Reference Tables:**
- CLM_STS_TYP (Claim Status Type)
- CLM_TYP (Claim Type)
- BILL_TYP (Bill Type)
- REJ_RSN_TYP (Rejection Reason Type)

Would you like to see the relationships between these tables?"
```

---

## Advanced Queries

### Finding Related Tables
```
You: "What other tables work with ADJD_MCE_SRVC?"

Claude:
[Calls datadict_find_related_tables]

Shows:
- Tables with direct joins
- Tables in same subject area
- Commonly used together
```

### Understanding Business Terms
```
You: "What's the business name for CLM_NBR?"

Claude:
[Calls datadict_search_business_glossary with "CLM_NBR"]

Shows: Business terminology, definitions, and usage context
```

### Exploring Table Metadata
```
You: "Tell me about table update frequency and data sources"

Claude:
[Calls datadict_get_table_details]

Shows:
- Update frequency (Daily, Weekly, Monthly, etc.)
- Source systems
- Data ownership
- Last update timestamp
```

---

## Best Practices

### 1. Start Broad, Then Narrow
```
✓ Good:
  "Show me member tables" 
  → Review results
  → "Show me columns in MBR_COV"

✗ Avoid:
  "Give me the exact SQL to join 5 specific tables I haven't explored yet"
```

### 2. Understand Before Joining
```
✓ Good:
  "What's in the MEMBER table?"
  → Understand structure
  → "How does MEMBER join to claims?"
  
✗ Avoid:
  "Write a query with these tables" (without understanding them first)
```

### 3. Check Privacy Implications
```
✓ Good:
  "What PHI fields are in this table?"
  → Review sensitivity
  → Choose appropriate security view

✗ Avoid:
  Accessing PHI without understanding privacy levels
```

### 4. Explore Subject Areas
```
✓ Good:
  "What subject areas exist?"
  → "Show me tables in the Claims subject area"
  → Understand domain structure

✗ Avoid:
  Searching randomly without understanding data organization
```

### 5. Verify Relationships
```
✓ Good:
  "How do these tables join?"
  → Review documented joins
  → Check key columns
  
✗ Avoid:
  Assuming joins without verification
```

---

## Troubleshooting

### "Table Not Found"
```
You: "Show me the MEMBERS table"

Claude: "I couldn't find a table called 'MEMBERS'. Did you mean:
- MEMBER (singular)
- MBR_COV
- MBR_COV_HIST

Would you like details on any of these?"

[Use search to find correct table name]
```

### "How Do These Tables Relate?"
```
You: "I can't figure out how to join TABLE_A to TABLE_B"

Claude: [Checks datadict_get_table_joins]
       [If no direct join found]
       "These tables don't have a documented direct join. However:
       
       **Option 1:** Intermediate table approach
       TABLE_A → INTERMEDIATE → TABLE_B
       
       **Option 2:** Common keys
       Both tables have KEY_X - you might join on that
       
       Would you like me to explore either approach?"
```

### "Too Many Results"
```
You: "Find columns with 'date'"

Claude: "That search returned 450 columns. Let me help narrow it down:
        - Specify a database?
        - Filter by table type?
        - Looking for specific date type (effective, termination, service)?"
```

---

## Query Templates

### Template 1: Member-Claim Analysis
```sql
-- Find claims for specific members
SELECT 
    m.MBR_NBR,
    m.FIRST_NM,
    m.LAST_NM,
    c.CLM_NBR,
    c.SRVC_DT,
    c.PAID_AMT
FROM EDWBASESECUREVIEW2.MEMBER m
JOIN EDWBASESECUREVIEW2.MBR_COV mc ON m.EDW_MBR_ID = mc.EDW_MBR_ID
JOIN EDWBASESECUREVIEW2.ADJD_MCE_SRVC c ON mc.EDW_MBR_COV_ID = c.EDW_MBR_COV_ID
WHERE m.MBR_NBR = '123456789'
  AND c.SRVC_DT BETWEEN '2024-01-01' AND '2024-12-31'
```

### Template 2: Diagnosis Code Lookup
```sql
-- Find all claims with specific diagnosis
SELECT 
    c.CLM_NBR,
    c.SRVC_DT,
    d.DIAG_CD,
    dc.DIAG_DESC
FROM EDWBASESECUREVIEW1.ADJD_MCE_SRVC c
JOIN EDWBASESECUREVIEW1.ADJD_MCE_SRVC_DIAG d ON c.CLM_LN_ID = d.CLM_LN_ID
JOIN EDWBASESECUREVIEW1.DIAG_CD dc ON d.DIAG_CD = dc.DIAG_CD
WHERE d.DIAG_CD LIKE 'E11%'  -- Diabetes
  AND d.DIAG_SEQ_NBR = 1      -- Primary diagnosis
```

### Template 3: Coverage Period Check
```sql
-- Verify member coverage during service period
SELECT 
    m.MBR_NBR,
    mc.ENRLMT_EFF_DT,
    mc.ENRLMT_TERM_DT,
    mc.PROD_ID,
    mc.PLAN_ID
FROM EDWBASESECUREVIEW1.MEMBER m
JOIN EDWBASESECUREVIEW1.MBR_COV mc ON m.EDW_MBR_ID = mc.EDW_MBR_ID
WHERE m.MBR_NBR = '123456789'
  AND '2024-06-15' BETWEEN mc.ENRLMT_EFF_DT AND COALESCE(mc.ENRLMT_TERM_DT, CURRENT_DATE)
```

---

## Tips for Efficient Discovery

### 1. Use Subject Areas as Starting Points
- "What subject areas exist?" → Get the big picture
- "Show me tables in [Subject Area]" → Drill down

### 2. Follow the Relationships
- Start with core entity (MEMBER, CLAIM)
- Ask "What tables join to this?"
- Build outward systematically

### 3. Check Reference Tables
- Look for tables ending in _TYP, _CD, _REF
- These provide decode values and descriptions

### 4. Understand Key Patterns
- **Surrogate Keys:** EDW_*_ID (generated IDs)
- **Natural Keys:** *_NBR (business identifiers)
- **Foreign Keys:** Link to parent tables
- **Timeline Indicators:** TMLN_IND = 'Y' (historical data)

### 5. Mind Your Privacy Views
- VIEW1: Full PHI access
- VIEW2: Limited dataset (dates >89 years masked)
- VIEW3: De-identified (PHI removed)

---

## Getting Help

### Ask Claude
```
"I don't know where to start with [topic]"
"What's the difference between TABLE_A and TABLE_B?"
"How do I find [specific data element]?"
"What do these abbreviations mean?"
"Show me an example query for [use case]"
```

### Common Abbreviations
- **MBR:** Member
- **COV:** Coverage
- **ADJD:** Adjudicated
- **MCE:** Medical Claim Event
- **SRVC:** Service
- **DIAG:** Diagnosis
- **PROC:** Procedure
- **PROV:** Provider
- **EDW:** Enterprise Data Warehouse
- **TYP:** Type
- **CD:** Code
- **NBR:** Number
- **EFF:** Effective
- **TERM:** Termination/Terminal

---

## Summary

The data dictionary MCP tools provide:
- **12 specialized tools** for data discovery
- **Comprehensive metadata** for all tables and columns
- **Relationship documentation** for join design
- **Privacy and security context** for compliance
- **Business terminology** for understanding technical names

Use these tools to explore, understand, and effectively query your Teradata data warehouse with confidence.
