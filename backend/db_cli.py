#!/usr/bin/env python3

import argparse
import sys
from db_helper import (
    list_tables, view_table_contents, get_table_schema,
    clean_table, export_table_to_json, import_json_to_table,
    check_db_size, backup_database, run_custom_query, DEFAULT_DB_PATH
)

def print_colored(text, color="green"):
    """Print colored text to terminal"""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "bold": "\033[1m",
        "underline": "\033[4m",
        "end": "\033[0m"
    }
    
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def print_table(data, headers):
    """Print data in a tabular format"""
    if not data:
        print("No data to display")
        return
    
    # Calculate column widths
    col_widths = [max(len(str(row[i])) for row in [headers] + data) for i in range(len(headers))]
    
    # Print headers
    header_line = " | ".join(f"{headers[i]:{col_widths[i]}}" for i in range(len(headers)))
    print_colored(header_line, "bold")
    print("-" * len(header_line))
    
    # Print data rows
    for row in data:
        print(" | ".join(f"{str(row[i]):{col_widths[i]}}" for i in range(len(row))))

def list_cmd(args):
    """List all tables in the database"""
    tables = list_tables(args.db_path)
    if tables:
        print_colored("\nTables:", "bold")
        for table in tables:
            print(f"  - {table}")

def view_cmd(args):
    """View contents of a table"""
    if not args.table:
        print_colored("Error: Table name is required", "red")
        return
    
    df = view_table_contents(args.table, args.db_path)
    if df is not None:
        # Get the number of rows to display
        rows_to_display = min(args.rows, len(df)) if args.rows > 0 else len(df)
        
        # Display the DataFrame
        if args.format == "json":
            print(df.head(rows_to_display).to_json(orient="records", indent=2))
        elif args.format == "csv":
            print(df.head(rows_to_display).to_csv(index=False))
        else:  # Default to table format
            print(df.head(rows_to_display))
        
        if rows_to_display < len(df):
            print(f"\n... and {len(df) - rows_to_display} more rows")

def schema_cmd(args):
    """Display schema of a table"""
    if not args.table:
        print_colored("Error: Table name is required", "red")
        return
    
    schema = get_table_schema(args.table, args.db_path)
    if schema:
        print_colored(f"\nSchema for table '{args.table}':", "bold")
        for col in schema:
            pk_str = "PRIMARY KEY" if col["primary_key"] else ""
            null_str = "NOT NULL" if col["notnull"] else ""
            default_val = f"DEFAULT {col['default_value']}" if col["default_value"] is not None else ""
            print(f"  - {col['name']} ({col['type']}) {pk_str} {null_str} {default_val}")

def clean_cmd(args):
    """Clean a table (delete all records)"""
    if not args.table:
        print_colored("Error: Table name is required", "red")
        return
    
    if args.force:
        result = clean_table(args.table, confirm=False, db_path=args.db_path)
    else:
        result = clean_table(args.table, db_path=args.db_path)
    
    if result:
        print_colored(f"Successfully cleaned table '{args.table}'", "green")

def export_cmd(args):
    """Export a table to JSON"""
    if not args.table:
        print_colored("Error: Table name is required", "red")
        return
    
    output_file = args.output if args.output else f"{args.table}_export.json"
    result = export_table_to_json(args.table, output_file, args.db_path)
    
    if result:
        print_colored(f"Successfully exported table '{args.table}' to {output_file}", "green")

def import_cmd(args):
    """Import data from JSON into a table"""
    if not args.file or not args.table:
        print_colored("Error: Both file and table name are required", "red")
        return
    
    result = import_json_to_table(args.file, args.table, replace=args.replace, db_path=args.db_path)
    
    if result:
        print_colored(f"Successfully imported data into table '{args.table}'", "green")

def info_cmd(args):
    """Display database information"""
    print_colored("Database Information:", "bold")
    print(f"Database path: {args.db_path}")
    
    size = check_db_size(args.db_path)
    if size > 0:
        tables = list_tables(args.db_path)
        
        if tables:
            print_colored("\nTable Statistics:", "blue")
            for table in tables:
                df = view_table_contents(table, args.db_path)
                if df is not None:
                    print(f"  - {table}: {len(df)} rows")

def backup_cmd(args):
    """Backup the database"""
    result = backup_database(args.output, args.db_path)
    
    if result:
        print_colored("Database backup created successfully", "green")

def query_cmd(args):
    """Run a custom SQL query"""
    if not args.sql:
        print_colored("Error: SQL query is required", "red")
        return
    
    try:
        result = run_custom_query(args.sql, args.db_path)
        
        if isinstance(result, list):
            if result:
                # For SELECT queries with results
                if args.format == "json":
                    import json
                    print(json.dumps(result, indent=2))
                else:
                    # Format as table
                    headers = result[0].keys()
                    rows = [[row[col] for col in headers] for row in result]
                    print_table(rows, headers)
                
                print(f"\nRows returned: {len(result)}")
            else:
                print("Query executed successfully. No results returned.")
        elif isinstance(result, dict):
            if "error" in result:
                print_colored(f"Error: {result['error']}", "red")
            else:
                print(f"Query executed successfully. Rows affected: {result.get('affected_rows', 0)}")
    except Exception as e:
        print_colored(f"Error executing query: {str(e)}", "red")

def main():
    parser = argparse.ArgumentParser(description="SQLite Database Helper CLI")
    parser.add_argument("--db-path", help="Path to the SQLite database file", default=DEFAULT_DB_PATH)
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List tables command
    list_parser = subparsers.add_parser("list", help="List all tables in the database")
    
    # View table command
    view_parser = subparsers.add_parser("view", help="View contents of a table")
    view_parser.add_argument("table", help="Table name")
    view_parser.add_argument("-r", "--rows", type=int, default=10, help="Number of rows to display (default: 10, use 0 for all)")
    view_parser.add_argument("-f", "--format", choices=["table", "json", "csv"], default="table", help="Output format")
    
    # Schema command
    schema_parser = subparsers.add_parser("schema", help="Show schema of a table")
    schema_parser.add_argument("table", help="Table name")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean a table (delete all records)")
    clean_parser.add_argument("table", help="Table name")
    clean_parser.add_argument("-f", "--force", action="store_true", help="Skip confirmation prompt")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export a table to JSON")
    export_parser.add_argument("table", help="Table name")
    export_parser.add_argument("-o", "--output", help="Output file name")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import data from JSON into a table")
    import_parser.add_argument("file", help="Input JSON file")
    import_parser.add_argument("table", help="Table name")
    import_parser.add_argument("-r", "--replace", action="store_true", help="Replace existing data")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Display database information")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup the database")
    backup_parser.add_argument("-o", "--output", help="Output file name")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Run a custom SQL query")
    query_parser.add_argument("sql", help="SQL query to execute")
    query_parser.add_argument("-f", "--format", choices=["table", "json"], default="table", help="Output format for results")
    
    args = parser.parse_args()
    
    # If no command is provided, show help
    if not args.command:
        parser.print_help()
        return
    
    # Execute the appropriate command
    if args.command == "list":
        list_cmd(args)
    elif args.command == "view":
        view_cmd(args)
    elif args.command == "schema":
        schema_cmd(args)
    elif args.command == "clean":
        clean_cmd(args)
    elif args.command == "export":
        export_cmd(args)
    elif args.command == "import":
        import_cmd(args)
    elif args.command == "info":
        info_cmd(args)
    elif args.command == "backup":
        backup_cmd(args)
    elif args.command == "query":
        query_cmd(args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0) 