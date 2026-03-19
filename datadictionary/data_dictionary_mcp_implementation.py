# Data Dictionary MCP Server - Python Implementation Example

## Overview
This document provides example Python code for implementing the data dictionary MCP server using the official MCP Python SDK.

## Prerequisites

```bash
pip install mcp anthropic-mcp teradatasql
```

## Server Implementation

```python
import asyncio
import logging
from typing import Any, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
import teradatasql

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection configuration
DB_CONFIG = {
    "host": "your_teradata_host",
    "user": "your_username",
    "password": "your_password",
    "database": "ADLSTE_HCLS_MCP_DATA_DICT"
}

class DataDictionaryMCPServer:
    """MCP Server for Data Dictionary Queries"""
    
    def __init__(self):
        self.server = Server("data-dictionary-server")
        self.connection = None
        self._register_handlers()
    
    def _get_connection(self):
        """Get or create database connection"""
        if self.connection is None:
            self.connection = teradatasql.connect(**DB_CONFIG)
        return self.connection
    
    def _execute_query(self, query: str, params: Optional[dict] = None) -> list:
        """Execute a query and return results"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            cursor.close()
    
    def _format_results(self, results: list, title: str = "Results") -> str:
        """Format query results as readable text"""
        if not results:
            return "No results found."
        
        # Create formatted table
        output = [f"\n{title}", "=" * 80]
        
        for i, row in enumerate(results, 1):
            output.append(f"\n[{i}]")
            for key, value in row.items():
                output.append(f"  {key}: {value}")
        
        output.append("\n" + "=" * 80)
        output.append(f"Total: {len(results)} row(s)")
        
        return "\n".join(output)
    
    def _register_handlers(self):
        """Register all tool handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools"""
            return [
                Tool(
                    name="datadict_search_databases",
                    description="Search for databases by name or description",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Keyword to search for (optional, returns all if not provided)"
                            }
                        }
                    }
                ),
                Tool(
                    name="datadict_search_tables",
                    description="Search for tables by name, business name, description, or subject area",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Keyword to search for"
                            },
                            "database_name": {
                                "type": "string",
                                "description": "Filter by specific database (optional)"
                            },
                            "table_type": {
                                "type": "string",
                                "description": "Filter by table type: Fact, Dimension, Keymap, MRR, etc. (optional)"
                            },
                            "subject_area": {
                                "type": "string",
                                "description": "Filter by subject area name (optional)"
                            }
                        },
                        "required": ["search_term"]
                    }
                ),
                Tool(
                    name="datadict_get_table_details",
                    description="Get comprehensive details about a specific table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database_name": {
                                "type": "string",
                                "description": "Database name"
                            },
                            "table_name": {
                                "type": "string",
                                "description": "Table name"
                            }
                        },
                        "required": ["database_name", "table_name"]
                    }
                ),
                Tool(
                    name="datadict_get_table_columns",
                    description="Get all columns for a specific table with detailed metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database_name": {
                                "type": "string",
                                "description": "Database name"
                            },
                            "table_name": {
                                "type": "string",
                                "description": "Table name"
                            }
                        },
                        "required": ["database_name", "table_name"]
                    }
                ),
                Tool(
                    name="datadict_search_columns",
                    description="Search for columns across all tables by name, business name, or description",
                    inputSchema={
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
                            "phi_only": {
                                "type": "boolean",
                                "description": "Only return PHI columns (optional)"
                            },
                            "pii_only": {
                                "type": "boolean",
                                "description": "Only return PII columns (optional)"
                            },
                            "key_columns_only": {
                                "type": "boolean",
                                "description": "Only return key columns (PK, FK, NK) (optional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 100)"
                            }
                        },
                        "required": ["search_term"]
                    }
                ),
                Tool(
                    name="datadict_get_table_joins",
                    description="Get all documented join relationships for a specific table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database_name": {
                                "type": "string",
                                "description": "Database name"
                            },
                            "table_name": {
                                "type": "string",
                                "description": "Table name"
                            }
                        },
                        "required": ["database_name", "table_name"]
                    }
                ),
                Tool(
                    name="datadict_search_business_glossary",
                    description="Search the business glossary for business-friendly terms",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Keyword to search for"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 50)"
                            }
                        },
                        "required": ["search_term"]
                    }
                ),
                Tool(
                    name="datadict_get_subject_areas",
                    description="List all subject areas with descriptions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "asset_id": {
                                "type": "integer",
                                "description": "Filter by specific asset ID (optional)"
                            }
                        }
                    }
                ),
                Tool(
                    name="datadict_find_related_tables",
                    description="Find tables related to a specific table (same subject area or direct joins)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database_name": {
                                "type": "string",
                                "description": "Database name"
                            },
                            "table_name": {
                                "type": "string",
                                "description": "Table name"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 50)"
                            }
                        },
                        "required": ["database_name", "table_name"]
                    }
                ),
                Tool(
                    name="datadict_get_sensitive_columns",
                    description="Find all columns marked as PHI, PII, or requiring de-identification",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database_name": {
                                "type": "string",
                                "description": "Filter by database (optional)"
                            },
                            "sensitivity_type": {
                                "type": "string",
                                "enum": ["PHI", "PII", "DEID", "ALL"],
                                "description": "Type of sensitivity (default: ALL)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 200)"
                            }
                        }
                    }
                ),
                Tool(
                    name="datadict_get_key_columns",
                    description="Find all primary keys, foreign keys, and natural keys for a table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database_name": {
                                "type": "string",
                                "description": "Database name"
                            },
                            "table_name": {
                                "type": "string",
                                "description": "Table name"
                            }
                        },
                        "required": ["database_name", "table_name"]
                    }
                ),
                Tool(
                    name="datadict_suggest_join_query",
                    description="Suggest SQL join query between two tables based on documented relationships",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "left_database": {
                                "type": "string",
                                "description": "Left table's database name"
                            },
                            "left_table": {
                                "type": "string",
                                "description": "Left table name"
                            },
                            "right_database": {
                                "type": "string",
                                "description": "Right table's database name"
                            },
                            "right_table": {
                                "type": "string",
                                "description": "Right table name"
                            }
                        },
                        "required": ["left_database", "left_table", "right_database", "right_table"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls"""
            try:
                if name == "datadict_search_databases":
                    return await self._search_databases(arguments)
                elif name == "datadict_search_tables":
                    return await self._search_tables(arguments)
                elif name == "datadict_get_table_details":
                    return await self._get_table_details(arguments)
                elif name == "datadict_get_table_columns":
                    return await self._get_table_columns(arguments)
                elif name == "datadict_search_columns":
                    return await self._search_columns(arguments)
                elif name == "datadict_get_table_joins":
                    return await self._get_table_joins(arguments)
                elif name == "datadict_search_business_glossary":
                    return await self._search_business_glossary(arguments)
                elif name == "datadict_get_subject_areas":
                    return await self._get_subject_areas(arguments)
                elif name == "datadict_find_related_tables":
                    return await self._find_related_tables(arguments)
                elif name == "datadict_get_sensitive_columns":
                    return await self._get_sensitive_columns(arguments)
                elif name == "datadict_get_key_columns":
                    return await self._get_key_columns(arguments)
                elif name == "datadict_suggest_join_query":
                    return await self._suggest_join_query(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error executing tool: {str(e)}"
                )]
    
    async def _search_databases(self, args: dict) -> list[TextContent]:
        """Search for databases"""
        search_term = args.get("search_term", "")
        
        query = """
        SELECT 
            d.DB_ID,
            d.DB_NM as "Database Name",
            d.DB_BUS_NM as "Business Name",
            d.DB_DESC as "Description",
            d.INSTC_NM as "Instance",
            d.DBMS_TYP_NM as "DBMS Type",
            d.ACTV_DB_IND as "Active"
        FROM ADLSTE_HCLS_MCP_DATA_DICT.DB d
        WHERE d.ACTV_DB_IND = 'Y'
        """
        
        if search_term:
            query += """
            AND (
                UPPER(d.DB_NM) LIKE UPPER(?)
                OR UPPER(d.DB_BUS_NM) LIKE UPPER(?)
                OR UPPER(d.DB_DESC) LIKE UPPER(?)
            )
            """
            params = [f"%{search_term}%"] * 3
        else:
            params = None
        
        query += " ORDER BY d.DB_NM"
        
        results = self._execute_query(query, params)
        formatted = self._format_results(results, "Database Search Results")
        
        return [TextContent(type="text", text=formatted)]
    
    async def _search_tables(self, args: dict) -> list[TextContent]:
        """Search for tables"""
        search_term = args["search_term"]
        database_name = args.get("database_name")
        table_type = args.get("table_type")
        subject_area = args.get("subject_area")
        
        query = """
        SELECT 
            t.TBL_ID,
            d.DB_NM as "Database",
            t.TBL_NM as "Table Name",
            t.TBL_BUS_NM as "Business Name",
            t.TBL_BUS_DESC as "Description",
            sa.SBJ_AREA_NM as "Subject Area",
            t.TBL_TYP_TXT as "Table Type",
            t.TBL_SRC_TXT as "Source System",
            t.UPDT_FREQ_TXT as "Update Frequency"
        FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL t
        JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB d ON t.DB_ID = d.DB_ID
        LEFT JOIN ADLSTE_HCLS_MCP_DATA_DICT.SBJ_AREA sa ON t.SBJ_AREA_ID = sa.SBJ_AREA_ID
        WHERE (
            UPPER(t.TBL_NM) LIKE UPPER(?)
            OR UPPER(t.TBL_BUS_NM) LIKE UPPER(?)
            OR UPPER(t.TBL_BUS_DESC) LIKE UPPER(?)
            OR UPPER(sa.SBJ_AREA_NM) LIKE UPPER(?)
        )
        """
        
        params = [f"%{search_term}%"] * 4
        
        if database_name:
            query += " AND d.DB_NM = ?"
            params.append(database_name)
        
        if table_type:
            query += " AND t.TBL_TYP_TXT = ?"
            params.append(table_type)
        
        if subject_area:
            query += " AND sa.SBJ_AREA_NM = ?"
            params.append(subject_area)
        
        query += " ORDER BY d.DB_NM, t.TBL_NM"
        
        results = self._execute_query(query, params)
        formatted = self._format_results(results, f"Table Search Results for '{search_term}'")
        
        return [TextContent(type="text", text=formatted)]
    
    async def _get_table_details(self, args: dict) -> list[TextContent]:
        """Get table details"""
        database_name = args["database_name"]
        table_name = args["table_name"]
        
        query = """
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
            t.USER_UPDT_ID as "Last Updated By",
            t.USER_UPDT_TS as "Last Updated Timestamp"
        FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL t
        JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB d ON t.DB_ID = d.DB_ID
        LEFT JOIN ADLSTE_HCLS_MCP_DATA_DICT.SBJ_AREA sa ON t.SBJ_AREA_ID = sa.SBJ_AREA_ID
        WHERE d.DB_NM = ?
          AND t.TBL_NM = ?
        """
        
        results = self._execute_query(query, [database_name, table_name])
        formatted = self._format_results(results, f"Table Details: {database_name}.{table_name}")
        
        return [TextContent(type="text", text=formatted)]
    
    async def _get_table_columns(self, args: dict) -> list[TextContent]:
        """Get table columns"""
        database_name = args["database_name"]
        table_name = args["table_name"]
        
        query = """
        SELECT 
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
            c.PHI_IND as "PHI",
            c.PII_IND as "PII",
            c.DATA_PVT_LVL_NM as "Privacy Level"
        FROM ADLSTE_HCLS_MCP_DATA_DICT.TBL_COL c
        JOIN ADLSTE_HCLS_MCP_DATA_DICT.TBL t ON c.TBL_ID = t.TBL_ID
        JOIN ADLSTE_HCLS_MCP_DATA_DICT.DB d ON t.DB_ID = d.DB_ID
        WHERE d.DB_NM = ?
          AND t.TBL_NM = ?
        ORDER BY c.COL_ID
        """
        
        results = self._execute_query(query, [database_name, table_name])
        formatted = self._format_results(results, f"Columns for {database_name}.{table_name}")
        
        return [TextContent(type="text", text=formatted)]
    
    # Implement remaining tool methods similarly...
    
    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

# Main entry point
if __name__ == "__main__":
    server = DataDictionaryMCPServer()
    asyncio.run(server.run())
```

