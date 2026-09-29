from flask import Blueprint, render_template, request, jsonify, session, current_app
from routes.auth import login_required, get_current_user
from models.book import Book
from models.member import Member
from models.issue import Issue, Reservation
import json
import os

from extensions import limiter

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

@ai_bp.route('/assistant', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per minute")
def assistant():
    user = get_current_user()
    if request.method == 'POST':
        query = request.json.get('query', '')
        
        # Determine intent (mock implementation for safe offline/no-api usage)
        query_lower = query.lower()
        
        if 'due' in query_lower or 'my books' in query_lower or 'have i' in query_lower:
            member = Member.get_by_user_id(user.id)
            if not member:
                return jsonify({'response': "You don't have a library membership yet."})
            issues = [i for i in Issue.get_by_member(member.id, status='issued')]
            if not issues:
                return jsonify({'response': "You don't have any books currently borrowed."})
            response_text = "Here are your currently borrowed books:\n\n"
            for i in issues:
                response_text += f"- **{i.book.title}**: Due on {i.due_date.strftime('%d %b %Y')}\n"
            return jsonify({'response': response_text})
            
        elif 'fine' in query_lower or 'owe' in query_lower:
            member = Member.get_by_user_id(user.id)
            if not member:
                return jsonify({'response': "You don't have a library membership yet."})
            from models.fine import Fine
            fines = Fine.get_by_member(member.id, status='pending')
            total = sum(f.amount for f in fines)
            if total > 0:
                return jsonify({'response': f"You have pending fines totaling ₹{total:.2f}."})
            else:
                return jsonify({'response': "You have no pending fines. Great job!"})
                
        else:
            # Search intent
            books = Book.get_all()
            results = []
            for b in books:
                if any(word in b.title.lower() or word in b.category.lower() for word in query_lower.split()):
                    results.append(b)
            
            if results:
                response_text = f"I found some books that match your query:\n\n"
                for r in results[:5]:
                    avail = f"{r.available_copies} copies available" if r.available_copies > 0 else "Currently unavailable"
                    response_text += f"- **{r.title}** by {r.author} ({avail})\n"
                return jsonify({'response': response_text})
            else:
                return jsonify({'response': "I couldn't find any books matching your query in the library."})

    return render_template('ai/assistant.html')
