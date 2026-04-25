import streamlit as st
import pandas as pd
import sqlite3
import datetime
import random
import string


# --- 1. DUMMY DATABASE SETUP (Replace with your SQLAlchemy/actual DB connection) ---
@st.cache_resource
def get_database_connection():
    # Creating a temporary local SQLite DB for demonstration
    conn = sqlite3.connect('site_management.db', check_same_thread=False)
    
    # Pre-populating with some sample data
    dummy_data = pd.DataFrame({
        'Supervisor': ['Sheng Hui', 'Edrey', 'Faiz', 'Kaung'],
        'Site_Location': ['Sector A - Foundation', 'Sector B - Framing', 'Sector A - Foundation', 'Sector C - Logistics'],
        'Max_Workers': [15, 20, 10, 25],
        'Deployment_Code': ['DEP-SH-001', 'DEP-ED-002', 'DEP-FZ-003', 'DEP-KG-004']
    })
    dummy_data.to_sql('deployments', conn, if_exists='replace', index=False)
    return conn

conn = get_database_connection()
# ---------------------------------------------------------------------------------

st.set_page_config(page_title="Deployment Lookup", page_icon="🏗️")

st.title("Worker Deployment Lookup")
st.markdown("Select the deployment details below to retrieve the assignment code.")

# --- 2. FETCH UNIQUE VALUES FOR DROPDOWNS ---
# Query the DB to populate the dropdown options dynamically
supervisors = pd.read_sql("SELECT DISTINCT Supervisor FROM deployments", conn)['Supervisor'].tolist()
sites = pd.read_sql("SELECT DISTINCT Site_Location FROM deployments", conn)['Site_Location'].tolist()

# --- 3. UI INPUTS ---
col1, col2 = st.columns(2)
with col1:
    selected_supervisor = st.selectbox("Supervisor Name", supervisors)
with col2:
    selected_site = st.selectbox("Site Location", sites)

# Number input for workers
num_workers = st.number_input("Number of Workers", min_value=1, value=5, step=1)

# --- 4. QUERY AND DISPLAY RESULT ---
if st.button("Generate & Retrieve Code", type="primary"):
    
    # Query your database based on the selections
    # (Adjust the SQL logic based on how you want to match the worker count)
    query = f"""
    SELECT Deployment_Code 
    FROM deployments 
    WHERE Supervisor = '{selected_supervisor}' 
      AND Site_Location = '{selected_site}'
    LIMIT 1
    """
    
    result_df = pd.read_sql(query, conn)
    
    st.divider()
    
    if not result_df.empty:
        # Extract the value from the dataframe
        value_to_copy = result_df.iloc[0]['Deployment_Code']
        
        st.success("Record retrieved successfully!")
        st.write("Click the icon on the right side of the box below to copy the value:")
        
        # st.code automatically provides a copy-to-clipboard button
        st.code(value_to_copy, language=None)
    else:
        st.warning("No matching record found for this Supervisor and Site combination.")
        
    if st.button("Generate WhatsApp Update", type="primary"):
        
        # Define your public Streamlit app URL here
        APP_URL = "https://your-app-name.streamlit.app"
        
        # Get today's date for the record
        today_date = datetime.datetime.now().strftime("%d %b %Y")
        
        # Construct the WhatsApp-friendly message using an f-string
        whatsapp_summary = f"""*👷 Site Deployment Update | {today_date}*

    *Supervisor:* {selected_supervisor}
    *Site Location:* {selected_site}
    *Workers Deployed:* {num_workers}

    ----------------------------------------
    *⚠️ TO THE NEXT SUPERVISOR:*
    Please DO NOT manually copy and edit this text!

    👉 *Click the link below to fill in the form and generate your update:*
    {APP_URL}"""

        st.divider()
        st.success("Summary generated! Click the copy icon in the top right of the box below:")
        
        # Display the formatted message for copying
        # Setting language to 'markdown' helps it look a bit cleaner in the Streamlit UI
        st.code(whatsapp_summary, language="markdown")