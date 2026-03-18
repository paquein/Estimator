import streamlit as st
import pandas as pd
from datetime import date
from fpdf import FPDF

# --- 0. PASSWORD PROTECTION ---
def check_password():
    """Returns True if the user had the correct password."""
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

# --- 1. INITIALIZATION ---
st.set_page_config(page_title="Regina Master Estimator", layout="wide")

if 'estimate_data' not in st.session_state:
    st.session_state.estimate_data = []
if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None
if 'pm_checklist' not in st.session_state:
    # Initialize PM Checklist items
    checklist_items = ["Detailed design done", "Designed Checked", "Contract documents done"]
    st.session_state.pm_checklist = {item: {"done": False, "na": False} for item in checklist_items}

# --- 2. DATA TREE MAP ---
LIST_MAP = {
    "PM Checklist": ["Detailed design done", "Designed Checked", "Contract documents done"],
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
    page = st.radio("Go to:", ["Global Quick Estimate"] + list(LIST_MAP.keys()) + ["Estimation Result"])
    
    st.divider()
    if st.button("Clear All Data", type="secondary"):
        st.session_state.estimate_data = []
        st.session_state.editing_index = None
        for item in st.session_state.pm_checklist:
            st.session_state.pm_checklist[item] = {"done": False, "na": False}
        st.rerun()

# --- 4. GLOBAL QUICK ESTIMATE ---
if page == "Global Quick Estimate":
    st.header("🚀 SIRP Estimates: Global Automated Tool")
    with st.container(border=True):
        col_left, col_right = st.columns(2)
        with col_left:
            road_len = st.number_input("Road Length (m)", value=0.0, step=10.0)
            road_width = st.number_input("Road Width (m)", value=0.0, step=0.1)
            con_element = st.selectbox("Concrete Element", ["Separate Walk/Curb", "Monolithic Walk/Curb", "Curb Only"])
            walk_width = st.number_input("Walk Width (m)", value=1.20, step=0.05)
        with col_right:
            replace_pct = st.number_input("Replacement %", value=100)
            fail_pct = st.number_input("Failure Repairs %", value=10)
            mill_depth = st.number_input("Mill (mm)", value=50)

    if st.button("⚡ Generate Automated Take-off", type="primary", use_container_width=True):
        new_items = []
        p_area = road_len * road_width
        new_items.append({"Category": "Pavement", "Item": f"Cold Planing ({mill_depth}mm)", "Quantity": p_area, "From": 0.0, "To": road_len, "Width": road_width, "Notes": "Global Auto-Calc"})
        st.session_state.estimate_data = new_items
        st.success("Global Estimate Generated!")

# --- 5. PM CHECKLIST TAB ---
elif page == "PM Checklist":
    st.header("📋 Project Management Checklist")
    st.write("Mark items as Done or Not Applicable (N/A).")
    
    with st.container(border=True):
        for item in LIST_MAP["PM Checklist"]:
            c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
            
            is_na = st.session_state.pm_checklist[item]["na"]
            label = f":grey[{item}]" if is_na else f"**{item}**"
            
            with c1:
                st.write(label)
            with c2:
                # Checkbox for "Done" - disabled if N/A is true
                done_val = st.checkbox("Done", key=f"d_{item}", value=st.session_state.pm_checklist[item]["done"], disabled=is_na)
                st.session_state.pm_checklist[item]["done"] = done_val
            with c3:
                # Checkbox for "N/A"
                na_val = st.checkbox("N/A", key=f"n_{item}", value=st.session_state.pm_checklist[item]["na"])
                if na_val != st.session_state.pm_checklist[item]["na"]:
                    st.session_state.pm_checklist[item]["na"] = na_val
                    if na_val: st.session_state.pm_checklist[item]["done"] = False
                    st.rerun()

# --- 6. MANUAL ENTRY TABS ---
elif page != "Estimation Result":
    st.header(f"{page}")
    items = LIST_MAP.get(page, [])
    with st.container(border=True):
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            item = st.selectbox("Item Selection", items)
            f_val = st.number_input("From Station", value=0.0)
            t_val = st.number_input("To Station", value=0.0)
            w_val = st.number_input("Width (m)", value=1.5)
        with col2:
            notes_val = st.text_area("Notes", value="")
    
    if st.button("➕ Add Item"):
        st.session_state.estimate_data.append({
            "Category": page, "Item": item, "Quantity": abs(t_val-f_val)*w_val, 
            "From": f_val, "To": t_val, "Width": w_val, "Notes": notes_val
        })
        st.toast(f"Added {item}")

# --- 7. RESULTS & PDF EXPORT ---
else:
    st.header(f"📊 Summary: {project_name}")
    
    # PDF Generator Function
    def create_pdf_report():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Estimate Report: {project_name}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 10, f"Contract: {contract_no} | Date: {report_date} | Est by: {est_by}", ln=True)
        pdf.ln(5)

        # Add Checklist Section
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "PM Checklist Status", ln=True)
        pdf.set_font("Arial", size=10)
        for item, status in st.session_state.pm_checklist.items():
            stat_text = "N/A" if status["na"] else ("COMPLETED" if status["done"] else "PENDING")
            pdf.cell(100, 8, f"{item}:", border='B')
            pdf.cell(40, 8, stat_text, border='B', ln=True)
        
        pdf.ln(10)
        # Add Quantity Table
        if st.session_state.estimate_data:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Quantity Take-off", ln=True)
            pdf.set_font("Arial", size=9)
            pdf.cell(60, 8, "Item", border=1)
            pdf.cell(30, 8, "Quantity", border=1)
            pdf.cell(30, 8, "Stationing", border=1, ln=True)
            
            for row in st.session_state.estimate_data:
                pdf.cell(60, 8, str(row['Item'][:30]), border=1)
                pdf.cell(30, 8, f"{row['Quantity']:.2f}", border=1)
                pdf.cell(30, 8, f"{row['From']}-{row['To']}", border=1, ln=True)
        
        return pdf.output(dest='S').encode('latin-1')

    # Display in App
    if st.session_state.estimate_data:
        df = pd.DataFrame(st.session_state.estimate_data)
        st.dataframe(df, use_container_width=True)
        
        pdf_data = create_pdf_report()
        st.download_button(label="📥 Download PDF Estimate", data=pdf_data, 
                           file_name=f"{project_name}_Estimate.pdf", mime="application/pdf")
    else:
        st.warning("No quantities recorded yet.")
