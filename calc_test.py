import streamlit as st
import pandas as pd
from datetime import date
from fpdf import FPDF
import os

# --- 0. PASSWORD PROTECTION ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "franistheman":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Please enter the password to access the Estimator", 
                      type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Please enter the password to access the Estimator", 
                      type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    return True

if not check_password():
    st.stop()

# --- 1. INITIALIZATION & DATA LOADING ---
st.set_page_config(page_title="Regina Master Estimator", layout="wide")

@st.cache_data
def load_checklist_data():
    csv_path = 'Roadways_Contract_Checklist.csv'
    if os.path.exists(csv_path):
        # Find the row that actually starts with "Task"
        raw_df = pd.read_csv(csv_path, header=None)
        header_idx = 0
        for i, row in raw_df.iterrows():
            if "Task" in row.values:
                header_idx = i
                break
        df = pd.read_csv(csv_path, header=header_idx)
        df = df.dropna(subset=['Task'])
        df['Phase'] = df['Phase'].fillna("General/Other")
        # Add a unique ID based on the index to prevent duplicate key errors
        df = df.reset_index() 
        return df
    return pd.DataFrame(columns=['Task', 'Phase', 'index'])

checklist_df = load_checklist_data()

# Initialize Session States
if 'estimate_data' not in st.session_state:
    st.session_state.estimate_data = []

if 'pm_checklist_state' not in st.session_state:
    # Key state by the row index to handle duplicates perfectly
    st.session_state.pm_checklist_state = {
        row['index']: {"task": row['Task'], "done": False, "na": False, "phase": row['Phase']} 
        for _, row in checklist_df.iterrows()
    }

# --- 2. CALLBACK FUNCTIONS (Prevents the crash) ---
def update_done(idx):
    key = f"done_check_{idx}"
    st.session_state.pm_checklist_state[idx]["done"] = st.session_state[key]

def update_na(idx):
    key = f"na_check_{idx}"
    is_na = st.session_state[key]
    st.session_state.pm_checklist_state[idx]["na"] = is_na
    # If N/A is checked, force "Done" to be false
    if is_na:
        st.session_state.pm_checklist_state[idx]["done"] = False

# --- 3. DATA TREE MAP (For Manual Entry) ---
LIST_MAP = {
    "Concrete Replacement": ["Install Standard Curb", "Install Sidewalk", "Install Pedestrian Ramp"],
    "Pavement": ["Cold Planing", "Hot Mix Asphalt", "Granular Base"],
    "Landscaping": ["Topsoil and Seed", "Sod"],
    "Water and Sewer": ["Adjust Water Box", "New Hydrant"]
}

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("📋 Project Details")
    project_name = st.text_input("Project Name", value="Regina SIRP Package")
    contract_no = st.text_input("Contract #", value="2026-SIRP")
    report_date = st.date_input("Report Date", date.today())
    est_by = st.text_input("Estimated by", placeholder="Name")
    
    st.divider()
    page = st.radio("Navigation", ["PM Checklist"] + list(LIST_MAP.keys()) + ["Estimation Result"])
    
    if st.button("Clear All Data"):
        st.session_state.estimate_data = []
        for idx in st.session_state.pm_checklist_state:
            st.session_state.pm_checklist_state[idx]["done"] = False
            st.session_state.pm_checklist_state[idx]["na"] = False
        st.rerun()

# --- 5. PDF GENERATION ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Project Report: {project_name}", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"Contract: {contract_no} | Date: {report_date}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "PM Checklist Status", ln=True)
    pdf.set_font("Arial", size=9)
    
    current_phase = ""
    for idx, data in st.session_state.pm_checklist_state.items():
        if data['phase'] != current_phase:
            current_phase = data['phase']
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, f"--- {current_phase} ---", ln=True)
            pdf.set_font("Arial", size=9)
        
        status = "N/A" if data["na"] else ("DONE" if data["done"] else "PENDING")
        pdf.cell(140, 7, f"  {data['task']}", border='B')
        pdf.cell(40, 7, status, border='B', ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 6. PAGE: PM CHECKLIST ---
if page == "PM Checklist":
    st.header("📋 Project Management Checklist")
    
    phases = checklist_df['Phase'].unique()
    for phase in phases:
        with st.expander(f"Phase: {phase}", expanded=True):
            # Get tasks for this phase
            phase_rows = checklist_df[checklist_df['Phase'] == phase]
            
            for _, row in phase_rows.iterrows():
                idx = row['index']
                task_name = row['Task']
                state = st.session_state.pm_checklist_state[idx]
                
                c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                
                with c1:
                    if state["na"]:
                        st.markdown(f"<span style='color: #adb5bd; text-decoration: line-through;'>{task_name}</span>", unsafe_allow_html=True)
                    else:
                        st.write(f"**{task_name}**")
                
                with c2:
                    st.checkbox("Done", key=f"done_check_{idx}", 
                                value=state["done"], 
                                disabled=state["na"],
                                on_change=update_done, args=(idx,))
                
                with c3
