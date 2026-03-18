import streamlit as st
import pandas as pd
from datetime import date
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

# --- 1. DATA LOADING & INITIALIZATION ---
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
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(subset=['Task'])
        df['Phase'] = df['Phase'].fillna("General/Other").str.strip()
        df['Task'] = df['Task'].str.strip()
        return df.reset_index()
    return pd.DataFrame(columns=['Task', 'Phase', 'index'])

checklist_df = load_checklist_data()

# Initialize Session States
if 'estimate_data' not in st.session_state:
    st.session_state.estimate_data = []

if 'pm_checklist_state' not in st.session_state:
    st.session_state.pm_checklist_state = {}
    for _, row in checklist_df.iterrows():
        uid = f"{row['Phase']}_{row['Task']}_{row['index']}"
        st.session_state.pm_checklist_state[uid] = {
            "task": row['Task'], 
            "done": False, 
            "na": False, 
            "phase": row['Phase']
        }

# --- 2. SAVE/LOAD LOGIC ---
def save_state():
    """Converts the current checklist and estimate into a JSON string."""
    full_data = {
        "checklist": st.session_state.pm_checklist_state,
        "estimates": st.session_state.estimate_data
    }
    return json.dumps(full_data)

def load_state(uploaded_file):
    """Parses an uploaded JSON file and overwrites the current session state."""
    try:
        data = json.load(uploaded_file)
        if "checklist" in data:
            st.session_state.pm_checklist_state = data["checklist"]
        if "estimates" in data:
            st.session_state.estimate_data = data["estimates"]
        st.success("✅ Progress Loaded Successfully!")
    except Exception as e:
        st.error(f"Error loading file: {e}")

# --- 3. CALLBACKS ---
def handle_check_change(uid, type):
    if type == "done":
        st.session_state.pm_checklist_state[uid]["done"] = st.session_state[f"d_{uid}"]
    if type == "na":
        is_na = st.session_state[f"n_{uid}"]
        st.session_state.pm_checklist_state[uid]["na"] = is_na
        if is_na:
            st.session_state.pm_checklist_state[uid]["done"] = False

# --- 4. DATA TREE MAP ---
LIST_MAP = {
    "Concrete Replacement": [
        "Install Standard Curb and Gutter", "Install Rolled Curb and Gutter", 
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

# --- 5. PDF ENGINE ---
def create_pdf(p_name, c_no, r_date, e_by):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Project Report: {p_name}", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"Contract: {c_no} | Date: {r_date} | Est: {e_by}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "PM Checklist Status", ln=True)
    current_phase = ""
    for uid, data in st.session_state.pm_checklist_state.items():
        if data['phase'] != current_phase:
            current_phase = data['phase']
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, f"SECTION: {current_phase}", ln=True)
        pdf.set_font("Arial", size=9)
        status = "N/A" if data["na"] else ("DONE" if data["done"] else "PENDING")
        pdf.cell(145, 7, f"  {data['task']}", border='B')
        pdf.cell(35, 7, status, border='B', ln=True, align='C')
    
    if st.session_state.estimate_data:
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Quantity Summary", ln=True)
        for row in st.session_state.estimate_data:
            pdf.set_font("Arial", size=9)
            pdf.cell(100, 7, row.get('Item', 'Item'), border=1)
            pdf.cell(40, 7, f"{row.get('Quantity', 0):.2f}", border=1, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("📋 Project Details")
    p_name = st.text_input("Project Name", value="Regina SIRP Package")
    c_no = st.text_input("Contract #", value="2026-SIRP")
    r_date = st.date_input("Report Date", date.today())
    e_by = st.text_input("Estimated by")
    
    st.divider()
    st.write("### 💾 Save / Load Progress")
    # Save Button
    st.download_button(
        label="💾 Save Progress to File",
        data=save_state(),
        file_name=f"{p_name}_progress.json",
        mime="application/json",
        use_container_width=True
    )
    
    # Load File Uploader
    uploaded_file = st.file_uploader("📂 Load Progress from File", type="json")
    if uploaded_file is not None:
        if st.button("Apply Loaded Progress", use_container_width=True):
            load_state(uploaded_file)
    
    st.divider()
    # Progress Bar
    done_count = sum(1 for v in st.session_state.pm_checklist_state.values() if v['done'])
    total_tasks = len(st.session_state.pm_checklist_state)
    progress = done_count / total_tasks if total_tasks > 0 else 0
    st.write(f"Checklist Progress: {int(progress * 100)}%")
    st.progress(progress)
    
    # PDF Button
    st.download_button(
        label="📥 DOWNLOAD FINAL PDF", 
        data=create_pdf(p_name, c_no, str(r_date), e_by), 
        file_name=f"{p_name}_Report.pdf", 
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )
    
    st.divider()
    page = st.radio("Navigation", ["Global Quick Estimate", "PM Checklist"] + list(LIST_MAP.keys()) + ["Estimation Result"])

# --- 7. PAGES ---

if page == "PM Checklist":
    st.header("📋 Project Management Checklist")
    phases = checklist_df['Phase'].unique()
    for phase in phases:
        with st.expander(f"Phase: {phase}", expanded=True):
            p_uids = [u for u, v in st.session_state.pm_checklist_state.items() if v['phase'] == phase]
            for uid in p_uids:
                data = st.session_state.pm_checklist_state[uid]
                c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                with c1:
                    if data["na"]:
                        st.markdown(f"<p style='color: #adb5bd; text-decoration: line-through; margin:0;'>{data['task']}</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='font-weight: bold; margin:0;'>{data['task']}</p>", unsafe_allow_html=True)
                with c2:
                    st.checkbox("Done", key=f"d_{uid}", value=data["done"], disabled=data["na"], on_change=handle_check_change, args=(uid, "done"))
                with c3:
                    st.checkbox("N/A", key=f"n_{uid}", value=data["na"], on_change=handle_check_change, args=(uid, "na"))

elif page == "Global Quick Estimate":
    st.header("🚀 SIRP Estimates: Global Automated Tool")
    with st.container(border=True):
        col_left, col_right = st.columns(2)
        with col_left:
            road_len = st.number_input("Road Length (m)", value=0.0)
            road_width = st.number_input("Road Width (m)", value=0.0)
        with col_right:
            mill_depth = st.number_input("Mill depth (mm)", value=50)

    if st.button("⚡ Generate Automated Take-off", type="primary"):
        st.session_state.estimate_data.append({
            "Category": "Pavement", "Item": f"Cold Planing ({mill_depth}mm)", 
            "Quantity": road_len * road_width, "From": 0, "To": road_len, "Notes": "Auto"
        })
        st.toast("Added to summary!")

elif page == "Estimation Result":
    st.header("📊 Final Summary")
    if st.session_state.estimate_data:
        st.dataframe(pd.DataFrame(st.session_state.estimate_data), use_container_width=True)
    else:
        st.info("No estimate items recorded.")

else: # Manual Entry Pages (Concrete, Pavement, etc.)
    st.header(f"Section: {page}")
    items = LIST_MAP.get(page, [])
    with st.container(border=True):
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            item = st.selectbox("Item Selection", items)
            f_val = st.number_input("From Station", value=0.0)
            t_val = st.number_input("To Station", value=0.0)
        with col2:
            notes = st.text_area("Notes")
    if st.button("➕ Add Item"):
        # Assuming standard width of 1.5m for auto-calc if not specified
        st.session_state.estimate_data.append({
            "Category": page, "Item": item, "Quantity": abs(t_val-f_val)*1.5, 
            "From": f_val, "To": t_val, "Notes": notes
        })
        st.toast(f"Added {item}")
