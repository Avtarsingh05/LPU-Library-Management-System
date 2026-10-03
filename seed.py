"""
Library Management System - Database Seeder
Run this after setting up the database to populate with demo data.
Usage: python seed.py
"""

from app import app
from models import db
from models.user import User
from models.book import Book
from models.member import Member
from models.issue import Issue, Reservation
from models.fine import Fine
from models.setting import Setting
from datetime import date, timedelta, datetime
import random

# ============================================================
# SEED DATA
# ============================================================

BOOKS_DATA = [
    # Programming
    {"isbn": "978-0-13-468599-1", "title": "Clean Code", "author": "Robert C. Martin", "category": "Programming",
     "publisher": "Prentice Hall", "publication_year": 2008, "total_copies": 5,
     "shelf_location": "A1-01", "language": "English",
     "description": "A handbook of agile software craftsmanship."},
    {"isbn": "978-0-20-161622-4", "title": "The Pragmatic Programmer", "author": "Andrew Hunt", "category": "Programming",
     "publisher": "Addison-Wesley", "publication_year": 2019, "total_copies": 4,
     "shelf_location": "A1-02", "language": "English",
     "description": "Your journey to mastery in software development."},
    {"isbn": "978-0-59-651798-1", "title": "Python Crash Course", "author": "Eric Matthes", "category": "Programming",
     "publisher": "No Starch Press", "publication_year": 2023, "total_copies": 6,
     "shelf_location": "A1-03", "language": "English",
     "description": "A hands-on, project-based introduction to programming."},
    {"isbn": "978-0-13-110362-7", "title": "The C Programming Language", "author": "Brian Kernighan", "category": "Programming",
     "publisher": "Prentice Hall", "publication_year": 1988, "total_copies": 3,
     "shelf_location": "A1-04", "language": "English",
     "description": "The original reference manual for C."},
    {"isbn": "978-0-13-235088-4", "title": "Design Patterns", "author": "Gang of Four", "category": "Programming",
     "publisher": "Addison-Wesley", "publication_year": 1994, "total_copies": 4,
     "shelf_location": "A1-05", "language": "English",
     "description": "Elements of Reusable Object-Oriented Software."},
    
    # Computer Science
    {"isbn": "978-0-26-203384-8", "title": "Introduction to Algorithms", "author": "Thomas H. Cormen", "category": "Computer Science",
     "publisher": "MIT Press", "publication_year": 2022, "total_copies": 5,
     "shelf_location": "B1-01", "language": "English",
     "description": "Comprehensive guide to algorithms and data structures."},
    {"isbn": "978-0-13-603252-3", "title": "Computer Organization and Architecture", "author": "William Stallings", "category": "Computer Science",
     "publisher": "Pearson", "publication_year": 2021, "total_copies": 4,
     "shelf_location": "B1-02", "language": "English",
     "description": "Design for performance in computer systems."},
    {"isbn": "978-0-13-213080-9", "title": "Artificial Intelligence: A Modern Approach", "author": "Stuart Russell", "category": "Artificial Intelligence",
     "publisher": "Pearson", "publication_year": 2020, "total_copies": 5,
     "shelf_location": "B2-01", "language": "English",
     "description": "The standard text in AI for university courses."},
    
    # Database
    {"isbn": "978-0-13-608960-5", "title": "Database System Concepts", "author": "Abraham Silberschatz", "category": "Database",
     "publisher": "McGraw-Hill", "publication_year": 2019, "total_copies": 6,
     "shelf_location": "C1-01", "language": "English",
     "description": "Comprehensive coverage of database concepts."},
    {"isbn": "978-0-59-651887-2", "title": "Learning SQL", "author": "Alan Beaulieu", "category": "Database",
     "publisher": "O'Reilly Media", "publication_year": 2020, "total_copies": 4,
     "shelf_location": "C1-02", "language": "English",
     "description": "Master SQL fundamentals."},
    {"isbn": "978-1-49-195442-1", "title": "MongoDB: The Definitive Guide", "author": "Shannon Bradshaw", "category": "Database",
     "publisher": "O'Reilly Media", "publication_year": 2019, "total_copies": 3,
     "shelf_location": "C1-03", "language": "English",
     "description": "Powerful and scalable data storage."},
    
    # Networking
    {"isbn": "978-0-13-294812-0", "title": "Computer Networks", "author": "Andrew S. Tanenbaum", "category": "Networking",
     "publisher": "Pearson", "publication_year": 2021, "total_copies": 5,
     "shelf_location": "D1-01", "language": "English",
     "description": "The standard networking textbook."},
    {"isbn": "978-0-07-352896-0", "title": "Data Communications and Networking", "author": "Behrouz Forouzan", "category": "Networking",
     "publisher": "McGraw-Hill", "publication_year": 2012, "total_copies": 4,
     "shelf_location": "D1-02", "language": "English",
     "description": "Comprehensive data communications reference."},
    
    # Operating Systems
    {"isbn": "978-0-13-813130-0", "title": "Operating System Concepts", "author": "Abraham Silberschatz", "category": "Operating Systems",
     "publisher": "Wiley", "publication_year": 2018, "total_copies": 6,
     "shelf_location": "E1-01", "language": "English",
     "description": "The definitive OS textbook, known as the Dinosaur Book."},
    {"isbn": "978-0-13-359162-0", "title": "Modern Operating Systems", "author": "Andrew S. Tanenbaum", "category": "Operating Systems",
     "publisher": "Pearson", "publication_year": 2014, "total_copies": 4,
     "shelf_location": "E1-02", "language": "English",
     "description": "A comprehensive view of operating system principles."},
    
    # Web Development
    {"isbn": "978-1-49-195201-4", "title": "Flask Web Development", "author": "Miguel Grinberg", "category": "Web Development",
     "publisher": "O'Reilly Media", "publication_year": 2018, "total_copies": 4,
     "shelf_location": "F1-01", "language": "English",
     "description": "Developing Web Applications with Python."},
    {"isbn": "978-0-59-651798-2", "title": "JavaScript: The Good Parts", "author": "Douglas Crockford", "category": "Web Development",
     "publisher": "O'Reilly Media", "publication_year": 2008, "total_copies": 3,
     "shelf_location": "F1-02", "language": "English",
     "description": "Unearthing the excellence in JavaScript."},
    {"isbn": "978-1-49-192068-6", "title": "HTML and CSS: Design and Build Websites", "author": "Jon Duckett", "category": "Web Development",
     "publisher": "Wiley", "publication_year": 2011, "total_copies": 5,
     "shelf_location": "F1-03", "language": "English",
     "description": "A beautiful guide to HTML and CSS."},
    
    # Mathematics
    {"isbn": "978-0-07-338533-8", "title": "Discrete Mathematics and Its Applications", "author": "Kenneth Rosen", "category": "Mathematics",
     "publisher": "McGraw-Hill", "publication_year": 2018, "total_copies": 5,
     "shelf_location": "G1-01", "language": "English",
     "description": "Comprehensive discrete math for CS students."},
    {"isbn": "978-0-13-486709-3", "title": "Linear Algebra and Its Applications", "author": "David Lay", "category": "Mathematics",
     "publisher": "Pearson", "publication_year": 2014, "total_copies": 4,
     "shelf_location": "G1-02", "language": "English",
     "description": "Accessible introduction to linear algebra."},
    
    # Management
    {"isbn": "978-0-07-337359-5", "title": "Project Management: A Systems Approach", "author": "Harold Kerzner", "category": "Management",
     "publisher": "Wiley", "publication_year": 2017, "total_copies": 3,
     "shelf_location": "H1-01", "language": "English",
     "description": "Planning, scheduling, and controlling projects."},
    
    # Engineering
    {"isbn": "978-0-07-352892-2", "title": "Engineering Mechanics: Statics", "author": "James L. Meriam", "category": "Engineering",
     "publisher": "Wiley", "publication_year": 2020, "total_copies": 4,
     "shelf_location": "I1-01", "language": "English",
     "description": "Classic statics textbook for engineering students."},
    
    # Fiction
    {"isbn": "978-0-06-112008-4", "title": "To Kill a Mockingbird", "author": "Harper Lee", "category": "Fiction",
     "publisher": "Harper Perennial", "publication_year": 1960, "total_copies": 4,
     "shelf_location": "J1-01", "language": "English",
     "description": "A Pulitzer Prize-winning masterwork of honor and injustice."},
    {"isbn": "978-0-74-327356-5", "title": "Harry Potter and the Philosopher's Stone", "author": "J.K. Rowling", "category": "Fiction",
     "publisher": "Bloomsbury", "publication_year": 1997, "total_copies": 5,
     "shelf_location": "J1-02", "language": "English",
     "description": "The magical first installment of the Harry Potter series."},
    {"isbn": "978-0-14-028329-7", "title": "1984", "author": "George Orwell", "category": "Fiction",
     "publisher": "Penguin Books", "publication_year": 1949, "total_copies": 4,
     "shelf_location": "J1-03", "language": "English",
     "description": "A dystopian social science fiction novel."},
    
    # Biography
    {"isbn": "978-1-45-165520-5", "title": "Steve Jobs", "author": "Walter Isaacson", "category": "Biography",
     "publisher": "Simon & Schuster", "publication_year": 2011, "total_copies": 3,
     "shelf_location": "K1-01", "language": "English",
     "description": "The biography of Apple's co-founder."},
    {"isbn": "978-0-06-251740-4", "title": "Elon Musk", "author": "Ashlee Vance", "category": "Biography",
     "publisher": "Ecco", "publication_year": 2015, "total_copies": 3,
     "shelf_location": "K1-02", "language": "English",
     "description": "Tesla, SpaceX, and the Quest for a Fantastic Future."},
    
    # Science
    {"isbn": "978-0-55-338016-3", "title": "A Brief History of Time", "author": "Stephen Hawking", "category": "Science",
     "publisher": "Bantam Books", "publication_year": 1988, "total_copies": 4,
     "shelf_location": "L1-01", "language": "English",
     "description": "From the Big Bang to Black Holes."},
    {"isbn": "978-0-39-332495-7", "title": "The Selfish Gene", "author": "Richard Dawkins", "category": "Science",
     "publisher": "Oxford University Press", "publication_year": 1976, "total_copies": 3,
     "shelf_location": "L1-02", "language": "English",
     "description": "The classic exposition of the gene-centered view of evolution."},
    
    # Economics  
    {"isbn": "978-0-06-197680-1", "title": "Freakonomics", "author": "Steven D. Levitt", "category": "Economics",
     "publisher": "HarperCollins", "publication_year": 2005, "total_copies": 3,
     "shelf_location": "M1-01", "language": "English",
     "description": "A Rogue Economist Explores the Hidden Side of Everything."},
]

