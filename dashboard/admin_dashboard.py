import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE = "https://face-attendance-system-1-635m.onrender.com"

st.set_page_config(page_title="Attendance Dashboard", page_icon="📊", layout="wide")

# Custom CSS for a premium look
st.markdown("""
    <style>
    .stMetric {
        background-color: rgba(28, 131, 225, 0.1);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(28, 131, 225, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Face Attendance Dashboard")
st.markdown("---")

try:
    # Fetch Data
    stats = requests.get(f"{API_BASE}/attendance/stats").json()
    present = requests.get(f"{API_BASE}/attendance/present").json()
    today_data = requests.get(f"{API_BASE}/attendance/today").json()

    # Metrics Row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Enrolled", stats["total_users"])
    col2.metric("Currently Present", stats["present"])
    col3.metric("Attendance Rate", f"{stats['attendance_percent']}%")

    st.divider()

    # Split View
    left_col, right_col = st.columns([1, 2])

    with left_col:
        st.subheader("🟢 Active This Session")
        if present:
            for u in present:
                st.success(f"👤 {u}")
        else:
            st.info("No active sessions detected.")

    with right_col:
        st.subheader("📋 Comprehensive Logs")
        if today_data:
            df = pd.DataFrame(today_data)
            # Formatting timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%H:%M:%S')
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No logs found for today.")

except Exception as e:
    st.error(f"Waiting for backend... (Error: {e})")
    st.info("Ensure the FastAPI server is running at http://127.0.0.1:8000")
