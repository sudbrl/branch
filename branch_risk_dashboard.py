import streamlit as st
import pandas as pd
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
    /* Global Styles */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
    }
    
    /* Header Styling */
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
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #667eea;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    /* Card Container */
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
        display: flex;
        align-items: center;
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
    }
    
    .badge-success { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; }
    .badge-warning { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; }
    .badge-danger { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        background-color: white; border-radius: 8px 8px 0 0;
        padding: 12px 24px; font-weight: 600; color: #64748b; border: none;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. AUTHENTICATION SYSTEM
# ==========================================
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        try:
            if "credentials" not in st.secrets:
                st.error("⚠️ Authentication not configured.")
                return
            
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
            st.error(f"⚠️ Error: {str(e)}")

    if "password_correct" not in st.session_state:
        if "credentials" not in st.secrets:
            st.warning("⚠️ Secrets not found.")
            st.stop()
        
        st.markdown("""<div style='text-align: center; padding: 2rem 0;'><h1 style='color: #1e293b;'>Branch Risk Analytics</h1></div>""", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.text_input("👤 Username", key="username")
            st.text_input("🔑 Password", type="password", key="password")
            st.button("Login", on_click=password_entered, use_container_width=True)
            if st.session_state.get("password_correct") is False:
                st.error("❌ Invalid login")
        return False
    elif not st.session_state["password_correct"]:
        st.session_state["password_correct"] = None
        st.rerun()
        return False
    else:
        return True

# ==========================================
# 4. OPTIMIZED CALCULATION ENGINE
# ==========================================
def get_grade(score, df_grades):
    try:
        for _, row in df_grades.iterrows():
            if row['Min Score'] <= score <= row['Max Score']:
                return row['Grade']
    except:
        return "N/A"
    return "N/A"

def apply_rules_vectorized(df, df_rules, unique_params):
    """
    Optimized function to apply rules using vectorized operations.
    """
    # Initialize score columns
    for param in unique_params:
        if param in df.columns:
            df[f"{param} Score"] = 0.0

    # Process each parameter
    for param in unique_params:
        if param not in df.columns: continue
        
        # Get rules for this parameter
        rules = df_rules[df_rules['Column Name'] == param]
        
        # Track which rows have already been assigned a score
        is_assigned = pd.Series([False] * len(df), index=df.index)
        
        for _, rule in rules.iterrows():
            op = str(rule['Operator']).strip().upper()
            val = rule['Value']
            score = float(rule['Score'])
            
            # Create mask for current rule
            try:
                col_data = df[param]
                
                if op == "ALL" or op == "ELSE":
                    current_mask = pd.Series([True] * len(df), index=df.index)
                elif op == ">":
                    current_mask = pd.to_numeric(col_data, errors='coerce') > float(val)
                elif op == "<":
                    current_mask = pd.to_numeric(col_data, errors='coerce') < float(val)
                elif op in [">=", "=>"]:
                    current_mask = pd.to_numeric(col_data, errors='coerce') >= float(val)
                elif op in ["<=", "=<"]:
                    current_mask = pd.to_numeric(col_data, errors='coerce') <= float(val)
                elif op == "=":
                    is_numeric_col = pd.to_numeric(col_data, errors='coerce').notna().all()
                    if is_numeric_col:
                        current_mask = pd.to_numeric(col_data, errors='coerce') == float(val)
                    else:
                        current_mask = col_data.astype(str).str.upper().str.strip() == str(val).upper().strip()
                elif op == "<>":
                    current_mask = col_data.astype(str).str.upper().str.strip() != str(val).upper().strip()
                elif op == "CONTAINS":
                    current_mask = col_data.astype(str).str.upper().str.contains(str(val).upper().strip(), na=False)
                else:
                    current_mask = pd.Series([False] * len(df), index=df.index)
                
                # Fill NaNs with False
                current_mask = current_mask.fillna(False)
                
                # Apply score to rows that match AND haven't been assigned yet
                update_mask = current_mask & (~is_assigned)
                if update_mask.any():
                    df.loc[update_mask, f"{param} Score"] = score
                    is_assigned = is_assigned | update_mask
                
            except Exception as e:
                continue
                
    # Sum total scores
    score_cols = [c for c in df.columns if c.endswith(" Score")]
    df["Total Score"] = df[score_cols].sum(axis=1)
    return df

@st.cache_data(show_spinner=False)
def process_uploaded_file(file_path):
    try:
        xls = pd.ExcelFile(file_path)
        df_rules = pd.read_excel(xls, "Sheet1")
        df_data = pd.read_excel(xls, "Sheet2", dtype={'BranchCode': str})
        df_grades = pd.read_excel(xls, "Sheet3")
        
        # Clean columns
        df_rules.columns = [c.strip() for c in df_rules.columns]
        df_data.columns = [c.strip() for c in df_data.columns]
        df_grades.columns = [c.strip() for c in df_grades.columns]
        
        unique_params = df_rules['Column Name'].unique()
        
        # USE OPTIMIZED VECTORIZED FUNCTION
        df_data = apply_rules_vectorized(df_data, df_rules, unique_params)
        
        # Apply Grades
        df_data["Final Grade"] = df_data["Total Score"].apply(lambda x: get_grade(x, df_grades))
        
        return df_data, None
    except Exception as e:
        return None, str(e)

def get_grade_color(grade):
    colors = {
        'A': {'primary': '#10b981', 'light': '#d1fae5'},
        'B': {'primary': '#f59e0b', 'light': '#fef3c7'},
        'C': {'primary': '#ef4444', 'light': '#fee2e2'}
    }
    return colors.get(grade, colors['C'])

def format_value(val, col_name=""):
    """Helper to format values based on type and column name"""
    # 1. Percentage Columns (Only if NOT a Score column)
    #    This ensures "Net NPL%" gets formatted, but "Net NPL% Score" is treated as a number
    if "%" in col_name and "Score" not in col_name and isinstance(val, (int, float, np.number)):
         return f"{val:.2%}"

    # 2. Standard Floats -> Format as 12.12
    if isinstance(val, (float, np.float64)):
        return f"{val:.2f}"
    
    # 3. Integers -> Format as 12
    if isinstance(val, (int, np.int64)):
        return f"{val}"
    
    return str(val)

# ==========================================
# 5. MAIN APPLICATION
# ==========================================
if check_password():
    
    with st.sidebar:
        st.markdown("### 👤 User Profile")
        st.success(f"**Welcome, {st.session_state.get('user_name', 'User')}**")
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            del st.session_state["password_correct"]
            st.rerun()
        st.markdown("---")
        st.info("💡 **Optimization Active:**\nCalculation engine updated for faster performance.")

    if "data" in st.secrets and "url" in st.secrets["data"]:
        DATA_URL = st.secrets["data"]["url"]
    else:
        st.error("⚠️ Data URL missing in secrets.")
        st.stop()

    with st.spinner("🔄 Fetching and processing data..."):
        df, error = process_uploaded_file(DATA_URL)

    if error:
        st.error(f"❌ Error: {error}")
    else:
        # Header
        st.markdown(f"""
            <div class="dashboard-header">
                <h1 class="dashboard-title">🏦 Branch Risk Analytics Platform</h1>
                <p class="dashboard-subtitle">Real-time Risk Assessment & Portfolio Management | Last Updated: {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive Dashboard", "🎯 Branch Analytics","🔍 Attribute Filter"])

        # TAB 1: EXECUTIVE
        with tab1:
            col1, col2, col3, col4, col5 = st.columns(5)
            total_branches = len(df)
            with col1: st.metric("📍 Total Branches", f"{total_branches:,}")
            with col2: st.metric("📊 Average Score", f"{df['Total Score'].mean():.2f}")
            with col3: st.metric("🟢 Low Risk (A)", f"{len(df[df['Final Grade'] == 'A'])}")
            with col4: st.metric("🟡 Medium Risk (B)", f"{len(df[df['Final Grade'] == 'B'])}")
            with col5: st.metric("🔴 High Risk (C)", f"{len(df[df['Final Grade'] == 'C'])}")

            st.markdown("<br>", unsafe_allow_html=True)
            col_left, col_right = st.columns([1, 2])
            
            with col_left:
                st.markdown('<div class="chart-card"><div class="chart-title">🎯 Risk Grade Distribution</div>', unsafe_allow_html=True)
                grade_counts = df['Final Grade'].value_counts()
                fig_pie = go.Figure(data=[go.Pie(labels=grade_counts.index, values=grade_counts.values, hole=0.5, marker=dict(colors=['#10b981', '#f59e0b', '#ef4444']))])
                fig_pie.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_right:
                st.markdown('<div class="chart-card"><div class="chart-title">📊 Risk Score Distribution</div>', unsafe_allow_html=True)
                df_sorted = df.sort_values('Total Score')
                fig_bar = go.Figure()
                for grade in ['A', 'B', 'C']:
                    grade_data = df_sorted[df_sorted['Final Grade'] == grade]
                    fig_bar.add_trace(go.Bar(x=grade_data['Total Score'], y=grade_data['BranchCode'], orientation='h', name=f'Grade {grade}', marker=dict(color=get_grade_color(grade)['primary'])))
                fig_bar.update_layout(height=400, barmode='overlay', xaxis_title='Risk Score', yaxis_title='Branch Code')
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

        # TAB 2: BRANCH ANALYTICS
        with tab2:
            st.markdown("### 🎯 Individual Branch Deep-Dive Analysis")
            
            col_select_container, col_rest = st.columns([1, 3])
            with col_select_container:
                branch_list = sorted(df['BranchCode'].unique())
                selected_branch = st.selectbox("🔍 Select Branch Code", branch_list)
            
            branch_data = df[df['BranchCode'] == selected_branch].iloc[0]
            grade = branch_data['Final Grade']
            color_scheme = get_grade_color(grade)

            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"<div style='background:white;padding:1.5rem;border-radius:12px;border-left:4px solid {color_scheme['primary']};text-align:center;'><b>Total Risk Score</b><div style='font-size:2.5rem;'>{branch_data['Total Score']:.2f}</div></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='background:white;padding:1.5rem;border-radius:12px;border-left:4px solid {color_scheme['primary']};text-align:center;'><b>Risk Grade</b><div style='font-size:2.5rem;color:{color_scheme['primary']}'>{grade}</div></div>", unsafe_allow_html=True)
            with col3:
                percentile = (df['Total Score'] < branch_data['Total Score']).sum() / len(df) * 100
                st.markdown(f"<div style='background:white;padding:1.5rem;border-radius:12px;border-left:4px solid {color_scheme['primary']};text-align:center;'><b>Percentile Rank</b><div style='font-size:2.5rem;'>{percentile:.0f}%</div></div>", unsafe_allow_html=True)
            with col4:
                status_text = 'LOW RISK' if grade == 'A' else 'MEDIUM RISK' if grade == 'B' else 'HIGH RISK'
                st.markdown(f"<div style='background:white;padding:1.5rem;border-radius:12px;border-left:4px solid {color_scheme['primary']};text-align:center;'><b>Risk Status</b><div style='margin-top:0.5rem;font-weight:bold;'>{status_text}</div></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col_radar, col_breakdown = st.columns([1.2, 1])
            
            score_cols = [c for c in df.columns if c.endswith(" Score") and c != "Total Score"]
            scores = [branch_data[c] for c in score_cols]
            params = [c.replace(" Score", "") for c in score_cols]

            with col_radar:
                st.markdown('<div class="chart-card"><div class="chart-title">🎯 Risk Parameter Breakdown</div>', unsafe_allow_html=True)
                fig_radar = go.Figure(go.Scatterpolar(r=scores, theta=params, fill='toself', line=dict(color=color_scheme['primary'])))
                max_score = df[score_cols].max().max()
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max_score+5])), height=450, margin=dict(l=80, r=80, t=40, b=40))
                st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_breakdown:
                st.markdown('<div class="chart-card"><div class="chart-title">📊 Score Breakdown</div>', unsafe_allow_html=True)
                # MODIFICATION: Pass column name to format_value
                param_data = [{'Parameter': p, 'Actual': format_value(branch_data.get(p, 'N/A'), p), 'Score': f"{s:.2f}"} for p, s in zip(params, scores)]
                st.dataframe(pd.DataFrame(param_data), use_container_width=True, hide_index=True, height=390)
                st.markdown('</div>', unsafe_allow_html=True)

       
        # TAB 4: ATTRIBUTE FILTER
        with tab4:
            st.markdown("### 🔍 Filter by Attributes")
            all_columns = df.columns.tolist()
            selected_attr = st.selectbox("Select Attribute", all_columns, key="attr_select")
            
            if selected_attr:
                filtered_attr_df = df.copy()
                if pd.api.types.is_numeric_dtype(df[selected_attr]):
                    min_val, max_val = float(df[selected_attr].min()), float(df[selected_attr].max())
                    c1, c2 = st.columns(2)
                    min_input = c1.number_input(f"Min {selected_attr}", value=min_val)
                    max_input = c2.number_input(f"Max {selected_attr}", value=max_val)
                    filtered_attr_df = df[(df[selected_attr] >= min_input) & (df[selected_attr] <= max_input)]
                else:
                    unique_vals = df[selected_attr].astype(str).unique().tolist()
                    selected_vals = st.multiselect(f"Select Values for {selected_attr}", unique_vals, default=unique_vals)
                    if selected_vals: filtered_attr_df = df[df[selected_attr].astype(str).isin(selected_vals)]
                    else: filtered_attr_df = pd.DataFrame(columns=df.columns)

                st.markdown("---")
                if not filtered_attr_df.empty:
                    st.markdown(f"**Found {len(filtered_attr_df)} records**")
                    
                    # MODIFICATION: Dynamic Formatting for Attribute Table
                    attr_format_dict = {}
                    for col in filtered_attr_df.columns:
                        # Apply % formatting ONLY if '%' in name AND 'Score' NOT in name
                        if "%" in col and "Score" not in col:
                            attr_format_dict[col] = "{:.2%}"
                        elif pd.api.types.is_float_dtype(filtered_attr_df[col]):
                            attr_format_dict[col] = "{:.2f}"
                        elif pd.api.types.is_integer_dtype(filtered_attr_df[col]):
                            attr_format_dict[col] = "{:.0f}"

                    st.dataframe(filtered_attr_df.style.format(attr_format_dict), use_container_width=True, height=600)
                else:
                    st.warning("No records found.")