MEMBERS_DATA = [
    {"name": "Arjun Kumar", "email": "arjun.kumar@student.edu", "phone": "9876543210", 
     "department": "Computer Science", "course": "B.Tech CSE", "semester": "6th Semester",
     "address": "Room 201, Boys Hostel, University Campus"},
    {"name": "Priya Sharma", "email": "priya.sharma@student.edu", "phone": "9876543211",
     "department": "Information Technology", "course": "B.Tech IT", "semester": "4th Semester",
     "address": "204, Girls Hostel, University Campus"},
    {"name": "Rahul Verma", "email": "rahul.verma@student.edu", "phone": "9876543212",
     "department": "Electronics", "course": "B.Tech ECE", "semester": "5th Semester",
     "address": "15, New Colony, Near University"},
    {"name": "Sneha Patel", "email": "sneha.patel@student.edu", "phone": "9876543213",
     "department": "Computer Science", "course": "MCA", "semester": "2nd Semester",
     "address": "Room 305, Girls Hostel, University Campus"},
    {"name": "Amit Singh", "email": "amit.singh@student.edu", "phone": "9876543214",
     "department": "Mechanical Engineering", "course": "B.Tech ME", "semester": "7th Semester",
     "address": "22, Staff Quarters, University Campus"},
    {"name": "Neha Gupta", "email": "neha.gupta@student.edu", "phone": "9876543215",
     "department": "Mathematics", "course": "M.Sc Math", "semester": "1st Semester",
     "address": "Room 102, Girls Hostel, University Campus"},
    {"name": "Vikram Reddy", "email": "vikram.reddy@student.edu", "phone": "9876543216",
     "department": "Computer Science", "course": "B.Tech CSE", "semester": "3rd Semester",
     "address": "Room 401, Boys Hostel, University Campus"},
    {"name": "Ananya Iyer", "email": "ananya.iyer@student.edu", "phone": "9876543217",
     "department": "Management", "course": "MBA", "semester": "2nd Semester",
     "address": "15, Faculty Lane, University Campus"},
    {"name": "Rohan Mehta", "email": "rohan.mehta@student.edu", "phone": "9876543218",
     "department": "Civil Engineering", "course": "B.Tech CE", "semester": "8th Semester",
     "address": "Room 503, Boys Hostel, University Campus"},
    {"name": "Kavitha Nair", "email": "kavitha.nair@student.edu", "phone": "9876543219",
     "department": "Information Technology", "course": "B.Tech IT", "semester": "6th Semester",
     "address": "Room 208, Girls Hostel, University Campus"},
    {"name": "Sanjay Desai", "email": "sanjay.desai@student.edu", "phone": "9876543220",
     "department": "Physics", "course": "M.Sc Physics", "semester": "3rd Semester",
     "address": "22, PG Housing, Near Science Block"},
    {"name": "Divya Kapoor", "email": "divya.kapoor@student.edu", "phone": "9876543221",
     "department": "Computer Science", "course": "B.Tech CSE", "semester": "5th Semester",
     "address": "Room 110, Girls Hostel, University Campus"},
    {"name": "Ravi Shankar", "email": "ravi.shankar@student.edu", "phone": "9876543222",
     "department": "Artificial Intelligence", "course": "M.Tech AI", "semester": "1st Semester",
     "address": "Room 601, Research Scholars Hostel"},
    {"name": "Meena Joshi", "email": "meena.joshi@student.edu", "phone": "9876543223",
     "department": "Chemistry", "course": "B.Sc Chemistry", "semester": "4th Semester",
     "address": "24, Old Campus Colony"},
    {"name": "Kiran Babu", "email": "kiran.babu@student.edu", "phone": "9876543224",
     "department": "Management", "course": "BBA", "semester": "2nd Semester",
     "address": "Room 303, Boys Hostel, University Campus"},
]

