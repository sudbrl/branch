import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import hmac
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    /* ... (keep your existing CSS) ... */
    .error-message {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ef4444;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. AUTHENTICATION SYSTEM
# ==========================================
def check_password():
    """Returns True if user is authenticated."""
    def password_entered():
        try:
            if "credentials" not in st.secrets:
                st.error("⚠️ Authentication not configured in secrets.")
                st.stop()
            
            username = st.session_state["username"]
            password = st.session_state["password"]
            
            if hmac.compare_digest(username, st.secrets["credentials"]["username"]) and \
               hmac.compare_digest(password, st.secrets["credentials"]["password"]):
                st.session_state["password_correct"] = True
                st.session_state["user_name"] = st.secrets["credentials"].get("name", "User")
                st.session_state["user_role"] = st.secrets["credentials"].get("role", "Administrator")
                logger.info(f"User {username} logged in successfully")
                # Clear password from memory
                del st.session_state["password"]
            else:
                st.session_state["password_correct"] = False
                logger.warning(f"Failed login attempt for user {username}")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            st.error(f"⚠️ System Error: {str(e)}")

    if st.session_state.get("password_correct", False):
        return True

    # Show login form
    st.markdown("""<div style='text-align: center; padding: 2rem 0;'><h1>Branch Risk Analytics</h1></div>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.text_input("👤 Username", key="username")
        st.text_input("🔑 Password", type="password", key="password")
        st.button("Login", on_click=password_entered, use_container_width=True)
        
        if st.session_state.get("password_correct") is False:
            st.error("❌ Invalid credentials")
            st.session_state.pop("password_correct", None)  # Reset error state
    
    return False

# ==========================================
# 4. ENHANCED CALCULATION ENGINE
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def process_uploaded_file(file_path):
    """Process Excel file with validation and error handling."""
    try:
        logger.info(f"Loading data from {file_path}")
        xls = pd.ExcelFile(file_path)
        
        # Validate sheets exist
        required_sheets = ["Sheet1", "Sheet2", "Sheet3"]
        missing = [s for s in required_sheets if s not in xls.sheet_names]
        if missing:
            raise ValueError(f"Missing required sheets: {', '.join(missing)}")
        
        # Load with validation
        df_rules = pd.read_excel(xls, "Sheet1")
        df_data = pd.read_excel(xls, "Sheet2", dtype={'BranchCode': str})
        df_grades = pd.read_excel(xls, "Sheet3")
        
        # Validate required columns
        _validate_columns(df_rules, ["Column Name", "Operator", "Value", "Score"], "Rules")
        _validate_columns(df_grades, ["Grade", "Min Score", "Max Score"], "Grades")
        
        # Clean column names
        df_rules.columns = df_rules.columns.str.strip()
        df_data.columns = df_data.columns.str.strip()
        df_grades.columns = df_grades.columns.str.strip()
        
        # Apply rules
        df_data = apply_rules_vectorized(df_data, df_rules)
        
        # Apply grades with non-overlapping ranges
        df_data["Final Grade"] = df_data["Total Score"].apply(
            lambda x: _get_grade_safe(x, df_grades)
        )
        
        logger.info(f"Successfully processed {len(df_data)} branches")
        return df_data, None
        
    except Exception as e:
        logger.error(f"Data processing error: {str(e)}")
        return None, str(e)

def _validate_columns(df, required_cols, sheet_name):
    """Validate required columns exist in dataframe."""
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Sheet '{sheet_name}' missing columns: {', '.join(missing)}")

def _get_grade_safe(score, df_grades):
    """Get grade with validation to prevent overlap."""
    try:
        for _, row in df_grades.iterrows():
            # Use half-open interval: min <= score < max
            if row['Min Score'] <= score < row['Max Score']:
                return row['Grade']
        return "N/A"
    except:
        return "N/A"

def apply_rules_vectorized(df, df_rules):
    """Vectorized rule application with performance optimization."""
    unique_params = df_rules['Column Name'].unique()
    
    # Pre-allocate score columns
    score_cols = [f"{param} Score" for param in unique_params if param in df.columns]
    df[score_cols] = 0.0
    
    # Cache for parsed rules
    rule_cache = {}
    
    for param in unique_params:
        if param not in df.columns:
            logger.warning(f"Parameter '{param}' not found in data columns")
            continue
        
        param_rules = df_rules[df_rules['Column Name'] == param].copy()
        
        # Process rules in order of specificity (most specific first)
        param_rules['is_else'] = param_rules['Operator'].str.upper().isin(['ALL', 'ELSE'])
        param_rules = param_rules.sort_values(['is_else', 'Score'], ascending=[True, False])
        
        # Get column data once
        col_data = df[param]
        
        # Track assigned rows
        assigned_mask = pd.Series(False, index=df.index)
        
        for _, rule in param_rules.iterrows():
            try:
                score = float(rule['Score'])
                mask = _evaluate_rule(rule, col_data, assigned_mask)
                
                # Apply score to unassigned rows
                update_mask = mask & (~assigned_mask)
                if update_mask.any():
                    df.loc[update_mask, f"{param} Score"] = score
                    assigned_mask |= update_mask
                    
            except Exception as e:
                logger.warning(f"Rule error for {param}: {str(e)}")
                continue
    
    # Calculate total score
    df["Total Score"] = df[score_cols].sum(axis=1, min_count=1)  # min_count avoids all-NaN warning
    return df

def _evaluate_rule(rule, col_data, assigned_mask):
    """Evaluate a single rule and return boolean mask."""
    op = str(rule['Operator']).strip().upper()
    val = rule['Value']
    
    # Handle special operators
    if op in ["ALL", "ELSE"]:
        return pd.Series(True, index=col_data.index)
    
    # Type conversion
    col_numeric = pd.to_numeric(col_data, errors='coerce')
    is_numeric = col_numeric.notna().any()
    
    if is_numeric and op not in ["=", "<>", "CONTAINS"]:
        try:
            val_num = float(val)
            if op == ">": return col_numeric > val_num
            elif op == "<": return col_numeric < val_num
            elif op == ">=": return col_numeric >= val_num
            elif op == "<=": return col_numeric <= val_num
            elif op == "=": return col_numeric == val_num
        except:
            return pd.Series(False, index=col_data.index)
    else:
        # String operations
        col_str = col_data.astype(str).str.upper().str.strip()
        val_str = str(val).upper().strip()
        
        if op == "=": return col_str == val_str
        elif op == "<>": return col_str != val_str
        elif op == "CONTAINS": return col_str.contains(val_str, na=False)
    
    return pd.Series(False, index=col_data.index)

def get_grade_color(grade):
    """Get color scheme for risk grade."""
    colors = {
        'A': {'primary': '#10b981', 'light': '#d1fae5'},
        'B': {'primary': '#f59e0b', 'light': '#fef3c7'},
        'C': {'primary': '#ef4444', 'light': '#fee2e2'}
    }
    return colors.get(grade, colors['C'])

def format_value(val, col_name=""):
    """Smart value formatting."""
    # Only format as percentage if '%' in name but NOT a score column
    if "%" in str(col_name) and "Score" not in str(col_name) and \
       isinstance(val, (int, float, np.number)) and not pd.isna(val):
        return f"{val:.2%}"
    
    # Standard number formatting
    if isinstance(val, (float, np.floating)) and not pd.isna(val):
        return f"{val:.2f}"
    if isinstance(val, (int, np.integer)):
        return f"{val:,}"
    
    return "N/A" if pd.isna(val) else str(val)

# ==========================================
# 5. MAIN APPLICATION
# ==========================================
def main():
    if not check_password():
        return

    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 User Profile")
        st.success(f"**Welcome, {st.session_state['user_name']}**")
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        st.info("💡 **Optimization Active:**\nVectorized calculations with 1-hour cache")

    # Load data
    if "data" not in st.secrets or "url" not in st.secrets["data"]:
        st.error("⚠️ Data URL not configured in secrets")
        st.stop()

    DATA_URL = st.secrets["data"]["url"]
    
    with st.spinner("🔄 Fetching and processing data..."):
        df, error = process_uploaded_file(DATA_URL)

    if error:
        st.markdown(f'<div class="error-message">❌ Data Loading Error: {error}</div>', unsafe_allow_html=True)
        logger.error(f"Data loading failed: {error}")
        st.stop()

    # Header
    st.markdown(f"""
        <div class="dashboard-header">
            <h1 class="dashboard-title">🏦 Branch Risk Analytics Platform</h1>
            <p class="dashboard-subtitle">
                Real-time Risk Assessment & Portfolio Management | 
                Last Updated: {datetime.now().strftime('%B %d, %Y %H:%M:%S')}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Display data freshness
    st.sidebar.caption(f"Data loaded: {datetime.now().strftime('%H:%M:%S')}")
    
    # TABS
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Executive Dashboard", 
        "🎯 Branch Analytics", 
        "📈 Detailed Reports", 
        "🔍 Attribute Filter"
    ])

    # TAB 1: EXECUTIVE DASHBOARD
    with tab1:
        _render_executive_dashboard(df)

    # TAB 2: BRANCH ANALYTICS
    with tab2:
        _render_branch_analytics(df)

    # TAB 3: REPORTS
    with tab3:
        _render_reports(df)

    # TAB 4: ATTRIBUTE FILTER
    with tab4:
        _render_attribute_filter(df)

