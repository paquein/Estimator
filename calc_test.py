import streamlit as st
import sqlite3
import pandas as pd

def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        # Change 'regina2026' to whatever password you want!
        if st.session_state["password"] == "franistheman":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input("Please enter the password to access the Estimator", 
                      type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Please enter the password to access the Estimator", 
                      type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if not check_password():
    st.stop()  # Do not run the rest of the app if not logged in

#############################################################################################################################################################################################################
import streamlit as st
import pandas as pd
from datetime import date

# --- 1. INITIALIZATION ---
st.set_page_config(page_title="Regina Master Estimator", layout="wide")

if 'estimate_data' not in st.session_state:
    st.session_state.estimate_data = []
if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None

# --- 2. DATA TREE MAP ---
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
    page = st.radio("Go to:", ["Global Quick Estimate"] + list(LIST_MAP.keys()) + ["Estimation Result"])
    
    st.divider()
    if st.button("Clear All Data", type="secondary"):
        st.session_state.estimate_data = []
        st.session_state.editing_index = None
        st.rerun()

# --- 4. GLOBAL QUICK ESTIMATE (SIRPESTI ENGINE) ---
if page == "Global Quick Estimate":
    st.header("🚀 SIRP Estimates: Global Automated Tool")
    
    with st.container(border=True):
        col_left, col_right = st.columns(2)
        
        with col_left:
            road_len = st.number_input("Road Length (m)", value=0.0, step=10.0)
            road_width = st.number_input("Road Width (include all lanes) (m)", value=0.0, step=0.1)
            con_median = st.selectbox("Concrete Median?", ["No", "Yes"])
            med_width = st.number_input("Median Width (m)", value=0.0, step=0.1)
            blvd_area = st.selectbox("Boulevard Area?", ["No", "Yes"])
            blvd_width = st.number_input("Boulevard Width (m)", value=0.0, step=0.1)
            con_element = st.selectbox("Concrete Element", ["Separate Walk/Curb", "Monolithic Walk/Curb", "Curb Only"])
            walk_width = st.number_input("Walk Width (m)", value=1.20, step=0.05)
            
        with col_right:
            replace_pct = st.number_input("Replacement %", value=100)
            fail_pct = st.number_input("Failure Repairs %", value=10)
            
            st.write("**Mill / Pave (mm)**")
            m_col1, m_col2 = st.columns(2)
            with m_col1: mill_depth = st.number_input("Mill", value=50, label_visibility="collapsed")
            with m_col2: pave_depth = st.number_input("Pave", value=60, label_visibility="collapsed")
            
            ext_utils = st.selectbox("External Utilities", ["None", "Standard", "Heavy"])
            road_type = st.selectbox("Road Type", ["Residential", "Collector", "Arterial"])

    if st.button("⚡ Generate Automated Take-off", type="primary", use_container_width=True):
        new_items = []
        f_rep = replace_pct / 100.0
        f_fail = fail_pct / 100.0

        # Pavement Calc
        p_area = road_len * road_width
        new_items.append({"Category": "Pavement", "Item": f"Cold Planing ({mill_depth}mm)", "Quantity": p_area, "From": 0.0, "To": road_len, "Width": road_width, "Notes": "Global Auto-Calc"})
        new_items.append({"Category": "Pavement", "Item": "Excavation - Pavement Failure", "Quantity": p_area * f_fail, "From": 0.0, "To": road_len, "Width": road_width * f_fail, "Notes": f"Based on {fail_pct}% failure"})

        # Concrete Calc
        if con_element != "Curb Only":
            item_name = "Install Sidewalk" if con_element == "Separate Walk/Curb" else "Install Standard Monolithic Walk, Curb & Gutter"
            new_items.append({"Category": "Concrete Replacement", "Item": item_name, "Quantity": road_len * walk_width * f_rep, "From": 0.0, "To": road_len, "Width": walk_width, "Notes": f"Global {replace_pct}% Replacement"})

        st.session_state.estimate_data = new_items
        st.success("Global Estimate Generated! Navigate to 'Estimation Result' to review.")

# --- 5. MANUAL ENTRY TABS ---
elif page != "Estimation Result":
    st.header(f"{page}")
    edit_idx = st.session_state.editing_index
    is_editing = (edit_idx is not None and edit_idx < len(st.session_state.estimate_data) and st.session_state.estimate_data[edit_idx]["Category"] == page)
    cur = st.session_state.estimate_data[edit_idx] if is_editing else {}

    with st.container(border=True):
        col1, col2, col3 = st.columns([0.3, 0.2, 0.5])
        with col1:
            items = LIST_MAP.get(page, [])
            item = st.selectbox("Item Selection", items, index=items.index(cur["Item"]) if is_editing and cur["Item"] in items else 0)
            f_val = st.number_input("From Station", value=float(cur.get("From", 0.0)))
            t_val = st.number_input("To Station", value=float(cur.get("To", 0.0)))
            w_val = st.number_input("Width (m)", value=float(cur.get("Width", 1.5)))
        with col2:
            st.write("**Options**")
            base_val = st.checkbox("Base", value=cur.get("Base", False))
            sod_val = st.checkbox("Sod", value=cur.get("Sod", False))
        with col3:
            notes_val = st.text_area("Notes", value=cur.get("Notes", ""), height=200)

    if is_editing:
        if st.button("✅ Update Item"):
            st.session_state.estimate_data[edit_idx] = {"Category": page, "Item": item, "Quantity": abs(t_val-f_val)*w_val, "From": f_val, "To": t_val, "Width": w_val, "Notes": notes_val, "Base": base_val, "Sod": sod_val}
            st.session_state.editing_index = None
            st.rerun()
    else:
        if st.button("➕ Add Item"):
            st.session_state.estimate_data.append({"Category": page, "Item": item, "Quantity": abs(t_val-f_val)*w_val, "From": f_val, "To": t_val, "Width": w_val, "Notes": notes_val, "Base": base_val, "Sod": sod_val})
            st.rerun()

# --- 6. RESULTS ---
else:
    st.header(f"📊 Summary: {project_name}")
    st.write(f"**Contract:** {contract_no} | **Est. By:** {est_by} | **Date:** {report_date}")
    if st.session_state.estimate_data:
        df = pd.DataFrame(st.session_state.estimate_data)
        st.table(df.groupby(['Category', 'Item'])['Quantity'].sum().reset_index())
        st.divider()
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("No data recorded.")


# ==========================================
# 📋 STANDALONE MODULE: IMPORTS + PDF + CHECKLIST
# ==========================================
import streamlit as st
import pandas as pd
import json
from fpdf import FPDF
from datetime import date

def create_pdf_report(p_name, c_no, r_date, e_by, checklist_state):
    """Generates the PDF bytes from the current checklist state."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, f"Project Status: {p_name}", ln=True)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 8, f"Contract: {c_no} | Date: {r_date} | PM: {e_by}", ln=True)
    pdf.ln(5)
    
    current_phase = ""
    for uid, data in checklist_state.items():
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

def render_pm_checklist_page(p_name, c_no, r_date, e_by, checklist_df):
    """Main Checklist UI with Stacked Controls."""
    
    # 1. Initialize State if missing
    if 'pm_checklist_state' not in st.session_state:
        st.session_state.pm_checklist_state = {}
        for _, row in checklist_df.iterrows():
            uid = f"{row['p_clean']}_{row['t_clean']}_{row['index']}"
            st.session_state.pm_checklist_state[uid] = {
                "task": row['t_clean'], "done": False, "na": False, "phase": row['p_clean']
            }

    # 2. Layout: Main Checklist vs Button Stack
    main_col, btn_col = st.columns([0.75, 0.25])
    
    with main_col:
        st.header("📋 Project Checklist")
        
    with btn_col:
        # --- BUTTON 1: SAVE ---
        save_json = json.dumps({
            "checklist": st.session_state.pm_checklist_state,
            "estimates": st.session_state.get('estimate_data', [])
        })
        st.download_button("💾 Save Progress", data=save_json, 
                           file_name=f"{p_name}_save.json", use_container_width=True)
        
        # --- BUTTON 2: LOAD (Caption + Uploader) ---
        st.write('<p style="font-size:14px; margin-bottom:0; font-weight:bold;">📂 Load Progress</p>', unsafe_allow_html=True)
        up_file = st.file_uploader("Load", type="json", label_visibility="collapsed", key="chk_loader_standalone")
        if up_file is not None:
            load_data = json.load(up_file)
            st.session_state.pm_checklist_state = load_data.get("checklist", {})
            st.session_state.estimate_data = load_data.get("estimates", [])
            st.toast("✅ Data Loaded! (Click any checkbox to refresh)")

        # --- BUTTON 3: EXPORT PDF ---
        pdf_bytes = create_pdf_report(p_name, c_no, str(r_date), e_by, st.session_state.pm_checklist_state)
        st.download_button("📥 Export PDF", data=pdf_bytes, 
                           file_name=f"{p_name}_Report.pdf", mime="application/pdf", use_container_width=True)

        # --- BUTTON 4: RESET ---
        if st.button("🗑️ Reset All Checks", use_container_width=True):
            for uid in st.session_state.pm_checklist_state:
                st.session_state.pm_checklist_state[uid]["done"] = False
                st.session_state.pm_checklist_state[uid]["na"] = False
            st.rerun()

    st.divider()

    # 3. Render Checklist Phases
    phases = checklist_df['p_clean'].unique()
    for phase in phases:
        with st.expander(f"Phase: {phase}", expanded=True):
            p_uids = [u for u, v in st.session_state.pm_checklist_state.items() if v['phase'] == phase]
            for uid in p_uids:
                data = st.session_state.pm_checklist_state[uid]
                c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
                
                with c1:
                    style = "color: #adb5bd; text-decoration: line-through;" if data["na"] else "font-weight: bold;"
                    st.markdown(f"<p style='{style} margin:0;'>{data['task']}</p>", unsafe_allow_html=True)
                
                # Checkbox Logic with local state sync
                with c2:
                    st.session_state.pm_checklist_state[uid]["done"] = st.checkbox(
                        "Done", key=f"d_{uid}", value=data["done"], disabled=data["na"]
                    )
                with c3:
                    st.session_state.pm_checklist_state[uid]["na"] = st.checkbox(
                        "N/A", key=f"n_{uid}", value=data["na"]
                    )
                    if st.session_state.pm_checklist_state[uid]["na"]:
                        st.session_state.pm_checklist_state[uid]["done"] = False

# ==========================================
