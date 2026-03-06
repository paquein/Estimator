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

# --- INITIALIZE MEMORY ---
# This creates an empty list if it's the first time opening the app
if "estimate_list" not in st.session_state:
    st.session_state.estimate_list = []

st.title("🚧 Regina Infrastructure Estimator")

# --- INPUT SECTION ---
with st.expander("Add New Item", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        item = st.selectbox("Infrastructure Item", ["Sidewalk", "Curb & Gutter", "Pavement Patch", "Driveway"])
    with col2:
        length = st.number_input("Quantity/Length", min_value=0.0, step=1.0, value=10.0)
    with col3:
        unit_price = st.number_input("Unit Price ($)", min_value=0.0, step=0.1, value=150.0)

    # Calculation for THIS specific item
    subtotal = length * unit_price
    
    if st.button("➕ Add to Estimate"):
        # Add a dictionary of data to our "Memory" list
        new_entry = {
            "Item": item,
            "Quantity": length,
            "Price/Unit": f"${unit_price:,.2f}",
            "Total": subtotal
        }
        st.session_state.estimate_list.append(new_entry)
        st.success(f"Added {item} to the list!")

# --- DISPLAY SECTION ---
st.divider()
st.subheader("Current Estimation List")

if st.session_state.estimate_list:
    # Convert our memory list into a nice table
    df = pd.DataFrame(st.session_state.estimate_list)
    st.table(df)

    # CALC TOTAL
    grand_total = df["Total"].sum()
    
    st.metric(label="GRAND TOTAL ESTIMATE", value=f"${grand_total:,.2f}")

    if st.button("🗑️ Clear All"):
        st.session_state.estimate_list = []
        st.rerun()
else:
    st.info("No items added yet. Use the section above to start your estimate.")
