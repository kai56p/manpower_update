import streamlit as st
import datetime
import db_utils 

# Initialize database
db_utils.init_dummy_db()

st.set_page_config(page_title="Site Manpower Logger", page_icon="🏗️")

st.title("Worker Deployment Logger")
st.markdown("Select the deployment details below to log today's manpower.")

# --- DATE FORMATTING ---
today_str = datetime.date.today().strftime("%Y-%m-%d")
display_date = datetime.date.today().strftime("%d/%m/%Y") 

# --- 1. UI INPUTS ---
col1, col2 = st.columns(2)
with col1:
    supervisors = db_utils.get_dropdown_options('Supervisor')
    selected_supervisor = st.selectbox("Supervisor Name", supervisors)
with col2:
    sites = db_utils.get_dropdown_options('Site_Location')
    selected_site = st.selectbox("Site Location", sites)

num_workers = st.number_input("Number of Workers", min_value=0, value=0, step=1)

# --- 2. PROCESS AND LOG DATA ---
if st.button("Log Deployment & Update Summary", type="primary"):
    
    # Log the data directly (Overwrites if the supervisor already logged today)
    db_utils.log_daily_deployment(today_str, selected_supervisor, selected_site, num_workers)
    
    st.success(f"✅ Record saved successfully for {selected_supervisor}!")

st.divider()

# --- 3. FETCH LIVE DATA ---
todays_df, total_manpower = db_utils.get_todays_summary(today_str)

if not todays_df.empty:
    
    # --- 4. WHATSAPP CONSOLIDATED MESSAGE ---
    whatsapp_lines = [
        "Daily Manpower",
        f"Date      {display_date}",
        ""
    ]
    
    for index, row in todays_df.iterrows():
        whatsapp_lines.append(f"{row['Supervisor']} ->  {row['Workers']}")
        
    whatsapp_lines.append(f"Total manpower  =  {int(total_manpower)}")
    
    # APP_URL = "https://your-app-name.streamlit.app"
    APP_URL = "https://manpowerupdate-tnyp8osa8fcfycjstivc7x.streamlit.app/?embed_options=dark_theme"
    whatsapp_lines.append("\n----------------------------------------")
    whatsapp_lines.append(f"⚠️ *Update via link:* {APP_URL}")
    
    whatsapp_summary = "\n".join(whatsapp_lines)
    
    st.subheader("📱 WhatsApp Daily Summary")
    st.markdown("Copy this block to paste into the group chat:")
    st.code(whatsapp_summary, language="text")

    st.divider()

    # --- 5. DATA VIEW (LAST) ---
    st.subheader(f"📋 Database View ({display_date})")
    st.metric(label="Total Manpower Deployed Today", value=int(total_manpower))
    st.dataframe(todays_df, use_container_width=True, hide_index=True)
    
else:
    st.info("No deployments have been logged for today yet. The summary will appear here once the first log is submitted.")