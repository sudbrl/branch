import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import hmac

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
    
    div[data-testid="stMetric"] label {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-right: 1px solid #e2e8f0;
    }
    
    section[data-testid="stSidebar"] > div {
        padding-top: 2rem;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
        color: #64748b;
        border: none;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
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
    
    .badge-success {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    .badge-warning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    }
    
    .badge-danger {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
    }
    
    /* DataFrame Styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. AUTHENTICATION SYSTEM
# ==========================================
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        try:
            if "credentials" not in st.secrets:
                st.error("⚠️ Authentication not configured. Please add credentials to Streamlit secrets.")
                return
            
            if "username" not in st.secrets["credentials"] or "password" not in st.secrets["credentials"]:
                st.error("⚠️ Missing username or password in secrets configuration.")
                return
            
            if hmac.compare_digest(st.session_state["username"], st.secrets["credentials"]["username"]) and \
               hmac.compare_digest(st.session_state["password"], st.secrets["credentials"]["password"]):
                st.session_state["password_correct"] = True
                st.session_state["user_name"] = st.secrets["credentials"].get("name", "User")
                st.session_state["user_role"] = st.secrets["credentials"].get("role", "Administrator")
                del st.session_state["password"]  # Don't store password
                del st.session_state["username"]  # Don't store username
            else:
                st.session_state["password_correct"] = False
        except Exception as e:
            st.error(f"⚠️ Authentication error: {str(e)}")
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show login screen
        if "credentials" not in st.secrets:
            st.warning("⚠️ Secrets not found. Please create .streamlit/secrets.toml")
            st.stop()
        
        st.markdown("""
            <div style='text-align: center; padding: 2rem 0;'>
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            width: 120px; height: 120px; border-radius: 30px; 
                            margin: 0 auto 2rem auto; display: flex; align-items: center; 
                            justify-content: center; box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);'>
                    <span style='font-size: 4rem;'>🏦</span>
                </div>
                <h1 style='color: #1e293b; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;'>
                    Branch Risk Analytics Platform
                </h1>
                <p style='color: #64748b; font-size: 1.1rem; margin-bottom: 3rem;'>
                    Enterprise-Grade Risk Assessment & Portfolio Management
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("""
                <div style='background: white; padding: 3rem 2.5rem; border-radius: 16px; 
                            box-shadow: 0 10px 40px rgba(0,0,0,0.1); border-top: 4px solid #667eea;'>
                    <h2 style='color: #1e293b; text-align: center; margin-bottom: 2rem; font-size: 1.8rem;'>
                        🔐 Secure Login
                    </h2>
                </div>
            """, unsafe_allow_html=True)
            
            st.text_input("👤 Username", key="username", placeholder="Enter your username")
            st.text_input("🔑 Password", type="password", key="password", placeholder="Enter your password")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                st.button("Login", on_click=password_entered, use_container_width=True)
            
            if st.session_state.get("password_correct") is False:
                st.error("❌ Invalid username or password")

            st.markdown("""
                <div style='text-align: center; margin-top: 2rem; padding-top: 1.5rem; 
                            border-top: 1px solid #e2e8f0;'>
                    <p style='color: #94a3b8; font-size: 0.9rem;'>
                        🔒 Secured by enterprise-grade authentication
                    </p>
                </div>
            """, unsafe_allow_html=True)
        return False
    
    elif not st.session_state["password_correct"]:
        st.session_state["password_correct"] = None
        st.rerun()
        return False
    else:
        return True

# ==========================================
# 4. MAIN APPLICATION
# ==========================================
if check_password():
    
    # ------------------------------------------
    # 4.1. SIDEBAR PROFILE
    # ------------------------------------------
    with st.sidebar:
        st.markdown("### 👤 User Profile")
        st.success(f"**Welcome, {st.session_state.get('user_name', 'User')}**")
        st.caption(f"Role: {st.session_state.get('user_role', 'Admin')}")
        
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            del st.session_state["password_correct"]
            st.rerun()
        st.markdown("---")

    # ------------------------------------------
    # 4.2. CALCULATION ENGINE
    # ------------------------------------------
    def check_condition(data_val, op, rule_val):
        try:
            op = str(op).strip().upper()
            if op in ["ALL", "ELSE"]: return True
            
            try:
                d_num = float(data_val)
                r_num = float(rule_val)
                if op == ">": return d_num > r_num
                if op == "<": return d_num < r_num
                if op in [">=", "=>"]: return d_num >= r_num
                if op in ["<=", "=<"]: return d_num <= r_num
                if op == "=": return d_num == r_num
            except:
                pass 
            
            d_str = str(data_val).upper().strip()
            r_str = str(rule_val).upper().strip()
            if op == "CONTAINS": return r_str in d_str
            if op == "=": return d_str == r_str
            if op == "<>": return d_str != r_str
            return False
        except:
            return False

    def get_grade(score, df_grades):
        try:
            for _, row in df_grades.iterrows():
                if row['Min Score'] <= score <= row['Max Score']:
                    return row['Grade']
        except:
            return "N/A"
        return "N/A"

    @st.cache_data(show_spinner=False)
    def process_uploaded_file(file_path):
        try:
            # Pandas can read directly from URL
            xls = pd.ExcelFile(file_path)
            df_rules = pd.read_excel(xls, "Sheet1")
            df_data = pd.read_excel(xls, "Sheet2", dtype={'BranchCode': str})
            df_grades = pd.read_excel(xls, "Sheet3")
            
            df_rules.columns = [c.strip() for c in df_rules.columns]
            df_data.columns = [c.strip() for c in df_data.columns]
            df_grades.columns = [c.strip() for c in df_grades.columns]
            
            unique_params = df_rules['Column Name'].unique()
            for param in unique_params:
                if param in df_data.columns:
                    df_data[f"{param} Score"] = 0.0
            
            df_data["Total Score"] = 0.0
            
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
            return df_data, None
        except Exception as e:
            return None, str(e)

    def get_grade_color(grade):
        colors = {
            'A': {'primary': '#10b981', 'light': '#d1fae5', 'gradient': 'linear-gradient(135deg, #10b981 0%, #059669 100%)'},
            'B': {'primary': '#f59e0b', 'light': '#fef3c7', 'gradient': 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'},
            'C': {'primary': '#ef4444', 'light': '#fee2e2', 'gradient': 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'}
        }
        return colors.get(grade, colors['C'])

    # ------------------------------------------
    # 4.3. SIDEBAR & DATA SOURCE
    # ------------------------------------------
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.info(
        """
        **Branch Risk Analytics Platform**
        
        A comprehensive risk assessment tool for branch portfolio management.
        
        - Real-time risk scoring
        - Multi-parameter analysis
        - Grade-based classification
        - Interactive visualizations
        """
    )

    # ------------------------------------------
    # 4.4. LOAD DATA FROM SECRETS
    # ------------------------------------------
    # Retrieve URL from secrets instead of hardcoding
    if "data" in st.secrets and "url" in st.secrets["data"]:
        DATA_URL = st.secrets["data"]["url"]
    else:
        st.error("⚠️ **Configuration Error:** Data URL not found in secrets.")
        st.info("Please add `[data] url = '...'` to your `.streamlit/secrets.toml` file.")
        st.stop()

    # ------------------------------------------
    # 4.5. DASHBOARD RENDER
    # ------------------------------------------

    with st.spinner("🔄 Fetching and processing risk data..."):
        df, error = process_uploaded_file(DATA_URL)

    if error:
        st.error(f"❌ **Error processing file:** {error}")
    else:
        # Header
        st.markdown(f"""
            <div class="dashboard-header">
                <h1 class="dashboard-title">🏦 Branch Risk Analytics Platform</h1>
                <p class="dashboard-subtitle">Real-time Risk Assessment & Portfolio Management | Last Updated: {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["📊 Executive Dashboard", "🎯 Branch Analytics", "📈 Detailed Reports"])

        # ==========================================
        # TAB 1: EXECUTIVE OVERVIEW
        # ==========================================
        with tab1:
            # KPI Metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            total_branches = len(df)
            avg_score = df['Total Score'].mean()
            high_risk = len(df[df['Final Grade'] == 'C'])
            medium_risk = len(df[df['Final Grade'] == 'B'])
            low_risk = len(df[df['Final Grade'] == 'A'])
            
            with col1:
                st.metric("📍 Total Branches", f"{total_branches:,}")
            with col2:
                st.metric("📊 Average Score", f"{avg_score:.2f}")
            with col3:
                st.metric("🟢 Low Risk (A)", f"{low_risk}", delta=f"{(low_risk/total_branches*100):.1f}%")
            with col4:
                st.metric("🟡 Medium Risk (B)", f"{medium_risk}", delta=f"{(medium_risk/total_branches*100):.1f}%")
            with col5:
                st.metric("🔴 High Risk (C)", f"{high_risk}", delta=f"-{(high_risk/total_branches*100):.1f}%", delta_color="inverse")

            st.markdown("<br>", unsafe_allow_html=True)

            # Risk Distribution Section
            col_left, col_right = st.columns([1, 2])
            
            with col_left:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown('<div class="chart-title">🎯 Risk Grade Distribution</div>', unsafe_allow_html=True)
                
                grade_counts = df['Final Grade'].value_counts()
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=grade_counts.index,
                    values=grade_counts.values,
                    hole=0.5,
                    marker=dict(
                        colors=['#10b981', '#f59e0b', '#ef4444'],
                        line=dict(color='white', width=3)
                    ),
                    textinfo='label+percent',
                    textfont=dict(size=14, color='white', family='Arial Black'),
                    hovertemplate='<b>Grade %{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
                )])
                
                fig_pie.update_layout(
                    showlegend=True,
                    height=400,
                    margin=dict(t=20, b=20, l=20, r=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.1,
                        font=dict(size=12)
                    ),
                    annotations=[dict(
                        text=f'<b>{total_branches}</b><br>Branches',
                        x=0.5, y=0.5,
                        font=dict(size=20, color='#1e293b'),
                        showarrow=False
                    )]
                )
                
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_right:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown('<div class="chart-title">📊 Risk Score Distribution by Branch</div>', unsafe_allow_html=True)
                
                df_sorted = df.sort_values('Total Score', ascending=True)
                
                fig_bar = go.Figure()
                
                for grade in ['A', 'B', 'C']:
                    grade_data = df_sorted[df_sorted['Final Grade'] == grade]
                    color = get_grade_color(grade)['primary']
                    
                    fig_bar.add_trace(go.Bar(
                        x=grade_data['Total Score'],
                        y=grade_data['BranchCode'],
                        orientation='h',
                        name=f'Grade {grade}',
                        marker=dict(
                            color=color,
                            line=dict(color='white', width=1)
                        ),
                        hovertemplate='<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>'
                    ))
                
                fig_bar.update_layout(
                    xaxis=dict(
                        title='Risk Score',
                        tickformat='.2f',
                        gridcolor='#e2e8f0',
                        showgrid=True
                    ),
                    yaxis=dict(
                        title='Branch Code',
                        gridcolor='#e2e8f0'
                    ),
                    height=400,
                    barmode='overlay',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    hovermode='closest'
                )
                
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            # Score Distribution Histogram
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">📈 Score Distribution Analysis</div>', unsafe_allow_html=True)
            
            fig_hist = go.Figure()
            
            fig_hist.add_trace(go.Histogram(
                x=df['Total Score'],
                nbinsx=30,
                marker=dict(
                    color=df['Total Score'],
                    colorscale=[[0, '#ef4444'], [0.5, '#f59e0b'], [1, '#10b981']],
                    line=dict(color='white', width=1)
                ),
                hovertemplate='Score Range: %{x}<br>Frequency: %{y}<extra></extra>'
            ))
            
            fig_hist.update_layout(
                xaxis=dict(title='Risk Score', tickformat='.2f', gridcolor='#e2e8f0'),
                yaxis=dict(title='Number of Branches', gridcolor='#e2e8f0'),
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False
            )
            
            st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        # ==========================================
        # TAB 2: BRANCH ANALYSIS
        # ==========================================
        with tab2:
            st.markdown("### 🎯 Individual Branch Deep-Dive Analysis")
            
            col_select, col_filter = st.columns([2, 1])
            
            with col_select:
                branch_list = sorted(df['BranchCode'].unique())
                selected_branch = st.selectbox(
                    "🔍 Select Branch Code",
                    branch_list,
                    index=0
                )
            
            with col_filter:
                filter_grade = st.multiselect(
                    "Filter by Grade",
                    options=['All', 'A', 'B', 'C'],
                    default=['All'],
                    key="tab2_grade_filter"
                )
                
                if 'All' in filter_grade or not filter_grade:
                    filter_grade = ['A', 'B', 'C']
            
            branch_data = df[df['BranchCode'] == selected_branch].iloc[0]
            grade = branch_data['Final Grade']
            color_scheme = get_grade_color(grade)

            st.markdown("<br>", unsafe_allow_html=True)

            # Branch Overview Cards
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                    <div style='background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center; border-left: 4px solid {color_scheme["primary"]};'>
                        <div style='color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;'>Total Risk Score</div>
                        <div style='color: #1e293b; font-size: 2.5rem; font-weight: 700;'>{branch_data['Total Score']:.2f}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div style='background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center; border-left: 4px solid {color_scheme["primary"]};'>
                        <div style='color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;'>Risk Grade</div>
                        <div style='color: {color_scheme["primary"]}; font-size: 2.5rem; font-weight: 700;'>{grade}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                percentile = (df['Total Score'] < branch_data['Total Score']).sum() / len(df) * 100
                st.markdown(f"""
                    <div style='background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center; border-left: 4px solid {color_scheme["primary"]};'>
                        <div style='color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;'>Percentile Rank</div>
                        <div style='color: #1e293b; font-size: 2.5rem; font-weight: 700;'>{percentile:.0f}%</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                badge_class = 'badge-success' if grade == 'A' else 'badge-warning' if grade == 'B' else 'badge-danger'
                status_text = 'LOW RISK' if grade == 'A' else 'MEDIUM RISK' if grade == 'B' else 'HIGH RISK'
                st.markdown(f"""
                    <div style='background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center; border-left: 4px solid {color_scheme["primary"]};'>
                        <div style='color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;'>Risk Status</div>
                        <div class='status-badge {badge_class}' style='margin-top: 0.5rem;'>{status_text}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Parameter Analysis
            col_radar, col_breakdown = st.columns([1.2, 1])
            
            with col_radar:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown('<div class="chart-title">🎯 Risk Parameter Breakdown</div>', unsafe_allow_html=True)
                
                score_cols = [c for c in df.columns if c.endswith("Score") and c != "Total Score"]
                scores = [branch_data[c] for c in score_cols]
                params = [c.replace(" Score", "") for c in score_cols]

                fig_radar = go.Figure()
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=scores,
                    theta=params,
                    fill='toself',
                    name=f'Branch {selected_branch}',
                    line=dict(color=color_scheme['primary'], width=3),
                    fillcolor=f"rgba({int(color_scheme['primary'][1:3], 16)}, {int(color_scheme['primary'][3:5], 16)}, {int(color_scheme['primary'][5:7], 16)}, 0.3)",
                    hovertemplate='<b>%{theta}</b><br>Score: %{r:.2f}<extra></extra>'
                ))

                max_score = df[score_cols].max().max()
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            tickformat=".2f",
                            range=[0, max_score + 5],
                            gridcolor='#e2e8f0',
                            tickfont=dict(size=10)
                        ),
                        angularaxis=dict(
                            gridcolor='#e2e8f0',
                            tickfont=dict(size=11, color='#1e293b', family='Arial')
                        ),
                        bgcolor='rgba(0,0,0,0)'
                    ),
                    showlegend=False,
                    height=450,
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=80, r=80, t=40, b=40)
                )

                st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_breakdown:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown('<div class="chart-title">📊 Score Breakdown</div>', unsafe_allow_html=True)
                
                # Create parameter breakdown table with actual values
                param_data = []
                for col, param in zip(score_cols, params):
                    score = branch_data[col]
                    contribution = (score / branch_data['Total Score'] * 100) if branch_data['Total Score'] > 0 else 0
                    
                    actual_value = branch_data.get(param, 'N/A')
                    
                    if isinstance(actual_value, (int, float)):
                        actual_display = f"{actual_value:.2f}"
                    else:
                        actual_display = str(actual_value)
                    
                    param_data.append({
                        'Parameter': param,
                        'Actual Value': actual_display,
                        'Score': f"{score:.2f}",
                        'Weight': f"{contribution:.1f}%"
                    })
                
                param_df = pd.DataFrame(param_data)
                
                st.dataframe(
                    param_df,
                    use_container_width=True,
                    hide_index=True,
                    height=390
                )
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Comparison with Portfolio Average
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">📊 Comparison with Portfolio Average</div>', unsafe_allow_html=True)
            
            avg_scores = [df[col].mean() for col in score_cols]
            
            fig_compare = go.Figure()
            
            fig_compare.add_trace(go.Bar(
                x=params,
                y=scores,
                name=f'Branch {selected_branch}',
                marker=dict(color=color_scheme['primary'], line=dict(color='white', width=1)),
                hovertemplate='<b>%{x}</b><br>Score: %{y:.2f}<extra></extra>'
            ))
            
            fig_compare.add_trace(go.Bar(
                x=params,
                y=avg_scores,
                name='Portfolio Average',
                marker=dict(color='#94a3b8', line=dict(color='white', width=1)),
                hovertemplate='<b>%{x}</b><br>Avg Score: %{y:.2f}<extra></extra>'
            ))
            
            fig_compare.update_layout(
                barmode='group',
                xaxis=dict(title='Risk Parameters', gridcolor='#e2e8f0'),
                yaxis=dict(title='Score', tickformat='.2f', gridcolor='#e2e8f0'),
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_compare, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        # ==========================================
        # TAB 3: DETAILED REPORTS
        # ==========================================
        with tab3:
            st.markdown("### 📈 Comprehensive Portfolio Data")
            
            col_grade, col_search, col_export = st.columns([1, 2, 1])
            
            with col_grade:
                grade_filter = st.multiselect(
                    "Filter by Grade",
                    options=['All', 'A', 'B', 'C'],
                    default=['All'],
                    key="tab3_grade_filter"
                )
                
                if 'All' in grade_filter or not grade_filter:
                    grade_filter = ['A', 'B', 'C']
            
            with col_search:
                search_term = st.text_input("🔍 Search Branch Code", "")
            
            # Apply filters
            filtered_df = df[df['Final Grade'].isin(grade_filter)]
            if search_term:
                branch_exists = df['BranchCode'].str.contains(search_term, case=False).any()
                if not branch_exists:
                    st.warning(f"⚠️ Branch Code '{search_term}' not found in the dataset.")
                
                filtered_df = filtered_df[filtered_df['BranchCode'].str.contains(search_term, case=False)]
            
            # Summary Statistics
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Filtered Branches", len(filtered_df))
            if len(filtered_df) > 0:
                col2.metric("Avg Score", f"{filtered_df['Total Score'].mean():.2f}")
                col3.metric("Min Score", f"{filtered_df['Total Score'].min():.2f}")
                col4.metric("Max Score", f"{filtered_df['Total Score'].max():.2f}")
            else:
                col2.metric("Avg Score", "N/A")
                col3.metric("Min Score", "N/A")
                col4.metric("Max Score", "N/A")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Data Table
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            
            if not filtered_df.empty:
                display_df = filtered_df.copy()
                numeric_cols = display_df.select_dtypes(include=['float64', 'int64']).columns
                
                def highlight_grade(row):
                    if row['Final Grade'] == 'A':
                        return ['background-color: #d1fae5'] * len(row)
                    elif row['Final Grade'] == 'B':
                        return ['background-color: #fef3c7'] * len(row)
                    elif row['Final Grade'] == 'C':
                        return ['background-color: #fee2e2'] * len(row)
                    return [''] * len(row)
                
                styled_df = display_df.style.format(
                    {col: "{:.2f}" for col in numeric_cols}
                ).apply(highlight_grade, axis=1)
                
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    height=500
                )
            else:
                st.info("No data available for the selected filters.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download Section
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 💾 Export Data")
            
            col1, col2 = st.columns(2)
            with col1:
                if not filtered_df.empty:
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"branch_risk_report_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                    )
                else:
                    st.download_button(
                        label="📥 Download CSV",
                        data="",
                        disabled=True,
                        file_name="empty.csv"
                    )
            
            with col2:
                st.info(f"📊 Dataset contains {len(filtered_df)} branches with {len(filtered_df.columns)} attributes")
