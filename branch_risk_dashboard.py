import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Branch Risk Analytics Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. LOGIN LOGIC
# ==========================================
def check_password():
    """Return True only if user is authenticated."""

    def login_form():
        st.markdown(
            """
            <div style='text-align: center; padding: 2rem;'>
                <h1 style='color: #667eea;'>Security Portal</h1>
                <p style='color: #64748b;'>
                    Please enter your credentials to access the analytics hub.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("Credentials", clear_on_submit=False):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            submitted = st.form_submit_button("Log In")

            if submitted:
                if (
                    st.session_state.get("username") == st.secrets["credentials"]["username"]
                    and st.session_state.get("password") == st.secrets["credentials"]["password"]
                ):
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("User not found or password incorrect")

    if st.session_state.get("password_correct", False):
        return True
    else:
        login_form()
        return False

# ==========================================
# 3. MAIN APPLICATION
# ==========================================
def main_app():
    # Sidebar
    with st.sidebar:
        st.markdown("### Session")
        if st.button("Logout"):
            for key in ["password_correct", "username", "password"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # Main UI (guaranteed visible)
    st.title("🏦 Branch Risk Analytics Platform")
    st.caption("Internal Risk Monitoring Dashboard")

    # Example content (replace with your real logic)
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Branches", 128)
    col2.metric("High Risk Branches", 14)
    col3.metric("Last Refresh", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    st.divider()

    df = pd.DataFrame({
        "Branch": ["A", "B", "C", "D"],
        "Risk Score": [72, 45, 88, 60]
    })

    fig = px.bar(
        df,
        x="Branch",
        y="Risk Score",
        title="Branch Risk Scores"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4. EXECUTION FLOW
# ==========================================
if check_password():
    main_app()
