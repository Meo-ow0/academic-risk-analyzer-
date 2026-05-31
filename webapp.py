import os
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st

# ==========================================
# CONFIGURATION & PATHS
# ==========================================
st.set_page_config(page_title="Academic Risk Analyzer", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "academic_records.db")

# Ensure database exists
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY, name TEXT NOT NULL, attendance_pct REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT,
            subject TEXT NOT NULL, assignment_score REAL, exam_score REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# WEB UI VIEW
# ==========================================
st.title("🎓 University Academic Performance & Risk Analyzer")
st.markdown("Upload raw student spreadsheets, clean data parameters, and analyze institutional student risk profiles instantly.")

# Layout: Sidebar for actions
st.sidebar.header("📁 Data Control Panel")
uploaded_file = st.sidebar.file_saver = st.sidebar.file_uploader("Upload Student CSV File", type=["csv"])

if uploaded_file is not None:
    # 1. Ingest Data using Pandas
    df = pd.read_csv(uploaded_file)
    
    # 2. Pipeline Cleaning
    df = df.dropna(subset=['student_id'])
    df['exam_score'] = df['exam_score'].fillna(0)
    
    # 3. NumPy Algorithmic Risk Flagging
    risk_condition = (df['attendance_pct'] < 75.0) | (df['exam_score'] < 40.0)
    df['risk_status'] = np.where(risk_condition, 'At-Risk', 'Clear')
    
    # ==========================================
    # METRICS DISPLAY PANEL
    # ==========================================
    total_students = len(df)
    at_risk_count = len(df[df['risk_status'] == 'At-Risk'])
    avg_attendance = df['attendance_pct'].mean()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records Processed", f"{total_students} Students")
    col2.metric("Flagged 'At-Risk' Profiles", f"{at_risk_count} Students", delta=f"{at_risk_count} Urgent", delta_color="inverse")
    col3.metric("Average Course Attendance", f"{avg_attendance:.1f}%")
    
    st.markdown("---")
    
    # ==========================================
    # DATA VIEWS (TABS)
    # ==========================================
    tab1, tab2 = st.tabs(["⚠️ Flagged Risk Roster", "📋 Cleaned Dataset Matrix"])
    
    with tab1:
        st.subheader("Immediate Intervention Required")
        at_risk_df = df[df['risk_status'] == 'At-Risk']
        if not at_risk_df.empty:
            st.dataframe(at_risk_df[['student_id', 'name', 'attendance_pct', 'exam_score']], use_container_width=True)
        else:
            st.success("Excellent! No students currently fall below risk thresholds.")
            
    with tab2:
        st.subheader("All Sanitized Records")
        st.dataframe(df, use_container_width=True)
        
    # ==========================================
    # DATABASE ACTIONS
    # ==========================================
    st.markdown("---")
    st.subheader("💾 Database Synchronization")
    
    if st.button("Commit Processed Logs to SQLite Database"):
        try:
            conn = sqlite3.connect(DB_PATH)
            
            # Save profiles
            students_table = df[['student_id', 'name', 'attendance_pct']].drop_duplicates()
            students_table.to_sql('students', conn, if_exists='append', index=False)
            
            # Save grades
            performance_table = df[['student_id', 'subject', 'assignment_score', 'exam_score']]
            performance_table.to_sql('performance', conn, if_exists='append', index=False)
            
            conn.close()
            st.success("Successfully migrated and archived all rows to 'academic_records.db'!")
        except Exception as e:
            st.error(f"Database Sync Error: {e}. (This could mean records already exist in the database).")

else:
    st.info("💡 Getting Started: Please upload a student CSV file using the sidebar panel to launch analytics engines.")