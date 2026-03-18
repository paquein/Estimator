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
            if "Task" in row.values:
                header_idx = i
                break
        df = pd.read_csv(csv_path, header=header_idx)
        df = df.dropna(subset=['Task'])
        df['Phase'] = df['Phase'].fillna("General/Other").str.strip()
        df['Task'] = df['Task'].str.strip()
        return df.reset_index()
    return pd.DataFrame(columns=['Task', 'Phase', 'index'])

checklist_df = load_checklist_data()

# Initialize State
if 'pm_checklist_state' not in st.session_state:
    st.session_state.pm_checklist_state = {}
    for _, row in checklist_df.iterrows():
        # Create a truly unique ID for every single row
        uid = f"{row['Phase']}_{row['Task']}_{row['index']}"
        st.session_state.pm_checklist_state[uid] = {
            "task": row['Task'], 
            "done": False, 
            "na": False, 
            "phase": row['Phase']
        }

# --- 2. CALLBACKS ---
def handle_check_change(uid, type):
    if type == "done":
        st.session_state.pm_checklist_state[uid]["done"] = st.session_state[f"d_{uid}"]
    if type == "na":
        is_na = st.session_state[f"n_{uid}"]
        st.session_state.pm_checklist_state[uid]["na"] = is_na
        if is_na:
            st.session_state.pm_checklist_state[uid]["done"] = False

# --- 3. PDF ENGINE ---
def create_pdf(proj_name, cont_no, date_str, est_by):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Project Report: {proj_name}", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"Contract: {cont_no} | Date: {date_str} | Est: {est_by}", ln=True)
    pdf.ln(5)
    
    current_phase = ""
    for uid, data in st.session_state.pm_checklist_state.items():
        if data['phase'] != current_phase:
            current_phase = data['phase']
            pdf.ln(3)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, f"SECTION: {current_phase}", ln=True, fill=False)
            pdf.set_font("Arial", size=9)
        
        status = "N/A" if data["na"] else ("DONE" if data["done"] else "PENDING")
        pdf.cell(145, 7, f"  {data['task']}", border='B')
        pdf.cell(35, 7, status, border='B', ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("📋 Project Details")
    p_name = st.text_input("Project Name", value="Regina SIRP Package")
    c_no = st.text_input("Contract #", value="2026-SIRP")
    r_date = st.date_input("Report Date", date.today())
    e_by = st.text_input("Estimated by")
    
    st.divider()
    page = st.radio("Navigation", ["PM Checklist", "Estimation Result"])

# --- 5. PAGE: PM CHECKLIST ---
if page == "PM Checklist":
    st.header("📋 Project Management Checklist")
    
    phases = checklist_df['Phase'].unique()
    
    for phase in phases:
        with st.expander(f"Phase: {phase}", expanded=True):
            # Filter the unique IDs belonging to this phase
            phase_uids = [uid for uid, val in st.session_state.pm_checklist_state.items() if val['phase'] == phase]
            
            for uid in phase_uids:
                data = st.session_state.pm_checklist_state[uid]
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                
                with col1:
                    if data["na"]:
                        st.markdown(f"<p style='color: #adb5bd; text-decoration: line-through; margin:0;'>{data['task']}</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='font-weight: bold; margin:0;'>{data['task']}</p>", unsafe_allow_html=True)
                
                with col2:
                    st.checkbox("Done", key=f"d_{uid}", 
                                value=data["done"], 
                                disabled=data["na"],
                                on_change=handle_check_change, args=(uid, "done"))
                
                with col3:
                    st.checkbox("N/A", key=f"n_{uid}", 
                                value=data["na"],
                                on_change=handle_check_change, args=(uid, "na"))

    st.divider()
    btn_pdf = create_pdf(p_name, c_no, str(r_date), e_by)
    st.download_button("📥 Download Final PDF Report", data=btn_pdf, file_name=f"{p_name}_Report.pdf", mime="application/pdf", type="primary")

else:
    st.header("📊 Results Summary")
    st.write("Review your checklist status and download the final report.")
    btn_pdf = create_pdf(p_name, c_no, str(r_date), e_by)
    st.download_button("📄 Generate Official PDF", data=btn_pdf, file_name=f"{p_name}_Summary.pdf", type="primary")
