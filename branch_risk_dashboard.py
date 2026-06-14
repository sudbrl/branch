import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import hmac
import numpy as np
import requests
import io

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
# 2. YOUR ORIGINAL STYLING (RESTORED)
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
        color: #f8fafc;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
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
        transition: 0.2s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }

    .chart-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }

    .chart-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 1rem;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. AUTH (UNCHANGED)
# ==========================================
def check_password():
    def password_entered():
        if "credentials" not in st.secrets:
            st.error("⚠️ Authentication not configured.")
            return

        if (hmac.compare_digest(st.session_state["username"], st.secrets["credentials"]["username"]) and
            hmac.compare_digest(st.session_state["password"], st.secrets["credentials"]["password"])):

            st.session_state["password_correct"] = True
            st.session_state["user_name"] = st.secrets["credentials"].get("name", "User")
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h1 style='text-align:center;'>Branch Risk Analytics</h1>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.button("Login", on_click=password_entered)

        return False

    return st.session_state["password_correct"]

# ==========================================
# 4. FIXED DATA LOADER (ONLY CHANGE)
# ==========================================
@st.cache_data(show_spinner=False)
def process_uploaded_file(file_url):
    try:
        r = requests.get(file_url, timeout=60)
        r.raise_for_status()

        excel_file = io.BytesIO(r.content)
        xls = pd.ExcelFile(excel_file)

        df_rules = pd.read_excel(xls, "Sheet1")
        df_data = pd.read_excel(xls, "Sheet2", dtype={'BranchCode': str})
        df_grades = pd.read_excel(xls, "Sheet3")

        df_rules.columns = df_rules.columns.str.strip()
        df_data.columns = df_data.columns.str.strip()
        df_grades.columns = df_grades.columns.str.strip()

        unique_params = df_rules['Column Name'].unique()

        df_data = apply_rules_vectorized(df_data, df_rules, unique_params)
        df_data["Final Grade"] = df_data["Total Score"].apply(lambda x: get_grade(x, df_grades))

        return df_data, None

    except Exception as e:
        return None, str(e)

# ==========================================
# 5. RULE ENGINE (UNCHANGED)
# ==========================================
def apply_rules_vectorized(df, df_rules, unique_params):
    for param in unique_params:
        if param in df.columns:
            df[f"{param} Score"] = 0.0

    for param in unique_params:
        if param not in df.columns:
            continue

        rules = df_rules[df_rules['Column Name'] == param]
        is_assigned = pd.Series(False, index=df.index)

        for _, rule in rules.iterrows():
            op = str(rule['Operator']).strip().upper()
            val = rule['Value']
            score = float(rule['Score'])

            col = df[param]

            try:
                if op in ["ALL", "ELSE"]:
                    mask = pd.Series(True, index=df.index)
                elif op == ">":
                    mask = pd.to_numeric(col, errors='coerce') > float(val)
                elif op == "<":
                    mask = pd.to_numeric(col, errors='coerce') < float(val)
                elif op in [">=", "=>"]:
                    mask = pd.to_numeric(col, errors='coerce') >= float(val)
                elif op in ["<=", "=<"]:
                    mask = pd.to_numeric(col, errors='coerce') <= float(val)
                elif op == "=":
                    mask = col.astype(str).str.strip() == str(val).strip()
                elif op == "CONTAINS":
                    mask = col.astype(str).str.contains(str(val), na=False)
                else:
                    mask = pd.Series(False, index=df.index)

                mask = mask.fillna(False)
                update = mask & (~is_assigned)

                df.loc[update, f"{param} Score"] = score
                is_assigned |= update

            except:
                continue

    score_cols = [c for c in df.columns if c.endswith(" Score")]
    df["Total Score"] = df[score_cols].sum(axis=1)

    return df

# ==========================================
# 6. HELPERS
# ==========================================
def get_grade(score, df_grades):
    for _, r in df_grades.iterrows():
        if r["Min Score"] <= score <= r["Max Score"]:
            return r["Grade"]
    return "C"

# ==========================================
# 7. MAIN APP
# ==========================================
if check_password():

    url = st.secrets["data"]["url"]

    with st.spinner("🔄 Fetching and processing data..."):
        df, error = process_uploaded_file(url)

    if error:
        st.error(error)
        st.stop()

    # HEADER (RESTORED)
    st.markdown(f"""
        <div class="dashboard-header">
            <h1 class="dashboard-title">🏦 Branch Risk Analytics Platform</h1>
            <p class="dashboard-subtitle">
                Real-time Risk Assessment | {datetime.now().strftime('%B %d, %Y')}
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Executive Dashboard",
        "🎯 Branch Analytics",
        "📈 Detailed Reports",
        "🔍 Attribute Filter"
    ])

    # =========================
    # TAB 1
    # =========================
    with tab1:
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            st.metric("Total Branches", len(df))
        with c2:
            st.metric("Avg Score", round(df["Total Score"].mean(), 2))
        with c3:
            st.metric("A Grade", len(df[df["Final Grade"] == "A"]))
        with c4:
            st.metric("B Grade", len(df[df["Final Grade"] == "B"]))
        with c5:
            st.metric("C Grade", len(df[df["Final Grade"] == "C"]))

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown('<div class="chart-card"><div class="chart-title">Risk Distribution</div>', unsafe_allow_html=True)
            fig = go.Figure(data=[go.Pie(
                labels=df["Final Grade"].value_counts().index,
                values=df["Final Grade"].value_counts().values
            )])
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="chart-card"><div class="chart-title">Score Distribution</div>', unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Histogram(x=df["Total Score"]))
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # TAB 2
    # =========================
    with tab2:
        branch = st.selectbox("Select Branch", df["BranchCode"].unique())
        row = df[df["BranchCode"] == branch].iloc[0]
        st.dataframe(row)

    # =========================
    # TAB 3
    # =========================
    with tab3:
        st.dataframe(df)
        st.download_button("Download CSV", df.to_csv(index=False), "report.csv")

    # =========================
    # TAB 4
    # =========================
    with tab4:
        col = st.selectbox("Column", df.columns)

        if pd.api.types.is_numeric_dtype(df[col]):
            mn, mx = float(df[col].min()), float(df[col].max())
            v1, v2 = st.slider("Range", mn, mx, (mn, mx))
            filtered = df[(df[col] >= v1) & (df[col] <= v2)]
        else:
            vals = st.multiselect("Values", df[col].unique(), default=df[col].unique())
            filtered = df[df[col].isin(vals)]

        st.dataframe(filtered)
