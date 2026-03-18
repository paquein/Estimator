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
if 'pm_checklist_state' not in st.session_state:
    st.session_state.pm_checklist_state = {}
    for _, row in checklist_df.iterrows():
        uid = f"{row['p_clean']}_{row['t_clean']}_{row['index']}"
        st.session_state.pm_checklist_state[uid] = {
            "task": row['t_clean'], "done": False, "na": False, "phase": row['p_clean']
        }

# --- 2. LOGIC FUNCTIONS ---
def save_state():
    return json.dumps({
        "checklist": st.session_state.pm_checklist_state,
        "estimates": st.session_state.estimate_data
    })

def handle_check_change(uid, check_type):
    if check_type == "done":
        st.session_state.pm_checklist_state[uid]["done"] = st.session_state[f"d_{uid}"]
    if check_type == "na":
        is_na = st.session_state[f"n_{uid}"]
        st.session_state.pm_checklist_state[uid]["na"] = is_na
        if is_na:
            st.session_state.pm_checklist_state[uid]["done"] = False

# --- 3. FULL MAP LIST ---
LIST_MAP = {
    "Concrete Replacement": [
        "Install Standard Curb and Gutter", "Install Rolled Curb and Gutter", 
        "Install Reverse Curb and Gutter", "Install Median Curb", 
        "Install Sidewalk", "Install Pedestrian Ramp", 
        "Install Standard Monolithic Walk, Curb & Gutter",
        "Install Residential Driveway Crossing (130 mm)",
        "Slabjack Concrete Slab", "Concrete Extensions (Rebuild)"
    ],
    "Pavement": [
        "Asphalt Pavement Removal", "Cold Planing", "Asphalt Tack/Prime", 
        "Hot Mix Asphaltic Concrete (Fine Mix)", "Hot Mix Asphaltic Concrete (Coarse Mix)",
        "Excavation - Pavement Failure", "Granular Base Course"
    ],
    "Landscaping": [
        "Clearing and Grubbing", "Remove/Reinstate Existing Landscape Rock", 
        "Removal of Sidewalk Trip Hazard", "Topsoil and Seed", "Sod"
    ],
    "Water and Sewer": [
        "Adjust Existing Water Box", "Adjust Existing Sewer Box", 
        "New Hydrant Installation", "New Valve Installation"
    ]
}

# --- 4. PDF ENGINE ---
def create_pdf(p_name, c_no, r_date, e_by):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, f"Project Status: {p_name}", ln=True)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 8, f"Contract: {c_no} | Date: {r_date} | PM: {e_by}", ln=True)
    pdf.ln(5)
    
    current_phase = ""
    for uid, data in st.session_state.pm_checklist_state.items():
        if data['phase'] != current_phase:
            current_phase = data['phase']
            pdf.ln(2)
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(0, 8, f"SECTION: {current_phase}", ln=True)
            pdf.set_font("Helvetica", size=9)
        
        status = "N/A" if data["na"] else ("DONE" if data["done"] else "PENDING")
        pdf.cell(145, 7, f"  {data['task']}", border='B')
        pdf.cell(35, 7, status, border='B', ln=True, align='C')
    return bytes(pdf.output())

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("📋 Project Control")
    p_name = st.text_input("Project Name", value="11th Ave Revitalization")
    c_no = st.text_input("Contract #", value="2026-SIRP")
    r_date = st.date_input("Report Date", date.today())
    e_by = st.text_input("PM Name")
    
    st.divider()
    pdf_data = create_pdf(p_name, c_no, str(r_date), e_by)
    st.download_button("📥 EXPORT PDF REPORT", data=pdf_data, file_name=f"{p_name}_Report.pdf", 
                       mime="application/pdf", type="primary", use_container_width=True)
    
    st.divider()
    page = st.radio("Menu", ["Global Quick Estimate", "PM Checklist"] + list(LIST_MAP.keys()) + ["Estimation Result"])

# --- 6. PAGES ---
if page == "PM Checklist":
    # --- TOP RIGHT CONTROLS ---
    head_col, save_col, load_col = st.columns([0.5, 0.25, 0.25])
    
    with head_col:
        st.header("📋 Project Checklist")
        
    with save_col:
        st.download_button("💾 Save Progress", data=save_state(), file_name=f"{p_name}_save.json", use_container_width=True)
        
    with load_col:
        up_file = st.file_uploader("📂 Load Progress", type="json", label_visibility="collapsed")
        if up_file:
            data = json.load(up_file)
            st.session_state.pm_checklist_state = data.get("checklist", {})
            st.session_state.estimate_data = data.get("estimates", [])
            st.rerun() # Forces immediate refresh to show loaded data

    st.divider()
    
    phases = checklist_df['p_clean'].unique()
    for phase in phases:
        with st.expander(f"Phase: {phase}", expanded=True):
            p_uids = [u for u, v in st.session_state.pm_checklist_state.items() if v['phase'] == phase]
            for uid in p_uids:
                data = st.session_state.pm_checklist_state[uid]
                c1, c2, c3, c4 = st.columns([0.6, 0.15, 0.15, 0.1])
                with c1:
                    style = "color: #adb5bd; text-decoration: line-through;" if data["na"] else "font-weight: bold;"
                    st.markdown(f"<p style='{style} margin:0;'>{data['task']}</p>", unsafe_allow_html=True)
                with c2:
                    st.checkbox("Done", key=f"d_{uid}", value=data["done"], disabled=data["na"], on_change=handle_check_change, args=(uid, "done"))
                with c3:
                    st.checkbox("N/A", key=f"n_{uid}", value=data["na"], on_change=handle_check_change, args=(uid, "na"))

elif page == "Global Quick Estimate":
    st.header("🚀 Global Automated Tool")
    l = st.number_input("Road Length (m)", 0.0)
    w = st.number_input("Width (m)", 0.0)
    if st.button("Add to Summary"):
        st.session_state.estimate_data.append({"Category": "Pavement", "Item": "Road Paving", "Quantity": l*w})
        st.toast("Added!")

elif page == "Estimation Result":
    st.header("📊 Final Summary")
    if st.session_state.estimate_data:
        st.dataframe(pd.DataFrame(st.session_state.estimate_data), use_container_width=True)

else:
    st.header(f"Section: {page}")
    items = LIST_MAP.get(page, [])
    it = st.selectbox("Select Item", items)
    q = st.number_input("Quantity", 0.0)
    if st.button("Add Item"):
        st.session_state.estimate_data.append({"Category": page, "Item": it, "Quantity": q})
        st.toast(f"Added {it}")
