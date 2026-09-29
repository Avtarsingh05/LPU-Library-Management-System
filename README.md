# 📚 Library Management System

A complete, professional web-based Library Management System built with Python and Flask. Designed for college/university libraries with full admin and member portals.

---

## 🌟 Features

### Admin / Librarian
- **Dashboard** — Real-time statistics, 4 Chart.js charts, recent activity feed, overdue books
- **Book Management** — Add, edit, delete, search, filter, and paginate books
- **Member Management** — Register members, view profiles, enable/disable accounts
- **Issue Books** — Live member/book search with availability checking
- **Return Books** — Process returns with automatic fine calculation
- **Fine Management** — Mark fines as paid or waived
- **Reservations** — View and manage book reservations
- **Reports** — Period-filtered analytics with CSV export
- **Settings** — Configure library rules, fine rates, borrow periods

### Member / Student
- **Personal Dashboard** — View borrowed books, due dates, fines, reservations
- **Search Books** — Browse full catalog with filters and sorting
- **Reserve Books** — Reserve unavailable books
- **Borrowing History** — Complete history with fine details

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3, Flask |
| Database | SQLite + SQLAlchemy ORM |
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Icons | Bootstrap Icons 1.11 |
| Charts | Chart.js 4.4 |
| Auth | Flask sessions + Werkzeug password hashing |
| Fonts | Google Fonts (Inter) |

---

## 📁 Project Structure

```
library-management/
│
├── app.py                 # Flask application factory
├── config.py              # Configuration classes
├── seed.py                # Database seeder with demo data
├── requirements.txt       # Python dependencies
├── README.md
├── .env.example           # Environment variable template
│
├── instance/
│   └── library.db         # SQLite database (auto-created)
│
├── models/
│   ├── __init__.py        # SQLAlchemy db instance
│   ├── user.py            # User model (admin/member roles)
│   ├── book.py            # Book model
│   ├── member.py          # Member profile model
│   ├── issue.py           # Issue + Reservation models
│   ├── fine.py            # Fine model
│   └── setting.py         # Library settings model
│
├── routes/
│   ├── auth.py            # Login, logout, decorators
│   ├── dashboard.py       # Admin + member dashboards
│   ├── books.py           # Book CRUD + search API
│   ├── members.py         # Member CRUD + search API
│   ├── issues.py          # Issue + return system
│   ├── fines.py           # Fine management
│   ├── reservations.py    # Reservation system
│   ├── reports.py         # Reports + CSV export
│   └── settings.py        # Library + profile settings
│
├── templates/
│   ├── base.html          # Master layout (sidebar + topbar)
│   ├── login.html         # Login page
│   ├── dashboard.html     # Admin dashboard
│   ├── member_dashboard.html
│   ├── books/             # Book templates (index, add, edit, view)
│   ├── members/           # Member templates (index, add, edit, view)
│   ├── issues/            # Issue + return templates
│   ├── fines/             # Fines template
│   ├── reservations/      # Reservations template
│   ├── reports/           # Reports template
│   ├── settings/          # Settings template
│   └── errors/            # 404, 403, 500 error pages
│
└── static/
    ├── css/style.css      # Complete custom stylesheet
    └── js/app.js          # Application JavaScript
```

---

## 🗄️ Database Design

### Tables
- **users** — Login accounts (admin/member roles)
- **books** — Book catalog with copy tracking
- **members** — Student/member profiles
- **issues** — Book issue records (with due dates)
- **reservations** — Book reservation queue
- **fines** — Overdue fine records
- **settings** — Library configuration (key-value)

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip

### Step 1: Clone or Download
```bash
cd C:\Users\avtar\OneDrive\Desktop\System\lms
```

### Step 2: Create Virtual Environment
```bash
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment (Optional)
```bash
# Copy the example file
copy .env.example .env

# Edit .env with your settings (optional for development)
```

### Step 5: Seed the Database
```bash
python seed.py
```

This will create the SQLite database and populate it with:
- 30+ books across 12 categories
- 15+ student members
- 2 admin accounts
- Historical issue/return records
- Overdue books with fines
- Active reservations

### Step 6: Run the Application
```bash
python app.py
```

### Step 7: Open in Browser
```
http://127.0.0.1:5000
```

---

## 🔑 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin / Librarian** | admin@library.com | admin123 |
| **Member / Student** | student@library.com | student123 |

> ⚠️ Change these credentials in a production environment!

---

## 📊 Business Rules

| Rule | Default |
|------|---------|
| Default borrow period | 14 days |
| Fine per overdue day | ₹5 |
| Maximum books per member | 5 |
| Member must be active to borrow | Yes |
| Duplicate active issues prevented | Yes |
| Cannot delete book with active issues | Yes |

---

## 📸 Screenshots

_Run the app and take screenshots here_

- Login Page
- Admin Dashboard
- Book Catalog
- Member Profile
- Issue Book
- Reports

---

## 🔮 Future Improvements

- [ ] Email notifications for due dates
- [ ] Barcode/QR code scanning
- [ ] Book PDF upload and digital access
- [ ] Advanced reporting with charts export
- [ ] Multi-library branch support
- [ ] REST API for mobile app integration
- [ ] SMS alerts for overdue books
- [ ] Bulk book import via CSV/Excel
- [ ] Renewal system (extend due date)
- [ ] Waiting list management

---

## 📄 License

This project is for educational purposes.

---

*Built with ❤️ using Python, Flask, SQLite, and Bootstrap Icons.*
