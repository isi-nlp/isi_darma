import sqlite3
import sys 
from pathlib import Path 

def copy_table(source_db_path, new_db_path, table_name):
    # Connect to the source database
    source_conn = sqlite3.connect(source_db_path)
    source_cursor = source_conn.cursor()

    # Connect to the new empty database
    new_conn = sqlite3.connect(new_db_path)
    new_cursor = new_conn.cursor()

    # Get the schema of the table from the source database
    source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    schema = source_cursor.fetchone()[0]

    # Create the same table schema in the new empty database
    new_cursor.execute(schema)
    new_conn.commit()

    # Copy data from the source table to the new table in the new empty database
    source_cursor.execute(f"SELECT * FROM {table_name};")
    data = source_cursor.fetchall()
    new_cursor.executemany(f"INSERT INTO {table_name} VALUES ({','.join(['?' for _ in data[0]])});", data)
    new_conn.commit()

    # Close the connections
    source_conn.close()
    new_conn.close()

# Usage
src_fn = sys.argv[1]
dest_fn = Path(src_fn).stem + "_copy.db"
table_name = 'user'

copy_table(src_fn, dest_fn, table_name)