def _render_executive_dashboard(df):
    """Render executive summary metrics and charts."""
    col1, col2, col3, col4, col5 = st.columns(5)
    total_branches = len(df)
    
    with col1: st.metric("📍 Total Branches", f"{total_branches:,}")
    with col2: st.metric("📊 Average Score", f"{df['Total Score'].mean():.2f}")
    with col3: st.metric("🟢 Low Risk (A)", f"{len(df[df['Final Grade'] == 'A']):,}")
    with col4: st.metric("🟡 Medium Risk (B)", f"{len(df[df['Final Grade'] == 'B']):,}")
    with col5: st.metric("🔴 High Risk (C)", f"{len(df[df['Final Grade'] == 'C']):,}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1, 2])
    
    # Grade Distribution Pie Chart
    with col_left:
        st.markdown('<div class="chart-card"><div class="chart-title">🎯 Risk Grade Distribution</div>', unsafe_allow_html=True)
        grade_counts = df['Final Grade'].value_counts().sort_index()
        fig_pie = go.Figure(data=[go.Pie(
            labels=grade_counts.index, 
            values=grade_counts.values, 
            hole=0.5,
            marker=dict(colors=['#10b981', '#f59e0b', '#ef4444'])
        )])
        fig_pie.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Risk Score Distribution
    with col_right:
        st.markdown('<div class="chart-card"><div class="chart-title">📊 Risk Score Distribution</div>', unsafe_allow_html=True)
        df_sorted = df.sort_values('Total Score', ascending=True)
        fig_bar = go.Figure()
        
        for grade in ['A', 'B', 'C']:
            grade_data = df_sorted[df_sorted['Final Grade'] == grade]
            if not grade_data.empty:
                fig_bar.add_trace(go.Bar(
                    x=grade_data['Total Score'], 
                    y=grade_data['BranchCode'], 
                    orientation='h', 
                    name=f'Grade {grade}', 
                    marker=dict(color=get_grade_color(grade)['primary'])
                ))
        
        fig_bar.update_layout(
            height=400, 
            barmode='overlay', 
            xaxis_title='Risk Score', 
            yaxis_title='Branch Code'
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

def _render_branch_analytics(df):
    """Render individual branch analysis."""
    st.markdown("### 🎯 Individual Branch Deep-Dive Analysis")
    
    col_select, col_rest = st.columns([1, 3])
    with col_select:
        branch_list = sorted(df['BranchCode'].unique())
        selected_branch = st.selectbox("🔍 Select Branch Code", branch_list)
    
    # Validate branch exists
    branch_mask = df['BranchCode'] == selected_branch
    if not branch_mask.any():
        st.error(f"❌ Branch {selected_branch} not found")
        return
    
    branch_data = df[branch_mask].iloc[0]
    grade = branch_data['Final Grade']
    color_scheme = get_grade_color(grade)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Risk Score", f"{branch_data['Total Score']:.2f}", 
                 delta_color="inverse")
    with col2:
        st.metric("Risk Grade", grade, 
                 delta_color="inverse")
    with col3:
        percentile = (df['Total Score'] < branch_data['Total Score']).sum() / len(df) * 100
        st.metric("Percentile Rank", f"{percentile:.0f}%")
    with col4:
        status_text = 'LOW RISK' if grade == 'A' else 'MEDIUM RISK' if grade == 'B' else 'HIGH RISK'
        st.metric("Risk Status", status_text)

    st.markdown("<br>", unsafe_allow_html=True)
    col_radar, col_breakdown = st.columns([1.2, 1])
    
    score_cols = [c for c in df.columns if c.endswith(" Score") and c != "Total Score"]
    scores = [branch_data[c] for c in score_cols]
    params = [c.replace(" Score", "") for c in score_cols]

    # Radar Chart
    with col_radar:
        st.markdown('<div class="chart-card"><div class="chart-title">🎯 Risk Parameter Breakdown</div>', unsafe_allow_html=True)
        max_score = max(df[score_cols].max().max(), max(scores)) + 5
        fig_radar = go.Figure(go.Scatterpolar(
            r=scores, 
            theta=params, 
            fill='toself', 
            line=dict(color=color_scheme['primary'])
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max_score])),
            height=450, 
            margin=dict(l=80, r=80, t=40, b=40)
        )
        st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Score Table
    with col_breakdown:
        st.markdown('<div class="chart-card"><div class="chart-title">📊 Score Breakdown</div>', unsafe_allow_html=True)
        param_data = []
        for p, s in zip(params, scores):
            actual = format_value(branch_data.get(p, np.nan), p)
            param_data.append({'Parameter': p, 'Actual': actual, 'Score': f"{s:.2f}"})
        
        st.dataframe(pd.DataFrame(param_data), use_container_width=True, hide_index=True, height=390)
        st.markdown('</div>', unsafe_allow_html=True)

