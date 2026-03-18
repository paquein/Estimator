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

# Load Checklist from CSV
@st.cache_data
def load_checklist_data():
    csv_path = 'Roadways_Contract_Checklist.csv'
    if os.path.exists(csv_path):
        # We skip the first row because of the custom header in your file
        df = pd.read_csv(csv_path, header=1)
        # Clean up: Fill missing phases and remove empty tasks
        df['Phase'] = df['Phase'].fillna("General/Other")
        df = df.dropna(subset=['Task'])
        return df
    return pd.DataFrame(columns=['Task', 'Phase'])

checklist_df = load_checklist_data()

# Initialize Session States
if 'estimate_data' not in st.session_state:
    st.session_state.estimate_data = []
if 'pm_checklist_state' not in st.session_state:
    # Create a state dictionary: {task_name: {"done": False, "na": False}}
    st.session_state.pm_checklist_state = {
        row['Task']: {"done": False, "na": False, "phase": row['Phase']} 
        for _, row in checklist_df.iterrows()
    }

# --- 2. DATA TREE MAP (For Manual Entry) ---
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

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("📋 Project Details")
    project_name = st.text_input("Project Name", value="Regina SIRP Package")
    contract_no = st.text_input("Contract #", value="2026-SIRP")
    report_date = st.date_input("Report Date", date.today())
    
    st.divider()
    st.write("**Personnel**")
    est_by = st.text_input("Estimated by", placeholder="Name")
    rev_by = st.text_input("Reviewed by", placeholder="Name")
    
    st.divider()
    st.title("Navigation")
    # Note: "PM Checklist" is now dynamically generated from the CSV
    page = st.radio("Go to:", ["Global Quick Estimate", "PM Checklist"] + list(LIST_MAP.keys()) + ["Estimation Result"])
    
    st.divider()
    if st.button("Clear All Data", type="secondary"):
        st.session_state.estimate_data = []
        for task in st.session_state.pm_checklist_state:
            st.session_state.pm_checklist_state[task]["done"] = False
            st.session_state.pm_checklist_state[task]["na"] = False
        st.rerun()

# --- 4. PDF GENERATION ENGINE ---
def create_pdf_report():
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Project Estimate & Checklist: {project_name}", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Contract: {contract_no} | Date: {report_date} | Prepared by: {est_by}", ln=True)
    pdf.ln(5)

    # 1. Checklist Section
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "PM Checklist Status", ln=True)
    pdf.set_font("Arial", size=9)
    
    # Group by phase in PDF
    current_phase = ""
    for task, data in st.session_state.pm_checklist_state.items():
        if data['phase'] != current_phase:
            current_phase = data['phase']
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, f"--- {current_phase} ---", ln=True)
            pdf.set_font("Arial", size=9)
            
        status = "N/A" if data["na"] else ("DONE" if data["done"] else "PENDING")
        pdf.cell(140, 7, f"  {task}", border='B')
        pdf.cell(40, 7, status, border='B', ln=True)
    
    # 2. Quantities Section
    if st.session_state.estimate_data:
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Quantity Take-off Summary", ln=True)
        pdf.set_font("Arial", size=9)
        pdf.cell(80, 8, "Item", border=1, fill=False)
        pdf.cell(40, 8, "Quantity", border=1)
        pdf.cell(40, 8, "Stationing", border=1, ln=True)
        
        for row in st.session_state.estimate_data:
            pdf.cell(80, 8, str(row['Item'][:45]), border=1)
            pdf.cell(40, 8, f"{row['Quantity']:.2f}", border=1)
            pdf.cell(40, 8, f"{row['From']}-{row['To']}", border=1, ln=True)
            
    return pdf.output(dest='S').encode('latin-1')

# --- 5. PAGE CONTENT: GLOBAL QUICK ESTIMATE ---
if page == "Global Quick Estimate":
    st.header("🚀 SIRP Estimates: Global Automated Tool")
    # (Existing logic kept for brevity...)
    with st.container(border=True):
        road_len = st.number_input("Road Length (m)", value=0.0)
        if st.button("Generate Take-off"):
            st.session_state.estimate_data.append({"Category": "Pavement", "Item": "Auto-Generated Roadway", "Quantity": road_len, "From": 0, "To": road_len})
            st.success("Added to summary!")

# --- 6. PAGE CONTENT: PM CHECKLIST (DYNAMICALLY GROUPED) ---
elif page == "PM Checklist":
    st.header("📋 Project Management Checklist")
    st.info("Grouped by project phases from your uploaded checklist.")

    phases = checklist_df['Phase'].unique()
    
    for phase in phases:
        with st.expander(f"Phase: {phase}", expanded=True):
            phase_tasks = checklist_df[checklist_df['Phase'] == phase]['Task'].tolist()
            
            for task in phase_tasks:
                c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                
                # Fetch state
                task_state = st.session_state.pm_checklist_state[task]
                is_na = task_state["na"]
                
                with c1:
                    # Visual grey-out logic
                    if is_na:
                        st.markdown(f"<span style='color: #9ea4ad; text-decoration: line-through;'>{task}</span>", unsafe_allow_stdio=True, unsafe_allow_html=True)
                    else:
                        st.write(f"**{task}**")
                
                with c2:
                    done = st.checkbox("Done", key=f"done_{task}", value=task_state["done"], disabled=is_na)
                    st.session_state.pm_checklist_state[task]["done"] = done
                
                with c3:
                    na = st.checkbox("N/A", key=f"na_{task}", value=is_na)
                    if na != is_na:
                        st.session_state.pm_checklist_state[task]["na"] = na
                        if na: st.session_state.pm_checklist_state[task]["done"] = False
                        st.rerun()

    st.divider()
    # Explicit Download Button
    pdf_bytes = create_pdf_report()
    st.download_button("📥 Export & Download PDF Report", data=pdf_bytes, file_name=f"{project_name}_Checklist.pdf", mime="application/pdf", type="primary")

# --- 7. MANUAL ENTRY TABS ---
elif page != "Estimation Result":
    st.header(f"Section: {page}")
    items = LIST_MAP.get(page, [])
    with st.container(border=True):
        item = st.selectbox("Select Work Item", items)
        qty = st.number_input("Quantity", value=0.0)
        if st.button("Add to Estimate"):
            st.session_state.estimate_data.append({"Category": page, "Item": item, "Quantity": qty, "From": 0, "To": 0})
            st.toast("Item Added!")

# --- 8. PAGE CONTENT: ESTIMATION RESULT ---
else:
    st.header(f"📊 Final Summary: {project_name}")
    
    if st.session_state.estimate_data or any(v['done'] for v in st.session_state.pm_checklist_state.values()):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Quantities")
            if st.session_state.estimate_data:
                st.dataframe(pd.DataFrame(st.session_state.estimate_data), use_container_width=True)
            else:
                st.write("No quantities added.")
                
        with col2:
            st.subheader("Checklist Progress")
            done_count = sum(1 for v in st.session_state.pm_checklist_state.values() if v['done'])
            total_tasks = len(st.session_state.pm_checklist_state)
            st.write(f"Items Completed: {done_count} / {total_tasks}")
            st.progress(done_count/total_tasks if total_tasks > 0 else 0)

        st.divider()
        # Large Export Button at bottom
        pdf_bytes = create_pdf_report()
        st.download_button(
            label="📄 GENERATE OFFICIAL PDF REPORT",
            data=pdf_bytes,
            file_name=f"{project_name}_Full_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    else:
        st.warning("No data found to export. Please complete the checklist or add estimate items.")
