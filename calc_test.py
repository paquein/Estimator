import streamlit as st
import pandas as pd
from datetime import date, datetime
from fpdf import FPDF
import os
import json

# --- 0. PASSWORD PROTECTION ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "franistheman":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Please enter the password", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", False)

if not check_password():
    st.stop()

# --- 1. DATA LOADING ---
st.set_page_config(page_title="Regina Master Estimator", layout="wide")

@st.cache_data
def load_checklist_data():
    csv_path = 'Roadways_Contract_Checklist.csv'
    if os.path.exists(csv_path):
        raw_df = pd.read_csv(csv_path, header=None)
        header_idx = 0
        for i, row in raw_df.iterrows():
            if any("task" in str(val).lower() for val in row.values):
                header_idx = i
                break
        df = pd.read_csv(csv_path, header=header_idx)
        df.columns = [str(c).lower().strip() for c in df.columns]
        df = df.dropna(subset=['task'])
        p_col = 'phase' if 'phase' in df.columns else df.columns[1]
        df['p_clean'] = df[p_col].fillna("General").str.strip()
        df['t_clean'] = df['task'].str.strip()
        return df.reset_index()
    return pd.DataFrame(columns=['t_clean', 'p_clean', 'index'])

checklist_df = load_checklist_data()

# Initialize Session States
if 'estimate_data' not in st.session_state:
    st.session_state.estimate_data = []
if 'last_save_time' not in st.session_state:
    st.session_state.last_save_time = "Never"
if 'pm_checklist_state' not in st.session_state:
    st.session_state.pm_checklist_state = {}
    for _, row in checklist_df.iterrows():
        uid = f"{row['p_clean']}_{row['t_clean']}_{row['index']}"
        st.session_state.pm_checklist_state[uid] = {
            "task": row['t_clean'], "done": False, "na": False, "phase": row['p_clean']
        }

# --- 2. SAVE/LOAD LOGIC ---
def save_state():
    st.session_state.last_save_time = datetime.now().strftime("%H:%M:%S")
    return json.dumps({
        "checklist": st.session_state.pm_checklist_state,
        "estimates": st.session_state.estimate_data
    })

def load_state(uploaded_file):
    try:
        data = json.load(uploaded_file)
        st.session_state.pm_checklist_state = data.get("checklist", {})
        st.session_state.estimate_data = data.get("estimates", [])
        st.success("✅ Progress Loaded!")
        st.rerun()
    except Exception as e:
        st.error(f"Load Error: {e}")

# --- 3. CALLBACKS ---
def handle_check_change(uid, check_type):
    if check_type == "done":
        st.session_state.pm_checklist_state[uid]["done"] = st.session_state[f"d_{uid}"]
    if check_type == "na":
        is_na = st.session_state[f"n_{uid}"]
        st.session_state.pm_checklist_state[uid]["na"] = is_na
        if is_na:
            st.session_state.pm_checklist_state[uid]["done"] = False

# --- 4. FULL MAP LIST (RE-RESTORED) ---
LIST_MAP = {
    "Concrete Replacement": [
        "Install Standard Curb and Gutter", "Install Rolled Curb and Gutter", 
        "Install Reverse Curb and Gutter", "Install Median Curb", 
        "Install Sidewalk", "Install Pedestrian Ramp", 
        "Install Standard Monolithic Walk, Curb & Gutter",
        "Install Residential Driveway Crossing (130 mm)",
