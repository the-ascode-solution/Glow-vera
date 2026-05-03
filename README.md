# 🌿 Glowvera Naturals E-commerce Platform

**Official Domain**: [glowveranaturals.com](https://glowveranaturals.com)

A modern, high-performance e-commerce solution for **Glowvera Naturals**, specialized in premium organic beauty products. Featuring a robust admin dashboard, dynamic checkout with localized tax/shipping logic, and a stunning nature-inspired UI.

---

## 🚀 Production Deployment (cPanel + GitHub)

This project is configured for automated deployment to **SymbolHost cPanel** via GitHub Actions.

### Deployment Workflow
1. **Push to Main**: Any push to the `main` branch triggers the GitHub Action.
2. **Automated Build**: GitHub installs dependencies and runs basic checks.
3. **Secure Transfer**: Code is synced to `~/apps/glowveranaturals` on the server.
4. **Auto-Update**: The server automatically runs database migrations (`flask db upgrade`) and restarts the Python Passenger process.

### Environment Secrets
Ensure the following secrets are set in GitHub:
- `SSH_HOST`: Server IP/Hostname
- `SSH_USER`: cPanel Username
- `SSH_KEY`: Private SSH Key
- `PROD_ENV`: Full content of production `.env`

---

## ✨ Key Features

### 🛍️ Premium Shopping Experience
- **Dedicated Brand Pages**: Comprehensive **About Us** and **Contact Us** pages detailing the brand's artisanal story and commitment to sustainability.
- **Legal Compliance**: Built-in templates for **Privacy Policy**, **Terms of Service**, and **Shipping & Returns**.
- **Localized PKR Support**: Site is natively anchored to PKR currency with automated formatting.
- **Dynamic Checkout**: Support for **Cash on Delivery (COD)**, **50% Advance**, and **Full Advance** payment models.
- **Smart Promo System**: Apply discount codes for percentage-off, fixed-amount, or **Free Delivery**.
- **WhatsApp Support**: Floating support widget integrated for instant customer service.

### 🛡️ Professional Admin Dashboard
- **Admin Message Center**: Dedicated interface to manage customer inquiries from the contact form, including email reply support.
- **Product Management**: Full CRUD suite with **local file upload** support (no external dependencies).
- **Order Tracking**: Comprehensive order list with status updates (Pending, Processing, Shipped, Delivered).
- **Printable Invoices**: One-click professional bill generation for order fulfillment.
- **System Settings**: Admin-controlled tax rates (per payment method) and flat shipping fees.
- **Refactored Architecture**: Centralized `admin_base.html` ensures design consistency and easy scalability across all admin sub-panels.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+ / Flask
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: HTML5, Vanilla JS, CSS3 (Modern Flexbox/Grid)
- **UI Framework**: Bootstrap 5.3
- **Icons & Fonts**: FontAwesome 6, Google Fonts (Playfair Display & Poppins)

---

## 🚀 Installation & Setup

### 1. Environment Setup
Clone the repository and ensure you have Python installed.
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
The database is automatically initialized on the first run.
```bash
python app.py
```
*Access the site at `http://localhost:5000`*

---

## 🔐 Admin Access
To manage the store, navigate to `/admin` and use the default credentials:

- **Username**: `admin`
- **Password**: `faizi123`

---

## 📁 Project Structure

```text
├── .gitignore             # Git exclusion rules
├── app.py                 # Core Flask Logic & Routes
├── instance/              # Instance-specific files (Ignored)
│   └── glowvera.db        # SQLite Database
├── logs/                  # Application logs (Ignored)
├── static/                # Assets
│   ├── css/style.css      # Premium UI Styles
│   └── images/            # Local Asset Storage (Products, Logo)
├── templates/             # Jinja2 Layouts
│   ├── admin_base.html    # Master Admin Layout
│   ├── admin_*.html       # Dashboard, Messages, Orders, etc.
│   ├── about.html         # Brand Story Page
│   ├── contact.html       # Customer Inquiry Page
│   └── *_policy.html      # Legal & Policy Templates
└── requirements.txt       # Project Dependencies

### File Details
- **`app.py`**: The main entry point of the application. Handles routing, database models, and server logic.
- **`.gitignore`**: Specifies files and directories that Git should ignore (e.g., local databases, logs, virtual environments).
- **`instance/`**: Contains the local SQLite database. This folder is ignored by Git to prevent production data from being overwritten by local data.
- **`logs/`**: Stores application execution logs. Ignored by Git to avoid merge conflicts and bloating the repository.
- **`static/`**: Contains public-facing assets like CSS, JavaScript, and product images.
- **`templates/`**: Jinja2 HTML templates for the frontend and admin dashboard.
- **`requirements.txt`**: List of Python packages required to run the application.
```

---

## 🎨 Professional Design System
The site utilizes a curated color palette:
- **Primary**: `#2E7D32` (Forest Green)
- **Accent**: `#81C784` (Soft Leaf)
- **Background**: Modern `#FAFAFA` with custom nature-inspired micro-animations.

---

## 📞 Support & Social
Integrated WhatsApp support link for direct customer inquiries. 
Official Message Link: [Chat with Support](https://wa.me/message/IRE7QJVHVL6JN1)

---
**Glowvera Naturals** - *Pure Beauty from Nature* 🌿 | © 2026 All Rights Reserved