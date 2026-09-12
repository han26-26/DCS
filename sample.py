import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.request
import json
import time

# --- GOOGLE SHEET DATABASE CONNECTIVITY ---
SHEET_ID = "1_Hg3U5RamQlWQNVfFmjoIka1kUfwCjax3MK89s4u7q8"

CSV_RESULTS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
CSV_QUESTIONS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"
CSV_USERS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet3"

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzY8KzbJhna-yYHWG2IAUXy6HOw2fiVOAiYSJ2wc8THH0eHOmirEfAqvmHst6wBz9Cb/exec"

EXAM_DURATION_MINUTES = 5

def get_mm_now():
    return datetime.utcnow() + timedelta(hours=6, minutes=30)

if "global_results_pool" not in st.session_state:
    st.session_state.global_results_pool = []

def get_results_from_sheet():
    try:
        df = pd.read_csv(CSV_RESULTS_URL)
        return df.values.tolist()
    except:
        return []

def get_questions_from_sheet():
    try:
        df = pd.read_csv(CSV_QUESTIONS_URL)
        if df is not None and not df.empty:
            sheet_questions = []
            for row in df.values.tolist():
                if len(row) >= 6 and pd.notna(row[0]):
                    sheet_questions.append({
                        "q": str(row[0]),
                        "options": [str(row[1]), str(row[2]), str(row[3]), str(row[4])],
                        "correct": str(row[5])
                    })
            if sheet_questions:
                return sheet_questions
    except:
        pass
    return []

def save_result_to_sheet(username, score):
    timestamp = get_mm_now().strftime("%Y-%m-%d %H:%M:%S")
    new_record = [timestamp, username, score]
    if new_record not in st.session_state.global_results_pool:
        st.session_state.global_results_pool.append(new_record)
        
    try:
        payload = json.dumps({"timestamp": timestamp, "username": username, "score": int(score)}).encode('utf-8')
        req = urllib.request.Request(WEB_APP_URL, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req, timeout=3)
    except:
        pass

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Secure Exam Terminal", page_icon="🔐", layout="centered")

st.markdown(
    """
    <style>
    div[data-testid="stTextInput"] {
        max-width: 350px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_role" not in st.session_state: st.session_state.user_role = None
if "username" not in st.session_state: st.session_state.username = None
if "submitted" not in st.session_state: st.session_state.submitted = False

with st.sidebar:
    try:
        st.image("PU-logo.jpg", use_container_width=True)
    except:
        pass
    st.markdown("<h4 style='text-align: center;'>Pyay University</h4>", unsafe_allow_html=True)
    st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("PU-logo.jpg", width=150)
    except:
        pass

if not st.session_state.logged_in:
    st.title("🔐 Pyay University Online Examination Portal")
    st.subheader("Center for Human Resource Development")
    
    username = st.text_input("Username (Case-sensitive)")
    password = st.text_input("Password", type="password")
    
    if st.button("Secure Login", type="primary"):
        entered_user = username.strip()
        entered_pass = str(password).strip()
        
