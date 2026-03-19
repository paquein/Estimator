import streamlit as st
import pandas as pd
import os
from datetime import date

# 1. SECURITY / PASSWORD
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == "franistheman":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Please enter the password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Please enter the password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    return True

if not check_password():
    st.stop()

# 2. CONFIGURATION & INITIALIZATION
st.set_page_config(page_title="Regina Master Estimator", layout="wide")

# Initialize global data storage if not already present
if 'estimate_data' not in st.session_state:
    st.session_state.estimate_data = []
if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None

# Load the Checklist CSV globally once
@st.cache_data
def load_global_checklist():
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
    return pd.DataFrame()

checklist_df = load_global_checklist()

# 3. SIDEBAR (The Control Center)
with st.sidebar:
    st.title("📋 Project Details")
    # We store these in a dictionary to pass them easily to modules
    proj_info = {
        "name": st.text_input("Project Name", value="Regina SIRP Package"),
        "contract": st.text_input("Contract #", value="2026-SIRP"),
        "date": st.date_input("Report Date", date.today()),
        "est_by": st.text_input("Estimated by", placeholder="Name"),
        "rev_by": st.text_input("Reviewed by", placeholder="Name")
    }
    
    st.divider()
    st.title("Navigation")
    
    # Define our Menu
    manual_sections = ["Concrete Replacement", "Pavement", "Landscaping", "Water and Sewer"]
    page = st.radio("Go to:", ["Global Quick Estimate", "PM Checklist"] + manual_sections + ["Estimation Result"])
    
    st.divider()
    if st.button("Clear All Project Data", type="secondary", use_container_width=True):
        st.session_state.estimate_data = []
        st.session_state.editing_index = None
        if 'pm_checklist_state' in st.session_state:
            del st.session_state.pm_checklist_state
        st.rerun()

# 4. ROUTER (The Switchboard)
# Note: We will create the 'modules' folder and files in the next steps.

try:
    from modules import checklist, global_engine, manual_entry, results

    if page == "PM Checklist":
        checklist.render(proj_info, checklist_df)

    elif page == "Global Quick Estimate":
        global_engine.render()

    elif page == "Estimation Result":
        results.render(proj_info)

    elif page in manual_sections:
        manual_entry.render(page)

except ImportError as e:
    st.error(f"Module Loading Error: {e}")
    st.info("We need to create the 'modules' folder and the .py files next!")
