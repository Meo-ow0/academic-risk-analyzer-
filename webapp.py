import os
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st

# ==========================================
# CONFIGURATION & CUSTOM AESTHETIC SKIN
# ==========================================
st.set_page_config(page_title="Academic Risk Analyzer", layout="wide")

st.markdown("""
    <style>
        .stApp {
            background: url("https://i.imgur.com/55kVUO4.png") !important;
            background-size: 300px !important;
            background-color: #efd1d1 !important;
            background-blend-mode: overlay !important;
            font-family: "Lucida Grande", "Lucida Sans Unicode", Verdana, sans-serif !important;
        }
        h1 {
            color: #000000 !important;
            text-shadow: -2px 3px 0 #fcbfda !important;
            font-style: italic !important;
            font-weight: bold !important;
        }
        h2, h3, h4 {
            color: #000000 !important;
            border-bottom: 1px solid #f7c3d8 !important;
            letter-spacing: .03em !important;
            font-style: oblique !important;
        }
        .block-container {
            background: linear-gradient(to right, #fff7f7, #fbe7ea, #fde4e6) !important;
            padding: 2.5rem !important;
            border-radius: 12px !important;
            box-shadow: 0px 3px 16px #efd1d1 !important;
            border: 2px solid #ffdcdc !important;
            margin-top: 20px;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(to bottom, #fff7f7, #fff2f4, #ffeced) !important;
            border-right: 2px solid #efd1d1 !important;
        }
        div[data-testid="stMetricBlock"] {
            background: radial-gradient(circle closest-corner at center, #fef2f3 0%, #ffe8e8 70%) !important;
            border: 5px double white !important;
            border-radius: 10px !important;
            box-shadow: 5px 5px 5px #cccccc !important;
            padding: 15px !important;
        }
        div[data-testid="stMetricLabel"] > div { color: #700 !important; font-weight: bold !important; }
        div[data-testid="stDataFrame"] {
            background-color: #ffffff !important;
            border: 2px solid #f3efec !important;
            border-radius: 5px !important;
            box-shadow: inset 1px 0 5px #f6c2d8 !important;
        }
        .stTabs [data-baseweb="tab"] {
            color: #700 !important;
            background-color: #fdf5f4 !important;
            border: 1px solid #efd1d1 !important;
            border-radius: 8px 8px 0px 0px !important;
            padding: 5px 12px !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #fee6ee !important;
            border: 2px solid #fbc4db !important;
            font-weight: bold !important;
        }
        .stButton > button {
            background-color: #FDF5F2 !important;
            color: #000000 !important;
            border: 1.6px solid #f7c1d9 !important;
            border-radius: 10px !important;
            font-weight: 570 !important;
            box-shadow: 3px 3px 5px #cccccc !important;
        }
        .stButton > button:hover {
            background: url("https://i.imgur.com/G2CGQBx.jpeg") !important;
            background-size: 500px !important;
            color: white !important;
            text-shadow: 1px 1px 2px rgb(0 0 0) !important;
            -webkit-text-stroke: .25px #ffffff !important;
        }
        .sparkle-separator { text-align: center; color: #ff9eba; margin: 15px 0; font-size: 20px; }
    </style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "academic_records.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS students (student_id TEXT PRIMARY KEY, name TEXT NOT NULL, attendance_pct REAL NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS performance (log_id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, subject TEXT NOT NULL, assignment_score REAL, exam_score REAL)')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# UI VIEW
# ==========================================
st.title("🎓 University Academic Performance & Risk Analyzer")
st.markdown('<div class="sparkle-separator">₊✩‧₊˚౨ৎ˚₊✩‧₊ ♡ ₊✩‧₊˚౨ৎ˚₊✩‧₊</div>', unsafe_allow_html=True)

st.sidebar.header("📁 Control Panel")
uploaded_file = st.sidebar.file_uploader("Upload Student Spreadsheet", type=["csv", "xlsx"])

if uploaded_file is not None:
    df = None
    with st.spinner("⏳ Parsing records..."):
        try:
            if uploaded_file.name.endswith('.xlsx'):
                # Using the specialized calamine engine to completely ignore the broken XML styles
                df = pd.read_excel(uploaded_file, engine='calamine')
            else:
                df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
            
    if df is not None:
        st.toast("⚡ Data parsed successfully!", icon="✅")
        df.columns = df.columns.str.strip().str.lower()
        
        required_cols = ['student_id', 'name', 'attendance_pct', 'exam_score']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"❌ Missing required columns: {missing_cols}. Please fix your spreadsheet headers!")
        else:
            df = df.dropna(subset=['student_id'])
            df['exam_score'] = df['exam_score'].fillna(0)
            
            risk_condition = (df['attendance_pct'] < 75.0) | (df['exam_score'] < 40.0)
            df['risk_status'] = np.where(risk_condition, 'At-Risk', 'Clear')
            
            # Metrics
            total_students = len(df)
            at_risk_count = len(df[df['risk_status'] == 'At-Risk'])
            avg_attendance = df['attendance_pct'].mean()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Processed Total ♡", f"{total_students} Students")
            col2.metric("Flagged Risk Profiles ♡", f"{at_risk_count} Profiles")
            col3.metric("Avg Course Attendance ♡", f"{avg_attendance:.1f}%")
            
            st.markdown('<div class="sparkle-separator">♡ ♡ ♡</div>', unsafe_allow_html=True)
            
            st.subheader("📊 Performance Cluster Analysis")
            st.scatter_chart(data=df, x="attendance_pct", y="exam_score", color="risk_status", use_container_width=True)
            
            tab1, tab2, tab3 = st.tabs(["⚠️ Flagged Risk Roster", "📋 Cleaned Dataset Matrix", "🗄️ Database Archive"])
            
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
                
            with tab3:
                st.subheader("Live Relational SQLite Archive Status")
                conn = sqlite3.connect(DB_PATH)
                try:
                    db_df = pd.read_sql_query("SELECT * FROM students", conn)
                    st.dataframe(db_df, use_container_width=True)
                except:
                    st.info("Database storage history is empty.")
                finally:
                    conn.close()
                
            st.markdown('<div class="sparkle-separator">₊✩‧₊˚౨ৎ˚₊✩‧₊</div>', unsafe_allow_html=True)
            
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("Commit Processed Logs to SQLite Database", use_container_width=True):
                    conn = sqlite3.connect(DB_PATH)
                    df[['student_id', 'name', 'attendance_pct']].drop_duplicates().to_sql('students', conn, if_exists='append', index=False)
                    perf_cols = ['student_id', 'subject', 'assignment_score', 'exam_score']
                    existing_perf_cols = [c for c in perf_cols if c in df.columns]
                    df[existing_perf_cols].to_sql('performance', conn, if_exists='append', index=False)
                    conn.close()
                    st.success("Successfully migrated and archived all rows! ♡")
                        
            with action_col2:
                at_risk_names = df[df['risk_status'] == 'At-Risk']['name'].tolist()
                report_text = f"ACADEMIC RISK REPORT\n====================\nTotal Flagged: {len(at_risk_names)}\n\nProfiles:\n" + "\n".join([f"- {name}" for name in at_risk_names])
                st.download_button(label="📥 Download Official Risk Roster Report (.txt)", data=report_text, file_name="academic_risk_summary.txt", mime="text/plain", use_container_width=True)
else:
    st.info("💡 Getting Started: Please upload a student CSV or Excel file using the sidebar panel to launch analytics engines.")