def seed_settings():
    """Seed default library settings."""
    defaults = {
        'library_name': 'LibEase',
        'library_address': 'Lovely Professional University, Phagwara',
        'library_email': 'library@university.edu',
        'library_phone': '+91-9876543210',
        'fine_per_day': '5',
        'max_books_per_member': '5',
        'default_borrow_days': '14',
    }
    for key, value in defaults.items():
        if not Setting.query.filter_by(key=key).first():
            db.session.add(Setting(key=key, value=value))
    db.session.commit()
    print("✅ Settings seeded")

def seed_admins():
    """Create admin users."""
    admins = [
        {"name": "Library Admin", "email": "admin@library.com", "password": "admin123", "role": "admin"},
        {"name": "Head Librarian", "email": "librarian@library.com", "password": "admin123", "role": "admin"},
    ]
    for data in admins:
        if not User.query.filter_by(email=data['email']).first():
            user = User(name=data['name'], email=data['email'], role=data['role'])
            user.set_password(data['password'])
            db.session.add(user)
    db.session.commit()
    print("✅ Admin users seeded")

def seed_books():
    """Add books to the database."""
    for data in BOOKS_DATA:
        if not Book.query.filter_by(isbn=data['isbn']).first():
            book = Book(
                isbn=data['isbn'],
                title=data['title'],
                author=data['author'],
                category=data['category'],
                publisher=data['publisher'],
                publication_year=data['publication_year'],
                total_copies=data['total_copies'],
                available_copies=data['total_copies'],  # All available initially
                shelf_location=data['shelf_location'],
                language=data['language'],
                description=data['description']
            )
            db.session.add(book)
    db.session.commit()
    print(f"✅ {len(BOOKS_DATA)} books seeded")

