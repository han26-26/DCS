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
# Google Sheet (Sheet3) မှ User အားလုံးကို Header မပါဘဲ တိုက်ရိုက်ဖတ်ယူခြင်း
        all_users = {}
        try:
            # header=None ထည့်လိုက်ခြင်းဖြင့် ပထမဆုံး row ကို header လို့ မသတ်မှတ်တော့ဘဲ ဒေတာအဖြစ် အကုန်ဖတ်မည်
            df_users = pd.read_csv(CSV_USERS_URL, header=None)
            if df_users is not None and not df_users.empty:
                for _, row in df_users.iterrows():
                    if len(row) >= 2 and pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                        u_val = str(row.iloc[0]).strip()
                        p_val = str(row.iloc[1]).strip()
                        # 'Username' ဆိုတဲ့ ခေါင်းစဉ်ပါလာလျှင် ကျော်ရန်
                        if u_val.lower() != "username":
                            all_users[u_val] = p_val
        except Exception as e:
            pass

        # Login စစ်ဆေးခြင်း
        if entered_user in all_users and entered_pass == all_users[entered_user]:
            if entered_user.lower() == "admin":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.username = "admin"
                st.rerun()
            else:
                sheet_data = get_results_from_sheet()
                submitted_users = [str(r[1]) for r in sheet_data if len(r) > 1]
                submitted_users += [str(r[1]) for r in st.session_state.global_results_pool]
                
                if entered_user in submitted_users:
                    st.error(f"❌ Access Denied: User '{entered_user}' has already submitted the exam. Account Locked.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "student"
                    st.session_state.username = entered_user
                    st.session_state.submitted = False
                    st.session_state.start_time = get_mm_now()
                    st.rerun()
        else:
            st.error("Invalid credentials. Please try again.")
else:
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.username = None
        st.session_state.submitted = False
        if "start_time" in st.session_state: del st.session_state.start_time
        st.rerun()
        
    if st.session_state.user_role == "admin":
        st.title("👩‍🏫 Administrative Control Panel: Question Bank & Result Management")
        
        st.sidebar.subheader("⚙️ System Control")
        if st.sidebar.button("♻️ Force Reboot System", type="secondary"):
            st.session_state.global_results_pool = []
            st.sidebar.success("Memory Pool Cleared Successfully!")
            time.sleep(0.5)
            st.rerun()
        
        tab1, tab2 = st.tabs(["📝 View Results Logs", "➕ Add Secure Questions"])
        
        with tab1:
            st.subheader("🔒 Terminal Live Records")
            db_data = get_results_from_sheet()
            display_data = []
            
            for r in db_data:
                if len(r) >= 3 and str(r[0]).lower() != "timestamp":
                    display_data.append({"Timestamp": r[0], "Student Username": r[1], "Score Obtained": f"{r[2]} Points"})
            
            for r in st.session_state.global_results_pool:
                row_dict = {"Timestamp": r[0], "Student Username": r[1], "Score Obtained": f"{r[2]} Points"}
                if row_dict not in display_data:
                    display_data.append(row_dict)
            
            if display_data:
                st.table(display_data)
            else:
                st.info("💡 ဖြေဆိုထားသော ကျောင်းသား မှတ်တမ်း မရှိသေးပါ။")
                
        with tab2:
            st.subheader("➕ Inject New Question to Sheet2")        
