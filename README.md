# 🏦 Branch Risk Analytics Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

A professional, enterprise-grade risk assessment and portfolio management dashboard for analyzing branch-level risk metrics.

![Dashboard Preview](https://via.placeholder.com/800x400/667eea/ffffff?text=Branch+Risk+Analytics+Dashboard)

## ✨ Features

- 🔐 **Secure Authentication** - Role-based access control
- 📊 **Interactive Dashboards** - Real-time risk visualization
- 🎯 **Multi-Branch Analytics** - Comprehensive portfolio overview
- 📈 **Deep-Dive Analysis** - Individual branch risk breakdown
- 🔍 **Advanced Filtering** - Dynamic data exploration
- 💾 **Data Export** - CSV download capabilities
- 📱 **Responsive Design** - Works on all devices

## 🚀 Quick Start

### Live Demo
Visit: [Your Streamlit App URL](https://your-app-url.streamlit.app)

**Demo Credentials:**
- Username: `admin` | Password: `admin`
- Username: `manager` | Password: `manager123`

### Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/branch-risk-analytics.git
   cd branch-risk-analytics
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure authentication:**
   ```bash
   mkdir .streamlit
   cp secrets.toml.template .streamlit/secrets.toml
   ```
   Edit `.streamlit/secrets.toml` with your credentials

4. **Run the app:**
   ```bash
   streamlit run branch_risk_dashboard.py
   ```

5. **Open browser:**
   Navigate to `http://localhost:8501`

## 📋 Requirements

- Python 3.8+
- Streamlit 1.31.0
- Pandas 2.1.4
- Plotly 5.18.0
- openpyxl 3.1.2

See [requirements.txt](requirements.txt) for complete list.

## 📁 Data Format

Upload an Excel file (.xlsx) with three sheets:

### Sheet 1: Risk Rules Configuration
| Column Name | Operator | Value | Score |
|------------|----------|-------|-------|
| Parameter1 | >        | 100   | 10    |
| Parameter2 | <        | 50    | 5     |

### Sheet 2: Branch Data
| BranchCode | Parameter1 | Parameter2 | ... |
|------------|------------|------------|-----|
| BR001      | 120        | 45         | ... |
| BR002      | 95         | 55         | ... |

### Sheet 3: Grading Criteria
| Grade | Min Score | Max Score |
|-------|-----------|-----------|
| A     | 0         | 30        |
| B     | 31        | 60        |
| C     | 61        | 100       |

## 🎨 Dashboard Views

### 📊 Executive Dashboard
- Portfolio-wide KPIs and metrics
- Risk grade distribution
- Score analysis charts
- Historical trends

### 🎯 Branch Analytics
- Individual branch deep-dive
- Parameter breakdown radar chart
- Comparison with portfolio average
- Percentile rankings

### 📈 Detailed Reports
- Comprehensive data tables
- Advanced filtering options
- Export functionality
- Summary statistics

## 🔐 Security

- SHA-256 password hashing
- Session-based authentication
- Secure secrets management
- Role-based access control

**Important:** Change default passwords before production deployment!

## 🛠️ Configuration

### Adding New Users

1. Generate password hash:
   ```python
   import hashlib
   password = "your_password"
   hash_value = hashlib.sha256(str.encode(password)).hexdigest()
   print(hash_value)
   ```

2. Add to `secrets.toml`:
   ```toml
   [credentials.usernames.newuser]
   name = "User Full Name"
   password = "HASH_VALUE_HERE"
   role = "User Role"
   ```

### Streamlit Cloud Deployment

1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Add secrets in app settings
4. Deploy!

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.

## 📊 Technology Stack

- **Frontend:** Streamlit
- **Data Processing:** Pandas
- **Visualizations:** Plotly
- **Authentication:** hashlib + Streamlit Secrets
- **Deployment:** Streamlit Cloud

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, email support@yourcompany.com or open an issue in the repository.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Charts powered by [Plotly](https://plotly.com)
- Icons from various emoji sets

---

**Made with ❤️ for enterprise risk management**

**Version:** 1.0.0 | **Last Updated:** January 2025