def seed_members():
    """Create member records with login accounts."""
    # Create the demo student user
    demo_user_email = "student@library.com"
    if not User.query.filter_by(email=demo_user_email).first():
        demo_user = User(name="Demo Student", email=demo_user_email, role="member")
        demo_user.set_password("student123")
        db.session.add(demo_user)
        db.session.flush()
        demo_member = Member(
            member_id="LIB2024DEMO",
            user_id=demo_user.id,
            name="Demo Student",
            email=demo_user_email,
            phone="9876540000",
            department="Computer Science",
            course="B.Tech CSE",
            semester="4th Semester",
            address="Demo Hostel, University Campus"
        )
        db.session.add(demo_member)
    
    year = date.today().year
    for i, data in enumerate(MEMBERS_DATA):
        if not Member.query.filter_by(email=data['email']).first():
            member_id = f"LIB{year}{str(i+1).zfill(4)}"
            member = Member(
                member_id=member_id,
                name=data['name'],
                email=data['email'],
                phone=data['phone'],
                department=data['department'],
                course=data['course'],
                semester=data['semester'],
                address=data['address'],
                status='active'
            )
            db.session.add(member)
    db.session.commit()
    print(f"✅ {len(MEMBERS_DATA) + 1} members seeded")

def seed_issues_and_fines():
    """Create realistic issue/return/fine records."""
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        print("⚠️  No admin found, skipping issues")
        return
    
    members = Member.query.all()
    books = Book.query.all()
    today = date.today()
    fine_per_day = 5
    
    if not members or not books:
        print("⚠️  No members or books found")
        return
    
    issues_created = 0
    
    # --- RETURNED ISSUES (historical data) ---
    historical_pairs = [
        (0, 0, -60, -50),   # member 0, book 0, issued 60 days ago, returned 50 days ago
        (1, 2, -55, -48),
        (2, 5, -45, -38),
        (3, 8, -40, -30),
        (4, 11, -35, -28),
        (5, 1, -30, -22),
        (6, 3, -25, -18),
        (7, 9, -20, -13),
        (8, 14, -15, -8),
        (9, 6, -12, -5),
        (0, 4, -90, -80),
        (1, 7, -70, -60),
        (2, 10, -50, -40),
        (3, 13, -80, -72),
    ]
    
    for mi, bi, issue_offset, return_offset in historical_pairs:
        m_idx = mi % len(members)
        b_idx = bi % len(books)
        m = members[m_idx]
        b = books[b_idx]
        
        issue_date = today + timedelta(days=issue_offset)
        return_date = today + timedelta(days=return_offset)
        due_date = issue_date + timedelta(days=14)
        
        issue = Issue(
            book_id=b.id,
            member_id=m.id,
            issued_by=admin.id,
            issue_date=issue_date,
            due_date=due_date,
            return_date=return_date,
            status='returned'
        )
        
        # Calculate fine if overdue
        fine_amount = 0
        if return_date > due_date:
            overdue_days = (return_date - due_date).days
            fine_amount = overdue_days * fine_per_day
            issue.fine_amount = fine_amount
        
        db.session.add(issue)
        db.session.flush()
        
        if fine_amount > 0:
            # Some fines paid, some pending
            status = 'paid' if random.random() > 0.3 else 'pending'
            fine = Fine(
                issue_id=issue.id,
                member_id=m.id,
                amount=fine_amount,
                reason=f'Overdue return',
                status=status,
                paid_date=datetime.utcnow() if status == 'paid' else None
            )
            db.session.add(fine)
        
        issues_created += 1
    
    # --- CURRENT ACTIVE ISSUES ---
    active_pairs = [
        (0, 0, -10, 4),    # issued 10 days ago, due in 4 days
        (1, 2, -5, 9),     # issued 5 days ago, due in 9 days
        (2, 5, -8, 6),     # issued 8 days ago, due in 6 days
        (3, 8, -12, 2),    # issued 12 days ago, due in 2 days (due soon!)
        (4, 11, -14, 0),   # issued 14 days ago, due today
        (5, 1, -3, 11),    # issued 3 days ago, due in 11 days
        (6, 3, -7, 7),     # issued 7 days ago, due in 7 days
    ]
    
    for mi, bi, issue_offset, days_left in active_pairs:
        m_idx = mi % len(members)
        b_idx = bi % len(books)
        m = members[m_idx]
        b = books[b_idx]
        
        if b.available_copies <= 0:
            continue
            
        issue_date = today + timedelta(days=issue_offset)
        due_date = today + timedelta(days=days_left)
        
        issue = Issue(
            book_id=b.id,
            member_id=m.id,
            issued_by=admin.id,
            issue_date=issue_date,
            due_date=due_date,
            status='issued'
        )
        b.available_copies -= 1
        db.session.add(issue)
        issues_created += 1
    
    # --- OVERDUE ISSUES ---
    overdue_pairs = [
        (7, 12, -25, -5),   # issued 25 days ago, was due 5 days ago
        (8, 15, -30, -10),  # issued 30 days ago, was due 10 days ago
        (9, 17, -20, -3),   # issued 20 days ago, was due 3 days ago
    ]
    
    for mi, bi, issue_offset, due_offset in overdue_pairs:
        m_idx = mi % len(members)
        b_idx = bi % len(books)
        m = members[m_idx]
        b = books[b_idx]
        
        if b.available_copies <= 0:
            continue
        
        issue_date = today + timedelta(days=issue_offset)
        due_date = today + timedelta(days=due_offset)
        
        issue = Issue(
            book_id=b.id,
            member_id=m.id,
            issued_by=admin.id,
            issue_date=issue_date,
            due_date=due_date,
            status='issued'
        )
        b.available_copies -= 1
        db.session.add(issue)
        issues_created += 1
    
    db.session.commit()
    print(f"✅ {issues_created} issue records seeded (active + returned + overdue)")

