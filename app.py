import os
import sqlite3
import pandas as pd
import numpy as np

# ==========================================
# STEP A: DYNAMIC PATH SETUP
# ==========================================
# This finds exactly where this app.py file lives on your Windows PC
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# These build absolute paths to your data so Python never gets lost
CSV_PATH = os.path.join(BASE_DIR, "student_data.csv")
DB_PATH = os.path.join(BASE_DIR, "academic_records.db")


# ==========================================
# STEP B: DATABASE INITIALIZATION
# ==========================================
def init_database():
    """Creates a relational SQL database structure with data safety rules."""
    print("-> Initializing SQLite Database...")
    
    # Connects to the database file (creates it if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Turn on Foreign Key protection rules
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Create the Master Students Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            attendance_pct REAL NOT NULL
        )
    ''')
    
    # Create the Performance Records Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            subject TEXT NOT NULL,
            assignment_score REAL,
            exam_score REAL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("-> Database Schema Created Successfully.")


# ==========================================
# STEP C: PANDAS & NUMPY PIPELINE
# ==========================================
def run_data_pipeline():
    """Ingests data, cleans anomalies, and runs the risk algorithm."""
    print("\n-> Ingesting and Cleaning CSV Data...")
    
    # CRITICAL CHECK: Make sure the file actually exists before reading it
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: Cannot find '{CSV_PATH}'. Make sure it's in the same folder!")
        return None

    # Load file into a Pandas DataFrame
    df = pd.read_csv(CSV_PATH)
    
    # 1. Clean: Drop rows that completely lack a student_id
    df = df.dropna(subset=['student_id'])
    
    # 2. Clean: Fill blank exam scores with 0 so math calculations don't crash
    df['exam_score'] = df['exam_score'].fillna(0)
    
    # 3. Algorithmic Filtering: Risk Engine using NumPy
    # Flag student if attendance < 75% OR exam score < 40
    risk_condition = (df['attendance_pct'] < 75.0) | (df['exam_score'] < 40.0)
    df['risk_status'] = np.where(risk_condition, 'At-Risk', 'Clear')
    
    print("-> Data Cleaning and Risk Analysis Complete.")
    return df


# ==========================================
# STEP D: CORE EXECUTION ENGINE
# ==========================================
if __name__ == "__main__":
    print("=== STARTING ACADEMIC RISK ANALYZER INTERN PROJECT ===")
    
    # 1. Setup Database
    init_database()
    
    # 2. Process Data
    processed_df = run_data_pipeline()
    
    if processed_df is not None:
        # 3. Display the At-Risk Students instantly in terminal
        print("\n=== SYSTEM ALERT: FLAGGED AT-RISK STUDENTS ===")
        at_risk = processed_df[processed_df['risk_status'] == 'At-Risk']
        print(at_risk[['student_id', 'name', 'attendance_pct', 'exam_score']])
        
        # 4. Save clean data directly into SQL tables
        print("\n-> Archiving records into SQLite Tables...")
        conn = sqlite3.connect(DB_PATH)
        
        # Isolate core profile columns and remove duplicates to save in 'students'
        students_table = processed_df[['student_id', 'name', 'attendance_pct']].drop_duplicates()
        students_table.to_sql('students', conn, if_exists='append', index=False)
        
        # Save grade details to 'performance' table
        performance_table = processed_df[['student_id', 'subject', 'assignment_score', 'exam_score']]
        performance_table.to_sql('performance', conn, if_exists='append', index=False)
        
        conn.close()
        print("=== PROCESS COMPLETE: ALL LOGS SAVED TO DATABASE ===")