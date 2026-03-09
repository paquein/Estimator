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

# --- 2. THE CONSOLIDATED TREE ---
# Merged Full/Spot into Concrete Replacement and added Rebuild items here
LIST_MAP = {
    "Concrete Replacement": [
        "Install Standard Curb and Gutter", "Install Rolled Curb and Gutter", 
        "Install Reverse Curb and Gutter", "Install Median Curb", 
        "Install Median Access Curb", "Install Median Apron", 
        "Install Sidewalk", "Install Pedestrian Ramp", 
        "Install Standard Monolithic Walk, Curb & Gutter", 
        "Install Rolled Monolithic Walk, Curb & Gutter", 
        "Install Reverse Monolithic Walk, Curb & Gutter", 
        "Install Residential Driveway Crossing (130 mm)", 
        "Install Alley/Commercial Driveway Crossing (180 mm)", 
        "Private Driveway (Rebar)", "Asphalt Driveway Repair",
        "Slabjack Curb and Gutter", "Slabjack Concrete Slab", "Slabjack Combined Concrete",
        "Install Perforated Pipe (Rebuild)", "Concrete Extensions (Rebuild)"
    ],
    "Pavement": [
        "Asphalt Pavement Removal", "Cold Planing", "Asphalt Tack/Prime", 
        "Hot Mix Asphaltic Concrete (Fine Mix)", "Hot Mix Asphaltic Concrete (Coarse Mix)", 
        "Subgrade Preparation and Compaction", "Granular Base Course", "Granular Sub-Base Course",
        "Excavation - Pavement Failure", "Concrete Base (Mix 4HE)"
    ],
    "Landscaping": [
        "Clearing and Grubbing", "Remove/Reinstate Existing Landscape Rock", 
        "Remove Existing Brick", "Removal of Sidewalk Trip Hazard", "Install Existing Brick"
    ],
    "Water and Sewer": [
        "Standard Water Box", "Standard Sewer Box", "Adjust Existing Water Box", 
        "Adjust Existing Sewer Box", "New Hydrant Installation", "New Valve Installation"
    ]
}

# --- 3. SIDEBAR & PROJECT DETAILS ---
with st.sidebar:
    st.title("📋 Project Details")
    project_name = st.text_input("Project Name", value="Regina Infrastructure")
    contract_no = st.text_input("Contract #", value="2026-001")
    report_date = st.date_input("Report Date", date.today())
    
    st.divider()
    st.write("**Personnel**")
    est_by = st.text_input("Estimated by", placeholder="Name")
    rev_by = st.text_input("Reviewed by", placeholder="Name")
    
    st.divider()
    st.title("Navigation")
    page = st.radio("Go to:", list(LIST_MAP.keys()) + ["Estimation Result"])
    
    st.divider()
    if st.button("Clear All Data", type="secondary"):
        st.session_state.estimate_data = []
        st.session_state.editing_index = None
        st.rerun()

# --- 4. DATA ENTRY LOGIC ---
if page != "Estimation Result":
    st.header(f"{page}")
    
    # Selection logic for editing existing rows
    edit_idx = st.session_state.editing_index
    is_editing = (edit_idx is not None and edit_idx < len(st.session_state.estimate_data) and st.session_state.estimate_data[edit_idx]["Category"] == page)
    cur = st.session_state.estimate_data[edit_idx] if is_editing else {}

    with st.container(border=True):
        col1, col2, col3 = st.columns([0.3, 0.2, 0.5])
        with col1:
            items = LIST_MAP.get(page, [])
            item = st.selectbox("Item Selection", items, index=items.index(cur["Item"]) if is_editing and cur["Item"] in items else 0)
            f_val = st.number_input("From Station", value=float(cur.get("From", 0.0)), format="%.2f", step=1.0)
            t_val = st.number_input("To Station", value=float(cur.get("To", 0.0)), format="%.2f", step=1.0)
            w_val = st.number_input("Width (m)", value=float(cur.get("Width", 1.5)), step=0.1)
        with col2:
            st.write("**Options**")
            base_val = st.checkbox("Add Base Only", value=cur.get("Base", False))
            seed_val = st.checkbox("Add Seed", value=cur.get("Seed", False))
            sod_val = st.checkbox("Add SOD", value=cur.get("SOD", False))
        with col3:
            notes_val = st.text_area("Notes", value=cur.get("Notes", ""), height=225, placeholder="Enter site-specific details...")

    # Action Buttons
    if is_editing:
        c1, c2, c3 = st.columns([1, 1, 4])
        with c1:
            if st.button("✅ Update", type="primary", use_container_width=True):
                st.session_state.estimate_data[edit_idx] = {
                    "Category": page, "Item": item, "Unit": "m²", 
                    "Quantity": abs(t_val - f_val) * w_val, "From": f_val, "To": t_val, 
                    "Width": w_val, "Notes": notes_val, "Base": base_val, "Seed": seed_val, "SOD": sod_val
                }
                st.session_state.editing_index = None
                st.rerun()
        with c2:
            if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                st.session_state.estimate_data.pop(edit_idx)
                st.session_state.editing_index = None
                st.rerun()
        with c3:
            if st.button("Cancel"):
                st.session_state.editing_index = None
                st.rerun()
    else:
        if st.button("➕ Add to Estimate", type="primary"):
            st.session_state.estimate_data.append({
                "Category": page, "Item": item, "Unit": "m²", 
                "Quantity": abs(t_val - f_val) * w_val, "From": f_val, "To": t_val, 
                "Width": w_val, "Notes": notes_val, "Base": base_val, "Seed": seed_val, "SOD": sod_val
            })
            st.rerun()

    st.divider()

    # Local Table for Current Page
    if st.session_state.estimate_data:
        df = pd.DataFrame(st.session_state.estimate_data)
        page_df = df[df['Category'] == page]
        if not page_df.empty:
            st.write(f"### {page} Work List")
            event = st.dataframe(page_df[['Item', 'Quantity', 'From', 'To', 'Notes']], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            st.info(f"**Section Total:** {page_df['Quantity'].sum():.2f} m²")
            if event.selection.rows:
                st.session_state.editing_index = page_df.index[event.selection.rows[0]]
                st.rerun()

# --- 5. RESULT PAGE ---
else:
    st.header(f"📊 Project Summary: {project_name}")
    
    with st.container(border=True):
        colA, colB = st.columns(2)
        with colA:
            st.write(f"**Contract #:** {contract_no}")
            st.write(f"**Estimated by:** {est_by if est_by else 'Not Specified'}")
        with colB:
            st.write(f"**Date:** {report_date}")
            st.write(f"**Reviewed by:** {rev_by if rev_by else 'Not Specified'}")
    
    if st.session_state.estimate_data:
        final_df = pd.DataFrame(st.session_state.estimate_data)
        st.write("### Project Totals by Item")
        summary = final_df.groupby(['Category', 'Item'])['Quantity'].sum().reset_index()
        st.table(summary)

        st.divider()
        st.write("### Detailed Take-off")
        st.dataframe(final_df[['Category', 'Item', 'Quantity', 'From', 'To', 'Notes']], use_container_width=True, hide_index=True)
    else:
        st.warning("No data recorded. Use the sidebar to navigate and add items.")