## Configuration File (mcp_config.json)

```json
{
  "mcpServers": {
    "data-dictionary": {
      "command": "python",
      "args": ["/path/to/data_dictionary_mcp_server.py"],
      "env": {
        "TD_HOST": "your_teradata_host",
        "TD_USER": "your_username",
        "TD_PASSWORD": "your_password"
      }
    }
  }
}
```

## Testing the Server

```python
# test_data_dictionary_server.py
import asyncio
from data_dictionary_mcp_server import DataDictionaryMCPServer

async def test_search_tables():
    """Test table search functionality"""
    server = DataDictionaryMCPServer()
    
    # Test search
    result = await server._search_tables({
        "search_term": "member"
    })
    
    print(result[0].text)

async def test_get_table_details():
    """Test getting table details"""
    server = DataDictionaryMCPServer()
    
    result = await server._get_table_details({
        "database_name": "EDWBASESECUREVIEW1",
        "table_name": "MEMBER"
    })
    
    print(result[0].text)

if __name__ == "__main__":
    asyncio.run(test_search_tables())
    asyncio.run(test_get_table_details())
```

## Usage with Claude

Once the MCP server is running, Claude can use it like this:

```
User: "What tables do we have for claims data?"

Claude: [Calls datadict_search_tables with search_term="claims"]
        [Receives results and presents them to user]

User: "Show me the columns in ADJD_MCE_SRVC"

Claude: [Calls datadict_get_table_columns with database="EDWBASESECUREVIEW1", 
         table="ADJD_MCE_SRVC"]
        [Formats and presents the column information]
```