def _render_reports(df):
    """Render detailed reports with filtering."""
    st.markdown("### 📈 Comprehensive Portfolio Data")
    
    col_grade, col_search, col_export = st.columns([1, 2, 1])
    
    with col_grade:
        grade_filter = st.multiselect(
            "Filter by Grade", 
            ['All', 'A', 'B', 'C'], 
            default=['All']
        )
        if 'All' in grade_filter or not grade_filter:
            grade_filter = ['A', 'B', 'C']
    
    with col_search:
        search_term = st.text_input("🔍 Search Branch Code")
    
    # Apply filters
    filtered_df = df[df['Final Grade'].isin(grade_filter)]
    if search_term:
        filtered_df = filtered_df[filtered_df['BranchCode'].str.contains(search_term, case=False, na=False)]
    
    # Dynamic formatting
    format_dict = _get_format_dict(filtered_df)
    st.dataframe(
        filtered_df.style.format(format_dict), 
        use_container_width=True, 
        height=500
    )
    
    # Export
    if not filtered_df.empty:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV", 
            csv, 
            "risk_report.csv", 
            "text/csv",
            use_container_width=False
        )

def _render_attribute_filter(df):
    """Render attribute-based filtering."""
    st.markdown("### 🔍 Filter by Attributes")
    
    all_columns = df.columns.tolist()
    selected_attr = st.selectbox("Select Attribute", all_columns, key="attr_select")
    
    if not selected_attr:
        return
    
    col_data = df[selected_attr]
    
    if pd.api.types.is_numeric_dtype(col_data):
        # Numeric range filter
        min_val, max_val = float(col_data.min()), float(col_data.max())
        c1, c2 = st.columns(2)
        min_input = c1.number_input(f"Min {selected_attr}", value=min_val)
        max_input = c2.number_input(f"Max {selected_attr}", value=max_val)
        filtered_df = df[(col_data >= min_input) & (col_data <= max_input)]
    else:
        # String filter
        unique_vals = col_data.dropna().astype(str).unique().tolist()
        if not unique_vals:
            st.warning("No values available for this attribute")
            return
        
        selected_vals = st.multiselect(
            f"Select Values for {selected_attr}", 
            unique_vals, 
            default=unique_vals
        )
        if selected_vals:
            filtered_df = df[col_data.astype(str).isin(selected_vals)]
        else:
            filtered_df = pd.DataFrame(columns=df.columns)
    
    st.markdown("---")
    
    if filtered_df.empty:
        st.warning("⚠️ No records found matching your criteria")
        return
    
    st.markdown(f"**Found {len(filtered_df):,} records**")
    format_dict = _get_format_dict(filtered_df)
    st.dataframe(
        filtered_df.style.format(format_dict), 
        use_container_width=True, 
        height=600
    )

def _get_format_dict(df):
    """Generate formatting dictionary for dataframe."""
    format_dict = {}
    for col in df.columns:
        if "%" in col and "Score" not in col:
            format_dict[col] = "{:.2%}"
        elif pd.api.types.is_float_dtype(df[col]):
            format_dict[col] = "{:.2f}"
        elif pd.api.types.is_integer_dtype(df[col]):
            format_dict[col] = "{:,}"
    return format_dict

# ==========================================
# RUN APPLICATION
# ==========================================
if __name__ == "__main__":
    main()
