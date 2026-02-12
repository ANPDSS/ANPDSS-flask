#!/usr/bin/env python3

"""
Migration script to add _is_guest column to the users table.
This script safely adds the column without losing existing data.

Usage:
> cd /Users/sathwik/CSPTeamRepo/ANPDSS/ANPDSS-flask
> python scripts/add_is_guest_column.py
"""

import sys
import os

# Add the directory containing main.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, db
from sqlalchemy import text

def add_is_guest_column():
    """Add _is_guest column to users table if it doesn't exist."""
    with app.app_context():
        try:
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]

            if '_is_guest' in columns:
                print("Column '_is_guest' already exists in the users table.")
                return

            # Add the column with a default value of 0 (False)
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN _is_guest BOOLEAN DEFAULT 0 NOT NULL'))
                conn.commit()

            print("Successfully added '_is_guest' column to the users table.")
            print("All existing users have been set to _is_guest = False (0).")

        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Adding _is_guest column")
    print("=" * 60)
    add_is_guest_column()
    print("=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)
