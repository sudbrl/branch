import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import hmac
import numpy as np

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
# 2. MODERN STYLING
# ==========================================
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
    }
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    .dashboard-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .dashboard-subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    div[data-testid="stMetric"] {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #667eea;
    }
    .chart-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        margin-bottom: 1rem;
    }
    .chart-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 1rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .badge-success { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; }
    .badge-warning { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; }
    .badge-danger { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. AUTHENTICATION SYSTEM
# ==========================================
def check_password():
    def password_entered():
        try:
            if hmac.compare_digest(st.session_state["username"], st.secrets["credentials"]["username"]) and \
               hmac.compare_digest(st.session_state["password"], st.secrets["credentials"]["password"]):
                st.session_state["password_correct"] = True
                st.session_state["user_name"] = st.secrets["credentials"].get("name", "User")
                st.session_state["user_role"] = st.secrets["credentials"].get("role", "Administrator")
                del st.session_state["password"]
                del st.session_state["username"]
            else:
                st.session_state["password_correct"] = False
        except Exception as e:
            st.error(f"⚠️ Authentication error: {str(e)}")

    if "password_correct" not in st.session_state:
        st.text_input("👤 Username", key="username")
        st.text_input("🔑 Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        return False
    return st.session_state["password_correct"]

# ==========================================
# 4. MAIN APPLICATION
# ==========================================
if check_password():
    
    # ------------------------------------------
    # 4.1. CORE LOGIC FUNCTIONS
    # ------------------------------------------
    def check_condition(data_val, op, rule_val):
        try:
            op = str(op).strip().upper()
            if op in ["ALL", "ELSE"]: return True
            try:
                d_num, r_num = float(data_val), float(rule_val)
                if op == ">": return d_num > r_num
                if op == "<": return d_num < r_num
                if op in [">=", "=>"]: return d_num >= r_num
                if op in ["<=", "=<"]: return d_num <= r_num
                if op == "=": return d_num == r_num
            except: pass
            d_str, r_str = str(data_val).upper().strip(), str(rule_val).upper().strip()
            if op == "CONTAINS": return r_str in d_str
            if op == "=": return d_str == r_str
            if op == "<>": return d_str != r_str
            return False
        except: return False

    def get_grade(score, df_grades):
        for _, row in df_grades.iterrows():
            if row['Min Score'] <= score <= row['Max Score']:
                return row['Grade']
        return "N/A"

    @st.cache_data(show_spinner=False)
    def process_data(url):
        xls = pd.ExcelFile(url)
        df_rules = pd.read_excel(xls, "Sheet1")
        df_data = pd.read_excel(xls, "Sheet2", dtype={'BranchCode': str})
        df_grades = pd.read_excel(xls, "Sheet3")
        
        unique_params = df_rules['Column Name'].unique()
        for param in unique_params:
            if param in df_data.columns:
                df_data[f"{param} Score"] = 0.0
        
        for index, row in df_data.iterrows():
            total_score = 0.0
            for param in unique_params:
                if param not in df_data.columns: continue
                param_rules = df_rules[df_rules['Column Name'] == param]
                for _, rule in param_rules.iterrows():
                    if check_condition(row[param], rule['Operator'], rule['Value']):
                        score = float(rule['Score'])
                        df_data.at[index, f"{param} Score"] = score
                        total_score += score
                        break
            df_data.at[index, "Total Score"] = total_score
        
        df_data["Final Grade"] = df_data["Total Score"].apply(lambda x: get_grade(x, df_grades))
        return df_data

    def get_grade_color(grade):
        colors = {
            'A': {'primary': '#10b981', 'light': '#d1fae5'},
            'B': {'primary': '#f59e0b', 'light': '#fef3c7'},
            'C': {'primary': '#ef4444', 'light': '#fee2e2'}
        }
        return colors.get(grade, {'primary': '#94a3b8', 'light': '#f1f5f9'})

    # ------------------------------------------
    # 4.2. DATA INITIALIZATION
    # ------------------------------------------
    DATA_URL = st.secrets["data"]["url"]
    df = process_data(DATA_URL)

    # ------------------------------------------
    # 4.3. RENDER TABS
    # ------------------------------------------
    st.markdown(f"""
        <div class="dashboard-header">
            <h1 class="dashboard-title">🏦 Branch Risk Analytics Platform</h1>
            <p class="dashboard-subtitle">Data-Driven Portfolio Oversight | {datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Executive Dashboard", "🎯 Branch Analytics", "📈 Detailed Reports"])

    # --- TAB 1: EXECUTIVE OVERVIEW ---
    with tab1:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Branches", len(df))
        col2.metric("Avg Portfolio Score", f"{df['Total Score'].mean():.2f}")
        col3.metric("Low Risk (A)", len(df[df['Final Grade']=='A']))
        col4.metric("Med Risk (B)", len(df[df['Final Grade']=='B']))
        col5.metric("High Risk (C)", len(df[df['Final Grade']=='C']))
        
        # Grade Distribution Pie
        fig_pie = px.pie(df, names='Final Grade', hole=0.4, 
                         color='Final Grade', color_discrete_map={'A':'#10b981','B':'#f59e0b','C':'#ef4444'})
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- TAB 2: BRANCH ANALYTICS (DEEP DIVE) ---
    with tab2:
        st.markdown("### 🎯 Branch Profile Analysis")
        
        # Logic: Set "All" as default
        branch_options = ["All"] + sorted(df['BranchCode'].unique().tolist())
        selected_branch = st.selectbox("🔍 Select Branch to Inspect", options=branch_options, index=0)
        
        if selected_branch == "All":
            # Portfolio Average View
            branch_data = df.mean(numeric_only=True)
            grade = "Portfolio Avg"
            color_scheme = {'primary': '#667eea'}
            status_text = "PORTFOLIO AVERAGE"
            badge_class = "badge-success"
        else:
            # Single Branch View
            branch_data = df[df['BranchCode'] == selected_branch].iloc[0]
            grade = branch_data['Final Grade']
            color_scheme = get_grade_color(grade)
            status_text = f"{grade} RISK PROFILE"
            badge_class = 'badge-success' if grade == 'A' else 'badge-warning' if grade == 'B' else 'badge-danger'

        col1, col2, col3 = st.columns(3)
        col1.metric("Risk Score", f"{branch_data['Total Score']:.2f}")
        col2.metric("Grade / Context", grade)
        with col3:
            st.markdown(f"<div class='status-badge {badge_class}'>{status_text}</div>", unsafe_allow_html=True)

        # Radar Chart
        score_cols = [c for c in df.columns if c.endswith("Score") and c != "Total Score"]
        params = [c.replace(" Score", "") for c in score_cols]
        scores = [branch_data[c] for c in score_cols]

        fig_radar = go.Figure(data=go.Scatterpolar(r=scores, theta=params, fill='toself', line_color=color_scheme['primary']))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, df[score_cols].max().max()])), showlegend=False)
        st.plotly_chart(fig_radar, use_container_width=True)

    # --- TAB 3: DETAILED REPORTS ---
    with tab3:
        st.markdown("### 📈 Comprehensive Portfolio Data")
        
        # Logic: Replace Search with Validation Box, "All" as default
        all_branches = sorted(df['BranchCode'].unique().tolist())
        branch_selection = st.multiselect(
            "🔍 Validate & Filter Branch Selection", 
            options=["All"] + all_branches, 
            default=["All"]
        )
        
        grade_filter = st.multiselect("Filter by Grade", options=['A', 'B', 'C'], default=['A', 'B', 'C'])
        
        # Filtering Logic
        if "All" in branch_selection or not branch_selection:
            filtered_df = df[df['Final Grade'].isin(grade_filter)]
        else:
            filtered_df = df[(df['BranchCode'].isin(branch_selection)) & (df['Final Grade'].isin(grade_filter))]

        st.dataframe(filtered_df.style.background_gradient(subset=['Total Score'], cmap='RdYlGn_r'), use_container_width=True)
        
        # Export
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Filtered Report", data=csv, file_name="risk_report.csv", mime="text/csv")

# ==========================================
# 5. FOOTER
# ==========================================
st.sidebar.markdown("---")
st.sidebar.caption(f"System Version: 2.4.0 | Jan 2026")
