import os
from dotenv import load_dotenv
load_dotenv()

from app import app
import requests
from models.book import Book
import random

def fetch_and_add_books():
    subjects = ['science', 'history', 'fantasy', 'programming', 'business']
    books_added = 0
    
    print("Fetching books from OpenLibrary API...")
    for subject in subjects:
        url = f"https://openlibrary.org/subjects/{subject}.json?limit=5"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for work in data.get('works', []):
                    title = work.get('title', 'Unknown Title')
                    authors = ", ".join([a.get('name', 'Unknown') for a in work.get('authors', [])])
                    year = work.get('first_publish_year', 2020)
                    
                    # Randomize copies
                    total = random.randint(2, 6)
                    isbn = f"OL-{work.get('key', '').split('/')[-1]}-{random.randint(1000, 9999)}"
                    
                    b = Book(
                        isbn=isbn,
                        title=title,
                        author=authors,
                        category=subject.capitalize(),
                        publisher="OpenLibrary Import",
                        publication_year=year,
                        total_copies=total,
                        available_copies=total,
                        description=f"A fascinating book about {subject}.",
                        language="English",
                        shelf_location=f"RND-{random.randint(1, 10)}"
                    )
                    b.save()
                    books_added += 1
                    print(f"  [+] Added: {title} by {authors}")
            else:
                print(f"Failed to fetch {subject}")
        except Exception as e:
            print(f"Error fetching {subject}: {e}")
                
    print(f"\nDone! Successfully added {books_added} real random books to the database.")

if __name__ == '__main__':
    with app.app_context():
        fetch_and_add_books()
