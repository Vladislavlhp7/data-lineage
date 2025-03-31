import sqlite3
import os
import pandas as pd
from pathlib import Path
import json
import argparse

# Default database path
DEFAULT_DB_PATH = "./bank_digital_twin.db"

def get_db_connection(db_path=None):
    """Create a connection to the SQLite database"""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def list_tables(db_path=None):
    """List all tables in the database"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    conn.close()
    
    if not tables:
        print("No tables found in the database.")
        return []
    
    table_names = [table[0] for table in tables]
    print(f"Found {len(table_names)} tables: {', '.join(table_names)}")
    return table_names

def view_table_contents(table_name, db_path=None):
    """View the contents of a specific table"""
    conn = get_db_connection(db_path)
    
    try:
        # Try to read the table into a pandas DataFrame
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        
        if df.empty:
            print(f"Table '{table_name}' is empty.")
            return None
        
        print(f"Contents of table '{table_name}' ({len(df)} rows):")
        return df
    
    except (sqlite3.OperationalError, pd.io.sql.DatabaseError) as e:
        print(f"Error reading table '{table_name}': {str(e)}")
        conn.close()
        return None

def get_table_schema(table_name, db_path=None):
    """Get the schema of a specific table"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"PRAGMA table_info({table_name});")
        schema = cursor.fetchall()
        
        if not schema:
            print(f"No schema information found for table '{table_name}'.")
            conn.close()
            return None
        
        columns = []
        for col in schema:
            columns.append({
                "cid": col[0],
                "name": col[1],
                "type": col[2],
                "notnull": bool(col[3]),
                "default_value": col[4],
                "primary_key": bool(col[5])
            })
        
        conn.close()
        print(f"Schema for table '{table_name}':")
        return columns
    
    except sqlite3.OperationalError as e:
        print(f"Error getting schema for table '{table_name}': {str(e)}")
        conn.close()
        return None

def clean_table(table_name, confirm=True, db_path=None):
    """Delete all records from a table"""
    if confirm:
        confirmation = input(f"Are you sure you want to delete all records from '{table_name}'? (y/n): ")
        if confirmation.lower() != 'y':
            print("Operation cancelled.")
            return False
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"DELETE FROM {table_name};")
        conn.commit()
        row_count = cursor.rowcount
        print(f"Deleted all records from '{table_name}'. ({row_count} records affected)")
        
        cursor.execute(f"VACUUM;")
        conn.commit()
        print("Database vacuumed to reclaim space.")
        
        conn.close()
        return True
    
    except sqlite3.OperationalError as e:
        print(f"Error cleaning table '{table_name}': {str(e)}")
        conn.close()
        return False

def export_table_to_json(table_name, output_file=None, db_path=None):
    """Export a table to a JSON file"""
    if output_file is None:
        output_file = f"{table_name}_export.json"
    
    conn = get_db_connection(db_path)
    
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        
        if df.empty:
            print(f"Table '{table_name}' is empty. Nothing to export.")
            return False
        
        # Convert DataFrame to JSON
        json_data = df.to_json(orient="records", indent=4)
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write(json_data)
        
        print(f"Exported {len(df)} records from '{table_name}' to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error exporting table '{table_name}' to JSON: {str(e)}")
        return False

def import_json_to_table(input_file, table_name, replace=False, db_path=None):
    """Import data from a JSON file into a table"""
    if not os.path.exists(input_file):
        print(f"File '{input_file}' not found.")
        return False
    
    try:
        # Read JSON file
        with open(input_file, 'r') as f:
            json_data = json.load(f)
        
        if not json_data:
            print("JSON file is empty. Nothing to import.")
            return False
        
        # Convert to DataFrame
        df = pd.DataFrame(json_data)
        
        conn = get_db_connection(db_path)
        
        # If replace is True, delete existing records
        if replace:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name};")
            conn.commit()
            print(f"Deleted existing records from '{table_name}'.")
        
        # Import data
        df.to_sql(table_name, conn, if_exists='append', index=False)
        
        conn.close()
        print(f"Imported {len(df)} records into '{table_name}'.")
        return True
    
    except Exception as e:
        print(f"Error importing data into '{table_name}': {str(e)}")
        return False

def check_db_size(db_path=None):
    """Check the size of the database file"""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
        
    try:
        size_bytes = os.path.getsize(db_path)
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024
        
        if size_mb >= 1:
            print(f"Database size: {size_mb:.2f} MB")
        else:
            print(f"Database size: {size_kb:.2f} KB")
        
        return size_bytes
    except FileNotFoundError:
        print(f"Database file '{db_path}' not found.")
        return 0

def backup_database(backup_path=None, db_path=None):
    """Create a backup of the database"""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
        
    if not os.path.exists(db_path):
        print(f"Database file '{db_path}' not found.")
        return False
    
    if backup_path is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"db_backup_{timestamp}.db"
    
    import shutil
    try:
        shutil.copy2(db_path, backup_path)
        print(f"Database backup created at {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating database backup: {str(e)}")
        return False

def run_custom_query(query, db_path=None):
    """Run a custom SQL query on the database"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        
        # If the query is a SELECT query, fetch results
        if query.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            
            # Convert to list of dicts
            result_dicts = []
            for row in results:
                result_dicts.append({column_names[i]: row[i] for i in range(len(column_names))})
            
            conn.close()
            return result_dicts
        else:
            # For non-SELECT queries, commit and return affected row count
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            return {"affected_rows": affected_rows}
    
    except Exception as e:
        print(f"Error executing query: {str(e)}")
        conn.close()
        return {"error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQLite Database Helper")
    parser.add_argument("--db-path", help="Path to the SQLite database file", default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    
    db_path = args.db_path
    
    print("SQLite Database Helper")
    print(f"Database path: {db_path}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database file does not exist. It will be created when you first use it.")
    else:
        check_db_size(db_path)
        tables = list_tables(db_path)
        
        if tables:
            # Ask which table to inspect
            table_input = input("\nEnter table name to view (or press Enter to skip): ")
            if table_input and table_input in tables:
                df = view_table_contents(table_input, db_path)
                if df is not None:
                    print(df.head(10))  # Show first 10 rows
                    if len(df) > 10:
                        print(f"... and {len(df) - 10} more rows")
                
                # Show schema
                schema = get_table_schema(table_input, db_path)
                if schema:
                    for col in schema:
                        pk_str = "PRIMARY KEY" if col["primary_key"] else ""
                        null_str = "NOT NULL" if col["notnull"] else ""
                        print(f"  - {col['name']} ({col['type']}) {pk_str} {null_str}") 