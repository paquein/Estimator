import streamlit as st
import sqlite3

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

# --- DATABASE SETUP (The 'Hidden' part) ---
def get_unit_price(item_name):
    # This simulates your 15-year database
    prices = {
        "Concrete Sidewalk": 120.00,
        "Curb & Gutter": 85.00,
        "Asphalt Patching": 45.00
    }
    return prices.get(item_name, 0.0)

# --- THE INTERFACE (The 'Streamlit' part) ---
st.title("🚧 Regina V2: Smart Estimator")

# Step 1: Selection from your 'Database'
item_choice = st.selectbox("Select Infrastructure Item:", ["Concrete Sidewalk", "Curb & Gutter", "Asphalt Patching"])
unit_price = get_unit_price(item_choice)

# Step 2: Dimensions
col1, col2 = st.columns(2)
with col1:
    length = st.number_input("Length (m)", value=10.0)
with col2:
    qty = st.number_input("Quantity of Units", value=1)

# Step 3: The Calculation
total_cost = unit_price * length * qty

# Step 4: The Result
st.divider()
st.metric(label=f"Estimated Cost for {item_choice}", value=f"${total_cost:,.2f}")
st.caption(f"Based on current Unit Price: ${unit_price}/m")