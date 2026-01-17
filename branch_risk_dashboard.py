import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import hmac

# =====================================================
# 0. AUTHENTICATION (MUST BE FIRST)
# =====================================================
def check_credentials():
    if not st.secrets["auth"]["enabled"]:
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.set_page_config(page_title="Secure Login", layout="centered")

    st.title("🔐 Secure Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if (
            hmac.compare_digest(username, st.secrets["auth"]["username"])
            and hmac.compare_digest(password, st.secrets["auth"]["password"])
        ):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid username or password")

    return False


if not check_credentials():
    st.stop()

# =====================================================
# 1. LOAD SECRETS / CONFIG
# =====================================================
APP_ENV = st.secrets["app"]["environment"]
DEFAULT_GRADE = st.secrets["app"]["default_grade"]
MAX_FILE_MB = st.secrets["limits"]["max_file_size_mb"]
ALLOWED_EXT = st.secrets["upload"]["allowed_extension"]
ENABLE_TAB_3 = st.secrets["features"]["enable_tab_3"]

# =====================================================
# 2. PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Branch Risk Analytics Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# 3. CORE LOGIC
# =====================================================
def check_condition(data_val, op, rule_val):
    op = str(op).strip().upper()

    if op in ("ALL", "ELSE"):
        return True

    try:
        d = float(data_val)
        r = float(rule_val)
        return {
            ">": d > r,
            "<": d < r,
            ">=": d >= r,
            "=>": d >= r,
            "<=": d <= r,
            "=<": d <= r,
            "=": d == r,
        }.get(op, False)
    except ValueError:
        d = str(data_val).upper().strip()
        r = str(rule_val).upper().strip()
        return {
            "CONTAINS": r in d,
            "=": d == r,
            "<>": d != r,
        }.get(op, False)


def get_grade(score, df_grades):
    df_grades = df_grades.sort_values("Min Score")
    for _, row in df_grades.iterrows():
        if row["Min Score"] <= score <= row["Max Score"]:
            return row["Grade"]
    return DEFAULT_GRADE


def process_uploaded_file(uploaded_file):
    try:
        xls = pd.ExcelFile(uploaded_file)
        df_rules = pd.read_excel(xls, "Sheet1")
        df_data = pd.read_excel(xls, "Sheet2", dtype={"BranchCode": str})
        df_grades = pd.read_excel(xls, "Sheet3")

        df_rules.columns = df_rules.columns.str.strip()
        df_data.columns = df_data.columns.str.strip()
        df_grades.columns = df_grades.columns.str.strip()

        grouped_rules = df_rules.groupby("Column Name")

        for param in grouped_rules.groups:
            if param in df_data.columns:
                df_data[f"{param} Score"] = 0.0

        df_data["Total Score"] = 0.0

        for i, row in df_data.iterrows():
            total = 0.0
            for param, rules in grouped_rules:
                if param not in df_data.columns:
                    continue
                for _, rule in rules.iterrows():
                    if check_condition(row[param], rule["Operator"], rule["Value"]):
                        score = float(rule["Score"])
                        df_data.at[i, f"{param} Score"] = score
                        total += score
                        break
            df_data.at[i, "Total Score"] = total

        df_data["Final Grade"] = df_data["Total Score"].apply(
            lambda x: get_grade(x, df_grades)
        )

        return df_data, None

    except Exception as e:
        return None, str(e)

# =====================================================
# 4. SIDEBAR
# =====================================================
st.sidebar.markdown("### 📁 Data Upload")
st.sidebar.markdown(f"**Environment:** `{APP_ENV.upper()}`")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader(
    "Upload Excel File",
    type=[ALLOWED_EXT]
)

if uploaded_file:
    if uploaded_file.size > MAX_FILE_MB * 1024 * 1024:
        st.sidebar.error("❌ File size exceeds limit")
        st.stop()
    st.sidebar.success("✓ File uploaded")

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()

# =====================================================
# 5. MAIN APP
# =====================================================
if uploaded_file:
    with st.spinner("Processing data..."):
        df, error = process_uploaded_file(uploaded_file)

    if error:
        st.error(error)
        st.stop()

    st.markdown(f"""
    <h1>🏦 Branch Risk Analytics Platform</h1>
    <p><b>Environment:</b> {APP_ENV.upper()} |
       <b>Updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    """, unsafe_allow_html=True)

    tabs = ["📊 Executive Dashboard", "🎯 Branch Analytics"]
    if ENABLE_TAB_3:
        tabs.append("📈 Detailed Reports")

    tab_objs = st.tabs(tabs)

    with tab_objs[0]:
        st.metric("Total Branches", len(df))
        st.metric("Average Risk Score", f"{df['Total Score'].mean():.2f}")

    with tab_objs[1]:
        branch = st.selectbox("Select Branch", df["BranchCode"].unique())
        st.dataframe(df[df["BranchCode"] == branch], use_container_width=True)

    if ENABLE_TAB_3:
        with tab_objs[2]:
            st.dataframe(df, use_container_width=True)

else:
    st.markdown("""
    <h1>🏦 Branch Risk Analytics Platform</h1>
    <p>Upload a file from the sidebar to begin.</p>
    """, unsafe_allow_html=True)