def seed_reservations():
    """Create sample reservation records."""
    members = Member.query.all()
    books = Book.query.filter(Book.available_copies == 0).all()
    
    if not members or not books:
        print("⚠️  Skipping reservations (no unavailable books)")
        return
    
    count = 0
    for i, book in enumerate(books[:4]):
        m_idx = (i + 10) % len(members)
        member = members[m_idx]
        
        existing = Reservation.query.filter_by(
            book_id=book.id, member_id=member.id
        ).filter(Reservation.status.in_(['pending', 'available'])).first()
        
        if not existing:
            res = Reservation(book_id=book.id, member_id=member.id, status='pending')
            db.session.add(res)
            count += 1
    
    db.session.commit()
    print(f"✅ {count} reservations seeded")

def main():
    with app.app_context():
        print("\n🌱 Starting database seeding...\n")
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created")
        
        seed_settings()
        seed_admins()
        seed_books()
        seed_members()
        seed_issues_and_fines()
        seed_reservations()
        
        print("\n" + "="*50)
        print("✅ Database seeding complete!")
        print("="*50)
        print("\n📋 Demo Credentials:")
        print("  Admin:   admin@library.com     / admin123")
        print("  Member:  student@library.com   / student123")
        print("\n🚀 Run: python app.py")
        print("   Open: http://127.0.0.1:5000")
        print()

if __name__ == '__main__':
    main()