## Deployment Options

### 1. Local Development
```bash
python data_dictionary_mcp_server.py
```

### 2. Docker Container
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY data_dictionary_mcp_server.py .

CMD ["python", "data_dictionary_mcp_server.py"]
```

### 3. Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-dictionary-mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: data-dictionary-mcp
  template:
    metadata:
      labels:
        app: data-dictionary-mcp
    spec:
      containers:
      - name: server
        image: data-dictionary-mcp:latest
        env:
        - name: TD_HOST
          valueFrom:
            secretKeyRef:
              name: teradata-credentials
              key: host
        - name: TD_USER
          valueFrom:
            secretKeyRef:
              name: teradata-credentials
              key: username
        - name: TD_PASSWORD
          valueFrom:
            secretKeyRef:
              name: teradata-credentials
              key: password
```

## Monitoring and Logging

```python
# Add to DataDictionaryMCPServer class

def _log_query(self, tool_name: str, args: dict, result_count: int):
    """Log query for monitoring"""
    logger.info(f"Tool: {tool_name}, Args: {args}, Results: {result_count}")
    
    # Optional: Send to monitoring system
    # monitoring.track_event("mcp_tool_call", {
    #     "tool": tool_name,
    #     "database": args.get("database_name"),
    #     "result_count": result_count
    # })
```

## Security Best Practices

1. **Use environment variables** for credentials, never hardcode
2. **Implement connection pooling** to manage database connections efficiently
3. **Add rate limiting** to prevent abuse
4. **Validate all inputs** before constructing SQL queries
5. **Use parameterized queries** to prevent SQL injection
6. **Log all accesses** for audit trail
7. **Implement role-based access** if needed

## Performance Optimization

```python
from functools import lru_cache
import asyncio

class DataDictionaryMCPServer:
    
    @lru_cache(maxsize=100)
    def _get_cached_subject_areas(self):
        """Cache subject areas since they change infrequently"""
        query = "SELECT * FROM ADLSTE_HCLS_MCP_DATA_DICT.SBJ_AREA"
        return self._execute_query(query)
    
    async def _execute_query_async(self, query: str, params=None):
        """Execute query asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._execute_query, 
            query, 
            params
        )
```

## Next Steps

1. Implement the remaining tool methods following the pattern shown
2. Add comprehensive error handling and input validation
3. Set up monitoring and alerting
4. Create integration tests
5. Deploy to your environment
6. Train users on how to interact with the data dictionary through Claude
