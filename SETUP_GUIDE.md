# Branch Risk Analytics Platform - Setup Guide

## 🚀 Deployment Instructions

### Option 1: Streamlit Cloud (Recommended)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Select the repository and branch
   - Set main file path: `branch_risk_dashboard.py`
   - Click "Deploy"

3. **Configure Secrets:**
   - In your Streamlit Cloud app settings
   - Go to "Secrets" section
   - Copy contents from `secrets.toml.template`
   - Paste and modify passwords as needed
   - Save secrets

### Option 2: Local Development

1. **Clone Repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
   cd YOUR_REPO
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Secrets:**
   ```bash
   mkdir .streamlit
   cp secrets.toml.template .streamlit/secrets.toml
   ```
   
   Edit `.streamlit/secrets.toml` and update passwords

4. **Run Application:**
   ```bash
   streamlit run branch_risk_dashboard.py
   ```

## 🔐 Authentication Setup

### Default Credentials
- **Admin:** username: `admin`, password: `admin`
- **Manager:** username: `manager`, password: `manager123`
- **Analyst:** username: `analyst`, password: `analyst123`

⚠️ **IMPORTANT:** Change these passwords before production deployment!

### Creating Custom Users

1. Generate password hash:
   ```python
   import hashlib
   password = "your_secure_password"
   hash_value = hashlib.sha256(str.encode(password)).hexdigest()
   print(hash_value)
   ```

2. Add to secrets.toml:
   ```toml
   [credentials.usernames.newuser]
   name = "New User Name"
   password = "PASTE_HASH_HERE"
   role = "User Role"
   ```

## 📁 Required Files

Your repository should contain:
- `branch_risk_dashboard.py` - Main application
- `requirements.txt` - Python dependencies
- `secrets.toml.template` - Template for authentication
- `README.md` - This file

## 🔧 Configuration

### Streamlit Cloud Secrets Format
```toml
[credentials]

[credentials.usernames.admin]
name = "Administrator"
password = "HASH_VALUE_HERE"
role = "System Administrator"
```

### File Upload Requirements
Users must upload an Excel file (.xlsx) with:
- **Sheet1:** Risk Rules Configuration
- **Sheet2:** Branch Data
- **Sheet3:** Grading Criteria

## 📊 Features

- ✅ Secure authentication system
- ✅ Role-based user management
- ✅ Real-time risk scoring
- ✅ Interactive dashboards
- ✅ Multi-branch analytics
- ✅ Data export capabilities

## 🛠️ Troubleshooting

### "Authentication configuration error"
- Verify secrets.toml is properly configured
- Check for syntax errors in TOML format
- Ensure all required fields are present

### "Module not found"
- Run: `pip install -r requirements.txt`
- Verify all dependencies are installed

### Login Issues
- Verify password hash matches
- Check username spelling (case-sensitive)
- Clear browser cache and try again

## 📞 Support

For issues or questions, please contact your system administrator.

## 🔒 Security Notes

1. Never commit `.streamlit/secrets.toml` to Git
2. Always use strong passwords in production
3. Regularly update user credentials
4. Monitor login attempts
5. Use HTTPS in production

---

**Version:** 1.0.0  
**Last Updated:** 2025-01-17
